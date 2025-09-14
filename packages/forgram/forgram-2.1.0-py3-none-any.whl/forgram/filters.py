"""
Forgram Filters Module
Advanced filtering system for message processing
"""

import re
import asyncio
from typing import List, Union, Callable, Any, Dict, Optional, Pattern
from functools import wraps

class BaseFilter:
    """Base class for all filters"""
    
    def __call__(self, message) -> bool:
        raise NotImplementedError
        
    def __and__(self, other):
        return AndFilter(self, other)
        
    def __or__(self, other):
        return OrFilter(self, other)
        
    def __invert__(self):
        return NotFilter(self)

class AndFilter(BaseFilter):
    """Logical AND filter"""
    
    def __init__(self, *filters):
        self.filters = filters
        
    def __call__(self, message) -> bool:
        return all(f(message) for f in self.filters)

class OrFilter(BaseFilter):
    """Logical OR filter"""
    
    def __init__(self, *filters):
        self.filters = filters
        
    def __call__(self, message) -> bool:
        return any(f(message) for f in self.filters)

class NotFilter(BaseFilter):
    """Logical NOT filter"""
    
    def __init__(self, filter_obj):
        self.filter = filter_obj
        
    def __call__(self, message) -> bool:
        return not self.filter(message)

class CommandFilter(BaseFilter):
    """Filter for bot commands"""
    
    def __init__(self, commands: Union[str, List[str]], prefix: str = '/'):
        if isinstance(commands, str):
            commands = [commands]
        self.commands = [f"{prefix}{cmd}" if not cmd.startswith(prefix) else cmd 
                        for cmd in commands]
        
    def __call__(self, message) -> bool:
        if not message.text:
            return False
        text = message.text.split()[0].lower()
        return text in [cmd.lower() for cmd in self.commands]

class TextFilter(BaseFilter):
    """Filter for text messages"""
    
    def __init__(self, text: Union[str, List[str]] = None, contains: str = None,
                 startswith: str = None, endswith: str = None, ignore_case: bool = True):
        self.text = text
        self.contains = contains
        self.startswith = startswith
        self.endswith = endswith
        self.ignore_case = ignore_case
        
    def __call__(self, message) -> bool:
        if not message.text:
            return False
            
        msg_text = message.text
        if self.ignore_case:
            msg_text = msg_text.lower()
            
        if self.text:
            texts = [self.text] if isinstance(self.text, str) else self.text
            if self.ignore_case:
                texts = [t.lower() for t in texts]
            return msg_text in texts
            
        if self.contains:
            check_text = self.contains.lower() if self.ignore_case else self.contains
            return check_text in msg_text
            
        if self.startswith:
            check_text = self.startswith.lower() if self.ignore_case else self.startswith
            return msg_text.startswith(check_text)
            
        if self.endswith:
            check_text = self.endswith.lower() if self.ignore_case else self.endswith
            return msg_text.endswith(check_text)
            
        return bool(message.text)

class RegexFilter(BaseFilter):
    """Filter for regex patterns"""
    
    def __init__(self, pattern: Union[str, Pattern], flags: int = 0):
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, flags)
        else:
            self.pattern = pattern
            
    def __call__(self, message) -> bool:
        if not message.text:
            return False
        match = self.pattern.search(message.text)
        if match:
            message.matches = match.groups()
            message.match = match
            return True
        return False

class ContentTypeFilter(BaseFilter):
    """Filter for content types"""
    
    def __init__(self, content_types: Union[str, List[str]]):
        if isinstance(content_types, str):
            content_types = [content_types]
        self.content_types = content_types
        
    def __call__(self, message) -> bool:
        if hasattr(message, 'content_type'):
            return message.content_type in self.content_types
            
        # Determine content type from message
        if message.text:
            return 'text' in self.content_types
        elif message.photo:
            return 'photo' in self.content_types
        elif message.video:
            return 'video' in self.content_types
        elif message.document:
            return 'document' in self.content_types
        elif message.audio:
            return 'audio' in self.content_types
        elif message.voice:
            return 'voice' in self.content_types
        elif message.sticker:
            return 'sticker' in self.content_types
        elif hasattr(message, 'animation') and message.animation:
            return 'animation' in self.content_types
        elif hasattr(message, 'video_note') and message.video_note:
            return 'video_note' in self.content_types
        elif hasattr(message, 'contact') and message.contact:
            return 'contact' in self.content_types
        elif hasattr(message, 'location') and message.location:
            return 'location' in self.content_types
        elif hasattr(message, 'venue') and message.venue:
            return 'venue' in self.content_types
        elif hasattr(message, 'poll') and message.poll:
            return 'poll' in self.content_types
        elif hasattr(message, 'dice') and message.dice:
            return 'dice' in self.content_types
            
        return False

class ChatTypeFilter(BaseFilter):
    """Filter for chat types"""
    
    def __init__(self, chat_types: Union[str, List[str]]):
        if isinstance(chat_types, str):
            chat_types = [chat_types]
        self.chat_types = chat_types
        
    def __call__(self, message) -> bool:
        return message.chat.type in self.chat_types

class UserFilter(BaseFilter):
    """Filter for specific users"""
    
    def __init__(self, user_ids: Union[int, List[int]]):
        if isinstance(user_ids, int):
            user_ids = [user_ids]
        self.user_ids = user_ids
        
    def __call__(self, message) -> bool:
        return message.user.id in self.user_ids

class AdminFilter(BaseFilter):
    """Filter for admin users (requires bot instance)"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self._admin_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def is_admin(self, user_id: int, chat_id: Union[int, str]) -> bool:
        if not self.bot:
            return False
            
        cache_key = f"{chat_id}:{user_id}"
        now = asyncio.get_event_loop().time()
        
        # Check cache
        if cache_key in self._admin_cache:
            cached_time, is_admin = self._admin_cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return is_admin
                
        try:
            admins = await self.bot.get_chat_admins(chat_id)
            admin_ids = [admin['user']['id'] for admin in admins]
            is_admin = user_id in admin_ids
            
            # Cache result
            self._admin_cache[cache_key] = (now, is_admin)
            return is_admin
            
        except Exception:
            return False
    
    def __call__(self, message) -> bool:
        # For sync filtering, we can't check admin status
        # This should be used with async handler decorators
        return True

class ForwardedFilter(BaseFilter):
    """Filter for forwarded messages"""
    
    def __call__(self, message) -> bool:
        return hasattr(message, 'forward_from') and message.forward_from is not None

class ReplyFilter(BaseFilter):
    """Filter for reply messages"""
    
    def __call__(self, message) -> bool:
        return (hasattr(message, 'reply_to_message') and 
                message.reply_to_message is not None)

class MediaGroupFilter(BaseFilter):
    """Filter for media group messages"""
    
    def __call__(self, message) -> bool:
        return (hasattr(message, 'media_group_id') and 
                message.media_group_id is not None)

class LanguageFilter(BaseFilter):
    """Filter messages by language (simple heuristic)"""
    
    def __init__(self, languages: Union[str, List[str]]):
        if isinstance(languages, str):
            languages = [languages]
        self.languages = [lang.lower() for lang in languages]
        
        # Simple language detection patterns
        self.patterns = {
            'ru': re.compile(r'[а-яё]', re.IGNORECASE),
            'en': re.compile(r'[a-z]', re.IGNORECASE),
            'de': re.compile(r'[äöüß]', re.IGNORECASE),
            'fr': re.compile(r'[àâäçéèêëïîôöùûüÿ]', re.IGNORECASE),
            'es': re.compile(r'[ñáéíóúü]', re.IGNORECASE),
        }
        
    def __call__(self, message) -> bool:
        if not message.text:
            return False
            
        text = message.text
        detected_langs = []
        
        for lang, pattern in self.patterns.items():
            if pattern.search(text):
                detected_langs.append(lang)
                
        return any(lang in self.languages for lang in detected_langs)

class LengthFilter(BaseFilter):
    """Filter messages by text length"""
    
    def __init__(self, min_length: int = 0, max_length: int = float('inf')):
        self.min_length = min_length
        self.max_length = max_length
        
    def __call__(self, message) -> bool:
        if not message.text:
            return self.min_length == 0
        length = len(message.text)
        return self.min_length <= length <= self.max_length

class TimeFilter(BaseFilter):
    """Filter messages by time"""
    
    def __init__(self, start_hour: int = 0, end_hour: int = 23):
        self.start_hour = start_hour
        self.end_hour = end_hour
        
    def __call__(self, message) -> bool:
        import datetime
        now = datetime.datetime.now()
        hour = now.hour
        
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour <= self.end_hour
        else:
            # Overnight period (e.g., 22-6)
            return hour >= self.start_hour or hour <= self.end_hour

class CallbackDataFilter(BaseFilter):
    """Filter for callback query data"""
    
    def __init__(self, data: Union[str, List[str], Pattern] = None,
                 startswith: str = None, contains: str = None):
        self.data = data
        self.startswith = startswith
        self.contains = contains
        
        if isinstance(data, str) and not startswith and not contains:
            self.exact_match = data
        else:
            self.exact_match = None
            
    def __call__(self, callback_query) -> bool:
        if not hasattr(callback_query, 'data') or not callback_query.data:
            return False
            
        query_data = callback_query.data
        
        if self.exact_match:
            return query_data == self.exact_match
            
        if self.data:
            if isinstance(self.data, list):
                return query_data in self.data
            elif isinstance(self.data, Pattern):
                match = self.data.search(query_data)
                if match:
                    callback_query.matches = match.groups()
                    callback_query.match = match
                    return True
                return False
                
        if self.startswith:
            return query_data.startswith(self.startswith)
            
        if self.contains:
            return self.contains in query_data
            
        return True

# Pre-defined filter instances
all = BaseFilter()
text = TextFilter()
photo = ContentTypeFilter('photo')
video = ContentTypeFilter('video')
document = ContentTypeFilter('document')
audio = ContentTypeFilter('audio')
voice = ContentTypeFilter('voice')
sticker = ContentTypeFilter('sticker')
animation = ContentTypeFilter('animation')
contact = ContentTypeFilter('contact')
location = ContentTypeFilter('location')
venue = ContentTypeFilter('venue')
poll = ContentTypeFilter('poll')
dice = ContentTypeFilter('dice')

private = ChatTypeFilter('private')
group = ChatTypeFilter(['group', 'supergroup'])
channel = ChatTypeFilter('channel')

forwarded = ForwardedFilter()
reply = ReplyFilter()
media_group = MediaGroupFilter()

# Language filters
russian = LanguageFilter('ru')
english = LanguageFilter('en')
multilang = LanguageFilter(['ru', 'en'])

def create_filter(filter_func: Callable) -> BaseFilter:
    """Create custom filter from function"""
    
    class CustomFilter(BaseFilter):
        def __call__(self, message) -> bool:
            return filter_func(message)
            
    return CustomFilter()

def command(commands: Union[str, List[str]], prefix: str = '/'):
    """Create command filter"""
    return CommandFilter(commands, prefix)

def regex(pattern: Union[str, Pattern], flags: int = 0):
    """Create regex filter"""
    return RegexFilter(pattern, flags)

def content_type(*types):
    """Create content type filter"""
    return ContentTypeFilter(list(types))

def user(*user_ids):
    """Create user filter"""
    return UserFilter(list(user_ids))

def chat_type(*types):
    """Create chat type filter"""
    return ChatTypeFilter(list(types))

def length(min_len: int = 0, max_len: int = float('inf')):
    """Create length filter"""
    return LengthFilter(min_len, max_len)

def time_range(start: int, end: int):
    """Create time filter"""
    return TimeFilter(start, end)

def callback_data(data=None, **kwargs):
    """Create callback data filter"""
    return CallbackDataFilter(data, **kwargs)
