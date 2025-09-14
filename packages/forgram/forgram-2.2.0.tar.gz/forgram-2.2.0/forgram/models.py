from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            id=data['id'],
            is_bot=data['is_bot'], 
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            username=data.get('username')
        )
    
    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def mention(self) -> str:
        return f'<a href="tg://user?id={self.id}">{self.full_name}</a>'
    
    @property
    def url(self) -> Optional[str]:
        if self.username:
            return f"https://t.me/{self.username}"
        return None


@dataclass 
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chat':
        return cls(
            id=data['id'],
            type=data['type'],
            title=data.get('title'), 
            username=data.get('username')
        )
    
    @property
    def is_private(self) -> bool:
        return self.type == 'private'
    
    @property
    def is_group(self) -> bool:
        return self.type in ['group', 'supergroup']
    
    @property
    def is_channel(self) -> bool:
        return self.type == 'channel'
    
    @property
    def url(self) -> Optional[str]:
        if self.username:
            return f"https://t.me/{self.username}"
        return None


class Message:
    def __init__(self, message_id: int, from_user: Optional[User], chat: Chat, 
                 date: datetime, text: Optional[str] = None, bot=None):
        self.message_id = message_id
        self.from_user = from_user
        self.chat = chat
        self.date = date
        self.text = text
        self._bot = bot
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], bot=None) -> 'Message':
        return cls(
            message_id=data['message_id'],
            from_user=User.from_dict(data['from']) if 'from' in data else None,
            chat=Chat.from_dict(data['chat']),
            date=datetime.fromtimestamp(data['date']),
            text=data.get('text'),
            bot=bot
        )
    
    async def reply(self, text: str, **kwargs):
        if self._bot:
            return await self._bot.send_message(self.chat.id, text, 
                                              reply_to_message_id=self.message_id, **kwargs)
    
    async def answer(self, text: str, **kwargs):
        if self._bot:
            return await self._bot.send_message(self.chat.id, text, **kwargs)
    
    async def reply_with_typing(self, text: str, delay: float = 1.0, **kwargs):
        if self._bot:
            return await self._bot.send_typing_message(self.chat.id, text, delay)
    
    async def edit(self, text: str, reply_markup: Optional[Dict] = None):
        if self._bot:
            return await self._bot.edit_message_text(self.chat.id, self.message_id, text, reply_markup)
    
    async def delete(self):
        if self._bot:
            return await self._bot.delete_message(self.chat.id, self.message_id)
    
    async def forward(self, to_chat_id: int):
        if self._bot:
            return await self._bot.forward_message(to_chat_id, self.chat.id, self.message_id)
    
    def is_command(self) -> bool:
        return self.text and self.text.startswith('/')
    
    def get_command(self) -> Optional[str]:
        if self.is_command():
            return self.text.split()[0][1:].split('@')[0]
        return None
    
    def get_args(self) -> List[str]:
        if self.text:
            parts = self.text.split()
            return parts[1:] if len(parts) > 1 else []
        return []
    
    @property
    def words(self) -> List[str]:
        return self.text.split() if self.text else []
    
    def __str__(self) -> str:
        return f"Message(id={self.message_id}, text='{self.text[:50]}...')"


@dataclass
class CallbackQuery:
    id: str
    from_user: User
    message: Optional[Message]
    data: Optional[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], bot=None) -> 'CallbackQuery':
        return cls(
            id=data['id'],
            from_user=User.from_dict(data['from']),
            message=Message.from_dict(data['message'], bot) if 'message' in data else None,
            data=data.get('data')
        )


@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], bot=None) -> 'Update':
        return cls(
            update_id=data['update_id'],
            message=Message.from_dict(data['message'], bot) if 'message' in data else None,
            callback_query=CallbackQuery.from_dict(data['callback_query'], bot) if 'callback_query' in data else None
        )
