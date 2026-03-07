import time
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction

def benchmark():
    ef = PhoBERTEmbeddingFunction()
    texts = [
        "Triệu chứng đau đầu là gì?",
        "Cách điều trị bệnh sốt xuất huyết",
        "Bệnh tiểu đường có nguy hiểm không?",
        "Làm sao để phòng ngừa cảm cúm?",
        "Dấu hiệu của bệnh viêm phổi"
    ]
    
    print(f"Benchmarking {len(texts)} texts...")
    
    # Sequential
    start = time.time()
    for text in texts:
        ef([text])
    sequential_time = time.time() - start
    print(f"Sequential time: {sequential_time:.4f}s")
    
    # Batch
    start = time.time()
    ef(texts)
    batch_time = time.time() - start
    print(f"Batch time: {batch_time:.4f}s")
    
    improvement = (sequential_time - batch_time) / sequential_time * 100
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    benchmark()
