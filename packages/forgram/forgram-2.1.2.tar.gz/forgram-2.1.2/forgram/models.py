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
        """Ответить на сообщение"""
        if self._bot:
            return await self._bot.send_message(self.chat.id, text, 
                                              reply_to_message_id=self.message_id, **kwargs)
    
    async def answer(self, text: str, **kwargs):
        """Отправить сообщение в чат"""
        if self._bot:
            return await self._bot.send_message(self.chat.id, text, **kwargs)
    
    async def reply_with_typing(self, text: str, typing_time: float = 1.0, **kwargs):
        """Ответить с имитацией печатания"""
        if self._bot:
            return await self._bot.send_with_typing(self.chat.id, text, typing_time, 
                                                   reply_to_message_id=self.message_id, **kwargs)
    
    async def edit(self, text: str, **kwargs):
        """Редактировать сообщение"""
        if self._bot:
            return await self._bot.edit_message(self.chat.id, self.message_id, text, **kwargs)
    
    async def delete(self):
        """Удалить сообщение"""
        if self._bot:
            return await self._bot.delete_message(self.chat.id, self.message_id)
    
    async def forward_to(self, chat_id):
        """Переслать сообщение"""
        if self._bot:
            return await self._bot.forward_message(chat_id, self.chat.id, self.message_id)
    
    @property
    def is_command(self) -> bool:
        """Проверка, является ли сообщение командой"""
        return bool(self.text and self.text.startswith('/'))
    
    @property
    def command(self) -> Optional[str]:
        """Получить команду из сообщения"""
        if self.is_command:
            return self.text.split()[0][1:]
        return None
    
    @property
    def args(self) -> List[str]:
        """Получить аргументы команды"""
        if self.text:
            parts = self.text.split()[1:]
            return parts
        return []
    
    @property
    def words(self) -> List[str]:
        """Слова в сообщении"""
        if self.text:
            return self.text.split()
        return []


@dataclass
class CallbackQuery:
    id: str
    from_user: User
    message: Optional[Message] = None
    data: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], bot=None) -> 'CallbackQuery':
        return cls(
            id=data['id'],
            from_user=User.from_dict(data['from']),
            message=Message.from_dict(data['message'], bot) if 'message' in data else None,
            data=data.get('data')
        )


@dataclass  
class InlineQuery:
    id: str
    from_user: User
    query: str
    offset: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InlineQuery':
        return cls(
            id=data['id'],
            from_user=User.from_dict(data['from']),
            query=data['query'],
            offset=data.get('offset', "")
        )


@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    inline_query: Optional[InlineQuery] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], bot=None) -> 'Update':
        return cls(
            update_id=data['update_id'],
            message=Message.from_dict(data['message'], bot) if 'message' in data else None,
            callback_query=CallbackQuery.from_dict(data['callback_query'], bot) if 'callback_query' in data else None,
            inline_query=InlineQuery.from_dict(data['inline_query']) if 'inline_query' in data else None
        )
