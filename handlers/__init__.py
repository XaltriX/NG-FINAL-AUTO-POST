from .start import register_start_handlers
from .create_post import register_create_post_handlers
from .schedule import register_schedule_handlers
from .dashboard import register_dashboard_handlers
from .settings import register_settings_handlers
from .auto_acceptor import register_auto_acceptor_handlers  # Add this import

def register_all_handlers(application):
    """Register all bot handlers"""
    register_start_handlers(application)
    register_create_post_handlers(application)
    register_schedule_handlers(application)
    register_dashboard_handlers(application)
    register_settings_handlers(application)
    register_auto_acceptor_handlers(application)  # Add this line

__all__ = ['register_all_handlers']
