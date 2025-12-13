import re
from datetime import datetime, timezone, timedelta

# IST Timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def is_valid_url(url):
    """Validate if string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def validate_datetime_format(date_string):
    """Validate datetime string in format: DD/MM/YYYY HH:MM"""
    try:
        datetime.strptime(date_string, '%d/%m/%Y %H:%M')
        return True
    except ValueError:
        return False

def parse_datetime(date_string):
    """Parse datetime string to datetime object in IST timezone"""
    try:
        # Parse the naive datetime
        dt = datetime.strptime(date_string, '%d/%m/%Y %H:%M')
        # Add IST timezone (treat input as IST time)
        dt_ist = dt.replace(tzinfo=IST)
        return dt_ist
    except ValueError:
        return None

def is_future_datetime(dt):
    """Check if datetime is in the future (IST comparison)"""
    # Get current time in IST
    now_ist = datetime.now(IST)
    
    # If dt is naive, assume it's IST
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    else:
        # Convert to IST for comparison
        dt = dt.astimezone(IST)
    
    return dt > now_ist
