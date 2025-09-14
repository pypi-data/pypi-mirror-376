"""
Forgram Advanced Types Module
Enhanced data types with maximum functionality
"""

import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

class BaseType:
    """Base class for all Telegram types"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._created_at = time.time()
        
    def __getattr__(self, name: str):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
    def __setattr__(self, name: str, value: Any):
        if name.startswith('_') or hasattr(self.__class__, name):
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            self._data[name] = value
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self._data.copy()
        
    def to_json(self) -> str:
        """Convert to JSON string"""
        import json
        return json.dumps(self._data, ensure_ascii=False)
        
    @property
    def age(self) -> float:
        """Get age of object in seconds"""
        return time.time() - self._created_at

class User(BaseType):
    """Enhanced User class with utility methods"""
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        first = self._data.get('first_name', '')
        last = self._data.get('last_name', '')
        return f"{first} {last}".strip() or "Unknown"
    
    @property
    def mention(self) -> str:
        """Get HTML mention"""
        from .utils import mention_html
        return mention_html(self.id, self.full_name)
    
    @property
    def mention_markdown(self) -> str:
        """Get Markdown mention"""
        from .utils import mention_markdown
        return mention_markdown(self.id, self.full_name)
    
    @property
    def username_link(self) -> Optional[str]:
        """Get username link"""
        if hasattr(self, 'username') and self.username:
            return f"@{self.username}"
        return None
    
    @property
    def profile_link(self) -> str:
        """Get profile link"""
        if hasattr(self, 'username') and self.username:
            return f"https://t.me/{self.username}"
        return f"tg://user?id={self.id}"
    
    @property
    def is_bot(self) -> bool:
        """Check if user is bot"""
        return self._data.get('is_bot', False)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has Telegram Premium"""
        return self._data.get('is_premium', False)
    
    @property
    def language_code(self) -> Optional[str]:
        """Get user language code"""
        return self._data.get('language_code')
    
    def __str__(self) -> str:
        return self.full_name
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.full_name}')"

class Chat(BaseType):
    """Enhanced Chat class with utility methods"""
    
    @property
    def is_private(self) -> bool:
        """Check if chat is private"""
        return self._data.get('type') == 'private'
    
    @property
    def is_group(self) -> bool:
        """Check if chat is group"""
        return self._data.get('type') in ['group', 'supergroup']
    
    @property
    def is_channel(self) -> bool:
        """Check if chat is channel"""
        return self._data.get('type') == 'channel'
    
    @property
    def is_supergroup(self) -> bool:
        """Check if chat is supergroup"""
        return self._data.get('type') == 'supergroup'
    
    @property
    def title_or_name(self) -> str:
        """Get chat title or user name"""
        if self.is_private:
            first = self._data.get('first_name', '')
            last = self._data.get('last_name', '')
            return f"{first} {last}".strip() or "Private Chat"
        return self._data.get('title', 'Unknown Chat')
    
    @property
    def link(self) -> Optional[str]:
        """Get chat link"""
        if hasattr(self, 'username') and self.username:
            return f"https://t.me/{self.username}"
        return None
    
    @property
    def member_count(self) -> Optional[int]:
        """Get member count if available"""
        return self._data.get('member_count')
    
    def __str__(self) -> str:
        return self.title_or_name
    
    def __repr__(self) -> str:
        return f"Chat(id={self.id}, type='{self.type}', title='{self.title_or_name}')"

class Message(BaseType):
    """Enhanced Message class with rich functionality"""
    
    def __init__(self, data: Dict[str, Any], bot=None):
        super().__init__(data)
        self._bot = bot
        self._entities_cache = None
        
    @property
    def user(self) -> User:
        """Get message sender as User object"""
        from_data = self._data.get('from', {})
        return User(from_data)
    
    @property
    def chat(self) -> Chat:
        """Get message chat as Chat object"""
        chat_data = self._data.get('chat', {})
        return Chat(chat_data)
    
    @property
    def reply_to_message(self) -> Optional['Message']:
        """Get replied message"""
        reply_data = self._data.get('reply_to_message')
        if reply_data:
            return Message(reply_data, self._bot)
        return None
    
    @property
    def forward_from_user(self) -> Optional[User]:
        """Get forward from user"""
        forward_data = self._data.get('forward_from')
        if forward_data:
            return User(forward_data)
        return None
    
    @property
    def forward_from_chat(self) -> Optional[Chat]:
        """Get forward from chat"""
        forward_data = self._data.get('forward_from_chat')
        if forward_data:
            return Chat(forward_data)
        return None
    
    @property
    def content_type(self) -> str:
        """Determine message content type"""
        if self._data.get('text'):
            return 'text'
        elif self._data.get('photo'):
            return 'photo'
        elif self._data.get('video'):
            return 'video'
        elif self._data.get('document'):
            return 'document'
        elif self._data.get('audio'):
            return 'audio'
        elif self._data.get('voice'):
            return 'voice'
        elif self._data.get('sticker'):
            return 'sticker'
        elif self._data.get('animation'):
            return 'animation'
        elif self._data.get('video_note'):
            return 'video_note'
        elif self._data.get('contact'):
            return 'contact'
        elif self._data.get('location'):
            return 'location'
        elif self._data.get('venue'):
            return 'venue'
        elif self._data.get('poll'):
            return 'poll'
        elif self._data.get('dice'):
            return 'dice'
        elif self._data.get('game'):
            return 'game'
        elif self._data.get('invoice'):
            return 'invoice'
        elif self._data.get('successful_payment'):
            return 'successful_payment'
        else:
            return 'unknown'
    
    @property
    def is_command(self) -> bool:
        """Check if message is a command"""
        if not self.text:
            return False
        entities = self._data.get('entities', [])
        return (entities and entities[0].get('type') == 'bot_command' 
                and entities[0].get('offset') == 0)
    
    @property
    def command(self) -> Optional[str]:
        """Get command name if message is a command"""
        if not self.is_command:
            return None
        
        text = self.text
        first_space = text.find(' ')
        command_text = text[:first_space] if first_space != -1 else text
        
        # Remove @ mention from command
        at_pos = command_text.find('@')
        if at_pos != -1:
            command_text = command_text[:at_pos]
        
        return command_text[1:]  # Remove /
    
    @property
    def command_args(self) -> str:
        """Get command arguments"""
        if not self.is_command or not self.text:
            return ''
        
        first_space = self.text.find(' ')
        return self.text[first_space + 1:].strip() if first_space != -1 else ''
    
    @property
    def entities(self) -> List[Dict]:
        """Get parsed message entities"""
        if self._entities_cache is None:
            self._entities_cache = self._parse_entities()
        return self._entities_cache
    
    def _parse_entities(self) -> List[Dict]:
        """Parse message entities with text"""
        entities = self._data.get('entities', [])
        text = self.text or ''
        
        result = []
        for entity in entities:
            offset = entity.get('offset', 0)
            length = entity.get('length', 0)
            entity_text = text[offset:offset + length]
            
            result.append({
                'type': entity.get('type'),
                'offset': offset,
                'length': length,
                'text': entity_text,
                'url': entity.get('url'),
                'user': User(entity['user']) if 'user' in entity else None,
                'language': entity.get('language')
            })
        
        return result
    
    @property
    def urls(self) -> List[str]:
        """Extract URLs from message"""
        urls = []
        for entity in self.entities:
            if entity['type'] == 'url':
                urls.append(entity['text'])
            elif entity['type'] == 'text_link':
                urls.append(entity['url'])
        return urls
    
    @property
    def mentions(self) -> List[str]:
        """Extract mentions from message"""
        mentions = []
        for entity in self.entities:
            if entity['type'] == 'mention':
                mentions.append(entity['text'])
        return mentions
    
    @property
    def hashtags(self) -> List[str]:
        """Extract hashtags from message"""
        hashtags = []
        for entity in self.entities:
            if entity['type'] == 'hashtag':
                hashtags.append(entity['text'])
        return hashtags
    
    @property
    def is_forwarded(self) -> bool:
        """Check if message is forwarded"""
        return any(key.startswith('forward_') for key in self._data.keys())
    
    @property
    def is_reply(self) -> bool:
        """Check if message is a reply"""
        return self.reply_to_message is not None
    
    @property
    def is_edited(self) -> bool:
        """Check if message was edited"""
        return 'edit_date' in self._data
    
    @property
    def datetime(self) -> datetime:
        """Get message datetime"""
        return datetime.fromtimestamp(self._data.get('date', 0))
    
    @property
    def edit_datetime(self) -> Optional[datetime]:
        """Get edit datetime"""
        edit_date = self._data.get('edit_date')
        return datetime.fromtimestamp(edit_date) if edit_date else None
    
    @property
    def file_id(self) -> Optional[str]:
        """Get file ID for media messages"""
        content = self.content_type
        
        if content == 'photo':
            photos = self._data.get('photo', [])
            return photos[-1]['file_id'] if photos else None
        elif content in ['video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note']:
            media = self._data.get(content, {})
            return media.get('file_id')
        
        return None
    
    @property
    def file_size(self) -> Optional[int]:
        """Get file size for media messages"""
        content = self.content_type
        
        if content == 'photo':
            photos = self._data.get('photo', [])
            return photos[-1].get('file_size') if photos else None
        elif content in ['video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note']:
            media = self._data.get(content, {})
            return media.get('file_size')
        
        return None
    
    # Message manipulation methods
    
    async def reply(self, text: str, **kwargs):
        """Reply to this message"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        kwargs['reply_to_message_id'] = self.message_id
        return await self._bot.send_message(self.chat.id, text, **kwargs)
    
    async def edit(self, text: str, **kwargs):
        """Edit this message"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.edit_message_text(
            self.chat.id, self.message_id, text, **kwargs
        )
    
    async def delete(self):
        """Delete this message"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.delete_message(self.chat.id, self.message_id)
    
    async def forward_to(self, chat_id: Union[int, str]):
        """Forward this message to another chat"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.forward_message(chat_id, self.chat.id, self.message_id)
    
    async def copy_to(self, chat_id: Union[int, str], **kwargs):
        """Copy this message to another chat"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.copy_message(chat_id, self.chat.id, self.message_id, **kwargs)
    
    async def pin(self):
        """Pin this message"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.pin_message(self.chat.id, self.message_id)
    
    async def unpin(self):
        """Unpin this message"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.unpin_message(self.chat.id, self.message_id)
    
    async def react(self, emoji: str):
        """React to this message (if supported)"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        # This would be implemented when Telegram adds reaction API
        pass
    
    def __str__(self) -> str:
        return self.text or f"<{self.content_type} message>"
    
    def __repr__(self) -> str:
        return f"Message(id={self.message_id}, from={self.user.full_name}, type={self.content_type})"

class CallbackQuery(BaseType):
    """Enhanced CallbackQuery class"""
    
    def __init__(self, data: Dict[str, Any], bot=None):
        super().__init__(data)
        self._bot = bot
    
    @property
    def user(self) -> User:
        """Get callback query user"""
        from_data = self._data.get('from', {})
        return User(from_data)
    
    @property
    def message(self) -> Optional[Message]:
        """Get callback query message"""
        message_data = self._data.get('message')
        if message_data:
            return Message(message_data, self._bot)
        return None
    
    async def answer(self, text: str = None, show_alert: bool = False, **kwargs):
        """Answer callback query"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.answer_callback_query(
            self.id, text=text, show_alert=show_alert, **kwargs
        )
    
    async def edit_message_text(self, text: str, **kwargs):
        """Edit message text"""
        if not self._bot or not self.message:
            raise RuntimeError("Bot instance or message not available")
        
        return await self._bot.edit_message_text(
            self.message.chat.id, self.message.message_id, text, **kwargs
        )
    
    async def edit_message_reply_markup(self, reply_markup=None):
        """Edit message reply markup"""
        if not self._bot or not self.message:
            raise RuntimeError("Bot instance or message not available")
        
        return await self._bot.edit_message_reply_markup(
            self.message.chat.id, self.message.message_id, reply_markup=reply_markup
        )
    
    def __str__(self) -> str:
        return self.data or f"<callback query from {self.user.full_name}>"
    
    def __repr__(self) -> str:
        return f"CallbackQuery(id={self.id}, data='{self.data}', from={self.user.full_name})"

class InlineQuery(BaseType):
    """Enhanced InlineQuery class"""
    
    def __init__(self, data: Dict[str, Any], bot=None):
        super().__init__(data)
        self._bot = bot
    
    @property
    def user(self) -> User:
        """Get inline query user"""
        from_data = self._data.get('from', {})
        return User(from_data)
    
    @property
    def location(self) -> Optional[Dict]:
        """Get user location if shared"""
        return self._data.get('location')
    
    async def answer(self, results: List[Dict], **kwargs):
        """Answer inline query"""
        if not self._bot:
            raise RuntimeError("Bot instance not available")
        
        return await self._bot.answer_inline_query(self.id, results, **kwargs)
    
    def __str__(self) -> str:
        return self.query or f"<inline query from {self.user.full_name}>"
    
    def __repr__(self) -> str:
        return f"InlineQuery(id={self.id}, query='{self.query}', from={self.user.full_name})"

class Update(BaseType):
    """Enhanced Update class"""
    
    def __init__(self, data: Dict[str, Any], bot=None):
        super().__init__(data)
        self._bot = bot
    
    @property
    def message(self) -> Optional[Message]:
        """Get update message"""
        message_data = self._data.get('message')
        if message_data:
            return Message(message_data, self._bot)
        return None
    
    @property
    def edited_message(self) -> Optional[Message]:
        """Get edited message"""
        message_data = self._data.get('edited_message')
        if message_data:
            return Message(message_data, self._bot)
        return None
    
    @property
    def channel_post(self) -> Optional[Message]:
        """Get channel post"""
        message_data = self._data.get('channel_post')
        if message_data:
            return Message(message_data, self._bot)
        return None
    
    @property
    def edited_channel_post(self) -> Optional[Message]:
        """Get edited channel post"""
        message_data = self._data.get('edited_channel_post')
        if message_data:
            return Message(message_data, self._bot)
        return None
    
    @property
    def callback_query(self) -> Optional[CallbackQuery]:
        """Get callback query"""
        callback_data = self._data.get('callback_query')
        if callback_data:
            return CallbackQuery(callback_data, self._bot)
        return None
    
    @property
    def inline_query(self) -> Optional[InlineQuery]:
        """Get inline query"""
        inline_data = self._data.get('inline_query')
        if inline_data:
            return InlineQuery(inline_data, self._bot)
        return None
    
    @property
    def chosen_inline_result(self) -> Optional[Dict]:
        """Get chosen inline result"""
        return self._data.get('chosen_inline_result')
    
    @property
    def shipping_query(self) -> Optional[Dict]:
        """Get shipping query"""
        return self._data.get('shipping_query')
    
    @property
    def pre_checkout_query(self) -> Optional[Dict]:
        """Get pre-checkout query"""
        return self._data.get('pre_checkout_query')
    
    @property
    def poll(self) -> Optional[Dict]:
        """Get poll"""
        return self._data.get('poll')
    
    @property
    def poll_answer(self) -> Optional[Dict]:
        """Get poll answer"""
        return self._data.get('poll_answer')
    
    @property
    def my_chat_member(self) -> Optional[Dict]:
        """Get my chat member update"""
        return self._data.get('my_chat_member')
    
    @property
    def chat_member(self) -> Optional[Dict]:
        """Get chat member update"""
        return self._data.get('chat_member')
    
    @property
    def chat_join_request(self) -> Optional[Dict]:
        """Get chat join request"""
        return self._data.get('chat_join_request')
    
    @property
    def update_type(self) -> str:
        """Get update type"""
        for key in ['message', 'edited_message', 'channel_post', 'edited_channel_post',
                   'callback_query', 'inline_query', 'chosen_inline_result',
                   'shipping_query', 'pre_checkout_query', 'poll', 'poll_answer',
                   'my_chat_member', 'chat_member', 'chat_join_request']:
            if key in self._data:
                return key
        return 'unknown'
    
    @property
    def effective_message(self) -> Optional[Message]:
        """Get effective message from any update type"""
        for attr in ['message', 'edited_message', 'channel_post', 'edited_channel_post']:
            msg = getattr(self, attr)
            if msg:
                return msg
        
        # Check callback query message
        if self.callback_query and self.callback_query.message:
            return self.callback_query.message
        
        return None
    
    @property
    def effective_user(self) -> Optional[User]:
        """Get effective user from any update type"""
        effective_msg = self.effective_message
        if effective_msg:
            return effective_msg.user
        
        if self.callback_query:
            return self.callback_query.user
        
        if self.inline_query:
            return self.inline_query.user
        
        return None
    
    @property
    def effective_chat(self) -> Optional[Chat]:
        """Get effective chat from any update type"""
        effective_msg = self.effective_message
        if effective_msg:
            return effective_msg.chat
        
        if self.callback_query and self.callback_query.message:
            return self.callback_query.message.chat
        
        return None
    
    def __str__(self) -> str:
        return f"<Update {self.update_id}: {self.update_type}>"
    
    def __repr__(self) -> str:
        return f"Update(id={self.update_id}, type={self.update_type})"

# Additional specialized types

class ChatMember(BaseType):
    """Chat member information"""
    
    @property
    def user(self) -> User:
        """Get user"""
        user_data = self._data.get('user', {})
        return User(user_data)
    
    @property
    def is_admin(self) -> bool:
        """Check if member is admin"""
        return self.status in ['creator', 'administrator']
    
    @property
    def is_owner(self) -> bool:
        """Check if member is owner"""
        return self.status == 'creator'
    
    @property
    def can_delete_messages(self) -> bool:
        """Check if can delete messages"""
        return self._data.get('can_delete_messages', False)
    
    @property
    def can_restrict_members(self) -> bool:
        """Check if can restrict members"""
        return self._data.get('can_restrict_members', False)

class WebhookInfo(BaseType):
    """Webhook information"""
    
    @property
    def is_set(self) -> bool:
        """Check if webhook is set"""
        return bool(self._data.get('url'))
    
    @property
    def pending_updates(self) -> int:
        """Get pending updates count"""
        return self._data.get('pending_update_count', 0)
        
    @property
    def last_error_date(self) -> Optional[datetime]:
        """Get last error date"""
        error_date = self._data.get('last_error_date')
        return datetime.fromtimestamp(error_date) if error_date else None

class BotCommand(BaseType):
    """Bot command"""
    
    def __init__(self, command: str, description: str):
        super().__init__({
            'command': command,
            'description': description
        })

class InlineKeyboardButton(BaseType):
    """Inline keyboard button"""
    
    def __init__(self, text: str, **kwargs):
        data = {'text': text}
        data.update(kwargs)
        super().__init__(data)

class KeyboardButton(BaseType):
    """Reply keyboard button"""
    
    def __init__(self, text: str, **kwargs):
        data = {'text': text}
        data.update(kwargs)
        super().__init__(data)
