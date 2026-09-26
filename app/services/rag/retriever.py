from typing import List, Optional
from app.schemas.evidence import EvidenceObject
from app.services.rag.vector_store import vector_store
from app.core.logging import logger

class EvidenceRetriever:
    """
    RAG Evidence Retriever.
    Finds the most decision-critical Evidence objects including claims and source metadata.
    """

    def retrieve_decision_evidence(
        self,
        case_id: str,
        query: Optional[str] = None,
        all_evidence: Optional[List[EvidenceObject]] = None,
        top_k: int = 10
    ) -> List[EvidenceObject]:
        
        # Ensure all case evidence is indexed in vector store
        if all_evidence:
            for ev in all_evidence:
                vector_store.index_evidence(case_id, ev)

        search_query = query or f"Key financial, location, device, kyc, and risk evidence for {case_id}"
        results = vector_store.similarity_search(case_id, search_query, top_k=top_k)

        # Fallback to returning all evidence if vector search returned fewer items
        if not results and all_evidence:
            return all_evidence[:top_k]

        return results

retriever = EvidenceRetriever()
