"""
Index Hospital Specialties Script
==================================
Script để index dữ liệu hospital specialties vào ChromaDB.

Usage:
    python scripts/index_hospital_specialties.py
"""

import json
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.services.hospital_specialty_rag import (
    initialize_hospital_specialty_collection,
    index_hospital_specialties,
    list_all_specialties
)

def main():
    print("=" * 60)
    print("🏥 Hospital Specialties Indexing Script")
    print("=" * 60)
    print()
    
    # Step 1: Load data
    print("📂 Step 1: Loading specialty data...")
    data_path = os.path.join(project_root, "src", "nlp_model", "data", "hospital_specialties.json")
    
    if not os.path.exists(data_path):
        print(f"✗ Error: Data file not found at {data_path}")
        return False
    
    with open(data_path, 'r', encoding='utf-8') as f:
        specialties_data = json.load(f)
    
    print(f"✓ Loaded {len(specialties_data)} specialties from JSON")
    print()
    
    # Step 2: Initialize collection
    print("🗄️  Step 2: Initializing ChromaDB collection...")
    success = initialize_hospital_specialty_collection()
    
    if not success:
        print("✗ Failed to initialize collection")
        return False
    
    print("✓ Collection initialized successfully")
    print()
    
    # Step 3: Index data
    print("📊 Step 3: Indexing specialties into ChromaDB...")
    print("   (This may take a minute...)")
    
    success = index_hospital_specialties(specialties_data)
    
    if not success:
        print("✗ Indexing failed")
        return False
    
    print(f"✓ Successfully indexed {len(specialties_data)} specialties")
    print()
    
    # Step 4: Verify
    print("✅ Step 4: Verifying indexed data...")
    all_specialties = list_all_specialties()
    
    print(f"✓ Found {len(all_specialties)} specialties in ChromaDB:")
    for i, name in enumerate(all_specialties, 1):
        print(f"   {i:2d}. {name}")
    
    print()
    print("=" * 60)
    print("🎉 Indexing completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test semantic search: python src/services/hospital_specialty_rag.py")
    print("2. Integrate with hospital finder service")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
