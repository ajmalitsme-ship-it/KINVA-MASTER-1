# ============================================
# DATABASE.PY - COMPLETE DATABASE MANAGEMENT
# KINVA MASTER PRO
# ============================================

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from config import Config

logger = logging.getLogger(__name__)

class Database:
    """Complete Database Management System for Kinva Master Pro"""
    
    def __init__(self):
        self.db_path = Config.DATABASE_FILE
        self.conn = None
        self.connect()
        self.init_tables()
    
    def connect(self):
        """Create database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_tables(self):
        """Initialize all database tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                is_premium INTEGER DEFAULT 0,
                premium_expiry TEXT,
                premium_type TEXT DEFAULT 'monthly',
                edits_today INTEGER DEFAULT 0,
                total_edits INTEGER DEFAULT 0,
                last_edit_date TEXT,
                balance REAL DEFAULT 0,
                stars_balance INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Edit history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                edit_type TEXT,
                tool_used TEXT,
                file_type TEXT,
                input_size INTEGER,
                output_size INTEGER,
                processing_time REAL,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                stars_amount INTEGER,
                payment_method TEXT,
                transaction_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                payment_data TEXT,
                plan_type TEXT,
                duration_days INTEGER,
                created_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                data TEXT,
                thumbnail TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                category TEXT,
                data TEXT,
                preview_url TEXT,
                thumbnail TEXT,
                created_by INTEGER,
                is_public INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback TEXT,
                rating INTEGER,
                category TEXT,
                status TEXT DEFAULT 'pending',
                admin_response TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                user_id INTEGER,
                session_id TEXT,
                data TEXT,
                ip_address TEXT,
                created_at TEXT
            )
        ''')
        
        # Downloads table (for social media downloads)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                platform TEXT,
                quality TEXT,
                file_size INTEGER,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                reward_amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users(id),
                FOREIGN KEY (referred_id) REFERENCES users(id)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                message TEXT,
                type TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edits_user ON edit_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edits_date ON edit_history(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id)')
        
        self.conn.commit()
        
        # Initialize default settings
        self.init_default_settings()
        
        logger.info("All tables initialized successfully")
    
    def init_default_settings(self):
        """Initialize default system settings"""
        defaults = {
            'bot_name': 'Kinva Master Pro',
            'bot_version': Config.BOT_VERSION,
            'maintenance_mode': 'false',
            'welcome_message': 'Welcome to Kinva Master Pro!',
            'referral_bonus': '10',
            'daily_free_edits': str(Config.FREE_DAILY_EDITS),
            'daily_premium_edits': str(Config.PREMIUM_DAILY_EDITS),
            'min_withdrawal': '10',
            'support_chat': 'https://t.me/kinvasupport',
            'announcement': '',
            'announcement_active': 'false'
        }
        
        for key, value in defaults.items():
            if not self.get_setting(key):
                self.set_setting(key, value)
    
    # ============================================
    # USER MANAGEMENT
    # ============================================
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, 
                    last_name: str = None, referrer_id: int = 0) -> Dict:
        """Create new user"""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (id, username, first_name, last_name, created_at, updated_at, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, now, now, referrer_id))
        
        # Add referral bonus if applicable
        if referrer_id > 0:
            cursor.execute('''
                UPDATE users SET referral_count = referral_count + 1, balance = balance + 5
                WHERE id = ?
            ''', (referrer_id,))
            
            # Record referral
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, created_at)
                VALUES (?, ?, ?)
            ''', (referrer_id, user_id, now))
        
        self.conn.commit()
        
        # Send welcome notification
        self.add_notification(user_id, "Welcome!", f"Welcome to {Config.BOT_NAME}! Start editing now!")
        
        return self.get_user(user_id)
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user data"""
        cursor = self.conn.cursor()
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            values.append(user_id)
            values.append(datetime.now().isoformat())
            query = f"UPDATE users SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
            cursor.execute(query, values)
            self.conn.commit()
            return True
        return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user (admin only)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM edit_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return True
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_user_count(self) -> int:
        """Get total user count"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    
    # ============================================
    # PREMIUM MANAGEMENT
    # ============================================
    
    def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium"""
        user = self.get_user(user_id)
        if user and user['is_premium'] == 1 and user['premium_expiry']:
            try:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                if datetime.now() < expiry:
                    return True
                else:
                    # Expired - downgrade user
                    self.update_user(user_id, is_premium=0, premium_expiry=None)
                    return False
            except:
                return False
        return False
    
    def add_premium(self, user_id: int, days: int = 30, premium_type: str = "monthly") -> bool:
        """Add premium subscription to user"""
        user = self.get_user(user_id)
        now = datetime.now()
        
        if user and user['premium_expiry']:
            try:
                current_expiry = datetime.fromisoformat(user['premium_expiry'])
                if current_expiry > now:
                    new_expiry = current_expiry + timedelta(days=days)
                else:
                    new_expiry = now + timedelta(days=days)
            except:
                new_expiry = now + timedelta(days=days)
        else:
            new_expiry = now + timedelta(days=days)
        
        return self.update_user(
            user_id, 
            is_premium=1, 
            premium_expiry=new_expiry.isoformat(),
            premium_type=premium_type
        )
    
    def remove_premium(self, user_id: int) -> bool:
        """Remove premium from user"""
        return self.update_user(user_id, is_premium=0, premium_expiry=None)
    
    def get_premium_users(self) -> List[Dict]:
        """Get all premium users"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_premium = 1 AND premium_expiry > ?", 
                      (datetime.now().isoformat(),))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_expiring_premium(self, days: int = 7) -> List[Dict]:
        """Get premium users expiring within days"""
        expiry_date = (datetime.now() + timedelta(days=days)).isoformat()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_premium = 1 AND premium_expiry <= ?", (expiry_date,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # EDIT MANAGEMENT
    # ============================================
    
    def increment_edits(self, user_id: int, edit_type: str = "general", tool: str = None,
                        input_size: int = 0, output_size: int = 0, processing_time: float = 0) -> bool:
        """Increment user edit count and record history"""
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        
        # Update edit counts
        if user:
            if user['last_edit_date'] != today:
                self.update_user(user_id, edits_today=1, last_edit_date=today)
            else:
                self.update_user(user_id, edits_today=user['edits_today'] + 1)
            
            self.update_user(user_id, total_edits=user['total_edits'] + 1)
        
        # Record edit history
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO edit_history (user_id, edit_type, tool_used, input_size, output_size, 
                                      processing_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, edit_type, tool, input_size, output_size, processing_time, 'completed', now))
        
        self.conn.commit()
        return True
    
    def can_edit(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can perform an edit"""
        if self.is_premium(user_id):
            return True, "Premium user - unlimited edits"
        
        user = self.get_user(user_id)
        if not user:
            return True, "New user"
        
        today = datetime.now().date().isoformat()
        
        if user['last_edit_date'] != today:
            return True, "First edit of the day"
        
        if user['edits_today'] < Config.FREE_DAILY_EDITS:
            return True, f"Edit {user['edits_today'] + 1}/{Config.FREE_DAILY_EDITS}"
        
        return False, f"Daily limit reached! {Config.FREE_DAILY_EDITS}/{Config.FREE_DAILY_EDITS}"
    
    def get_user_edits_today(self, user_id: int) -> int:
        """Get user's edits today"""
        user = self.get_user(user_id)
        today = datetime.now().date().isoformat()
        
        if user and user['last_edit_date'] == today:
            return user['edits_today']
        return 0
    
    def get_edit_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's edit history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM edit_history WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # TRANSACTION MANAGEMENT
    # ============================================
    
    def add_transaction(self, user_id: int, amount: float, payment_method: str, 
                        transaction_id: str, stars_amount: int = None, 
                        plan_type: str = "monthly", duration_days: int = 30) -> int:
        """Add transaction record"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, stars_amount, payment_method, transaction_id, 
                                      status, plan_type, duration_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, stars_amount, payment_method, transaction_id, 'pending', 
              plan_type, duration_days, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_transaction(self, transaction_id: str) -> bool:
        """Complete transaction and activate premium"""
        cursor = self.conn.cursor()
        
        # Get transaction details
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        tx = cursor.fetchone()
        
        if tx:
            # Update transaction status
            cursor.execute('''
                UPDATE transactions SET status = 'completed', completed_at = ?
                WHERE transaction_id = ?
            ''', (datetime.now().isoformat(), transaction_id))
            
            # Add premium for user
            self.add_premium(tx['user_id'], tx['duration_days'], tx['plan_type'])
            
            # Add stars if applicable
            if tx['stars_amount']:
                user = self.get_user(tx['user_id'])
                self.update_user(tx['user_id'], stars_balance=(user['stars_balance'] + tx['stars_amount']))
            
            # Add notification
            self.add_notification(
                tx['user_id'], 
                "Premium Activated!", 
                f"Your {tx['plan_type']} premium plan has been activated!"
            )
            
            self.conn.commit()
            return True
        
        return False
    
    def fail_transaction(self, transaction_id: str, reason: str = None) -> bool:
        """Mark transaction as failed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE transactions SET status = 'failed', payment_data = ?
            WHERE transaction_id = ?
        ''', (json.dumps({'error': reason}) if reason else None, transaction_id))
        self.conn.commit()
        return True
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get transaction by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's transactions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # PROJECT MANAGEMENT
    # ============================================
    
    def save_project(self, project_id: str, user_id: int, name: str, data: dict, thumbnail: str = None) -> bool:
        """Save user project"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Check if project exists
        existing = self.get_project(project_id, user_id)
        
        if existing:
            cursor.execute('''
                UPDATE projects SET name = ?, data = ?, thumbnail = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            ''', (name, json.dumps(data), thumbnail, now, project_id, user_id))
        else:
            cursor.execute('''
                INSERT INTO projects (id, user_id, name, data, thumbnail, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, user_id, name, json.dumps(data), thumbnail, now, now))
        
        self.conn.commit()
        return True
    
    def get_project(self, project_id: str, user_id: int) -> Optional[Dict]:
        """Get user project"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        row = cursor.fetchone()
        if row:
            project = dict(row)
            project['data'] = json.loads(project['data']) if project['data'] else {}
            return project
        return None
    
    def get_user_projects(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all user projects"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM projects WHERE user_id = ? 
            ORDER BY updated_at DESC LIMIT ?
        ''', (user_id, limit))
        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            project['data'] = json.loads(project['data']) if project['data'] else {}
            projects.append(project)
        return projects
    
    def delete_project(self, project_id: str, user_id: int) -> bool:
        """Delete user project"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        self.conn.commit()
        return True
    
    # ============================================
    # TEMPLATE MANAGEMENT
    # ============================================
    
    def add_template(self, name: str, template_type: str, category: str, data: dict, 
                     preview_url: str = None, created_by: int = 0, is_public: int = 1) -> int:
        """Add new template"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO templates (name, type, category, data, preview_url, created_by, is_public, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, template_type, category, json.dumps(data), preview_url, created_by, is_public, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_templates(self, template_type: str = None, category: str = None, limit: int = 100) -> List[Dict]:
        """Get templates"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM templates WHERE is_public = 1"
        params = []
        
        if template_type:
            query += " AND type = ?"
            params.append(template_type)
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY usage_count DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        templates = []
        for row in cursor.fetchall():
            template = dict(row)
            template['data'] = json.loads(template['data']) if template['data'] else {}
            templates.append(template)
        return templates
    
    def increment_template_usage(self, template_id: int) -> bool:
        """Increment template usage count"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE templates SET usage_count = usage_count + 1 WHERE id = ?", (template_id,))
        self.conn.commit()
        return True
    
    # ============================================
    # FEEDBACK MANAGEMENT
    # ============================================
    
    def add_feedback(self, user_id: int, feedback: str, rating: int, category: str = "general") -> int:
        """Add user feedback"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feedback (user_id, feedback, rating, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, feedback, rating, category, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_feedback(self, status: str = None, limit: int = 100) -> List[Dict]:
        """Get feedback entries"""
        cursor = self.conn.cursor()
        if status:
            cursor.execute('''
                SELECT f.*, u.username, u.first_name 
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.id
                WHERE f.status = ?
                ORDER BY f.created_at DESC LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT f.*, u.username, u.first_name 
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.id
                ORDER BY f.created_at DESC LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def respond_to_feedback(self, feedback_id: int, response: str) -> bool:
        """Respond to feedback"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE feedback SET admin_response = ?, status = 'reviewed'
            WHERE id = ?
        ''', (response, feedback_id))
        self.conn.commit()
        return True
    
    # ============================================
    # NOTIFICATION MANAGEMENT
    # ============================================
    
    def add_notification(self, user_id: int, title: str, message: str, notification_type: str = "info") -> int:
        """Add notification for user"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, type, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, message, notification_type, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """Get user notifications"""
        cursor = self.conn.cursor()
        if unread_only:
            cursor.execute('''
                SELECT * FROM notifications WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM notifications WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        self.conn.commit()
        return True
    
    def mark_all_notifications_read(self, user_id: int) -> bool:
        """Mark all user notifications as read"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return True
    
    def broadcast_notification(self, title: str, message: str, user_ids: List[int] = None) -> int:
        """Broadcast notification to users"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        count = 0
        
        if user_ids:
            for user_id in user_ids:
                cursor.execute('''
                    INSERT INTO notifications (user_id, title, message, type, created_at)
                    VALUES (?, ?, ?, 'broadcast', ?)
                ''', (user_id, title, message, now))
                count += 1
        else:
            # Broadcast to all users
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            for user in users:
                cursor.execute('''
                    INSERT INTO notifications (user_id, title, message, type, created_at)
                    VALUES (?, ?, ?, 'broadcast', ?)
                ''', (user['id'], title, message, now))
                count += 1
        
        self.conn.commit()
        return count
    
    # ============================================
    # SETTINGS MANAGEMENT
    # ============================================
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set system setting"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, now))
        
        self.conn.commit()
        return True
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get system setting"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default
    
    def get_all_settings(self) -> Dict:
        """Get all settings"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    # ============================================
    # ANALYTICS
    # ============================================
    
    def add_analytics(self, event_type: str, user_id: int, data: dict, session_id: str = None, ip: str = None) -> bool:
        """Add analytics event"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO analytics (event_type, user_id, session_id, data, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, user_id, session_id, json.dumps(data), ip, now))
        
        self.conn.commit()
        return True
    
    def get_stats(self) -> Dict:
        """Get overall statistics"""
        cursor = self.conn.cursor()
        
        # User stats
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
        banned_users = cursor.fetchone()[0]
        
        # Edit stats
        cursor.execute("SELECT SUM(total_edits) FROM users")
        total_edits = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM edit_history WHERE date(created_at) = date('now')")
        today_edits = cursor.fetchone()[0]
        
        # Transaction stats
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Feedback stats
        cursor.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "banned_users": banned_users,
            "total_edits": total_edits,
            "today_edits": today_edits,
            "total_revenue": total_revenue,
            "avg_rating": round(avg_rating, 1),
            "premium_percent": round((premium_users / total_users * 100), 1) if total_users > 0 else 0
        }
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily statistics for last N days"""
        cursor = self.conn.cursor()
        stats = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()
            
            cursor.execute('''
                SELECT COUNT(*) FROM users WHERE date(created_at) = ?
            ''', (date,))
            new_users = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM edit_history WHERE date(created_at) = ?
            ''', (date,))
            edits = cursor.fetchone()[0]
            
            stats.append({
                "date": date,
                "new_users": new_users,
                "edits": edits
            })
        
        return stats
    
    # ============================================
    # DOWNLOAD MANAGEMENT
    # ============================================
    
    def add_download(self, user_id: int, url: str, platform: str, quality: str, file_size: int = 0) -> int:
        """Record download"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO downloads (user_id, url, platform, quality, file_size, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        ''', (user_id, url, platform, quality, file_size, now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_download_status(self, download_id: int, status: str, file_size: int = None) -> bool:
        """Update download status"""
        cursor = self.conn.cursor()
        if file_size:
            cursor.execute('''
                UPDATE downloads SET status = ?, file_size = ? WHERE id = ?
            ''', (status, file_size, download_id))
        else:
            cursor.execute('''
                UPDATE downloads SET status = ? WHERE id = ?
            ''', (status, download_id))
        
        self.conn.commit()
        return True
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up old data"""
        cursor = self.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        count = 0
        
        # Clean old edit history
        cursor.execute("DELETE FROM edit_history WHERE created_at < ?", (cutoff,))
        count += cursor.rowcount
        
        # Clean old analytics
        cursor.execute("DELETE FROM analytics WHERE created_at < ?", (cutoff,))
        count += cursor.rowcount
        
        # Clean old notifications (read only)
        cursor.execute("DELETE FROM notifications WHERE is_read = 1 AND created_at < ?", (cutoff,))
        count += cursor.rowcount
        
        self.conn.commit()
        return count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        """Destructor"""
        self.close()


# ============================================
# INITIALIZE DATABASE
# ============================================

db = Database()
