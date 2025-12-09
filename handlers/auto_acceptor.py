from telegram import Update
from telegram.ext import ContextTypes, ChatJoinRequestHandler # Updated import
from database import db
import logging

logger = logging.getLogger(__name__)

async def handle_chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat join requests and auto-accept if enabled"""
    try:
        # The update object for ChatJoinRequestHandler directly contains the chat_join_request
        chat_join_request = update.chat_join_request
        
        if not chat_join_request:
            return
        
        chat_id = chat_join_request.chat.id
        user_id = chat_join_request.from_user.id
        
        # Get bot owner's settings (assuming bot owner is admin)
        user_settings = db.get_user_settings(chat_id)
        
        # Check if auto-acceptor is enabled for this channel
        if user_settings.get('auto_acceptor_enabled', False):
            channels = user_settings.get('channels', [])
            
            # Check if this channel has auto-acceptor enabled
            channel_enabled = any(ch['id'] == chat_id for ch in channels)
            
            if channel_enabled:
                try:
                    # Approve the join request
                    await context.bot.approve_chat_join_request(
                        chat_id=chat_id,
                        user_id=user_id
                    )
                    logger.info(f"✅ Auto-approved join request from user {user_id} in chat {chat_id}")
                except Exception as e:
                    # NOTE: The bot must be an administrator in the channel with the 
                    # "Manage Chat" and "Add New Admins" (or "Approve Join Requests") permission.
                    logger.error(f"❌ Error approving join request in chat {chat_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in auto-acceptor: {e}")


def register_auto_acceptor_handlers(application):
    """Register auto-acceptor handlers"""
    # Use ChatJoinRequestHandler for join requests
    application.add_handler(ChatJoinRequestHandler(handle_chat_join_request))
    
    logger.info("✅ Auto Request Acceptor handlers registered")