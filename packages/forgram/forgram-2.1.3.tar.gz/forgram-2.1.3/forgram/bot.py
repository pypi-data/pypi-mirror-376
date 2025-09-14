import asyncio
import logging
import time
import re
import os
from typing import Callable, Optional, List, Dict, Any, Union
import aiohttp
import json
from datetime import datetime, timedelta

from .models import Update, Message, User
from .exceptions import APIError, NetworkError


class Bot:
    def __init__(self, token: str, parse_mode: str = "HTML"):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.file_url = f"https://api.telegram.org/file/bot{token}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.parse_mode = parse_mode
        
        self._handlers = []
        self._callback_handlers = []
        self._middleware = []
        self._scheduled_tasks = []
        self._webhooks = []
        
        self._running = False
        self._offset = 0
        self._cache = {}
        self._rate_limits = {}
        self._auto_replies = []
        self._admin_ids = set()
        
        self.stats = {
            'messages': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'users': set(),
            'chats': set()
        }
        
        self.logger = logging.getLogger("forgram")
    
    async def _request(self, method: str, params: Optional[Dict] = None) -> Dict:
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.api_url}/{method}"
        
        try:
            async with self.session.post(url, json=params) as resp:
                data = await resp.json()
                
                if not data.get('ok'):
                    error_code = data.get('error_code')
                    description = data.get('description', 'Unknown error')
                    raise APIError(f"{description}", error_code)
                
                return data.get('result', {})
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {e}")
    
    async def get_me(self) -> User:
        result = await self._request('getMe')
        return User.from_dict(result)
    
    async def send_message(self, chat_id: Union[int, str], text: str, 
                          reply_to_message_id: Optional[int] = None,
                          reply_markup: Optional[Dict] = None,
                          parse_mode: Optional[str] = None,
                          disable_web_page_preview: bool = False,
                          disable_notification: bool = False) -> Message:
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode or self.parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification
        }
        
        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        if reply_markup:
            params['reply_markup'] = reply_markup
            
        result = await self._request('sendMessage', params)
        return Message.from_dict(result, bot=self)
    
    async def send_photo(self, chat_id: Union[int, str], photo: Union[str, bytes], 
                        caption: str = None, **kwargs):
        if isinstance(photo, str) and os.path.exists(photo):
            with open(photo, 'rb') as f:
                photo_data = f.read()
        else:
            photo_data = photo
            
        params = {'chat_id': chat_id}
        if caption:
            params['caption'] = caption
        if kwargs:
            params.update(kwargs)
            
        data = aiohttp.FormData()
        for key, value in params.items():
            data.add_field(key, str(value))
        data.add_field('photo', photo_data, filename='photo.jpg')
        
        async with self.session.post(f"{self.api_url}/sendPhoto", data=data) as resp:
            result = await resp.json()
            if not result.get('ok'):
                raise APIError(result.get('description', 'Photo send failed'))
            return Message.from_dict(result['result'], bot=self)
    
    async def send_document(self, chat_id: Union[int, str], document: Union[str, bytes],
                           caption: str = None, **kwargs):
        if isinstance(document, str) and os.path.exists(document):
            with open(document, 'rb') as f:
                doc_data = f.read()
            filename = os.path.basename(document)
        else:
            doc_data = document
            filename = 'document'
            
        params = {'chat_id': chat_id}
        if caption:
            params['caption'] = caption
        if kwargs:
            params.update(kwargs)
            
        data = aiohttp.FormData()
        for key, value in params.items():
            data.add_field(key, str(value))
        data.add_field('document', doc_data, filename=filename)
        
        async with self.session.post(f"{self.api_url}/sendDocument", data=data) as resp:
            result = await resp.json()
            if not result.get('ok'):
                raise APIError(result.get('description', 'Document send failed'))
            return Message.from_dict(result['result'], bot=self)
    
    async def send_video(self, chat_id: Union[int, str], video: Union[str, bytes], **kwargs):
        return await self._send_media('sendVideo', chat_id, 'video', video, **kwargs)
    
    async def send_audio(self, chat_id: Union[int, str], audio: Union[str, bytes], **kwargs):
        return await self._send_media('sendAudio', chat_id, 'audio', audio, **kwargs)
    
    async def send_voice(self, chat_id: Union[int, str], voice: Union[str, bytes], **kwargs):
        return await self._send_media('sendVoice', chat_id, 'voice', voice, **kwargs)
    
    async def send_sticker(self, chat_id: Union[int, str], sticker: Union[str, bytes], **kwargs):
        return await self._send_media('sendSticker', chat_id, 'sticker', sticker, **kwargs)
    
    async def _send_media(self, method: str, chat_id: Union[int, str], 
                         media_type: str, media: Union[str, bytes], **kwargs):
        if isinstance(media, str) and os.path.exists(media):
            with open(media, 'rb') as f:
                media_data = f.read()
            filename = os.path.basename(media)
        else:
            media_data = media
            filename = f'{media_type}.bin'
            
        params = {'chat_id': chat_id}
        params.update(kwargs)
            
        data = aiohttp.FormData()
        for key, value in params.items():
            data.add_field(key, str(value))
        data.add_field(media_type, media_data, filename=filename)
        
        async with self.session.post(f"{self.api_url}/{method}", data=data) as resp:
            result = await resp.json()
            if not result.get('ok'):
                raise APIError(result.get('description', f'{method} failed'))
            return Message.from_dict(result['result'], bot=self)
    
    async def send_action(self, chat_id: Union[int, str], action: str = 'typing'):
        actions = ['typing', 'upload_photo', 'record_video', 'upload_video',
                  'record_voice', 'upload_voice', 'upload_document', 'find_location',
                  'record_video_note', 'upload_video_note']
        if action not in actions:
            action = 'typing'
        
        await self._request('sendChatAction', {
            'chat_id': chat_id,
            'action': action
        })
    
    async def send_typing(self, chat_id: Union[int, str]):
        await self.send_action(chat_id, 'typing')
    
    async def edit_message(self, chat_id: Union[int, str], message_id: int, text: str,
                          reply_markup: Optional[Dict] = None):
        """Редактировать сообщение"""
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': self.parse_mode
        }
        if reply_markup:
            params['reply_markup'] = reply_markup
        
        return await self._request('editMessageText', params)
    
    async def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: str,
                               reply_markup: Optional[Dict] = None):
        """Редактировать текст сообщения"""
        return await self.edit_message(chat_id, message_id, text, reply_markup)
    
    async def delete_message(self, chat_id: Union[int, str], message_id: int):
        """Удалить сообщение"""
        return await self._request('deleteMessage', {
            'chat_id': chat_id,
            'message_id': message_id
        })
    
    async def forward_message(self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
                             message_id: int):
        """Переслать сообщение"""
        return await self._request('forwardMessage', {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        })
    
    async def get_chat_member(self, chat_id: Union[int, str], user_id: int):
        """Получить информацию о участнике чата"""
        return await self._request('getChatMember', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def ban_user(self, chat_id: Union[int, str], user_id: int, 
                      until_date: Optional[int] = None):
        """Забанить пользователя"""
        params = {'chat_id': chat_id, 'user_id': user_id}
        if until_date:
            params['until_date'] = until_date
        return await self._request('banChatMember', params)
    
    async def unban_user(self, chat_id: Union[int, str], user_id: int):
        return await self._request('unbanChatMember', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def restrict_user(self, chat_id: Union[int, str], user_id: int, 
                           permissions: Dict, until_date: Optional[int] = None):
        params = {
            'chat_id': chat_id,
            'user_id': user_id,
            'permissions': permissions
        }
        if until_date:
            params['until_date'] = until_date
        return await self._request('restrictChatMember', params)
    
    async def promote_user(self, chat_id: Union[int, str], user_id: int, **permissions):
        params = {'chat_id': chat_id, 'user_id': user_id}
        params.update(permissions)
        return await self._request('promoteChatMember', params)
    
    async def set_chat_title(self, chat_id: Union[int, str], title: str):
        return await self._request('setChatTitle', {
            'chat_id': chat_id,
            'title': title
        })
    
    async def set_chat_description(self, chat_id: Union[int, str], description: str):
        return await self._request('setChatDescription', {
            'chat_id': chat_id,
            'description': description
        })
    
    async def pin_message(self, chat_id: Union[int, str], message_id: int, 
                         disable_notification: bool = False):
        return await self._request('pinChatMessage', {
            'chat_id': chat_id,
            'message_id': message_id,
            'disable_notification': disable_notification
        })
    
    async def unpin_message(self, chat_id: Union[int, str], message_id: Optional[int] = None):
        params = {'chat_id': chat_id}
        if message_id:
            params['message_id'] = message_id
        return await self._request('unpinChatMessage', params)
    
    async def get_chat(self, chat_id: Union[int, str]):
        return await self._request('getChat', {'chat_id': chat_id})
    
    async def get_chat_admins(self, chat_id: Union[int, str]):
        return await self._request('getChatAdministrators', {'chat_id': chat_id})
    
    async def get_member_count(self, chat_id: Union[int, str]):
        return await self._request('getChatMemberCount', {'chat_id': chat_id})
    
    async def leave_chat(self, chat_id: Union[int, str]):
        return await self._request('leaveChat', {'chat_id': chat_id})
    
    async def export_invite_link(self, chat_id: Union[int, str]):
        return await self._request('exportChatInviteLink', {'chat_id': chat_id})
    
    async def create_invite_link(self, chat_id: Union[int, str], expire_date: Optional[int] = None,
                                member_limit: Optional[int] = None, name: Optional[str] = None):
        params = {'chat_id': chat_id}
        if expire_date:
            params['expire_date'] = expire_date
        if member_limit:
            params['member_limit'] = member_limit
        if name:
            params['name'] = name
        return await self._request('createChatInviteLink', params)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = None,
                                   show_alert: bool = False, url: str = None):
        params = {'callback_query_id': callback_query_id}
        if text:
            params['text'] = text
        if show_alert:
            params['show_alert'] = show_alert
        if url:
            params['url'] = url
        return await self._request('answerCallbackQuery', params)
    
    async def get_file(self, file_id: str):
        return await self._request('getFile', {'file_id': file_id})
    
    async def download_file(self, file_path: str) -> bytes:
        url = f"{self.file_url}/{file_path}"
        async with self.session.get(url) as resp:
            return await resp.read()
    
    async def set_webhook(self, url: str, certificate: str = None, **kwargs):
        params = {'url': url}
        if certificate:
            params['certificate'] = certificate
        params.update(kwargs)
        return await self._request('setWebhook', params)
    
    async def delete_webhook(self, drop_pending_updates: bool = False):
        return await self._request('deleteWebhook', {
            'drop_pending_updates': drop_pending_updates
        })
    
    async def get_updates(self, offset: Optional[int] = None, limit: int = 100, timeout: int = 10):
        params = {'limit': limit, 'timeout': timeout}
        if offset:
            params['offset'] = offset
            
        result = await self._request('getUpdates', params)
        return [Update.from_dict(update_data, bot=self) for update_data in result]
    
    # УНИКАЛЬНЫЕ ФИЧИ FORGRAM
    
    def smart_reply(self, triggers: List[str], response: str, exact_match: bool = False):
        """Умные автоответы - уникальная фича Forgram!"""
        def decorator(func):
            self._auto_reply_rules.append({
                'triggers': triggers,
                'response': response,
                'exact_match': exact_match,
                'handler': func
            })
            return func
        return decorator
    
    def rate_limit(self, calls_per_minute: int = 20):
        """Автоматический rate limiting - защита от спама"""
        def decorator(func):
            func._rate_limit = calls_per_minute
            return func
        return decorator
    
    def schedule(self, interval: int, unit: str = "seconds"):
        """Планировщик задач встроенный в бота!"""
        def decorator(func):
            self._scheduled_tasks.append({
                'func': func,
                'interval': interval,
                'unit': unit,
                'last_run': 0
            })
            return func
        return decorator
    
    async def send_with_typing(self, chat_id: Union[int, str], text: str, 
                              typing_time: float = 1.0, **kwargs):
        """Отправка с имитацией печатания"""
        await self.send_typing(chat_id)
        await asyncio.sleep(typing_time)
        return await self.send_message(chat_id, text, **kwargs)
    
    async def bulk_send(self, chat_ids: List[Union[int, str]], text: str, 
                       delay: float = 0.1):
        """Массовая рассылка с задержкой"""
        results = []
        for chat_id in chat_ids:
            try:
                result = await self.send_message(chat_id, text)
                results.append(result)
                if delay > 0:
                    await asyncio.sleep(delay)
            except Exception as e:
                self.logger.error(f"Failed to send to {chat_id}: {e}")
                results.append(None)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Встроенная статистика бота"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            'uptime': str(uptime),
            'messages_processed': self.stats['messages_processed'],
            'errors_count': self.stats['errors_count'],
            'unique_users': len(self.stats['users_count']),
            'handlers_count': len(self._handlers),
            'middleware_count': len(self._middleware)
        }
    
    async def cache_message(self, key: str, message: Message, ttl: int = 3600):
        """Кэширование сообщений"""
        expire_time = time.time() + ttl
        self._message_cache[key] = {
            'message': message,
            'expire_time': expire_time
        }
    
    async def get_cached_message(self, key: str) -> Optional[Message]:
        """Получить сообщение из кэша"""
        if key in self._message_cache:
            cached = self._message_cache[key]
            if time.time() < cached['expire_time']:
                return cached['message']
            else:
                del self._message_cache[key]
        return None
    
    def message_handler(self, commands: Optional[List[str]] = None,
                       content_types: Optional[List[str]] = None,
                       state: Optional[str] = None,
                       func: Optional[Callable] = None,
                       admin_only: bool = False,
                       private_only: bool = False,
                       group_only: bool = False,
                       regexp: Optional[str] = None):
        """Улучшенный message_handler с фильтрами"""
        def decorator(handler_func):
            self._handlers.append({
                'handler': handler_func,
                'commands': commands or [],
                'content_types': content_types or ['text'],
                'state': state,
                'func': func,
                'admin_only': admin_only,
                'private_only': private_only,
                'group_only': group_only,
                'regexp': re.compile(regexp) if regexp else None,
                'rate_limit': getattr(handler_func, '_rate_limit', None)
            })
            return handler_func
        return decorator
    
    def callback_query_handler(self, func: Optional[Callable] = None):
        def decorator(handler_func):
            self._callback_handlers.append({
                'handler': handler_func,
                'func': func
            })
            return handler_func
        return decorator
    
    def middleware_handler(self, middleware_func: Callable):
        self._middleware.append(middleware_func)
        return middleware_func
    
    async def _process_update(self, update: Update):
        try:
            for middleware_func in self._middleware:
                result = await middleware_func(update)
                if result is False:
                    return
            
            if update.message:
                await self._process_message(update.message)
            
            if update.callback_query:
                await self._process_callback(update.callback_query)
                
        except Exception as e:
            self.logger.error(f"Error processing update: {e}")
    
    async def _process_message(self, message: Message):
        user_id = message.from_user.id if message.from_user else None
        current_state = self.state.get_state(user_id) if user_id else None
        
        # Статистика
        self.stats['messages_processed'] += 1
        if user_id:
            self.stats['users_count'].add(user_id)
        
        # Проверяем автоответы
        if await self._check_auto_replies(message):
            return
        
        for handler_info in self._handlers:
            if await self._check_handler(message, handler_info, current_state):
                try:
                    # Rate limiting
                    if handler_info.get('rate_limit'):
                        if not await self._check_rate_limit(user_id, handler_info['rate_limit']):
                            continue
                    
                    await handler_info['handler'](message)
                    break
                except Exception as e:
                    self.stats['errors_count'] += 1
                    self.logger.error(f"Handler error: {e}")
    
    async def _check_auto_replies(self, message: Message) -> bool:
        """Проверка автоответов"""
        if not message.text:
            return False
            
        for rule in self._auto_reply_rules:
            text_lower = message.text.lower()
            
            for trigger in rule['triggers']:
                if rule['exact_match']:
                    if text_lower == trigger.lower():
                        await message.reply(rule['response'])
                        return True
                else:
                    if trigger.lower() in text_lower:
                        await message.reply(rule['response'])
                        return True
        return False
    
    async def _check_rate_limit(self, user_id: Optional[int], limit: int) -> bool:
        """Rate limiting"""
        if not user_id:
            return True
            
        now = time.time()
        key = f"rate_{user_id}"
        
        if key not in self._rate_limits:
            self._rate_limits[key] = []
        
        # Убираем старые записи
        self._rate_limits[key] = [
            timestamp for timestamp in self._rate_limits[key]
            if now - timestamp < 60  # последняя минута
        ]
        
        if len(self._rate_limits[key]) >= limit:
            return False
        
        self._rate_limits[key].append(now)
        return True
    
    async def _check_handler(self, message: Message, handler_info: Dict, current_state: Optional[str]) -> bool:
        # Проверка состояния
        if handler_info.get('state') and handler_info['state'] != current_state:
            return False
        
        # Проверка типа чата
        if handler_info.get('private_only') and message.chat.type != 'private':
            return False
        if handler_info.get('group_only') and message.chat.type == 'private':
            return False
        
        # Проверка админки
        if handler_info.get('admin_only'):
            if not await self._is_admin(message.from_user.id, message.chat.id):
                return False
        
        # Проверка регулярки
        if handler_info.get('regexp') and message.text:
            if not handler_info['regexp'].search(message.text):
                return False
        
        # Проверка команд
        if handler_info['commands'] and message.text:
            if message.text.startswith('/'):
                command = message.text.split()[0][1:]
                if command in handler_info['commands']:
                    return True
        
        # Проверка типа контента
        if 'text' in handler_info['content_types'] and message.text and not handler_info['commands']:
            return True
        
        # Пользовательская функция
        if handler_info['func']:
            return await handler_info['func'](message)
        
        return False
    
    async def _is_admin(self, user_id: Optional[int], chat_id: int) -> bool:
        """Проверка на админа"""
        if not user_id or chat_id > 0:  # В приватных чатах все админы
            return True
        
        try:
            member = await self.get_chat_member(chat_id, user_id)
            return member['status'] in ['creator', 'administrator']
        except:
            return False
    
    async def _process_callback(self, callback_query):
        for handler_info in self._callback_handlers:
            if not handler_info['func'] or await handler_info['func'](callback_query):
                try:
                    await handler_info['handler'](callback_query)
                    break
                except Exception as e:
                    self.logger.error(f"Callback handler error: {e}")
    
    async def start_polling(self):
        self.logger.info("Bot started")
        self._running = True
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            me = await self.get_me()
            self.logger.info(f"Logged in as @{me.username}")
            
            # Запускаем планировщик задач
            asyncio.create_task(self._run_scheduler())
            
            while self._running:
                try:
                    updates = await self.get_updates(offset=self._offset)
                    
                    for update in updates:
                        self._offset = max(self._offset, update.update_id + 1)
                        asyncio.create_task(self._process_update(update))
                    
                    # Очищаем кэш от устаревших записей
                    await self._cleanup_cache()
                        
                except Exception as e:
                    self.logger.error(f"Polling error: {e}")
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("Bot stopped")
        finally:
            await self.stop()
    
    async def _run_scheduler(self):
        """Планировщик задач - уникальная фича!"""
        while self._running:
            current_time = time.time()
            
            for task in self._scheduled_tasks:
                interval_seconds = task['interval']
                if task['unit'] == 'minutes':
                    interval_seconds *= 60
                elif task['unit'] == 'hours':
                    interval_seconds *= 3600
                
                if current_time - task['last_run'] >= interval_seconds:
                    try:
                        await task['func']()
                        task['last_run'] = current_time
                    except Exception as e:
                        self.logger.error(f"Scheduler error: {e}")
            
            await asyncio.sleep(1)
    
    async def _cleanup_cache(self):
        """Очистка устаревшего кэша"""
        current_time = time.time()
        expired_keys = []
        
        for key, cached in self._message_cache.items():
            if current_time >= cached['expire_time']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._message_cache[key]
    
    async def stop(self):
        self._running = False
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Bot stopped")
    
    def run(self):
        """Запуск бота с красивыми логами"""
        print("🚀 Starting Forgram Bot...")
        print(f"📊 Features: Smart replies, Rate limiting, Scheduler, Cache")
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
    
    # ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
    
    def command(self, name: str, **kwargs):
        """Алиас для message_handler с командами"""
        return self.message_handler(commands=[name], **kwargs)
    
    def text(self, **kwargs):
        """Алиас для обработки текста"""
        return self.message_handler(content_types=['text'], **kwargs)
    
    def private(self, **kwargs):
        """Только приватные чаты"""
        return self.message_handler(private_only=True, **kwargs)
    
    def group(self, **kwargs):
        """Только группы"""
        return self.message_handler(group_only=True, **kwargs)
    
    def admin(self, **kwargs):
        return self.message_handler(admin_only=True, **kwargs)
    
    def _extract_entity_text(self, message: 'Message', entity: Dict) -> str:
        text = message.text or message.caption or ""
        start = entity.get('offset', 0)
        length = entity.get('length', 0)
        return text[start:start + length]
    
    async def answer_inline_query(self, inline_query_id: str, results: List[Dict],
                                 cache_time: int = 300, is_personal: bool = False,
                                 next_offset: str = None, switch_pm_text: str = None,
                                 switch_pm_parameter: str = None):
        params = {
            'inline_query_id': inline_query_id,
            'results': json.dumps(results),
            'cache_time': cache_time,
            'is_personal': is_personal
        }
        if next_offset:
            params['next_offset'] = next_offset
        if switch_pm_text:
            params['switch_pm_text'] = switch_pm_text
        if switch_pm_parameter:
            params['switch_pm_parameter'] = switch_pm_parameter
        return await self._request('answerInlineQuery', params)
    
    async def send_invoice(self, chat_id: Union[int, str], title: str, description: str,
                          payload: str, provider_token: str, currency: str,
                          prices: List[Dict], **kwargs):
        params = {
            'chat_id': chat_id,
            'title': title,
            'description': description,
            'payload': payload,
            'provider_token': provider_token,
            'currency': currency,
            'prices': json.dumps(prices)
        }
        params.update(kwargs)
        return await self._request('sendInvoice', params)
    
    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool,
                                       error_message: str = None):
        params = {'pre_checkout_query_id': pre_checkout_query_id, 'ok': ok}
        if error_message:
            params['error_message'] = error_message
        return await self._request('answerPreCheckoutQuery', params)
    
    async def send_game(self, chat_id: Union[int, str], game_short_name: str,
                       reply_to_message_id: int = None, reply_markup=None):
        params = {'chat_id': chat_id, 'game_short_name': game_short_name}
        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return await self._request('sendGame', params)
    
    async def set_game_score(self, user_id: int, score: int, chat_id: Union[int, str] = None,
                            message_id: int = None, inline_message_id: str = None,
                            force: bool = False, disable_edit_message: bool = False):
        params = {'user_id': user_id, 'score': score}
        if chat_id:
            params['chat_id'] = chat_id
        if message_id:
            params['message_id'] = message_id
        if inline_message_id:
            params['inline_message_id'] = inline_message_id
        if force:
            params['force'] = force
        if disable_edit_message:
            params['disable_edit_message'] = disable_edit_message
        return await self._request('setGameScore', params)
    
    def middleware(self, func):
        self.middlewares.append(func)
        return func
    
    async def _apply_middlewares(self, update: Dict) -> bool:
        for middleware in self.middlewares:
            try:
                result = await middleware(update, self)
                if result is False:
                    return False
            except Exception as e:
                print(f"Middleware error: {e}")
        return True
    
    def create_deep_link(self, payload: str) -> str:
        return f"https://t.me/{self.username}?start={payload}"
    
    async def get_my_commands(self):
        return await self._request('getMyCommands')
    
    async def set_my_commands(self, commands: List[Dict]):
        return await self._request('setMyCommands', {
            'commands': json.dumps(commands)
        })
    
    async def delete_my_commands(self):
        return await self._request('deleteMyCommands')
    
    async def get_updates_long_poll(self, timeout: int = 60):
        try:
            response = await self._request('getUpdates', {
                'offset': self.last_update_id + 1,
                'timeout': timeout,
                'allowed_updates': ['message', 'callback_query', 'inline_query']
            })
            
            if response and isinstance(response, list):
                for update in response:
                    self.last_update_id = max(self.last_update_id, update.get('update_id', 0))
                    yield update
        except Exception as e:
            print(f"Long poll error: {e}")
