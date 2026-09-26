from datetime import datetime
from typing import List, Optional, Dict, Any
from app.db.mongodb import mongo_db
from app.core.logging import logger

class Repository:
    """
    Unified Data Access Repository.
    Stores and retrieves all Case, Evidence, Decision, and Document data in MongoDB.
    """

    # ----------------------------------------------------
    # CASES
    # ----------------------------------------------------
    @staticmethod
    async def create_case(case_data: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            case_data.setdefault("created_at", datetime.utcnow().isoformat())
            case_data.setdefault("updated_at", datetime.utcnow().isoformat())
            await db.cases.update_one(
                {"case_id": case_data["case_id"]},
                {"$set": case_data},
                upsert=True
            )
            return case_data
        return case_data

    @staticmethod
    async def get_case(case_id: str) -> Optional[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            doc = await db.cases.find_one({"case_id": case_id}, {"_id": 0})
            return doc
        return None

    @staticmethod
    async def list_cases(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            cursor = db.cases.find({}, {"_id": 0}).skip(offset).limit(limit)
            return await cursor.to_list(length=limit)
        return []

    # ----------------------------------------------------
    # EVIDENCE
    # ----------------------------------------------------
    @staticmethod
    async def add_evidence(evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            evidence_data.setdefault("created_at", datetime.utcnow().isoformat())
            await db.evidence.update_one(
                {"evidence_id": evidence_data["evidence_id"]},
                {"$set": evidence_data},
                upsert=True
            )
        return evidence_data

    @staticmethod
    async def get_case_evidence(case_id: str) -> List[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            cursor = db.evidence.find({"case_id": case_id}, {"_id": 0})
            return await cursor.to_list(length=100)
        return []

    @staticmethod
    async def clear_case_evidence(case_id: str):
        db = mongo_db.db
        if db is not None:
            await db.evidence.delete_many({"case_id": case_id})

    # ----------------------------------------------------
    # DOCUMENTS
    # ----------------------------------------------------
    @staticmethod
    async def create_document(doc_data: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            doc_data.setdefault("created_at", datetime.utcnow().isoformat())
            await db.documents.update_one(
                {"document_id": doc_data["document_id"]},
                {"$set": doc_data},
                upsert=True
            )
        return doc_data

    # ----------------------------------------------------
    # DECISIONS
    # ----------------------------------------------------
    @staticmethod
    async def save_decision(decision_packet: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            record = {
                "case_id": decision_packet["case_id"],
                "trust_status": decision_packet["trust_status"],
                "packet": decision_packet,
                "created_at": datetime.utcnow().isoformat()
            }
            await db.decisions.insert_one(record)
            # Update case trust_status
            await db.cases.update_one(
                {"case_id": decision_packet["case_id"]},
                {"$set": {
                    "trust_status": decision_packet["trust_status"],
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
        return decision_packet

    @staticmethod
    async def get_latest_decision(case_id: str) -> Optional[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            doc = await db.decisions.find_one(
                {"case_id": case_id},
                {"_id": 0},
                sort=[("created_at", -1)]
            )
            if doc and "packet" in doc:
                return doc["packet"]
        return None

    # ----------------------------------------------------
    # REVIEWS
    # ----------------------------------------------------
    @staticmethod
    async def add_review(review_data: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            review_data.setdefault("created_at", datetime.utcnow().isoformat())
            await db.reviews.insert_one(review_data)
            await db.cases.update_one(
                {"case_id": review_data["case_id"]},
                {"$set": {"status": f"RESOLVED_{review_data['action_taken']}"}}
            )
        return review_data

    @staticmethod
    async def list_reviews(case_id: str) -> List[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            cursor = db.reviews.find({"case_id": case_id}, {"_id": 0})
            return await cursor.to_list(length=50)
        return []

    # ----------------------------------------------------
    # CONNECTORS
    # ----------------------------------------------------
    @staticmethod
    async def save_connector(connector_data: Dict[str, Any]) -> Dict[str, Any]:
        db = mongo_db.db
        if db is not None:
            connector_data.setdefault("created_at", datetime.utcnow().isoformat())
            await db.connectors.update_one(
                {"connector_id": connector_data["connector_id"]},
                {"$set": connector_data},
                upsert=True
            )
        return connector_data

    @staticmethod
    async def list_connectors() -> List[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            cursor = db.connectors.find({}, {"_id": 0})
            return await cursor.to_list(length=50)
        return []

    @staticmethod
    async def get_connector(connector_id: str) -> Optional[Dict[str, Any]]:
        db = mongo_db.db
        if db is not None:
            return await db.connectors.find_one({"connector_id": connector_id}, {"_id": 0})
        return None

repo = Repository()
