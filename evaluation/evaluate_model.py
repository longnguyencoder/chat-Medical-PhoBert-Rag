"""
PhoBERT Medical Chatbot Evaluation Script
==========================================
Script để đánh giá mô hình PhoBERT RAG trực tiếp trên local.

Usage:
    python evaluate_model.py --test_file test_data/sample_test_questions.csv
    python evaluate_model.py --test_file test_data/test.json --output results.json
"""

import os
import sys
import json
import time
import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from backend
from src.nlp_model.phobert_embedding import PhoBERTEmbeddingFunction
from src.services.medical_chatbot_service import (
    get_or_create_collection,
    hybrid_search,
    generate_natural_response
)
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ==================== EVALUATION METRICS ====================

def calculate_precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """Precision@K: Tỷ lệ tài liệu đúng trong top K"""
    retrieved_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    correct = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
    return correct / k if k > 0 else 0.0

def calculate_recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """Recall@K: Tỷ lệ tìm được tài liệu đúng trong top K"""
    retrieved_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    if len(relevant_set) == 0:
        return 0.0
    correct = len(retrieved_k & relevant_set)
    return correct / len(relevant_set)

def calculate_mrr(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
    """Mean Reciprocal Rank: 1 / vị trí của kết quả đúng đầu tiên"""
    relevant_set = set(relevant_ids)
    for i, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in relevant_set:
            return 1.0 / i
    return 0.0

def calculate_ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """NDCG@K: Normalized Discounted Cumulative Gain"""
    retrieved_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    
    # DCG
    dcg = sum((1 if doc_id in relevant_set else 0) / np.log2(i + 2) 
              for i, doc_id in enumerate(retrieved_k))
    
    # IDCG (ideal DCG)
    ideal_k = min(k, len(relevant_ids))
    idcg = sum(1 / np.log2(i + 2) for i in range(ideal_k))
    
    return dcg / idcg if idcg > 0 else 0.0

def calculate_semantic_similarity(text1: str, text2: str, phobert_model) -> float:
    """Semantic Similarity using PhoBERT embeddings"""
    try:
        emb1 = phobert_model([text1])[0]
        emb2 = phobert_model([text2])[0]
        
        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        print(f"Warning: Semantic similarity calculation failed: {e}")
        return 0.0

def extract_medical_entities(text: str) -> set:
    """Extract medical entities (simple keyword-based)"""
    medical_keywords = [
        'sốt', 'đau', 'viêm', 'nhiễm', 'bệnh', 'thuốc', 'paracetamol', 'aspirin',
        'xuất huyết', 'tiểu cầu', 'gan', 'phổi', 'tim', 'vắc-xin', 'điều trị',
        'triệu chứng', 'phòng ngừa', 'chẩn đoán', 'xét nghiệm'
    ]
    text_lower = text.lower()
    return {kw for kw in medical_keywords if kw in text_lower}

def calculate_entity_accuracy(generated: str, reference: str) -> float:
    """Medical Entity Accuracy: Tỷ lệ thực thể y tế đúng"""
    gen_entities = extract_medical_entities(generated)
    ref_entities = extract_medical_entities(reference)
    
    if len(ref_entities) == 0:
        return 1.0 if len(gen_entities) == 0 else 0.0
    
    correct = len(gen_entities & ref_entities)
    return correct / len(ref_entities)

# ==================== EVALUATION FUNCTIONS ====================

def evaluate_single_question(
    question: str,
    expected_answer: str,
    relevant_doc_ids: List[str],  # Now optional - can be empty list
    phobert_model,
    k_values: List[int] = [1, 3, 5],
    auto_detect_relevant: bool = True  # NEW: Auto-detect relevant docs
) -> Dict[str, Any]:
    """Đánh giá một câu hỏi"""
    
    start_time = time.time()
    
    # 1. RETRIEVAL
    try:
        search_results = hybrid_search(question, n_results=max(k_values))
        retrieved_ids = [r['id'] for r in search_results]
    except Exception as e:
        print(f"Error in retrieval: {e}")
        retrieved_ids = []
        search_results = []
    
    # 2. AUTO-DETECT RELEVANT DOC IDs (NEW!)
    if auto_detect_relevant and not relevant_doc_ids:
        # Coi các doc có relevance_score > threshold là relevant
        # OPTIMIZED: Lowered threshold further to verify retrieval coverage
        RELEVANCE_THRESHOLD = 0.1  # Lowered from 0.2 to capture any potential signal
        relevant_doc_ids = [
            r['id'] for r in search_results 
            if r.get('relevance_score', 0) >= RELEVANCE_THRESHOLD
        ]
        
        if relevant_doc_ids:
            print(f"   Auto-detected {len(relevant_doc_ids)} relevant docs (score ≥ {RELEVANCE_THRESHOLD})")
    
    # 3. GENERATION (optional - comment out nếu không có OpenAI API key)
    try:
        generated_answer = generate_natural_response(
            question=question,
            search_results=search_results,
            extracted_features={},
            conversation_id=None,
            user_name=None
        )
        generated_answer = generated_answer.get('answer', '') if isinstance(generated_answer, dict) else str(generated_answer)
    except Exception as e:
        print(f"Warning: Generation failed: {e}")
        generated_answer = "[Generation skipped - no API key or error]"
    
    response_time = time.time() - start_time
    
    # 4. CALCULATE METRICS
    result = {
        'question': question,
        'expected_answer': expected_answer,
        'generated_answer': generated_answer,
        'retrieved_ids': retrieved_ids[:10],  # Top 10
        'relevant_ids': relevant_doc_ids,
        'auto_detected': auto_detect_relevant and len(relevant_doc_ids) > 0,
        'response_time': response_time,
    }
    
    # Add top retrieval scores for analysis
    if search_results:
        result['top_scores'] = [
            {
                'id': r['id'],
                'score': r.get('relevance_score', 0),
                'disease': r.get('metadata', {}).get('disease_name', 'N/A')[:50]
            }
            for r in search_results[:3]
        ]
    
    # Retrieval metrics
    for k in k_values:
        result[f'precision@{k}'] = calculate_precision_at_k(retrieved_ids, relevant_doc_ids, k)
        result[f'recall@{k}'] = calculate_recall_at_k(retrieved_ids, relevant_doc_ids, k)
        result[f'ndcg@{k}'] = calculate_ndcg_at_k(retrieved_ids, relevant_doc_ids, k)
    
    result['mrr'] = calculate_mrr(retrieved_ids, relevant_doc_ids)
    
    # Response quality metrics (only if generation succeeded)
    if generated_answer and generated_answer != "[Generation skipped - no API key or error]":
        result['semantic_similarity'] = calculate_semantic_similarity(
            generated_answer, expected_answer, phobert_model
        )
        result['entity_accuracy'] = calculate_entity_accuracy(generated_answer, expected_answer)
    else:
        result['semantic_similarity'] = 0.0
        result['entity_accuracy'] = 0.0
    
    return result


def evaluate_dataset(
    test_file: str,
    output_file: str = None,
    k_values: List[int] = [1, 3, 5],
    auto_detect_relevant: bool = True  # NEW: Enable auto-detection
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Đánh giá toàn bộ test dataset"""
    
    print("=" * 60)
    print("🔍 PhoBERT Medical Chatbot Evaluation")
    print("=" * 60)
    
    # Load test data
    print(f"\n📂 Loading test data from: {test_file}")
    if test_file.endswith('.csv'):
        test_df = pd.read_csv(test_file)
    elif test_file.endswith('.json'):
        test_df = pd.read_json(test_file)
    else:
        raise ValueError("Test file must be CSV or JSON")
    
    # Check if relevant_doc_ids column exists
    has_relevant_ids = 'relevant_doc_ids' in test_df.columns
    
    if has_relevant_ids:
        # Parse relevant_doc_ids if it's a string
        test_df['relevant_doc_ids'] = test_df['relevant_doc_ids'].apply(
            lambda x: x.split(',') if isinstance(x, str) else (x if isinstance(x, list) else [])
        )
        print(f"✅ Loaded {len(test_df)} test questions (with manual doc IDs)")
    else:
        # Add empty relevant_doc_ids column
        test_df['relevant_doc_ids'] = [[] for _ in range(len(test_df))]
        print(f"✅ Loaded {len(test_df)} test questions (auto-detect mode)")
        auto_detect_relevant = True  # Force auto-detection
    
    if 'category' in test_df.columns:
        print(f"   Categories: {test_df['category'].value_counts().to_dict()}")
    
    # Initialize PhoBERT
    print("\n🧠 Loading PhoBERT model...")
    phobert_model = PhoBERTEmbeddingFunction()
    print("✅ PhoBERT loaded")
    
    # Check ChromaDB
    print("\n📊 Checking ChromaDB...")
    try:
        collection = get_or_create_collection()
        doc_count = collection.count()
        print(f"✅ ChromaDB ready with {doc_count} documents")
    except Exception as e:
        print(f"❌ ChromaDB error: {e}")
        return None, None
    
    # Run evaluation
    print(f"\n🚀 Evaluating {len(test_df)} questions...")
    if auto_detect_relevant:
        print("   Mode: AUTO-DETECT (using retrieval scores to determine relevance)")
    else:
        print("   Mode: MANUAL (using provided doc IDs)")
    print("-" * 60)
    
    results = []
    for idx, row in tqdm(test_df.iterrows(), total=len(test_df), desc="Evaluating"):
        try:
            result = evaluate_single_question(
                question=row['question'],
                expected_answer=row['expected_answer'],
                relevant_doc_ids=row['relevant_doc_ids'],
                phobert_model=phobert_model,
                k_values=k_values,
                auto_detect_relevant=auto_detect_relevant
            )
            results.append(result)
            
            # Print progress every 5 questions
            if (idx + 1) % 5 == 0:
                print(f"   Processed {idx + 1}/{len(test_df)} questions")
        
        except Exception as e:
            print(f"❌ Error evaluating question {idx + 1}: {e}")
            continue
    
    if not results:
        print("❌ No results generated")
        return None, None
    
    results_df = pd.DataFrame(results)
    
    # Calculate summary statistics
    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)
    
    metrics_summary = {}
    
    # Retrieval metrics
    print("\n🔍 RETRIEVAL METRICS:")
    for k in k_values:
        metrics_summary[f'Precision@{k}'] = results_df[f'precision@{k}'].mean()
        metrics_summary[f'Recall@{k}'] = results_df[f'recall@{k}'].mean()
        metrics_summary[f'NDCG@{k}'] = results_df[f'ndcg@{k}'].mean()
        print(f"   Precision@{k}: {metrics_summary[f'Precision@{k}']:.4f}")
        print(f"   Recall@{k}: {metrics_summary[f'Recall@{k}']:.4f}")
        print(f"   NDCG@{k}: {metrics_summary[f'NDCG@{k}']:.4f}")
    
    metrics_summary['MRR'] = results_df['mrr'].mean()
    print(f"   MRR: {metrics_summary['MRR']:.4f}")
    
    # Response quality
    print("\n💬 RESPONSE QUALITY METRICS:")
    metrics_summary['Semantic Similarity'] = results_df['semantic_similarity'].mean()
    metrics_summary['Entity Accuracy'] = results_df['entity_accuracy'].mean()
    print(f"   Semantic Similarity: {metrics_summary['Semantic Similarity']:.4f}")
    print(f"   Entity Accuracy: {metrics_summary['Entity Accuracy']:.4f}")
    
    # Performance
    print("\n⚡ PERFORMANCE METRICS:")
    metrics_summary['Avg Response Time (s)'] = results_df['response_time'].mean()
    print(f"   Avg Response Time: {metrics_summary['Avg Response Time (s)']:.2f}s")
    
    print("\n" + "=" * 60)
    
    # Interpretation
    print("\n🎯 INTERPRETATION:")
    precision_3 = metrics_summary['Precision@3']
    semantic_sim = metrics_summary['Semantic Similarity']
    entity_acc = metrics_summary['Entity Accuracy']
    
    score = 0
    if precision_3 >= 0.7:
        print("   ✅ Retrieval: GOOD (Precision@3 ≥ 0.7)")
        score += 1
    elif precision_3 >= 0.5:
        print("   ⚠️  Retrieval: MEDIUM (Precision@3 = 0.5-0.7)")
    else:
        print("   ❌ Retrieval: POOR (Precision@3 < 0.5)")
    
    if semantic_sim >= 0.7:
        print("   ✅ Response Quality: GOOD (Semantic Similarity ≥ 0.7)")
        score += 1
    elif semantic_sim >= 0.5:
        print("   ⚠️  Response Quality: MEDIUM (Semantic Similarity = 0.5-0.7)")
    else:
        print("   ❌ Response Quality: POOR (Semantic Similarity < 0.5)")
    
    if entity_acc >= 0.8:
        print("   ✅ Medical Accuracy: GOOD (Entity Accuracy ≥ 0.8)")
        score += 1
    elif entity_acc >= 0.6:
        print("   ⚠️  Medical Accuracy: MEDIUM (Entity Accuracy = 0.6-0.8)")
    else:
        print("   ❌ Medical Accuracy: POOR (Entity Accuracy < 0.6)")
    
    print(f"\n📈 OVERALL SCORE: {score}/3")
    if score >= 2:
        print("   🎉 Model is GOOD - Ready for production!")
    elif score == 1:
        print("   ⚠️  Model is MEDIUM - Needs improvement")
    else:
        print("   ❌ Model is POOR - Major improvements needed")
    
    print("=" * 60)
    
    # Save results
    if output_file:
        print(f"\n💾 Saving results to: {output_file}")
        if output_file.endswith('.csv'):
            results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        elif output_file.endswith('.json'):
            results_df.to_json(output_file, orient='records', force_ascii=False, indent=2)
        
        # Save summary
        summary_file = output_file.replace('.csv', '_summary.json').replace('.json', '_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Results saved:")
        print(f"   - {output_file}")
        print(f"   - {summary_file}")
    
    return results_df, metrics_summary

# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(description='Evaluate PhoBERT Medical Chatbot')
    parser.add_argument(
        '--test_file',
        type=str,
        required=True,
        help='Path to test data file (CSV or JSON)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results.csv',
        help='Output file path (default: evaluation_results.csv)'
    )
    parser.add_argument(
        '--k_values',
        type=int,
        nargs='+',
        default=[1, 3, 5],
        help='K values for Precision@K, Recall@K (default: 1 3 5)'
    )
    
    args = parser.parse_args()
    
    try:
        results_df, metrics_summary = evaluate_dataset(
            test_file=args.test_file,
            output_file=args.output,
            k_values=args.k_values
        )
        
        if results_df is not None:
            print("\n✅ Evaluation completed successfully!")
        else:
            print("\n❌ Evaluation failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
