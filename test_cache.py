"""
Test script for caching layer

This script demonstrates the performance improvement from caching.
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"
CACHED_CHAT_ENDPOINT = f"{BASE_URL}/api/medical-chatbot/chat-cached"
CACHE_STATS_ENDPOINT = f"{BASE_URL}/api/medical-chatbot/cache/stats"
CACHE_CLEAR_ENDPOINT = f"{BASE_URL}/api/medical-chatbot/cache/clear"


def test_cache_performance():
    """Test cache performance with same question"""
    
    print("\n" + "="*80)
    print("🧪 TESTING CACHE PERFORMANCE".center(80))
    print("="*80)
    
    question = "Triệu chứng của sốt xuất huyết là gì?"
    
    # Clear cache first
    print("\n1️⃣  Clearing cache...")
    response = requests.post(CACHE_CLEAR_ENDPOINT)
    print(f"   ✓ Cache cleared: {response.json()}")
    
    # First request (cache miss)
    print(f"\n2️⃣  First request (cache MISS expected)...")
    print(f"   Question: {question}")
    
    start_time = time.time()
    response1 = requests.post(CACHED_CHAT_ENDPOINT, json={"question": question})
    latency1 = time.time() - start_time
    
    result1 = response1.json()
    print(f"\n   ⏱️  Latency: {latency1:.2f}s")
    print(f"   📊 Cache Info:")
    print(f"      - Search cached: {result1['cache_info']['search_cached']}")
    print(f"      - Response cached: {result1['cache_info']['response_cached']}")
    print(f"      - Fully cached: {result1['cache_info']['fully_cached']}")
    
    # Second request (cache hit)
    print(f"\n3️⃣  Second request (cache HIT expected)...")
    print(f"   Question: {question}")
    
    start_time = time.time()
    response2 = requests.post(CACHED_CHAT_ENDPOINT, json={"question": question})
    latency2 = time.time() - start_time
    
    result2 = response2.json()
    print(f"\n   ⏱️  Latency: {latency2:.2f}s")
    print(f"   📊 Cache Info:")
    print(f"      - Search cached: {result2['cache_info']['search_cached']}")
    print(f"      - Response cached: {result2['cache_info']['response_cached']}")
    print(f"      - Fully cached: {result2['cache_info']['fully_cached']}")
    
    # Performance improvement
    improvement = ((latency1 - latency2) / latency1) * 100
    speedup = latency1 / latency2
    
    print(f"\n4️⃣  Performance Comparison:")
    print(f"   📈 First request:  {latency1:.2f}s")
    print(f"   📉 Second request: {latency2:.2f}s")
    print(f"   ⚡ Improvement:    {improvement:.1f}%")
    print(f"   🚀 Speedup:        {speedup:.1f}x faster")
    
    # Get cache statistics
    print(f"\n5️⃣  Cache Statistics:")
    stats_response = requests.get(CACHE_STATS_ENDPOINT)
    stats = stats_response.json()
    
    print(f"   📊 Cache size: {stats['size']}/{stats['max_size']}")
    print(f"   ✅ Cache hits: {stats['hits']}")
    print(f"   ❌ Cache misses: {stats['misses']}")
    print(f"   📈 Hit rate: {stats['hit_rate']:.1f}%")
    
    print("\n" + "="*80)
    print("✅ Cache test completed!".center(80))
    print("="*80)


def test_cache_normalization():
    """Test that cache normalizes queries correctly"""
    
    print("\n" + "="*80)
    print("🧪 TESTING CACHE NORMALIZATION".center(80))
    print("="*80)
    
    # Clear cache
    requests.post(CACHE_CLEAR_ENDPOINT)
    
    # Different formats of same question
    questions = [
        "Triệu chứng sốt xuất huyết?",
        "TRIỆU CHỨNG SỐT XUẤT HUYẾT",
        "triệu chứng sốt xuất huyết!!!",
        "Triệu   chứng   sốt   xuất   huyết"
    ]
    
    print("\nTesting with different formats of same question:")
    
    latencies = []
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. Question: \"{q}\"")
        
        start_time = time.time()
        response = requests.post(CACHED_CHAT_ENDPOINT, json={"question": q})
        latency = time.time() - start_time
        latencies.append(latency)
        
        result = response.json()
        cached = result['cache_info']['fully_cached']
        
        print(f"   ⏱️  Latency: {latency:.2f}s")
        print(f"   📊 Cached: {'✅ YES' if cached else '❌ NO'}")
    
    # Check if subsequent requests were cached
    if all(latencies[i] < latencies[0] for i in range(1, len(latencies))):
        print("\n✅ Cache normalization working correctly!")
        print("   All variations hit the same cache entry.")
    else:
        print("\n⚠️  Cache normalization may have issues.")
    
    print("\n" + "="*80)


def test_multiple_questions():
    """Test cache with multiple different questions"""
    
    print("\n" + "="*80)
    print("🧪 TESTING MULTIPLE QUESTIONS".center(80))
    print("="*80)
    
    # Clear cache
    requests.post(CACHE_CLEAR_ENDPOINT)
    
    questions = [
        "Triệu chứng của sốt xuất huyết là gì?",
        "Cách điều trị cảm cúm tại nhà?",
        "Paracetamol liều lượng cho trẻ em?",
        "Triệu chứng của sốt xuất huyết là gì?",  # Repeat
        "Cách điều trị cảm cúm tại nhà?",  # Repeat
    ]
    
    print("\nAsking 5 questions (2 are repeats)...")
    
    for i, q in enumerate(questions, 1):
        response = requests.post(CACHED_CHAT_ENDPOINT, json={"question": q})
        result = response.json()
        cached = result['cache_info']['fully_cached']
        
        print(f"{i}. {q[:50]}... → {'✅ CACHED' if cached else '❌ NEW'}")
    
    # Get final stats
    stats_response = requests.get(CACHE_STATS_ENDPOINT)
    stats = stats_response.json()
    
    print(f"\n📊 Final Statistics:")
    print(f"   Cache size: {stats['size']} entries")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")
    print(f"   Expected: 40% (2 hits out of 5 requests)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n🚀 Starting Cache Tests...")
    print("Make sure the server is running on http://127.0.0.1:5000")
    
    try:
        # Test 1: Performance
        test_cache_performance()
        
        # Test 2: Normalization
        test_cache_normalization()
        
        # Test 3: Multiple questions
        test_multiple_questions()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS COMPLETED!".center(80))
        print("="*80)
        
        print("\n💡 Key Takeaways:")
        print("   1. First request is slow (3-5s) - cache miss")
        print("   2. Repeated requests are FAST (<0.5s) - cache hit")
        print("   3. Cache normalizes queries (case, punctuation)")
        print("   4. Cache hit rate improves with repeated questions")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("   Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
