from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database import db
from utils import settings_keyboard, back_to_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
AWAIT_CHANNEL_INPUT = range(1)

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_settings = db.get_user_settings(user_id)
    
    auto_acceptor_enabled = user_settings.get('auto_acceptor_enabled', False)
    
    settings_text = """
⚙️ *SETTINGS*

Configure your bot preferences:
"""
    
    await query.edit_message_text(
        settings_text,
        reply_markup=settings_keyboard(auto_acceptor_enabled),
        parse_mode='Markdown'
    )


async def toggle_auto_acceptor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto request acceptor"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_settings = db.get_user_settings(user_id)
    
    # Toggle status
    current_status = user_settings.get('auto_acceptor_enabled', False)
    new_status = not current_status
    
    db.update_user_settings(user_id, {'auto_acceptor_enabled': new_status})
    
    status_text = "✅ enabled" if new_status else "❌ disabled"
    await query.answer(f"Auto Request Acceptor {status_text}!")
    
    # Refresh settings page
    await settings_callback(update, context)


async def manage_channels_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage channels for posting"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_settings = db.get_user_settings(user_id)
    channels = user_settings.get('channels', [])
    
    channel_list = ""
    if channels:
        channel_list = "\n\n*Your Channels:*\n"
        for i, channel in enumerate(channels, 1):
            channel_list += f"{i}\\. {channel.get('title', 'Unknown')} \\(`{channel['id']}`\\)\n"
    else:
        channel_list = "\n\n_No channels added yet\\._"
    
    await query.edit_message_text(
        f"""📢 *Channel Management*
{channel_list}

*How to add a channel:*
1\\. Make bot admin in your channel
2\\. Send channel username \\(@channel\\)
3\\. Or send channel ID \\(\\-100xxxxxxxxxx\\)
4\\. Or forward a message from channel

_Send channel info now or tap Back:_""",
        reply_markup=back_to_main_keyboard(),
        parse_mode='MarkdownV2'
    )
    
    return AWAIT_CHANNEL_INPUT


async def receive_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive channel username/ID or forwarded message"""
    user_id = update.effective_user.id
    message = update.message
    
    channel_id = None
    channel_title = None
    
    try:
        # Check if it's a forwarded message from channel
        # Check if it's a forwarded message from a channel
        if message.forward_from_chat:
            forward_chat = message.forward_from_chat
            if forward_chat.type == 'channel':
                channel_id = forward_chat.id
                channel_title = forward_chat.title
                
        # Check if it's a username or ID
        elif message.text:
            text = message.text.strip()
            
            # Username format: @channel
            if text.startswith('@'):
                try:
                    chat = await context.bot.get_chat(text)
                    if chat.type == 'channel':
                        channel_id = chat.id
                        channel_title = chat.title
                except Exception as e:
                    await message.reply_text(
                        f"❌ *Error:* Channel not found or bot is not admin\\.\n\n"
                        f"Make sure:\n"
                        f"1\\. Bot is admin in the channel\n"
                        f"2\\. Channel username is correct",
                        parse_mode='MarkdownV2'
                    )
                    return AWAIT_CHANNEL_INPUT
            
            # Channel ID format: -100xxxxxxxxxx
            elif text.startswith('-100') or text.lstrip('-').isdigit():
                try:
                    chat_id = int(text)
                    chat = await context.bot.get_chat(chat_id)
                    if chat.type == 'channel':
                        channel_id = chat.id
                        channel_title = chat.title
                except Exception as e:
                    await message.reply_text(
                        f"❌ *Error:* Invalid channel ID or bot is not admin\\.",
                        parse_mode='MarkdownV2'
                    )
                    return AWAIT_CHANNEL_INPUT
        
        if not channel_id:
            await message.reply_text(
                "❌ *Invalid input\\!*\n\n"
                "Please send:\n"
                "• Channel username \\(@channel\\)\n"
                "• Channel ID \\(\\-100xxx\\)\n"
                "• Forward a message from channel",
                parse_mode='MarkdownV2'
            )
            return AWAIT_CHANNEL_INPUT
        
        # Verify bot is admin
        bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.reply_text(
                "❌ *Bot is not admin in this channel\\!*\n\n"
                "Please make the bot admin first\\.",
                parse_mode='MarkdownV2'
            )
            return AWAIT_CHANNEL_INPUT
        
        # Add channel to user settings
        user_settings = db.get_user_settings(user_id)
        channels = user_settings.get('channels', [])
        
        # Check if channel already exists
        if any(ch['id'] == channel_id for ch in channels):
            await message.reply_text(
                "ℹ️ *Channel already added\\!*",
                reply_markup=back_to_main_keyboard(),
                parse_mode='MarkdownV2'
            )
            return ConversationHandler.END
        
        # Add new channel
        channels.append({
            'id': channel_id,
            'title': channel_title
        })
        
        db.update_user_settings(user_id, {'channels': channels})
        
        await message.reply_text(
            f"✅ *Channel Added Successfully\\!*\n\n"
            f"*Title:* {channel_title}\n"
            f"*ID:* `{channel_id}`\n\n"
            f"You can now post to this channel\\.",
            reply_markup=back_to_main_keyboard(),
            parse_mode='MarkdownV2'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await message.reply_text(
            "❌ *Error adding channel\\!*\n\n"
            "Please make sure:\n"
            "1\\. Bot is admin in the channel\n"
            "2\\. You sent correct channel info",
            reply_markup=back_to_main_keyboard(),
            parse_mode='MarkdownV2'
        )
        return ConversationHandler.END


def register_settings_handlers(application):
    """Register settings handlers"""
    # Main settings
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(toggle_auto_acceptor, pattern="^toggle_auto_acceptor$"))
    
    # Channel management conversation
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(manage_channels_callback, pattern="^manage_channels$"),
        ],
        states={
            AWAIT_CHANNEL_INPUT: [
                MessageHandler(filters.TEXT | filters.FORWARDED, receive_channel_input)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(settings_callback, pattern="^settings$"),
        ],
    )
    
    application.add_handler(conv_handler)
