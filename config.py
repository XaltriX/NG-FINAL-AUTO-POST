import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7008031473:AAEqhmmWZnMGNTgFXGC14degVtTKlPzPysw')

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://villainravangaming:mikey_kun_781_@cluster0.fbgs1zz.mongodb.net/?retryWrites=true&w=majority')
DATABASE_NAME = 'telegram_post_bot'

# Collections
POSTS_COLLECTION = 'posts'
SCHEDULED_POSTS_COLLECTION = 'scheduled_posts'
SETTINGS_COLLECTION = 'settings'

# Default Channel (for "More Channels" button)
MORE_CHANNELS_LINK = 'https://t.me/Linkz_Wallah/2'

# Admin User ID (optional - for admin features)

ADMIN_USER_ID = 5706788169  # Set your Telegram user ID here
OWNER_ID = 5706788169



