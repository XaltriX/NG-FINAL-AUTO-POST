from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import db
from utils import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Get pending posts count
    pending_count = db.get_pending_count()
    
    welcome_message = f"""
🎉 **Welcome to LinkzWallah Bot!** 🎉

Hello {user.first_name}! 👋

**Bot Features:**
✨ Create stunning posts with templates
📅 Schedule posts for later
📊 Track post analytics & views
⚙️ Auto-accept join requests

**📅 Pending Posts:** {pending_count}

Choose an option below to get started:
"""
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=main_menu_keyboard(pending_count),
        parse_mode='Markdown'
    )


async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu"""
    query = update.callback_query
    await query.answer()
    
    pending_count = db.get_pending_count()
    
    welcome_message = """
🏠 **Main Menu**

Choose an option:
"""
    
    await query.edit_message_text(
        welcome_message,
        reply_markup=main_menu_keyboard(pending_count),
        parse_mode='Markdown'
    )


def register_start_handlers(application):
    """Register start-related handlers"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main$"))