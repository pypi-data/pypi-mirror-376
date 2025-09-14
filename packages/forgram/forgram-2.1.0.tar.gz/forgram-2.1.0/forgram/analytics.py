"""
Forgram Analytics Module  
Advanced analytics and metrics collection for bots
"""

import time
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

class AnalyticsCollector:
    """Collect and analyze bot usage analytics"""
    
    def __init__(self, storage=None, retention_days: int = 30):
        self.storage = storage
        self.retention_days = retention_days
        
        # In-memory analytics
        self.metrics = {
            'messages': [],
            'commands': [],
            'users': {},
            'chats': {},
            'errors': [],
            'response_times': []
        }
        
        self.daily_stats = defaultdict(lambda: {
            'messages': 0,
            'users': set(),
            'commands': Counter(),
            'chats': set(),
            'errors': 0
        })
        
        self.hourly_stats = defaultdict(lambda: {
            'messages': 0,
            'users': set(),
            'peak_hour': None
        })
        
        self._start_time = time.time()
    
    async def track_message(self, message, response_time: float = None):
        """Track incoming message"""
        timestamp = time.time()
        date_key = datetime.fromtimestamp(timestamp).date().isoformat()
        hour_key = datetime.fromtimestamp(timestamp).hour
        
        # Message tracking
        message_data = {
            'timestamp': timestamp,
            'user_id': message.user.id,
            'chat_id': message.chat.id,
            'chat_type': message.chat.type,
            'content_type': message.content_type,
            'text_length': len(message.text or ''),
            'has_entities': bool(message._data.get('entities')),
            'is_forwarded': message.is_forwarded,
            'is_reply': message.is_reply
        }
        
        self.metrics['messages'].append(message_data)
        
        # Daily stats
        self.daily_stats[date_key]['messages'] += 1
        self.daily_stats[date_key]['users'].add(message.user.id)
        self.daily_stats[date_key]['chats'].add(message.chat.id)
        
        # Hourly stats
        hour_full_key = f"{date_key}_{hour_key:02d}"
        self.hourly_stats[hour_full_key]['messages'] += 1
        self.hourly_stats[hour_full_key]['users'].add(message.user.id)
        
        # User tracking
        user_id = str(message.user.id)
        if user_id not in self.metrics['users']:
            self.metrics['users'][user_id] = {
                'first_seen': timestamp,
                'last_seen': timestamp,
                'message_count': 0,
                'chat_ids': set(),
                'favorite_commands': Counter(),
                'avg_message_length': 0,
                'total_text_length': 0
            }
        
        user_stats = self.metrics['users'][user_id]
        user_stats['last_seen'] = timestamp
        user_stats['message_count'] += 1
        user_stats['chat_ids'].add(message.chat.id)
        user_stats['total_text_length'] += len(message.text or '')
        user_stats['avg_message_length'] = user_stats['total_text_length'] / user_stats['message_count']
        
        # Chat tracking
        chat_id = str(message.chat.id)
        if chat_id not in self.metrics['chats']:
            self.metrics['chats'][chat_id] = {
                'first_message': timestamp,
                'last_message': timestamp,
                'message_count': 0,
                'user_count': set(),
                'chat_type': message.chat.type,
                'title': getattr(message.chat, 'title', 'Private Chat')
            }
        
        chat_stats = self.metrics['chats'][chat_id]
        chat_stats['last_message'] = timestamp
        chat_stats['message_count'] += 1
        chat_stats['user_count'].add(message.user.id)
        
        # Response time tracking
        if response_time:
            self.metrics['response_times'].append({
                'timestamp': timestamp,
                'response_time': response_time,
                'user_id': message.user.id,
                'chat_id': message.chat.id
            })
        
        # Command tracking
        if message.is_command:
            command_data = {
                'timestamp': timestamp,
                'command': message.command,
                'user_id': message.user.id,
                'chat_id': message.chat.id,
                'args_length': len(message.command_args)
            }
            
            self.metrics['commands'].append(command_data)
            self.daily_stats[date_key]['commands'][message.command] += 1
            user_stats['favorite_commands'][message.command] += 1
        
        await self._cleanup_old_data()
    
    async def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track bot errors"""
        error_data = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.metrics['errors'].append(error_data)
        
        date_key = datetime.now().date().isoformat()
        self.daily_stats[date_key]['errors'] += 1
    
    async def _cleanup_old_data(self):
        """Clean up old analytics data"""
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        
        # Clean messages
        self.metrics['messages'] = [
            msg for msg in self.metrics['messages']
            if msg['timestamp'] > cutoff_time
        ]
        
        # Clean commands
        self.metrics['commands'] = [
            cmd for cmd in self.metrics['commands']
            if cmd['timestamp'] > cutoff_time
        ]
        
        # Clean errors
        self.metrics['errors'] = [
            err for err in self.metrics['errors']
            if err['timestamp'] > cutoff_time
        ]
        
        # Clean response times
        self.metrics['response_times'] = [
            rt for rt in self.metrics['response_times']
            if rt['timestamp'] > cutoff_time
        ]
        
        # Clean daily stats
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).date()
        self.daily_stats = {
            date: stats for date, stats in self.daily_stats.items()
            if datetime.fromisoformat(date).date() >= cutoff_date
        }
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Get overview analytics"""
        now = time.time()
        uptime = now - self._start_time
        
        # Basic counts
        total_messages = len(self.metrics['messages'])
        total_commands = len(self.metrics['commands'])
        total_users = len(self.metrics['users'])
        total_chats = len(self.metrics['chats'])
        total_errors = len(self.metrics['errors'])
        
        # Calculate rates
        messages_per_hour = (total_messages / (uptime / 3600)) if uptime > 0 else 0
        commands_per_hour = (total_commands / (uptime / 3600)) if uptime > 0 else 0
        
        # Active users (messaged in last 24h)
        day_ago = now - 86400
        active_users = sum(1 for user_stats in self.metrics['users'].values()
                          if user_stats['last_seen'] > day_ago)
        
        # Response time stats
        response_times = [rt['response_time'] for rt in self.metrics['response_times']]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': self._format_duration(uptime),
            'total_messages': total_messages,
            'total_commands': total_commands,
            'total_users': total_users,
            'total_chats': total_chats,
            'total_errors': total_errors,
            'active_users_24h': active_users,
            'messages_per_hour': round(messages_per_hour, 2),
            'commands_per_hour': round(commands_per_hour, 2),
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'error_rate': round((total_errors / total_messages * 100), 2) if total_messages > 0 else 0
        }
    
    def get_user_stats(self, user_id: int = None, limit: int = 10) -> Union[Dict, List]:
        """Get user statistics"""
        if user_id:
            user_stats = self.metrics['users'].get(str(user_id))
            if not user_stats:
                return None
            
            # Convert sets to lists for JSON serialization
            stats = user_stats.copy()
            stats['chat_ids'] = list(stats['chat_ids'])
            stats['favorite_commands'] = dict(stats['favorite_commands'].most_common(5))
            stats['first_seen_formatted'] = datetime.fromtimestamp(stats['first_seen']).isoformat()
            stats['last_seen_formatted'] = datetime.fromtimestamp(stats['last_seen']).isoformat()
            
            return stats
        else:
            # Top users by message count
            top_users = sorted(
                self.metrics['users'].items(),
                key=lambda x: x[1]['message_count'],
                reverse=True
            )[:limit]
            
            return [
                {
                    'user_id': int(user_id),
                    'message_count': stats['message_count'],
                    'avg_message_length': round(stats['avg_message_length'], 1),
                    'chat_count': len(stats['chat_ids']),
                    'last_seen': datetime.fromtimestamp(stats['last_seen']).isoformat()
                }
                for user_id, stats in top_users
            ]
    
    def get_chat_stats(self, chat_id: Union[int, str] = None, limit: int = 10) -> Union[Dict, List]:
        """Get chat statistics"""
        if chat_id:
            chat_stats = self.metrics['chats'].get(str(chat_id))
            if not chat_stats:
                return None
            
            stats = chat_stats.copy()
            stats['user_count'] = len(stats['user_count'])
            stats['first_message_formatted'] = datetime.fromtimestamp(stats['first_message']).isoformat()
            stats['last_message_formatted'] = datetime.fromtimestamp(stats['last_message']).isoformat()
            
            return stats
        else:
            # Top chats by message count
            top_chats = sorted(
                self.metrics['chats'].items(),
                key=lambda x: x[1]['message_count'],
                reverse=True
            )[:limit]
            
            return [
                {
                    'chat_id': int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id,
                    'title': stats['title'],
                    'chat_type': stats['chat_type'],
                    'message_count': stats['message_count'],
                    'user_count': len(stats['user_count']),
                    'last_message': datetime.fromtimestamp(stats['last_message']).isoformat()
                }
                for chat_id, stats in top_chats
            ]
    
    def get_command_stats(self, limit: int = 10) -> List[Dict]:
        """Get command usage statistics"""
        command_counts = Counter()
        
        for cmd_data in self.metrics['commands']:
            command_counts[cmd_data['command']] += 1
        
        return [
            {'command': cmd, 'count': count}
            for cmd, count in command_counts.most_common(limit)
        ]
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily statistics"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        daily_data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_key = current_date.isoformat()
            stats = self.daily_stats.get(date_key, {
                'messages': 0,
                'users': set(),
                'commands': Counter(),
                'chats': set(),
                'errors': 0
            })
            
            daily_data.append({
                'date': date_key,
                'messages': stats['messages'],
                'unique_users': len(stats['users']),
                'unique_chats': len(stats['chats']),
                'commands': sum(stats['commands'].values()),
                'errors': stats['errors'],
                'top_command': stats['commands'].most_common(1)[0][0] if stats['commands'] else None
            })
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    def get_hourly_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly statistics"""
        hourly_data = []
        now = datetime.now()
        
        for i in range(hours):
            target_time = now - timedelta(hours=i)
            hour_key = f"{target_time.date().isoformat()}_{target_time.hour:02d}"
            
            stats = self.hourly_stats.get(hour_key, {
                'messages': 0,
                'users': set()
            })
            
            hourly_data.append({
                'hour': target_time.strftime('%Y-%m-%d %H:00'),
                'messages': stats['messages'],
                'unique_users': len(stats['users'])
            })
        
        return list(reversed(hourly_data))
    
    def get_error_stats(self, limit: int = 10) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.metrics['errors']:
            return {'total_errors': 0, 'error_types': [], 'recent_errors': []}
        
        # Count error types
        error_types = Counter()
        for error in self.metrics['errors']:
            error_types[error['error_type']] += 1
        
        # Recent errors
        recent_errors = sorted(
            self.metrics['errors'],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
        
        for error in recent_errors:
            error['timestamp_formatted'] = datetime.fromtimestamp(error['timestamp']).isoformat()
        
        return {
            'total_errors': len(self.metrics['errors']),
            'error_types': [
                {'type': error_type, 'count': count}
                for error_type, count in error_types.most_common()
            ],
            'recent_errors': recent_errors
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        response_times = [rt['response_time'] for rt in self.metrics['response_times']]
        
        if not response_times:
            return {'no_data': True}
        
        return {
            'total_responses': len(response_times),
            'avg_response_time_ms': round(statistics.mean(response_times) * 1000, 2),
            'median_response_time_ms': round(statistics.median(response_times) * 1000, 2),
            'min_response_time_ms': round(min(response_times) * 1000, 2),
            'max_response_time_ms': round(max(response_times) * 1000, 2),
            'p95_response_time_ms': round(self._percentile(response_times, 95) * 1000, 2),
            'p99_response_time_ms': round(self._percentile(response_times, 99) * 1000, 2)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}d {hours}h"
    
    async def export_data(self, format: str = 'json', file_path: str = None) -> Union[str, bytes]:
        """Export analytics data"""
        data = {
            'export_timestamp': time.time(),
            'overview': self.get_overview_stats(),
            'daily_stats': self.get_daily_stats(30),
            'command_stats': self.get_command_stats(20),
            'user_stats': self.get_user_stats(limit=50),
            'chat_stats': self.get_chat_stats(limit=20),
            'error_stats': self.get_error_stats(50),
            'performance_stats': self.get_performance_stats()
        }
        
        if format == 'json':
            json_data = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            return json_data
        
        elif format == 'csv':
            # Simple CSV export for daily stats
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write daily stats
            writer.writerow(['Date', 'Messages', 'Users', 'Chats', 'Commands', 'Errors'])
            for day in data['daily_stats']:
                writer.writerow([
                    day['date'], day['messages'], day['unique_users'],
                    day['unique_chats'], day['commands'], day['errors']
                ])
            
            csv_data = output.getvalue()
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(csv_data)
            
            return csv_data
        
        else:
            raise ValueError(f"Unsupported format: {format}")

def analytics_middleware(collector: AnalyticsCollector):
    """Middleware for automatic analytics collection"""
    
    async def middleware(update, bot, context):
        start_time = time.time()
        
        # Process the update normally first
        result = True
        
        try:
            # Track after processing to measure response time
            if 'message' in update:
                from .advanced_types import Message
                message = Message(update['message'], bot)
                response_time = time.time() - start_time
                await collector.track_message(message, response_time)
            
        except Exception as e:
            await collector.track_error(e, {'update_id': update.get('update_id')})
        
        return result
    
    return middleware
