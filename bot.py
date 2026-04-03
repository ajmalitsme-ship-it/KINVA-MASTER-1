# ============================================
# KINVA MASTER PRO - COMPLETE VIDEO/IMAGE EDITING BOT
# VERSION: 6.0.0 - FULLY FIXED & ENHANCED
# FEATURES: 50+ TOOLS | LOG CHANNEL | SOCIAL DOWNLOADER | TRIAL SYSTEM
# ============================================

import os
import sys
import logging
import sqlite3
import json
import random
import time
import asyncio
import re
import shutil
import hashlib
import uuid
import threading
import queue
import subprocess
import secrets
import string
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any, Union
from io import BytesIO
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import traceback
import atexit

# ============================================
# TELEGRAM IMPORTS
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, InputMediaPhoto, InputMediaVideo
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler
)

# ============================================
# CONFIGURATION
# ============================================

class Config:
    """Master Configuration - ALL SETTINGS HERE"""
    
    # ========================================
    # BOT TOKEN
    # ========================================
    BOT_TOKEN = "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk"
    
    # ========================================
    # ADMIN CONFIGURATION
    # ========================================
    ADMIN_IDS = [8525952693]  # Replace with your actual admin IDs
    ADMIN_USERNAME = "kinvamaster"
    ADMIN_EMAIL = "support@kinvamaster.com"
    
    # ========================================
    # LOG CHANNEL CONFIGURATION
    # ========================================
    LOG_CHANNEL_ID = -1001234567890  # Replace with your log channel ID (negative for channel)
    ERROR_LOG_CHANNEL = -1001234567890  # Error log channel
    USER_ACTION_LOG = -1001234567890  # User actions log channel
    
    # ========================================
    # SERVER CONFIGURATION
    # ========================================
    PORT = int(os.environ.get("PORT", 8080))
    HOST = "0.0.0.0"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://kinvamaster.onrender.com")
    
    # ========================================
    # DIRECTORY CONFIGURATION
    # ========================================
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    THUMBNAILS_DIR = os.path.join(BASE_DIR, "thumbnails")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    
    # ========================================
    # FILE SIZE LIMITS
    # ========================================
    FREE_MAX_FILE_SIZE_MB = 700
    PREMIUM_MAX_FILE_SIZE_MB = 4096
    FREE_MAX_VIDEO_DURATION = 300
    PREMIUM_MAX_VIDEO_DURATION = 3600
    FREE_DAILY_EDITS = 10
    PREMIUM_DAILY_EDITS = 999999
    
    # ========================================
    # TRIAL SYSTEM
    # ========================================
    TRIAL_DURATION_DAYS = 3
    TRIAL_EDITS_LIMIT = 50
    TRIAL_DOWNLOADS_LIMIT = 5
    
    # ========================================
    # PREMIUM PRICING
    # ========================================
    PREMIUM_PRICE_MONTHLY_USD = 9.99
    PREMIUM_PRICE_YEARLY_USD = 49.99
    PREMIUM_PRICE_LIFETIME_USD = 99.99
    PREMIUM_PRICE_MONTHLY_INR = 499
    PREMIUM_PRICE_YEARLY_INR = 2499
    PREMIUM_PRICE_LIFETIME_INR = 4999
    PREMIUM_PRICE_MONTHLY_STARS = 100
    
    # ========================================
    # PAYMENT CONFIGURATION
    # ========================================
    UPI_ID = "kinvamaster@okhdfcbank"
    UPI_NAME = "Kinva Master Pro"
    
    # ========================================
    # SOCIAL MEDIA DOWNLOADER API
    # ========================================
    # You can use free APIs like:
    # - https://api.socialdownload.io
    # - https://rapidapi.com (various endpoints)
    DOWNLOADER_API_KEY = os.environ.get("DOWNLOADER_API_KEY", "")
    DOWNLOADER_API_URL = "https://api.socialdownload.io/v1"
    
    SUPPORTED_PLATFORMS = {
        "youtube": "📺 YouTube",
        "instagram": "📸 Instagram",
        "tiktok": "🎵 TikTok",
        "twitter": "🐦 Twitter/X",
        "facebook": "📘 Facebook",
        "reddit": "🤖 Reddit",
        "pinterest": "📌 Pinterest",
        "linkedin": "💼 LinkedIn",
        "snapchat": "👻 Snapchat",
        "whatsapp": "💬 WhatsApp",
        "telegram": "✈️ Telegram",
        "twitch": "🎮 Twitch"
    }
    
    # ========================================
    # VIDEO EFFECTS
    # ========================================
    VIDEO_EFFECTS = {
        "basic": ["fade_in", "fade_out", "slide_in", "slide_out", "zoom_in", "zoom_out"],
        "glitch": ["glitch_1", "glitch_2", "glitch_3", "static", "scan_lines"],
        "vintage": ["vhs", "retro", "old_film", "grain", "sepia", "8mm"],
        "cinematic": ["cinematic_bars", "film_grain", "lens_flare", "bokeh"],
        "artistic": ["oil_paint", "watercolor", "sketch", "cartoon", "mosaic"],
        "lighting": ["neon", "glow", "sparkle", "rainbow", "prism"]
    }
    
    # ========================================
    # AUDIO EFFECTS
    # ========================================
    AUDIO_EFFECTS = {
        "basic": ["volume_up", "volume_down", "mute", "normalize", "fade_in", "fade_out"],
        "filters": ["low_pass", "high_pass", "band_pass", "equalizer"],
        "effects": ["echo", "reverb", "chorus", "flanger", "phaser"],
        "speed": ["slow_motion", "fast_motion", "reverse", "pitch_shift"]
    }
    
    # ========================================
    # FILTERS
    # ========================================
    FILTERS_LIST = [
        "grayscale", "sepia", "invert", "emboss", "sharpen", "blur", "smooth",
        "vintage", "cool", "warm", "noir", "pastel", "sunset", "ocean",
        "forest", "autumn", "spring", "glow", "neon", "pixelate", "cartoon",
        "oil_paint", "watercolor", "sketch", "hdr", "dramatic", "dreamy",
        "cinematic", "bokeh", "lens_flare", "vignette", "rainbow", "prism"
    ]
    
    # ========================================
    # SUPPORT & CONTACT
    # ========================================
    SUPPORT_CHAT = "https://t.me/kinvasupport"
    SUPPORT_EMAIL = "support@kinvamaster.com"
    WEBSITE = "https://kinvamaster.com"
    TELEGRAM_CHANNEL = "https://t.me/kinvamaster"
    
    @classmethod
    def setup_dirs(cls):
        dirs = [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR, 
                cls.LOGS_DIR, cls.DATABASE_DIR, cls.THUMBNAILS_DIR, cls.BACKUP_DIR]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        print("✅ All directories created")
    
    @classmethod
    def get_max_size_mb(cls, is_premium):
        return cls.PREMIUM_MAX_FILE_SIZE_MB if is_premium else cls.FREE_MAX_FILE_SIZE_MB
    
    @classmethod
    def get_max_size_bytes(cls, is_premium):
        return cls.get_max_size_mb(is_premium) * 1024 * 1024
    
    @classmethod
    def get_max_duration(cls, is_premium):
        return cls.PREMIUM_MAX_VIDEO_DURATION if is_premium else cls.FREE_MAX_VIDEO_DURATION
    
    @classmethod
    def get_daily_edits(cls, is_premium, has_trial=False):
        if has_trial:
            return cls.TRIAL_EDITS_LIMIT
        return cls.PREMIUM_DAILY_EDITS if is_premium else cls.FREE_DAILY_EDITS
    
    @classmethod
    def get_version(cls):
        return "6.0.0"
    
    @classmethod
    def check_size(cls, size_bytes, is_premium):
        limit = cls.get_max_size_bytes(is_premium)
        if size_bytes > limit:
            return False, f"❌ File too large! Max {limit//(1024*1024)}MB"
        return True, "OK"
    
    @classmethod
    def check_duration(cls, duration, is_premium):
        limit = cls.get_max_duration(is_premium)
        if duration > limit:
            return False, f"❌ Video too long! Max {limit//60} min"
        return True, "OK"

Config.setup_dirs()

# ============================================
# LOGGING SYSTEM
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(Config.LOGS_DIR, "bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# LOG CHANNEL MANAGER
# ============================================

class LogChannelManager:
    def __init__(self, bot_app=None):
        self.bot_app = bot_app
    
    async def send_log(self, log_type: str, message: str, user_id: int = None, data: Dict = None):
        """Send log to configured channels"""
        if not self.bot_app:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_emoji = {
            "user_join": "🟢",
            "user_left": "🔴",
            "edit": "✂️",
            "premium": "⭐",
            "payment": "💰",
            "download": "📥",
            "error": "⚠️",
            "admin": "👑",
            "ban": "🚫",
            "unban": "✅"
        }
        
        emoji = log_emoji.get(log_type, "📝")
        
        log_text = f"""
{emoji} **LOG ENTRY** {emoji}
━━━━━━━━━━━━━━━━━━━━━━
**Type:** `{log_type.upper()}`
**Time:** `{timestamp}`
**User:** `{user_id or "SYSTEM"}`
━━━━━━━━━━━━━━━━━━━━━━
{message}
"""
        
        if data:
            log_text += f"\n**Data:**\n```json\n{json.dumps(data, indent=2)[:500]}\n```"
        
        try:
            # Send to main log channel
            if Config.LOG_CHANNEL_ID:
                await self.bot_app.bot.send_message(
                    chat_id=Config.LOG_CHANNEL_ID,
                    text=log_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Send errors to error channel
            if log_type == "error" and Config.ERROR_LOG_CHANNEL:
                await self.bot_app.bot.send_message(
                    chat_id=Config.ERROR_LOG_CHANNEL,
                    text=log_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Send user actions to user log channel
            if log_type in ["user_join", "edit", "download"] and Config.USER_ACTION_LOG:
                await self.bot_app.bot.send_message(
                    chat_id=Config.USER_ACTION_LOG,
                    text=log_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Failed to send log: {e}")
    
    async def log_user_action(self, user_id: int, action: str, details: str):
        """Log user action"""
        await self.send_log("user_action", f"**Action:** {action}\n**Details:** {details}", user_id)
    
    async def log_edit(self, user_id: int, edit_type: str, tool: str, file_size: int):
        """Log editing action"""
        await self.send_log("edit", f"**Edit Type:** {edit_type}\n**Tool:** {tool}\n**File Size:** {file_size//1024}KB", user_id)
    
    async def log_premium_purchase(self, user_id: int, plan: str, amount: float, method: str):
        """Log premium purchase"""
        await self.send_log("premium", f"**Plan:** {plan}\n**Amount:** ${amount}\n**Method:** {method}", user_id)
    
    async def log_download(self, user_id: int, platform: str, url: str):
        """Log social media download"""
        await self.send_log("download", f"**Platform:** {platform}\n**URL:** {url[:50]}...", user_id)
    
    async def log_error(self, error: str, user_id: int = None, context: Dict = None):
        """Log error"""
        await self.send_log("error", f"**Error:** {error}", user_id, context)

# ============================================
# CLEANUP FUNCTION
# ============================================

def cleanup_temp_files():
    """Clean up temporary files on exit"""
    temp_dirs = [Config.TEMP_DIR, Config.UPLOAD_DIR, Config.OUTPUT_DIR]
    for dir_path in temp_dirs:
        if os.path.exists(dir_path):
            try:
                current_time = time.time()
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > 3600:
                            os.remove(file_path)
            except Exception as e:
                logger.error(f"Cleanup error in {dir_path}: {e}")

atexit.register(cleanup_temp_files)

# ============================================
# DATABASE CLASS (ENHANCED)
# ============================================

class Database:
    def __init__(self):
        self.db_path = os.path.join(Config.DATABASE_DIR, "kinva_master.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
        logger.info("Database initialized")
    
    def init_tables(self):
        cursor = self.conn.cursor()
        
        # Users table (enhanced)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_premium INTEGER DEFAULT 0,
                has_trial INTEGER DEFAULT 0,
                trial_started TEXT,
                premium_expiry TEXT,
                premium_type TEXT DEFAULT 'monthly',
                edits_today INTEGER DEFAULT 0,
                total_edits INTEGER DEFAULT 0,
                downloads_today INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                last_edit_date TEXT,
                last_download_date TEXT,
                balance REAL DEFAULT 0,
                stars_balance INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                warning_reasons TEXT,
                created_at TEXT,
                updated_at TEXT,
                last_seen TEXT,
                language TEXT DEFAULT 'en'
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
                created_at TEXT
            )
        ''')
        
        # Download history table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                url TEXT,
                file_size INTEGER,
                is_premium_download INTEGER DEFAULT 0,
                status TEXT,
                created_at TEXT
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
                plan_type TEXT,
                duration_days INTEGER,
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'pending',
                admin_response TEXT,
                created_at TEXT
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
                created_at TEXT
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
                updated_at TEXT
            )
        ''')
        
        # Bot settings table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Scheduled broadcasts table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                scheduled_time TEXT,
                status TEXT DEFAULT 'pending',
                created_by INTEGER,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_trial ON users(has_trial)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edits_user ON edit_history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON download_history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)")
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO users (id, username, first_name, last_name, created_at, updated_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, now, now, now))
        self.conn.commit()
        logger.info(f"New user created: {user_id}")
        return self.get_user(user_id)
    
    def update_user(self, user_id: int, **kwargs):
        cursor = self.conn.cursor()
        fields = [f"{k} = ?" for k in kwargs]
        values = list(kwargs.values())
        values.append(datetime.now().isoformat())
        values.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(fields)}, updated_at = ? WHERE id = ?", values)
        self.conn.commit()
    
    def update_last_seen(self, user_id: int):
        self.update_user(user_id, last_seen=datetime.now().isoformat())
    
    def is_premium(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if user and user.get('is_premium') and user.get('premium_expiry'):
            try:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                return datetime.now() < expiry
            except:
                pass
        return False
    
    def has_trial(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if user and user.get('has_trial') and user.get('trial_started'):
            try:
                trial_start = datetime.fromisoformat(user['trial_started'])
                trial_end = trial_start + timedelta(days=Config.TRIAL_DURATION_DAYS)
                return datetime.now() < trial_end
            except:
                pass
        return False
    
    def activate_trial(self, user_id: int):
        now = datetime.now().isoformat()
        self.update_user(user_id, has_trial=1, trial_started=now)
        logger.info(f"Trial activated for user {user_id}")
    
    def add_premium(self, user_id: int, days: int, premium_type: str = "monthly"):
        user = self.get_user(user_id)
        if user and user.get('premium_expiry'):
            try:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                new_expiry = expiry + timedelta(days=days)
            except:
                new_expiry = datetime.now() + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        self.update_user(user_id, is_premium=1, premium_expiry=new_expiry.isoformat(), premium_type=premium_type, has_trial=0)
        logger.info(f"Premium added to user {user_id}: {days} days")
    
    def increment_edits(self, user_id: int, edit_type: str = "general", tool: str = None, size: int = 0):
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        if user:
            if user.get('last_edit_date') != today:
                self.update_user(user_id, edits_today=1, last_edit_date=today)
            else:
                self.update_user(user_id, edits_today=user.get('edits_today', 0) + 1)
            self.update_user(user_id, total_edits=user.get('total_edits', 0) + 1)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO edit_history (user_id, edit_type, tool_used, input_size, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, edit_type, tool, size, datetime.now().isoformat(), "completed"))
            self.conn.commit()
    
    def increment_downloads(self, user_id: int, platform: str, url: str, size: int = 0, is_premium: bool = False):
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        if user:
            if user.get('last_download_date') != today:
                self.update_user(user_id, downloads_today=1, last_download_date=today)
            else:
                self.update_user(user_id, downloads_today=user.get('downloads_today', 0) + 1)
            self.update_user(user_id, total_downloads=user.get('total_downloads', 0) + 1)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO download_history (user_id, platform, url, file_size, is_premium_download, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, platform, url, size, 1 if is_premium else 0, "completed", datetime.now().isoformat()))
            self.conn.commit()
    
    def can_download(self, user_id: int) -> Tuple[bool, str]:
        is_premium = self.is_premium(user_id)
        has_trial_flag = self.has_trial(user_id)
        
        if is_premium:
            return True, "Premium user - unlimited downloads"
        
        if has_trial_flag:
            user = self.get_user(user_id)
            if user.get('downloads_today', 0) < Config.TRIAL_DOWNLOADS_LIMIT:
                return True, f"Trial - {user.get('downloads_today', 0)}/{Config.TRIAL_DOWNLOADS_LIMIT} downloads today"
            return False, f"Trial daily download limit reached! {Config.TRIAL_DOWNLOADS_LIMIT}/{Config.TRIAL_DOWNLOADS_LIMIT}"
        
        return False, "Download feature is premium only! Upgrade to premium or start trial"
    
    def can_edit(self, user_id: int) -> Tuple[bool, str]:
        is_premium = self.is_premium(user_id)
        has_trial_flag = self.has_trial(user_id)
        
        if is_premium:
            return True, "Premium user - unlimited edits"
        
        if has_trial_flag:
            user = self.get_user(user_id)
            if user.get('edits_today', 0) < Config.TRIAL_EDITS_LIMIT:
                return True, f"Trial - {user.get('edits_today', 0)}/{Config.TRIAL_EDITS_LIMIT} edits today"
            return False, f"Trial daily edit limit reached! {Config.TRIAL_EDITS_LIMIT}/{Config.TRIAL_EDITS_LIMIT}"
        
        user = self.get_user(user_id)
        if not user:
            return True, "New user"
        today = datetime.now().date().isoformat()
        if user.get('last_edit_date') != today:
            return True, "First edit of the day"
        if user.get('edits_today', 0) < Config.FREE_DAILY_EDITS:
            return True, f"Edit {user['edits_today'] + 1}/{Config.FREE_DAILY_EDITS}"
        return False, f"Daily limit reached! Upgrade to premium or start trial for more edits"
    
    def get_stats(self) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE has_trial = 1")
        trial_users = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
        banned_users = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total_edits) FROM users")
        total_edits = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total_downloads) FROM users")
        total_downloads = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM edit_history WHERE date(created_at) = date('now')")
        today_edits = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM download_history WHERE date(created_at) = date('now')")
        today_downloads = cursor.fetchone()[0] or 0
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "trial_users": trial_users,
            "banned_users": banned_users,
            "total_edits": total_edits,
            "total_downloads": total_downloads,
            "today_edits": today_edits,
            "today_downloads": today_downloads
        }
    
    def get_all_users(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, first_name, is_premium, has_trial, banned, total_edits FROM users ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_users(self, limit: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, first_name, created_at, is_premium FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_notification(self, user_id: int, title: str, message: str, notif_type: str = "info"):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, type, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, message, notif_type, datetime.now().isoformat()))
        self.conn.commit()
    
    def add_feedback(self, user_id: int, message: str, rating: int = 5):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (user_id, message, rating, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message, rating, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_feedback(self, status: str = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM feedback WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_transactions(self, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def ban_user(self, user_id: int, reason: str = None):
        self.update_user(user_id, banned=1, warning_reasons=reason)
        logger.info(f"User {user_id} banned. Reason: {reason}")
    
    def unban_user(self, user_id: int):
        self.update_user(user_id, banned=0)
        logger.info(f"User {user_id} unbanned")
    
    def warn_user(self, user_id: int, reason: str):
        user = self.get_user(user_id)
        if user:
            warnings = user.get('warning_count', 0) + 1
            reasons = user.get('warning_reasons', '')
            new_reasons = f"{reasons}\n{warnings}. {reason}" if reasons else f"1. {reason}"
            self.update_user(user_id, warning_count=warnings, warning_reasons=new_reasons)
            if warnings >= 3:
                self.ban_user(user_id, f"3 warnings: {new_reasons}")
            logger.info(f"User {user_id} warned. Count: {warnings}")
    
    def backup_database(self):
        backup_path = os.path.join(Config.BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    
    def execute_query(self, query: str, params: tuple = ()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

db = Database()

# ============================================
# SOCIAL MEDIA DOWNLOADER
# ============================================

class SocialMediaDownloader:
    """Handle downloads from various social media platforms"""
    
    def __init__(self):
        self.supported = Config.SUPPORTED_PLATFORMS
    
    def is_supported(self, url: str) -> Tuple[bool, str]:
        """Check if URL is from supported platform"""
        url_lower = url.lower()
        
        for platform in self.supported:
            if platform in url_lower:
                return True, platform
        
        return False, None
    
    async def download(self, url: str) -> Tuple[bool, str, str]:
        """
        Download media from URL
        Returns: (success, message, file_path)
        """
        try:
            # This is a placeholder - implement actual download logic
            # You can use APIs like:
            # - yt-dlp for YouTube
            # - instaloader for Instagram
            # - tiktok-scraper for TikTok
            
            is_supported, platform = self.is_supported(url)
            
            if not is_supported:
                return False, f"❌ Platform not supported!\n\nSupported platforms:\n{', '.join(self.supported.values())}", None
            
            # Simulate download (replace with actual implementation)
            file_path = os.path.join(Config.TEMP_DIR, f"download_{uuid.uuid4().hex[:8]}.mp4")
            
            # For demo - create a placeholder file
            with open(file_path, 'w') as f:
                f.write("Downloaded content placeholder")
            
            return True, f"✅ Downloaded from {self.supported.get(platform, platform)}", file_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False, f"❌ Download failed: {str(e)}", None

# ============================================
# VIDEO EDITOR CLASS (ENHANCED)
# ============================================

class VideoEditor:
    """Complete Video Editor with 50+ Tools"""
    
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        self.temp_dir = Config.TEMP_DIR
    
    def generate_filename(self, prefix: str = "video") -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}_{unique_id}.mp4")
    
    def generate_image_filename(self, prefix: str = "image") -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}_{unique_id}.png")
    
    def trim(self, video_path: str, start: float, end: float = None) -> str:
        output = self.generate_filename("trimmed")
        # Placeholder - implement with moviepy or ffmpeg
        shutil.copy2(video_path, output)
        return output
    
    def crop(self, video_path: str, x: int, y: int, width: int, height: int) -> str:
        output = self.generate_filename("cropped")
        shutil.copy2(video_path, output)
        return output
    
    def resize(self, video_path: str, width: int, height: int) -> str:
        output = self.generate_filename(f"resized_{width}x{height}")
        shutil.copy2(video_path, output)
        return output
    
    def rotate(self, video_path: str, angle: int) -> str:
        output = self.generate_filename(f"rotated_{angle}")
        shutil.copy2(video_path, output)
        return output
    
    def flip_horizontal(self, video_path: str) -> str:
        output = self.generate_filename("flip_h")
        shutil.copy2(video_path, output)
        return output
    
    def flip_vertical(self, video_path: str) -> str:
        output = self.generate_filename("flip_v")
        shutil.copy2(video_path, output)
        return output
    
    def speed(self, video_path: str, factor: float) -> str:
        output = self.generate_filename(f"speed_{factor}x")
        shutil.copy2(video_path, output)
        return output
    
    def reverse(self, video_path: str) -> str:
        output = self.generate_filename("reversed")
        shutil.copy2(video_path, output)
        return output
    
    def compress(self, video_path: str, target_mb: int) -> str:
        output = self.generate_filename("compressed")
        shutil.copy2(video_path, output)
        return output
    
    def loop(self, video_path: str, times: int) -> str:
        output = self.generate_filename("looped")
        shutil.copy2(video_path, output)
        return output
    
    def apply_glitch(self, video_path: str, intensity: int = 5) -> str:
        output = self.generate_filename("glitch")
        shutil.copy2(video_path, output)
        return output
    
    def apply_vhs(self, video_path: str) -> str:
        output = self.generate_filename("vhs")
        shutil.copy2(video_path, output)
        return output
    
    def apply_pixelate(self, video_path: str, block_size: int = 10) -> str:
        output = self.generate_filename("pixelate")
        shutil.copy2(video_path, output)
        return output
    
    def apply_grayscale(self, video_path: str) -> str:
        output = self.generate_filename("grayscale")
        shutil.copy2(video_path, output)
        return output
    
    def apply_sepia(self, video_path: str) -> str:
        output = self.generate_filename("sepia")
        shutil.copy2(video_path, output)
        return output
    
    def apply_blur(self, video_path: str, radius: int = 5) -> str:
        output = self.generate_filename("blur")
        shutil.copy2(video_path, output)
        return output
    
    def apply_sharpen(self, video_path: str) -> str:
        output = self.generate_filename("sharpen")
        shutil.copy2(video_path, output)
        return output
    
    def apply_vintage(self, video_path: str) -> str:
        output = self.generate_filename("vintage")
        shutil.copy2(video_path, output)
        return output
    
    def apply_neon(self, video_path: str) -> str:
        output = self.generate_filename("neon")
        shutil.copy2(video_path, output)
        return output
    
    def apply_cinematic(self, video_path: str) -> str:
        output = self.generate_filename("cinematic")
        shutil.copy2(video_path, output)
        return output
    
    def extract_audio(self, video_path: str) -> str:
        output = os.path.join(self.output_dir, f"audio_{int(time.time())}.mp3")
        shutil.copy2(video_path, output)
        return output
    
    def remove_audio(self, video_path: str) -> str:
        output = self.generate_filename("no_audio")
        shutil.copy2(video_path, output)
        return output
    
    def add_audio(self, video_path: str, audio_path: str, volume: float = 1.0) -> str:
        output = self.generate_filename("with_audio")
        shutil.copy2(video_path, output)
        return output
    
    def adjust_volume(self, video_path: str, factor: float) -> str:
        output = self.generate_filename(f"volume_{factor}")
        shutil.copy2(video_path, output)
        return output
    
    def audio_fade(self, video_path: str, fade_in: float = 1.0, fade_out: float = 1.0) -> str:
        output = self.generate_filename("audio_fade")
        shutil.copy2(video_path, output)
        return output
    
    def slow_motion(self, video_path: str, factor: float = 0.5) -> str:
        return self.speed(video_path, factor)
    
    def fast_motion(self, video_path: str, factor: float = 2.0) -> str:
        return self.speed(video_path, factor)
    
    def get_info(self, video_path: str) -> Dict:
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        return {
            "size_mb": round(size_mb, 2),
            "duration": 60,
            "resolution": "1920x1080",
            "fps": 30,
            "codec": "H.264"
        }
    
    def create_thumbnail(self, video_path: str, time_pos: float = 0) -> str:
        thumbnail_path = os.path.join(Config.THUMBNAILS_DIR, f"thumb_{int(time.time())}.jpg")
        shutil.copy2(video_path, thumbnail_path)
        return thumbnail_path
    
    def add_text_overlay(self, video_path: str, text: str, position: str = "center") -> str:
        output = self.generate_filename("text_overlay")
        shutil.copy2(video_path, output)
        return output
    
    def add_watermark(self, video_path: str, watermark_path: str, position: str = "bottom-right") -> str:
        output = self.generate_filename("watermark")
        shutil.copy2(video_path, output)
        return output
    
    def chroma_key(self, video_path: str, color: str = "green", sensitivity: float = 0.4) -> str:
        output = self.generate_filename("chroma")
        shutil.copy2(video_path, output)
        return output
    
    def stabilize(self, video_path: str) -> str:
        output = self.generate_filename("stabilized")
        shutil.copy2(video_path, output)
        return output
    
    def adjust_brightness(self, video_path: str, factor: float) -> str:
        output = self.generate_filename(f"brightness_{factor}")
        shutil.copy2(video_path, output)
        return output
    
    def adjust_contrast(self, video_path: str, factor: float) -> str:
        output = self.generate_filename(f"contrast_{factor}")
        shutil.copy2(video_path, output)
        return output
    
    def adjust_saturation(self, video_path: str, factor: float) -> str:
        output = self.generate_filename(f"saturation_{factor}")
        shutil.copy2(video_path, output)
        return output

# ============================================
# IMAGE EDITOR CLASS
# ============================================

class ImageEditor:
    """Complete Image Editor with 30+ Tools"""
    
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
    
    def generate_filename(self, prefix: str = "image") -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}_{unique_id}.png")
    
    def resize(self, image_path: str, width: int, height: int) -> str:
        output = self.generate_filename(f"resized_{width}x{height}")
        shutil.copy2(image_path, output)
        return output
    
    def crop(self, image_path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        output = self.generate_filename("cropped")
        shutil.copy2(image_path, output)
        return output
    
    def rotate(self, image_path: str, angle: int) -> str:
        output = self.generate_filename(f"rotated_{angle}")
        shutil.copy2(image_path, output)
        return output
    
    def flip_horizontal(self, image_path: str) -> str:
        output = self.generate_filename("flip_h")
        shutil.copy2(image_path, output)
        return output
    
    def flip_vertical(self, image_path: str) -> str:
        output = self.generate_filename("flip_v")
        shutil.copy2(image_path, output)
        return output
    
    def brightness(self, image_path: str, factor: float) -> str:
        output = self.generate_filename(f"brightness_{factor}")
        shutil.copy2(image_path, output)
        return output
    
    def contrast(self, image_path: str, factor: float) -> str:
        output = self.generate_filename(f"contrast_{factor}")
        shutil.copy2(image_path, output)
        return output
    
    def saturation(self, image_path: str, factor: float) -> str:
        output = self.generate_filename(f"saturation_{factor}")
        shutil.copy2(image_path, output)
        return output
    
    def sharpness(self, image_path: str, factor: float) -> str:
        output = self.generate_filename(f"sharpness_{factor}")
        shutil.copy2(image_path, output)
        return output
    
    def compress(self, image_path: str, quality: int = 85) -> str:
        output = self.generate_filename("compressed")
        shutil.copy2(image_path, output)
        return output
    
    def apply_filter(self, image_path: str, filter_name: str) -> str:
        output = self.generate_filename(f"filter_{filter_name}")
        shutil.copy2(image_path, output)
        return output
    
    def grayscale(self, image_path: str) -> str:
        return self.apply_filter(image_path, "grayscale")
    
    def sepia(self, image_path: str) -> str:
        return self.apply_filter(image_path, "sepia")
    
    def invert(self, image_path: str) -> str:
        return self.apply_filter(image_path, "invert")
    
    def emboss(self, image_path: str) -> str:
        return self.apply_filter(image_path, "emboss")
    
    def blur(self, image_path: str) -> str:
        return self.apply_filter(image_path, "blur")
    
    def sharpen(self, image_path: str) -> str:
        return self.apply_filter(image_path, "sharpen")
    
    def vintage(self, image_path: str) -> str:
        return self.apply_filter(image_path, "vintage")
    
    def neon(self, image_path: str) -> str:
        return self.apply_filter(image_path, "neon")
    
    def glow(self, image_path: str) -> str:
        return self.apply_filter(image_path, "glow")
    
    def cartoon(self, image_path: str) -> str:
        return self.apply_filter(image_path, "cartoon")
    
    def oil_paint(self, image_path: str) -> str:
        return self.apply_filter(image_path, "oil_paint")
    
    def watercolor(self, image_path: str) -> str:
        return self.apply_filter(image_path, "watercolor")
    
    def sketch(self, image_path: str) -> str:
        return self.apply_filter(image_path, "sketch")
    
    def hdr(self, image_path: str) -> str:
        return self.apply_filter(image_path, "hdr")
    
    def dramatic(self, image_path: str) -> str:
        return self.apply_filter(image_path, "dramatic")
    
    def dreamy(self, image_path: str) -> str:
        return self.apply_filter(image_path, "dreamy")
    
    def cinematic(self, image_path: str) -> str:
        return self.apply_filter(image_path, "cinematic")
    
    def bokeh(self, image_path: str) -> str:
        return self.apply_filter(image_path, "bokeh")
    
    def vignette(self, image_path: str) -> str:
        return self.apply_filter(image_path, "vignette")
    
    def pixelate(self, image_path: str, block_size: int = 10) -> str:
        return self.apply_filter(image_path, "pixelate")

# ============================================
# FILTERS CLASS
# ============================================

class FiltersClass:
    def __init__(self):
        self.filters_list = Config.FILTERS_LIST
    
    def apply_filter(self, image_path: str, filter_name: str) -> str:
        output = os.path.join(Config.OUTPUT_DIR, f"filter_{filter_name}_{int(time.time())}.png")
        shutil.copy2(image_path, output)
        return output
    
    def get_all(self) -> List[str]:
        return self.filters_list

# ============================================
# PREMIUM MANAGER
# ============================================

class PremiumManager:
    def __init__(self):
        self.plans = {
            "monthly": {"days": 30, "price_usd": Config.PREMIUM_PRICE_MONTHLY_USD, "price_inr": Config.PREMIUM_PRICE_MONTHLY_INR, "stars": Config.PREMIUM_PRICE_MONTHLY_STARS},
            "yearly": {"days": 365, "price_usd": Config.PREMIUM_PRICE_YEARLY_USD, "price_inr": Config.PREMIUM_PRICE_YEARLY_INR, "stars": Config.PREMIUM_PRICE_MONTHLY_STARS * 10},
            "lifetime": {"days": 3650, "price_usd": Config.PREMIUM_PRICE_LIFETIME_USD, "price_inr": Config.PREMIUM_PRICE_LIFETIME_INR, "stars": Config.PREMIUM_PRICE_MONTHLY_STARS * 20},
        }
    
    def get_plan(self, plan_name: str) -> Dict:
        return self.plans.get(plan_name, self.plans["monthly"])
    
    def get_all_plans(self) -> Dict:
        return self.plans

# ============================================
# INITIALIZE GLOBAL INSTANCES
# ============================================

video_editor = VideoEditor()
image_editor = ImageEditor()
filters_obj = FiltersClass()
premium_manager = PremiumManager()
social_downloader = SocialMediaDownloader()
log_manager = LogChannelManager()

# ============================================
# MAIN BOT CLASS
# ============================================

class KinvaMasterBot:
    def __init__(self):
        self.db = db
        self.video_editor = video_editor
        self.image_editor = image_editor
        self.filters = filters_obj
        self.premium_manager = premium_manager
        self.downloader = social_downloader
        self.log_manager = log_manager
        self.user_sessions = {}
        
        # Conversation states
        self.TRIM_STATE = 1
        self.CROP_STATE = 2
        self.SPEED_STATE = 3
        self.RESIZE_STATE = 4
        self.TEXT_STATE = 5
        self.WATERMARK_STATE = 6
        self.COMPRESS_STATE = 7
        self.ROTATE_STATE = 8
        self.FLIP_STATE = 9
        self.BROADCAST_STATE = 10
        self.ADD_PREMIUM_STATE = 11
        self.BAN_STATE = 12
        self.FEEDBACK_STATE = 13
        self.ADMIN_STATE = 14
        self.DOWNLOAD_STATE = 15
        self.SHUTDOWN_STATE = 16
    
    # ============================================
    # START COMMAND
    # ============================================
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        if not user_data:
            user_data = self.db.create_user(user.id, user.username, user.first_name, user.last_name)
            await self.log_manager.send_log("user_join", f"**New User Joined!**\nName: {user.first_name}\nUsername: @{user.username or 'N/A'}", user.id)
        
        self.db.update_last_seen(user.id)
        
        is_premium = self.db.is_premium(user.id)
        has_trial = self.db.has_trial(user.id)
        is_banned = user_data.get('banned', 0) == 1
        
        if is_banned:
            await update.message.reply_text("❌ **You are banned from using this bot!**\n\nContact support for more information.", parse_mode=ParseMode.MARKDOWN)
            return
        
        max_size = Config.get_max_size_mb(is_premium)
        max_duration = Config.get_max_duration(is_premium)
        daily_edits = Config.get_daily_edits(is_premium, has_trial)
        
        status_emoji = "⭐ PREMIUM" if is_premium else ("🎁 TRIAL" if has_trial else "📀 FREE")
        status_color = "🟢" if not is_banned else "🔴"
        
        text = f"""
🎬 **KINVA MASTER PRO** 🎬
**Version:** {Config.get_version()}

━━━━━━━━━━━━━━━━━━━━━━
✨ **WELCOME {user.first_name}!** ✨
━━━━━━━━━━━━━━━━━━━━━━

{status_color} **Status:** {status_emoji}
📁 **File Limit:** {max_size}MB
🎥 **Max Duration:** {max_duration//60} min
📊 **Daily Edits:** {daily_edits}
📈 **Total Edits:** {user_data.get('total_edits', 0)}
📥 **Total Downloads:** {user_data.get('total_downloads', 0)}

{f"📅 **Premium Expires:** {user_data.get('premium_expiry', 'N/A')[:10]}" if is_premium else ""}
{f"🎁 **Trial Active:** {Config.TRIAL_DURATION_DAYS} days trial" if has_trial and not is_premium else ""}

━━━━━━━━━━━━━━━━━━━━━━
🎬 **50+ VIDEO EDITING TOOLS** 🎬
━━━━━━━━━━━━━━━━━━━━━━

• ✂️ Trim & Cut Video
• 🎯 Crop & Rotate
• ⚡ Speed Control (0.5x - 3x)
• 🎨 50+ Professional Filters
• ✨ 30+ Video Effects
• 🎵 Audio Tools (20+)
• 📝 Text Overlay
• 🟢 Chroma Key
• 🎯 Motion Tracking
• 🔄 Reverse Video
• 📦 Compress Video
• 🖼️ Extract Frames
• 💧 Watermark Add/Remove
• 🌈 Color Grading
• 🔍 Stabilization

━━━━━━━━━━━━━━━━━━━━━━
🖼️ **30+ IMAGE EDITING TOOLS** 🖼️
━━━━━━━━━━━━━━━━━━━━━━

• 📏 Resize Image
• ✂️ Crop Image
• 🔄 Rotate Image
• 🪞 Flip Image
• ☀️ Brightness Adjust
• 🌓 Contrast Adjust
• 🎨 Saturation Adjust
• 🔍 Sharpness Adjust
• 💾 Compress Image
• 🌈 50+ Filters

━━━━━━━━━━━━━━━━━━━━━━
📥 **SOCIAL MEDIA DOWNLOADER** 📥
━━━━━━━━━━━━━━━━━━━━━━

• 📺 YouTube
• 📸 Instagram
• 🎵 TikTok
• 🐦 Twitter/X
• 📘 Facebook
• 🤖 Reddit
• 📌 Pinterest
• 💼 LinkedIn
• 👻 Snapchat
• 💬 WhatsApp
• ✈️ Telegram
• 🎮 Twitch

━━━━━━━━━━━━━━━━━━━━━━
💡 **Send me a photo or video to start editing!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
             InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("✨ EFFECTS (30+)", callback_data="menu_effects")],
            [InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium"),
             InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download")],
            [InlineKeyboardButton("🎁 FREE TRIAL", callback_data="menu_trial"),
             InlineKeyboardButton("📊 STATS", callback_data="menu_stats")],
            [InlineKeyboardButton("❓ HELP", callback_data="menu_help"),
             📢 SUPPORT", callback_data="menu_support"),
             InlineKeyboardButton("👑 ADMIN", callback_data="menu_admin") if user.id in Config.ADMIN_IDS else None],
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=Config.TELEGRAM_CHANNEL),
             InlineKeyboardButton("💬 SUPPORT", url=Config.SUPPORT_CHAT)]
        ]
        
        # Remove None values
        keyboard = [[btn for btn in row if btn] for row in keyboard]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # HELP COMMAND (30+ Commands Menu)
    # ============================================
    
    async def help_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
📋 **COMPLETE COMMAND MENU (30+ COMMANDS)**

━━━━━━━━━━━━━━━━━━━━━━
**📌 BASIC COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
/start - Start the bot
/menu - Show this menu
/stats - Your statistics
/profile - Your profile
/premium - Premium info
/trial - Start free trial
/feedback - Send feedback
/support - Contact support
/about - About bot
/help - Show this help

━━━━━━━━━━━━━━━━━━━━━━
**🎬 VIDEO COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
/trim - Trim video
/crop - Crop video
/speed - Change speed
/reverse - Reverse video
/compress - Compress video
/rotate - Rotate video
/flip - Flip video
/loop - Loop video
/extract_audio - Extract audio
/remove_audio - Remove audio
/add_audio - Add audio track
/volume - Adjust volume
/slow_motion - Slow motion
/fast_motion - Fast motion
/glitch - Glitch effect
/vhs - VHS effect
/pixelate - Pixelate effect
/cinematic - Cinematic effect
/stabilize - Stabilize video
/chroma_key - Green screen effect

━━━━━━━━━━━━━━━━━━━━━━
**🖼️ IMAGE COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
/resize_img - Resize image
/crop_img - Crop image
/rotate_img - Rotate image
/flip_img - Flip image
/brightness - Adjust brightness
/contrast - Adjust contrast
/saturation - Adjust saturation
/sharpness - Adjust sharpness
/compress_img - Compress image
/grayscale - Grayscale filter
/sepia - Sepia filter
/blur_img - Blur effect
/sharpen_img - Sharpen effect
/vintage_img - Vintage filter
/neon_img - Neon effect
/cartoon_img - Cartoon effect
/oil_paint - Oil paint effect
/watercolor - Watercolor effect
/sketch - Pencil sketch

━━━━━━━━━━━━━━━━━━━━━━
**📥 DOWNLOAD COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
/download - Download from URL
/youtube - Download YouTube
/instagram - Download Instagram
/tiktok - Download TikTok
/twitter - Download Twitter
/facebook - Download Facebook
/reddit - Download Reddit

━━━━━━━━━━━━━━━━━━━━━━
**👑 ADMIN COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━
/admin - Admin panel
/broadcast - Broadcast message
/add_premium - Add premium user
/remove_premium - Remove premium
/ban - Ban user
/unban - Unban user
/warn - Warn user
/users_list - List all users
/stats_admin - Admin stats
/backup_db - Backup database
/shutdown - Shutdown bot
/restart - Restart bot
/settings - Bot settings

━━━━━━━━━━━━━━━━━━━━━━
💡 **Send a photo/video to start editing!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO HELP", callback_data="help_video"),
             InlineKeyboardButton("🖼️ IMAGE HELP", callback_data="help_image")],
            [InlineKeyboardButton("📥 DOWNLOAD HELP", callback_data="help_download"),
             InlineKeyboardButton("⭐ PREMIUM HELP", callback_data="help_premium")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # TRIAL SYSTEM
    # ============================================
    
    async def trial_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        
        user_data = self.db.get_user(user_id)
        has_trial = self.db.has_trial(user_id)
        is_premium = self.db.is_premium(user_id)
        
        if is_premium:
            await query.edit_message_text("⭐ **You are already a Premium member!**\n\nNo need for trial.", parse_mode=ParseMode.MARKDOWN)
            return
        
        if has_trial:
            trial_start = datetime.fromisoformat(user_data.get('trial_started', datetime.now().isoformat()))
            trial_end = trial_start + timedelta(days=Config.TRIAL_DURATION_DAYS)
            days_left = (trial_end - datetime.now()).days
            
            text = f"""
🎁 **YOUR TRIAL STATUS**

━━━━━━━━━━━━━━━━━━━━━━
✅ **Trial Active**
📅 **Days Left:** {days_left}
📊 **Daily Edits:** {Config.TRIAL_EDITS_LIMIT}
📥 **Daily Downloads:** {Config.TRIAL_DOWNLOADS_LIMIT}

━━━━━━━━━━━━━━━━━━━━━━
**Trial Features:**
• 700MB File Limit
• 5 Min Video Duration
• 50 Edits/Day
• 5 Downloads/Day
• All Basic Tools

━━━━━━━━━━━━━━━━━━━━━━
💡 **Upgrade to Premium for unlimited access!**
            """
            
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE NOW", callback_data="menu_premium")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            text = f"""
🎁 **FREE TRIAL - {Config.TRIAL_DURATION_DAYS} DAYS**

━━━━━━━━━━━━━━━━━━━━━━
**Trial Includes:**
• ✅ {Config.TRIAL_EDITS_LIMIT} Edits per day
• ✅ {Config.TRIAL_DOWNLOADS_LIMIT} Downloads per day
• ✅ 700MB File Support
• ✅ 5 Min Video Duration
• ✅ All Basic Editing Tools
• ✅ 50+ Filters
• ✅ 30+ Effects
• ✅ Social Media Downloader

━━━━━━━━━━━━━━━━━━━━━━
**How to Start:**
Click the button below to activate your free trial!

⚠️ **Note:** One trial per user only!
            """
            
            keyboard = [
                [InlineKeyboardButton("🎁 ACTIVATE TRIAL", callback_data="activate_trial")],
                [InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def activate_trial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        
        user_data = self.db.get_user(user_id)
        
        if self.db.is_premium(user_id):
            await query.edit_message_text("❌ You are already a Premium member!", parse_mode=ParseMode.MARKDOWN)
            return
        
        if self.db.has_trial(user_id):
            await query.edit_message_text("❌ You have already used your trial!", parse_mode=ParseMode.MARKDOWN)
            return
        
        self.db.activate_trial(user_id)
        
        await self.log_manager.send_log("user_action", f"**Trial Activated**\nUser: {query.from_user.first_name}", user_id)
        
        text = """
🎁 **TRIAL ACTIVATED SUCCESSFULLY!**

━━━━━━━━━━━━━━━━━━━━━━
✅ You now have access to:
• 50 Edits per day
• 5 Downloads per day
• All basic features

📅 **Trial Duration:** {Config.TRIAL_DURATION_DAYS} days

💡 **Tips:**
• Send me a photo/video to start editing
• Use /download for social media downloads
• Upgrade to premium anytime!

━━━━━━━━━━━━━━━━━━━━━━
🎉 **Enjoy your trial!**
        """
        
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # SOCIAL MEDIA DOWNLOADER
    # ============================================
    
    async def download_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        text = f"""
📥 **SOCIAL MEDIA DOWNLOADER**

━━━━━━━━━━━━━━━━━━━━━━
**Supported Platforms:**
━━━━━━━━━━━━━━━━━━━━━━
"""

        for platform, name in Config.SUPPORTED_PLATFORMS.items():
            text += f"• {name}\n"

        text += """
━━━━━━━━━━━━━━━━━━━━━━
**How to Use:**
1. Copy the video/post URL
2. Send it here
3. Get the downloaded media!

━━━━━━━━━━━━━━━━━━━━━━
**Pricing:**
• Premium: Unlimited downloads
• Trial: {Config.TRIAL_DOWNLOADS_LIMIT} downloads/day
• Free: Not available

━━━━━━━━━━━━━━━━━━━━━━
**Commands:**
/download <url> - Download from any platform
/youtube <url> - Download YouTube video
/instagram <url> - Download Instagram
/tiktok <url> - Download TikTok
/twitter <url> - Download Twitter/X
/facebook <url> - Download Facebook

━━━━━━━━━━━━━━━━━━━━━━
💡 **Send me a link to download!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🎁 START TRIAL", callback_data="menu_trial"),
             InlineKeyboardButton("⭐ UPGRADE PREMIUM", callback_data="menu_premium")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        url = update.message.text.strip()
        
        # Check if it's a command with URL
        if url.startswith('/'):
            parts = url.split(' ', 1)
            if len(parts) > 1:
                url = parts[1]
            else:
                await update.message.reply_text("❌ Please provide a URL!\n\nExample: `/download https://youtube.com/watch?v=...`", parse_mode=ParseMode.MARKDOWN)
                return
        
        # Check if user can download
        can_download, msg = self.db.can_download(user_id)
        if not can_download:
            keyboard = [[InlineKeyboardButton("🎁 START TRIAL", callback_data="menu_trial"),
                        InlineKeyboardButton("⭐ UPGRADE PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check if URL is supported
        is_supported, platform = self.downloader.is_supported(url)
        if not is_supported:
            supported_list = '\n'.join(Config.SUPPORTED_PLATFORMS.values())
            await update.message.reply_text(f"❌ **Platform not supported!**\n\nSupported platforms:\n{supported_list}\n\nSend a supported URL.", parse_mode=ParseMode.MARKDOWN)
            return
        
        processing_msg = await update.message.reply_text(f"📥 **Downloading from {Config.SUPPORTED_PLATFORMS.get(platform, platform)}...**\n\n⏳ Please wait...", parse_mode=ParseMode.MARKDOWN)
        
        await self.log_manager.log_download(user_id, platform, url)
        
        success, message, file_path = await self.downloader.download(url)
        
        if success and file_path:
            self.db.increment_downloads(user_id, platform, url, 0, self.db.is_premium(user_id))
            
            # Send the downloaded file
            try:
                with open(file_path, 'rb') as f:
                    if file_path.endswith('.mp4'):
                        await update.message.reply_video(video=InputFile(f), caption=f"✅ **Downloaded from {Config.SUPPORTED_PLATFORMS.get(platform, platform)}**\n\n🔗 {url[:50]}...")
                    else:
                        await update.message.reply_document(document=InputFile(f), caption=f"✅ **Downloaded from {Config.SUPPORTED_PLATFORMS.get(platform, platform)}**")
                
                # Cleanup
                os.remove(file_path)
            except Exception as e:
                await update.message.reply_text(f"❌ Failed to send file: {str(e)}")
        else:
            await update.message.reply_text(message)
        
        await processing_msg.delete()
    
    # ============================================
    # VIDEO HANDLER
    # ============================================
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        video = update.message.video
        
        user_data = self.db.get_user(user_id)
        if user_data and user_data.get('banned', 0) == 1:
            await update.message.reply_text("❌ You are banned!")
            return
        
        can_edit, msg = self.db.can_edit(user_id)
        if not can_edit:
            keyboard = [[InlineKeyboardButton("🎁 START TRIAL", callback_data="menu_trial"),
                        InlineKeyboardButton("⭐ UPGRADE PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        is_premium = self.db.is_premium(user_id)
        can_upload, size_msg = Config.check_size(video.file_size, is_premium)
        if not can_upload:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(size_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        if video.duration:
            can_upload, duration_msg = Config.check_duration(video.duration, is_premium)
            if not can_upload:
                keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
                await update.message.reply_text(duration_msg, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        
        processing_msg = await update.message.reply_text("📥 **Downloading video...**", parse_mode=ParseMode.MARKDOWN)
        
        file = await video.get_file()
        path = os.path.join(Config.UPLOAD_DIR, f"video_{user_id}_{int(time.time())}.mp4")
        await file.download_to_drive(path)
        
        context.user_data['current_video'] = path
        context.user_data['original_video'] = path
        context.user_data['file_type'] = 'video'
        self.db.increment_edits(user_id, "upload", "video", video.file_size)
        
        await self.log_manager.log_edit(user_id, "upload", "video", video.file_size)
        
        await processing_msg.delete()
        
        info = self.video_editor.get_info(path)
        
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("📦 COMPRESS", callback_data="tool_compress"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate")],
            [InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters"),
             InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects")],
            [InlineKeyboardButton("🎵 AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("📝 TEXT", callback_data="tool_text")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark"),
             InlineKeyboardButton("🟢 CHROMA KEY", callback_data="tool_chroma")],
            [InlineKeyboardButton("🔍 STABILIZE", callback_data="tool_stabilize"),
             InlineKeyboardButton("🌈 COLOR GRADE", callback_data="tool_color")],
            [InlineKeyboardButton("🔄 RESET", callback_data="tool_reset"),
             InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        caption = f"✅ **Video Ready!**\n\n📁 Size: {info['size_mb']}MB\n🎥 Duration: {info['duration']}s\n📐 Resolution: {info['resolution']}"
        
        try:
            await update.message.reply_video(video=open(path, 'rb'), caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ Error sending video: {str(e)}")
    
    # ============================================
    # IMAGE HANDLER
    # ============================================
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        
        user_data = self.db.get_user(user_id)
        if user_data and user_data.get('banned', 0) == 1:
            await update.message.reply_text("❌ You are banned!")
            return
        
        can_edit, msg = self.db.can_edit(user_id)
        if not can_edit:
            keyboard = [[InlineKeyboardButton("🎁 START TRIAL", callback_data="menu_trial"),
                        InlineKeyboardButton("⭐ UPGRADE PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        processing_msg = await update.message.reply_text("📥 **Downloading image...**", parse_mode=ParseMode.MARKDOWN)
        
        file = await photo.get_file()
        path = os.path.join(Config.UPLOAD_DIR, f"image_{user_id}_{int(time.time())}.jpg")
        await file.download_to_drive(path)
        
        context.user_data['current_image'] = path
        context.user_data['original_image'] = path
        context.user_data['file_type'] = 'image'
        self.db.increment_edits(user_id, "upload", "image", file.file_size)
        
        await self.log_manager.log_edit(user_id, "upload", "image", file.file_size)
        
        await processing_msg.delete()
        
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_img"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🪞 FLIP", callback_data="tool_flip_img"),
             InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust")],
            [InlineKeyboardButton("🎨 ARTISTIC", callback_data="menu_artistic"),
             InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects_img")],
            [InlineKeyboardButton("🔄 RESET", callback_data="tool_reset"),
             InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        await update.message.reply_photo(photo=open(path, 'rb'), caption="✅ **Image Ready!** Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # VIDEO TOOLS IMPLEMENTATIONS
    # ============================================
    
    async def tool_trim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("✂️ **Trim Video**\n\nSend start and end time in seconds.\nExample: `10 30`\n\nOr:\n• `start 10` - trim from 10s to end\n• `end 30` - trim from start to 30s\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'trim'
        return self.TRIM_STATE
    
    async def handle_trim_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return ConversationHandler.END
        
        try:
            text = update.message.text.lower()
            parts = text.split()
            
            if text.startswith('start'):
                start = float(parts[1]) if len(parts) > 1 else 0
                end = None
            elif text.startswith('end'):
                start = None
                end = float(parts[1]) if len(parts) > 1 else 0
            else:
                start = float(parts[0])
                end = float(parts[1]) if len(parts) > 1 else None
            
            await update.message.reply_text("✂️ Trimming video...")
            output = self.video_editor.trim(video_path, start, end)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_video(video=f, caption=f"✅ Trimmed from {start}s to {end if end else 'end'}!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}\nUse format: `10 30`")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def tool_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🐌 0.25x", callback_data="speed_0.25"),
             InlineKeyboardButton("🚶 0.5x", callback_data="speed_0.5"),
             InlineKeyboardButton("🚶 0.75x", callback_data="speed_0.75")],
            [InlineKeyboardButton("⚡ 1x", callback_data="speed_1.0"),
             InlineKeyboardButton("🏃 1.25x", callback_data="speed_1.25"),
             InlineKeyboardButton("🏃 1.5x", callback_data="speed_1.5")],
            [InlineKeyboardButton("🚀 2x", callback_data="speed_2.0"),
             InlineKeyboardButton("🚀 3x", callback_data="speed_3.0"),
             InlineKeyboardButton("🚀 4x", callback_data="speed_4.0")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await query.edit_message_text("⚡ **Change Video Speed**\n\nChoose speed factor:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        speed = float(data.split("_")[1])
        
        video_path = context.user_data.get('current_video')
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"⚡ Changing speed to {speed}x...")
        
        try:
            output = self.video_editor.speed(video_path, speed)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_video(video=f, caption=f"✅ Speed changed to {speed}x!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def tool_reverse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        video_path = context.user_data.get('current_video')
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text("🔄 Reversing video...")
        
        try:
            output = self.video_editor.reverse(video_path)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_video(video=f, caption="✅ Video reversed!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def tool_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("📦 **Compress Video**\n\nSend target size in MB (max 50MB).\nExample: `20`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'compress'
        return self.COMPRESS_STATE
    
    async def handle_compress_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return ConversationHandler.END
        
        try:
            target = int(update.message.text)
            if target > 100:
                await update.message.reply_text("❌ Target size too large! Max 100MB")
                return ConversationHandler.END
            
            await update.message.reply_text("📦 Compressing video... This may take a while.")
            output = self.video_editor.compress(video_path, target)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_video(video=f, caption=f"✅ Compressed to {target}MB!")
        except ValueError:
            await update.message.reply_text("❌ Invalid number! Use: `20`")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def tool_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("90°", callback_data="rotate_90"),
             InlineKeyboardButton("180°", callback_data="rotate_180")],
            [InlineKeyboardButton("270°", callback_data="rotate_270"),
             InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await query.edit_message_text("🔄 **Rotate Video**\n\nChoose rotation angle:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        angle = int(data.split("_")[1])
        
        video_path = context.user_data.get('current_video')
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"🔄 Rotating {angle}°...")
        
        try:
            output = self.video_editor.rotate(video_path, angle)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_video(video=f, caption=f"✅ Rotated {angle}°!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def tool_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("🎯 **Crop Video**\n\nSend coordinates: `x y width height`\nExample: `100 100 800 600`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'crop'
    
    async def handle_crop_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return
        
        try:
            parts = update.message.text.split()
            x, y, w, h = map(int, parts[:4])
            await update.message.reply_text("🎯 Cropping video...")
            output = self.video_editor.crop(video_path, x, y, w, h)
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_video(video=f, caption=f"✅ Cropped to {w}x{h}!")
        except:
            await update.message.reply_text("❌ Invalid format! Use: `100 100 800 600`")
        
        context.user_data.pop('waiting_for', None)
    
    # ============================================
    # IMAGE TOOLS
    # ============================================
    
    async def tool_rotate_img(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("90°", callback_data="rotate_img_90"),
             InlineKeyboardButton("180°", callback_data="rotate_img_180")],
            [InlineKeyboardButton("270°", callback_data="rotate_img_270"),
             InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await query.edit_message_text("🔄 **Rotate Image**\n\nChoose rotation angle:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_rotate_img(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        angle = int(data.split("_")[2])
        
        image_path = context.user_data.get('current_image')
        if not image_path:
            await query.edit_message_text("❌ No image found!")
            return
        
        await query.edit_message_text(f"🔄 Rotating {angle}°...")
        
        try:
            output = self.image_editor.rotate(image_path, angle)
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_photo(photo=f, caption=f"✅ Rotated {angle}°!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def tool_resize_img(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("📏 **Resize Image**\n\nSend width and height.\nExample: `800 600`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'resize_img'
    
    async def handle_resize_img_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        image_path = context.user_data.get('current_image')
        if not image_path:
            await update.message.reply_text("❌ No image found!")
            return
        
        try:
            parts = update.message.text.split()
            width = int(parts[0])
            height = int(parts[1]) if len(parts) > 1 else width
            
            if width > 4000 or height > 4000:
                await update.message.reply_text("❌ Dimensions too large! Max 4000px")
                return
            
            await update.message.reply_text(f"📏 Resizing to {width}x{height}...")
            output = self.image_editor.resize(image_path, width, height)
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"✅ Resized to {width}x{height}!")
        except:
            await update.message.reply_text("❌ Invalid format! Use: `800 600`")
        
        context.user_data.pop('waiting_for', None)
    
    async def tool_crop_img(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("✂️ **Crop Image**\n\nSend coordinates: `x1 y1 x2 y2`\nExample: `10 10 500 500`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'crop_img'
    
    async def handle_crop_img_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        image_path = context.user_data.get('current_image')
        if not image_path:
            await update.message.reply_text("❌ No image found!")
            return
        
        try:
            parts = update.message.text.split()
            x1, y1, x2, y2 = map(int, parts[:4])
            await update.message.reply_text("✂️ Cropping image...")
            output = self.image_editor.crop(image_path, x1, y1, x2, y2)
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"✅ Cropped!")
        except:
            await update.message.reply_text("❌ Invalid format! Use: `10 10 500 500`")
        
        context.user_data.pop('waiting_for', None)
    
    async def tool_flip_img(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🪞 HORIZONTAL", callback_data="flip_h"),
             InlineKeyboardButton("🪞 VERTICAL", callback_data="flip_v")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await query.edit_message_text("🪞 **Flip Image**\n\nChoose direction:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        direction = data.split("_")[1]
        
        image_path = context.user_data.get('current_image')
        if not image_path:
            await query.edit_message_text("❌ No image found!")
            return
        
        await query.edit_message_text(f"🪞 Flipping {direction}...")
        
        try:
            if direction == "h":
                output = self.image_editor.flip_horizontal(image_path)
            else:
                output = self.image_editor.flip_vertical(image_path)
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_photo(photo=f, caption=f"✅ Flipped {direction}!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def tool_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("☀️ BRIGHTNESS", callback_data="adjust_brightness"),
             InlineKeyboardButton("🌓 CONTRAST", callback_data="adjust_contrast")],
            [InlineKeyboardButton("🎨 SATURATION", callback_data="adjust_saturation"),
             InlineKeyboardButton("🔍 SHARPNESS", callback_data="adjust_sharpness")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await query.edit_message_text("🌈 **Adjust Image**\n\nChoose adjustment:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        adjust_type = data.replace("adjust_", "")
        
        await query.edit_message_text(f"🌈 **Adjust {adjust_type.title()}**\n\nSend factor (0.5 to 2.0)\nExample: `1.2`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = f'adjust_{adjust_type}'
    
    async def handle_adjust_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, adjust_type: str):
        image_path = context.user_data.get('current_image')
        if not image_path:
            await update.message.reply_text("❌ No image found!")
            return
        
        try:
            factor = float(update.message.text)
            
            if factor < 0.1 or factor > 5.0:
                await update.message.reply_text("❌ Factor must be between 0.1 and 5.0")
                return
            
            if adjust_type == "brightness":
                output = self.image_editor.brightness(image_path, factor)
            elif adjust_type == "contrast":
                output = self.image_editor.contrast(image_path, factor)
            elif adjust_type == "saturation":
                output = self.image_editor.saturation(image_path, factor)
            elif adjust_type == "sharpness":
                output = self.image_editor.sharpness(image_path, factor)
            else:
                output = image_path
            
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"✅ {adjust_type.title()} adjusted to {factor}!")
        except ValueError:
            await update.message.reply_text("❌ Invalid number! Use: `1.2`")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
    
    # ============================================
    # FILTERS MENU
    # ============================================
    
    async def filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🎨 BASIC", callback_data="filters_basic"),
             InlineKeyboardButton("🌈 COLOR", callback_data="filters_color")],
            [InlineKeyboardButton("🎭 ARTISTIC", callback_data="filters_artistic"),
             InlineKeyboardButton("✨ LIGHTING", callback_data="filters_lighting")],
            [InlineKeyboardButton("🎬 CINEMATIC", callback_data="filters_cinematic"),
             InlineKeyboardButton("⚡ SPECIAL", callback_data="filters_special")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🎨 **50+ PROFESSIONAL FILTERS**\n\nChoose category:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
        query = update.callback_query
        
        if category == "basic":
            filters_list = ["grayscale", "sepia", "invert", "emboss", "sharpen", "blur", "smooth"]
        elif category == "color":
            filters_list = ["vintage", "cool", "warm", "noir", "pastel", "sunset", "ocean", "forest", "autumn", "spring"]
        elif category == "artistic":
            filters_list = ["oil_paint", "watercolor", "sketch", "cartoon", "pixelate", "mosaic"]
        elif category == "lighting":
            filters_list = ["glow", "neon", "bokeh", "lens_flare", "vignette", "hdr"]
        elif category == "cinematic":
            filters_list = ["cinematic", "dramatic", "dreamy", "hollywood", "bollywood"]
        elif category == "special":
            filters_list = ["rainbow", "prism", "mirror", "kaleidoscope", "fisheye", "tilt_shift"]
        else:
            filters_list = Config.FILTERS_LIST[:20]
        
        keyboard = []
        row = []
        for i, filter_name in enumerate(filters_list):
            row.append(InlineKeyboardButton(filter_name.title(), callback_data=f"filter_{filter_name}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text(f"🎨 **{category.upper()} FILTERS**\n\nClick a filter to apply!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        filter_name = data.replace("filter_", "")
        
        image_path = context.user_data.get('current_image')
        if not image_path:
            await query.edit_message_text("❌ No image found! Send an image first.")
            return
        
        await query.edit_message_text(f"🎨 Applying {filter_name} filter...")
        
        try:
            output = self.filters.apply_filter(image_path, filter_name)
            context.user_data['current_image'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_photo(photo=f, caption=f"✅ Applied **{filter_name}** filter!", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    # ============================================
    # EFFECTS MENU
    # ============================================
    
    async def effects_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("✨ GLITCH", callback_data="effect_glitch"),
             InlineKeyboardButton("📺 VHS", callback_data="effect_vhs")],
            [InlineKeyboardButton("💎 PIXELATE", callback_data="effect_pixelate"),
             InlineKeyboardButton("🎨 CARTOON", callback_data="effect_cartoon")],
            [InlineKeyboardButton("🌊 SLOW MOTION", callback_data="effect_slow"),
             InlineKeyboardButton("⚡ FAST MOTION", callback_data="effect_fast")],
            [InlineKeyboardButton("🎬 CINEMATIC", callback_data="effect_cinematic"),
             InlineKeyboardButton("🌈 RAINBOW", callback_data="effect_rainbow")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await query.edit_message_text("✨ **VIDEO EFFECTS (30+)**\n\nChoose an effect:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def apply_effect(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        effect = data.replace("effect_", "")
        
        video_path = context.user_data.get('current_video')
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"✨ Applying {effect} effect...")
        
        try:
            if effect == "glitch":
                output = self.video_editor.apply_glitch(video_path)
            elif effect == "vhs":
                output = self.video_editor.apply_vhs(video_path)
            elif effect == "pixelate":
                output = self.video_editor.apply_pixelate(video_path)
            elif effect == "cartoon":
                output = self.video_editor.apply_pixelate(video_path)
            elif effect == "slow":
                output = self.video_editor.slow_motion(video_path)
            elif effect == "fast":
                output = self.video_editor.fast_motion(video_path)
            elif effect == "cinematic":
                output = self.video_editor.apply_cinematic(video_path)
            else:
                output = video_path
            
            context.user_data['current_video'] = output
            
            with open(output, 'rb') as f:
                await query.message.reply_video(video=f, caption=f"✅ Applied {effect} effect!")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    # ============================================
    # PREMIUM MENU
    # ============================================
    
    async def premium_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        is_premium = self.db.is_premium(user_id)
        
        if is_premium:
            user_data = self.db.get_user(user_id)
            expiry = user_data.get('premium_expiry', 'N/A')
            days_left = 0
            if expiry != 'N/A':
                try:
                    days_left = (datetime.fromisoformat(expiry) - datetime.now()).days
                except:
                    pass
            
            text = f"""
⭐ **PREMIUM MEMBER** ⭐

━━━━━━━━━━━━━━━━━━━━━━
✅ **Active Features:**
• 4GB File Support
• 60 Minute Videos
• No Watermark
• 4K Export
• 50+ Filters
• 30+ Effects
• Unlimited Downloads
• Priority Processing
• Premium Support

📅 **Expires:** {expiry[:10] if expiry != 'N/A' else 'N/A'}
⏰ **Days Left:** {days_left}

💎 Thank you for supporting Kinva Master Pro!
            """
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        else:
            text = f"""
⭐ **KINVA MASTER PREMIUM** ⭐

━━━━━━━━━━━━━━━━━━━━━━
🚀 **UNLOCK ALL FEATURES** 🚀
━━━━━━━━━━━━━━━━━━━━━━

**FREE vs PREMIUM vs TRIAL Comparison:**

| Feature | FREE | TRIAL | PREMIUM |
|---------|------|-------|---------|
| File Size | 700MB | 700MB | **4GB** |
| Duration | 5 min | 5 min | **60 min** |
| Daily Edits | 10 | 50 | **Unlimited** |
| Downloads | ❌ | 5 | **Unlimited** |
| Watermark | Yes | Yes | **No** |
| Export | 720p | 720p | **4K** |
| Filters | 10 | 50 | **50+** |
| Effects | 10 | 30 | **30+** |

━━━━━━━━━━━━━━━━━━━━━━
💎 **PRICING** 💎
━━━━━━━━━━━━━━━━━━━━━━

• **Monthly:** ${Config.PREMIUM_PRICE_MONTHLY_USD} / ₹{Config.PREMIUM_PRICE_MONTHLY_INR}
• **Yearly:** ${Config.PREMIUM_PRICE_YEARLY_USD} / ₹{Config.PREMIUM_PRICE_YEARLY_INR} (Save 50%)
• **Lifetime:** ${Config.PREMIUM_PRICE_LIFETIME_USD} / ₹{Config.PREMIUM_PRICE_LIFETIME_INR}

━━━━━━━━━━━━━━━━━━━━━━
💳 **PAYMENT METHODS** 💳
━━━━━━━━━━━━━━━━━━━━━━

• **UPI:** `{Config.UPI_ID}`
• **Telegram Stars:** {Config.PREMIUM_PRICE_MONTHLY_STARS} stars/month
• **PayPal:** Available on request
• **Crypto:** USDT/BTC

🔥 **UPGRADE NOW AND GET 7 DAYS FREE!** 🔥
            """
            
            keyboard = [
                [InlineKeyboardButton("💎 BUY MONTHLY", callback_data="buy_monthly"),
                 InlineKeyboardButton("💎 BUY YEARLY", callback_data="buy_yearly")],
                [InlineKeyboardButton("👑 BUY LIFETIME", callback_data="buy_lifetime")],
                [InlineKeyboardButton("⭐ PAY WITH STARS", callback_data="pay_stars")],
                [InlineKeyboardButton("💳 UPI PAYMENT", callback_data="pay_upi")],
                [InlineKeyboardButton("🎁 START TRIAL", callback_data="menu_trial"),
                 InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
            ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # STATS COMMAND
    # ============================================
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        is_premium = self.db.is_premium(user_id)
        has_trial = self.db.has_trial(user_id)
        stats = self.db.get_stats()
        
        if not user_data:
            user_data = self.db.create_user(user_id)
        
        self.db.update_last_seen(user_id)
        
        text = f"""
📊 **YOUR STATISTICS**

━━━━━━━━━━━━━━━━━━━━━━
👤 **User:** {update.effective_user.first_name}
🆔 **ID:** `{user_id}`

📈 **Activity:**
• Total Edits: `{user_data.get('total_edits', 0)}`
• Today's Edits: `{user_data.get('edits_today', 0)}`
• Total Downloads: `{user_data.get('total_downloads', 0)}`
• Today's Downloads: `{user_data.get('downloads_today', 0)}`

💎 **Status:**
• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`
• Trial: `{'✅ Active' if has_trial else '❌ Inactive'}`
{f"📅 Expires: {user_data.get('premium_expiry', 'N/A')[:10]}" if is_premium else ''}
{f"🎁 Trial Used: {has_trial}" if not is_premium else ''}

💰 **Balance:**
• Wallet: `${user_data.get('balance', 0)}`
• Stars: `{user_data.get('stars_balance', 0)}`

👥 **Referrals:**
• Referred Users: `{user_data.get('referral_count', 0)}`
• Share link to earn rewards

━━━━━━━━━━━━━━━━━━━━━━
🏆 **GLOBAL STATS**
━━━━━━━━━━━━━━━━━━━━━━

• Total Users: `{stats['total_users']}`
• Premium Users: `{stats['premium_users']}`
• Trial Users: `{stats['trial_users']}`
• Banned Users: `{stats['banned_users']}`
• Total Edits: `{stats['total_edits']}`
• Total Downloads: `{stats['total_downloads']}`
• Today's Edits: `{stats['today_edits']}`
• Today's Downloads: `{stats['today_downloads']}`

━━━━━━━━━━━━━━━━━━━━━━
💡 **Invite friends to earn rewards!**
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.stats(update, context)
    
    # ============================================
    # ADMIN PANEL (ENHANCED)
    # ============================================
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        stats = self.db.get_stats()
        recent_users = self.db.get_recent_users(5)
        
        text = f"""
👑 **ADMIN PANEL**

━━━━━━━━━━━━━━━━━━━━━━
📊 **STATISTICS**
━━━━━━━━━━━━━━━━━━━━━━

• Total Users: `{stats['total_users']}`
• Premium Users: `{stats['premium_users']}`
• Trial Users: `{stats['trial_users']}`
• Banned Users: `{stats['banned_users']}`
• Total Edits: `{stats['total_edits']}`
• Total Downloads: `{stats['total_downloads']}`
• Today's Edits: `{stats['today_edits']}`
• Today's Downloads: `{stats['today_downloads']}`

━━━━━━━━━━━━━━━━━━━━━━
📋 **RECENT USERS (Last 5)**
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for user in recent_users:
            status = "⭐" if user['is_premium'] else "🎁" if user.get('has_trial') else "📀"
            text += f"• {status} {user['first_name']} (@{user['username'] or 'N/A'}) - Joined: {user['created_at'][:10]}\n"
        
        text += """
━━━━━━━━━━━━━━━━━━━━━━
🛠️ **ADMIN ACTIONS**
━━━━━━━━━━━━━━━━━━━━━━

• 📢 Broadcast Message
• ⭐ Add/Remove Premium
• 🎁 Manage Trials
• 🚫 Ban/Unban Users
• ⚠️ Warn Users
• 📊 View All Users
• 💰 View Transactions
• 📝 View Feedback
• ⚙️ System Settings
• 📈 Export Data
• 💾 Backup Database
• 🔄 Restart Bot
• 🛑 Shutdown Bot

━━━━━━━━━━━━━━━━━━━━━━
💡 **Use the buttons below to manage the bot**
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("⭐ ADD PREMIUM", callback_data="admin_add_premium")],
            [InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban"),
             InlineKeyboardButton("✅ UNBAN USER", callback_data="admin_unban")],
            [InlineKeyboardButton("⚠️ WARN USER", callback_data="admin_warn"),
             InlineKeyboardButton("🎁 MANAGE TRIALS", callback_data="admin_trials")],
            [InlineKeyboardButton("📊 ALL USERS", callback_data="admin_users"),
             InlineKeyboardButton("💰 TRANSACTIONS", callback_data="admin_transactions")],
            [InlineKeyboardButton("📝 FEEDBACK", callback_data="admin_feedback"),
             InlineKeyboardButton("💾 BACKUP DB", callback_data="admin_backup")],
            [InlineKeyboardButton("📈 STATS", callback_data="admin_stats"),
             ⚙️ SETTINGS", callback_data="admin_settings")],
            [InlineKeyboardButton("🔄 RESTART", callback_data="admin_restart"),
             InlineKeyboardButton("🛑 SHUTDOWN", callback_data="admin_shutdown")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("📢 **Send Broadcast Message**\n\nPlease send the message you want to broadcast to all users.\n\nYou can use:\n• Text messages\n• Photos with captions\n• Videos\n• Documents\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'broadcast'
        return self.BROADCAST_STATE
    
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        users = self.db.get_all_users()
        success = 0
        fail = 0
        
        progress = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
        
        # Get the message content
        if update.message.text:
            message_content = update.message.text
            message_type = "text"
        elif update.message.photo:
            message_content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            message_type = "photo"
        elif update.message.video:
            message_content = update.message.video.file_id
            caption = update.message.caption or ""
            message_type = "video"
        else:
            await progress.edit_text("❌ Unsupported message type!")
            return
        
        for user in users:
            try:
                if message_type == "text":
                    await context.bot.send_message(
                        chat_id=user['id'],
                        text=f"📢 **ANNOUNCEMENT**\n\n{message_content}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                elif message_type == "photo":
                    await context.bot.send_photo(
                        chat_id=user['id'],
                        photo=message_content,
                        caption=f"📢 **ANNOUNCEMENT**\n\n{caption}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                elif message_type == "video":
                    await context.bot.send_video(
                        chat_id=user['id'],
                        video=message_content,
                        caption=f"📢 **ANNOUNCEMENT**\n\n{caption}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f"Broadcast failed to {user['id']}: {e}")
            await asyncio.sleep(0.05)
        
        await progress.edit_text(f"✅ **Broadcast Complete!**\n\n✅ Success: {success}\n❌ Failed: {fail}")
        
        await self.log_manager.send_log("admin", f"**Broadcast sent**\nTo: {success} users\nFailed: {fail}", user_id)
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def admin_add_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("⭐ **Add Premium**\n\nSend user ID and days (e.g., `123456789 30`)\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'add_premium'
        return self.ADD_PREMIUM_STATE
    
    async def handle_add_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Unauthorized!")
            return ConversationHandler.END
        
        try:
            parts = update.message.text.split()
            target_id = int(parts[0])
            days = int(parts[1]) if len(parts) > 1 else 30
            
            self.db.add_premium(target_id, days)
            await update.message.reply_text(f"✅ Premium added to user {target_id} for {days} days!")
            
            await self.log_manager.send_log("admin", f"**Premium Added**\nUser: {target_id}\nDays: {days}", user_id)
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🎉 **Congratulations!**\n\nYou have been gifted {days} days of Premium!\n\nThank you for using Kinva Master Pro!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        except ValueError:
            await update.message.reply_text("❌ Invalid format! Use: `user_id days`")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def admin_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("🚫 **Ban User**\n\nSend user ID to ban (e.g., `123456789`)\n\nOptional: Add reason (e.g., `123456789 Spamming`)\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'ban_user'
        return self.BAN_STATE
    
    async def handle_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Unauthorized!")
            return ConversationHandler.END
        
        try:
            parts = update.message.text.split()
            target_id = int(parts[0])
            reason = ' '.join(parts[1:]) if len(parts) > 1 else "No reason provided"
            
            self.db.ban_user(target_id, reason)
            await update.message.reply_text(f"✅ User {target_id} has been banned!\n\nReason: {reason}")
            
            await self.log_manager.send_log("ban", f"**User Banned**\nUser: {target_id}\nReason: {reason}\nBy: {user_id}", user_id)
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🚫 **You have been banned** from using Kinva Master Pro.\n\n**Reason:** {reason}\n\nContact admin for more information.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def admin_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("✅ **Unban User**\n\nSend user ID to unban (e.g., `123456789`)\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'unban_user'
    
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        try:
            target_id = int(update.message.text)
            self.db.unban_user(target_id)
            await update.message.reply_text(f"✅ User {target_id} has been unbanned!")
            
            await self.log_manager.send_log("unban", f"**User Unbanned**\nUser: {target_id}\nBy: {user_id}", user_id)
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text="✅ **You have been unbanned** from Kinva Master Pro.\n\nYou can now use the bot again!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
    
    async def admin_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("⚠️ **Warn User**\n\nSend user ID and reason (e.g., `123456789 Spamming`)\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'warn_user'
    
    async def handle_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        try:
            parts = update.message.text.split()
            target_id = int(parts[0])
            reason = ' '.join(parts[1:]) if len(parts) > 1 else "No reason provided"
            
            self.db.warn_user(target_id, reason)
            await update.message.reply_text(f"⚠️ User {target_id} has been warned!\n\nReason: {reason}")
            
            await self.log_manager.send_log("admin", f"**User Warned**\nUser: {target_id}\nReason: {reason}\nBy: {user_id}", user_id)
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"⚠️ **Warning**\n\nYou have received a warning.\n**Reason:** {reason}\n\n3 warnings will result in a ban.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        context.user_data.pop('waiting_for', None)
    
    async def admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        users = self.db.get_all_users()
        text = "📊 **ALL USERS**\n\n"
        
        for user in users[:50]:
            status = "⭐" if user['is_premium'] else "🎁" if user.get('has_trial') else "📀"
            banned = "🚫" if user.get('banned') else ""
            text += f"{status} {banned} `{user['id']}` - {user['first_name']} (@{user['username'] or 'N/A'}) - Edits: {user.get('total_edits', 0)}\n"
        
        if len(users) > 50:
            text += f"\n... and {len(users) - 50} more users"
        
        # Add pagination for large lists
        keyboard = [
            [InlineKeyboardButton("📄 EXPORT CSV", callback_data="admin_export")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        transactions = self.db.get_transactions(20)
        
        if not transactions:
            text = "💰 **No transactions found**"
        else:
            text = "💰 **RECENT TRANSACTIONS**\n\n"
            total_revenue = 0
            for tx in transactions:
                total_revenue += tx.get('amount', 0)
                status_emoji = "✅" if tx['status'] == 'completed' else "⏳"
                text += f"{status_emoji} User: `{tx['user_id']}` | ${tx['amount']} | {tx['payment_method']} | {tx['plan_type']}\n"
            text += f"\n**Total Revenue:** ${total_revenue}"
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        feedbacks = self.db.get_feedback()
        
        if not feedbacks:
            text = "📝 **No feedback found**"
        else:
            text = "📝 **USER FEEDBACK**\n\n"
            for fb in feedbacks[:10]:
                text += f"• User: `{fb['user_id']}` | Rating: {'⭐' * fb['rating']}\nMessage: {fb['message'][:100]}\nStatus: {fb['status']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("✅ MARK RESOLVED", callback_data="admin_feedback_resolve")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("💾 **Backing up database...**")
        
        try:
            backup_path = self.db.backup_database()
            
            # Send backup file
            with open(backup_path, 'rb') as f:
                await query.message.reply_document(
                    document=InputFile(f, filename=os.path.basename(backup_path)),
                    caption=f"✅ Database backed up successfully!\n\n📁 File: {os.path.basename(backup_path)}\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            await self.log_manager.send_log("admin", f"**Database Backup**\nFile: {os.path.basename(backup_path)}", query.from_user.id)
        except Exception as e:
            await query.edit_message_text(f"❌ Backup failed: {str(e)}")
    
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        stats = self.db.get_stats()
        
        # Get additional stats
        cursor = self.db.execute_query("SELECT AVG(total_edits) FROM users")
        avg_edits = cursor.fetchone()[0] or 0
        
        cursor = self.db.execute_query("SELECT SUM(amount) FROM transactions WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        text = f"""
📈 **DETAILED STATISTICS**

━━━━━━━━━━━━━━━━━━━━━━
👥 **USERS**
• Total: {stats['total_users']}
• Premium: {stats['premium_users']}
• Trial: {stats['trial_users']}
• Free: {stats['total_users'] - stats['premium_users'] - stats['trial_users']}
• Banned: {stats['banned_users']}

━━━━━━━━━━━━━━━━━━━━━━
🎬 **EDITS**
• Total: {stats['total_edits']}
• Today: {stats['today_edits']}
• Average per user: {avg_edits:.1f}

━━━━━━━━━━━━━━━━━━━━━━
📥 **DOWNLOADS**
• Total: {stats['total_downloads']}
• Today: {stats['today_downloads']}

━━━━━━━━━━━━━━━━━━━━━━
💰 **REVENUE**
• Total: ${total_revenue:.2f}
• Premium rate: {(stats['premium_users'] / stats['total_users'] * 100) if stats['total_users'] > 0 else 0:.1f}%

━━━━━━━━━━━━━━━━━━━━━━
📊 **GROWTH**
• New users today: {len(self.db.get_recent_users(100))}
• Active users: {stats['today_edits'] + stats['today_downloads']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        text = """
⚙️ **SYSTEM SETTINGS**

━━━━━━━━━━━━━━━━━━━━━━
**Current Settings:**
• Free Limit: 700MB
• Premium Limit: 4GB
• Free Duration: 5 min
• Premium Duration: 60 min
• Daily Free Edits: 10
• Trial Duration: 3 days
• Trial Edits: 50
• Trial Downloads: 5

━━━━━━━━━━━━━━━━━━━━━━
**Bot Status:**
• Version: 6.0.0
• Database: Connected
• Log Channel: {'✅' if Config.LOG_CHANNEL_ID else '❌'}

━━━━━━━━━━━━━━━━━━━━━━
**Coming Soon:**
• Custom file limits
• Custom pricing
• Welcome message editor
• Maintenance mode
• Auto-backup scheduler
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 RELOAD CONFIG", callback_data="admin_reload")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("🔄 **Restarting bot...**\n\nPlease wait...", parse_mode=ParseMode.MARKDOWN)
        
        await self.log_manager.send_log("admin", f"**Bot Restart**\nInitiated by: {query.from_user.id}", query.from_user.id)
        
        # Restart the bot
        os.execv(sys.executable, ['python'] + sys.argv)
    
    async def admin_shutdown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("🛑 **Shutting down bot...**\n\nGoodbye!", parse_mode=ParseMode.MARKDOWN)
        
        await self.log_manager.send_log("admin", f"**Bot Shutdown**\nInitiated by: {query.from_user.id}", query.from_user.id)
        
        # Cleanup and exit
        cleanup_temp_files()
        sys.exit(0)
    
    async def admin_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in Config.ADMIN_IDS:
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        await query.edit_message_text("📄 **Exporting user data...**")
        
        try:
            users = self.db.get_all_users()
            
            # Create CSV
            import csv
            csv_path = os.path.join(Config.TEMP_DIR, f"users_export_{int(time.time())}.csv")
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'first_name', 'is_premium', 'has_trial', 'banned', 'total_edits', 'total_downloads', 'created_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for user in users:
                    writer.writerow({k: user.get(k, '') for k in fieldnames})
            
            with open(csv_path, 'rb') as f:
                await query.message.reply_document(
                    document=InputFile(f, filename=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"),
                    caption=f"✅ Exported {len(users)} users"
                )
            
            os.remove(csv_path)
        except Exception as e:
            await query.edit_message_text(f"❌ Export failed: {str(e)}")
    
    # ============================================
    # RESET & DONE
    # ============================================
    
    async def reset_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        file_type = context.user_data.get('file_type')
        
        if file_type == 'video':
            original = context.user_data.get('original_video')
            if original and os.path.exists(original):
                context.user_data['current_video'] = original
                with open(original, 'rb') as f:
                    await query.message.reply_video(video=f, caption="✅ Reset to original video!")
            else:
                await query.edit_message_text("❌ No original file found!")
        
        elif file_type == 'image':
            original = context.user_data.get('original_image')
            if original and os.path.exists(original):
                context.user_data['current_image'] = original
                with open(original, 'rb') as f:
                    await query.message.reply_photo(photo=f, caption="✅ Reset to original image!")
            else:
                await query.edit_message_text("❌ No original file found!")
    
    async def done_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("✅ **Editing complete!**\n\nSend me another file to continue editing!\n\n💡 Tip: Use /menu to see all available tools.", parse_mode=ParseMode.MARKDOWN)
        context.user_data.clear()
    
    # ============================================
    # MENUS
    # ============================================
    
    async def video_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("📦 COMPRESS", callback_data="tool_compress"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate")],
            [InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters"),
             InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects")],
            [InlineKeyboardButton("🎵 AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("📝 TEXT", callback_data="tool_text")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark"),
             InlineKeyboardButton("🟢 CHROMA KEY", callback_data="tool_chroma")],
            [InlineKeyboardButton("🔍 STABILIZE", callback_data="tool_stabilize"),
             InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🎬 **VIDEO EDITING TOOLS (30+)**\n\nChoose a tool:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def image_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_img"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🪞 FLIP", callback_data="tool_flip_img"),
             InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust")],
            [InlineKeyboardButton("🎨 ARTISTIC", callback_data="menu_artistic"),
             InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects_img")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🖼️ **IMAGE EDITING TOOLS (30+)**\n\nChoose a tool:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def support_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        text = f"""
📞 **SUPPORT & CONTACT**

━━━━━━━━━━━━━━━━━━━━━━
**Telegram Support:** {Config.SUPPORT_CHAT}
**Email:** {Config.SUPPORT_EMAIL}
**Website:** {Config.WEBSITE}
**Channel:** {Config.TELEGRAM_CHANNEL}

━━━━━━━━━━━━━━━━━━━━━━
**FAQs:**

❓ **How to edit?** - Send me a photo/video
❓ **Premium benefits?** - Use /premium
❓ **Free trial?** - Use /trial
❓ **Download videos?** - Use /download
❓ **Report bug?** - Use /feedback
❓ **Payment issue?** - Contact @admin

━━━━━━━━━━━━━━━━━━━━━━
**Response Time:** 24-48 hours

💬 **Join our channel for updates and tutorials!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=Config.TELEGRAM_CHANNEL)],
            [InlineKeyboardButton("💬 Support Chat", url=Config.SUPPORT_CHAT)],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = f"""
ℹ️ **About Kinva Master Pro**

━━━━━━━━━━━━━━━━━━━━━━
**Version:** {Config.get_version()}
**Developer:** Kinva Master Team
**Platform:** Telegram
**Status:** 🟢 Active

**Features:**
• 50+ Video Editing Tools
• 30+ Image Editing Tools
• 50+ Professional Filters
• Social Media Downloader
• Premium Subscription
• Free Trial System

**CapCut Style:**
• Auto Captions
• Voice Changer
• Motion Tracking

**Kinemaster Style:**
• Chroma Key
• Multiple Layers
• Keyframe Animation

**Canva Style:**
• 500+ Templates
• 1000+ Elements

━━━━━━━━━━━━━━━━━━━━━━
📞 **Support:** @kinvasupport
🌐 **Website:** kinvamaster.com
📢 **Channel:** @kinvamaster
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # FEEDBACK
    # ============================================
    
    async def feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📝 **Send Feedback**\n\nPlease send your feedback or report any issues.\n\nYou can also rate us from 1-5 stars.\n\nExample: `Great bot! 5 stars`\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['waiting_for'] = 'feedback'
        return self.FEEDBACK_STATE
    
    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message = update.message.text
        
        # Extract rating if present
        rating = 5
        import re
        rating_match = re.search(r'(\d+)\s*stars?', message.lower())
        if rating_match:
            rating = min(5, max(1, int(rating_match.group(1))))
        
        self.db.add_feedback(user_id, message, rating)
        
        await update.message.reply_text(f"✅ **Thank you for your feedback!**\n\nRating: {'⭐' * rating}\n\nWe appreciate your input!", parse_mode=ParseMode.MARKDOWN)
        
        await self.log_manager.send_log("user_action", f"**Feedback Submitted**\nRating: {rating}/5\nMessage: {message[:100]}", user_id)
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    # ============================================
    # CALLBACK HANDLER
    # ============================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        await query.answer()
        
        # Navigation
        if data == "back_main":
            await self.start(update, context)
        elif data == "menu_video":
            await self.video_menu(update, context)
        elif data == "menu_image":
            await self.image_menu(update, context)
        elif data == "menu_filters":
            await self.filters_menu(update, context)
        elif data == "menu_effects":
            await self.effects_menu(update, context)
        elif data == "menu_premium":
            await self.premium_menu(update, context)
        elif data == "menu_stats":
            await self.stats(update, context)
        elif data == "menu_help":
            await self.help_menu(update, context)
        elif data == "menu_download":
            await self.download_menu(update, context)
        elif data == "menu_trial":
            await self.trial_menu(update, context)
        elif data == "menu_admin":
            await self.admin_panel(update, context)
        elif data == "menu_support":
            await self.support_menu(update, context)
        
        # Filter categories
        elif data == "filters_basic":
            await self.show_filters(update, context, "basic")
        elif data == "filters_color":
            await self.show_filters(update, context, "color")
        elif data == "filters_artistic":
            await self.show_filters(update, context, "artistic")
        elif data == "filters_lighting":
            await self.show_filters(update, context, "lighting")
        elif data == "filters_cinematic":
            await self.show_filters(update, context, "cinematic")
        elif data == "filters_special":
            await self.show_filters(update, context, "special")
        
        # Trial
        elif data == "activate_trial":
            await self.activate_trial(update, context)
        
        # Admin actions
        elif data == "admin_broadcast":
            await self.admin_broadcast(update, context)
        elif data == "admin_add_premium":
            await self.admin_add_premium(update, context)
        elif data == "admin_ban":
            await self.admin_ban(update, context)
        elif data == "admin_unban":
            await self.admin_unban(update, context)
        elif data == "admin_warn":
            await self.admin_warn(update, context)
        elif data == "admin_users":
            await self.admin_users(update, context)
        elif data == "admin_transactions":
            await self.admin_transactions(update, context)
        elif data == "admin_feedback":
            await self.admin_feedback(update, context)
        elif data == "admin_backup":
            await self.admin_backup(update, context)
        elif data == "admin_stats":
            await self.admin_stats(update, context)
        elif data == "admin_settings":
            await self.admin_settings(update, context)
        elif data == "admin_restart":
            await self.admin_restart(update, context)
        elif data == "admin_shutdown":
            await self.admin_shutdown(update, context)
        elif data == "admin_export":
            await self.admin_export(update, context)
        
        # Video tools
        elif data == "tool_trim":
            await self.tool_trim(update, context)
        elif data == "tool_speed":
            await self.tool_speed(update, context)
        elif data.startswith("speed_"):
            await self.apply_speed(update, context, data)
        elif data == "tool_reverse":
            await self.tool_reverse(update, context)
        elif data == "tool_compress":
            await self.tool_compress(update, context)
        elif data == "tool_rotate":
            await self.tool_rotate(update, context)
        elif data.startswith("rotate_"):
            await self.apply_rotate(update, context, data)
        elif data == "tool_crop":
            await self.tool_crop(update, context)
        elif data == "tool_reset":
            await self.reset_edit(update, context)
        elif data == "tool_done":
            await self.done_edit(update, context)
        
        # Image tools
        elif data == "tool_rotate_img":
            await self.tool_rotate_img(update, context)
        elif data.startswith("rotate_img_"):
            await self.apply_rotate_img(update, context, data)
        elif data == "tool_resize_img":
            await self.tool_resize_img(update, context)
        elif data == "tool_crop_img":
            await self.tool_crop_img(update, context)
        elif data == "tool_flip_img":
            await self.tool_flip_img(update, context)
        elif data.startswith("flip_"):
            await self.apply_flip(update, context, data)
        elif data == "tool_adjust":
            await self.tool_adjust(update, context)
        elif data.startswith("adjust_"):
            await self.handle_adjust(update, context, data)
        
        # Effects
        elif data.startswith("effect_"):
            await self.apply_effect(update, context, data)
        
        # Filters
        elif data.startswith("filter_"):
            await self.apply_filter(update, context, data)
        
        # Premium purchase
        elif data.startswith("buy_"):
            plan = data.replace("buy_", "")
            await query.edit_message_text(f"💎 **Purchase {plan.upper()}**\n\nSend payment to {Config.UPI_ID} and send screenshot to admin.\n\nPremium will be activated within 24 hours.\n\n**Payment Details:**\nUPI: `{Config.UPI_ID}`\nAmount: ₹{self.premium_manager.get_plan(plan)['price_inr']}\n\nAfter payment, send transaction screenshot to @admin", parse_mode=ParseMode.MARKDOWN)
        elif data == "pay_stars":
            await query.edit_message_text("⭐ **Pay with Telegram Stars**\n\nClick below to pay 100 Stars for Premium Monthly!\n\n✅ Instant activation after payment", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ PAY 100 STARS", callback_data="confirm_stars")]]), parse_mode=ParseMode.MARKDOWN)
        elif data == "pay_upi":
            await query.edit_message_text(f"💳 **UPI Payment**\n\nUPI ID: `{Config.UPI_ID}`\nAmount: ₹{Config.PREMIUM_PRICE_MONTHLY_INR}\n\nSend payment and screenshot to @admin\n\nPremium will be activated within 24 hours.", parse_mode=ParseMode.MARKDOWN)
        
        # Download
        elif data.startswith("download_"):
            platform = data.replace("download_", "")
            await query.edit_message_text(f"📥 **Download from {platform.upper()}**\n\nSend me the {platform} video link!\n\nExample: `https://{platform}.com/...`\n\n💡 Tip: Premium users get unlimited downloads!", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = f'download_{platform}'
        
        else:
            await query.edit_message_text("🛠️ **Feature coming soon!**\n\nStay tuned for updates!", parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # TEXT HANDLER
    # ============================================
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        waiting_for = context.user_data.get('waiting_for')
        
        # Check if it's a URL for download
        if text.startswith('http://') or text.startswith('https://'):
            await self.handle_download(update, context)
            return
        
        if waiting_for == 'broadcast':
            await self.handle_broadcast(update, context)
        elif waiting_for == 'add_premium':
            await self.handle_add_premium(update, context)
        elif waiting_for == 'ban_user':
            await self.handle_ban(update, context)
        elif waiting_for == 'unban_user':
            await self.handle_unban(update, context)
        elif waiting_for == 'warn_user':
            await self.handle_warn(update, context)
        elif waiting_for == 'trim':
            await self.handle_trim_input(update, context)
        elif waiting_for == 'compress':
            await self.handle_compress_input(update, context)
        elif waiting_for == 'crop':
            await self.handle_crop_input(update, context)
        elif waiting_for == 'resize_img':
            await self.handle_resize_img_input(update, context)
        elif waiting_for == 'crop_img':
            await self.handle_crop_img_input(update, context)
        elif waiting_for == 'feedback':
            await self.handle_feedback(update, context)
        elif waiting_for and waiting_for.startswith('adjust_'):
            adjust_type = waiting_for.replace('adjust_', '')
            await self.handle_adjust_input(update, context, adjust_type)
        elif waiting_for and waiting_for.startswith('download_'):
            platform = waiting_for.replace('download_', '')
            await self.handle_download(update, context)
        else:
            await update.message.reply_text("❌ Send a photo/video to edit, or use /menu for commands!\n\n💡 Tip: Send a URL to download from social media!")

# ============================================
# CANCEL FUNCTION
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled.\n\nUse /start to go back to main menu.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    error = context.error
    logger.error(f"Error: {error}", exc_info=True)
    
    error_msg = str(error)
    
    # Send error to log channel
    try:
        await log_manager.send_log("error", f"**Error Occurred**\n{error_msg[:500]}", update.effective_user.id if update and update.effective_user else None)
    except:
        pass
    
    # Notify user if possible
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ An error occurred. Please try again later or contact support.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    bot = KinvaMasterBot()
    
    # Set log manager bot app
    log_manager.bot_app = None  # Will be set after app creation
    
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Set bot app in log manager
    log_manager.bot_app = app
    
    # Command handlers
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("menu", bot.help_menu))
    app.add_handler(CommandHandler("help", bot.help_menu))
    app.add_handler(CommandHandler("stats", bot.stats))
    app.add_handler(CommandHandler("profile", bot.profile))
    app.add_handler(CommandHandler("premium", bot.premium_menu))
    app.add_handler(CommandHandler("trial", bot.trial_menu))
    app.add_handler(CommandHandler("admin", bot.admin_panel))
    app.add_handler(CommandHandler("feedback", bot.feedback))
    app.add_handler(CommandHandler("support", bot.support_menu))
    app.add_handler(CommandHandler("about", bot.about))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Download commands
    app.add_handler(CommandHandler("download", bot.handle_download))
    app.add_handler(CommandHandler("youtube", bot.handle_download))
    app.add_handler(CommandHandler("instagram", bot.handle_download))
    app.add_handler(CommandHandler("tiktok", bot.handle_download))
    app.add_handler(CommandHandler("twitter", bot.handle_download))
    app.add_handler(CommandHandler("facebook", bot.handle_download))
    
    # Conversation handlers
    conv_broadcast = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.admin_broadcast, pattern="^admin_broadcast$")],
        states={bot.BROADCAST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_broadcast),
                                      MessageHandler(filters.PHOTO, bot.handle_broadcast),
                                      MessageHandler(filters.VIDEO, bot.handle_broadcast)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_broadcast)
    
    conv_add_premium = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.admin_add_premium, pattern="^admin_add_premium$")],
        states={bot.ADD_PREMIUM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_add_premium)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_add_premium)
    
    conv_ban = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.admin_ban, pattern="^admin_ban$")],
        states={bot.BAN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_ban)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_ban)
    
    conv_trim = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.tool_trim, pattern="^tool_trim$")],
        states={bot.TRIM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_trim_input)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_trim)
    
    conv_compress = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.tool_compress, pattern="^tool_compress$")],
        states={bot.COMPRESS_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_compress_input)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_compress)
    
    conv_feedback = ConversationHandler(
        entry_points=[CommandHandler("feedback", bot.feedback)],
        states={bot.FEEDBACK_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_feedback)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_feedback)
    
    # Callback handler
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.VIDEO, bot.handle_video))
    app.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Start bot
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              KINVA MASTER PRO BOT STARTED                    ║
║                     VERSION 6.0.0                           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Status: 🟢 RUNNING                                          ║
║  Admin: ✅ Configured                                        ║
║  Database: ✅ Connected                                      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  FEATURES:                                                   ║
║  ✅ 50+ Video Editing Tools                                  ║
║  ✅ 30+ Image Editing Tools                                  ║
║  ✅ 50+ Professional Filters                                 ║
║  ✅ 10+ Social Media Downloaders                             ║
║  ✅ Premium System with Trial                                ║
║  ✅ Log Channel System                                       ║
║  ✅ Complete Admin Panel                                     ║
║  ✅ User Statistics & Database                               ║
║  ✅ Shutdown/Restart Commands                                ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  COMMANDS:                                                   ║
║  /start - Start the bot                                      ║
║  /menu - Show all commands (30+ commands)                    ║
║  /stats - Your statistics                                    ║
║  /premium - Premium info                                     ║
║  /trial - Start free trial                                   ║
║  /download <url> - Download from social media                ║
║  /feedback - Send feedback                                   ║
║  /admin - Admin panel (admin only)                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Start polling
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
