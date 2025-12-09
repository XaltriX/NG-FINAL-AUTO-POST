import re
from datetime import datetime

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
    """Parse datetime string to datetime object"""
    try:
        return datetime.strptime(date_string, '%d/%m/%Y %H:%M')
    except ValueError:
        return None


def is_future_datetime(dt):
    """Check if datetime is in the future"""
    return dt > datetime.now()