from transformers import AutoTokenizer, AutoModel
import time

print("Start loading...")
try:
    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
    model = AutoModel.from_pretrained("vinai/phobert-base-v2")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error: {e}")
