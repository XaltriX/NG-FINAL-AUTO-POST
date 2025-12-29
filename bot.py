#!/usr/bin/env python3
"""
LinkzWallah Telegram Post Bot
Main entry point for the bot
"""
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, PicklePersistence
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
    
    # Handle NoneType attribute errors
    if isinstance(context.error, AttributeError):
        error_msg = str(context.error)
        if "'NoneType' object has no attribute 'message'" in error_msg:
            logger.warning("Callback query message is None - this is normal for inline queries")
            return
        logger.error(f"AttributeError: {context.error}")
        return
    
    # For other errors, try to notify user
    if update and isinstance(update, Update):
        message = None
        if update.effective_message:
            message = update.effective_message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        elif update.callback_query:
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
    
    # Add persistence to save conversation state
    persistence = PicklePersistence(filepath="bot_data.pkl")
    
    # Create application with persistence
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
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
    logger.info("⚠️ IMPORTANT: Listening for chat_join_request updates")
    
    application.run_polling(
        allowed_updates=[
            "message", 
            "callback_query", 
            "chat_join_request",
            "chat_member"
        ],
        drop_pending_updates=False
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
