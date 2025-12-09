"""
Health Profile Service
======================
Service layer xử lý logic nghiệp vụ cho Health Profile.

Chức năng:
- Validate dữ liệu trước khi lưu
- Xử lý JSON serialization cho allergies, conditions, medications
- Format dữ liệu để đưa vào chatbot prompt
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from src.models.base import db
from src.models.health_profile import HealthProfile

logger = logging.getLogger(__name__)


class HealthProfileService:
    """
    Service xử lý các thao tác liên quan đến Health Profile.
    """
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[HealthProfile]:
        """
        Lấy hồ sơ sức khỏe của user.
        
        Args:
            user_id: ID của user
            
        Returns:
            HealthProfile object hoặc None nếu chưa có
        """
        return HealthProfile.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def create_or_update_profile(user_id: int, data: Dict) -> HealthProfile:
        """
        Tạo mới hoặc cập nhật hồ sơ sức khỏe.
        
        Args:
            user_id: ID của user
            data: Dictionary chứa thông tin hồ sơ
            
        Returns:
            HealthProfile object đã được lưu
            
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ
        """
        # Kiểm tra xem đã có profile chưa
        profile = HealthProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Tạo mới
            profile = HealthProfile(user_id=user_id)
            db.session.add(profile)
            logger.info(f"Creating new health profile for user {user_id}")
        else:
            logger.info(f"Updating health profile for user {user_id}")
        
        # === CẬP NHẬT CÁC TRƯỜNG ===
        
        # Ngày sinh
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                # Chuyển string thành date object
                if isinstance(data['date_of_birth'], str):
                    profile.date_of_birth = datetime.strptime(
                        data['date_of_birth'], '%Y-%m-%d'
                    ).date()
                else:
                    profile.date_of_birth = data['date_of_birth']
            except ValueError as e:
                raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
        
        # Giới tính
        if 'gender' in data:
            gender = data['gender']
            if gender and gender not in ['Male', 'Female', 'Other']:
                raise ValueError("Gender must be: Male, Female, or Other")
            profile.gender = gender
        
        # Nhóm máu
        if 'blood_type' in data:
            profile.blood_type = data['blood_type']
        
        # Chiều cao
        if 'height' in data and data['height']:
            height = float(data['height'])
            if height <= 0 or height > 300:  # Validate reasonable range
                raise ValueError("Height must be between 0 and 300 cm")
            profile.height = height
        
        # Cân nặng
        if 'weight' in data and data['weight']:
            weight = float(data['weight'])
            if weight <= 0 or weight > 500:  # Validate reasonable range
                raise ValueError("Weight must be between 0 and 500 kg")
            profile.weight = weight
        
        # === XỬ LÝ CÁC TRƯỜNG JSON ===
        
        # Dị ứng
        if 'allergies' in data:
            allergies = data['allergies']
            if isinstance(allergies, list):
                # Chuyển list thành JSON string
                profile.allergies = json.dumps(allergies, ensure_ascii=False)
            elif isinstance(allergies, str):
                # Nếu đã là string, validate JSON
                try:
                    json.loads(allergies)
                    profile.allergies = allergies
                except json.JSONDecodeError:
                    raise ValueError("Allergies must be valid JSON array")
            elif allergies is None:
                profile.allergies = None
        
        # Bệnh mãn tính
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
        
        # Thuốc đang dùng
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
        
        # Tiền sử gia đình
        if 'family_history' in data:
            profile.family_history = data['family_history']
        
        # Cập nhật timestamp
        profile.updated_at = datetime.utcnow()
        
        # Lưu vào database
        db.session.commit()
        
        logger.info(f"Health profile saved for user {user_id}")
        return profile
    
    @staticmethod
    def delete_profile(user_id: int) -> bool:
        """
        Xóa hồ sơ sức khỏe của user.
        
        Args:
            user_id: ID của user
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
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
        Lấy và format hồ sơ sức khỏe để đưa vào prompt của chatbot.
        
        Args:
            user_id: ID của user
            
        Returns:
            String chứa thông tin hồ sơ, hoặc None nếu chưa có
            
        Example:
            >>> HealthProfileService.format_profile_for_chatbot(1)
            "Tuổi: 30 | Giới tính: Nam | ⚠️ DỊ ỨNG: Penicillin, Peanuts | Bệnh mãn tính: Diabetes Type 2"
        """
        profile = HealthProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None
        
        return profile.format_for_chatbot()
    
    @staticmethod
    def validate_allergies(allergies: List[str]) -> bool:
        """
        Kiểm tra danh sách dị ứng có hợp lệ không.
        
        Args:
            allergies: Danh sách dị ứng
            
        Returns:
            True nếu hợp lệ
        """
        if not isinstance(allergies, list):
            return False
        
        # Kiểm tra mỗi item phải là string
        for item in allergies:
            if not isinstance(item, str) or len(item.strip()) == 0:
                return False
        
        return True


# Singleton instance
health_profile_service = HealthProfileService()
