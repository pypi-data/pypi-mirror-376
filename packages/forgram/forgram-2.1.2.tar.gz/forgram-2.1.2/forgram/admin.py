"""
Forgram Admin Module
Advanced administration tools for bot management
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class BotAdmin:
    """Advanced bot administration system"""
    
    def __init__(self, bot, admin_users: List[int] = None, 
                 storage=None, log_actions: bool = True):
        self.bot = bot
        self.admin_users = set(admin_users or [])
        self.storage = storage
        self.log_actions = log_actions
        
        # Admin permissions
        self.permissions = {
            'super_admin': [],  # All permissions
            'admin': ['ban', 'unban', 'mute', 'warn', 'stats', 'broadcast'],
            'moderator': ['ban', 'unban', 'mute', 'warn']
        }
        
        # User roles
        self.user_roles = {}
        
        # Action logs
        self.action_logs = []
        
        self.stats = {
            'commands_executed': 0,
            'users_banned': 0,
            'users_unbanned': 0,
            'broadcasts_sent': 0,
            'warnings_issued': 0
        }
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_users or user_id in self.user_roles
    
    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get user role"""
        if user_id in self.admin_users:
            return 'super_admin'
        return self.user_roles.get(user_id)
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        role = self.get_user_role(user_id)
        if not role:
            return False
        
        if role == 'super_admin':
            return True
        
        return permission in self.permissions.get(role, [])
    
    def add_admin(self, user_id: int, role: str = 'admin'):
        """Add admin user"""
        if role in self.permissions:
            self.user_roles[user_id] = role
            self._log_action('add_admin', {'user_id': user_id, 'role': role})
    
    def remove_admin(self, user_id: int):
        """Remove admin user"""
        if user_id in self.user_roles:
            old_role = self.user_roles.pop(user_id)
            self._log_action('remove_admin', {'user_id': user_id, 'old_role': old_role})
    
    def _log_action(self, action: str, data: Dict[str, Any]):
        """Log admin action"""
        if not self.log_actions:
            return
        
        log_entry = {
            'action': action,
            'data': data,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        
        self.action_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.action_logs) > 1000:
            self.action_logs = self.action_logs[-1000:]
        
        logger.info(f"Admin action: {action} - {data}")
    
    # User management
    
    async def ban_user_globally(self, user_id: int, reason: str = None, admin_id: int = None):
        """Ban user globally across all chats"""
        if admin_id and not self.has_permission(admin_id, 'ban'):
            raise PermissionError("Insufficient permissions")
        
        chats = await self._get_bot_chats()
        banned_chats = 0
        
        for chat_id in chats:
            try:
                await self.bot.ban_user(chat_id, user_id)
                banned_chats += 1
            except Exception as e:
                logger.warning(f"Failed to ban user {user_id} in chat {chat_id}: {e}")
        
        self.stats['users_banned'] += 1
        self._log_action('global_ban', {
            'user_id': user_id,
            'reason': reason,
            'admin_id': admin_id,
            'banned_chats': banned_chats
        })
        
        return banned_chats
    
    async def unban_user_globally(self, user_id: int, admin_id: int = None):
        """Unban user globally"""
        if admin_id and not self.has_permission(admin_id, 'unban'):
            raise PermissionError("Insufficient permissions")
        
        chats = await self._get_bot_chats()
        unbanned_chats = 0
        
        for chat_id in chats:
            try:
                await self.bot.unban_user(chat_id, user_id)
                unbanned_chats += 1
            except Exception as e:
                logger.warning(f"Failed to unban user {user_id} in chat {chat_id}: {e}")
        
        self.stats['users_unbanned'] += 1
        self._log_action('global_unban', {
            'user_id': user_id,
            'admin_id': admin_id,
            'unbanned_chats': unbanned_chats
        })
        
        return unbanned_chats
    
    async def warn_user(self, chat_id: Union[int, str], user_id: int, 
                       reason: str = None, admin_id: int = None):
        """Issue warning to user"""
        if admin_id and not self.has_permission(admin_id, 'warn'):
            raise PermissionError("Insufficient permissions")
        
        # Store warning
        warning_key = f"warnings:{chat_id}:{user_id}"
        if self.storage:
            warnings = await self.storage.get(warning_key) or []
            warnings.append({
                'reason': reason,
                'timestamp': time.time(),
                'admin_id': admin_id
            })
            await self.storage.set(warning_key, warnings)
        
        self.stats['warnings_issued'] += 1
        self._log_action('warn_user', {
            'chat_id': chat_id,
            'user_id': user_id,
            'reason': reason,
            'admin_id': admin_id
        })
        
        return len(warnings) if self.storage else 1
    
    async def get_user_warnings(self, chat_id: Union[int, str], user_id: int) -> List[Dict]:
        """Get user warnings"""
        if not self.storage:
            return []
        
        warning_key = f"warnings:{chat_id}:{user_id}"
        return await self.storage.get(warning_key) or []
    
    async def clear_user_warnings(self, chat_id: Union[int, str], user_id: int,
                                 admin_id: int = None):
        """Clear user warnings"""
        if admin_id and not self.has_permission(admin_id, 'warn'):
            raise PermissionError("Insufficient permissions")
        
        if self.storage:
            warning_key = f"warnings:{chat_id}:{user_id}"
            await self.storage.delete(warning_key)
        
        self._log_action('clear_warnings', {
            'chat_id': chat_id,
            'user_id': user_id,
            'admin_id': admin_id
        })
    
    # Broadcasting
    
    async def broadcast_message(self, message: str, chats: List[Union[int, str]] = None,
                               admin_id: int = None, delay: float = 0.1):
        """Broadcast message to multiple chats"""
        if admin_id and not self.has_permission(admin_id, 'broadcast'):
            raise PermissionError("Insufficient permissions")
        
        if chats is None:
            chats = await self._get_bot_chats()
        
        sent_count = 0
        failed_count = 0
        
        for chat_id in chats:
            try:
                await self.bot.send_message(chat_id, message)
                sent_count += 1
                
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast to {chat_id}: {e}")
        
        self.stats['broadcasts_sent'] += 1
        self._log_action('broadcast', {
            'message': message[:100] + '...' if len(message) > 100 else message,
            'admin_id': admin_id,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_chats': len(chats)
        })
        
        return {'sent': sent_count, 'failed': failed_count}
    
    async def broadcast_to_users(self, message: str, user_ids: List[int],
                                admin_id: int = None, delay: float = 0.1):
        """Broadcast message to specific users"""
        if admin_id and not self.has_permission(admin_id, 'broadcast'):
            raise PermissionError("Insufficient permissions")
        
        sent_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                await self.bot.send_message(user_id, message)
                sent_count += 1
                
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send message to user {user_id}: {e}")
        
        self._log_action('user_broadcast', {
            'message': message[:100] + '...' if len(message) > 100 else message,
            'admin_id': admin_id,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_users': len(user_ids)
        })
        
        return {'sent': sent_count, 'failed': failed_count}
    
    # Statistics and monitoring
    
    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get comprehensive bot statistics"""
        bot_stats = self.bot.get_stats() if hasattr(self.bot, 'get_stats') else {}
        
        stats = {
            'bot': bot_stats,
            'admin': self.stats.copy(),
            'uptime': time.time() - self.bot._start_time if hasattr(self.bot, '_start_time') else 0,
            'total_admins': len(self.admin_users) + len(self.user_roles),
            'action_logs_count': len(self.action_logs)
        }
        
        return stats
    
    async def get_chat_stats(self, chat_id: Union[int, str]) -> Dict[str, Any]:
        """Get chat-specific statistics"""
        try:
            chat_info = await self.bot.get_chat(chat_id)
            member_count = await self.bot.get_member_count(chat_id)
            admins = await self.bot.get_chat_admins(chat_id)
            
            return {
                'chat_info': chat_info,
                'member_count': member_count,
                'admin_count': len(admins),
                'chat_type': chat_info.get('type'),
                'title': chat_info.get('title', 'Private Chat')
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _get_bot_chats(self) -> List[Union[int, str]]:
        """Get list of chats where bot is active"""
        # This would need to be implemented based on your storage
        # For now, return empty list
        if self.storage:
            return await self.storage.get('bot_chats') or []
        return []
    
    def get_action_logs(self, limit: int = 100, 
                       action_type: str = None) -> List[Dict[str, Any]]:
        """Get action logs"""
        logs = self.action_logs[-limit:]
        
        if action_type:
            logs = [log for log in logs if log['action'] == action_type]
        
        return logs
    
    # Backup and restore
    
    async def backup_data(self, backup_path: str):
        """Backup admin data"""
        backup_data = {
            'admin_users': list(self.admin_users),
            'user_roles': self.user_roles,
            'permissions': self.permissions,
            'stats': self.stats,
            'action_logs': self.action_logs[-100:],  # Last 100 logs
            'backup_time': time.time(),
            'version': '2.1.0'
        }
        
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Admin data backed up to {backup_path}")
    
    async def restore_data(self, backup_path: str):
        """Restore admin data from backup"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        self.admin_users = set(backup_data.get('admin_users', []))
        self.user_roles = backup_data.get('user_roles', {})
        self.permissions.update(backup_data.get('permissions', {}))
        self.stats.update(backup_data.get('stats', {}))
        
        # Merge action logs
        restored_logs = backup_data.get('action_logs', [])
        self.action_logs.extend(restored_logs)
        
        logger.info(f"Admin data restored from {backup_path}")
        self._log_action('restore_backup', {'backup_path': backup_path})

class AdminPanel:
    """Web-based admin panel"""
    
    def __init__(self, admin: BotAdmin, host: str = '127.0.0.1', 
                 port: int = 8081, secret_key: str = None):
        self.admin = admin
        self.host = host
        self.port = port
        self.secret_key = secret_key or 'forgram-admin-secret'
        self.app = None
    
    def create_flask_app(self):
        """Create Flask admin panel"""
        try:
            from flask import Flask, render_template_string, request, jsonify, session
            
            app = Flask(__name__)
            app.secret_key = self.secret_key
            
            @app.route('/')
            def dashboard():
                if 'user_id' not in session:
                    return render_template_string(LOGIN_TEMPLATE)
                
                user_id = session['user_id']
                if not self.admin.is_admin(user_id):
                    return "Access denied", 403
                
                stats = self.admin.get_bot_stats()
                return render_template_string(DASHBOARD_TEMPLATE, stats=stats)
            
            @app.route('/login', methods=['POST'])
            def login():
                user_id = int(request.form.get('user_id', 0))
                if self.admin.is_admin(user_id):
                    session['user_id'] = user_id
                    return jsonify({'success': True})
                return jsonify({'success': False, 'error': 'Invalid credentials'})
            
            @app.route('/api/stats')
            def api_stats():
                if 'user_id' not in session or not self.admin.is_admin(session['user_id']):
                    return jsonify({'error': 'Unauthorized'}), 401
                
                return jsonify(self.admin.get_bot_stats())
            
            @app.route('/api/logs')
            def api_logs():
                if 'user_id' not in session or not self.admin.is_admin(session['user_id']):
                    return jsonify({'error': 'Unauthorized'}), 401
                
                limit = int(request.args.get('limit', 50))
                action_type = request.args.get('type')
                
                logs = self.admin.get_action_logs(limit, action_type)
                return jsonify(logs)
            
            self.app = app
            return app
            
        except ImportError:
            raise ImportError("Flask is required for admin panel")
    
    async def start(self):
        """Start admin panel server"""
        if not self.app:
            self.create_flask_app()
        
        self.app.run(host=self.host, port=self.port, debug=False)

# Templates for admin panel

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Forgram Admin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; }
        .login-form { max-width: 300px; margin: 100px auto; }
        input, button { width: 100%; padding: 10px; margin: 5px 0; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-form">
        <h2>Forgram Admin Login</h2>
        <form onsubmit="login(event)">
            <input type="number" id="user_id" placeholder="Admin User ID" required>
            <button type="submit">Login</button>
        </form>
    </div>
    
    <script>
        async function login(event) {
            event.preventDefault();
            const formData = new FormData();
            formData.append('user_id', document.getElementById('user_id').value);
            
            const response = await fetch('/login', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                location.reload();
            } else {
                alert('Login failed: ' + (result.error || 'Unknown error'));
            }
        }
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Forgram Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .stat-item { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .logs { max-height: 400px; overflow-y: auto; }
        .log-entry { padding: 5px; border-bottom: 1px solid #eee; font-size: 12px; }
    </style>
</head>
<body>
    <h1>Forgram Admin Dashboard</h1>
    
    <div class="card">
        <h3>Bot Statistics</h3>
        <div class="stats">
            <div class="stat-item">
                <h4>{{ stats.admin.commands_executed }}</h4>
                <p>Commands Executed</p>
            </div>
            <div class="stat-item">
                <h4>{{ stats.admin.users_banned }}</h4>
                <p>Users Banned</p>
            </div>
            <div class="stat-item">
                <h4>{{ stats.admin.broadcasts_sent }}</h4>
                <p>Broadcasts Sent</p>
            </div>
            <div class="stat-item">
                <h4>{{ stats.total_admins }}</h4>
                <p>Total Admins</p>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h3>Recent Actions</h3>
        <div id="logs" class="logs">
            Loading logs...
        </div>
    </div>
    
    <script>
        async function loadLogs() {
            const response = await fetch('/api/logs?limit=20');
            const logs = await response.json();
            
            const logsDiv = document.getElementById('logs');
            logsDiv.innerHTML = logs.map(log => 
                `<div class="log-entry">
                    <strong>${log.action}</strong> - ${log.datetime} - ${JSON.stringify(log.data)}
                </div>`
            ).join('');
        }
        
        loadLogs();
        setInterval(loadLogs, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""
