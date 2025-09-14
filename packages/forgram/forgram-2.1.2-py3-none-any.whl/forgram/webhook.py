"""
Forgram Webhook Module
Advanced webhook handling with Flask/FastAPI integration
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any, Union
from urllib.parse import urljoin
import hmac
import hashlib

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Advanced webhook handler with security features"""
    
    def __init__(self, bot, webhook_path: str = "/webhook", 
                 secret_token: str = None, verify_ip: bool = True):
        self.bot = bot
        self.webhook_path = webhook_path
        self.secret_token = secret_token
        self.verify_ip = verify_ip
        
        # Telegram webhook IPs (as of 2024)
        self.telegram_ips = [
            '149.154.160.0/20',
            '91.108.4.0/22',
            '91.108.56.0/22',
            '91.108.56.0/23',
            '149.154.160.0/22',
            '149.154.164.0/22',
            '149.154.168.0/22',
            '149.154.172.0/22'
        ]
        
        self.stats = {
            'total_requests': 0,
            'valid_requests': 0,
            'invalid_requests': 0,
            'last_update_id': 0
        }
    
    def _verify_telegram_ip(self, client_ip: str) -> bool:
        """Verify request comes from Telegram servers"""
        if not self.verify_ip:
            return True
            
        import ipaddress
        client_addr = ipaddress.ip_address(client_ip)
        
        for ip_range in self.telegram_ips:
            if client_addr in ipaddress.ip_network(ip_range):
                return True
        
        return False
    
    def _verify_secret_token(self, request_token: str) -> bool:
        """Verify secret token"""
        if not self.secret_token:
            return True
        
        return hmac.compare_digest(self.secret_token, request_token or '')
    
    async def process_update(self, update_data: Dict[str, Any], 
                           client_ip: str = None, secret_token: str = None) -> bool:
        """Process webhook update with security checks"""
        self.stats['total_requests'] += 1
        
        # Verify IP
        if client_ip and not self._verify_telegram_ip(client_ip):
            logger.warning(f"Invalid IP: {client_ip}")
            self.stats['invalid_requests'] += 1
            return False
        
        # Verify secret token
        if not self._verify_secret_token(secret_token):
            logger.warning("Invalid secret token")
            self.stats['invalid_requests'] += 1
            return False
        
        # Update stats
        update_id = update_data.get('update_id', 0)
        if update_id > self.stats['last_update_id']:
            self.stats['last_update_id'] = update_id
        
        self.stats['valid_requests'] += 1
        
        # Process update
        try:
            await self.bot._process_update(update_data)
            return True
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        return self.stats.copy()

class FlaskWebhookHandler(WebhookHandler):
    """Flask-based webhook handler"""
    
    def __init__(self, bot, app=None, **kwargs):
        super().__init__(bot, **kwargs)
        self.app = app
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        if not self.app:
            return
        
        @self.app.route(self.webhook_path, methods=['POST'])
        def webhook():
            from flask import request, jsonify
            
            try:
                # Get client IP
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                              request.environ.get('REMOTE_ADDR'))
                
                # Get secret token
                secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
                
                # Get update data
                update_data = request.get_json()
                
                # Process in background
                asyncio.create_task(
                    self.process_update(update_data, client_ip, secret_token)
                )
                
                return jsonify({'ok': True})
                
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return jsonify({'error': str(e)}), 400
        
        @self.app.route(f"{self.webhook_path}/health", methods=['GET'])
        def health():
            from flask import jsonify
            return jsonify({
                'status': 'ok',
                'bot': self.bot.username if hasattr(self.bot, 'username') else 'unknown',
                'stats': self.get_stats()
            })

class FastAPIWebhookHandler(WebhookHandler):
    """FastAPI-based webhook handler"""
    
    def __init__(self, bot, app=None, **kwargs):
        super().__init__(bot, **kwargs)
        self.app = app
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        if not self.app:
            return
        
        @self.app.post(self.webhook_path)
        async def webhook(request):
            try:
                # Get client IP
                client_ip = request.client.host
                
                # Get secret token
                secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
                
                # Get update data
                update_data = await request.json()
                
                # Process update
                success = await self.process_update(update_data, client_ip, secret_token)
                
                return {'ok': success}
                
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get(f"{self.webhook_path}/health")
        async def health():
            return {
                'status': 'ok',
                'bot': self.bot.username if hasattr(self.bot, 'username') else 'unknown',
                'stats': self.get_stats()
            }

class AioHttpWebhookHandler(WebhookHandler):
    """aiohttp-based webhook handler"""
    
    def __init__(self, bot, app=None, **kwargs):
        super().__init__(bot, **kwargs)
        self.app = app
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup aiohttp routes"""
        if not self.app:
            return
        
        async def webhook_handler(request):
            try:
                # Get client IP
                client_ip = request.remote
                
                # Get secret token
                secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
                
                # Get update data
                update_data = await request.json()
                
                # Process update
                success = await self.process_update(update_data, client_ip, secret_token)
                
                from aiohttp import web
                return web.json_response({'ok': success})
                
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                from aiohttp import web
                return web.json_response({'error': str(e)}, status=400)
        
        async def health_handler(request):
            from aiohttp import web
            return web.json_response({
                'status': 'ok',
                'bot': self.bot.username if hasattr(self.bot, 'username') else 'unknown',
                'stats': self.get_stats()
            })
        
        self.app.router.add_post(self.webhook_path, webhook_handler)
        self.app.router.add_get(f"{self.webhook_path}/health", health_handler)

class WebhookServer:
    """Standalone webhook server"""
    
    def __init__(self, bot, host: str = '0.0.0.0', port: int = 8080,
                 ssl_context=None, **webhook_kwargs):
        self.bot = bot
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        
        self.handler = WebhookHandler(bot, **webhook_kwargs)
        self.app = None
        self.runner = None
    
    async def start(self):
        """Start webhook server"""
        from aiohttp import web
        
        self.app = web.Application()
        
        # Setup handler
        aiohttp_handler = AioHttpWebhookHandler(self.bot, self.app, 
                                               webhook_path=self.handler.webhook_path,
                                               secret_token=self.handler.secret_token,
                                               verify_ip=self.handler.verify_ip)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port, ssl_context=self.ssl_context)
        await site.start()
        
        protocol = 'https' if self.ssl_context else 'http'
        logger.info(f"Webhook server started on {protocol}://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop webhook server"""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Webhook server stopped")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

class WebhookManager:
    """Manage webhook configuration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.current_webhook = None
    
    async def set_webhook(self, url: str, certificate=None, secret_token: str = None,
                         allowed_updates: list = None, drop_pending_updates: bool = False,
                         max_connections: int = 40):
        """Set webhook with enhanced options"""
        params = {
            'url': url,
            'drop_pending_updates': drop_pending_updates,
            'max_connections': max_connections
        }
        
        if certificate:
            params['certificate'] = certificate
        
        if secret_token:
            params['secret_token'] = secret_token
        
        if allowed_updates:
            params['allowed_updates'] = json.dumps(allowed_updates)
        
        result = await self.bot._request('setWebhook', params)
        
        if result:
            self.current_webhook = {
                'url': url,
                'secret_token': secret_token,
                'max_connections': max_connections,
                'allowed_updates': allowed_updates
            }
            logger.info(f"Webhook set to {url}")
        
        return result
    
    async def delete_webhook(self, drop_pending_updates: bool = False):
        """Delete webhook"""
        result = await self.bot._request('deleteWebhook', {
            'drop_pending_updates': drop_pending_updates
        })
        
        if result:
            self.current_webhook = None
            logger.info("Webhook deleted")
        
        return result
    
    async def get_webhook_info(self):
        """Get webhook info"""
        return await self.bot._request('getWebhookInfo')
    
    async def check_webhook(self) -> Dict[str, Any]:
        """Check webhook status"""
        info = await self.get_webhook_info()
        
        status = {
            'is_set': bool(info.get('url')),
            'url': info.get('url'),
            'pending_updates': info.get('pending_update_count', 0),
            'last_error': info.get('last_error_message'),
            'last_error_date': info.get('last_error_date'),
            'max_connections': info.get('max_connections'),
            'allowed_updates': info.get('allowed_updates', [])
        }
        
        return status
    
    def create_handler(self, framework: str = 'aiohttp', **kwargs):
        """Create webhook handler for specific framework"""
        if framework == 'flask':
            return FlaskWebhookHandler(self.bot, **kwargs)
        elif framework == 'fastapi':
            return FastAPIWebhookHandler(self.bot, **kwargs)
        elif framework == 'aiohttp':
            return AioHttpWebhookHandler(self.bot, **kwargs)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
    
    def create_server(self, **kwargs):
        """Create standalone webhook server"""
        return WebhookServer(self.bot, **kwargs)

# Webhook utilities

async def auto_setup_webhook(bot, domain: str, port: int = 443, 
                           certificate_path: str = None, secret_token: str = None):
    """Auto-setup webhook with SSL certificate"""
    webhook_url = f"https://{domain}:{port}/webhook"
    
    certificate = None
    if certificate_path:
        with open(certificate_path, 'rb') as cert_file:
            certificate = cert_file.read()
    
    manager = WebhookManager(bot)
    return await manager.set_webhook(
        webhook_url, 
        certificate=certificate,
        secret_token=secret_token
    )

def generate_secret_token(length: int = 32) -> str:
    """Generate secure secret token"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def test_webhook_connectivity(webhook_url: str, timeout: int = 10) -> bool:
    """Test webhook URL connectivity"""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(f"{webhook_url}/health") as response:
                return response.status == 200
    except Exception:
        return False

class WebhookMonitor:
    """Monitor webhook health and performance"""
    
    def __init__(self, bot, check_interval: int = 300):
        self.bot = bot
        self.check_interval = check_interval
        self.monitoring = False
        self.stats = {
            'checks': 0,
            'errors': 0,
            'last_check': None,
            'last_error': None
        }
    
    async def start_monitoring(self):
        """Start webhook monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                await self._check_webhook_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Webhook monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_webhook_health(self):
        """Check webhook health"""
        self.stats['checks'] += 1
        self.stats['last_check'] = time.time()
        
        try:
            manager = WebhookManager(self.bot)
            info = await manager.get_webhook_info()
            
            # Check for errors
            if info.get('last_error_message'):
                self.stats['errors'] += 1
                self.stats['last_error'] = {
                    'message': info['last_error_message'],
                    'date': info.get('last_error_date'),
                    'timestamp': time.time()
                }
                
                logger.warning(f"Webhook error detected: {info['last_error_message']}")
            
            # Check pending updates
            pending = info.get('pending_update_count', 0)
            if pending > 100:
                logger.warning(f"High pending updates count: {pending}")
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Health check failed: {e}")
    
    def stop_monitoring(self):
        """Stop webhook monitoring"""
        self.monitoring = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return self.stats.copy()
