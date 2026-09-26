import math
from typing import List, Dict, Any, Tuple
from app.schemas.evidence import EvidenceObject
from app.core.logging import logger

class VectorStoreService:
    """
    RAG Vector Store & Embedding Manager.
    Stores and indexes Evidence Objects with their semantic embeddings.
    Supports pgvector / sentence-transformers, with lightweight in-memory cosine fallback.
    """

    def __init__(self):
        self._memory_index: Dict[str, List[Tuple[EvidenceObject, List[float]]]] = {}
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer embedding model loaded successfully.")
        except Exception as e:
            logger.warning(f"SentenceTransformer not loaded ({e}). Using deterministic token-hash embeddings.")
            self._model = None

    def embed_text(self, text: str) -> List[float]:
        if self._model:
            try:
                embedding = self._model.encode(text).tolist()
                return embedding
            except Exception as e:
                logger.warning(f"Model encoding failed: {e}")

        # Deterministic lightweight 64-dim embedding simulation
        import hashlib
        vec = [0.0] * 64
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % 64
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 4) for x in vec]

    def index_evidence(self, case_id: str, evidence: EvidenceObject):
        if case_id not in self._memory_index:
            self._memory_index[case_id] = []

        # Prepare rich searchable text (predicate + claim + subject + source)
        text_repr = f"Subject: {evidence.claim.subject} | Property: {evidence.claim.predicate} | Value: {evidence.claim.value} | Source: {evidence.source.type} {evidence.source.name}"
        embedding = self.embed_text(text_repr)
        self._memory_index[case_id].append((evidence, embedding))

    def similarity_search(self, case_id: str, query: str, top_k: int = 5) -> List[EvidenceObject]:
        if case_id not in self._memory_index or not self._memory_index[case_id]:
            return []

        query_vec = self.embed_text(query)
        scored: List[Tuple[float, EvidenceObject]] = []

        for ev, ev_vec in self._memory_index[case_id]:
            # Cosine similarity
            dot = sum(a * b for a, b in zip(query_vec, ev_vec))
            norm_a = math.sqrt(sum(a * a for a in query_vec)) or 1.0
            norm_b = math.sqrt(sum(b * b for b in ev_vec)) or 1.0
            similarity = dot / (norm_a * norm_b)
            scored.append((similarity, ev))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

vector_store = VectorStoreService()
