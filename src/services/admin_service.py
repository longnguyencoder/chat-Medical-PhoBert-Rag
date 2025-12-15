"""
Admin Service
=============
Service layer xử lý logic thống kê cho Admin Dashboard.
Tương tác trực tiếp với Database để query số liệu.

Chức năng:
1. Thống kê User (Verified/Unverified).
2. Thống kê Hoạt động Chat (Conversations, Messages).
"""

from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.base import db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

def get_total_users() -> dict:
    """
    Đếm số lượng người dùng trong hệ thống.
    
    Returns:
        dict: {
            'success': bool,
            'data': {
                'total_users': int,
                'verified_users': int,
                'unverified_users': int
            }
        }
    """
    try:
        # Tổng số user
        total_users = User.query.count()
        
        # Số user đã xác thực email
        verified_users = User.query.filter_by(is_verified=True).count()
        
        # Số user chưa xác thực
        unverified_users = User.query.filter_by(is_verified=False).count()
        
        return {
            'success': True,
            'data': {
                'total_users': total_users,
                'verified_users': verified_users,
                'unverified_users': unverified_users
            },
            'message': 'User statistics retrieved successfully'
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {
            'success': False,
            'message': f'Error retrieving user statistics: {str(e)}'
        }


def get_conversation_stats() -> dict:
    """
    Thống kê hoạt động Chatbot.
    
    Returns:
        dict: {
            'total_conversations': int,
            'total_messages': int,
            'avg_messages_per_conversation': float
        }
    """
    try:
        # Đếm tổng số hội thoại
        total_conversations = Conversation.query.count()
        
        # Đếm tổng số tin nhắn
        total_messages = Message.query.count()
        
        # Tính trung bình tin nhắn mỗi hội thoại
        avg_messages = 0
        if total_conversations > 0:
            avg_messages = round(total_messages / total_conversations, 2)
        
        return {
            'success': True,
            'data': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'avg_messages_per_conversation': avg_messages
            },
            'message': 'Conversation statistics retrieved successfully'
        }
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        return {
            'success': False,
            'message': f'Error retrieving conversation statistics: {str(e)}'
        }


def get_all_stats() -> dict:
    """
    Tổng hợp tất cả thống kê (User + Chat).
    Giúp Client chỉ cần gọi 1 API để lấy full data Dashboard.
    """
    try:
        # Gọi 2 hàm con
        user_stats = get_total_users()
        conversation_stats = get_conversation_stats()
        
        if user_stats['success'] and conversation_stats['success']:
            return {
                'success': True,
                'data': {
                    'users': user_stats['data'],
                    'conversations': conversation_stats['data']
                },
                'message': 'All statistics retrieved successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Error retrieving statistics (Partial failure)'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error retrieving all statistics: {str(e)}'
        }
