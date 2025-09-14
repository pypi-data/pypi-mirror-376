

from typing import Any, Dict, Optional
from .storage import BaseStorage, MemoryStorage


class StateStorage:
    def __init__(self, storage: Optional[BaseStorage] = None):
        self.storage = storage or MemoryStorage()
    
    async def set_state(self, user_id: int, state: str, data: Optional[Dict[str, Any]] = None):
        state_key = f"state:{user_id}"
        state_data = {
            'current_state': state,
            'data': data or {}
        }
        await self.storage.set(state_key, state_data)
    
    async def get_state(self, user_id: int) -> Optional[str]:
        state_key = f"state:{user_id}"
        state_data = await self.storage.get(state_key)
        if state_data:
            return state_data.get('current_state')
        return None
    
    async def get_data(self, user_id: int) -> Dict[str, Any]:
        state_key = f"state:{user_id}"
        state_data = await self.storage.get(state_key)
        if state_data:
            return state_data.get('data', {})
        return {}
    
    async def get_state_data(self, user_id: int) -> Dict[str, Any]:
        return await self.get_data(user_id)
    
    async def update_data(self, user_id: int, data: Dict[str, Any]):
        state_key = f"state:{user_id}"
        state_data = await self.storage.get(state_key) or {}
        current_data = state_data.get('data', {})
        current_data.update(data)
        state_data['data'] = current_data
        await self.storage.set(state_key, state_data)
    
    async def clear_state(self, user_id: int):
        state_key = f"state:{user_id}"
        await self.storage.delete(state_key)
    
    async def has_state(self, user_id: int) -> bool:
        state = await self.get_state(user_id)
        return state is not None


class State:
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, State):
            return self.name == other.name
        return False


class States:
    
    WAITING_INPUT = State("waiting_input")
    WAITING_CONFIRMATION = State("waiting_confirmation") 
    PROCESSING = State("processing")
    COMPLETED = State("completed")
    CANCELLED = State("cancelled")
    