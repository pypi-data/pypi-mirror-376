"""
Forgram HTTP Client Module
Advanced HTTP client with connection pooling, retries, and rate limiting
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin
import json
from .exceptions import NetworkError, APIError, RateLimitError

logger = logging.getLogger(__name__)

class HTTPClient:
    """Advanced HTTP client for Telegram API with enterprise features"""
    
    def __init__(self, token: str, base_url: str = "https://api.telegram.org/bot",
                 timeout: float = 30.0, connector_limit: int = 100,
                 rate_limit: bool = True, max_retries: int = 3):
        self.token = token
        self.base_url = base_url.rstrip('/') + token + '/'
        self.file_url = f"https://api.telegram.org/file/bot{token}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.connector_limit = connector_limit
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        
        # Rate limiting
        self._request_times = []
        self._rate_limit_window = 60  # 1 minute
        self._max_requests = 30  # 30 requests per minute default
        
        # Connection pooling
        self._session = None
        self._connector = None
        
        # Request statistics
        self._total_requests = 0
        self._failed_requests = 0
        self._retry_count = 0
        self._avg_response_time = 0.0
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Initialize HTTP session with optimized settings"""
        self._connector = aiohttp.TCPConnector(
            limit=self.connector_limit,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=self.timeout,
            headers={
                'User-Agent': 'Forgram/2.1.0 (Python Bot Library)',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
        )
        
    async def close(self):
        """Clean shutdown of HTTP client"""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
            
    def _check_rate_limit(self):
        """Check if request is within rate limits"""
        if not self.rate_limit:
            return True
            
        now = time.time()
        # Remove old requests outside window
        self._request_times = [t for t in self._request_times 
                              if now - t < self._rate_limit_window]
        
        if len(self._request_times) >= self._max_requests:
            sleep_time = self._rate_limit_window - (now - self._request_times[0])
            raise RateLimitError(f"Rate limit exceeded. Retry after {sleep_time:.1f}s")
            
        self._request_times.append(now)
        return True
        
    async def request(self, method: str, data: Dict[str, Any] = None,
                     files: Dict[str, Any] = None, **kwargs) -> Any:
        """Make HTTP request with retries and error handling"""
        if not self._session:
            await self.start()
            
        self._check_rate_limit()
        
        url = urljoin(self.base_url, method)
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                # Prepare request data
                request_kwargs = {}
                
                if files:
                    # Multipart form data for file uploads
                    form_data = aiohttp.FormData()
                    
                    if data:
                        for key, value in data.items():
                            if isinstance(value, (dict, list)):
                                form_data.add_field(key, json.dumps(value))
                            else:
                                form_data.add_field(key, str(value))
                    
                    for key, file_data in files.items():
                        if hasattr(file_data, 'read'):
                            # File-like object
                            form_data.add_field(key, file_data)
                        elif isinstance(file_data, bytes):
                            # Raw bytes
                            form_data.add_field(key, file_data)
                        else:
                            # File path or file_id
                            form_data.add_field(key, str(file_data))
                            
                    request_kwargs['data'] = form_data
                    
                elif data:
                    request_kwargs['data'] = data
                    
                async with self._session.post(url, **request_kwargs) as response:
                    response_time = time.time() - start_time
                    self._update_stats(response_time, response.status == 200)
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        if response_data.get('ok'):
                            return response_data.get('result')
                        else:
                            error_code = response_data.get('error_code', 0)
                            description = response_data.get('description', 'Unknown error')
                            
                            if error_code == 429:  # Too Many Requests
                                retry_after = response_data.get('parameters', {}).get('retry_after', 1)
                                if attempt < self.max_retries:
                                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                                    await asyncio.sleep(retry_after)
                                    continue
                                raise RateLimitError(f"Rate limited: {description}")
                            
                            raise APIError(f"API Error {error_code}: {description}")
                    
                    elif response.status in [500, 502, 503, 504]:  # Server errors
                        if attempt < self.max_retries:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Server error {response.status}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        raise NetworkError(f"Server error: {response.status}")
                    
                    else:
                        raise NetworkError(f"HTTP error: {response.status}")
                        
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries + 1}")
                    await asyncio.sleep(1)
                    continue
                raise NetworkError("Request timeout")
                
            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    logger.warning(f"Client error: {e}, attempt {attempt + 1}/{self.max_retries + 1}")
                    await asyncio.sleep(1)
                    continue
                raise NetworkError(f"Client error: {e}")
                
        raise NetworkError("Max retries exceeded")
        
    def _update_stats(self, response_time: float, success: bool):
        """Update request statistics"""
        self._total_requests += 1
        if not success:
            self._failed_requests += 1
            
        # Update average response time
        if self._total_requests == 1:
            self._avg_response_time = response_time
        else:
            self._avg_response_time = (
                (self._avg_response_time * (self._total_requests - 1) + response_time) 
                / self._total_requests
            )
            
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Telegram servers"""
        if not self._session:
            await self.start()
            
        url = f"{self.file_url}/{file_path}"
        
        try:
            async with self._session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise NetworkError(f"Failed to download file: {response.status}")
        except Exception as e:
            raise NetworkError(f"Download error: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP client statistics"""
        success_rate = 0.0
        if self._total_requests > 0:
            success_rate = ((self._total_requests - self._failed_requests) 
                           / self._total_requests * 100)
            
        return {
            'total_requests': self._total_requests,
            'failed_requests': self._failed_requests,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(self._avg_response_time * 1000, 2),  # ms
            'retry_count': self._retry_count,
            'active_connections': len(self._request_times) if self._request_times else 0
        }
        
    def set_rate_limit(self, max_requests: int, window: int = 60):
        """Configure rate limiting"""
        self._max_requests = max_requests
        self._rate_limit_window = window
        
    async def test_connection(self) -> bool:
        """Test connection to Telegram API"""
        try:
            result = await self.request('getMe')
            return result is not None
        except Exception:
            return False
