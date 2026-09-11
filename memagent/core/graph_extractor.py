import re
from typing import List, Optional
from pydantic import BaseModel, Field

class KnowledgeTriplet(BaseModel):
    subject: str = Field(..., description='Entity subject')
    predicate: str = Field(..., description='Relationship verb')
    object: str = Field(..., description='Target entity')
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class RuleBasedGraphExtractor:
    PATTERNS = [
        (r'(\w+)\s+(?:prefers|likes|favors|uses)\s+(\w+)', 'uses'),
        (r'(\w+)\s+(?:works at|works for)\s+(\w+)', 'works_at'),
        (r'(\w+)\s+(?:depends on|relies on)\s+(\w+)', 'depends_on'),
        (r'(\w+)\s+(?:deployed on|hosted on|runs on)\s+(\w+)', 'deployed_on')
    ]

    def extract_triplets(self, text: str) -> List[KnowledgeTriplet]:
        triplets = []
        clean = text.strip()
        if len(clean) < 4:
            return []

        for pattern, pred in self.PATTERNS:
            for m in re.finditer(pattern, clean, re.IGNORECASE):
                subj = m.group(1).lower().strip()
                obj = m.group(2).lower().strip()
                if subj != obj and len(subj) > 1 and len(obj) > 1:
                    triplets.append(KnowledgeTriplet(
                        subject=subj,
                        predicate=pred,
                        object=obj,
                        confidence=0.9
                    ))
        return triplets
