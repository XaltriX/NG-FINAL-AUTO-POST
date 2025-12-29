from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Conversation states
AWAIT_CUSTOM_TIME, SELECT_CHANNELS = range(2)

async def schedule_new_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start scheduling a new post"""
    query = update.callback_query
    await query.answer()
    
    if not query.message:
        await query.answer("⚠️ Cannot schedule from here", show_alert=True)
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📅 **Schedule New Post**\n\n"
        "⚠️ This feature requires you to create a post first.\n\n"
        "Please use **Create New Post** first, then select **Schedule This Post** from the preview.",
        reply_markup=back_to_main_keyboard(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def schedule_this_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule the current post being previewed"""
    query = update.callback_query
    await query.answer()
    
    if not query.message:
        await query.answer("⚠️ Cannot schedule from here", show_alert=True)
        return ConversationHandler.END
    
    # Check if there's a post in user_data
    if 'generated_text' not in context.user_data:
        await query.edit_message_text(
            "❌ No post found to schedule!\n\n"
            "Please create a post first.",
            reply_markup=back_to_main_keyboard()
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        "⏰ **Select Schedule Time:**\n\n"
        "Choose when you want to post this:",
        reply_markup=schedule_time_keyboard(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def schedule_next_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for next hour"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_next_hour()
    context.user_data['scheduled_time'] = scheduled_time
    
    logger.info(f"User scheduled for next hour: {scheduled_time}")
    
    # Now show channel selection
    return await show_channel_selection(update, context)


async def schedule_2_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for +2 hours"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_time_offset(2)
    context.user_data['scheduled_time'] = scheduled_time
    
    logger.info(f"User scheduled for +2 hours: {scheduled_time}")
    
    # Now show channel selection
    return await show_channel_selection(update, context)


async def schedule_6_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule for +6 hours"""
    query = update.callback_query
    await query.answer()
    
    scheduled_time = get_time_offset(6)
    context.user_data['scheduled_time'] = scheduled_time
    
    logger.info(f"User scheduled for +6 hours: {scheduled_time}")
    
    # Now show channel selection
    return await show_channel_selection(update, context)


async def schedule_custom_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for custom datetime"""
    query = update.callback_query
    await query.answer()
    
    if not query.message:
        await query.answer("⚠️ Cannot schedule from here", show_alert=True)
        return ConversationHandler.END
    
    logger.info("User selected custom date/time")
    
    await query.edit_message_text(
        "📅 **Custom Date & Time**\n\n"
        "Enter the date and time in this format:\n"
        "`DD/MM/YYYY HH:MM`\n\n"
        "Example: `25/12/2024 15:30`\n\n"
        "⏰ Current IST: " + format_datetime(datetime.now(IST)),
        reply_markup=back_to_main_keyboard(),
        parse_mode='Markdown'
    )
    return AWAIT_CUSTOM_TIME


async def receive_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate custom datetime"""
    time_str = update.message.text.strip()
    
    logger.info(f"Received custom time input: {time_str}")
    
    if not validate_datetime_format(time_str):
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Please use: DD/MM/YYYY HH:MM\n"
            "Example: 25/12/2024 15:30",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_CUSTOM_TIME
    
    scheduled_time = parse_datetime(time_str)
    
    if not scheduled_time:
        await update.message.reply_text(
            "❌ Error parsing time!",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_CUSTOM_TIME
    
    if not is_future_datetime(scheduled_time):
        await update.message.reply_text(
            "❌ Time must be in the future!\n\n"
            f"You entered: {format_datetime(scheduled_time)}\n"
            f"Current IST: {format_datetime(datetime.now(IST))}",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_CUSTOM_TIME
    
    # Show confirmation with IST time
    await update.message.reply_text(
        f"✅ Time set to: {format_datetime(scheduled_time)}\n\nProceeding to channel selection..."
    )
    
    context.user_data['scheduled_time'] = scheduled_time
    
    logger.info(f"Scheduled time set: {scheduled_time}")
    
    # Now show channel selection
    return await show_channel_selection(update, context)


async def show_channel_selection(update, context):
    """Show channel selection for scheduling"""
    user_id = update.effective_user.id
    user_settings = db.get_user_settings(user_id)
    channels = user_settings.get('channels', [])
    
    if not channels:
        msg = "❌ No channels found!\n\nPlease add channels first:\nSettings → Manage Channels"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            if not update.callback_query.message:
                await update.callback_query.answer(msg, show_alert=True)
                return ConversationHandler.END
            
            try:
                await update.callback_query.edit_message_text(
                    msg,
                    reply_markup=back_to_main_keyboard()
                )
            except:
                await update.callback_query.message.reply_text(
                    msg,
                    reply_markup=back_to_main_keyboard()
                )
        else:
            await update.message.reply_text(
                msg,
                reply_markup=back_to_main_keyboard()
            )
        return ConversationHandler.END
    
    # Initialize selected channels list
    if 'selected_channels' not in context.user_data:
        context.user_data['selected_channels'] = []
    
    # Create channel selection keyboard
    keyboard = []
    for channel in channels:
        ch_id = channel['id']
        ch_title = channel.get('title', 'Unknown')
        
        # Check if selected
        is_selected = ch_id in context.user_data['selected_channels']
        emoji = "✅" if is_selected else "⬜"
        
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {ch_title}",
            callback_data=f"toggle_schedule_ch_{ch_id}"
        )])
    
    # Add action buttons
    keyboard.append([InlineKeyboardButton("✅ Confirm Selection", callback_data="confirm_schedule_channels")])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_schedule")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    selected_count = len(context.user_data['selected_channels'])
    msg = f"📢 Select Channels for Posting\n\nSelected: {selected_count}/{len(channels)}\n\nTap to select/deselect:"
    
    if hasattr(update, 'callback_query') and update.callback_query:
        if not update.callback_query.message:
            await update.callback_query.answer("⚠️ Cannot display here", show_alert=True)
            return ConversationHandler.END
        
        try:
            await update.callback_query.edit_message_text(
                msg,
                reply_markup=reply_markup
            )
        except:
            await update.callback_query.message.reply_text(
                msg,
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup
        )
    
    return SELECT_CHANNELS


async def toggle_schedule_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle channel selection"""
    query = update.callback_query
    await query.answer()
    
    # Extract channel ID
    channel_id = int(query.data.replace('toggle_schedule_ch_', ''))
    
    # Toggle selection
    if 'selected_channels' not in context.user_data:
        context.user_data['selected_channels'] = []
    
    if channel_id in context.user_data['selected_channels']:
        context.user_data['selected_channels'].remove(channel_id)
    else:
        context.user_data['selected_channels'].append(channel_id)
    
    # Refresh UI
    return await show_channel_selection(update, context)


async def confirm_schedule_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm channel selection and save schedule"""
    query = update.callback_query
    
    selected_channels = context.user_data.get('selected_channels', [])
    
    if not selected_channels:
        await query.answer("⚠️ Please select at least one channel!", show_alert=True)
        return SELECT_CHANNELS
    
    await query.answer()
    
    scheduled_time = context.user_data.get('scheduled_time')
    
    if not scheduled_time:
        if not query.message:
            await query.answer("❌ Error: Time not set", show_alert=True)
            return ConversationHandler.END
        
        await query.edit_message_text(
            "❌ Error: Time not set. Please try again.",
            reply_markup=back_to_main_keyboard()
        )
        return ConversationHandler.END
    
    # Save scheduled post
    await save_scheduled_post_with_channels(update, context, scheduled_time, selected_channels)
    
    return ConversationHandler.END


async def save_scheduled_post_with_channels(update, context, scheduled_time, channel_ids):
    """Save scheduled post with selected channels"""
    post_data = context.user_data.get('post_data', {})
    post_type = context.user_data.get('post_type')
    generated_text = context.user_data.get('generated_text')
    user_id = update.effective_user.id
    
    # Prepare schedule data
    schedule_data = {
        'user_id': user_id,
        'post_type': post_type,
        'post_data': post_data,
        'generated_text': generated_text,
        'scheduled_time': scheduled_time,
        'channel_ids': channel_ids,
        'status': 'pending'
    }
    
    # Save to database
    result = db.save_scheduled_post(schedule_data)
    
    time_str = format_datetime(scheduled_time)
    ch_count = len(channel_ids)
    
    success_msg = f"""✅ Post Scheduled Successfully!

📅 Time: {time_str}
📝 Type: {post_type}
📢 Channels: {ch_count}

Will post automatically."""
    
    if hasattr(update, 'callback_query') and update.callback_query:
        if not update.callback_query.message:
            await update.callback_query.answer(success_msg, show_alert=True)
        else:
            try:
                await update.callback_query.edit_message_text(
                    success_msg,
                    reply_markup=back_to_main_keyboard()
                )
            except:
                await update.callback_query.message.reply_text(
                    success_msg,
                    reply_markup=back_to_main_keyboard()
                )
    else:
        await update.message.reply_text(
            success_msg,
            reply_markup=back_to_main_keyboard()
        )
    
    # Clear user data
    context.user_data.clear()


async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel scheduling"""
    query = update.callback_query
    await query.answer("Scheduling cancelled")
    
    if not query.message:
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text(
        "❌ Scheduling cancelled.",
        reply_markup=back_to_main_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def conversation_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout"""
    logger.warning("Schedule conversation timed out")
    
    if update.effective_message:
        await update.effective_message.reply_text(
            "⏱️ Session expired. Please start again.",
            reply_markup=back_to_main_keyboard()
        )
    
    context.user_data.clear()
    return ConversationHandler.END


def register_schedule_handlers(application):
    """Register schedule handlers"""
    # Main schedule callbacks (outside conversation)
    application.add_handler(CallbackQueryHandler(schedule_new_callback, pattern="^schedule_new$"))
    application.add_handler(CallbackQueryHandler(schedule_this_callback, pattern="^schedule_this$"))
    
    # Quick schedule options (outside conversation)
    application.add_handler(CallbackQueryHandler(schedule_next_hour, pattern="^schedule_next_hour$"))
    application.add_handler(CallbackQueryHandler(schedule_2_hours, pattern="^schedule_2_hours$"))
    application.add_handler(CallbackQueryHandler(schedule_6_hours, pattern="^schedule_6_hours$"))
    
    # Custom time conversation with LONGER timeout
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(schedule_custom_callback, pattern="^schedule_custom$"),
        ],
        states={
            AWAIT_CUSTOM_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_time)
            ],
            SELECT_CHANNELS: [
                CallbackQueryHandler(toggle_schedule_channel, pattern="^toggle_schedule_ch_"),
                CallbackQueryHandler(confirm_schedule_channels, pattern="^confirm_schedule_channels$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_schedule, pattern="^cancel_schedule$"),
        ],
        conversation_timeout=600,
        name="schedule_conversation"
    )
    
    application.add_handler(conv_handler)
    
    # Channel selection handlers (outside conversation for non-custom schedules)
    application.add_handler(CallbackQueryHandler(toggle_schedule_channel, pattern="^toggle_schedule_ch_"))
    application.add_handler(CallbackQueryHandler(confirm_schedule_channels, pattern="^confirm_schedule_channels$"))
    
    logger.info("Schedule handlers registered with extended timeout")
