from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import db
from utils import back_to_main_keyboard, format_datetime

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
    
    # IMPORTANT: Check if message exists
    if not query.message:
        await query.answer("⚠️ Cannot display dashboard here", show_alert=True)
        return
    
    await query.answer()
    
    # Get pending posts
    pending_posts = db.get_pending_scheduled_posts()
    
    # Get recent posts
    recent_posts = db.get_recent_posts(limit=10)
    
    # Build dashboard message (plain text to avoid errors)
    dashboard_text = "📊 DASHBOARD\n\n"
    
    # Pending Posts Section
    dashboard_text += "🕒 Pending Scheduled Posts\n"
    if pending_posts:
        dashboard_text += f"Count: {len(pending_posts)}\n\n"
        for post in pending_posts[:5]:
            title = post.get('post_data', {}).get('title', 'Untitled')[:20]
            scheduled_time = format_datetime(post['scheduled_time'])
            post_id = str(post['_id'])
            dashboard_text += f"📅 {title}\n"
            dashboard_text += f"   ⏰ {scheduled_time}\n"
            dashboard_text += f"   [Delete: /del_{post_id}]\n\n"
    else:
        dashboard_text += "No pending posts.\n\n"
    
    dashboard_text += "━━━━━━━━━━━━━━━\n\n"
    
    # Recent Posts Section
    dashboard_text += "📮 Last 10 Posted\n"
    if recent_posts:
        for post in recent_posts[:5]:
            title = post.get('title', 'Untitled')[:20]
            post_type = post.get('type', '?')
            dashboard_text += f"🔹 {title} (Type {post_type})\n"
    else:
        dashboard_text += "No posts yet.\n\n"
    
    # Add delete buttons for pending posts
    keyboard = []
    for post in pending_posts[:5]:
        title = post.get('post_data', {}).get('title', 'Untitled')[:20]
        post_id = str(post['_id'])
        keyboard.append([InlineKeyboardButton(
            f"🗑️ Delete: {title}",
            callback_data=f"delete_schedule_{post_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            dashboard_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        # Fallback: send new message if edit fails
        await query.message.reply_text(
            "📊 DASHBOARD\n\nPending: " + str(len(pending_posts)) + "\nPosted: " + str(len(recent_posts)),
            reply_markup=reply_markup
        )

async def delete_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a scheduled post"""
    query = update.callback_query
    
    # IMPORTANT: Check if message exists
    if not query.message:
        await query.answer("⚠️ Cannot delete from here", show_alert=True)
        return
    
    await query.answer()
    
    # Extract schedule ID
    schedule_id = query.data.replace('delete_schedule_', '')
    
    try:
        from bson.objectid import ObjectId
        db.delete_scheduled_post(ObjectId(schedule_id))
        await query.answer("✅ Deleted!", show_alert=True)
    except Exception as e:
        await query.answer("❌ Error deleting!", show_alert=True)
    
    # Refresh dashboard
    await dashboard_callback(update, context)

def register_dashboard_handlers(application):
    """Register dashboard handlers"""
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"))
    application.add_handler(CallbackQueryHandler(delete_schedule_callback, pattern="^delete_schedule_"))
