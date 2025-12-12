"""
Medication Schedule Model
=========================
Mô hình lưu trữ lịch uống thuốc của người dùng.

Mục đích:
- Lưu thông tin lịch uống thuốc (tên thuốc, liều lượng, tần suất, thời gian)
- Hỗ trợ nhắc nhở tự động qua email và local notification
- Tích hợp với chatbot để theo dõi tuân thủ
"""

from datetime import datetime
from src.models.base import db
import json


class MedicationSchedule(db.Model):
    """
    Bảng lưu lịch uống thuốc của người dùng.
    
    Quan hệ: 1 User - N MedicationSchedules (One-to-Many)
    """
    __tablename__ = 'MedicationSchedules'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    schedule_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    
    # ========================================================================
    # FOREIGN KEY
    # ========================================================================
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='ID người dùng'
    )
    
    # ========================================================================
    # THÔNG TIN THUỐC
    # ========================================================================
    medication_name = db.Column(
        db.String(200),
        nullable=False,
        comment='Tên thuốc (VD: Paracetamol, Vitamin C)'
    )
    
    dosage = db.Column(
        db.String(100),
        nullable=True,
        comment='Liều lượng (VD: "500mg", "2 viên", "1 thìa")'
    )
    
    # ========================================================================
    # LỊCH TRÌNH
    # ========================================================================
    frequency = db.Column(
        db.String(50),
        nullable=False,
        default='daily',
        comment='Tần suất: daily, twice_daily, three_times_daily, weekly, custom'
    )
    
    time_of_day = db.Column(
        db.Text,
        nullable=False,
        comment='Thời gian trong ngày (JSON array). VD: ["08:00", "20:00"] cho 2 lần/ngày'
    )
    
    start_date = db.Column(
        db.Date,
        nullable=False,
        default=datetime.utcnow,
        comment='Ngày bắt đầu uống thuốc'
    )
    
    end_date = db.Column(
        db.Date,
        nullable=True,
        comment='Ngày kết thúc (nullable nếu uống dài hạn)'
    )
    
    # ========================================================================
    # THÔNG TIN BỔ SUNG
    # ========================================================================
    notes = db.Column(
        db.Text,
        nullable=True,
        comment='Ghi chú thêm (VD: "Uống sau ăn", "Không uống với sữa")'
    )
    
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        comment='Trạng thái kích hoạt (False = tạm dừng nhắc nhở)'
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='Thời gian tạo lịch'
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
    user = db.relationship('User', backref=db.backref('medication_schedules', lazy=True))
    logs = db.relationship('MedicationLog', backref='schedule', lazy=True, cascade='all, delete-orphan')
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_time_of_day_list(self):
        """
        Chuyển JSON string thành Python list.
        
        Returns:
            list: Danh sách thời gian, VD: ["08:00", "20:00"]
        """
        if not self.time_of_day:
            return []
        try:
            return json.loads(self.time_of_day)
        except json.JSONDecodeError:
            return []
    
    def set_time_of_day_list(self, time_list):
        """
        Chuyển Python list thành JSON string để lưu vào DB.
        
        Args:
            time_list (list): Danh sách thời gian, VD: ["08:00", "20:00"]
        """
        self.time_of_day = json.dumps(time_list)
    
    def is_active_today(self):
        """
        Kiểm tra lịch có còn active cho hôm nay không.
        
        Returns:
            bool: True nếu lịch đang active và chưa hết hạn
        """
        if not self.is_active:
            return False
        
        today = datetime.utcnow().date()
        
        # Kiểm tra đã bắt đầu chưa
        if today < self.start_date:
            return False
        
        # Kiểm tra đã hết hạn chưa
        if self.end_date and today > self.end_date:
            return False
        
        return True
    
    def to_dict(self):
        """
        Chuyển object thành dictionary để trả về API.
        
        Returns:
            dict: Thông tin lịch dạng JSON-serializable
        """
        return {
            'schedule_id': self.schedule_id,
            'user_id': self.user_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage or "",  # Return empty string to prevent client null error
            'frequency': self.frequency,
            'time_of_day': self.get_time_of_day_list(),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes or "",  # Return empty string to prevent client null error
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MedicationSchedule {self.schedule_id}: {self.medication_name} for user {self.user_id}>'
