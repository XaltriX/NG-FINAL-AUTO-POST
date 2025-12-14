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
        # Convert IST to UTC for MongoDB storage
        post_data['created_at'] = datetime.now(IST).astimezone(timezone.utc)
        return self.posts.insert_one(post_data)
    
    def get_recent_posts(self, limit=10):
        """Get last N posted messages"""
        posts = list(self.posts.find().sort('created_at', -1).limit(limit))
        
        # Convert UTC timestamps back to IST
        for post in posts:
            if 'created_at' in post and post['created_at']:
                # MongoDB returns naive UTC datetime, add UTC timezone then convert to IST
                if post['created_at'].tzinfo is None:
                    post['created_at'] = post['created_at'].replace(tzinfo=timezone.utc).astimezone(IST)
                else:
                    post['created_at'] = post['created_at'].astimezone(IST)
            
            if 'posted_at' in post and post['posted_at']:
                if post['posted_at'].tzinfo is None:
                    post['posted_at'] = post['posted_at'].replace(tzinfo=timezone.utc).astimezone(IST)
                else:
                    post['posted_at'] = post['posted_at'].astimezone(IST)
        
        return posts
    
    def update_post_views(self, post_id, views):
        """Update views count for a post"""
        return self.posts.update_one(
            {'_id': post_id},
            {'$set': {'views': views, 'updated_at': datetime.now(IST).astimezone(timezone.utc)}}
        )
    
    # ========== SCHEDULED POSTS OPERATIONS ==========
    
    def save_scheduled_post(self, schedule_data):
        """Save a scheduled post - CRITICAL: Store in UTC"""
        schedule_data['created_at'] = datetime.now(IST).astimezone(timezone.utc)
        schedule_data['status'] = 'pending'
        
        # CRITICAL: Convert scheduled_time from IST to UTC for storage
        if 'scheduled_time' in schedule_data:
            st = schedule_data['scheduled_time']
            
            # If naive, assume IST
            if st.tzinfo is None:
                st = st.replace(tzinfo=IST)
            
            # Convert to UTC for MongoDB storage
            schedule_data['scheduled_time'] = st.astimezone(timezone.utc)
        
        result = self.scheduled_posts.insert_one(schedule_data)
        return result
    
    def get_pending_scheduled_posts(self):
        """Get all pending scheduled posts - CRITICAL: Convert UTC back to IST"""
        posts = list(self.scheduled_posts.find({'status': 'pending'}).sort('scheduled_time', 1))
        
        # Convert all UTC times back to IST
        for post in posts:
            if 'scheduled_time' in post and post['scheduled_time']:
                st = post['scheduled_time']
                
                # MongoDB returns naive UTC datetime
                # Add UTC timezone, then convert to IST
                if st.tzinfo is None:
                    post['scheduled_time'] = st.replace(tzinfo=timezone.utc).astimezone(IST)
                else:
                    post['scheduled_time'] = st.astimezone(IST)
            
            if 'created_at' in post and post['created_at']:
                if post['created_at'].tzinfo is None:
                    post['created_at'] = post['created_at'].replace(tzinfo=timezone.utc).astimezone(IST)
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
            {'$set': {'status': status, 'updated_at': datetime.now(IST).astimezone(timezone.utc)}}
        )
    
    def delete_scheduled_post(self, schedule_id):
        """Delete a scheduled post"""
        return self.scheduled_posts.delete_one({'_id': schedule_id})
    
    def cleanup_past_schedules(self):
        """Delete all scheduled posts that are in the past"""
        current_time_utc = datetime.now(IST).astimezone(timezone.utc)
        
        # Delete directly from MongoDB using UTC comparison
        result = self.scheduled_posts.delete_many({
            'status': 'pending',
            'scheduled_time': {'$lt': current_time_utc}
        })
        
        return result.deleted_count
    
    # ========== SETTINGS OPERATIONS ==========
    
    def get_user_settings(self, user_id):
        """Get user settings"""
        settings = self.settings.find_one({'user_id': user_id})
        if not settings:
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
