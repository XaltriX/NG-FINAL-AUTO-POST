from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def main_menu_keyboard(pending_count=0):
    """Main menu keyboard with pending count"""
    keyboard = [
        [InlineKeyboardButton("➕ Create New Post", callback_data="create_new")],
        [InlineKeyboardButton("📅 Schedule Post", callback_data="schedule_new")],
        [InlineKeyboardButton(f"📊 Dashboard ({pending_count} Pending)", callback_data="dashboard")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


def post_type_keyboard():
    """Select post type keyboard"""
    keyboard = [
        [InlineKeyboardButton("🖼️ Type A — Media Post (All Links)", callback_data="type_a")],
        [InlineKeyboardButton("🔗 Type B — Simple 3-Link Post", callback_data="type_b")],
        [InlineKeyboardButton("📥 Type C — Basic 2-Link Post", callback_data="type_c")],
        [InlineKeyboardButton("📝 Type D — Title + 3-Link Post", callback_data="type_d")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def post_preview_keyboard():
    """Post preview action keyboard"""
    keyboard = [
        [InlineKeyboardButton("👁️ Preview Post", callback_data="preview_post")],
        [InlineKeyboardButton("📤 Post Now", callback_data="post_now")],
        [InlineKeyboardButton("📅 Schedule This Post", callback_data="schedule_this")],
        [InlineKeyboardButton("✏️ Edit Post", callback_data="edit_post")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")]
    ]
    return InlineKeyboardMarkup(keyboard)


def more_channels_keyboard():
    """More channels button for posts"""
    keyboard = [
        [InlineKeyboardButton("➡️ More Channels", url=config.MORE_CHANNELS_LINK)]
    ]
    return InlineKeyboardMarkup(keyboard)


def post_buttons_with_links(preview_url, download_url, how_to_url=None):
    """Inline buttons with actual URLs for posts"""
    keyboard = [
        [InlineKeyboardButton("👁️ 𝗣𝗿𝗲𝘃𝗶𝗲𝘄", url=preview_url)],
        [InlineKeyboardButton("📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱", url=download_url)]
    ]
    
    if how_to_url:
        keyboard.append([InlineKeyboardButton("🔗 𝗛𝗼𝘄 𝘁𝗼 𝗢𝗽𝗲𝗻", url=how_to_url)])
    
    keyboard.append([InlineKeyboardButton("➡️ More Channels", url=config.MORE_CHANNELS_LINK)])
    
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard():
    """Simple back button"""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def channel_selection_keyboard(channels):
    """Dynamic channel selection keyboard"""
    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(
            f"📢 {channel['title']}", 
            callback_data=f"select_channel_{channel['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_post")])
    return InlineKeyboardMarkup(keyboard)


def schedule_time_keyboard():
    """Quick schedule time options"""
    keyboard = [
        [InlineKeyboardButton("⏰ Next Hour", callback_data="schedule_next_hour")],
        [InlineKeyboardButton("⏰ +2 Hours", callback_data="schedule_2_hours")],
        [InlineKeyboardButton("⏰ +6 Hours", callback_data="schedule_6_hours")],
        [InlineKeyboardButton("📅 Custom Date/Time", callback_data="schedule_custom")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_schedule")]
    ]
    return InlineKeyboardMarkup(keyboard)


def scheduled_post_actions_keyboard(schedule_id):
    """Actions for scheduled posts"""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit", callback_data=f"edit_schedule_{schedule_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_schedule_{schedule_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(auto_acceptor_enabled):
    """Settings menu keyboard"""
    status = "✅ ON" if auto_acceptor_enabled else "❌ OFF"
    keyboard = [
        [InlineKeyboardButton(f"🤖 Auto Request Acceptor: {status}", callback_data="toggle_auto_acceptor")],
        [InlineKeyboardButton("📢 Manage Channels", callback_data="manage_channels")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)