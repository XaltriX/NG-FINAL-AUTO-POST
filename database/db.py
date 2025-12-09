from pymongo import MongoClient
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URL)
        self.db = self.client[config.DATABASE_NAME]
        self.posts = self.db[config.POSTS_COLLECTION]
        self.scheduled_posts = self.db[config.SCHEDULED_POSTS_COLLECTION]
        self.settings = self.db[config.SETTINGS_COLLECTION]
    
    # ========== POSTS OPERATIONS ==========
    
    def save_post(self, post_data):
        """Save a posted message to database"""
        post_data['created_at'] = datetime.now()
        return self.posts.insert_one(post_data)
    
    def get_recent_posts(self, limit=10):
        """Get last N posted messages"""
        return list(self.posts.find().sort('created_at', -1).limit(limit))
    
    def update_post_views(self, post_id, views):
        """Update views count for a post"""
        return self.posts.update_one(
            {'_id': post_id},
            {'$set': {'views': views, 'updated_at': datetime.now()}}
        )
    
    # ========== SCHEDULED POSTS OPERATIONS ==========
    
    def save_scheduled_post(self, schedule_data):
        """Save a scheduled post"""
        schedule_data['created_at'] = datetime.now()
        schedule_data['status'] = 'pending'
        return self.scheduled_posts.insert_one(schedule_data)
    
    def get_pending_scheduled_posts(self):
        """Get all pending scheduled posts"""
        return list(self.scheduled_posts.find({'status': 'pending'}).sort('scheduled_time', 1))
    
    def get_pending_count(self):
        """Get count of pending scheduled posts"""
        return self.scheduled_posts.count_documents({'status': 'pending'})
    
    def update_schedule_status(self, schedule_id, status):
        """Update status of scheduled post"""
        return self.scheduled_posts.update_one(
            {'_id': schedule_id},
            {'$set': {'status': status, 'updated_at': datetime.now()}}
        )
    
    def delete_scheduled_post(self, schedule_id):
        """Delete a scheduled post"""
        return self.scheduled_posts.delete_one({'_id': schedule_id})
    
    # ========== SETTINGS OPERATIONS ==========
    
    def get_user_settings(self, user_id):
        """Get user settings"""
        settings = self.settings.find_one({'user_id': user_id})
        if not settings:
            # Create default settings
            settings = {
                'user_id': user_id,
                'auto_acceptor_enabled': False,
                'channels': []
            }
            self.settings.insert_one(settings)
        return settings
    
    def update_user_settings(self, user_id, settings_data):
        """Update user settings"""
        return self.settings.update_one(
            {'user_id': user_id},
            {'$set': settings_data},
            upsert=True
        )

# Initialize database
db = Database()