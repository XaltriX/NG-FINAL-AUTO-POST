from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import config

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

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
        post_data['created_at'] = datetime.now(IST)
        return self.posts.insert_one(post_data)
    
    def get_recent_posts(self, limit=10):
        """Get last N posted messages"""
        posts = list(self.posts.find().sort('created_at', -1).limit(limit))
        
        # Convert timestamps to IST
        for post in posts:
            if 'created_at' in post and post['created_at']:
                if post['created_at'].tzinfo is None:
                    post['created_at'] = post['created_at'].replace(tzinfo=IST)
                else:
                    post['created_at'] = post['created_at'].astimezone(IST)
            
            if 'posted_at' in post and post['posted_at']:
                if post['posted_at'].tzinfo is None:
                    post['posted_at'] = post['posted_at'].replace(tzinfo=IST)
                else:
                    post['posted_at'] = post['posted_at'].astimezone(IST)
        
        return posts
    
    def update_post_views(self, post_id, views):
        """Update views count for a post"""
        return self.posts.update_one(
            {'_id': post_id},
            {'$set': {'views': views, 'updated_at': datetime.now(IST)}}
        )
    
    # ========== SCHEDULED POSTS OPERATIONS ==========
    
    def save_scheduled_post(self, schedule_data):
        """Save a scheduled post"""
        schedule_data['created_at'] = datetime.now(IST)
        schedule_data['status'] = 'pending'
        
        # Ensure scheduled_time has timezone
        if 'scheduled_time' in schedule_data:
            st = schedule_data['scheduled_time']
            if st.tzinfo is None:
                schedule_data['scheduled_time'] = st.replace(tzinfo=IST)
        
        return self.scheduled_posts.insert_one(schedule_data)
    
    def get_pending_scheduled_posts(self):
        """Get all pending scheduled posts with proper timezone handling"""
        posts = list(self.scheduled_posts.find({'status': 'pending'}).sort('scheduled_time', 1))
        
        # Convert all scheduled_time to IST timezone-aware datetimes
        for post in posts:
            if 'scheduled_time' in post and post['scheduled_time']:
                st = post['scheduled_time']
                
                # If naive datetime, treat as IST
                if st.tzinfo is None:
                    post['scheduled_time'] = st.replace(tzinfo=IST)
                else:
                    # Convert to IST
                    post['scheduled_time'] = st.astimezone(IST)
            
            # Also fix created_at if present
            if 'created_at' in post and post['created_at']:
                if post['created_at'].tzinfo is None:
                    post['created_at'] = post['created_at'].replace(tzinfo=IST)
                else:
                    post['created_at'] = post['created_at'].astimezone(IST)
        
        return posts
    
    def get_pending_count(self):
        """Get count of pending scheduled posts"""
        return self.scheduled_posts.count_documents({'status': 'pending'})
    
    def update_schedule_status(self, schedule_id, status):
        """Update status of scheduled post"""
        return self.scheduled_posts.update_one(
            {'_id': schedule_id},
            {'$set': {'status': status, 'updated_at': datetime.now(IST)}}
        )
    
    def delete_scheduled_post(self, schedule_id):
        """Delete a scheduled post"""
        return self.scheduled_posts.delete_one({'_id': schedule_id})
    
    def cleanup_past_schedules(self):
        """Delete all scheduled posts that are in the past"""
        current_time = datetime.now(IST)
        
        # Get all pending posts
        pending = self.get_pending_scheduled_posts()
        
        deleted_count = 0
        for post in pending:
            if post['scheduled_time'] < current_time:
                self.delete_scheduled_post(post['_id'])
                deleted_count += 1
        
        return deleted_count
    
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
