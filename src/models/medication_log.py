"""
Medication Log Model
====================
Mô hình lưu trữ lịch sử tuân thủ uống thuốc của người dùng.

Mục đích:
- Ghi nhận mỗi lần uống thuốc (đã uống, bỏ qua, hoặc đang chờ)
- Tính toán thống kê tuân thủ (compliance rate)
- Cung cấp dữ liệu cho chatbot để hỏi về việc uống thuốc
"""

from datetime import datetime
from src.models.base import db


class MedicationLog(db.Model):
    """
    Bảng lưu lịch sử tuân thủ uống thuốc.
    
    Quan hệ: 
    - 1 MedicationSchedule - N MedicationLogs (One-to-Many)
    - 1 User - N MedicationLogs (One-to-Many)
    """
    __tablename__ = 'MedicationLogs'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    log_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    
    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey('MedicationSchedules.schedule_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='ID lịch uống thuốc'
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='ID người dùng'
    )
    
    # ========================================================================
    # THÔNG TIN LOG
    # ========================================================================
    scheduled_time = db.Column(
        db.DateTime,
        nullable=False,
        index=True,
        comment='Thời gian dự kiến uống thuốc (GMT+7)'
    )
    
    actual_time = db.Column(
        db.DateTime,
        nullable=True,
        comment='Thời gian thực tế uống thuốc (nullable nếu chưa uống hoặc bỏ qua)'
    )
    
    status = db.Column(
        db.String(20),
        nullable=False,
        default='pending',
        comment='Trạng thái: pending (chờ), taken (đã uống), skipped (bỏ qua)'
    )
    
    note = db.Column(
        db.Text,
        nullable=True,
        comment='Ghi chú từ người dùng (VD: "Uống muộn 30 phút", "Quên mang thuốc")'
    )
    
    # ========================================================================
    # METADATA
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='Thời gian tạo log'
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
    user = db.relationship('User', backref=db.backref('medication_logs', lazy=True))
    # schedule relationship is defined in MedicationSchedule model
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def mark_as_taken(self, note=None):
        """
        Đánh dấu đã uống thuốc.
        
        Args:
            note (str, optional): Ghi chú thêm
        """
        self.status = 'taken'
        self.actual_time = datetime.utcnow()
        if note:
            self.note = note
    
    def mark_as_skipped(self, note=None):
        """
        Đánh dấu bỏ qua.
        
        Args:
            note (str, optional): Ghi chú lý do bỏ qua
        """
        self.status = 'skipped'
        self.actual_time = None
        if note:
            self.note = note
    
    def is_overdue(self):
        """
        Kiểm tra có quá hạn chưa (quá 2 giờ so với thời gian dự kiến).
        
        Returns:
            bool: True nếu đã quá 2 giờ và vẫn pending
        """
        if self.status != 'pending':
            return False
        
        now = datetime.utcnow()
        time_diff = (now - self.scheduled_time).total_seconds() / 3600  # Convert to hours
        return time_diff > 2
    
    def to_dict(self):
        """
        Chuyển object thành dictionary để trả về API.
        
        Returns:
            dict: Thông tin log dạng JSON-serializable
        """
        return {
            'log_id': self.log_id,
            'schedule_id': self.schedule_id,
            'user_id': self.user_id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'actual_time': self.actual_time.isoformat() if self.actual_time else None,
            'status': self.status,
            'note': self.note,
            'is_overdue': self.is_overdue(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MedicationLog {self.log_id}: {self.status} for schedule {self.schedule_id}>'
