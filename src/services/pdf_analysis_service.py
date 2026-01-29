
import fitz  # PyMuPDF
import base64
import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class PDFAnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def pdf_to_base64_images(self, pdf_bytes: bytes) -> List[str]:
        """
        Convert each page of the PDF to a base64 encoded PNG image.
        """
        base64_images = []
        try:
            # Open the PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Better quality (2x zoom)
                
                # Convert pixmap to bytes (PNG)
                img_bytes = pix.tobytes("png")
                
                # Encode to base64
                base64_img = base64.b64encode(img_bytes).decode('utf-8')
                base64_images.append(f"data:image/png;base64,{base64_img}")
            
            doc.close()
            logger.info(f"✓ Converted PDF ({len(base64_images)} pages) to images.")
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise ValueError(f"Could not process PDF: {str(e)}")
            
        return base64_images

    def analyze_medical_report(self, file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        """
        Analyze medical report from PDF or Image bytes.
        """
        try:
            # 1. Determine file type and get images (base64)
            is_pdf = filename.lower().endswith('.pdf') or (not filename and file_bytes.startswith(b'%PDF'))
            
            if is_pdf:
                # Convert PDF to images
                images = self.pdf_to_base64_images(file_bytes)
            else:
                # Treat as image
                file_ext = filename.lower().split('.')[-1] if '.' in filename else 'png'
                img_type = file_ext if file_ext in ['png', 'jpg', 'jpeg'] else 'png'
                base64_img = base64.b64encode(file_bytes).decode('utf-8')
                images = [f"data:image/{img_type};base64,{base64_img}"]
            
            if not images:
                return {"success": False, "message": "Could not extract images from file"}

            # 2. Call OpenAI Vision
            messages = [
                {
                    "role": "system",
                    "content": """Bạn là chuyên gia phân tích xét nghiệm y tế. 
Hãy đọc các hình ảnh kết quả xét nghiệm được cung cấp và trích xuất dữ liệu theo định dạng JSON.

YÊU CẦU:
1. Trích xuất tất cả các chỉ số xét nghiệm (Blood test results).
2. Với mỗi chỉ số, lấy: Tên (indicator), Kết quả (result), Trị số đối chiếu (reference_range), Đơn vị (unit).
3. Thêm một trường nhận định (status) cho mỗi chỉ số: "Bình thường", "Cao", "Thấp", hoặc "Cần lưu ý".
4. Với mỗi chỉ số, thêm trường "explanation": Giải thích ngắn gọn ý nghĩa của kết quả này (VD: Nếu cao thì có nguy cơ gì, thấp thì sao, hoặc chỉ số này đại diện cho chức năng gì).
5. Cuối cùng, đưa ra một nhận định tổng quát (summary) và lời khuyên (advice) bằng tiếng Việt.

ĐỊNH DẠNG TRẢ VỀ (CHỈ TRẢ VỀ JSON):
{
  "patient_info": { "name": "...", "date": "..." },
  "indicators": [
    { 
      "name": "...", 
      "result": "...", 
      "reference_range": "...", 
      "unit": "...", 
      "status": "...",
      "explanation": "Giải thích ý nghĩa lâm sàng (VD: Cao có thể do...)" 
    }
  ],
  "summary": "...",
  "advice": "..."
}"""
                },
                {
                    "role": "user",
                    "content": []
                }
            ]

            # Add images to the user message
            messages[1]["content"].append({"type": "text", "text": "Đây là các trang của kết quả xét nghiệm y tế của tôi:"})
            for img_url in images[:3]:  # Limit to first 3 pages for token management
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": img_url}
                })

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=2000
            )

            analysis_data = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "data": analysis_data
            }

        except Exception as e:
            logger.error(f"Error in analyze_medical_report: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Lỗi phân tích kết quả: {str(e)}"
            }

pdf_analysis_service = PDFAnalysisService()
