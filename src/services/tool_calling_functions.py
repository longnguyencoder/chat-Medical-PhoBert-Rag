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
    },
    {
        "type": "function",
        "function": {
            "name": "lay_thong_tin_nguoi_dung",
            "description": """Lấy thông tin chi tiết về người dùng để tư vấn cá nhân hóa.

SỬ DỤNG TOOL NÀY KHI:
- User nói về triệu chứng bệnh (đau đầu, sốt, ho...)
- User hỏi về thuốc nên dùng
- Cần kiểm tra dị ứng trước khi đề xuất thuốc
- Cần xem lịch uống thuốc của user
- Muốn cá nhân hóa câu trả lời dựa trên tiền sử bệnh

TOOL NÀY TRẢ VỀ:
- Hồ sơ sức khỏe (dị ứng, bệnh mãn tính, tiền sử)
- Lịch uống thuốc hiện tại
- Thuốc sắp uống trong 24h tới
- Tỷ lệ tuân thủ uống thuốc

QUAN TRỌNG: Hãy TỰ ĐỘNG gọi tool này khi user đề cập đến vấn đề sức khỏe để đưa ra tư vấn an toàn và cá nhân hóa.

VÍ DỤ:
- User: "Tôi bị đau đầu" → GỌI TOOL để check tiền sử, thuốc đang dùng
- User: "Nên uống thuốc gì?" → GỌI TOOL để check dị ứng
- User: "Tôi quên uống thuốc" → GỌI TOOL để xem lịch uống thuốc""",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "ID của người dùng cần lấy thông tin"
                    }
                },
                "required": ["user_id"]
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


def lay_thong_tin_nguoi_dung(user_id: int) -> str:
    """
    Lấy thông tin toàn diện về người dùng để tư vấn cá nhân hóa.
    
    Args:
        user_id: ID người dùng
        
    Returns:
        String formatted chứa thông tin user (cho GPT)
    """
    logger.info(f"👤 Tool called: lay_thong_tin_nguoi_dung(user_id={user_id})")
    
    try:
        from src.services.health_profile_service import health_profile_service
        from src.services.medication_service import (
            get_schedules_by_user,
            get_upcoming_medications,
            get_compliance_stats
        )
        
        result_parts = []
        
        # === 1. HEALTH PROFILE ===
        try:
            profile = health_profile_service.get_profile(user_id)
            if profile:
                result_parts.append("【HỒ SƠ SỨC KHỎE】")
                result_parts.append(f"📅 Ngày sinh: {profile.date_of_birth or 'Chưa cập nhật'}")
                result_parts.append(f"⚧ Giới tính: {profile.gender or 'Chưa cập nhật'}")
                
                if profile.allergies:
                    result_parts.append(f"⚠️ DỊ ỨNG: {profile.allergies}")
                    result_parts.append("   → TUYỆT ĐỐI KHÔNG đề xuất thuốc/thực phẩm có chất này!")
                
                if profile.chronic_diseases:
                    result_parts.append(f"🏥 Bệnh mãn tính: {profile.chronic_diseases}")
                
                if profile.current_medications:
                    result_parts.append(f"💊 Thuốc đang dùng: {profile.current_medications}")
                
                result_parts.append("")
            else:
                result_parts.append("【HỒ SƠ SỨC KHỎE】")
                result_parts.append("Chưa có thông tin hồ sơ sức khỏe.")
                result_parts.append("")
        except Exception as e:
            logger.warning(f"Could not fetch health profile: {e}")
        
        # === 2. MEDICATION SCHEDULE ===
        try:
            schedules = get_schedules_by_user(user_id)
            if schedules:
                result_parts.append("【LỊCH UỐNG THUỐC】")
                for schedule in schedules[:3]:  # Top 3
                    times = ', '.join(schedule.get_time_of_day_list())
                    result_parts.append(
                        f"💊 {schedule.medication_name} ({schedule.dosage or 'N/A'}) "
                        f"- {times}"
                    )
                result_parts.append("")
        except Exception as e:
            logger.warning(f"Could not fetch medication schedules: {e}")
        
        # === 3. RECENT MEDICATION LOGS (24h) ===
        try:
            from src.services.medication_service import get_logs_by_user
            from datetime import datetime, timedelta
            import pytz
            
            # Get logs from last 24 hours
            now = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
            start_date = (now - timedelta(hours=24)).strftime('%Y-%m-%d')
            
            recent_logs = get_logs_by_user(user_id, start_date=start_date)
            
            if recent_logs:
                result_parts.append("【LỊCH SỬ UỐNG THUỐC (24H QUA)】")
                for log in recent_logs[:5]:  # Top 5 recent
                    status_icon = "✅" if log.status == "taken" else "⏭️" if log.status == "skipped" else "⏳"
                    status_text = "Đã uống" if log.status == "taken" else "Đã bỏ qua" if log.status == "skipped" else "Chưa uống"
                    
                    # Get medication name from schedule
                    med_name = log.schedule.medication_name if log.schedule else "Unknown"
                    
                    # Format time with date context
                    scheduled_vn = log.scheduled_time.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                    
                    # Check if today or yesterday
                    today_str = now.strftime('%Y-%m-%d')
                    log_date_str = scheduled_vn.strftime('%Y-%m-%d')
                    yesterday_str = (now - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    if log_date_str == today_str:
                        date_display = "Hôm nay"
                    elif log_date_str == yesterday_str:
                        date_display = "Hôm qua"
                    else:
                        date_display = scheduled_vn.strftime('%d/%m')
                        
                    time_str = scheduled_vn.strftime('%H:%M')
                    
                    result_parts.append(
                        f"{status_icon} {med_name} lúc {time_str} ({date_display}) - {status_text}"
                    )
                result_parts.append("")
                result_parts.append("💡 Gợi ý: Tham khảo lịch sử này để KHÔNG hỏi lại những thuốc đã uống!")
                result_parts.append("")
        except Exception as e:
            logger.warning(f"Could not fetch recent medication logs: {e}")
        
        # === 4. UPCOMING MEDICATIONS (24h) ===
        try:
            upcoming = get_upcoming_medications(user_id, hours=24)
            if upcoming:
                result_parts.append("【THUỐC SẮP UỐNG (24H TỚI)】")
                for med in upcoming[:5]:  # Top 5
                    result_parts.append(
                        f"⏰ {med['display']}: {med['medication_name']} ({med.get('dosage', 'N/A')})"
                    )
                result_parts.append("")
                result_parts.append("💡 Gợi ý: Hỏi user đã uống thuốc chưa CHỈ KHI thuốc CHƯA có trong lịch sử!")
                result_parts.append("")
        except Exception as e:
            logger.warning(f"Could not fetch upcoming medications: {e}")
        
        # === 5. COMPLIANCE STATS ===
        try:
            stats = get_compliance_stats(user_id, days=7)
            if stats['total'] > 0:
                result_parts.append("【TUÂN THỦ UỐNG THUỐC (7 NGÀY)】")
                result_parts.append(
                    f"✅ Đã uống: {stats['taken']}/{stats['total']} "
                    f"({stats['compliance_rate']:.0f}%)"
                )
                result_parts.append(f"⏭️ Bỏ qua: {stats['skipped']}")
                result_parts.append(f"⏳ Chưa uống: {stats['pending']}")
                result_parts.append("")
                
                if stats['compliance_rate'] < 70:
                    result_parts.append("⚠️ Tỷ lệ tuân thủ thấp! Nên nhắc nhở user uống thuốc đều đặn.")
                    result_parts.append("")
        except Exception as e:
            logger.warning(f"Could not fetch compliance stats: {e}")
        
        # === 5. PROACTIVE SUGGESTIONS ===
        result_parts.append("【GỢI Ý CHỦ ĐỘNG】")
        result_parts.append("Dựa trên thông tin trên, hãy:")
        result_parts.append("• Tham khảo DỊ ỨNG trước khi đề xuất thuốc")
        result_parts.append("• Nhắc nhở nếu có thuốc sắp uống")
        result_parts.append("• Hỏi thêm về bệnh mãn tính nếu liên quan")
        result_parts.append("• Đề xuất tìm bệnh viện nếu triệu chứng nghiêm trọng")
        
        formatted_result = "\n".join(result_parts)
        logger.info(f"✓ Retrieved user context for user {user_id}")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error in lay_thong_tin_nguoi_dung: {e}", exc_info=True)
        return f"Không thể lấy thông tin người dùng: {str(e)}"


# Mapping function names to actual functions
TOOL_FUNCTIONS = {
    "tim_benh_vien_gan_nhat": tim_benh_vien_gan_nhat,
    "lay_thong_tin_nguoi_dung": lay_thong_tin_nguoi_dung
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
