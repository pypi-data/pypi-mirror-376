import json
import asyncio
import aiohttp
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union, List, Callable
from .models import Message, User, Chat, Update, CallbackQuery
from .storage import BaseStorage, MemoryStorage
from .exceptions import APIError, BotError


class Bot:
    def __init__(self, token: str, parse_mode: str = 'HTML', storage: BaseStorage = None):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.file_url = f"https://api.telegram.org/file/bot{token}"
        self.parse_mode = parse_mode
        self.session = None
        self.storage = storage or MemoryStorage()
        self.logger = None
        self._handlers = {}
        self._middleware = []
        self.last_update_id = 0
        self._message_cache = {}
        self.username = None
        
        self.stats = {
            'start_time': datetime.now(),
            'messages_processed': 0,
            'errors_count': 0,
            'users_count': set()
        }
        
        self.auto_replies = {}
        self.rate_limits = {}
        self.scheduled_tasks = []
        self.middlewares = []
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        bot_info = await self.get_me()
        if bot_info:
            self.username = bot_info.get('username', '')
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, params: Dict[str, Any] = None) -> Any:
        if not self.session:
            await self.initialize()
        
        url = f"{self.api_url}/{method}"
        try:
            async with self.session.post(url, json=params or {}) as response:
                result = await response.json()
                if not result.get('ok'):
                    raise APIError(result.get('description', 'Unknown API error'))
                return result.get('result')
        except Exception as e:
            self.stats['errors_count'] += 1
            if self.logger:
                self.logger.error(f"API request failed: {e}")
            raise APIError(str(e))
    
    async def get_me(self):
        return await self._request('getMe')
    
    async def send_message(self, chat_id: Union[int, str], text: str, 
                          reply_markup: Optional[Dict] = None, 
                          reply_to_message_id: Optional[int] = None,
                          parse_mode: Optional[str] = None,
                          disable_web_page_preview: bool = False,
                          disable_notification: bool = False):
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode or self.parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification
        }
        if reply_markup:
            params['reply_markup'] = reply_markup
        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        
        result = await self._request('sendMessage', params)
        return Message.from_dict(result, bot=self)
    
    async def send_photo(self, chat_id: Union[int, str], photo: Union[str, bytes],
                        caption: str = None, **kwargs):
        if isinstance(photo, str):
            if photo.startswith('http'):
                params = {'chat_id': chat_id, 'photo': photo}
                if caption:
                    params['caption'] = caption
                if kwargs:
                    params.update(kwargs)
                result = await self._request('sendPhoto', params)
                return Message.from_dict(result, bot=self)
            elif os.path.exists(photo):
                with open(photo, 'rb') as f:
                    photo_data = f.read()
            else:
                photo_data = photo.encode() if isinstance(photo, str) else photo
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
    
    async def send_animation(self, chat_id: Union[int, str], animation: Union[str, bytes], **kwargs):
        return await self._send_media('sendAnimation', chat_id, 'animation', animation, **kwargs)
    
    async def send_location(self, chat_id: Union[int, str], latitude: float, longitude: float,
                           reply_markup: Optional[Dict] = None, **kwargs):
        params = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude
        }
        if reply_markup:
            params['reply_markup'] = reply_markup
        if kwargs:
            params.update(kwargs)
        
        result = await self._request('sendLocation', params)
        return Message.from_dict(result, bot=self)
    
    async def send_contact(self, chat_id: Union[int, str], phone_number: str, first_name: str,
                          last_name: str = None, reply_markup: Optional[Dict] = None, **kwargs):
        params = {
            'chat_id': chat_id,
            'phone_number': phone_number,
            'first_name': first_name
        }
        if last_name:
            params['last_name'] = last_name
        if reply_markup:
            params['reply_markup'] = reply_markup
        if kwargs:
            params.update(kwargs)
        
        result = await self._request('sendContact', params)
        return Message.from_dict(result, bot=self)
    
    async def send_dice(self, chat_id: Union[int, str], emoji: str = "🎲", **kwargs):
        params = {'chat_id': chat_id, 'emoji': emoji}
        if kwargs:
            params.update(kwargs)
        result = await self._request('sendDice', params)
        return Message.from_dict(result, bot=self)
    
    async def send_chat_action(self, chat_id: Union[int, str], action: str):
        return await self._request('sendChatAction', {
            'chat_id': chat_id,
            'action': action
        })
    
    async def _send_media(self, method: str, chat_id: Union[int, str], 
                         media_type: str, media: Union[str, bytes], **kwargs):
        if isinstance(media, str) and media.startswith('http'):
            params = {'chat_id': chat_id, media_type: media}
            params.update(kwargs)
            result = await self._request(method, params)
            return Message.from_dict(result, bot=self)
        
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
    
    async def set_chat_menu_button(self, chat_id: Union[int, str] = None, menu_button: Dict = None):
        params = {}
        if chat_id:
            params['chat_id'] = chat_id
        if menu_button:
            params['menu_button'] = menu_button
        return await self._request('setChatMenuButton', params)
    
    async def get_chat_menu_button(self, chat_id: Union[int, str] = None):
        params = {}
        if chat_id:
            params['chat_id'] = chat_id
        return await self._request('getChatMenuButton', params)
    
    async def set_my_default_administrator_rights(self, rights: Dict = None, for_channels: bool = None):
        params = {}
        if rights:
            params['rights'] = rights
        if for_channels is not None:
            params['for_channels'] = for_channels
        return await self._request('setMyDefaultAdministratorRights', params)
    
    async def get_my_default_administrator_rights(self, for_channels: bool = None):
        params = {}
        if for_channels is not None:
            params['for_channels'] = for_channels
        return await self._request('getMyDefaultAdministratorRights', params)
    
    async def edit_message(self, chat_id: Union[int, str], message_id: int, text: str,
                          reply_markup: Optional[Dict] = None):
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
        return await self.edit_message(chat_id, message_id, text, reply_markup)
    
    async def delete_message(self, chat_id: Union[int, str], message_id: int):
        return await self._request('deleteMessage', {
            'chat_id': chat_id,
            'message_id': message_id
        })
    
    async def forward_message(self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
                             message_id: int):
        return await self._request('forwardMessage', {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        })
    
    async def get_chat_member(self, chat_id: Union[int, str], user_id: int):
        return await self._request('getChatMember', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def ban_user(self, chat_id: Union[int, str], user_id: int, 
                      until_date: Optional[int] = None):
        params = {'chat_id': chat_id, 'user_id': user_id}
        if until_date:
            params['until_date'] = until_date
        return await self._request('banChatMember', params)
    
    async def unban_user(self, chat_id: Union[int, str], user_id: int):
        return await self._request('unbanChatMember', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def restrict_chat_member(self, chat_id: Union[int, str], user_id: int, permissions: Dict,
                                  until_date: Optional[int] = None):
        params = {
            'chat_id': chat_id,
            'user_id': user_id,
            'permissions': json.dumps(permissions)
        }
        if until_date:
            params['until_date'] = until_date
        return await self._request('restrictChatMember', params)
    
    async def promote_chat_member(self, chat_id: Union[int, str], user_id: int, **permissions):
        params = {'chat_id': chat_id, 'user_id': user_id}
        params.update(permissions)
        return await self._request('promoteChatMember', params)
    
    async def set_chat_administrator_custom_title(self, chat_id: Union[int, str], 
                                                 user_id: int, custom_title: str):
        return await self._request('setChatAdministratorCustomTitle', {
            'chat_id': chat_id,
            'user_id': user_id,
            'custom_title': custom_title
        })
    
    async def ban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: int):
        return await self._request('banChatSenderChat', {
            'chat_id': chat_id,
            'sender_chat_id': sender_chat_id
        })
    
    async def unban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: int):
        return await self._request('unbanChatSenderChat', {
            'chat_id': chat_id,
            'sender_chat_id': sender_chat_id
        })
    
    async def set_chat_permissions(self, chat_id: Union[int, str], permissions: Dict):
        return await self._request('setChatPermissions', {
            'chat_id': chat_id,
            'permissions': json.dumps(permissions)
        })
    
    async def get_chat(self, chat_id: Union[int, str]):
        return await self._request('getChat', {'chat_id': chat_id})
    
    async def get_chat_administrators(self, chat_id: Union[int, str]):
        return await self._request('getChatAdministrators', {'chat_id': chat_id})
    
    async def get_chat_member_count(self, chat_id: Union[int, str]):
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
        return await self._request('getUpdates', params)
    
    def add_auto_reply(self, trigger: str, response: str):
        self.auto_replies[trigger.lower()] = response
    
    def check_auto_reply(self, text: str) -> Optional[str]:
        if not text:
            return None
        text_lower = text.lower()
        for trigger, response in self.auto_replies.items():
            if trigger in text_lower:
                return response
        return None
    
    def rate_limit(self, chat_id: Union[int, str], limit: int = 1, window: int = 60) -> bool:
        now = time.time()
        key = str(chat_id)
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        self.rate_limits[key] = [t for t in self.rate_limits[key] if now - t < window]
        
        if len(self.rate_limits[key]) >= limit:
            return False
        
        self.rate_limits[key].append(now)
        return True
    
    def schedule_task(self, func: Callable, delay: int, *args, **kwargs):
        task = asyncio.create_task(self._delayed_task(func, delay, *args, **kwargs))
        self.scheduled_tasks.append(task)
        return task
    
    async def _delayed_task(self, func: Callable, delay: int, *args, **kwargs):
        await asyncio.sleep(delay)
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    
    async def send_typing_message(self, chat_id: Union[int, str], text: str, delay: float = 1.0):
        await self.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(delay)
        return await self.send_message(chat_id, text)
    
    async def broadcast_message(self, chat_ids: List[Union[int, str]], text: str, delay: float = 0.1):
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
        expire_time = time.time() + ttl
        self._message_cache[key] = {
            'message': message,
            'expire_time': expire_time
        }
    
    async def get_cached_message(self, key: str) -> Optional[Message]:
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
        def decorator(handler_func):
            handler_config = {
                'function': handler_func,
                'commands': commands or [],
                'content_types': content_types or ['text'],
                'state': state,
                'func': func,
                'admin_only': admin_only,
                'private_only': private_only,
                'group_only': group_only,
                'regexp': regexp
            }
            
            handler_key = f"handler_{len(self._handlers)}"
            self._handlers[handler_key] = handler_config
            return handler_func
        return decorator
    
    def callback_query_handler(self, func: Optional[Callable] = None):
        def decorator(handler_func):
            self._handlers[f"callback_{len(self._handlers)}"] = {
                'function': handler_func,
                'type': 'callback_query',
                'func': func
            }
            return handler_func
        return decorator
    
    async def _process_update(self, update_data: Dict):
        try:
            update = Update.from_dict(update_data)
            self.stats['messages_processed'] += 1
            
            if update.message:
                self.stats['users_count'].add(update.message.from_user.id)
                await self._handle_message(update.message)
            elif update.callback_query:
                await self._handle_callback_query(update.callback_query)
        except Exception as e:
            self.stats['errors_count'] += 1
            if self.logger:
                self.logger.error(f"Update processing failed: {e}")
    
    async def _handle_message(self, message: Message):
        if not self.rate_limit(message.chat.id, 10, 60):
            await self.send_message(message.chat.id, "Rate limit exceeded. Please slow down.")
            return
        
        auto_response = self.check_auto_reply(message.text)
        if auto_response:
            await self.send_message(message.chat.id, auto_response)
            return
        
        for handler_config in self._handlers.values():
            if await self._check_handler_match(message, handler_config):
                try:
                    if asyncio.iscoroutinefunction(handler_config['function']):
                        await handler_config['function'](message)
                    else:
                        handler_config['function'](message)
                    break
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Handler error: {e}")
    
    async def _handle_callback_query(self, callback_query: CallbackQuery):
        for handler_config in self._handlers.values():
            if handler_config.get('type') == 'callback_query':
                try:
                    if asyncio.iscoroutinefunction(handler_config['function']):
                        await handler_config['function'](callback_query)
                    else:
                        handler_config['function'](callback_query)
                    break
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Callback handler error: {e}")
    
    async def _check_handler_match(self, message: Message, handler_config: Dict) -> bool:
        if handler_config['private_only'] and not message.chat.is_private:
            return False
        if handler_config['group_only'] and message.chat.is_private:
            return False
        
        if handler_config['commands']:
            if message.is_command():
                command = message.get_command()
                return command in handler_config['commands']
            return False
        
        if handler_config.get('func'):
            return handler_config['func'](message)
        
        return True
    
    async def start_polling(self):
        print("Bot started successfully!")
        offset = 0
        
        while True:
            try:
                updates = await self.get_updates(offset=offset, timeout=30)
                
                if updates:
                    for update in updates:
                        offset = max(offset, update.get('update_id', 0) + 1)
                        asyncio.create_task(self._process_update(update))
                        
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
    
    def run(self):
        print("🚀 Starting Forgram Bot...")
        print(f"📊 Features: Auto replies, Rate limiting, Scheduler, Cache")
        try:
            asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
    
    def command(self, name: str, **kwargs):
        return self.message_handler(commands=[name], **kwargs)
    
    def text(self, **kwargs):
        return self.message_handler(content_types=['text'], **kwargs)
    
    def private(self, **kwargs):
        return self.message_handler(private_only=True, **kwargs)
    
    def group(self, **kwargs):
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
    
    # === STICKER METHODS (15 методов) ===
    async def create_new_sticker_set(self, user_id: int, name: str, title: str, 
                                    stickers: List[Dict], sticker_format: str, **kwargs):
        params = {
            'user_id': user_id,
            'name': name,
            'title': title,
            'stickers': json.dumps(stickers),
            'sticker_format': sticker_format
        }
        params.update(kwargs)
        return await self._request('createNewStickerSet', params)
    
    async def add_sticker_to_set(self, user_id: int, name: str, sticker: Dict):
        return await self._request('addStickerToSet', {
            'user_id': user_id,
            'name': name,
            'sticker': json.dumps(sticker)
        })
    
    async def set_sticker_position_in_set(self, sticker: str, position: int):
        return await self._request('setStickerPositionInSet', {
            'sticker': sticker,
            'position': position
        })
    
    async def delete_sticker_from_set(self, sticker: str):
        return await self._request('deleteStickerFromSet', {'sticker': sticker})
    
    async def set_sticker_emoji_list(self, sticker: str, emoji_list: List[str]):
        return await self._request('setStickerEmojiList', {
            'sticker': sticker,
            'emoji_list': json.dumps(emoji_list)
        })
    
    async def set_sticker_keywords(self, sticker: str, keywords: List[str]):
        return await self._request('setStickerKeywords', {
            'sticker': sticker,
            'keywords': json.dumps(keywords)
        })
    
    async def set_sticker_mask_position(self, sticker: str, mask_position: Dict):
        return await self._request('setStickerMaskPosition', {
            'sticker': sticker,
            'mask_position': json.dumps(mask_position)
        })
    
    async def set_sticker_set_title(self, name: str, title: str):
        return await self._request('setStickerSetTitle', {
            'name': name,
            'title': title
        })
    
    async def set_sticker_set_thumbnail(self, name: str, user_id: int, thumbnail=None):
        params = {'name': name, 'user_id': user_id}
        if thumbnail:
            params['thumbnail'] = thumbnail
        return await self._request('setStickerSetThumbnail', params)
    
    async def set_custom_emoji_sticker_set_thumbnail(self, name: str, custom_emoji_id: str = None):
        params = {'name': name}
        if custom_emoji_id:
            params['custom_emoji_id'] = custom_emoji_id
        return await self._request('setCustomEmojiStickerSetThumbnail', params)
    
    async def upload_sticker_file(self, user_id: int, sticker, sticker_format: str):
        return await self._request('uploadStickerFile', {
            'user_id': user_id,
            'sticker': sticker,
            'sticker_format': sticker_format
        })
    
    async def get_sticker_set(self, name: str):
        return await self._request('getStickerSet', {'name': name})
    
    async def get_custom_emoji_stickers(self, custom_emoji_ids: List[str]):
        return await self._request('getCustomEmojiStickers', {
            'custom_emoji_ids': json.dumps(custom_emoji_ids)
        })
    
    async def delete_sticker_set(self, name: str):
        return await self._request('deleteStickerSet', {'name': name})
    
    async def replace_sticker_in_set(self, user_id: int, name: str, old_sticker: str, sticker: Dict):
        return await self._request('replaceStickerInSet', {
            'user_id': user_id,
            'name': name,
            'old_sticker': old_sticker,
            'sticker': json.dumps(sticker)
        })
    
    # === INLINE METHODS (8 методов) ===
    async def answer_web_app_query(self, web_app_query_id: str, result: Dict):
        return await self._request('answerWebAppQuery', {
            'web_app_query_id': web_app_query_id,
            'result': json.dumps(result)
        })
    
    async def set_chat_photo(self, chat_id: Union[int, str], photo):
        return await self._request('setChatPhoto', {
            'chat_id': chat_id,
            'photo': photo
        })
    
    async def delete_chat_photo(self, chat_id: Union[int, str]):
        return await self._request('deleteChatPhoto', {'chat_id': chat_id})
    
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
    
    async def pin_chat_message(self, chat_id: Union[int, str], message_id: int, 
                              disable_notification: bool = False):
        return await self._request('pinChatMessage', {
            'chat_id': chat_id,
            'message_id': message_id,
            'disable_notification': disable_notification
        })
    
    async def unpin_chat_message(self, chat_id: Union[int, str], message_id: int = None):
        params = {'chat_id': chat_id}
        if message_id:
            params['message_id'] = message_id
        return await self._request('unpinChatMessage', params)
    
    async def unpin_all_chat_messages(self, chat_id: Union[int, str]):
        return await self._request('unpinAllChatMessages', {'chat_id': chat_id})
    
    # === FORUM METHODS (10 методов) ===
    async def get_forum_topic_icon_stickers(self):
        return await self._request('getForumTopicIconStickers')
    
    async def create_forum_topic(self, chat_id: Union[int, str], name: str, 
                                icon_color: int = None, icon_custom_emoji_id: str = None):
        params = {'chat_id': chat_id, 'name': name}
        if icon_color:
            params['icon_color'] = icon_color
        if icon_custom_emoji_id:
            params['icon_custom_emoji_id'] = icon_custom_emoji_id
        return await self._request('createForumTopic', params)
    
    async def edit_forum_topic(self, chat_id: Union[int, str], message_thread_id: int,
                              name: str = None, icon_custom_emoji_id: str = None):
        params = {'chat_id': chat_id, 'message_thread_id': message_thread_id}
        if name:
            params['name'] = name
        if icon_custom_emoji_id:
            params['icon_custom_emoji_id'] = icon_custom_emoji_id
        return await self._request('editForumTopic', params)
    
    async def close_forum_topic(self, chat_id: Union[int, str], message_thread_id: int):
        return await self._request('closeForumTopic', {
            'chat_id': chat_id,
            'message_thread_id': message_thread_id
        })
    
    async def reopen_forum_topic(self, chat_id: Union[int, str], message_thread_id: int):
        return await self._request('reopenForumTopic', {
            'chat_id': chat_id,
            'message_thread_id': message_thread_id
        })
    
    async def delete_forum_topic(self, chat_id: Union[int, str], message_thread_id: int):
        return await self._request('deleteForumTopic', {
            'chat_id': chat_id,
            'message_thread_id': message_thread_id
        })
    
    async def unpin_all_forum_topic_messages(self, chat_id: Union[int, str], message_thread_id: int):
        return await self._request('unpinAllForumTopicMessages', {
            'chat_id': chat_id,
            'message_thread_id': message_thread_id
        })
    
    async def edit_general_forum_topic(self, chat_id: Union[int, str], name: str):
        return await self._request('editGeneralForumTopic', {
            'chat_id': chat_id,
            'name': name
        })
    
    async def close_general_forum_topic(self, chat_id: Union[int, str]):
        return await self._request('closeGeneralForumTopic', {'chat_id': chat_id})
    
    async def reopen_general_forum_topic(self, chat_id: Union[int, str]):
        return await self._request('reopenGeneralForumTopic', {'chat_id': chat_id})
    
    async def hide_general_forum_topic(self, chat_id: Union[int, str]):
        return await self._request('hideGeneralForumTopic', {'chat_id': chat_id})
    
    async def unhide_general_forum_topic(self, chat_id: Union[int, str]):
        return await self._request('unhideGeneralForumTopic', {'chat_id': chat_id})
    
    # === ADVANCED MESSAGE METHODS (12 методов) ===
    async def copy_message(self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
                          message_id: int, **kwargs):
        params = {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        }
        params.update(kwargs)
        return await self._request('copyMessage', params)
    
    async def copy_messages(self, chat_id: Union[int, str], from_chat_id: Union[int, str],
                           message_ids: List[int], **kwargs):
        params = {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_ids': json.dumps(message_ids)
        }
        params.update(kwargs)
        return await self._request('copyMessages', params)
    
    async def forward_messages(self, chat_id: Union[int, str], from_chat_id: Union[int, str],
                              message_ids: List[int], **kwargs):
        params = {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_ids': json.dumps(message_ids)
        }
        params.update(kwargs)
        return await self._request('forwardMessages', params)
    
    async def delete_messages(self, chat_id: Union[int, str], message_ids: List[int]):
        return await self._request('deleteMessages', {
            'chat_id': chat_id,
            'message_ids': json.dumps(message_ids)
        })
    
    async def edit_message_media(self, chat_id: Union[int, str], message_id: int, 
                                media: Dict, reply_markup: Dict = None):
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'media': json.dumps(media)
        }
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return await self._request('editMessageMedia', params)
    
    async def edit_message_caption(self, chat_id: Union[int, str], message_id: int,
                                  caption: str = None, reply_markup: Dict = None, **kwargs):
        params = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        if caption:
            params['caption'] = caption
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        params.update(kwargs)
        return await self._request('editMessageCaption', params)
    
    async def edit_message_reply_markup(self, chat_id: Union[int, str], message_id: int,
                                       reply_markup: Dict = None):
        params = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return await self._request('editMessageReplyMarkup', params)
    
    async def stop_poll(self, chat_id: Union[int, str], message_id: int, reply_markup: Dict = None):
        params = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return await self._request('stopPoll', params)
    
    async def send_poll(self, chat_id: Union[int, str], question: str, options: List[str], **kwargs):
        params = {
            'chat_id': chat_id,
            'question': question,
            'options': json.dumps(options)
        }
        params.update(kwargs)
        return await self._request('sendPoll', params)
    
    async def send_venue(self, chat_id: Union[int, str], latitude: float, longitude: float,
                        title: str, address: str, **kwargs):
        params = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude,
            'title': title,
            'address': address
        }
        params.update(kwargs)
        return await self._request('sendVenue', params)
    
    async def edit_message_live_location(self, chat_id: Union[int, str], message_id: int,
                                        latitude: float, longitude: float, **kwargs):
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'latitude': latitude,
            'longitude': longitude
        }
        params.update(kwargs)
        return await self._request('editMessageLiveLocation', params)
    
    async def stop_message_live_location(self, chat_id: Union[int, str], message_id: int,
                                        reply_markup: Dict = None):
        params = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return await self._request('stopMessageLiveLocation', params)
    
    # === USER PROFILE METHODS (5 методов) ===
    async def get_user_profile_photos(self, user_id: int, offset: int = None, limit: int = None):
        params = {'user_id': user_id}
        if offset:
            params['offset'] = offset
        if limit:
            params['limit'] = limit
        return await self._request('getUserProfilePhotos', params)
    
    async def get_user_chat_boosts(self, chat_id: Union[int, str], user_id: int):
        return await self._request('getUserChatBoosts', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def get_business_connection(self, business_connection_id: str):
        return await self._request('getBusinessConnection', {
            'business_connection_id': business_connection_id
        })
    
    async def set_my_description(self, description: str = None, language_code: str = None):
        params = {}
        if description:
            params['description'] = description
        if language_code:
            params['language_code'] = language_code
        return await self._request('setMyDescription', params)
    
    async def get_my_description(self, language_code: str = None):
        params = {}
        if language_code:
            params['language_code'] = language_code
        return await self._request('getMyDescription', params)
    
    # === CHAT INVITE LINK METHODS (8 методов) ===
    async def edit_chat_invite_link(self, chat_id: Union[int, str], invite_link: str, **kwargs):
        params = {
            'chat_id': chat_id,
            'invite_link': invite_link
        }
        params.update(kwargs)
        return await self._request('editChatInviteLink', params)
    
    async def revoke_chat_invite_link(self, chat_id: Union[int, str], invite_link: str):
        return await self._request('revokeChatInviteLink', {
            'chat_id': chat_id,
            'invite_link': invite_link
        })
    
    async def approve_chat_join_request(self, chat_id: Union[int, str], user_id: int):
        return await self._request('approveChatJoinRequest', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def decline_chat_join_request(self, chat_id: Union[int, str], user_id: int):
        return await self._request('declineChatJoinRequest', {
            'chat_id': chat_id,
            'user_id': user_id
        })
    
    async def get_chat_invite_link(self, chat_id: Union[int, str], invite_link: str):
        return await self._request('getChatInviteLink', {
            'chat_id': chat_id,
            'invite_link': invite_link
        })
    
    async def create_chat_subscription_invite_link(self, chat_id: Union[int, str], 
                                                  subscription_period: int, subscription_price: int, **kwargs):
        params = {
            'chat_id': chat_id,
            'subscription_period': subscription_period,
            'subscription_price': subscription_price
        }
        params.update(kwargs)
        return await self._request('createChatSubscriptionInviteLink', params)
    
    async def edit_chat_subscription_invite_link(self, chat_id: Union[int, str], invite_link: str, **kwargs):
        params = {
            'chat_id': chat_id,
            'invite_link': invite_link
        }
        params.update(kwargs)
        return await self._request('editChatSubscriptionInviteLink', params)
    
    async def get_star_transactions(self, offset: int = None, limit: int = None):
        params = {}
        if offset:
            params['offset'] = offset
        if limit:
            params['limit'] = limit
        return await self._request('getStarTransactions', params)
    
    # === BUSINESS METHODS (6 методов) ===
    async def set_my_short_description(self, short_description: str = None, language_code: str = None):
        params = {}
        if short_description:
            params['short_description'] = short_description
        if language_code:
            params['language_code'] = language_code
        return await self._request('setMyShortDescription', params)
    
    async def get_my_short_description(self, language_code: str = None):
        params = {}
        if language_code:
            params['language_code'] = language_code
        return await self._request('getMyShortDescription', params)
    
    async def set_my_name(self, name: str = None, language_code: str = None):
        params = {}
        if name:
            params['name'] = name
        if language_code:
            params['language_code'] = language_code
        return await self._request('setMyName', params)
    
    async def get_my_name(self, language_code: str = None):
        params = {}
        if language_code:
            params['language_code'] = language_code
        return await self._request('getMyName', params)
    
    async def refund_star_payment(self, user_id: int, telegram_payment_charge_id: str):
        return await self._request('refundStarPayment', {
            'user_id': user_id,
            'telegram_payment_charge_id': telegram_payment_charge_id
        })
    
    async def send_paid_media(self, chat_id: Union[int, str], star_count: int, media: List[Dict], **kwargs):
        params = {
            'chat_id': chat_id,
            'star_count': star_count,
            'media': json.dumps(media)
        }
        params.update(kwargs)
        return await self._request('sendPaidMedia', params)
