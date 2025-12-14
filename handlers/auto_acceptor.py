from telegram import Update
from telegram.ext import ContextTypes, ChatJoinRequestHandler
from database import db
import config  # Import config to get OWNER_ID
import logging

logger = logging.getLogger(__name__)

async def handle_chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat join requests and auto-accept if enabled"""
    try:
        chat_join_request = update.chat_join_request
        
        if not chat_join_request:
            logger.warning("⚠️ No chat_join_request in update")
            return
        
        chat_id = chat_join_request.chat.id
        user_id = chat_join_request.from_user.id
        chat_title = chat_join_request.chat.title or "Unknown"
        user_name = chat_join_request.from_user.first_name or "Unknown"
        
        logger.info(f"🔔 Join request from {user_name} (ID: {user_id}) in {chat_title} (ID: {chat_id})")
        
        # Get bot owner's settings
        # If OWNER_ID is not in config, use first admin who set up the bot
        owner_id = getattr(config, 'OWNER_ID', None)
        
        if not owner_id:
            logger.warning("⚠️ OWNER_ID not set in config.py - auto-acceptor may not work properly")
            return
        
        # Get owner's settings
        owner_settings = db.get_user_settings(owner_id)
        
        # Check if auto-acceptor is globally enabled
        if not owner_settings.get('auto_acceptor_enabled', False):
            logger.info(f"⏸️ Auto-acceptor globally disabled")
            return
        
        # Check if this specific channel has auto-acceptor enabled
        channels = owner_settings.get('channels', [])
        channel_config = next((ch for ch in channels if ch['id'] == chat_id), None)
        
        if not channel_config:
            logger.info(f"⏸️ Channel {chat_id} not configured in bot settings")
            return
        
        # Check if auto-accept is enabled for this channel
        if channel_config.get('auto_accept_requests', True):  # Default True if not specified
            try:
                # Approve the join request
                await context.bot.approve_chat_join_request(
                    chat_id=chat_id,
                    user_id=user_id
                )
                logger.info(f"✅ Auto-approved join request from {user_name} (ID: {user_id}) in {chat_title}")
            
            except Exception as e:
                error_msg = str(e)
                
                if "not enough rights" in error_msg.lower() or "forbidden" in error_msg.lower():
                    logger.error(f"❌ Bot doesn't have permission to approve join requests in {chat_title}")
                    logger.error("   📝 Solution: Make bot admin with 'Add Members' or 'Invite Users' permission")
                elif "chat not found" in error_msg.lower():
                    logger.error(f"❌ Chat {chat_id} not found or bot is not a member")
                elif "user_not_participant" in error_msg.lower():
                    logger.error(f"❌ Bot is not a participant in {chat_title}")
                else:
                    logger.error(f"❌ Error approving join request in {chat_title}: {e}")
        else:
            logger.info(f"⏸️ Auto-acceptor disabled for channel {chat_title}")
    
    except Exception as e:
        logger.error(f"❌ Error in auto-acceptor handler: {e}", exc_info=True)


def register_auto_acceptor_handlers(application):
    """Register auto-acceptor handlers"""
    application.add_handler(ChatJoinRequestHandler(handle_chat_join_request))
    logger.info("✅ Auto Request Acceptor handlers registered")
