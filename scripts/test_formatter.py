
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.services.hospital_finder_service import hospital_finder_service

def test_formatter():
    mock_hospitals = [
        {
            'name': 'Bệnh viện Chợ Rẫy',
            'address': '201B Nguyễn Chí Thanh, Quận 5',
            'distance': 5.01,
            'match_reasons': ['Bệnh viện đầu ngành'],
            'phone': '028 3855 4137',
            'website': 'http://choray.vn/',
            'latitude': 10.7578,
            'longitude': 106.6628
        }
    ]
    
    formatted = hospital_finder_service.format_hospitals_for_chatbot(mock_hospitals)
    print("--- Formatted Output ---")
    print(formatted)
    print("------------------------")
    
    if "km" in formatted:
        print("✗ FAIL: Distance still present in formatted output")
        return False
    else:
        print("✓ PASS: Distance removed from formatted output")
        return True

if __name__ == "__main__":
    success = test_formatter()
    sys.exit(0 if success else 1)
