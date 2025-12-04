from flask_restx import Resource, Namespace
from src.services.admin_service import get_total_users, get_conversation_stats, get_all_stats
from src.utils.auth_middleware import admin_required

# Create namespace for admin endpoints
admin_ns = Namespace('admin', description='Admin statistics and management operations')

@admin_ns.route('/stats/users')
class UserStats(Resource):
    @admin_ns.doc('get_user_statistics')
    @admin_required
    def get(self, current_user):
        """
        Get total number of users
        Returns statistics about registered users including total, verified, and unverified counts
        """
        result = get_total_users()
        
        if result['success']:
            return result, 200
        else:
            return result, 500

@admin_ns.route('/stats/conversations')
class ConversationStats(Resource):
    @admin_ns.doc('get_conversation_statistics')
    @admin_required
    def get(self, current_user):
        """
        Get conversation statistics
        Returns statistics about conversations and messages
        """
        result = get_conversation_stats()
        
        if result['success']:
            return result, 200
        else:
            return result, 500

@admin_ns.route('/stats/all')
class AllStats(Resource):
    @admin_ns.doc('get_all_statistics')
    @admin_required
    def get(self, current_user):
        """
        Get all statistics
        Returns combined statistics about users, conversations, and messages
        """
        result = get_all_stats()
        
        if result['success']:
            return result, 200
        else:
            return result, 500
