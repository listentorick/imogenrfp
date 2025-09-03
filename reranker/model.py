import torch
from transformers import AutoTokenizer, AutoModel
import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class Qwen3Reranker:
    def __init__(self, model_name: str = "Qwen/Qwen3-Reranker-0.6B"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
    def load_model(self):
        """Load the Qwen4-reranker model"""
        try:
            logger.info(f"Loading Qwen3-reranker model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Qwen3-reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def rerank(self, query: str, passages: List[str], top_k: int = 5) -> List[Tuple[str, float, int]]:
        """
        Rerank passages based on relevance to query using Qwen3 reranker format
        
        Returns:
            List of tuples (text, score, original_index) sorted by relevance score
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if not passages:
            return []
        
        scores = []
        
        # Task instruction for reranking
        task = "Given a query, find relevant passages"
        
        with torch.no_grad():
            for i, passage in enumerate(passages):
                try:
                    # Format input according to Qwen3 reranker format
                    formatted_input = f"<Instruct>: {task}\n<Query>: {query}\n<Document>: {passage}"
                    
                    # Tokenize
                    inputs = self.tokenizer(
                        formatted_input,
                        truncation=True,
                        padding=True,
                        max_length=512,
                        return_tensors="pt"
                    )
                    
                    # Move to device
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Get embeddings/outputs
                    outputs = self.model(**inputs)
                    
                    # Extract score from last hidden state or pooled output
                    if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                        # Use pooled output if available
                        score_tensor = outputs.pooler_output
                    else:
                        # Use mean of last hidden state
                        score_tensor = outputs.last_hidden_state.mean(dim=1)
                    
                    # Convert to scalar score
                    score = torch.sigmoid(score_tensor).cpu().numpy().item()
                    scores.append((passage, float(score), i))
                    
                except Exception as e:
                    logger.warning(f"Error processing passage {i}: {e}")
                    scores.append((passage, 0.0, i))
        
        # Sort by score (descending) and return top_k
        sorted_results = sorted(scores, key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

# Global reranker instance
reranker = Qwen3Reranker()