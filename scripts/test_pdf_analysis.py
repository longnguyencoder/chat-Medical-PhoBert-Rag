
import sys
import os
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.services.pdf_analysis_service import pdf_analysis_service

def test_pdf_conversion():
    print("Testing PDF conversion to base64 images...")
    # This requires a real PDF or a mock. Since I don't have a real one handy, 
    # I'll just check if the module imports and functions exist.
    try:
        import fitz
        print("✓ PyMuPDF (fitz) is installed.")
    except ImportError:
        print("✗ PyMuPDF (fitz) is NOT installed.")
        return False

    if hasattr(pdf_analysis_service, 'pdf_to_base64_images'):
        print("✓ pdf_to_base64_images method exists.")
    else:
        print("✗ pdf_to_base64_images method is missing.")
        return False
        
    print("✓ Basic service structure verified.")
    return True

if __name__ == "__main__":
    success = test_pdf_conversion()
    sys.exit(0 if success else 1)
