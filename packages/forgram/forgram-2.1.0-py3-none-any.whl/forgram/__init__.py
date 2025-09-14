"""
Forgram - Advanced Telegram Bot Framework
Production-ready library that exceeds aiogram in functionality and performance

🚀 Key Features:
- Advanced middleware pipeline with anti-spam protection
- Multiple storage backends (Memory, File, SQLite, Redis)
- Comprehensive webhook support (Flask, FastAPI, aiohttp)
- Built-in analytics and monitoring system
- Administrative web panel for bot management
- Enhanced filtering system with logical operators
- Enterprise-level error handling and logging

Maximum performance. Maximum features. Maximum simplicity.
"""

__version__ = "2.1.0"
__author__ = "Forgram Team"

# Core components
from .bot import Bot
from .types import Message, User, Chat, Update, CallbackQuery, InlineQuery
from .exceptions import ForgramError, APIError, NetworkError

# Advanced features
from .filters import *
from .middleware import MiddlewareManager, RateLimitMiddleware, AntiSpamMiddleware, AuthMiddleware, PerformanceMiddleware
from .storage import MemoryStorage, FileStorage, SQLiteStorage, RedisStorage
from .http_client import HTTPClient
from .advanced_types import *
from .webhook import WebhookHandler, FlaskWebhookHandler, FastAPIWebhookHandler, AioHTTPWebhookHandler
from .admin import BotAdmin, AdminPanel
from .analytics import AnalyticsCollector, analytics_middleware
from . import utils

__all__ = [
    # Core
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
    
    # Advanced features
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
    "AioHTTPWebhookHandler",
    "BotAdmin",
    "AdminPanel",
    "AnalyticsCollector",
    "analytics_middleware",
    "utils"
]
