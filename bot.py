#!/usr/bin/env python3
"""
LinkzWallah Telegram Post Bot
Main entry point for the bot
"""

import logging
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.error import TimedOut, NetworkError, TelegramError
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
    from telegram.error import BadRequest
    if isinstance(context.error, BadRequest):
        logger.error(f"BadRequest error: {context.error}")
        if update and isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ Message formatting error. Please try again or use /start to restart."
                )
            except:
                pass
        return
    
    # For other errors, try to notify user
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
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