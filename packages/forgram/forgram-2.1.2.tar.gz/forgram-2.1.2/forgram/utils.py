"""
Forgram Utils Module
Utility functions and helpers for common tasks
"""

import re
import asyncio
import hashlib
import base64
import random
import string
import time
from typing import Union, List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import urllib.parse
import html
import json

# Text processing utilities

def escape_html(text: str) -> str:
    """Escape HTML characters in text"""
    return html.escape(text)

def escape_markdown(text: str, version: int = 2) -> str:
    """Escape MarkdownV2 characters"""
    if version == 2:
        # MarkdownV2 special characters
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
    else:
        # Markdown V1
        chars_to_escape = ['_', '*', '[', '`']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
    
    return text

def mention_html(user_id: int, name: str) -> str:
    """Create HTML mention"""
    return f'<a href="tg://user?id={user_id}">{escape_html(name)}</a>'

def mention_markdown(user_id: int, name: str) -> str:
    """Create Markdown mention"""
    escaped_name = escape_markdown(name)
    return f'[{escaped_name}](tg://user?id={user_id})'

def extract_command_args(text: str, command: str) -> str:
    """Extract arguments from command"""
    pattern = rf'^/{command}(?:@\w+)?\s*(.*)$'
    match = re.match(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ''

def split_text(text: str, max_length: int = 4096, split_by: str = '\n') -> List[str]:
    """Split text into chunks respecting max length"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ''
    
    for part in text.split(split_by):
        if len(current_chunk + part + split_by) <= max_length:
            current_chunk += part + split_by
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip(split_by))
                current_chunk = part + split_by
            else:
                # Single part is too long, force split
                while len(part) > max_length:
                    chunks.append(part[:max_length])
                    part = part[max_length:]
                current_chunk = part + split_by
    
    if current_chunk:
        chunks.append(current_chunk.rstrip(split_by))
    
    return chunks

def clean_text(text: str) -> str:
    """Clean text from extra whitespace and special characters"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters except newline and tab
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    hashtag_pattern = r'#\w+'
    return re.findall(hashtag_pattern, text)

def extract_mentions(text: str) -> List[str]:
    """Extract mentions from text"""
    mention_pattern = r'@\w+'
    return re.findall(mention_pattern, text)

# Time utilities

def format_duration(seconds: int) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h" if hours else f"{days}d"

def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds"""
    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, duration_str.lower())
    
    total_seconds = 0
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    
    for value, unit in matches:
        total_seconds += int(value) * multipliers.get(unit, 1)
    
    return total_seconds

def format_timestamp(timestamp: Union[int, float], format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format timestamp to string"""
    return datetime.fromtimestamp(timestamp).strftime(format_str)

def get_relative_time(timestamp: Union[int, float]) -> str:
    """Get relative time (e.g., '2 hours ago')"""
    now = time.time()
    diff = int(now - timestamp)
    
    if diff < 60:
        return "just now"
    elif diff < 3600:
        minutes = diff // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif diff < 86400:
        hours = diff // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < 2592000:  # 30 days
        days = diff // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return format_timestamp(timestamp, '%Y-%m-%d')

# Validation utilities

def is_valid_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    pattern = r'^\d{8,10}:[a-zA-Z0-9_-]{35}$'
    return bool(re.match(pattern, token))

def is_valid_user_id(user_id: Union[int, str]) -> bool:
    """Validate Telegram user ID"""
    try:
        uid = int(user_id)
        return 1 <= uid <= 2147483647  # Max 32-bit signed integer
    except (ValueError, TypeError):
        return False

def is_valid_chat_id(chat_id: Union[int, str]) -> bool:
    """Validate Telegram chat ID"""
    try:
        cid = int(chat_id)
        # User IDs are positive, group/channel IDs are negative
        return -1002147483647 <= cid <= 2147483647
    except (ValueError, TypeError):
        return False

def is_valid_username(username: str) -> bool:
    """Validate Telegram username format"""
    if not username:
        return False
    
    # Remove @ if present
    if username.startswith('@'):
        username = username[1:]
    
    # Username rules: 5-32 chars, alphanumeric + underscore, must start with letter
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Crypto utilities

def generate_random_string(length: int = 32, chars: str = None) -> str:
    """Generate random string"""
    if chars is None:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash string using specified algorithm"""
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def encode_base64(data: Union[str, bytes]) -> str:
    """Encode data to base64"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')

def decode_base64(data: str) -> bytes:
    """Decode base64 data"""
    return base64.b64decode(data.encode('ascii'))

# File utilities

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def get_mime_type(filename: str) -> str:
    """Get MIME type by file extension"""
    ext = get_file_extension(filename)
    
    mime_types = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp',
        'mp4': 'video/mp4', 'avi': 'video/avi', 'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv', 'flv': 'video/x-flv', 'webm': 'video/webm',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
        'flac': 'audio/flac', 'aac': 'audio/aac', 'm4a': 'audio/m4a',
        'pdf': 'application/pdf', 'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain', 'csv': 'text/csv', 'json': 'application/json',
        'xml': 'application/xml', 'html': 'text/html', 'css': 'text/css',
        'js': 'application/javascript', 'py': 'text/x-python',
        'zip': 'application/zip', 'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed', 'tar': 'application/x-tar',
        'gz': 'application/gzip'
    }
    
    return mime_types.get(ext, 'application/octet-stream')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

# Data structures utilities

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def remove_duplicates(lst: List, key: Callable = None) -> List:
    """Remove duplicates from list"""
    if key is None:
        return list(dict.fromkeys(lst))  # Preserves order
    
    seen = set()
    result = []
    for item in lst:
        k = key(item)
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result

# Async utilities

async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout)

async def gather_with_limit(tasks: List, limit: int = 10):
    """Run tasks with concurrency limit"""
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[limited_task(task) for task in tasks])

def retry_async(max_attempts: int = 3, delay: float = 1.0, 
                backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Async retry decorator"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise e
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
                    
        return wrapper
    return decorator

# Rate limiting utilities

class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        now = time.time()
        # Add tokens based on time passed
        self.tokens = min(
            self.capacity,
            self.tokens + (now - self.last_refill) * self.refill_rate
        )
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time for tokens"""
        if self.tokens >= tokens:
            return 0.0
        
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if call is allowed"""
        now = time.time()
        # Remove old calls
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
    
    def wait_time(self) -> float:
        """Calculate wait time"""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))

# Logging utilities

def setup_logging(level: str = 'INFO', format_str: str = None, 
                 file_path: str = None) -> None:
    """Setup logging configuration"""
    import logging
    
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    logging.basicConfig(
        level=level_map.get(level.upper(), logging.INFO),
        format=format_str,
        filename=file_path
    )

# Memory utilities

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    except ImportError:
        return {'error': 'psutil not installed'}

# Bot utilities

def create_deep_link(bot_username: str, payload: str) -> str:
    """Create deep link for bot"""
    return f"https://t.me/{bot_username}?start={payload}"

def create_inline_link(bot_username: str, query: str = '') -> str:
    """Create inline link for bot"""
    if query:
        return f"https://t.me/{bot_username}?startinline={urllib.parse.quote(query)}"
    return f"https://t.me/{bot_username}?startinline"

def parse_deep_link_payload(text: str) -> Optional[str]:
    """Parse payload from /start command"""
    if not text.startswith('/start'):
        return None
    
    parts = text.split(None, 1)
    return parts[1] if len(parts) > 1 else None

# JSON utilities

def safe_json_loads(json_str: str, default=None):
    """Safe JSON loading with default value"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safe JSON dumping with error handling"""
    try:
        return json.dumps(obj, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError):
        return '{}'

# Template utilities

def simple_template(template: str, **kwargs) -> str:
    """Simple string template replacement"""
    for key, value in kwargs.items():
        template = template.replace(f'{{{key}}}', str(value))
    return template

# Health check utilities

async def health_check_bot(bot) -> Dict[str, Any]:
    """Perform health check on bot"""
    result = {
        'status': 'unknown',
        'api_accessible': False,
        'bot_info': None,
        'webhook_info': None,
        'response_time': None
    }
    
    try:
        start_time = time.time()
        
        # Test getMe
        bot_info = await bot.get_me()
        result['bot_info'] = bot_info
        result['api_accessible'] = True
        
        # Test webhook info
        try:
            webhook_info = await bot.get_webhook_info()
            result['webhook_info'] = webhook_info
        except:
            pass
        
        result['response_time'] = time.time() - start_time
        result['status'] = 'healthy'
        
    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
    
    return result
