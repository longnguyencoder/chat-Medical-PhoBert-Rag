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
            "description": """Tìm bệnh viện gần vị trí người dùng và cung cấp thông tin liên hệ (địa chỉ, số điện thoại).

SỬ DỤNG TOOL NÀY KHI user:
- Hỏi về bệnh viện gần đây / gần nhất
- Cần đi khám bệnh / cấp cứu
- Hỏi địa chỉ bệnh viện
- Hỏi số điện thoại bệnh viện
- Cần tìm bệnh viện chuyên khoa (nhi, tim mạch, sản...)
- Có triệu chứng cần khám ngay (sốt cao, đau ngực, khó thở...)
- Hỏi "bệnh viện nào tốt", "nên đi bệnh viện nào"

QUAN TRỌNG: Nếu user hỏi về thông tin liên hệ bệnh viện (số điện thoại, địa chỉ) mà KHÔNG cung cấp vị trí, hãy HỎI LẠI vị trí của họ trước khi gọi tool này.

VÍ DỤ:
- "Bệnh viện nào gần tôi?" → Gọi tool
- "Bạn có số điện thoại bệnh viện không?" → HỎI: "Bạn đang ở khu vực nào để tôi tìm bệnh viện gần nhất?"
- "Tôi ở Thủ Đức, bệnh viện nào gần?" → Gọi tool với vị trí Thủ Đức""",
            "parameters": {
                "type": "object",
                "properties": {
                    "vi_do": {
                        "type": "number",
                        "description": "Vĩ độ (latitude) của vị trí user. VD: 10.8506 cho Thủ Đức, 10.7769 cho Quận 1"
                    },
                    "kinh_do": {
                        "type": "number",
                        "description": "Kinh độ (longitude) của vị trí user. VD: 106.7719 cho Thủ Đức, 106.7009 cho Quận 1"
                    },
                    "chuyen_khoa": {
                        "type": "string",
                        "description": "Chuyên khoa cần tìm (nếu có): nhi, tim mạch, sản, răng hàm mặt, da liễu, mắt, tai mũi họng..."
                    },
                    "ban_kinh_km": {
                        "type": "number",
                        "description": "Bán kính tìm kiếm (km), mặc định 5km. Tăng lên 10-15km nếu khu vực xa trung tâm"
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
