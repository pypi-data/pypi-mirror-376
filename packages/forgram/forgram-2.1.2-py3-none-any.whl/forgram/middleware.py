"""
Forgram Middleware System
Advanced middleware for request/response processing
"""

import asyncio
import time
import logging
from typing import Callable, Any, Dict, List, Optional, Union
from functools import wraps
from .exceptions import MiddlewareError

logger = logging.getLogger(__name__)

class MiddlewareManager:
    """Manages middleware execution pipeline"""
    
    def __init__(self):
        self.middlewares: List[Callable] = []
        self.before_handlers: List[Callable] = []
        self.after_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
    def add_middleware(self, middleware: Callable):
        """Add middleware to pipeline"""
        self.middlewares.append(middleware)
        
    def add_before_handler(self, handler: Callable):
        """Add before-processing handler"""
        self.before_handlers.append(handler)
        
    def add_after_handler(self, handler: Callable):
        """Add after-processing handler"""
        self.after_handlers.append(handler)
        
    def add_error_handler(self, handler: Callable):
        """Add error handler"""
        self.error_handlers.append(handler)
        
    async def process_update(self, update: Dict, bot: Any) -> bool:
        """Process update through middleware pipeline"""
        context = MiddlewareContext(update, bot)
        
        try:
            # Run before handlers
            for handler in self.before_handlers:
                await self._call_handler(handler, context)
                
            # Run middlewares
            for middleware in self.middlewares:
                result = await self._call_middleware(middleware, context)
                if result is False:
                    logger.debug("Middleware stopped processing")
                    return False
                    
            return True
            
        except Exception as e:
            # Run error handlers
            for handler in self.error_handlers:
                try:
                    await self._call_handler(handler, context, error=e)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
                    
            logger.error(f"Middleware error: {e}")
            return False
            
    async def process_response(self, response: Any, context: 'MiddlewareContext'):
        """Process response through after handlers"""
        try:
            for handler in self.after_handlers:
                await self._call_handler(handler, context, response=response)
        except Exception as e:
            logger.error(f"After handler error: {e}")
            
    async def _call_middleware(self, middleware: Callable, context: 'MiddlewareContext'):
        """Call middleware with proper signature detection"""
        if asyncio.iscoroutinefunction(middleware):
            return await middleware(context.update, context.bot, context)
        else:
            return middleware(context.update, context.bot, context)
            
    async def _call_handler(self, handler: Callable, context: 'MiddlewareContext', **kwargs):
        """Call handler with proper signature"""
        if asyncio.iscoroutinefunction(handler):
            await handler(context, **kwargs)
        else:
            handler(context, **kwargs)

class MiddlewareContext:
    """Context object passed through middleware pipeline"""
    
    def __init__(self, update: Dict, bot: Any):
        self.update = update
        self.bot = bot
        self.data: Dict[str, Any] = {}
        self.start_time = time.time()
        self.user_id = self._extract_user_id()
        self.chat_id = self._extract_chat_id()
        self.message_id = self._extract_message_id()
        
    def _extract_user_id(self) -> Optional[int]:
        """Extract user ID from update"""
        if 'message' in self.update:
            return self.update['message'].get('from', {}).get('id')
        elif 'callback_query' in self.update:
            return self.update['callback_query'].get('from', {}).get('id')
        elif 'inline_query' in self.update:
            return self.update['inline_query'].get('from', {}).get('id')
        return None
        
    def _extract_chat_id(self) -> Optional[Union[int, str]]:
        """Extract chat ID from update"""
        if 'message' in self.update:
            return self.update['message'].get('chat', {}).get('id')
        elif 'callback_query' in self.update:
            return self.update['callback_query'].get('message', {}).get('chat', {}).get('id')
        return None
        
    def _extract_message_id(self) -> Optional[int]:
        """Extract message ID from update"""
        if 'message' in self.update:
            return self.update['message'].get('message_id')
        elif 'callback_query' in self.update:
            return self.update['callback_query'].get('message', {}).get('message_id')
        return None
        
    @property
    def processing_time(self) -> float:
        """Get current processing time in seconds"""
        return time.time() - self.start_time

# Built-in middlewares

class LoggingMiddleware:
    """Logs all incoming updates"""
    
    def __init__(self, level: int = logging.INFO, include_data: bool = False):
        self.logger = logging.getLogger(f"{__name__}.LoggingMiddleware")
        self.level = level
        self.include_data = include_data
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        update_type = list(update.keys())[1] if len(update) > 1 else 'unknown'
        
        log_msg = f"Update {update.get('update_id', 'N/A')} ({update_type})"
        if context.user_id:
            log_msg += f" from user {context.user_id}"
        if context.chat_id:
            log_msg += f" in chat {context.chat_id}"
            
        if self.include_data:
            log_msg += f" - Data: {update}"
            
        self.logger.log(self.level, log_msg)
        return True

class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, max_requests: int = 30, window: int = 60, 
                 per_user: bool = True, per_chat: bool = False):
        self.max_requests = max_requests
        self.window = window
        self.per_user = per_user
        self.per_chat = per_chat
        
        self._user_requests: Dict[int, List[float]] = {}
        self._chat_requests: Dict[Union[int, str], List[float]] = {}
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        now = time.time()
        
        if self.per_user and context.user_id:
            if not self._check_limit(self._user_requests, context.user_id, now):
                logger.warning(f"Rate limit exceeded for user {context.user_id}")
                return False
                
        if self.per_chat and context.chat_id:
            if not self._check_limit(self._chat_requests, context.chat_id, now):
                logger.warning(f"Rate limit exceeded for chat {context.chat_id}")
                return False
                
        return True
        
    def _check_limit(self, storage: Dict, key: Any, now: float) -> bool:
        """Check if request is within limits"""
        if key not in storage:
            storage[key] = []
            
        # Clean old requests
        storage[key] = [t for t in storage[key] if now - t < self.window]
        
        if len(storage[key]) >= self.max_requests:
            return False
            
        storage[key].append(now)
        return True

class AntiSpamMiddleware:
    """Anti-spam middleware"""
    
    def __init__(self, max_identical: int = 3, time_window: int = 60,
                 max_length: int = 1000, blocked_words: List[str] = None):
        self.max_identical = max_identical
        self.time_window = time_window
        self.max_length = max_length
        self.blocked_words = blocked_words or []
        
        self._user_messages: Dict[int, List[Dict]] = {}
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        if 'message' not in update or not context.user_id:
            return True
            
        message = update['message']
        text = message.get('text', '')
        
        # Check message length
        if len(text) > self.max_length:
            logger.warning(f"Long message from user {context.user_id}")
            return False
            
        # Check for blocked words
        text_lower = text.lower()
        for word in self.blocked_words:
            if word.lower() in text_lower:
                logger.warning(f"Blocked word '{word}' from user {context.user_id}")
                return False
                
        # Check for identical messages
        now = time.time()
        user_id = context.user_id
        
        if user_id not in self._user_messages:
            self._user_messages[user_id] = []
            
        # Clean old messages
        self._user_messages[user_id] = [
            msg for msg in self._user_messages[user_id]
            if now - msg['time'] < self.time_window
        ]
        
        # Count identical messages
        identical_count = sum(
            1 for msg in self._user_messages[user_id]
            if msg['text'] == text
        )
        
        if identical_count >= self.max_identical:
            logger.warning(f"Spam detected from user {context.user_id}")
            return False
            
        # Store message
        self._user_messages[user_id].append({
            'text': text,
            'time': now
        })
        
        return True

class AuthMiddleware:
    """Authentication middleware"""
    
    def __init__(self, allowed_users: List[int] = None,
                 allowed_chats: List[Union[int, str]] = None,
                 admin_only: bool = False):
        self.allowed_users = set(allowed_users) if allowed_users else None
        self.allowed_chats = set(allowed_chats) if allowed_chats else None
        self.admin_only = admin_only
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        # Check allowed users
        if self.allowed_users and context.user_id:
            if context.user_id not in self.allowed_users:
                logger.warning(f"Unauthorized user {context.user_id}")
                return False
                
        # Check allowed chats
        if self.allowed_chats and context.chat_id:
            if context.chat_id not in self.allowed_chats:
                logger.warning(f"Unauthorized chat {context.chat_id}")
                return False
                
        # Check admin status (basic implementation)
        if self.admin_only and context.user_id and context.chat_id:
            try:
                admins = await bot.get_chat_admins(context.chat_id)
                admin_ids = [admin['user']['id'] for admin in admins]
                if context.user_id not in admin_ids:
                    logger.warning(f"Non-admin user {context.user_id} in chat {context.chat_id}")
                    return False
            except Exception:
                return False
                
        return True

class PerformanceMiddleware:
    """Performance monitoring middleware"""
    
    def __init__(self, slow_threshold: float = 1.0):
        self.slow_threshold = slow_threshold
        self.stats = {
            'total_requests': 0,
            'slow_requests': 0,
            'avg_processing_time': 0.0,
            'max_processing_time': 0.0
        }
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        # This runs before processing
        return True
        
    async def after_processing(self, context: MiddlewareContext, response: Any = None):
        """Called after processing completes"""
        processing_time = context.processing_time
        
        self.stats['total_requests'] += 1
        
        if processing_time > self.slow_threshold:
            self.stats['slow_requests'] += 1
            logger.warning(f"Slow request: {processing_time:.3f}s for update {context.update.get('update_id')}")
            
        # Update average
        total = self.stats['total_requests']
        current_avg = self.stats['avg_processing_time']
        self.stats['avg_processing_time'] = (current_avg * (total - 1) + processing_time) / total
        
        # Update max
        if processing_time > self.stats['max_processing_time']:
            self.stats['max_processing_time'] = processing_time
            
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.stats.copy()

class CacheMiddleware:
    """Response caching middleware"""
    
    def __init__(self, cache_time: int = 300, max_size: int = 1000):
        self.cache_time = cache_time
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        
    async def __call__(self, update: Dict, bot: Any, context: MiddlewareContext):
        # Generate cache key
        cache_key = self._generate_key(update)
        
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data['time'] < self.cache_time:
                context.data['cached_response'] = cached_data['response']
                return True
                
        return True
        
    def _generate_key(self, update: Dict) -> str:
        """Generate cache key from update"""
        if 'message' in update:
            msg = update['message']
            return f"msg_{msg.get('from', {}).get('id')}_{msg.get('text', '')[:50]}"
        elif 'callback_query' in update:
            cb = update['callback_query']
            return f"cb_{cb.get('from', {}).get('id')}_{cb.get('data', '')}"
        return f"update_{update.get('update_id', 'unknown')}"
        
    async def cache_response(self, context: MiddlewareContext, response: Any):
        """Cache response for future use"""
        cache_key = self._generate_key(context.update)
        
        # Clean old entries if cache is full
        if len(self._cache) >= self.max_size:
            old_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k]['time'])[:100]
            for key in old_keys:
                del self._cache[key]
                
        self._cache[cache_key] = {
            'response': response,
            'time': time.time()
        }

def middleware(middleware_func: Callable):
    """Decorator to create middleware from function"""
    return middleware_func

def rate_limit(max_requests: int = 30, window: int = 60, per_user: bool = True):
    """Rate limiting decorator"""
    def decorator(func):
        middleware_obj = RateLimitMiddleware(max_requests, window, per_user)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need bot context to work properly
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def anti_spam(max_identical: int = 3, time_window: int = 60):
    """Anti-spam decorator"""
    def decorator(func):
        middleware_obj = AntiSpamMiddleware(max_identical, time_window)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
