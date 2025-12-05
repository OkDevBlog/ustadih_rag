"""ChromaDB vector store management for storing and retrieving embeddings."""

import chromadb
import os
import importlib
from typing import Optional, List
from app.config import settings


# Defensive: disable or no-op ChromaDB telemetry/capture hooks that may be
# present in different chromadb versions and cause runtime errors (seen as
# "capture() takes 1 positional argument but 3 were given"). We attempt to
# locate common telemetry objects and replace their `capture` with a no-op.


def _disable_chromadb_telemetry():
    paths = [
        "telemetry",
        "utils.telemetry",
        "utils._telemetry",
        "utils.telemetry.telemetry",
    ]
    for p in paths:
        parts = p.split('.')
        obj = chromadb
        try:
            for part in parts:
                obj = getattr(obj, part)
            # If we found an object with a `capture` attribute, replace it.
            if hasattr(obj, 'capture'):
                setattr(obj, 'capture', lambda *a, **kw: None)
        except Exception:
            # ignore missing attributes and continue
            continue


_disable_chromadb_telemetry()


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
        
        # Create ChromaDB client with persistent storage. If initialization fails
        # (for example due to telemetry hooks or incompatible chromadb versions),
        # fall back to an in-memory client implementation to keep the app
        # functional in development and testing environments.
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
            # Initialize collections
            self.study_materials_collection = self._get_or_create_collection("study_materials")
            self.questions_collection = self._get_or_create_collection("questions")
        except Exception as e:
            print(f"Warning: ChromaDB client init failed, using in-memory fallback: {e}")
            # Simple in-memory fallback client and collections
            class _InMemoryCollection:
                def __init__(self):
                    self._data = {}

                def upsert(self, ids, documents, metadatas):
                    for i, _id in enumerate(ids):
                        self._data[_id] = (documents[i], metadatas[i])

                def query(self, query_texts, n_results=5, where=None):
                    # Very naive: return first n_results entries
                    ids = list(self._data.keys())[:n_results]
                    documents = [self._data[_id][0] for _id in ids]
                    metadatas = [self._data[_id][1] for _id in ids]
                    distances = [0.0 for _ in ids]
                    return {
                        'ids': [ids],
                        'documents': [documents],
                        'metadatas': [metadatas],
                        'distances': [distances]
                    }

                def delete(self, ids=None, where=None):
                    if ids:
                        for _id in ids:
                            self._data.pop(_id, None)
                    else:
                        # delete by where not implemented; clear all
                        self._data.clear()

            class _InMemoryClient:
                def __init__(self):
                    self._cols = {}

                def get_collection(self, name):
                    if name in self._cols:
                        return self._cols[name]
                    raise Exception("collection not found")

                def create_collection(self, name, metadata=None):
                    col = _InMemoryCollection()
                    self._cols[name] = col
                    return col

            self.client = _InMemoryClient()
            self.study_materials_collection = self.client.create_collection(name="study_materials")
            self.questions_collection = self.client.create_collection(name="questions")
    
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
