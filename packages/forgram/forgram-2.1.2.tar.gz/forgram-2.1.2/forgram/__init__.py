"""
Forgram - современная библиотека для Telegram ботов
Быстрая, простая и мощная альтернатива aiogram
"""

__version__ = "2.1.1"
__author__ = "Forgram Team"

from .bot import Bot
from .models import Message, User, Chat, Update, CallbackQuery, InlineQuery
from .exceptions import ForgramError, APIError, NetworkError

from .filters import *
from .middleware import MiddlewareManager, RateLimitMiddleware, AntiSpamMiddleware, AuthMiddleware, PerformanceMiddleware
from .storage import MemoryStorage, FileStorage, SQLiteStorage, RedisStorage
from .http_client import HTTPClient
from . import advanced_types
from .webhook import WebhookHandler, FlaskWebhookHandler, FastAPIWebhookHandler, AioHttpWebhookHandler
from .admin import BotAdmin, AdminPanel
from .analytics import AnalyticsCollector, analytics_middleware
from . import utils

__all__ = [
    "Bot",
    "Message", 
    "User",
    "Chat",
    "Update",
    "CallbackQuery",
    "InlineQuery",
    "ForgramError",
    "APIError",
    "NetworkError",
    "MiddlewareManager",
    "RateLimitMiddleware",
    "AntiSpamMiddleware",
    "AuthMiddleware", 
    "PerformanceMiddleware",
    "MemoryStorage",
    "FileStorage",
    "SQLiteStorage",
    "RedisStorage", 
    "HTTPClient",
    "WebhookHandler",
    "FlaskWebhookHandler",
    "FastAPIWebhookHandler", 
    "AioHttpWebhookHandler",
    "BotAdmin",
    "AdminPanel",
    "AnalyticsCollector",
    "analytics_middleware",
    "utils"
]
