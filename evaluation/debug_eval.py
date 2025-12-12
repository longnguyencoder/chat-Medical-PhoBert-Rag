import sys
print("1. Starting imports...", flush=True)
import os
import json
print("2. Basic imports done", flush=True)
import pandas as pd
print("3. Pandas imported", flush=True)
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
print("4. PhoBERT imported", flush=True)
from src.services.medical_chatbot_service import hybrid_search
print("5. Service imported", flush=True)
print("Ready to run evaluation...", flush=True)
