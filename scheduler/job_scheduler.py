from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from database import db
from templates import template_a, template_b, template_c, template_d
from utils import post_buttons_with_links
import logging

logger = logging.getLogger(__name__)

class PostScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        # Check for pending posts every minute
        self.scheduler.add_job(
            self.check_pending_posts,
            'interval',
            minutes=1,
            id='check_pending_posts'
        )
        self.scheduler.start()
        logger.info("Scheduler started")
    
    async def check_pending_posts(self):
        """Check and post pending scheduled posts"""
        try:
            logger.info("🔍 Checking pending scheduled posts...")
            pending_posts = db.get_pending_scheduled_posts()
            logger.info(f"📌 Found {len(pending_posts)} pending posts")
            
            # IST timezone
            from datetime import timezone, timedelta
            IST = timezone(timedelta(hours=5, minutes=30))
            current_time = datetime.now(IST)
            
            logger.info(f"⏰ Current IST time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            for post in pending_posts:
                scheduled_time = post['scheduled_time']
                
                # Make sure scheduled_time has timezone
                if scheduled_time.tzinfo is None:
                    # If naive, assume it's IST
                    scheduled_time = scheduled_time.replace(tzinfo=IST)
                    logger.info(f"📅 Post scheduled (naive→IST): {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                else:
                    # Convert to IST for comparison
                    scheduled_time = scheduled_time.astimezone(IST)
                    logger.info(f"📅 Post scheduled (converted): {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
                # Check if it's time to post
                if current_time >= scheduled_time:
                    logger.info(f"⏰ Time to post NOW: {post['_id']}")
                    await self.publish_scheduled_post(post)
                else:
                    time_diff = (scheduled_time - current_time).total_seconds() / 60
                    logger.info(f"⏳ Post {post['_id']} will post in {time_diff:.1f} minutes")
        
        except Exception as e:
            logger.error(f"❌ Error checking pending posts: {e}", exc_info=True)
    
    async def publish_scheduled_post(self, post):
        """Publish a scheduled post"""
        try:
            post_type = post['post_type']
            post_data = post['post_data']
            generated_text = post['generated_text']
            channel_ids = post.get('channel_ids', [])
            
            # If no channels specified, skip
            if not channel_ids:
                logger.warning(f"No channels specified for post {post['_id']}")
                db.update_schedule_status(post['_id'], 'failed')
                return
            
            # Create buttons with URLs (optional - only More Channels button)
            how_to = post_data.get('how_to_link')
            buttons = post_buttons_with_links(
                post_data['preview_link'],
                post_data['download_link'],
                how_to
            ) if post_data.get('preview_link') else None
            
            # Post to each channel
            for channel_id in channel_ids:
                try:
                    # Check if Type A (has media)
                    if post_type == 'A' and 'media_file_id' in post_data:
                        media_type = post_data['media_type']
                        file_id = post_data['media_file_id']
                        
                        if media_type == 'photo':
                            sent_message = await self.bot.send_photo(
                                chat_id=channel_id,
                                photo=file_id,
                                caption=generated_text,
                                reply_markup=buttons,
                                parse_mode='MarkdownV2',
                                disable_web_page_preview=False
                            )
                        elif media_type == 'video':
                            sent_message = await self.bot.send_video(
                                chat_id=channel_id,
                                video=file_id,
                                caption=generated_text,
                                reply_markup=buttons,
                                parse_mode='MarkdownV2'
                            )
                        elif media_type == 'animation':
                            sent_message = await self.bot.send_animation(
                                chat_id=channel_id,
                                animation=file_id,
                                caption=generated_text,
                                reply_markup=buttons,
                                parse_mode='MarkdownV2'
                            )
                    else:
                        # Text-only post
                        sent_message = await self.bot.send_message(
                            chat_id=channel_id,
                            text=generated_text,
                            reply_markup=buttons,
                            parse_mode='MarkdownV2',
                            disable_web_page_preview=True  # DISABLE PREVIEW
                        )
                    
                    # Save to posts collection
                    save_data = {
                        'type': post_type,
                        'title': post_data.get('title', ''),
                        'preview_link': post_data.get('preview_link'),
                        'download_link': post_data.get('download_link'),
                        'how_to_link': post_data.get('how_to_link'),
                        'message_id': sent_message.message_id,
                        'chat_id': channel_id,
                        'posted_at': datetime.now(),
                        'views': 0
                    }
                    
                    if post_type == 'A':
                        save_data['media_file_id'] = post_data.get('media_file_id')
                        save_data['media_type'] = post_data.get('media_type')
                    
                    db.save_post(save_data)
                    logger.info(f"Posted to channel {channel_id}")
                
                except Exception as e:
                    logger.error(f"Error posting to channel {channel_id}: {e}")
            
            # Mark as posted
            db.update_schedule_status(post['_id'], 'posted')
            logger.info(f"Scheduled post {post['_id']} published successfully")
        
        except Exception as e:
            logger.error(f"Error publishing scheduled post: {e}")
            db.update_schedule_status(post['_id'], 'failed')
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
