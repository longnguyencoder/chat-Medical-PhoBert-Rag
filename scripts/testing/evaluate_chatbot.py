import pandas as pd
import os
import sys
import time
import csv
from datetime import datetime
from tqdm import tqdm

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.services.medical_chatbot_service import (
    extract_user_intent_and_features,
    combined_search_with_filters,
    generate_natural_response
)

def evaluate_chatbot(input_csv_path, output_csv_path):
    """
    Run chatbot evaluation on a list of questions.
    """
    print(f"Loading questions from: {input_csv_path}")
    
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found: {input_csv_path}")
        return

    try:
        df = pd.read_csv(input_csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    results = []
    
    print(f"Starting evaluation of {len(df)} questions...")
    
    for index, row in tqdm(df.iterrows(), total=len(df)):
        question = str(row['question'])
        question_id = row.get('id', index + 1)
        
        start_time = time.time()
        
        try:
            # 1. Extract Intent
            intent_data = extract_user_intent_and_features(question)
            extracted_features = intent_data.get('extracted_features', {})
            
            # 2. Search
            search_result = combined_search_with_filters(question, extracted_features)
            
            # 3. Generate Response
            response_data = generate_natural_response(
                question, 
                search_result.get('results', []), 
                extracted_features
            )
            
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            
            # Extract key metrics
            answer = response_data.get('answer', '')
            confidence = response_data.get('confidence', 'unknown')
            sources = response_data.get('sources', [])
            
            top_source = "None"
            top_score = 0.0
            
            if sources:
                top_source = sources[0]['metadata'].get('disease_name', 'Unknown')
                top_score = sources[0].get('relevance_score', 0.0)
            
            results.append({
                'id': question_id,
                'question': question,
                'chatbot_answer': answer,
                'top_source_found': top_source,
                'relevance_score': top_score,
                'confidence_level': confidence,
                'response_time_sec': duration,
                'user_rating_1_to_5': '', # Placeholder for user
                'user_comments': ''       # Placeholder for user
            })
            
        except Exception as e:
            print(f"Error processing question '{question}': {e}")
            results.append({
                'id': question_id,
                'question': question,
                'chatbot_answer': f"ERROR: {str(e)}",
                'top_source_found': 'ERROR',
                'relevance_score': 0,
                'confidence_level': 'error',
                'response_time_sec': 0,
                'user_rating_1_to_5': '',
                'user_comments': ''
            })

    # Save results
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    
    print(f"\nEvaluation complete!")
    print(f"Results saved to: {output_csv_path}")
    print(f"Total questions processed: {len(results)}")

if __name__ == "__main__":
    # Setup file logging
    log_file = os.path.join(current_dir, 'evaluation_debug.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Starting evaluation at {datetime.now()}\n")
    
    def log(msg):
        print(msg)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{msg}\n")

    try:
        # Define paths
        input_file = os.path.join(current_dir, 'data', 'test_questions.csv')
        
        # Create timestamped output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(current_dir, f'evaluation_report_{timestamp}.csv')
        
        log(f"Input file: {input_file}")
        log(f"Output file: {output_file}")
        
        evaluate_chatbot(input_file, output_file)
        log("Evaluation finished successfully")
        
    except Exception as e:
        log(f"CRITICAL ERROR: {str(e)}")
        import traceback
        log(traceback.format_exc())
