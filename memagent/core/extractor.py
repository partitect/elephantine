import re
from typing import Any, Dict, List, Optional, Tuple

class TwoStageMemoryExtractor:
    """
    Two-stage cognitive extraction pipeline:
    Stage 1: Regex & heuristic pattern analyzer (detects facts, user preferences, API keys, credentials, procedural configs).
             If score < threshold, it skips expensive SLM inference entirely.
    Stage 2: Structured extraction (clean fact sentence + extracted key).
    """

    PREFERENCE_PATTERNS = [
        re.compile(r"(?:i prefer|i like|i always use|my favorite|always configure|my preference is)\s+(?P<val>[^.\n;]+)", re.IGNORECASE),
        re.compile(r"(?:use|set|target)\s+(?P<key>database|theme|model|language|compiler|port)\s*(?:to|=)\s*(?P<val>[^.\n;]+)", re.IGNORECASE),
    ]

    FACT_PATTERNS = [
        re.compile(r"(?:my name is|i live in|the server ip is|we are using|our deployment runs on)\s+(?P<val>[^.\n;]+)", re.IGNORECASE),
        re.compile(r"(?:the api key for|token for)\s+(?P<key>[a-zA-Z0-9_\-]+)\s*(?:is|=|:)\s*(?P<val>[^.\n;]+)", re.IGNORECASE),
    ]

    PROCEDURAL_PATTERNS = [
        re.compile(r"(?:to fix this error|steps to reproduce|deploy by running|first run|then execute)\s+(?P<val>[^.\n;]+)", re.IGNORECASE),
    ]

    TRIVIAL_PATTERNS = [
        re.compile(r"^(?:ok|okay|thanks|thank you|yes|no|hello|hi|bye|sure|got it)[\s.!]*$", re.IGNORECASE),
    ]

    def pre_filter(self, text: str) -> Tuple[bool, float, str]:
        """
        Stage 1: Evaluates whether input text carries persistent memory value.
        Returns: (should_extract, value_score, detected_category)
        """
        trimmed = text.strip()
        if len(trimmed) < 4:
            return False, 0.0, "trivial"

        # Check trivial greetings or single-word confirmations
        for p in self.TRIVIAL_PATTERNS:
            if p.match(trimmed):
                return False, 0.0, "trivial"

        # Check preferences
        for p in self.PREFERENCE_PATTERNS:
            if p.search(trimmed):
                return True, 0.95, "preference"

        # Check procedural hints
        for p in self.PROCEDURAL_PATTERNS:
            if p.search(trimmed):
                return True, 0.90, "procedural"

        # Check facts
        for p in self.FACT_PATTERNS:
            if p.search(trimmed):
                return True, 0.85, "fact"

        # General sentence check: if sentence contains informative keywords
        info_keywords = ["database", "server", "config", "endpoint", "url", "user", "api", "project", "agent", "rules", "always", "never"]
        words = set(re.findall(r"\w+", trimmed.lower()))
        matched = words.intersection(info_keywords)
        if len(matched) >= 1 and len(trimmed.split()) >= 3:
            return True, 0.70, "general"

        return False, 0.2, "general"

    def extract_structured(self, text: str, default_category: str = "general") -> Dict[str, Any]:
        """
        Stage 2: Deterministic heuristic extraction for facts, entity keys, and clean representations.
        """
        should_extract, score, detected_category = self.pre_filter(text)
        category = default_category if default_category != "general" else detected_category

        entity_key = None
        # Heuristic entity key derivation
        for p in self.PREFERENCE_PATTERNS:
            m = p.search(text)
            if m and "key" in m.groupdict() and m.group("key"):
                entity_key = f"pref:{m.group('key').strip().lower()}"
                break
            elif m:
                entity_key = "pref:general"
                break

        if not entity_key:
            for p in self.FACT_PATTERNS:
                m = p.search(text)
                if m and "key" in m.groupdict() and m.group("key"):
                    entity_key = f"fact:{m.group('key').strip().lower()}"
                    break

        return {
            "should_store": should_extract,
            "confidence": score,
            "category": category,
            "entity_key": entity_key,
            "cleaned_content": text.strip()
        }
