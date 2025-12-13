#!/usr/bin/env python3
"""
LinkzWallah Telegram Post Bot
Main entry point for the bot
"""
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.error import TimedOut, NetworkError, TelegramError, BadRequest
import config
from handlers import register_all_handlers
from scheduler import PostScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors caused by updates"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Handle timeout errors gracefully
    if isinstance(context.error, TimedOut):
        logger.warning("Request timed out, but continuing...")
        return
    
    # Handle network errors
    if isinstance(context.error, NetworkError):
        logger.warning("Network error occurred, but continuing...")
        return
    
    # Handle BadRequest errors (formatting issues)
    if isinstance(context.error, BadRequest):
        logger.error(f"BadRequest error: {context.error}")
        if update and isinstance(update, Update):
            # Try to get message from either effective_message or callback_query
            message = None
            if update.effective_message:
                message = update.effective_message
            elif update.callback_query and update.callback_query.message:
                message = update.callback_query.message
            
            if message:
                try:
                    await message.reply_text(
                        "⚠️ Message formatting error. Please try again or use /start to restart."
                    )
                except:
                    pass
        return
    
    # Handle NoneType attribute errors (callback_query.message is None)
    if isinstance(context.error, AttributeError):
        error_msg = str(context.error)
        if "'NoneType' object has no attribute 'message'" in error_msg:
            logger.warning("Callback query message is None - this is normal for inline queries")
            return
        logger.error(f"AttributeError: {context.error}")
        return
    
    # For other errors, try to notify user
    if update and isinstance(update, Update):
        # Try multiple ways to get a message object
        message = None
        if update.effective_message:
            message = update.effective_message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        elif update.callback_query:
            # For inline queries without message, try to answer the callback
            try:
                await update.callback_query.answer(
                    "⚠️ An error occurred. Please try again.",
                    show_alert=True
                )
            except:
                pass
            return
        
        if message:
            try:
                await message.reply_text(
                    "⚠️ An error occurred. Please try again or use /start to restart."
                )
            except Exception as e:
                logger.error(f"Could not send error message to user: {e}")

def main():
    """Main function to run the bot"""
    logger.info("Starting LinkzWallah Bot...")
    
    # Create application with increased timeouts and connection pooling
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .connect_timeout(30)  # Increase connection timeout
        .read_timeout(30)     # Increase read timeout
        .write_timeout(30)    # Increase write timeout
        .pool_timeout(30)     # Increase pool timeout
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )
    
    # Add error handler
    application.add_error_handler(error_handler)
    logger.info("Error handler registered")
    
    # Register all handlers
    register_all_handlers(application)
    logger.info("All handlers registered successfully")
    
    # Initialize and start scheduler
    scheduler = PostScheduler(application.bot)
    scheduler.start()
    logger.info("Post scheduler started")
    
    # Start the bot
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    application.run_polling(
        allowed_updates=["message", "callback_query", "chat_join_request", "chat_member"],
        drop_pending_updates=True  # Drop old pending updates on restart
    )
    
    # Stop scheduler on exit
    scheduler.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
