"""
Health Profile Service
======================
Service layer xử lý logic nghiệp vụ cho Health Profile (Hồ sơ sức khỏe).
Tầng này nằm giữa Controller (API) và Model (Database).

Chức năng chính:
1. Validate dữ liệu đầu vào (kiểm tra ngày sinh, chiều cao, cân nặng hợp lệ).
2. Xử lý chuyển đổi kiểu dữ liệu (Serialization/Deserialization) cho các trường list như allergies, medications vì DB lưu dưới dạng JSON string.
3. Cung cấp hàm format dữ liệu để Chatbot dễ dàng sử dụng.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from src.models.base import db
from src.models.health_profile import HealthProfile  # Model SQLAlchemy

logger = logging.getLogger(__name__)


class HealthProfileService:
    """
    Class chứa các static methods để tương tác với hồ sơ sức khỏe.
    Dùng static method để không cần khởi tạo instance mỗi lần dùng.
    """
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[HealthProfile]:
        """
        Lấy hồ sơ sức khỏe của một user cụ thể.
        
        Args:
            user_id: ID của user cần lấy hồ sơ
            
        Returns:
            HealthProfile object: Nếu tìm thấy
            None: Nếu user chưa có hồ sơ
        """
        # Query trực tiếp từ bảng HealthProfile
        return HealthProfile.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def create_or_update_profile(user_id: int, data: Dict) -> HealthProfile:
        """
        Tạo mới hoặc cập nhật hồ sơ sức khỏe.
        Hàm này xử lý chi tiết validate và convert dữ liệu.
        
        Args:
            user_id: ID người dùng
            data: Dictionary chứa data từ request body
            
        Returns:
            HealthProfile object đã lưu DB
            
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ (ngày sai format, số âm...)
        """
        # 1. Tìm xem hồ sơ đã tồn tại chưa
        profile = HealthProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Nếu chưa có -> Khởi tạo mới
            profile = HealthProfile(user_id=user_id)
            db.session.add(profile)
            logger.info(f"Creating new health profile for user {user_id}")
        else:
            # Nếu có rồi -> Chỉ update
            logger.info(f"Updating health profile for user {user_id}")
        
        # 2. CẬP NHẬT TỪNG TRƯỜNG DỮ LIỆU (Có validation)
        
        # --- Ngày sinh (date_of_birth) ---
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                # Nếu là string 'YYYY-MM-DD', parse thành object date
                if isinstance(data['date_of_birth'], str):
                    profile.date_of_birth = datetime.strptime(
                        data['date_of_birth'], '%Y-%m-%d'
                    ).date()
                else:
                    profile.date_of_birth = data['date_of_birth']
            except ValueError as e:
                raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
        
        # --- Giới tính (gender) ---
        if 'gender' in data:
            gender = data['gender']
            # Kiểm tra giá trị hợp lệ
            if gender and gender not in ['Male', 'Female', 'Other']:
                raise ValueError("Gender must be: Male, Female, or Other")
            profile.gender = gender
        
        # --- Nhóm máu (blood_type) ---
        if 'blood_type' in data:
            profile.blood_type = data['blood_type']
        
        # --- Chiều cao (height) ---
        if 'height' in data and data['height']:
            try:
                height = float(data['height'])
                if height <= 0 or height > 300:  # Giới hạn hợp lý: 0-3m
                    raise ValueError("Height must be between 0 and 300 cm")
                profile.height = height
            except ValueError:
                 raise ValueError("Height must be a number")
        
        # --- Cân nặng (weight) ---
        if 'weight' in data and data['weight']:
            try:
                weight = float(data['weight'])
                if weight <= 0 or weight > 500:  # Giới hạn hợp lý: 0-500kg
                    raise ValueError("Weight must be between 0 and 500 kg")
                profile.weight = weight
            except ValueError:
                 raise ValueError("Weight must be a number")
        
        # 3. XỬ LÝ CÁC TRƯỜNG JSON (LIST -> STRING)
        # Database relation SQL thường lưu list dưới dạng JSON string hoặc bảng phụ.
        # Ở đây dùng JSON string cho đơn giản.
        
        # --- Dị ứng (allergies) ---
        if 'allergies' in data:
            allergies = data['allergies']
            if isinstance(allergies, list):
                # Chuyển List Python thành chuỗi JSON (VD: ['A', 'B'] -> '["A", "B"]')
                profile.allergies = json.dumps(allergies, ensure_ascii=False)
            elif isinstance(allergies, str):
                # Nếu client gửi string, thử parse xem có đúng chuẩn JSON không
                try:
                    json.loads(allergies)
                    profile.allergies = allergies
                except json.JSONDecodeError:
                    raise ValueError("Allergies must be valid JSON array")
            elif allergies is None:
                profile.allergies = None
        
        # --- Bệnh mãn tính (chronic_conditions) ---
        if 'chronic_conditions' in data:
            conditions = data['chronic_conditions']
            if isinstance(conditions, list):
                profile.chronic_conditions = json.dumps(conditions, ensure_ascii=False)
            elif isinstance(conditions, str):
                try:
                    json.loads(conditions)
                    profile.chronic_conditions = conditions
                except json.JSONDecodeError:
                    raise ValueError("Chronic conditions must be valid JSON array")
            elif conditions is None:
                profile.chronic_conditions = None
        
        # --- Thuốc đang dùng (medications) ---
        if 'medications' in data:
            medications = data['medications']
            if isinstance(medications, list):
                profile.medications = json.dumps(medications, ensure_ascii=False)
            elif isinstance(medications, str):
                try:
                    json.loads(medications)
                    profile.medications = medications
                except json.JSONDecodeError:
                    raise ValueError("Medications must be valid JSON array")
            elif medications is None:
                profile.medications = None
        
        # --- Tiền sử gia đình (family_history) ---
        if 'family_history' in data:
            profile.family_history = data['family_history']
        
        # Cập nhật thời gian sửa đổi
        profile.updated_at = datetime.utcnow()
        
        # 4. LƯU VÀO DATABASE
        db.session.commit()
        
        logger.info(f"Health profile saved for user {user_id}")
        return profile
    
    @staticmethod
    def delete_profile(user_id: int) -> bool:
        """
        Xóa hồ sơ sức khỏe.
        
        Returns:
            True: Xóa thành công
            False: Không tìm thấy hồ sơ
        """
        profile = HealthProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return False
        
        db.session.delete(profile)
        db.session.commit()
        logger.info(f"Deleted health profile for user {user_id}")
        return True
    
    @staticmethod
    def format_profile_for_chatbot(user_id: int) -> Optional[str]:
        """
        Tạo chuỗi tóm tắt hồ sơ để gán vào System Prompt của Chatbot.
        Giúp Chatbot hiểu ngữ cảnh sức khỏe của user.
        
        VD Output: "Tuổi: 30 | Giới tính: Nam | ⚠️ DỊ ỨNG: Penicillin"
        """
        profile = HealthProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None
        
        # Gọi phương thức format của Model (đã định nghĩa trong models/health_profile.py)
        return profile.format_for_chatbot()
    
    @staticmethod
    def validate_allergies(allergies: List[str]) -> bool:
        """
        Helper method: Validate danh sách dị ứng.
        Đảm bảo input là list các string không rỗng.
        """
        if not isinstance(allergies, list):
            return False
        
        for item in allergies:
            if not isinstance(item, str) or len(item.strip()) == 0:
                return False
        
        return True


# Tạo singleton instance để dùng ở Controller
health_profile_service = HealthProfileService()
