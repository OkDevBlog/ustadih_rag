"""RAG (Retrieval-Augmented Generation) pipeline for intelligent tutoring responses."""

import os
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from app.config import settings
from app.rag.vector_store import get_vector_store
from app.rag.embeddings import get_embedding_service


class RAGPipeline:
    """Handles the complete RAG pipeline: retrieval, augmentation, and generation."""
    
    def __init__(self):
        """Initialize RAG pipeline with vector store and embedding service."""
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()
        
        # Configure Gemini API
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def retrieve_context(self, query: str, subject: Optional[str] = None,
                        top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant study materials and related questions.
        
        Args:
            query: User query or question
            subject: Optional filter by subject
            top_k: Number of top results to retrieve
            
        Returns:
            List of relevant context documents
        """
        # Search for similar study materials
        where_filter = {"subject": subject} if subject else None
        
        materials = self.vector_store.search_study_materials(
            query=query,
            top_k=top_k,
            where_filter=where_filter
        )
        
        # Search for similar questions for reference
        questions = self.vector_store.search_questions(
            query=query,
            top_k=min(3, top_k),
            where_filter=where_filter
        )
        
        context = {
            "materials": materials,
            "reference_questions": questions
        }
        
        return context
    
    def format_context_for_prompt(self, context: Dict) -> str:
        """
        Format retrieved context into a structured prompt.
        
        Args:
            context: Context dictionary from retrieve_context
            
        Returns:
            Formatted string for inclusion in LLM prompt
        """
        prompt_parts = []
        
        if context.get("materials"):
            prompt_parts.append("=== STUDY MATERIALS ===")
            for material in context["materials"]:
                prompt_parts.append(f"\nTopic: {material['metadata'].get('topic', 'N/A')}")
                prompt_parts.append(f"Content: {material['content'][:500]}...")  # Truncate for brevity
        
        if context.get("reference_questions"):
            prompt_parts.append("\n\n=== REFERENCE QUESTIONS & ANSWERS ===")
            for question in context["reference_questions"]:
                prompt_parts.append(f"Q: {question['content'][:200]}...")
        
        return "\n".join(prompt_parts)
    
    def generate_response(self, query: str, context: Dict, 
                         system_prompt: Optional[str] = None) -> str:
        """
        Generate response using Gemini with retrieved context.
        
        Args:
            query: User question
            context: Retrieved context from vector store
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated response from LLM
        """
        if not self.model:
            # Fallback response if Gemini is not configured
            return self._generate_fallback_response(query, context)
        
        # Format context for the prompt
        context_text = self.format_context_for_prompt(context)
        
        # Build the complete prompt
        if system_prompt is None:
            system_prompt = """You are an expert educational tutor for Iraqi students. 
Provide clear, helpful, and educational responses in both Arabic and English as appropriate.
Focus on explaining concepts thoroughly and building understanding.
Use the provided study materials and reference questions to inform your response.
Be encouraging and supportive."""
        
        full_prompt = f"""{system_prompt}

CONTEXT FROM STUDY MATERIALS:
{context_text}

STUDENT QUESTION:
{query}

RESPONSE:"""
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: Dict) -> str:
        """
        Generate a fallback response when LLM is unavailable.
        
        Args:
            query: User question
            context: Retrieved context
            
        Returns:
            Response based on retrieved materials
        """
        response_parts = ["Based on available study materials:"]
        
        if context.get("materials"):
            for material in context["materials"][:2]:  # Use top 2 materials
                response_parts.append(f"\n{material['content'][:300]}...")
        
        if not context.get("materials"):
            response_parts.append("\nSorry, I couldn't find relevant materials to answer your question. ")
            response_parts.append("Please try rephrasing your question or check if the topic is covered in our database.")
        
        return "\n".join(response_parts)
    
    def answer_question(self, query: str, subject: Optional[str] = None,
                       user_id: Optional[str] = None) -> Dict:
        """
        Complete pipeline: retrieve -> augment -> generate.
        
        Args:
            query: User question
            subject: Optional subject filter
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary with question, retrieved context, and generated answer
        """
        # Retrieve context
        context = self.retrieve_context(query, subject=subject, top_k=5)
        
        # Generate response
        answer = self.generate_response(query, context)
        
        result = {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "type": "study_material",
                    "id": m["id"],
                    "title": m["metadata"].get("title", "Unknown")
                }
                for m in context.get("materials", [])
            ],
            "retrieved_context": context
        }
        
        return result
    
    def add_study_material(self, material_id: str, title: str, content: str,
                          topic: str, subject: str, difficulty: str = "intermediate") -> bool:
        """
        Add study material to RAG system.
        
        Args:
            material_id: Unique ID for material
            title: Material title
            content: Material content
            topic: Topic classification
            subject: Subject classification
            difficulty: Difficulty level
            
        Returns:
            Success status
        """
        try:
            metadata = {
                "title": title,
                "topic": topic,
                "subject": subject,
                "difficulty": difficulty
            }
            self.vector_store.add_study_material(material_id, content, metadata)
            return True
        except Exception as e:
            print(f"Error adding study material: {e}")
            return False
    
    def add_question(self, question_id: str, question_text: str, answer_text: str,
                    topic: str, subject: str, difficulty: str = "intermediate") -> bool:
        """
        Add question to RAG system.
        
        Args:
            question_id: Unique ID for question
            question_text: Question text
            answer_text: Answer text
            topic: Topic classification
            subject: Subject classification
            difficulty: Difficulty level
            
        Returns:
            Success status
        """
        try:
            # Combine question and answer for better semantic search
            combined_text = f"{question_text}\n\nAnswer: {answer_text}"
            
            metadata = {
                "question": question_text,
                "answer": answer_text,
                "topic": topic,
                "subject": subject,
                "difficulty": difficulty
            }
            self.vector_store.add_question(question_id, combined_text, metadata)
            return True
        except Exception as e:
            print(f"Error adding question: {e}")
            return False


# Global RAG pipeline instance
_pipeline_instance = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the global RAG pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
