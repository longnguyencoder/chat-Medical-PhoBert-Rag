"""
Manual Indexing Script - Step by Step
======================================
Chạy từng bước để index hospital specialties vào ChromaDB
"""

print("=" * 70)
print("🏥 MANUAL INDEXING - STEP BY STEP")
print("=" * 70)
print()

# ============================================================================
# STEP 1: Import libraries
# ============================================================================
print("STEP 1: Importing libraries...")
try:
    import json
    import sys
    import os
    
    # Add project to path
    project_root = r"d:\ChatbotMedical_server\ChatbotMedical_server"
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print("   ✓ Basic imports successful")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print()

# ============================================================================
# STEP 2: Load specialty data
# ============================================================================
print("STEP 2: Loading hospital specialties data...")
try:
    data_path = os.path.join(project_root, "src", "nlp_model", "data", "hospital_specialties.json")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        specialties_data = json.load(f)
    
    print(f"   ✓ Loaded {len(specialties_data)} specialties")
    print(f"   Examples: {[s['specialty_name'] for s in specialties_data[:3]]}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print()

# ============================================================================
# STEP 3: Import RAG service
# ============================================================================
print("STEP 3: Importing RAG service...")
try:
    from src.services.hospital_specialty_rag import (
        initialize_hospital_specialty_collection,
        index_hospital_specialties,
        list_all_specialties
    )
    print("   ✓ RAG service imported successfully")
except Exception as e:
    print(f"   ✗ Error: {e}")
    print(f"   Make sure you're in the project directory")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# STEP 4: Initialize ChromaDB collection
# ============================================================================
print("STEP 4: Initializing ChromaDB collection...")
try:
    success = initialize_hospital_specialty_collection()
    if success:
        print("   ✓ Collection initialized successfully")
    else:
        print("   ✗ Collection initialization failed")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# STEP 5: Index data (This will load PhoBERT - may take 1-2 minutes)
# ============================================================================
print("STEP 5: Indexing specialties into ChromaDB...")
print("   ⏳ Loading PhoBERT model (this may take 1-2 minutes)...")
print("   Please wait...")
print()

try:
    success = index_hospital_specialties(specialties_data)
    
    if success:
        print(f"   ✓ Successfully indexed {len(specialties_data)} specialties!")
    else:
        print("   ✗ Indexing failed")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error during indexing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# STEP 6: Verify indexing
# ============================================================================
print("STEP 6: Verifying indexed data...")
try:
    all_specialties = list_all_specialties()
    
    print(f"   ✓ Found {len(all_specialties)} specialties in ChromaDB")
    print()
    print("   Indexed specialties:")
    for i, name in enumerate(all_specialties[:10], 1):
        print(f"      {i:2d}. {name}")
    
    if len(all_specialties) > 10:
        print(f"      ... and {len(all_specialties) - 10} more")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# STEP 7: Quick test
# ============================================================================
print("STEP 7: Testing semantic search...")
try:
    from src.services.hospital_specialty_rag import semantic_search_specialty
    
    test_query = "bệnh viện chữa ung thư"
    print(f"   Query: '{test_query}'")
    
    results = semantic_search_specialty(test_query, top_k=3)
    
    print("   Results:")
    for i, r in enumerate(results, 1):
        print(f"      {i}. {r['specialty_name']} (similarity: {r['similarity_score']:.3f})")
        print(f"         Keywords: {r['hospital_keywords'][:3]}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("✅ INDEXING COMPLETED SUCCESSFULLY!")
print("=" * 70)
print()
print("Next steps:")
print("1. Restart your Flask server: python main.py")
print("2. Test with chatbot: 'Tìm bệnh viện chữa ung thư gần tôi'")
print("3. Look for 'Khớp chuyên khoa (AI)' in the results")
print()
