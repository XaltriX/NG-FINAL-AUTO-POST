from datetime import datetime, timedelta
from telegram.error import TelegramError

async def get_channel_list(context, user_id):
    """Get list of channels where bot is admin"""
    channels = []
    # This is a placeholder - you need to implement channel storage
    # For now, returning empty list
    return channels


async def get_post_views(context, chat_id, message_id):
    """Get views count for a post"""
    try:
        # Note: This only works for channels, not groups
        # Returns None if views are not available
        message = await context.bot.get_chat(chat_id)
        return None  # Telegram doesn't provide direct view count via Bot API
    except TelegramError:
        return None


def format_datetime(dt):
    """Format datetime for display"""
    return dt.strftime('%d/%m/%Y %H:%M')


def get_next_hour():
    """Get next hour datetime"""
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour


def get_time_offset(hours):
    """Get datetime with offset"""
    return datetime.now() + timedelta(hours=hours)


def truncate_text(text, max_length=50):
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."