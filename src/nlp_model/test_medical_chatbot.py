import os
import sys
import json
import time
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response
)

def load_test_questions() -> List[Dict]:
    """Load test questions from JSON file"""
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    qa_file = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'sample_medical_qa.json')
    
    with open(qa_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_single_question(question_data: Dict, verbose: bool = True) -> Dict:
    """Test chatbot with a single question"""
    question = question_data['question']
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"Expected Disease: {question_data.get('expected_disease', 'N/A')}")
        print(f"Category: {question_data.get('category', 'N/A')}")
        print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Step 1: Extract intent and features
        extraction_result = extract_user_intent_and_features(question)
        
        if verbose:
            print(f"\n[1] Intent Extraction:")
            print(f"    Intent: {extraction_result.get('intent')}")
            print(f"    Features: {extraction_result.get('extracted_features')}")
        
        # Step 2: Search for medical info
        search_result = combined_search_with_filters(
            question,
            extraction_result.get('extracted_features', {})
        )
        
        if verbose:
            print(f"\n[2] Search Results:")
            print(f"    Found: {search_result.get('total_found', 0)} results")
            
            if search_result.get('results'):
                top_result = search_result['results'][0]
                print(f"    Top Match: {top_result['metadata'].get('disease_name')}")
                print(f"    Relevance Score: {top_result.get('relevance_score', 0):.3f}")
                print(f"    Score Breakdown: {top_result.get('score_breakdown')}")
                print(f"    Confidence: {top_result.get('confidence')}")
        
        # Step 3: Generate response
        response = generate_natural_response(
            question,
            search_result.get('results', []),
            extraction_result.get('extracted_features', {})
        )
        
        elapsed_time = time.time() - start_time
        
        if verbose:
            print(f"\n[3] Generated Response:")
            print(f"    Confidence: {response.get('confidence')}")
            print(f"    Avg Relevance: {response.get('avg_relevance_score', 0):.3f}")
            print(f"\n{'-'*80}")
            print("ANSWER:")
            print(f"{'-'*80}")
            print(response.get('answer'))
            print(f"{'-'*80}")
            print(f"\nResponse Time: {elapsed_time:.2f}s")
        
        return {
            'question_id': question_data.get('id'),
            'question': question,
            'expected_disease': question_data.get('expected_disease'),
            'found_disease': search_result['results'][0]['metadata'].get('disease_name') if search_result.get('results') else None,
            'relevance_score': search_result['results'][0].get('relevance_score') if search_result.get('results') else 0,
            'confidence': response.get('confidence'),
            'response_time': elapsed_time,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error testing question: {str(e)}", exc_info=True)
        return {
            'question_id': question_data.get('id'),
            'question': question,
            'success': False,
            'error': str(e)
        }

def run_full_test_suite():
    """Run tests on all sample questions"""
    print("\n" + "="*80)
    print("MEDICAL CHATBOT TEST SUITE")
    print("="*80)
    
    # Load test questions
    test_questions = load_test_questions()
    print(f"\nLoaded {len(test_questions)} test questions")
    
    # Run tests
    results = []
    successful = 0
    total_time = 0
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n\n{'#'*80}")
        print(f"TEST {i}/{len(test_questions)}")
        print(f"{'#'*80}")
        
        result = test_single_question(q, verbose=True)
        results.append(result)
        
        if result['success']:
            successful += 1
            total_time += result.get('response_time', 0)
        
        # Add delay to avoid rate limiting
        if i < len(test_questions):
            time.sleep(1)
    
    # Print summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Questions: {len(test_questions)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(test_questions) - successful}")
    print(f"Success Rate: {(successful/len(test_questions)*100):.1f}%")
    print(f"Average Response Time: {(total_time/successful if successful > 0 else 0):.2f}s")
    
    # Confidence distribution
    confidence_counts = {}
    for r in results:
        if r['success']:
            conf = r.get('confidence', 'unknown')
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    print(f"\nConfidence Distribution:")
    for conf, count in confidence_counts.items():
        print(f"  {conf}: {count} ({count/successful*100:.1f}%)")
    
    # Save results
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results_file = os.path.join(workspace_root, 'src', 'nlp_model', 'data', 'test_results.json')
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(test_questions),
                'successful': successful,
                'failed': len(test_questions) - successful,
                'avg_response_time': total_time/successful if successful > 0 else 0,
                'confidence_distribution': confidence_counts
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Detailed results saved to: {results_file}")
    print("="*80 + "\n")

def test_quick():
    """Quick test with a few questions"""
    print("\n" + "="*80)
    print("QUICK TEST - Top 5 Questions")
    print("="*80)
    
    test_questions = load_test_questions()[:5]
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n[{i}] Testing: {q['question']}")
        result = test_single_question(q, verbose=False)
        
        if result['success']:
            print(f"    ✓ Found: {result.get('found_disease')}")
            print(f"    ✓ Score: {result.get('relevance_score', 0):.3f}")
            print(f"    ✓ Time: {result.get('response_time', 0):.2f}s")
        else:
            print(f"    ✗ Error: {result.get('error')}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Medical Chatbot')
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                       help='Test mode: quick (5 questions) or full (all questions)')
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        test_quick()
    else:
        run_full_test_suite()
