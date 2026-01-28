"""
Simple Indexing Script - Direct Approach
=========================================
Index hospital specialties directly without complex imports
"""

import json
import os
import sys

# Add to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("🏥 Simple Hospital Specialties Indexing")
print("=" * 60)
print()

# Step 1: Load data
print("1. Loading data...")
data_path = os.path.join(os.path.dirname(__file__), "..", "src", "nlp_model", "data", "hospital_specialties.json")
data_path = os.path.abspath(data_path)

with open(data_path, 'r', encoding='utf-8') as f:
    specialties = json.load(f)

print(f"   ✓ Loaded {len(specialties)} specialties")
print()

# Step 2: Import and initialize
print("2. Importing RAG service...")
try:
    from src.services.hospital_specialty_rag import (
        initialize_hospital_specialty_collection,
        index_hospital_specialties
    )
    print("   ✓ Import successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

print()

# Step 3: Initialize collection
print("3. Initializing ChromaDB collection...")
try:
    success = initialize_hospital_specialty_collection()
    if success:
        print("   ✓ Collection initialized")
    else:
        print("   ✗ Initialization failed")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 4: Index data
print("4. Indexing specialties (this may take 1-2 minutes)...")
print("   Loading PhoBERT model...")
try:
    success = index_hospital_specialties(specialties)
    if success:
        print(f"   ✓ Successfully indexed {len(specialties)} specialties")
    else:
        print("   ✗ Indexing failed")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ INDEXING COMPLETED SUCCESSFULLY!")
print("=" * 60)
print()
print("Next: Test with chatbot or run:")
print("  python scripts/test_hospital_rag_integration.py")
print()
