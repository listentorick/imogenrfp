import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import os
from sqlalchemy.orm import Session
from models import StandardAnswer, Tenant

class RAGService:
    def __init__(self):
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        
        try:
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(allow_reset=True)
            )
            self.client.heartbeat()  # Test connection
        except Exception as e:
            print(f"Warning: Could not connect to ChromaDB at {self.chroma_host}:{self.chroma_port}: {e}")
            self.client = None
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_tenant_collection_name(self, tenant_id: str) -> str:
        return f"tenant_{tenant_id.replace('-', '_')}"
    
    def create_tenant_collection(self, tenant_id: str):
        if not self.is_available():
            return None
        
        collection_name = self.get_tenant_collection_name(tenant_id)
        try:
            collection = self.client.get_collection(collection_name)
            return collection
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"tenant_id": tenant_id}
            )
            return collection
    
    def add_standard_answer(self, tenant_id: str, answer_id: str, question: str, answer: str, tags: List[str] = None):
        collection = self.create_tenant_collection(tenant_id)
        
        text_to_embed = f"{question} {answer}"
        if tags:
            text_to_embed += f" {' '.join(tags)}"
        
        embedding = self.model.encode([text_to_embed])[0].tolist()
        
        metadata = {
            "question": question,
            "answer": answer,
            "tags": tags or [],
            "answer_id": answer_id
        }
        
        collection.add(
            ids=[answer_id],
            embeddings=[embedding],
            documents=[text_to_embed],
            metadatas=[metadata]
        )
    
    def update_standard_answer(self, tenant_id: str, answer_id: str, question: str, answer: str, tags: List[str] = None):
        collection = self.create_tenant_collection(tenant_id)
        
        text_to_embed = f"{question} {answer}"
        if tags:
            text_to_embed += f" {' '.join(tags)}"
        
        embedding = self.model.encode([text_to_embed])[0].tolist()
        
        metadata = {
            "question": question,
            "answer": answer,
            "tags": tags or [],
            "answer_id": answer_id
        }
        
        collection.update(
            ids=[answer_id],
            embeddings=[embedding],
            documents=[text_to_embed],
            metadatas=[metadata]
        )
    
    def delete_standard_answer(self, tenant_id: str, answer_id: str):
        collection = self.create_tenant_collection(tenant_id)
        collection.delete(ids=[answer_id])
    
    def search_similar_answers(self, tenant_id: str, question: str, n_results: int = 5) -> List[Dict[str, Any]]:
        collection = self.create_tenant_collection(tenant_id)
        
        question_embedding = self.model.encode([question])[0].tolist()
        
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        similar_answers = []
        for i in range(len(results['ids'][0])):
            similar_answers.append({
                "answer_id": results['ids'][0][i],
                "question": results['metadatas'][0][i]['question'],
                "answer": results['metadatas'][0][i]['answer'],
                "tags": results['metadatas'][0][i]['tags'],
                "similarity_score": 1 - results['distances'][0][i],
                "distance": results['distances'][0][i]
            })
        
        return similar_answers
    
    def generate_rfp_answer(self, tenant_id: str, rfp_question: str, context_answers: List[Dict] = None) -> str:
        if not context_answers:
            context_answers = self.search_similar_answers(tenant_id, rfp_question, n_results=3)
        
        if not context_answers:
            return "No relevant information found in the knowledge base. Please provide a manual answer."
        
        best_match = context_answers[0]
        
        if best_match['similarity_score'] > 0.8:
            return best_match['answer']
        elif best_match['similarity_score'] > 0.6:
            combined_answer = f"Based on similar questions:\n\n{best_match['answer']}\n\n"
            combined_answer += "Please review and modify as needed for this specific question."
            return combined_answer
        else:
            suggestions = []
            for match in context_answers[:2]:
                suggestions.append(f"- {match['question']}: {match['answer'][:200]}...")
            
            return f"No direct match found. Here are some related answers that might help:\n\n" + "\n\n".join(suggestions)
    
    def bulk_index_standard_answers(self, db: Session, tenant_id: str):
        answers = db.query(StandardAnswer).filter(
            StandardAnswer.tenant_id == tenant_id
        ).all()
        
        collection = self.create_tenant_collection(tenant_id)
        
        for answer in answers:
            self.add_standard_answer(
                tenant_id=tenant_id,
                answer_id=str(answer.id),
                question=answer.question,
                answer=answer.answer,
                tags=answer.tags or []
            )
        
        return len(answers)

rag_service = RAGService()