import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from elephantine.config import settings

class HybridScorer:
    """
    Combines Dense Vector Similarity + Sparse BM25 + Exponential Temporal Decay.
    Score = [alpha * dense_norm + (1 - alpha) * sparse_norm] * exp(-lambda * delta_hours)
    """
    def __init__(self, decay_lambda: float = settings.TIME_DECAY_LAMBDA):
        self.decay_lambda = decay_lambda

    def calculate_time_decay(self, created_at_epoch: float, now_epoch: float = None) -> float:
        if now_epoch is None:
            now_epoch = datetime.now(timezone.utc).timestamp()
        
        delta_seconds = max(0.0, now_epoch - created_at_epoch)
        delta_hours = delta_seconds / 3600.0
        decay = math.exp(-self.decay_lambda * delta_hours)
        return float(decay)

    def fuse_and_rank(
        self,
        dense_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        alpha: float = 0.7,
        use_time_decay: bool = True
    ) -> List[Dict[str, Any]]:
        combined: Dict[str, Dict[str, Any]] = {}
        now_epoch = datetime.now(timezone.utc).timestamp()

        for item in dense_results:
            mem_id = item["id"]
            sim = float(item.get("cosine_similarity", 0.0))
            combined[mem_id] = {
                "id": mem_id,
                "vector_score": sim,
                "bm25_score": 0.0,
                "created_at_epoch": item.get("created_at_epoch", now_epoch),
                "source_agent": item.get("source_agent", "default"),
                "category": item.get("category", "general")
            }

        for item in bm25_results:
            mem_id = item["id"]
            raw_rank = float(item.get("bm25_rank", 0.0))
            norm_bm25 = 1.0 / (1.0 + abs(raw_rank)) if raw_rank != 0.0 else 0.5
            
            if mem_id in combined:
                combined[mem_id]["bm25_score"] = norm_bm25
            else:
                combined[mem_id] = {
                    "id": mem_id,
                    "vector_score": 0.0,
                    "bm25_score": norm_bm25,
                    "created_at_epoch": now_epoch,
                    "source_agent": item.get("source_agent", "default"),
                    "category": item.get("category", "general")
                }

        ranked_list = []
        for mem_id, data in combined.items():
            vec_s = data["vector_score"]
            bm_s = data["bm25_score"]
            
            if vec_s > 0 and bm_s > 0:
                hybrid_score = (alpha * vec_s) + ((1.0 - alpha) * bm_s)
            elif vec_s > 0:
                hybrid_score = vec_s * alpha
            else:
                hybrid_score = bm_s * (1.0 - alpha)

            decay = self.calculate_time_decay(data["created_at_epoch"], now_epoch) if use_time_decay else 1.0
            final_score = hybrid_score * decay

            ranked_list.append({
                "id": mem_id,
                "vector_score": round(vec_s, 4),
                "bm25_score": round(bm_s, 4),
                "hybrid_score": round(hybrid_score, 4),
                "decayed_score": round(final_score, 4),
                "decay_factor": round(decay, 4)
            })

        ranked_list.sort(key=lambda x: x["decayed_score"], reverse=True)
        return ranked_list
