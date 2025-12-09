from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import db
from utils import back_to_main_keyboard, scheduled_post_actions_keyboard, format_datetime

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dashboard with pending and posted content"""
    query = update.callback_query
    await query.answer()
    
    # Get pending posts
    pending_posts = db.get_pending_scheduled_posts()
    
    # Get recent posts
    recent_posts = db.get_recent_posts(limit=10)
    
    # Build dashboard message
    dashboard_text = "📊 **DASHBOARD**\n\n"
    
    # Pending Posts Section
    dashboard_text += "### 🕒 Pending Scheduled Posts\n"
    if pending_posts:
        dashboard_text += f"**Count:** {len(pending_posts)}\n\n"
        for post in pending_posts[:5]:  # Show first 5
            title = post.get('post_data', {}).get('title', 'Untitled')
            scheduled_time = format_datetime(post['scheduled_time'])
            dashboard_text += f"📅 **{title[:30]}...**\n"
            dashboard_text += f"   ⏰ {scheduled_time}\n"
            dashboard_text += f"   📢 {len(post.get('channel_ids', []))} channel(s)\n\n"
    else:
        dashboard_text += "No pending posts.\n\n"
    
    dashboard_text += "━━━━━━━━━━━━━━━\n\n"
    
    # Recent Posts Section
    dashboard_text += "### 📮 Last 10 Posted\n"
    if recent_posts:
        for post in recent_posts:
            title = post.get('title', 'Untitled')
            post_type = post.get('type', 'Unknown')
            views = post.get('views', 'N/A')
            posted_at = format_datetime(post.get('created_at'))
            
            dashboard_text += f"🔹 **{title[:30]}...** (Type {post_type})\n"
            dashboard_text += f"   👁️ Views: {views}\n"
            dashboard_text += f"   📅 {posted_at}\n\n"
    else:
        dashboard_text += "No posts yet.\n\n"
    
    await query.edit_message_text(
        dashboard_text,
        reply_markup=back_to_main_keyboard(),
        parse_mode='Markdown'
    )


def register_dashboard_handlers(application):
    """Register dashboard handlers"""
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"))