
import sys
import os
from unittest.mock import MagicMock

# Add workspace root to sys.path
workspace_root = r"d:\ChatbotMedical_server\ChatbotMedical_server"
sys.path.append(workspace_root)

# Mocking external dependencies if needed, but let's try running it directly first
# with some sample coordinates (HCMC area)
LAT, LNG = 10.762622, 106.660172 # Near Cho Ray Hospital

from src.services.hospital_finder_service import hospital_finder_service

def test_recommendations():
    print(f"Testing Hospital Finder with coordinates: {LAT}, {LNG}")
    
    # Test case 1: General search
    result = hospital_finder_service.find_nearby_hospitals(LAT, LNG, specialty="nhi")
    
    if not result['success']:
        print(f"❌ Error: {result['message']}")
        return

    print(f"✅ Found {len(result['hospitals'])} hospitals.")
    
    recs = result['recommendations']
    print("\n--- Recommendation Set ---")
    if recs['best_prestige']:
        print(f"🏆 Prestigious: {recs['best_prestige']['name']} ({recs['best_prestige']['distance']}km)")
    else:
        print("🏆 Prestigious: Not found")
        
    if recs['nearest']:
        print(f"📍 Nearest: {recs['nearest']['name']} ({recs['nearest']['distance']}km)")
        
    if recs['cheapest']:
        print(f"💰 Cheapest (Public): {recs['cheapest']['name']} ({recs['cheapest']['distance']}km)")
    else:
        print("💰 Cheapest: Not found")

    print("\n--- Formatted Output ---")
    formatted = hospital_finder_service.format_hospitals_for_chatbot(result)
    print(formatted)

if __name__ == "__main__":
    test_recommendations()
