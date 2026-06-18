import os
import logging
from typing import List, Dict, Any, Optional, cast
import chromadb

logger = logging.getLogger(__name__)


class ChromaService:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Locate inside artifacts/api-server/db/chroma_db to keep things unified
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "db", "chroma_db")

        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = "cybershield_kb"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB initialized at: {db_path}")

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ):
        """Insert or update chunks inside ChromaDB collection."""
        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=cast(Any, embeddings),
                metadatas=cast(Any, metadatas),
            )
            logger.info(f"Upserted {len(ids)} documents to ChromaDB.")
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            raise

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform similarity search with optional metadata filtering."""
        try:
            results = self.collection.query(
                query_embeddings=cast(Any, [query_embedding]),
                n_results=n_results,
                where=where,
            )
            return cast(Dict[str, Any], results)
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

    def delete_all(self):
        """Reset collection by deleting and recreating it."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection cleared.")
        except Exception as e:
            logger.error(f"Failed to reset ChromaDB: {e}")
            raise
