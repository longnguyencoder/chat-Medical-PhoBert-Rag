"""
Health Profile Model
====================
Mô hình lưu trữ thông tin sức khỏe cá nhân của người dùng.

Mục đích:
- Lưu thông tin y tế cá nhân (tuổi, giới tính, dị ứng, bệnh mãn tính...)
- Cung cấp context cho chatbot để tư vấn chính xác hơn
- Giúp chatbot tránh khuyến cáo thuốc/phương pháp không phù hợp

Ví dụ sử dụng:
- User dị ứng Penicillin → Bot sẽ KHÔNG đề xuất thuốc chứa Penicillin
- User có tiền sử tiểu đường → Bot sẽ lưu ý về chế độ ăn phù hợp
"""

from datetime import datetime
from src.models.base import db
import json


class HealthProfile(db.Model):
    """
    Bảng lưu hồ sơ sức khỏe cá nhân của người dùng.
    
    Quan hệ: 1 User - 1 HealthProfile (One-to-One)
    """
    __tablename__ = 'HealthProfiles'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('Users.user_id', ondelete='CASCADE'),  # Xóa user → xóa profile
        primary_key=True,
        nullable=False
    )
    
    # ========================================================================
    # THÔNG TIN CƠ BẢN
    # ========================================================================
    date_of_birth = db.Column(
        db.Date,
        nullable=True,
        comment='Ngày sinh (để tính tuổi)'
    )
    
    gender = db.Column(
        db.String(10),
        nullable=True,
        comment='Giới tính: Male, Female, Other'
    )
    
    blood_type = db.Column(
        db.String(5),
        nullable=True,
        comment='Nhóm máu: A, B, AB, O (có thể thêm Rh+ hoặc Rh-)'
    )
    
    height = db.Column(
        db.Float,
        nullable=True,
        comment='Chiều cao (cm)'
    )
    
    weight = db.Column(
        db.Float,
        nullable=True,
        comment='Cân nặng (kg)'
    )
    
    # ========================================================================
    # THÔNG TIN Y TẾ QUAN TRỌNG (Lưu dạng JSON)
    # ========================================================================
    allergies = db.Column(
        db.Text,
        nullable=True,
        comment='Danh sách dị ứng (JSON array). VD: ["Penicillin", "Peanuts", "Seafood"]'
    )
    
    chronic_conditions = db.Column(
        db.Text,
        nullable=True,
        comment='Bệnh mãn tính (JSON array). VD: ["Diabetes Type 2", "Hypertension"]'
    )
    
    medications = db.Column(
        db.Text,
        nullable=True,
        comment='Thuốc đang dùng (JSON array). VD: ["Metformin 500mg", "Aspirin 100mg"]'
    )
    
    family_history = db.Column(
        db.Text,
        nullable=True,
        comment='Tiền sử gia đình (text tự do). VD: "Bố bị tiểu đường, mẹ bị cao huyết áp"'
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='Thời gian tạo hồ sơ'
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment='Thời gian cập nhật gần nhất'
    )
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    # Liên kết ngược với User model (backref sẽ tạo user.health_profile)
    user = db.relationship('User', backref=db.backref('health_profile', uselist=False))
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_allergies_list(self):
        """
        Chuyển JSON string thành Python list.
        
        Returns:
            list: Danh sách dị ứng, hoặc [] nếu không có
        """
        if not self.allergies:
            return []
        try:
            return json.loads(self.allergies)
        except json.JSONDecodeError:
            return []
    
    def get_chronic_conditions_list(self):
        """
        Chuyển JSON string thành Python list.
        
        Returns:
            list: Danh sách bệnh mãn tính, hoặc [] nếu không có
        """
        if not self.chronic_conditions:
            return []
        try:
            return json.loads(self.chronic_conditions)
        except json.JSONDecodeError:
            return []
    
    def get_medications_list(self):
        """
        Chuyển JSON string thành Python list.
        
        Returns:
            list: Danh sách thuốc đang dùng, hoặc [] nếu không có
        """
        if not self.medications:
            return []
        try:
            return json.loads(self.medications)
        except json.JSONDecodeError:
            return []
    
    def calculate_age(self):
        """
        Tính tuổi từ ngày sinh.
        
        Returns:
            int: Tuổi hiện tại, hoặc None nếu chưa có ngày sinh
        """
        if not self.date_of_birth:
            return None
        today = datetime.utcnow().date()
        age = today.year - self.date_of_birth.year
        # Điều chỉnh nếu chưa qua sinh nhật năm nay
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    def calculate_bmi(self):
        """
        Tính chỉ số BMI (Body Mass Index).
        
        Returns:
            float: BMI, hoặc None nếu thiếu chiều cao/cân nặng
        """
        if not self.height or not self.weight:
            return None
        height_m = self.height / 100  # Chuyển cm sang m
        bmi = self.weight / (height_m ** 2)
        return round(bmi, 2)
    
    def to_dict(self):
        """
        Chuyển object thành dictionary để trả về API.
        
        Returns:
            dict: Thông tin hồ sơ dạng JSON-serializable
        """
        return {
            'user_id': self.user_id,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.calculate_age(),
            'gender': self.gender,
            'blood_type': self.blood_type,
            'height': self.height,
            'weight': self.weight,
            'bmi': self.calculate_bmi(),
            'allergies': self.get_allergies_list(),
            'chronic_conditions': self.get_chronic_conditions_list(),
            'medications': self.get_medications_list(),
            'family_history': self.family_history,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def format_for_chatbot(self):
        """
        Format thông tin hồ sơ thành text để đưa vào prompt của chatbot.
        
        Returns:
            str: Thông tin hồ sơ dạng text dễ đọc cho AI
        """
        parts = []
        
        # Thông tin cơ bản
        age = self.calculate_age()
        if age:
            parts.append(f"Tuổi: {age}")
        if self.gender:
            gender_vn = {'Male': 'Nam', 'Female': 'Nữ', 'Other': 'Khác'}.get(self.gender, self.gender)
            parts.append(f"Giới tính: {gender_vn}")
        
        # BMI
        bmi = self.calculate_bmi()
        if bmi:
            parts.append(f"BMI: {bmi}")
        
        # Dị ứng (QUAN TRỌNG NHẤT)
        allergies = self.get_allergies_list()
        if allergies:
            parts.append(f"⚠️ DỊ ỨNG: {', '.join(allergies)}")
        
        # Bệnh mãn tính
        conditions = self.get_chronic_conditions_list()
        if conditions:
            parts.append(f"Bệnh mãn tính: {', '.join(conditions)}")
        
        # Thuốc đang dùng
        meds = self.get_medications_list()
        if meds:
            parts.append(f"Thuốc đang dùng: {', '.join(meds)}")
        
        # Tiền sử gia đình
        if self.family_history:
            parts.append(f"Tiền sử gia đình: {self.family_history}")
        
        if not parts:
            return "Chưa có thông tin hồ sơ sức khỏe."
        
        return " | ".join(parts)
    
    def __repr__(self):
        return f'<HealthProfile user_id={self.user_id} age={self.calculate_age()}>'
