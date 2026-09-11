import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdaptiveComputeGovernor:
    def __init__(self, max_concurrent_slm: int = 2, cooldown_seconds: float = 0.5):
        self.max_concurrent_slm = max_concurrent_slm
        self.cooldown_seconds = cooldown_seconds
        self._active_slm_requests = 0
        self._last_slm_finish = 0.0

    def should_use_slm(self, text_length: int) -> bool:
        if text_length < 15:
            return False
        if self._active_slm_requests >= self.max_concurrent_slm:
            logger.info('AdaptiveComputeGovernor: High concurrency, throttling SLM to Regex fallback.')
            return False
        if (time.time() - self._last_slm_finish) < self.cooldown_seconds:
            logger.info('AdaptiveComputeGovernor: CPU cooldown active, using Heuristic fallback.')
            return False
        return True

    def acquire_slm(self) -> None:
        self._active_slm_requests += 1

    def release_slm(self) -> None:
        self._active_slm_requests = max(0, self._active_slm_requests - 1)
        self._last_slm_finish = time.time()
