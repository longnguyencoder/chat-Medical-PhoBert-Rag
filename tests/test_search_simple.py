import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.medical_chatbot_service import combined_search_with_filters

# Test search
question = "Triệu chứng của cảm cúm là gì?"
print(f"Testing search with: {question}\n")

result = combined_search_with_filters(
    question=question,
    extracted_features={},
    n_results=5
)

print("Result:")
print(f"Success: {result.get('success')}")
print(f"Total found: {result.get('total_found')}")
print(f"Message: {result.get('message', 'N/A')}")

if result.get('results'):
    print(f"\nTop result:")
    top = result['results'][0]
    print(f"  Disease: {top['metadata'].get('disease_name', top['metadata'].get('question', 'N/A'))}")
    print(f"  Score: {top['relevance_score']}")
    print(f"  Doc type: {top['metadata'].get('doc_type', 'N/A')}")
