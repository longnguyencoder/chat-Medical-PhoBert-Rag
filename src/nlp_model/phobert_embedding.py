import torch
from chromadb import EmbeddingFunction, Documents, Embeddings
from transformers import AutoModel, AutoTokenizer
from typing import List
import logging

logger = logging.getLogger(__name__)

class PhoBERTEmbeddingFunction(EmbeddingFunction):
    """
    PhoBERT embedding function optimized for Vietnamese medical text.
    Uses vinai/phobert-base model with mean pooling.
    """
    
    def __init__(self, model_name="vinai/phobert-base", device=None, max_length=256):
        """
        Initialize PhoBERT embedding function.
        
        Args:
            model_name: HuggingFace model name (default: vinai/phobert-base)
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
            max_length: Maximum sequence length for tokenization
        """
        logger.info(f"Initializing PhoBERT embedding function with model: {model_name}")
        
        self.model_name = model_name
        self.max_length = max_length
        
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Using device: {self.device}")
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info(f"✓ PhoBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load PhoBERT model: {str(e)}")
            raise

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for input documents.
        
        Args:
            input: List of text documents
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        try:
            if not input:
                logger.warning("Empty input received")
                return []
            
            # Tokenize sentences with proper padding and truncation
            encoded_input = self.tokenizer(
                input, 
                padding=True, 
                truncation=True, 
                return_tensors='pt', 
                max_length=self.max_length
            )
            
            # Move to device
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}

            # Compute token embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)

            # Perform mean pooling
            embeddings = self._mean_pooling(
                model_output.last_hidden_state,
                encoded_input['attention_mask']
            )
            
            # Convert to list and return
            return embeddings.cpu().numpy().tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _mean_pooling(self, token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Perform mean pooling on token embeddings.
        
        Args:
            token_embeddings: Token-level embeddings from the model
            attention_mask: Attention mask to ignore padding tokens
            
        Returns:
            Sentence-level embeddings
        """
        # Expand attention mask to match embedding dimensions
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # Sum embeddings and mask
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        # Calculate mean
        return sum_embeddings / sum_mask
    
    def embed_batch(self, texts: List[str], batch_size: int = 8) -> Embeddings:
        """
        Generate embeddings for a large list of texts in batches.
        Useful for processing large datasets efficiently.
        
        Args:
            texts: List of text documents
            batch_size: Number of texts to process at once
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self(batch)
            all_embeddings.extend(batch_embeddings)
            
            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"Processed {i + len(batch)}/{len(texts)} documents")
        
        return all_embeddings

