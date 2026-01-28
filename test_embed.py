import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print("Importing PhoBERTEmbeddingFunction...")
try:
    from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
    print("Initializing...")
    ef = PhoBERTEmbeddingFunction()
    print("Embedding...")
    emb = ef(["test"])
    print(f"Success. Dim: {len(emb[0])}")
except Exception as e:
    print(f"Error: {e}")
