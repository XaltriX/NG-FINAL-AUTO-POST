import config

def escape_markdown(text):
    """Escape special characters for MarkdownV2"""
    if not text:
        return ""
    # Escape these characters for MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def escape_url(url):
    """Escape URL for MarkdownV2 - only escape closing parenthesis"""
    if not url:
        return ""
    # Only escape ) in URLs
    return url.replace(')', '\\)')

def template_a(title, preview, download, how_to):
    """Type A - Media Post (Thumbnail + All Links) - Clickable links + Buttons"""
    title_text = f"*📌 𝗧𝗶𝘁𝗹𝗲:* {escape_markdown(title)}" if title else "*📌 𝗡𝗼 𝗧𝗶𝘁𝗹𝗲*"
    
    return f"""*🎥 𝗡𝗘𝗪 𝗩𝗜𝗗𝗘𝗢 𝗔𝗟𝗘𝗥𝗧*
━━━━━━━━━━━━━━━━━━
{title_text}

👁️ [𝗣𝗿𝗲𝘃𝗶𝗲𝘄]({escape_url(preview)})
📥 [𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱]({escape_url(download)})
🔗 [𝗛𝗼𝘄 𝘁𝗼 𝗢𝗽𝗲𝗻]({escape_url(how_to)})

*𝗪𝗔𝗧𝗖𝗛 𝗡𝗢𝗪\\!* 🎬
⚡ *𝗕𝘆* @NeonGhost\\_Network"""

def template_b(title, preview, download, how_to):
    """Type B - Simple 3-Link Post - Clickable links + Buttons"""
    title_text = f"*📌 𝗧𝗶𝘁𝗹𝗲:* {escape_markdown(title)}" if title else "*📌 𝗡𝗼 𝗧𝗶𝘁𝗹𝗲*"
    
    return f"""*🎥 𝗡𝗘𝗪 𝗩𝗜𝗗𝗘𝗢 𝗔𝗟𝗘𝗥𝗧*
━━━━━━━━━━━━━━━━━━
{title_text}

👁️ [𝗣𝗿𝗲𝘃𝗶𝗲𝘄]({escape_url(preview)})
📥 [𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱]({escape_url(download)})
🔗 [𝗛𝗼𝘄 𝘁𝗼 𝗢𝗽𝗲𝗻]({escape_url(how_to)})

*𝗪𝗔𝗧𝗖𝗛 𝗡𝗢𝗪\\!* 🎬
⚡ *𝗕𝘆* @NeonGhost\\_Network"""

def template_c(title, preview, download):
    """Type C - Basic 2-Link Post - Clickable links + Buttons"""
    title_text = f"*📌 𝗧𝗶𝘁𝗹𝗲:* {escape_markdown(title)}" if title else "*📌 𝗡𝗼 𝗧𝗶𝘁𝗹𝗲*"
    
    return f"""*🎥 𝗡𝗘𝗪 𝗩𝗜𝗗𝗘𝗢 𝗔𝗟𝗘𝗥𝗧*
━━━━━━━━━━━━━━━━━━
{title_text}

👁️ [𝗣𝗿𝗲𝘃𝗶𝗲𝘄]({escape_url(preview)})
📥 [𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱]({escape_url(download)})

*𝗪𝗔𝗧𝗖𝗛 𝗡𝗢𝗪\\!* 🎬
⚡ *𝗕𝘆* @NeonGhost\\_Network"""

def template_d(title, preview, download, how_to):
    """Type D - Title + 3-Link Post - Clickable links + Buttons"""
    return f"""*🎥 𝗡𝗘𝗪 𝗩𝗜𝗗𝗘𝗢 𝗔𝗟𝗘𝗥𝗧*
━━━━━━━━━━━━━━━━━━
*📌 𝗧𝗶𝘁𝗹𝗲:* {escape_markdown(title)}

👁️ [𝗣𝗿𝗲𝘃𝗶𝗲𝘄]({escape_url(preview)})
📥 [𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱]({escape_url(download)})
🔗 [𝗛𝗼𝘄 𝘁𝗼 𝗢𝗽𝗲𝗻]({escape_url(how_to)})

*𝗪𝗔𝗧𝗖𝗛 𝗡𝗢𝗪\\!* 🎬
⚡ *𝗕𝘆* @NeonGhost\\_Network"""