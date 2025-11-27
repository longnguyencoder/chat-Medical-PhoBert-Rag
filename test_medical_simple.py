"""
Simple test script for medical chatbot without running full server.
Works with Python 3.14 if you can install the core dependencies.
"""

import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_medical_chatbot():
    """Test medical chatbot with a simple question"""
    
    print("="*60)
    print("MEDICAL CHATBOT SIMPLE TEST")
    print("="*60)
    
    try:
        # Import medical chatbot service
        from src.services.medical_chatbot_service import (
            extract_user_intent_and_features,
            combined_search_with_filters,
            generate_natural_response
        )
        
        # Test question
        question = "Triệu chứng của cảm cúm là gì?"
        print(f"\nQuestion: {question}\n")
        
        # Step 1: Extract features
        print("[1] Extracting medical features...")
        extraction = extract_user_intent_and_features(question)
        print(f"    Intent: {extraction.get('intent')}")
        print(f"    Features: {extraction.get('extracted_features')}")
        
        # Step 2: Search
        print("\n[2] Searching medical database...")
        search_result = combined_search_with_filters(
            question, 
            extraction.get('extracted_features', {})
        )
        
        if search_result.get('success'):
            results = search_result.get('results', [])
            print(f"    Found: {len(results)} results")
            
            if results:
                top = results[0]
                print(f"    Top match: {top['metadata'].get('disease_name')}")
                print(f"    Relevance: {top.get('relevance_score', 0):.3f}")
        
            # Step 3: Generate response
            print("\n[3] Generating response...")
            response = generate_natural_response(
                question,
                results,
                extraction.get('extracted_features', {})
            )
            
            print("\n" + "="*60)
            print("ANSWER:")
            print("="*60)
            print(response.get('answer'))
            print("="*60)
            print(f"\nConfidence: {response.get('confidence')}")
            
        else:
            print(f"    Error: {search_result.get('message')}")
        
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\nYou need to install:")
        print("  pip install chromadb transformers torch openai")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_medical_chatbot()
