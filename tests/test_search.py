import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.medical_chatbot_service import combined_search_with_filters, extract_user_intent_and_features

# Configure logging to see our debug prints
logging.basicConfig(level=logging.INFO)

def test_search():
    question = "Triệu chứng của cảm cúm là gì?"
    print(f"\nTesting search with question: {question}")
    
    # 1. Extract features (mocking or real)
    print("Extracting features...")
    features = extract_user_intent_and_features(question)
    print(f"Extracted features: {features}")
    
    # 2. Perform search
    print("\nPerforming search...")
    result = combined_search_with_filters(
        question=question,
        extracted_features=features['extracted_features'],
        n_results=5
    )
    
    print("\nSearch Results:")
    print(f"Success: {result.get('success')}")
    print(f"Total found: {result.get('total_found')}")
    
    if result.get('results'):
        for i, res in enumerate(result['results']):
            print(f"\nResult {i+1}:")
            print(f"  Disease: {res['metadata'].get('disease_name')}")
            print(f"  Score: {res['relevance_score']}")
            print(f"  Breakdown: {res['score_breakdown']}")
    else:
        print("No results found.")

if __name__ == "__main__":
    test_search()
