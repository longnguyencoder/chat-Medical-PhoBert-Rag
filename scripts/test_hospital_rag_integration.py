"""
Quick Test Script for Hospital RAG Integration
===============================================
Test the RAG integration without running full indexing.
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

def test_rag_service():
    """Test RAG service basic functionality"""
    print("=" * 60)
    print("🧪 Testing Hospital RAG Service")
    print("=" * 60)
    print()
    
    try:
        from src.services.hospital_specialty_rag import (
            initialize_hospital_specialty_collection,
            semantic_search_specialty,
            hybrid_specialty_matching
        )
        
        # Test 1: Initialize
        print("1. Testing collection initialization...")
        success = initialize_hospital_specialty_collection()
        print(f"   {'✓' if success else '✗'} Collection initialized\n")
        
        if not success:
            print("✗ Cannot proceed without collection")
            return False
        
        # Test 2: Check if data exists
        print("2. Checking if data is indexed...")
        try:
            results = semantic_search_specialty("tim mạch", top_k=1)
            if results:
                print(f"   ✓ Found data: {results[0]['specialty_name']}\n")
            else:
                print("   ⚠ No data found. Need to run indexing script.\n")
                print("   Run: python scripts/index_hospital_specialties.py\n")
                return False
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
            return False
        
        # Test 3: Semantic search
        print("3. Testing semantic search...")
        test_queries = [
            "bệnh viện chữa ung thư",
            "bệnh viện tim",
            "đau ngực khó thở"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            results = semantic_search_specialty(query, top_k=2)
            for i, r in enumerate(results, 1):
                print(f"      {i}. {r['specialty_name']} (score: {r['similarity_score']})")
        
        print()
        
        # Test 4: Hybrid matching
        print("4. Testing hybrid matching...")
        query = "bệnh viện chữa ung thư"
        keywords = hybrid_specialty_matching(query, top_k=3)
        print(f"   Query: '{query}'")
        print(f"   Keywords: {keywords[:5]}")
        print()
        
        print("=" * 60)
        print("✓ All RAG tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hospital_finder_integration():
    """Test hospital finder with RAG integration"""
    print("\n" + "=" * 60)
    print("🏥 Testing Hospital Finder Integration")
    print("=" * 60)
    print()
    
    try:
        from src.services.hospital_finder_service import hospital_finder_service
        
        # Test with a specialty query
        print("Testing: Find oncology hospitals near Quận 1, HCMC")
        print("Query: 'bệnh viện chữa ung thư'")
        print()
        
        result = hospital_finder_service.find_nearby_hospitals(
            latitude=10.7769,  # Quận 1, HCMC
            longitude=106.7009,
            specialty="bệnh viện chữa ung thư",
            radius=15000,  # 15km
            limit=5
        )
        
        if result['success']:
            hospitals = result['hospitals']
            print(f"✓ Found {len(hospitals)} hospitals:\n")
            
            for i, h in enumerate(hospitals, 1):
                print(f"{i}. {h['name']}")
                print(f"   Distance: {h['distance']} km")
                print(f"   Score: {h['priority_score']}")
                if h.get('match_reasons'):
                    print(f"   Reasons: {', '.join(h['match_reasons'])}")
                print()
        else:
            print(f"✗ Search failed: {result.get('message')}")
            return False
        
        print("=" * 60)
        print("✓ Hospital finder integration test passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting RAG Integration Tests\n")
    
    # Test 1: RAG Service
    rag_ok = test_rag_service()
    
    # Test 2: Hospital Finder Integration
    if rag_ok:
        finder_ok = test_hospital_finder_integration()
    else:
        print("\n⚠ Skipping hospital finder test (RAG not ready)")
        finder_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"RAG Service:           {'✓ PASS' if rag_ok else '✗ FAIL'}")
    print(f"Hospital Finder:       {'✓ PASS' if finder_ok else '✗ FAIL'}")
    print("=" * 60)
    
    if rag_ok and finder_ok:
        print("\n🎉 All tests passed! RAG integration is working.")
    elif not rag_ok:
        print("\n⚠ Need to index data first:")
        print("   python scripts/index_hospital_specialties.py")
    
    sys.exit(0 if (rag_ok and finder_ok) else 1)
