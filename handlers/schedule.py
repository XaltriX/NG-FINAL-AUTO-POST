from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from utils import (
    schedule_time_keyboard,
    back_to_main_keyboard,
    get_next_hour,
    get_time_offset,
    validate_datetime_format,
    parse_datetime,
    is_future_datetime,
    format_datetime
)
from datetime import datetime

# Conversation states
AWAIT_CUSTOM_TIME = range(1)

async def schedule_new_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start scheduling a new post"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📅 **Schedule New Post**\n\n"
        "⚠️ This feature requires you to create a post first.\n\n"
        "Please use **Create New Post** first, then select **Schedule This Post** from the preview.",
        reply_markup=back_to_main_keyboard(),
        parse_mode='Markdown'
    )


async def schedule_this_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule the current post being previewed"""
    query = update.callback_query
    await query.answer()
    
    # Check if there's a post in user_data
    if 'generated_text' not in context.user_data:
        await query.edit_message_text(
            "❌ No post found to schedule!\n\n"
            "Please create a post first.",
            reply_markup=back_to_main_keyboard()
        )
        return
    
    await query.edit_message_text(
        "⏰ **Select Schedule Time:**\n\n"
        "Choose when you want to post this:",
        reply_markup=schedule_time_keyboard(),
        parse_mode='Markdown'
    )


async def schedule_next_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for next hour"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_next_hour()
    await save_scheduled_post(update, context, scheduled_time)


async def schedule_2_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for +2 hours"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_time_offset(2)
    await save_scheduled_post(update, context, scheduled_time)


async def schedule_6_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for +6 hours"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_time_offset(6)
    await save_scheduled_post(update, context, scheduled_time)


async def schedule_custom_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for custom datetime"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📅 **Custom Date & Time**\n\n"
        "Enter the date and time in this format:\n"
        "`DD/MM/YYYY HH:MM`\n\n"
        "Example: `25/12/2024 15:30`",
        reply_markup=back_to_main_keyboard(),
        parse_mode='Markdown'
    )
    return AWAIT_CUSTOM_TIME


async def receive_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate custom datetime"""
    time_str = update.message.text.strip()
    
    if not validate_datetime_format(time_str):
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Please use: `DD/MM/YYYY HH:MM`\n"
            "Example: `25/12/2024 15:30`",
            reply_markup=back_to_main_keyboard(),
            parse_mode='Markdown'
        )
        return AWAIT_CUSTOM_TIME
    
    scheduled_time = parse_datetime(time_str)
    
    if not is_future_datetime(scheduled_time):
        await update.message.reply_text(
            "❌ Time must be in the future!\n\n"
            "Please enter a future date and time.",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_CUSTOM_TIME
    
    await save_scheduled_post(update, context, scheduled_time)
    return ConversationHandler.END


async def save_scheduled_post(update, context, scheduled_time):
    """Save the scheduled post to database"""
    post_data = context.user_data.get('post_data', {})
    post_type = context.user_data.get('post_type')
    generated_text = context.user_data.get('generated_text')
    
    # Prepare schedule data
    schedule_data = {
        'user_id': update.effective_user.id,
        'post_type': post_type,
        'post_data': post_data,
        'generated_text': generated_text,
        'scheduled_time': scheduled_time,
        'channel_ids': [],  # TODO: Add channel selection
        'status': 'pending'
    }
    
    # Save to database
    result = db.save_scheduled_post(schedule_data)
    
    success_msg = f"""
✅ **Post Scheduled Successfully!**

📅 **Scheduled Time:** {format_datetime(scheduled_time)}
📝 **Type:** {post_type}

Your post will be automatically published at the scheduled time.

You can view/edit this in the Dashboard.
"""
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(
            success_msg,
            reply_markup=back_to_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            success_msg,
            reply_markup=back_to_main_keyboard(),
            parse_mode='Markdown'
        )
    
    # Clear user data
    context.user_data.clear()


async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel scheduling"""
    query = update.callback_query
    await query.answer("Scheduling cancelled")
    
    await query.edit_message_text(
        "❌ Scheduling cancelled.",
        reply_markup=back_to_main_keyboard()
    )
    return ConversationHandler.END


def register_schedule_handlers(application):
    """Register schedule handlers"""
    # Main schedule callbacks
    application.add_handler(CallbackQueryHandler(schedule_new_callback, pattern="^schedule_new$"))
    application.add_handler(CallbackQueryHandler(schedule_this_callback, pattern="^schedule_this$"))
    
    # Quick schedule options
    application.add_handler(CallbackQueryHandler(schedule_next_hour, pattern="^schedule_next_hour$"))
    application.add_handler(CallbackQueryHandler(schedule_2_hours, pattern="^schedule_2_hours$"))
    application.add_handler(CallbackQueryHandler(schedule_6_hours, pattern="^schedule_6_hours$"))
    
    # Custom time conversation
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(schedule_custom_callback, pattern="^schedule_custom$"),
        ],
        states={
            AWAIT_CUSTOM_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_time)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_schedule, pattern="^cancel_schedule$"),
        ],
    )
    
    application.add_handler(conv_handler)