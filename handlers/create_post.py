from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.error import TimedOut, NetworkError
from templates import template_a, template_b, template_c, template_d
from templates.post_templates import escape_markdown
from utils import (
    post_type_keyboard,
    post_preview_keyboard,
    back_to_main_keyboard,
    main_menu_keyboard,
    post_buttons_with_links,
    channel_selection_keyboard,
    is_valid_url
)
from database import db
import asyncio
import logging

logger = logging.getLogger(__name__)

# Conversation states
SELECT_TYPE, AWAIT_MEDIA, AWAIT_TITLE, AWAIT_PREVIEW, AWAIT_DOWNLOAD, AWAIT_HOW_TO, SELECT_CHANNEL = range(7)


# ========== HELPER: SAFE REPLY ==========

async def safe_reply(message, text, **kwargs):
    """Send reply with retry logic for timeouts"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Force disable_web_page_preview if not specified
            if 'disable_web_page_preview' not in kwargs:
                kwargs['disable_web_page_preview'] = True
            return await message.reply_text(text, **kwargs)
        except (TimedOut, NetworkError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to send message after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            await asyncio.sleep(2)  # Wait 2 seconds before retry


# ========== STEP 1: SELECT POST TYPE ==========

async def create_new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show post type selection"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 **Select Post Type:**\n\nChoose the type of post you want to create:",
        reply_markup=post_type_keyboard(),
        parse_mode='Markdown'
    )
    return SELECT_TYPE


# ========== TYPE A: MEDIA POST ==========

async def type_a_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Type A post creation"""
    query = update.callback_query
    await query.answer()

    context.user_data['post_type'] = 'A'
    context.user_data['post_data'] = {}

    await query.edit_message_text(
        "🖼️ **Type A - Media Post**\n\nPlease send the **thumbnail** (Photo/Video/GIF):",
        parse_mode='Markdown'
    )
    return AWAIT_MEDIA


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive media for Type A"""
    message = update.message

    # Check what type of media was sent
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        media_type = 'video'
    elif message.animation:
        file_id = message.animation.file_id
        media_type = 'animation'
    else:
        await safe_reply(
            message,
            "❌ Please send a valid Photo, Video, or GIF.",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_MEDIA

    context.user_data['post_data']['media_file_id'] = file_id
    context.user_data['post_data']['media_type'] = media_type

    await safe_reply(
        message,
        "✅ Media received!\n\nNow send the **Title** (optional):\nType 'skip' to skip this field.",
        parse_mode='Markdown'
    )
    return AWAIT_TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive title (optional)"""
    if not update.message or not update.message.text:
        await safe_reply(update.message or update.effective_message, "❌ Please send text for the title.")
        return AWAIT_TITLE

    title = update.message.text.strip()

    if title.lower() != 'skip':
        context.user_data['post_data']['title'] = title

    await safe_reply(
        update.message,
        "📎 Now send the **Preview Link**:",
        parse_mode='Markdown'
    )
    return AWAIT_PREVIEW


async def receive_preview_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive preview link"""
    if not update.message or not update.message.text:
        await safe_reply(update.message or update.effective_message, "❌ Please send a valid URL.")
        return AWAIT_PREVIEW

    link = update.message.text.strip()

    if not is_valid_url(link):
        await safe_reply(
            update.message,
            "❌ Invalid URL! Please send a valid link starting with http:// or https://",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_PREVIEW

    context.user_data['post_data']['preview_link'] = link

    await safe_reply(
        update.message,
        "⬇️ Now send the **Download Link**:",
        parse_mode='Markdown'
    )
    return AWAIT_DOWNLOAD


async def receive_download_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive download link"""
    if not update.message or not update.message.text:
        await safe_reply(update.message or update.effective_message, "❌ Please send a valid URL.")
        return AWAIT_DOWNLOAD

    link = update.message.text.strip()

    if not is_valid_url(link):
        await safe_reply(
            update.message,
            "❌ Invalid URL! Please send a valid link.",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_DOWNLOAD

    context.user_data['post_data']['download_link'] = link

    # If Type C (no how-to needed)
    if context.user_data.get('post_type') == 'C':
        return await show_post_preview(update, context)

    await safe_reply(
        update.message,
        "⚙️ Finally, send the **How-To-Open Link**:",
        parse_mode='Markdown'
    )
    return AWAIT_HOW_TO


async def receive_how_to_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive how-to link"""
    if not update.message or not update.message.text:
        await safe_reply(update.message or update.effective_message, "❌ Please send a valid URL.")
        return AWAIT_HOW_TO

    link = update.message.text.strip()

    if not is_valid_url(link):
        await safe_reply(
            update.message,
            "❌ Invalid URL! Please send a valid link.",
            reply_markup=back_to_main_keyboard()
        )
        return AWAIT_HOW_TO

    context.user_data['post_data']['how_to_link'] = link

    return await show_post_preview(update, context)


# ========== TYPE B: SIMPLE 3-LINK ==========

async def type_b_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Type B post creation"""
    query = update.callback_query
    await query.answer()

    context.user_data['post_type'] = 'B'
    context.user_data['post_data'] = {}

    await query.edit_message_text(
        "🔗 **Type B - Simple 3-Link Post**\n\nSend the **Title** (optional):\nType 'skip' to skip.",
        parse_mode='Markdown'
    )
    return AWAIT_TITLE


# ========== TYPE C: BASIC 2-LINK ==========

async def type_c_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Type C post creation"""
    query = update.callback_query
    await query.answer()

    context.user_data['post_type'] = 'C'
    context.user_data['post_data'] = {}

    await query.edit_message_text(
        "📥 **Type C - Basic 2-Link Post**\n\nSend the **Title** (optional):\nType 'skip' to skip.",
        parse_mode='Markdown'
    )
    return AWAIT_TITLE


# ========== TYPE D: TITLE + 3-LINK ==========

async def type_d_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Type D post creation"""
    query = update.callback_query
    await query.answer()

    context.user_data['post_type'] = 'D'
    context.user_data['post_data'] = {}

    await query.edit_message_text(
        "📝 **Type D - Title + 3-Link Post**\n\nSend the **Title** (required):",
        parse_mode='Markdown'
    )
    return AWAIT_TITLE


# ========== SHOW PREVIEW ==========

async def show_post_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and show post preview"""
    post_type = context.user_data.get('post_type')
    post_data = context.user_data.get('post_data', {})

    if not post_type or not post_data:
        message = update.message or (update.callback_query.message if update.callback_query else None)
        if message:
            await safe_reply(message, "❌ Post data missing. Please create a post again.", reply_markup=back_to_main_keyboard())
        return ConversationHandler.END

    # Generate text based on type
    try:
        if post_type == 'A':
            text = template_a(
                post_data.get('title', ''),
                post_data['preview_link'],
                post_data['download_link'],
                post_data['how_to_link']
            )
        elif post_type == 'B':
            text = template_b(
                post_data.get('title', ''),
                post_data.get('preview_link'),
                post_data.get('download_link'),
                post_data.get('how_to_link')
            )
        elif post_type == 'C':
            text = template_c(
                post_data.get('title', ''),
                post_data.get('preview_link', ''),
                post_data.get('download_link', '')
            )
        elif post_type == 'D':
            text = template_d(
                post_data.get('title', ''),
                post_data.get('preview_link', ''),
                post_data.get('download_link', ''),
                post_data.get('how_to_link', '')
            )
        else:
            text = ""
    except KeyError as e:
        logger.error(f"Missing data for template: {e}")
        message = update.message or (update.callback_query.message if update.callback_query else None)
        if message:
            await safe_reply(message, "❌ Some required fields are missing. Please create the post again.", reply_markup=back_to_main_keyboard())
        return ConversationHandler.END

    context.user_data['generated_text'] = text

    # Create buttons with actual URLs
    how_to = post_data.get('how_to_link')
    buttons = post_buttons_with_links(
        post_data.get('preview_link'),
        post_data.get('download_link'),
        how_to
    )

    message_obj = update.message or (update.callback_query.message if update.callback_query else None)

    # Send preview - TRY ONLY ONCE, NO FALLBACK
    try:
        if post_type == 'A' and 'media_file_id' in post_data:
            media_type = post_data['media_type']
            file_id = post_data['media_file_id']

            if media_type == 'photo':
                await message_obj.reply_photo(
                    photo=file_id,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
            elif media_type == 'video':
                await message_obj.reply_video(
                    video=file_id,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
            elif media_type == 'animation':
                await message_obj.reply_animation(
                    animation=file_id,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
        else:
            await safe_reply(
                message_obj,
                text,
                reply_markup=buttons,
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )

        await safe_reply(
            message_obj,
            "✅ *Post Created Successfully\\!*\n\nChoose an action:",
            reply_markup=post_preview_keyboard(),
            parse_mode='MarkdownV2'
        )

    except Exception as e:
        logger.error(f"Error sending preview: {e}")
        await safe_reply(
            message_obj,
            f"❌ Preview failed\\! Error: {escape_markdown(str(e))}\n\nYou can still try to post it\\.",
            reply_markup=post_preview_keyboard()
        )

    return ConversationHandler.END


# ========== PREVIEW POST ==========

async def preview_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show post preview again"""
    query = update.callback_query
    await query.answer("Preview displayed above ⬆️")


# ========== EDIT POST ==========

async def edit_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit current post"""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "✏️ *Edit Post*\n\n⚠️ Edit feature coming soon\\!\n\nFor now, please create a new post\\.",
        reply_markup=back_to_main_keyboard(),
        parse_mode='MarkdownV2'
    )


async def post_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle post now action - show channel selection"""
    query = update.callback_query
    await query.answer()

    if 'generated_text' not in context.user_data:
        await query.message.reply_text(
            "❌ No post found! Please create a post first.",
            reply_markup=back_to_main_keyboard()
        )
        return

    try:
        user_id = update.effective_user.id
        channels = await get_user_channels(context, user_id)

        if not channels:
            await query.message.reply_text(
                "⚠️ *No channels found\\!*\n\nPlease add channels first:\n1\\. Make bot admin in your channel\n2\\. Use /addchannel command\n3\\. Or send channel invite link/ID",
                reply_markup=back_to_main_keyboard(),
                parse_mode='MarkdownV2'
            )
            return

        keyboard = channel_selection_keyboard(channels)
        await query.message.reply_text(
            "📢 *Select Channel to Post:*",
            reply_markup=keyboard,
            parse_mode='MarkdownV2'
        )

    except Exception as e:
        logger.error(f"Error in post_now: {e}")
        await query.message.reply_text(
            "❌ Error loading channels. Please try again.",
            reply_markup=back_to_main_keyboard()
        )


async def get_user_channels(context, user_id):
    """Get list of channels where bot is admin"""
    user_settings = db.get_user_settings(user_id) or {}
    channels = user_settings.get('channels', [])

    verified_channels = []
    for channel in channels:
        try:
            chat_id = channel.get('id')
            chat = await context.bot.get_chat(chat_id)
            bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if bot_member.status in ['administrator', 'creator']:
                verified_channels.append({
                    'id': channel['id'],
                    'title': chat.title or channel.get('title')
                })
        except Exception as e:
            logger.warning(f"Channel {channel.get('id')} not accessible: {e}")
            continue

    return verified_channels


async def select_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel selection and post - FIXED: NO DOUBLE POSTING"""
    query = update.callback_query
    await query.answer()

    # Extract channel ID from callback data
    data = query.data or ''
    channel_id = data.replace('select_channel_', '')

    # Get post data
    post_type = context.user_data.get('post_type')
    post_data = context.user_data.get('post_data', {})
    generated_text = context.user_data.get('generated_text')

    if not generated_text:
        await query.message.reply_text(
            "❌ Post data not found! Please create a post again.",
            reply_markup=back_to_main_keyboard()
        )
        return

    # Create buttons with URLs
    how_to = post_data.get('how_to_link')
    buttons = post_buttons_with_links(
        post_data.get('preview_link'),
        post_data.get('download_link'),
        how_to
    )

    sent_message = None

    try:
        # ========== TRY ONLY ONCE - NO FALLBACK ==========
        if post_type == 'A' and 'media_file_id' in post_data:
            media_type = post_data['media_type']
            file_id = post_data['media_file_id']

            if media_type == 'photo':
                sent_message = await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=file_id,
                    caption=generated_text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
            elif media_type == 'video':
                sent_message = await context.bot.send_video(
                    chat_id=channel_id,
                    video=file_id,
                    caption=generated_text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
            elif media_type == 'animation':
                sent_message = await context.bot.send_animation(
                    chat_id=channel_id,
                    animation=file_id,
                    caption=generated_text,
                    reply_markup=buttons,
                    parse_mode='MarkdownV2'
                )
        else:
            sent_message = await context.bot.send_message(
                chat_id=channel_id,
                text=generated_text,
                reply_markup=buttons,
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )

        # Save to database ONLY if message sent successfully
        if sent_message:
            save_data = {
                'type': post_type,
                'title': post_data.get('title', ''),
                'preview_link': post_data.get('preview_link'),
                'download_link': post_data.get('download_link'),
                'how_to_link': post_data.get('how_to_link'),
                'message_id': sent_message.message_id,
                'chat_id': channel_id,
                'views': 0
            }

            if post_type == 'A':
                save_data['media_file_id'] = post_data.get('media_file_id')
                save_data['media_type'] = post_data.get('media_type')

            db.save_post(save_data)

            # Success message
            await query.message.reply_text(
                "✅ *Post Published Successfully\\!*\n\n"
                f"Posted to channel: {escape_markdown(str(channel_id))}",
                reply_markup=back_to_main_keyboard(),
                parse_mode='MarkdownV2'
            )

            # Clear user data
            context.user_data.clear()

    except Exception as e:
        logger.error(f"Error posting to channel: {e}")
        # NO FALLBACK - Just show error message
        await query.message.reply_text(
            f"❌ *Error posting to channel\\!*\n\n"
            f"Error: {escape_markdown(str(e))}\n\n"
            f"*Possible reasons:*\n"
            f"• Bot is not admin in channel\n"
            f"• Invalid formatting in template\n"
            f"• Network issue\n\n"
            f"Please check and try again\\.",
            reply_markup=back_to_main_keyboard(),
            parse_mode='MarkdownV2'
        )


# ========== CANCEL ==========

async def cancel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel post creation"""
    context.user_data.clear()

    if getattr(update, 'callback_query', None):
        query = update.callback_query
        await query.answer("❌ Cancelled")

        try:
            pending_count = db.get_pending_count()
        except Exception:
            pending_count = 0

        try:
            await query.edit_message_text(
                "❌ *Post creation cancelled\\.*\n\nReturning to main menu\\.\\.\\.",
                reply_markup=main_menu_keyboard(pending_count),
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logger.error(f"Error editing message on cancel: {e}")
            await query.message.reply_text(
                "❌ *Post creation cancelled\\.*",
                reply_markup=main_menu_keyboard(pending_count),
                parse_mode='MarkdownV2'
            )
    else:
        message = update.message or update.effective_message
        await message.reply_text(
            "❌ *Post creation cancelled\\.*",
            reply_markup=back_to_main_keyboard(),
            parse_mode='MarkdownV2'
        )

    return ConversationHandler.END


def register_create_post_handlers(application):
    """Register create post conversation handler"""
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(create_new_post, pattern="^create_new$"),
        ],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(type_a_start, pattern="^type_a$"),
                CallbackQueryHandler(type_b_start, pattern="^type_b$"),
                CallbackQueryHandler(type_c_start, pattern="^type_c$"),
                CallbackQueryHandler(type_d_start, pattern="^type_d$"),
            ],
            AWAIT_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.IMAGE | filters.ANIMATION, receive_media)
            ],
            AWAIT_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)
            ],
            AWAIT_PREVIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_preview_link)
            ],
            AWAIT_DOWNLOAD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_download_link)
            ],
            AWAIT_HOW_TO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_how_to_link)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_post, pattern="^cancel_post$"),
            CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main$"),
        ],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(preview_post_callback, pattern="^preview_post$"))
    application.add_handler(CallbackQueryHandler(edit_post_callback, pattern="^edit_post$"))
    application.add_handler(CallbackQueryHandler(post_now_callback, pattern="^post_now$"))
    application.add_handler(CallbackQueryHandler(select_channel_callback, pattern="^select_channel_"))


# Import for back_to_main_callback
try:
    from start import back_to_main_callback
except Exception:
    def back_to_main_callback(update, context):
        """Fallback dummy if real import fails. Replace with your actual implementation."""
        return None