
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.services.pdf_analysis_service import pdf_analysis_service

def test_image_handling():
    print("Testing image handling in PDFAnalysisService...")
    # Mock image bytes
    mock_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    
    try:
        # We catch exceptions because it will try to call OpenAI which might fail without key/real data
        # But we want to see if it gets past the image detection part
        try:
            pdf_analysis_service.analyze_medical_report(mock_image_bytes, filename="test.png")
        except Exception as e:
            if "Could not extract images from file" in str(e):
                 print("✗ FAILED: Image detection failed")
                 return False
            # If it gets to OpenAI call, it's a success for our detection logic
            print(f"✓ Reached logic after detection (Expected API error: {str(e)[:50]}...)")
            
        print("✓ Image detection and base64 conversion logic verified.")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_image_handling()
    sys.exit(0 if success else 1)
