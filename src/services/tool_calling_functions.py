"""
Tool Calling Functions for Agentic Chatbot
==========================================
Các function mà GPT có thể gọi để thực hiện hành động tự động.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import hospital finder service
from src.services.hospital_finder_service import hospital_finder_service


# ═══════════════════════════════════════════════════════════════
# TOOL DEFINITIONS - Định nghĩa các công cụ cho GPT
# ═══════════════════════════════════════════════════════════════

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tim_benh_vien_gan_nhat",
            "description": "Tìm bệnh viện gần vị trí người dùng. Sử dụng khi user hỏi về bệnh viện gần, cần đi khám, hoặc có triệu chứng cần cấp cứu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vi_do": {
                        "type": "number",
                        "description": "Vĩ độ (latitude) của vị trí user"
                    },
                    "kinh_do": {
                        "type": "number",
                        "description": "Kinh độ (longitude) của vị trí user"
                    },
                    "chuyen_khoa": {
                        "type": "string",
                        "description": "Chuyên khoa cần tìm (nếu có): nhi, tim mạch, sản, răng hàm mặt, da liễu..."
                    },
                    "ban_kinh_km": {
                        "type": "number",
                        "description": "Bán kính tìm kiếm (km), mặc định 5km"
                    }
                },
                "required": ["vi_do", "kinh_do"]
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS - Triển khai các function
# ═══════════════════════════════════════════════════════════════

def tim_benh_vien_gan_nhat(
    vi_do: float,
    kinh_do: float,
    chuyen_khoa: Optional[str] = None,
    ban_kinh_km: float = 5.0
) -> str:
    """
    Function được GPT gọi để tìm bệnh viện.
    
    Args:
        vi_do: Vĩ độ
        kinh_do: Kinh độ
        chuyen_khoa: Chuyên khoa (optional)
        ban_kinh_km: Bán kính tìm kiếm
        
    Returns:
        String chứa danh sách bệnh viện (formatted cho GPT)
    """
    logger.info(f"🏥 Tool called: tim_benh_vien_gan_nhat({vi_do}, {kinh_do}, {chuyen_khoa}, {ban_kinh_km}km)")
    
    try:
        # Gọi hospital finder service
        result = hospital_finder_service.find_nearby_hospitals(
            latitude=vi_do,
            longitude=kinh_do,
            radius=int(ban_kinh_km * 1000),  # Convert km to meters
            specialty=chuyen_khoa,
            limit=5
        )
        
        if not result['success']:
            return f"Lỗi khi tìm bệnh viện: {result.get('message', 'Unknown error')}"
        
        hospitals = result['hospitals']
        
        if not hospitals:
            return "Không tìm thấy bệnh viện nào trong khu vực này. Vui lòng mở rộng bán kính tìm kiếm."
        
        # Format kết quả cho GPT
        formatted = hospital_finder_service.format_hospitals_for_chatbot(hospitals)
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error in tim_benh_vien_gan_nhat: {e}", exc_info=True)
        return f"Đã xảy ra lỗi khi tìm bệnh viện: {str(e)}"


# Mapping function names to actual functions
TOOL_FUNCTIONS = {
    "tim_benh_vien_gan_nhat": tim_benh_vien_gan_nhat
}


# ═══════════════════════════════════════════════════════════════
# TOOL CALLING HANDLER
# ═══════════════════════════════════════════════════════════════

def execute_tool_call(tool_call) -> str:
    """
    Thực thi một tool call từ GPT.
    
    Args:
        tool_call: Tool call object từ GPT response
        
    Returns:
        Kết quả từ function dạng string
    """
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    logger.info(f"🔧 Executing tool: {function_name} with args: {arguments}")
    
    # Lấy function từ mapping
    function_to_call = TOOL_FUNCTIONS.get(function_name)
    
    if not function_to_call:
        logger.error(f"Unknown function: {function_name}")
        return f"Lỗi: Không tìm thấy function {function_name}"
    
    try:
        # Gọi function với arguments
        result = function_to_call(**arguments)
        return result
    except Exception as e:
        logger.error(f"Error executing {function_name}: {e}", exc_info=True)
        return f"Lỗi khi thực thi {function_name}: {str(e)}"
