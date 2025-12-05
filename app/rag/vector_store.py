"""ChromaDB vector store management for storing and retrieving embeddings."""

import chromadb
import os
from typing import Optional, List
from app.config import settings


class VectorStore:
    """Manages ChromaDB collections for storing document embeddings."""
    
    def __init__(self, persist_dir: str = "./chromadb_data"):
        """
        Initialize ChromaDB client with persistence.
        
        Args:
            persist_dir: Directory to persist ChromaDB data
        """
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Create ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Initialize collections
        self.study_materials_collection = self._get_or_create_collection("study_materials")
        self.questions_collection = self._get_or_create_collection("questions")
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create a new one."""
        try:
            collection = self.client.get_collection(name=name)
        except:
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return collection
    
    def add_study_material(self, material_id: str, content: str, metadata: dict = None) -> str:
        """
        Add study material embedding to vector store.
        
        Args:
            material_id: Unique identifier for the material
            content: Text content to embed
            metadata: Additional metadata for filtering
            
        Returns:
            material_id: The ID of stored material
        """
        if metadata is None:
            metadata = {}
        
        self.study_materials_collection.upsert(
            ids=[material_id],
            documents=[content],
            metadatas=[metadata]
        )
        return material_id
    
    def add_question(self, question_id: str, content: str, metadata: dict = None) -> str:
        """
        Add question embedding to vector store.
        
        Args:
            question_id: Unique identifier for the question
            content: Question text to embed
            metadata: Additional metadata for filtering
            
        Returns:
            question_id: The ID of stored question
        """
        if metadata is None:
            metadata = {}
        
        self.questions_collection.upsert(
            ids=[question_id],
            documents=[content],
            metadatas=[metadata]
        )
        return question_id
    
    def search_study_materials(self, query: str, top_k: int = 5, 
                               where_filter: dict = None) -> List[dict]:
        """
        Search study materials by semantic similarity.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            where_filter: Optional metadata filter
            
        Returns:
            List of matched materials with scores
        """
        results = self.study_materials_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )
        
        return self._format_search_results(results)
    
    def search_questions(self, query: str, top_k: int = 5,
                        where_filter: dict = None) -> List[dict]:
        """
        Search questions by semantic similarity.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            where_filter: Optional metadata filter
            
        Returns:
            List of matched questions with scores
        """
        results = self.questions_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )
        
        return self._format_search_results(results)
    
    def _format_search_results(self, results: dict) -> List[dict]:
        """Format ChromaDB query results into list of dictionaries."""
        formatted = []
        
        if not results or not results['ids'] or len(results['ids'][0]) == 0:
            return formatted
        
        for i, doc_id in enumerate(results['ids'][0]):
            formatted.append({
                'id': doc_id,
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else 0
            })
        
        return formatted
    
    def delete_study_material(self, material_id: str) -> bool:
        """Delete a study material from vector store."""
        try:
            self.study_materials_collection.delete(ids=[material_id])
            return True
        except:
            return False
    
    def delete_question(self, question_id: str) -> bool:
        """Delete a question from vector store."""
        try:
            self.questions_collection.delete(ids=[question_id])
            return True
        except:
            return False
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all items from a collection."""
        try:
            if collection_name == "study_materials":
                self.study_materials_collection.delete(where={})
            elif collection_name == "questions":
                self.questions_collection.delete(where={})
            return True
        except:
            return False


# Global vector store instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
