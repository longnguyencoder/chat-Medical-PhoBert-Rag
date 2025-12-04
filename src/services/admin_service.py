from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.base import db
from sqlalchemy import func

def get_total_users():
    """
    Get total number of users and breakdown by verification status
    
    Returns:
        dict: Statistics about users including total, verified, and unverified counts
    """
    try:
        # Count total users
        total_users = User.query.count()
        
        # Count verified users
        verified_users = User.query.filter_by(is_verified=True).count()
        
        # Count unverified users
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
        return {
            'success': False,
            'message': f'Error retrieving user statistics: {str(e)}'
        }

def get_conversation_stats():
    """
    Get statistics about conversations
    
    Returns:
        dict: Statistics about conversations
    """
    try:
        # Count total conversations
        total_conversations = Conversation.query.count()
        
        # Count total messages
        total_messages = Message.query.count()
        
        # Calculate average messages per conversation
        avg_messages = round(total_messages / total_conversations, 2) if total_conversations > 0 else 0
        
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
        return {
            'success': False,
            'message': f'Error retrieving conversation statistics: {str(e)}'
        }

def get_all_stats():
    """
    Get all statistics (users + conversations)
    
    Returns:
        dict: Combined statistics
    """
    try:
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
                'message': 'Error retrieving statistics'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error retrieving all statistics: {str(e)}'
        }
