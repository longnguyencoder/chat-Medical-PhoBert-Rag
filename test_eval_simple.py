import sys
import os
import time

print("Starting simple test...", flush=True)

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print("Importing services...", flush=True)
try:
    from src.services.medical_chatbot_service import (
        extract_user_intent_and_features,
        combined_search_with_filters,
        generate_natural_response
    )
    print("Imports successful!", flush=True)
except Exception as e:
    print(f"Import failed: {e}", flush=True)
    sys.exit(1)

question = "Triệu chứng của bệnh sốt xuất huyết là gì?"
print(f"Processing question: {question}", flush=True)

try:
    # 1. Extract Intent
    print("Extracting intent...", flush=True)
    intent_data = extract_user_intent_and_features(question)
    print(f"Intent extracted: {intent_data.get('intent')}", flush=True)
    
    # 2. Search
    print("Searching...", flush=True)
    extracted_features = intent_data.get('extracted_features', {})
    search_result = combined_search_with_filters(question, extracted_features)
    print(f"Search found {len(search_result.get('results', []))} results", flush=True)
    
    # 3. Generate Response
    print("Generating response...", flush=True)
    response_data = generate_natural_response(
        question, 
        search_result.get('results', []), 
        extracted_features
    )
    print("Response generated!", flush=True)
    print(f"Answer: {response_data.get('answer')[:100]}...", flush=True)

except Exception as e:
    print(f"Error during processing: {e}", flush=True)
