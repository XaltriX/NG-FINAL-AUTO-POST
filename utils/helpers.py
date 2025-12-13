from datetime import datetime, timedelta, timezone
from telegram.error import TelegramError

# IST Timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

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
    """Format datetime for display in IST"""
    if dt.tzinfo is None:
        # If naive datetime, assume it's IST
        dt = dt.replace(tzinfo=IST)
    else:
        # Convert to IST
        dt = dt.astimezone(IST)
    return dt.strftime('%d/%m/%Y %H:%M IST')

def get_next_hour():
    """Get next hour datetime in IST"""
    now = datetime.now(IST)
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour

def get_time_offset(hours):
    """Get datetime with offset in IST"""
    return datetime.now(IST) + timedelta(hours=hours)

def truncate_text(text, max_length=50):
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
