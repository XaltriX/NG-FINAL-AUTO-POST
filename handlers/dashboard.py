from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import db
from utils import back_to_main_keyboard, scheduled_post_actions_keyboard, format_datetime

def escape_md(text):
    """Escape for MarkdownV2"""
    if not text:
        return ""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        text = text.replace(c, f'\\{c}')
    return text

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dashboard with pending and posted content"""
    query = update.callback_query
    await query.answer()
    
    # Get pending posts
    pending_posts = db.get_pending_scheduled_posts()
    
    # Get recent posts
    recent_posts = db.get_recent_posts(limit=10)
    
    # Build dashboard message (plain text to avoid errors)
    dashboard_text = "📊 *DASHBOARD*\n\n"
    
    # Pending Posts Section
    dashboard_text += "*🕒 Pending Scheduled Posts*\n"
    if pending_posts:
        dashboard_text += f"Count: {len(pending_posts)}\n\n"
        for post in pending_posts[:5]:
            title = post.get('post_data', {}).get('title', 'Untitled')[:20]
            scheduled_time = format_datetime(post['scheduled_time'])
            dashboard_text += f"📅 {escape_md(title)}\n"
            dashboard_text += f"   ⏰ {escape_md(scheduled_time)}\n\n"
    else:
        dashboard_text += "No pending posts\\.\n\n"
    
    dashboard_text += "━━━━━━━━━━━━━━━\n\n"
    
    # Recent Posts Section
    dashboard_text += "*📮 Last 10 Posted*\n"
    if recent_posts:
        for post in recent_posts[:5]:
            title = post.get('title', 'Untitled')[:20]
            post_type = post.get('type', '?')
            dashboard_text += f"🔹 {escape_md(title)} \\(Type {post_type}\\)\n"
    else:
        dashboard_text += "No posts yet\\.\n\n"
    
    try:
        await query.edit_message_text(
            dashboard_text,
            reply_markup=back_to_main_keyboard(),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        # Fallback: plain text
        await query.message.reply_text(
            "📊 DASHBOARD\n\nPending: " + str(len(pending_posts)) + "\nPosted: " + str(len(recent_posts)),
            reply_markup=back_to_main_keyboard()
        )


def register_dashboard_handlers(application):
    """Register dashboard handlers"""
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"))
