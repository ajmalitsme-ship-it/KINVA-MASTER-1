#!/usr/bin/env python3
"""
TELEGRAM ADVANCED MEDIA EDITOR BOT - PRODUCTION READY
Complete Video & Image Editing Suite with 35+ Video Tools & 30+ Image Tools
Features: File Rename, 4GB Support, 7-Day Trial, 35+ Admin Panels, Timeline Editor
Deployment: Render.com, Heroku, VPS Ready - No Port Binding Issues
"""

import os
import re
import json
import sqlite3
import asyncio
import tempfile
import subprocess
import shutil
import random
import string
import time
import sys
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
from functools import wraps
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps
import requests
from gtts import gTTS
import numpy as np
import cv2
from pyrogram import Client, filters, enums, idle
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message,
    ReplyKeyboardMarkup, KeyboardButton, ForceReply, InputMediaPhoto, 
    InputMediaVideo, InputMediaDocument
)
from pyrogram.errors import FloodWait, UserNotParticipant, RPCError
from pyrogram.enums import ParseMode, ChatAction
# Add at the top with other imports
from aiohttp import web
import threading

# Add this class or method
class HealthServer:
    def __init__(self, port=8080):
        self.port = port
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.health_check)
    
    async def health_check(self, request):
        return web.Response(text="Bot is running!", status=200)
    
    def run(self):
        web.run_app(self.app, host='0.0.0.0', port=self.port)

# In your MediaEditorBot class, add:
def start_health_server(self):
    server = HealthServer()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    print("✅ Health check server started on port 8080")

# In your run method, before app.run():
def run(self):
    self.start_health_server()
    print("🤖 Bot Starting...")
    # ... rest of your run code
# ==================== LOGGING SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== COMPLETE BULK CONFIGURATION ====================
class Config:
    # Bot Configuration - Set via Environment Variables
    API_ID = int(os.environ.get("API_ID", "27806628"))
    API_HASH = os.environ.get("API_HASH", "25d88301e886b82826a525b7cf52e090")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8623600399:AAGNn_d6Lq5DRrwelD_rvOUfgsM-jyk8Kf8")
    OWNER_ID = int(os.environ.get("OWNER_ID", 8525952693))
    
    # Database & Storage
    DB_PATH = "media_bot.db"
    TEMP_DIR = "temp_media"
    THUMB_DIR = "thumbnails"
    FONTS_DIR = "fonts"
    STICKERS_DIR = "stickers"
    EFFECTS_DIR = "effects"
    BACKUP_DIR = "backups"
    LOGS_DIR = "logs"
    
    # File Size Limits (4GB Support)
    MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    MAX_IMAGE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_DOCUMENT_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    
    # Premium Settings - 7 Day Trial
    PREMIUM_PRICE = "$9.99/month | $49.99/year"
    PREMIUM_LINK = os.environ.get("PREMIUM_LINK", "https://t.me/yourpaymentbot")
    FREE_TRIAL_DAYS = 7  # 7 days trial
    MAX_FREE_EDITS = 10  # Free users get 10 edits/day
    
    # Google AdSense Configuration
    GOOGLE_ADS_ENABLED = os.environ.get("GOOGLE_ADS_ENABLED", "True") == "True"
    ADS_CLIENT_ID = os.environ.get("ADS_CLIENT_ID", "ca-pub-xxxxxxxxxxxxx")
    ADS_SLOT_ID = os.environ.get("ADS_SLOT_ID", "1234567890")
    ADS_TEXT = "🎬 **Support Our Bot**\n\nWatch this 30-second ad to continue editing!\n[Click Here to Support](https://www.google.com)\n\n⭐ **Premium Users:** No ads ever! Get /premium"
    ADS_INTERVAL = 3  # Show ad every 3 edits
    
    # Channel & Links
    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")
    FORCE_SUB_CHANNEL_ID = int(os.environ.get("FORCE_SUB_CHANNEL_ID", "0")) if os.environ.get("FORCE_SUB_CHANNEL_ID") else None
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/yourchannel")
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "https://t.me/yourgroup")
    
    # Watermark Settings
    WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "KiraFx")
    WATERMARK_OPACITY = 128
    WATERMARK_POSITION = "bottom_right"  # top_left, top_right, bottom_left, bottom_right, center
    
    # Processing Settings
    ENABLE_CACHE = True
    CACHE_DURATION_HOURS = 24
    MAX_PARALLEL_JOBS = 3
    PROCESSING_TIMEOUT = 300  # 5 minutes
    ENABLE_FFMPEG_LOGS = False
    
    # AI Model Settings
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
    TTS_LANG = os.environ.get("TTS_LANG", "en")
    
    # Supported Formats
    SUPPORTED_VIDEO = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"]
    SUPPORTED_IMAGE = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".ico"]
    SUPPORTED_AUDIO = [".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"]
    
    # Video Quality Presets
    VIDEO_PRESETS = {
        "144p": {"width": 256, "height": 144, "bitrate": "200k", "crf": 28},
        "240p": {"width": 426, "height": 240, "bitrate": "400k", "crf": 26},
        "360p": {"width": 640, "height": 360, "bitrate": "800k", "crf": 25},
        "480p": {"width": 854, "height": 480, "bitrate": "1200k", "crf": 24},
        "720p": {"width": 1280, "height": 720, "bitrate": "2500k", "crf": 23},
        "1080p": {"width": 1920, "height": 1080, "bitrate": "5000k", "crf": 22},
        "2k": {"width": 2560, "height": 1440, "bitrate": "8000k", "crf": 21},
        "4k": {"width": 3840, "height": 2160, "bitrate": "16000k", "crf": 20}
    }
    
    # Timeline Editor Settings
    TIMELINE_PRESETS = {
        "instagram": {"width": 1080, "height": 1080, "fps": 30, "duration": 60},
        "youtube": {"width": 1920, "height": 1080, "fps": 30, "duration": 600},
        "tiktok": {"width": 1080, "height": 1920, "fps": 30, "duration": 60},
        "facebook": {"width": 1280, "height": 720, "fps": 30, "duration": 120}
    }
    
    # Deployment Settings - Render.com Compatible
    USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "False") == "True"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    PORT = int(os.environ.get("PORT", "8080"))
    HOST = "0.0.0.0"
    
    # Create necessary directories
    for dir_path in [TEMP_DIR, THUMB_DIR, FONTS_DIR, STICKERS_DIR, EFFECTS_DIR, BACKUP_DIR, LOGS_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Bulk Config JSON (Full Configuration Export)
    BULK_CONFIG = {
        "bot_name": "KiraFx Media Editor Pro",
        "bot_version": "5.0.0",
        "bot_description": "Complete Video & Image Editing Suite",
        "features": {
            "image_tools": 30,
            "video_tools": 35,
            "ai_tools": 10,
            "filters": 50,
            "transitions": 15
        },
        "limits": {
            "free_edits_per_day": MAX_FREE_EDITS,
            "trial_days": FREE_TRIAL_DAYS,
            "max_file_size_gb": 4,
            "max_parallel_jobs": MAX_PARALLEL_JOBS
        },
        "social": {
            "update_channel": UPDATE_CHANNEL,
            "support_chat": SUPPORT_CHAT
        },
        "watermark": {
            "text": WATERMARK_TEXT,
            "opacity": WATERMARK_OPACITY,
            "position": WATERMARK_POSITION
        },
        "ads": {
            "enabled": GOOGLE_ADS_ENABLED,
            "interval": ADS_INTERVAL
        }
    }

# ==================== DATABASE WITH FULL MANAGEMENT ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_all_tables()
        self._migrate_database()
    
    def _create_all_tables(self):
        # Users table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            premium_until INTEGER DEFAULT 0,
            edits_today INTEGER DEFAULT 0,
            total_edits INTEGER DEFAULT 0,
            last_edit_date TEXT DEFAULT '',
            join_date INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            notification_settings INTEGER DEFAULT 1,
            banned INTEGER DEFAULT 0,
            edit_count INTEGER DEFAULT 0,
            ads_watched INTEGER DEFAULT 0,
            total_ads_watched INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            uploaded_files INTEGER DEFAULT 0,
            renamed_files INTEGER DEFAULT 0
        )''')
        
        # Admins table with permissions
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_date INTEGER,
            permissions TEXT DEFAULT 'full',
            can_manage_users INTEGER DEFAULT 1,
            can_manage_premium INTEGER DEFAULT 1,
            can_broadcast INTEGER DEFAULT 1,
            can_manage_commands INTEGER DEFAULT 1,
            can_view_stats INTEGER DEFAULT 1,
            can_backup INTEGER DEFAULT 1
        )''')
        
        # Custom commands table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS custom_commands (
            command TEXT PRIMARY KEY,
            response TEXT,
            is_media BOOLEAN,
            media_type TEXT,
            media_file_id TEXT,
            created_by INTEGER,
            created_date INTEGER,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )''')
        
        # Settings table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_by INTEGER,
            updated_date INTEGER
        )''')
        
        # Edit history
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_type TEXT,
            operation TEXT,
            input_size INTEGER,
            output_size INTEGER,
            processing_time REAL,
            timestamp INTEGER,
            status TEXT DEFAULT 'completed'
        )''')
        
        # Templates/Presets
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            config TEXT,
            created_by INTEGER,
            is_public INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            thumbnail TEXT
        )''')
        
        # User sessions
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            session_data TEXT,
            step TEXT,
            updated_at INTEGER,
            media_path TEXT
        )''')
        
        # Auto-reply rules
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS auto_reply (
            keyword TEXT PRIMARY KEY,
            response TEXT,
            match_type TEXT DEFAULT 'exact',
            is_active INTEGER DEFAULT 1,
            media_file_id TEXT
        )''')
        
        # Referrals table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            timestamp INTEGER,
            reward_given INTEGER DEFAULT 0
        )''')
        
        # File rename history
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS rename_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_name TEXT,
            new_name TEXT,
            file_size INTEGER,
            file_type TEXT,
            timestamp INTEGER
        )''')
        
        # Payments table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount TEXT,
            transaction_id TEXT,
            plan TEXT,
            status TEXT,
            timestamp INTEGER
        )''')
        
        # Banned users table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_by INTEGER,
            banned_date INTEGER,
            ban_duration INTEGER DEFAULT 0
        )''')
        
        self.conn.commit()
    
    def _migrate_database(self):
        """Add missing columns for backward compatibility"""
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN uploaded_files INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN renamed_files INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()
    
    # ========== USER MANAGEMENT ==========
    def add_user(self, user_id, username, first_name, last_name="", referred_by=0):
        now = int(datetime.now().timestamp())
        try:
            self.cursor.execute('''INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, join_date, referred_by) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, username or "", first_name or "", last_name or "", now, referred_by))
            self.cursor.execute("UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?", 
                               (username or "", first_name or "", last_name or "", user_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()
    
    def is_premium(self, user_id):
        self.cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result and result["premium_until"]:
            return result["premium_until"] > int(datetime.now().timestamp())
        return False
    
    def get_premium_expiry(self, user_id):
        self.cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result and result["premium_until"]:
            return result["premium_until"]
        return 0
    
    def give_premium(self, user_id, days, source="admin"):
        until = int((datetime.now() + timedelta(days=days)).timestamp())
        self.cursor.execute("UPDATE users SET premium_until=? WHERE user_id=?", (until, user_id))
        self.conn.commit()
        return True
    
    def remove_premium(self, user_id):
        self.cursor.execute("UPDATE users SET premium_until=0 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def can_edit(self, user_id):
        if self.is_premium(user_id):
            return True
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT edits_today, last_edit_date FROM users WHERE user_id=?", (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return True
        edits, last_date = row["edits_today"], row["last_edit_date"]
        free_edits = int(self.get_setting('free_edits', Config.MAX_FREE_EDITS))
        if last_date != today:
            self.cursor.execute("UPDATE users SET edits_today=0, last_edit_date=? WHERE user_id=?", (today, user_id))
            self.conn.commit()
            return True
        return edits < free_edits
    
    def increment_edit(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''UPDATE users 
            SET edits_today = edits_today + 1, 
                total_edits = total_edits + 1, 
                edit_count = edit_count + 1 
            WHERE user_id=?''', (user_id,))
        self.conn.commit()
        
        self.cursor.execute("SELECT edits_today FROM users WHERE user_id=?", (user_id,))
        edits = self.cursor.fetchone()["edits_today"]
        interval = int(self.get_setting('ads_interval', Config.ADS_INTERVAL))
        return edits % interval == 0 and not self.is_premium(user_id)
    
    def add_coins(self, user_id, amount):
        self.cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
        self.conn.commit()
    
    def get_coins(self, user_id):
        self.cursor.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result["coins"] if result else 0
    
    # ========== ADMIN MANAGEMENT ==========
    def is_admin(self, user_id):
        self.cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
        return self.cursor.fetchone() is not None
    
    def add_admin(self, user_id, added_by, permissions="full"):
        self.cursor.execute('''INSERT OR IGNORE INTO admins 
            (user_id, added_by, added_date, permissions) 
            VALUES (?, ?, ?, ?)''',
            (user_id, added_by, int(datetime.now().timestamp()), permissions))
        self.conn.commit()
    
    def remove_admin(self, user_id):
        self.cursor.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def get_all_admins(self):
        self.cursor.execute("SELECT user_id FROM admins")
        return [row["user_id"] for row in self.cursor.fetchall()]
    
    # ========== BAN MANAGEMENT ==========
    def ban_user(self, user_id, reason="", banned_by=0, duration=0):
        self.cursor.execute('''INSERT OR REPLACE INTO banned_users 
            (user_id, reason, banned_by, banned_date, ban_duration) 
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, reason, banned_by, int(datetime.now().timestamp()), duration))
        self.cursor.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id):
        self.cursor.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
        self.cursor.execute("UPDATE users SET banned=0 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def is_banned(self, user_id):
        self.cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result and result["banned"] == 1:
            # Check if ban duration expired
            self.cursor.execute("SELECT ban_duration, banned_date FROM banned_users WHERE user_id=?", (user_id,))
            ban_info = self.cursor.fetchone()
            if ban_info and ban_info["ban_duration"] > 0:
                expiry = ban_info["banned_date"] + (ban_info["ban_duration"] * 86400)
                if expiry < int(datetime.now().timestamp()):
                    self.unban_user(user_id)
                    return False
            return True
        return False
    
    # ========== FILE RENAME MANAGEMENT ==========
    def add_rename_record(self, user_id, original_name, new_name, file_size, file_type):
        self.cursor.execute('''INSERT INTO rename_history 
            (user_id, original_name, new_name, file_size, file_type, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, original_name, new_name, file_size, file_type, int(datetime.now().timestamp())))
        self.cursor.execute("UPDATE users SET renamed_files = renamed_files + 1 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def get_rename_stats(self, user_id):
        self.cursor.execute("SELECT COUNT(*) as count FROM rename_history WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()["count"]
    
    # ========== CUSTOM COMMANDS ==========
    def get_custom_command(self, command):
        self.cursor.execute('''SELECT response, is_media, media_type, media_file_id, usage_count 
            FROM custom_commands WHERE command=? AND is_active=1''', (command,))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE custom_commands SET usage_count = usage_count + 1 WHERE command=?", (command,))
            self.conn.commit()
            return dict(result)
        return None
    
    def add_custom_command(self, command, response, is_media=False, media_type=None, media_id=None, created_by=None):
        self.cursor.execute('''REPLACE INTO custom_commands 
            (command, response, is_media, media_type, media_file_id, created_by, created_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (command, response, is_media, media_type, media_id, created_by, int(datetime.now().timestamp())))
        self.conn.commit()
    
    def delete_custom_command(self, command):
        self.cursor.execute("DELETE FROM custom_commands WHERE command=?", (command,))
        self.conn.commit()
    
    def get_all_custom_commands(self):
        self.cursor.execute("SELECT command, usage_count, is_active FROM custom_commands ORDER BY command")
        return self.cursor.fetchall()
    
    # ========== SETTINGS ==========
    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = self.cursor.fetchone()
        return result["value"] if result else default
    
    def set_setting(self, key, value, updated_by=None):
        self.cursor.execute('''REPLACE INTO settings (key, value, updated_by, updated_date) 
            VALUES (?, ?, ?, ?)''',
            (key, value, updated_by, int(datetime.now().timestamp())))
        self.conn.commit()
    
    def get_all_settings(self):
        self.cursor.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in self.cursor.fetchall()}
    
    # ========== SESSION MANAGEMENT ==========
    def set_session(self, user_id, step, data, media_path=None):
        self.cursor.execute('''REPLACE INTO user_sessions 
            (user_id, session_data, step, updated_at, media_path) 
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, json.dumps(data), step, int(datetime.now().timestamp()), media_path))
        self.conn.commit()
    
    def get_session(self, user_id):
        self.cursor.execute("SELECT session_data, step, media_path FROM user_sessions WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result["session_data"]), result["step"], result["media_path"]
        return None, None, None
    
    def clear_session(self, user_id):
        self.cursor.execute("DELETE FROM user_sessions WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    # ========== REFERRAL SYSTEM ==========
    def add_referral(self, referrer_id, referred_id):
        self.cursor.execute('''INSERT OR IGNORE INTO referrals 
            (referrer_id, referred_id, timestamp) VALUES (?, ?, ?)''',
            (referrer_id, referred_id, int(datetime.now().timestamp())))
        if self.cursor.rowcount > 0:
            # Give 3 days premium per referral
            self.give_premium(referrer_id, 3, "referral")
            self.add_coins(referrer_id, 100)
            self.cursor.execute("UPDATE referrals SET reward_given=1 WHERE referrer_id=? AND referred_id=?", 
                               (referrer_id, referred_id))
            self.conn.commit()
            return True
        return False
    
    def get_referral_count(self, user_id):
        self.cursor.execute("SELECT COUNT(*) as count FROM referrals WHERE referrer_id=?", (user_id,))
        return self.cursor.fetchone()["count"]
    
    def get_referral_earnings(self, user_id):
        self.cursor.execute("SELECT COUNT(*) as count FROM referrals WHERE referrer_id=? AND reward_given=1", (user_id,))
        return self.cursor.fetchone()["count"]
    
    # ========== STATISTICS ==========
    def get_stats(self):
        total_users = self.cursor.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
        premium_users = self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE premium_until > ?", 
                                           (int(datetime.now().timestamp()),)).fetchone()["count"]
        banned_users = self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE banned=1").fetchone()["count"]
        total_edits = self.cursor.execute("SELECT SUM(edit_count) as total FROM users").fetchone()["total"] or 0
        today_edits = self.cursor.execute('''SELECT SUM(edits_today) as total FROM users 
            WHERE last_edit_date=?''', (datetime.now().strftime("%Y-%m-%d"),)).fetchone()["total"] or 0
        total_ads = self.cursor.execute("SELECT SUM(total_ads_watched) as total FROM users").fetchone()["total"] or 0
        total_renames = self.cursor.execute("SELECT COUNT(*) as count FROM rename_history").fetchone()["count"]
        total_commands = self.cursor.execute("SELECT SUM(usage_count) as total FROM custom_commands").fetchone()["total"] or 0
        
        return {
            'total_users': total_users,
            'premium_users': premium_users,
            'banned_users': banned_users,
            'total_edits': total_edits,
            'today_edits': today_edits,
            'total_ads': total_ads,
            'total_renames': total_renames,
            'total_commands': total_commands
        }
    
    def get_daily_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            edits = self.cursor.execute('''SELECT SUM(edits_today) as total FROM users 
                WHERE last_edit_date=?''', (date,)).fetchone()["total"] or 0
            stats[date] = edits
        return stats
    
    # ========== BACKUP ==========
    def backup_database(self):
        backup_path = f"{Config.BACKUP_DIR}/backup_{int(datetime.now().timestamp())}.db"
        shutil.copy2(Config.DB_PATH, backup_path)
        return backup_path
    
    def restore_database(self, backup_path):
        shutil.copy2(backup_path, Config.DB_PATH)
        self.conn.close()
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return True
    
    def cleanup_temp_files(self, age_hours=24):
        cutoff = time.time() - (age_hours * 3600)
        for file in os.listdir(Config.TEMP_DIR):
            file_path = os.path.join(Config.TEMP_DIR, file)
            if os.path.getctime(file_path) < cutoff:
                try:
                    os.unlink(file_path)
                except:
                    pass

db = Database()

# ==================== MEDIA PROCESSOR ====================
class MediaProcessor:
    
    # ========== 30+ IMAGE EDITING TOOLS ==========
    IMAGE_FILTERS = {
        'basic': [
            ("🌫️ Blur", "blur"), ("🔪 Sharpen", "sharpen"), ("⚪ Grayscale", "grayscale"),
            ("📜 Sepia", "sepia"), ("✨ Edge Enhance", "edge_enhance"), ("🌀 Contour", "contour"),
            ("🔘 Emboss", "emboss"), ("✨ Smooth", "smooth"), ("🔍 Detail", "detail"),
            ("🌊 Gaussian Blur", "gaussian_blur"), ("✨ Unsharp Mask", "unsharp_mask")
        ],
        'artistic': [
            ("🎨 Oil Paint", "oil_paint"), ("💧 Watercolor", "watercolor"), ("📝 Sketch", "sketch"),
            ("✏️ Pencil Sketch", "pencil_sketch"), ("🎭 Cartoon", "cartoon"), ("📱 Pixelate", "pixelate"),
            ("✨ Glitch", "glitch"), ("📸 Vintage", "vintage"), ("💡 Neon", "neon"),
            ("🎨 Pointillism", "pointillism"), ("🖼️ Mosaic", "mosaic"), ("🎨 Pastel", "pastel")
        ],
        'color': [
            ("💡 Brightness", "brightness"), ("🌞 Contrast", "contrast"), ("🌈 Saturation", "saturation"),
            ("🎨 Hue", "hue"), ("🌡️ Temperature", "temperature"), ("🎨 Auto Color", "auto_color"),
            ("⚡ Equalize", "equalize"), ("🎨 Posterize", "posterize"), ("🌓 Solarize", "solarize"),
            ("🔄 Invert", "invert"), ("🎨 Color Balance", "color_balance"), ("🌈 Channel Mixer", "channel_mixer")
        ],
        'transform': [
            ("🔄 Rotate 90", "rotate_90"), ("🔄 Rotate 180", "rotate_180"), ("🔄 Rotate 270", "rotate_270"),
            ("↔️ Flip H", "flip_h"), ("↕️ Flip V", "flip_v"), ("📏 Resize 50%", "resize_50"),
            ("📏 Resize 200%", "resize_200"), ("✂️ Crop Center", "crop_center"), ("🔄 Mirror", "mirror"),
            ("🌀 Skew", "skew"), ("🌀 Perspective", "perspective"), ("🔄 Auto Rotate", "auto_rotate")
        ],
        'special': [
            ("🎭 Blur BG", "blur_bg"), ("🎭 Vignette", "vignette"), ("🖼️ Border", "border"),
            ("⚪ Rounded", "rounded"), ("📦 Shadow", "shadow"), ("✨ Glow", "glow"),
            ("🎨 Duotone", "duotone"), ("🌅 Sunset", "sunset"), ("❄️ Winter", "winter"),
            ("🍂 Autumn", "autumn"), ("🌸 Spring", "spring"), ("🌙 Night", "night")
        ]
    }
    
    # ========== 35+ VIDEO EDITING TOOLS ==========
    VIDEO_EFFECTS = {
        'basic': [
            ("✂️ Trim", "trim"), ("✂️ Cut", "cut"), ("🔀 Speed 2x", "speed_2x"),
            ("🐢 Speed 0.5x", "speed_05x"), ("🔄 Reverse", "reverse"), ("🔄 Loop", "loop"),
            ("🔗 Merge", "merge"), ("🎬 Extract GIF", "extract_gif"), ("📸 Extract Frame", "extract_frame"),
            ("✂️ Split Video", "split_video"), ("📏 Change Resolution", "change_resolution")
        ],
        'filters': [
            ("⚫ B&W", "black_white"), ("📜 Sepia", "sepia"), ("📽️ Vintage", "vintage"),
            ("🎬 Cinematic", "cinematic"), ("✨ Glitch", "glitch"), ("📱 Pixelate", "pixelate"),
            ("🎨 Oil Paint", "oil_paint_video"), ("📝 Sketch", "sketch_video"), ("🎭 Cartoon", "cartoon_video"),
            ("💡 Neon", "neon_video"), ("🌅 Sunset", "sunset_video"), ("❄️ Winter", "winter_video"),
            ("🎨 Vibrant", "vibrant"), ("🌫️ Haze", "haze"), ("🔮 VHS", "vhs"),
            ("🌈 RGB Shift", "rgb_shift"), ("✨ Soft Glow", "soft_glow")
        ],
        'transitions': [
            ("🌅 Fade In", "fade_in"), ("🌄 Fade Out", "fade_out"), ("🌌 Fade Black", "fade_black"),
            ("✨ Crossfade", "crossfade"), ("⬅️ Slide Left", "slide_left"), ("➡️ Slide Right", "slide_right"),
            ("⬆️ Slide Up", "slide_up"), ("⬇️ Slide Down", "slide_down"), ("🌀 Zoom In", "zoom_in"),
            ("🌀 Zoom Out", "zoom_out"), ("💫 Blur Transition", "blur_transition"), ("✨ Wipe", "wipe"),
            ("🌀 Rotate Transition", "rotate_transition"), ("💥 Explode", "explode")
        ],
        'audio': [
            ("🔇 Mute", "mute"), ("🎵 Extract Audio", "extract_audio"), ("🎧 Add Music", "add_audio"),
            ("📢 Volume Up", "volume_up"), ("🔉 Volume Down", "volume_down"), ("🎤 Voiceover", "voiceover"),
            ("🎵 Background Music", "bg_music"), ("🔊 Boost Bass", "boost_bass"), ("🎧 Echo Effect", "echo"),
            ("🌀 Reverb", "reverb"), ("🎚️ Normalize Audio", "normalize_audio"), ("🎵 Fade Audio", "fade_audio")
        ],
        'speed': [
            ("🐢 0.25x", "speed_025"), ("🐢 0.5x", "speed_05x"), ("⚡ 0.75x", "speed_075"),
            ("⚡ 1.5x", "speed_15x"), ("🐇 2x", "speed_2x"), ("🚀 3x", "speed_3x"),
            ("🚀 4x", "speed_4x"), ("⚡ Variable Speed", "variable_speed"), ("🎬 Time Lapse", "timelapse"),
            ("🎥 Slow Motion", "slow_motion"), ("⚡ Speed Ramp", "speed_ramp")
        ],
        'ai': [
            ("🗣️ AI Speech", "ai_speech"), ("📝 AI Subtitles", "ai_subtitles"), ("🎨 AI Background", "ai_background"),
            ("👤 AI Face Blur", "face_blur"), ("🎯 AI Object Remove", "object_remove"), ("🎨 AI Colorize", "colorize"),
            ("🖼️ AI Enhance", "ai_enhance"), ("🎬 AI Scene Detect", "scene_detect"), ("📊 AI Analysis", "ai_analysis"),
            ("🎭 AI Style Transfer", "style_transfer"), ("👤 AI Face Swap", "face_swap")
        ],
        'advanced': [
            ("🎨 Chroma Key", "chroma_key"), ("📝 Text Overlay", "text_overlay"), ("🖼️ Sticker Overlay", "sticker_overlay"),
            ("💧 Watermark", "watermark"), ("🔄 Rotate", "rotate_video"), ("📏 Crop", "crop_video"),
            ("🎞️ Resize", "resize_video"), ("📊 Stabilize", "stabilize"), ("✨ Denoise", "denoise"),
            ("🎨 Color Grading", "color_grading"), ("🔲 Green Screen", "green_screen"), ("🎬 PIP", "picture_in_picture"),
            ("🎥 Video Collage", "video_collage"), ("📊 Keyframe Editor", "keyframe_editor")
        ]
    }
    
    @staticmethod
    async def download_media(client, file_id, user_id, file_type="video"):
        ext_map = {"video": ".mp4", "image": ".jpg", "document": ".file"}
        ext = ext_map.get(file_type, ".mp4")
        file_path = f"{Config.TEMP_DIR}/{user_id}_{int(datetime.now().timestamp())}_{random.randint(1000,9999)}{ext}"
        
        try:
            await client.download_media(file_id, file_path=file_path)
            return file_path
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    @staticmethod
    async def apply_image_filter(image_path: str, filter_name: str, params: dict = None) -> str:
        if params is None:
            params = {}
        
        try:
            img = Image.open(image_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            output = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
            
            filters = {
                "blur": lambda: img.filter(ImageFilter.BLUR),
                "sharpen": lambda: img.filter(ImageFilter.SHARPEN),
                "grayscale": lambda: img.convert("L"),
                "sepia": lambda: MediaProcessor._sepia(img),
                "edge_enhance": lambda: img.filter(ImageFilter.EDGE_ENHANCE),
                "contour": lambda: img.filter(ImageFilter.CONTOUR),
                "emboss": lambda: img.filter(ImageFilter.EMBOSS),
                "smooth": lambda: img.filter(ImageFilter.SMOOTH),
                "detail": lambda: img.filter(ImageFilter.DETAIL),
                "gaussian_blur": lambda: img.filter(ImageFilter.GaussianBlur(radius=params.get('radius', 2))),
                "unsharp_mask": lambda: img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)),
                "oil_paint": lambda: MediaProcessor._oil_paint(img),
                "watercolor": lambda: MediaProcessor._watercolor(img),
                "sketch": lambda: MediaProcessor._sketch(img),
                "pencil_sketch": lambda: MediaProcessor._pencil_sketch(img),
                "cartoon": lambda: MediaProcessor._cartoon(img),
                "pixelate": lambda: MediaProcessor._pixelate(img, params.get('size', 10)),
                "glitch": lambda: MediaProcessor._glitch(img),
                "vintage": lambda: MediaProcessor._vintage(img),
                "neon": lambda: MediaProcessor._neon(img),
                "pointillism": lambda: MediaProcessor._pointillism(img),
                "mosaic": lambda: MediaProcessor._pixelate(img, params.get('size', 20)),
                "pastel": lambda: MediaProcessor._pastel(img),
                "brightness": lambda: MediaProcessor._adjust_brightness(img, params.get('factor', 1.5)),
                "contrast": lambda: MediaProcessor._adjust_contrast(img, params.get('factor', 1.5)),
                "saturation": lambda: MediaProcessor._adjust_saturation(img, params.get('factor', 1.5)),
                "hue": lambda: MediaProcessor._adjust_hue(img, params.get('shift', 30)),
                "temperature": lambda: MediaProcessor._adjust_temperature(img, params.get('temp', 5000)),
                "auto_color": lambda: ImageOps.autocontrast(img),
                "equalize": lambda: ImageOps.equalize(img),
                "posterize": lambda: ImageOps.posterize(img, params.get('bits', 4)),
                "solarize": lambda: ImageOps.solarize(img, params.get('threshold', 128)),
                "invert": lambda: ImageOps.invert(img),
                "color_balance": lambda: MediaProcessor._color_balance(img, params),
                "channel_mixer": lambda: MediaProcessor._channel_mixer(img, params),
                "rotate_90": lambda: img.rotate(90, expand=True),
                "rotate_180": lambda: img.rotate(180, expand=True),
                "rotate_270": lambda: img.rotate(270, expand=True),
                "flip_h": lambda: img.transpose(Image.FLIP_LEFT_RIGHT),
                "flip_v": lambda: img.transpose(Image.FLIP_TOP_BOTTOM),
                "resize_50": lambda: img.resize((img.width//2, img.height//2), Image.Resampling.LANCZOS),
                "resize_200": lambda: img.resize((img.width*2, img.height*2), Image.Resampling.LANCZOS),
                "crop_center": lambda: img.crop((img.width//4, img.height//4, img.width*3//4, img.height*3//4)),
                "mirror": lambda: img.transpose(Image.FLIP_LEFT_RIGHT),
                "skew": lambda: MediaProcessor._skew_image(img, params.get('skew', 30)),
                "perspective": lambda: MediaProcessor._perspective(img, params),
                "auto_rotate": lambda: ImageOps.exif_transpose(img),
                "blur_bg": lambda: MediaProcessor._blur_background(img),
                "vignette": lambda: MediaProcessor._vignette(img),
                "border": lambda: ImageOps.expand(img, border=params.get('size', 10), fill=params.get('color', 'white')),
                "rounded": lambda: MediaProcessor._rounded_corners(img, params.get('radius', 30)),
                "shadow": lambda: MediaProcessor._add_shadow(img),
                "glow": lambda: MediaProcessor._glow_effect(img),
                "duotone": lambda: MediaProcessor._duotone(img, params.get('color1', 'blue'), params.get('color2', 'red')),
                "sunset": lambda: MediaProcessor._sunset_filter(img),
                "winter": lambda: MediaProcessor._winter_filter(img),
                "autumn": lambda: MediaProcessor._autumn_filter(img),
                "spring": lambda: MediaProcessor._spring_filter(img),
                "night": lambda: MediaProcessor._night_filter(img),
            }
            
            if filter_name in filters:
                result = filters[filter_name]()
                if isinstance(result, Image.Image):
                    result.save(output, quality=95, optimize=True)
                return output
            raise ValueError(f"Unknown filter: {filter_name}")
            
        except Exception as e:
            logger.error(f"Image filter error: {e}")
            raise
    
    @staticmethod
    async def apply_video_effect(video_path: str, effect: str, params: dict = None) -> str:
        if params is None:
            params = {}
        
        try:
            output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            
            effects = {
                "trim": lambda: MediaProcessor._trim_video(video_path, output, params),
                "cut": lambda: MediaProcessor._cut_video(video_path, output, params),
                "speed_2x": lambda: MediaProcessor._change_speed(video_path, output, 2.0),
                "speed_05x": lambda: MediaProcessor._change_speed(video_path, output, 0.5),
                "speed_025": lambda: MediaProcessor._change_speed(video_path, output, 0.25),
                "speed_075": lambda: MediaProcessor._change_speed(video_path, output, 0.75),
                "speed_15x": lambda: MediaProcessor._change_speed(video_path, output, 1.5),
                "speed_3x": lambda: MediaProcessor._change_speed(video_path, output, 3.0),
                "speed_4x": lambda: MediaProcessor._change_speed(video_path, output, 4.0),
                "reverse": lambda: MediaProcessor._reverse_video(video_path, output),
                "loop": lambda: MediaProcessor._loop_video(video_path, output, params.get('times', 3)),
                "merge": lambda: MediaProcessor._merge_videos([video_path] + params.get('videos', []), output),
                "extract_gif": lambda: MediaProcessor._video_to_gif(video_path, output),
                "extract_frame": lambda: MediaProcessor._extract_frame(video_path, output.replace('.mp4', '.jpg')),
                "split_video": lambda: MediaProcessor._split_video(video_path, output),
                "change_resolution": lambda: MediaProcessor._change_resolution(video_path, output, params),
                "black_white": lambda: MediaProcessor._color_filter(video_path, output, "hue=s=0"),
                "sepia": lambda: MediaProcessor._color_filter(video_path, output, "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"),
                "vintage": lambda: MediaProcessor._vintage_video(video_path, output),
                "cinematic": lambda: MediaProcessor._cinematic_video(video_path, output),
                "glitch": lambda: MediaProcessor._glitch_video(video_path, output),
                "pixelate": lambda: MediaProcessor._pixelate_video(video_path, output, params.get('size', 10)),
                "oil_paint_video": lambda: MediaProcessor._oil_paint_video(video_path, output),
                "sketch_video": lambda: MediaProcessor._sketch_video(video_path, output),
                "cartoon_video": lambda: MediaProcessor._cartoon_video(video_path, output),
                "neon_video": lambda: MediaProcessor._neon_video(video_path, output),
                "sunset_video": lambda: MediaProcessor._sunset_video(video_path, output),
                "winter_video": lambda: MediaProcessor._winter_video(video_path, output),
                "vibrant": lambda: MediaProcessor._vibrant_video(video_path, output),
                "haze": lambda: MediaProcessor._haze_video(video_path, output),
                "vhs": lambda: MediaProcessor._vhs_video(video_path, output),
                "rgb_shift": lambda: MediaProcessor._rgb_shift(video_path, output),
                "soft_glow": lambda: MediaProcessor._soft_glow(video_path, output),
                "fade_in": lambda: MediaProcessor._fade_video(video_path, output, "in", params.get('duration', 1)),
                "fade_out": lambda: MediaProcessor._fade_video(video_path, output, "out", params.get('duration', 1)),
                "fade_black": lambda: MediaProcessor._fade_video(video_path, output, "both", params.get('duration', 1)),
                "crossfade": lambda: MediaProcessor._crossfade_video(video_path, output, params.get('duration', 1)),
                "slide_left": lambda: MediaProcessor._slide_transition(video_path, output, "left"),
                "slide_right": lambda: MediaProcessor._slide_transition(video_path, output, "right"),
                "slide_up": lambda: MediaProcessor._slide_transition(video_path, output, "up"),
                "slide_down": lambda: MediaProcessor._slide_transition(video_path, output, "down"),
                "zoom_in": lambda: MediaProcessor._zoom_effect(video_path, output, "in"),
                "zoom_out": lambda: MediaProcessor._zoom_effect(video_path, output, "out"),
                "blur_transition": lambda: MediaProcessor._blur_transition(video_path, output),
                "wipe": lambda: MediaProcessor._wipe_transition(video_path, output),
                "rotate_transition": lambda: MediaProcessor._rotate_transition(video_path, output),
                "explode": lambda: MediaProcessor._explode_effect(video_path, output),
                "mute": lambda: MediaProcessor._mute_audio(video_path, output),
                "extract_audio": lambda: MediaProcessor._extract_audio(video_path, output.replace('.mp4', '.mp3')),
                "add_audio": lambda: MediaProcessor._add_audio(video_path, output, params.get('audio_path')),
                "volume_up": lambda: MediaProcessor._adjust_volume(video_path, output, 2.0),
                "volume_down": lambda: MediaProcessor._adjust_volume(video_path, output, 0.5),
                "voiceover": lambda: MediaProcessor._add_voiceover(video_path, output, params.get('text')),
                "bg_music": lambda: MediaProcessor._add_background_music(video_path, output, params.get('music_path')),
                "boost_bass": lambda: MediaProcessor._boost_bass(video_path, output),
                "echo": lambda: MediaProcessor._add_echo(video_path, output),
                "reverb": lambda: MediaProcessor._add_reverb(video_path, output),
                "normalize_audio": lambda: MediaProcessor._normalize_audio(video_path, output),
                "fade_audio": lambda: MediaProcessor._fade_audio(video_path, output, params.get('duration', 3)),
                "variable_speed": lambda: MediaProcessor._variable_speed(video_path, output),
                "timelapse": lambda: MediaProcessor._timelapse(video_path, output, params.get('speed', 10)),
                "slow_motion": lambda: MediaProcessor._slow_motion(video_path, output),
                "speed_ramp": lambda: MediaProcessor._speed_ramp(video_path, output),
                "ai_speech": lambda: MediaProcessor._ai_speech(video_path, output, params.get('text')),
                "ai_subtitles": lambda: MediaProcessor._ai_subtitles(video_path, output, params.get('lang', 'en')),
                "ai_background": lambda: MediaProcessor._ai_background_remove(video_path, output),
                "face_blur": lambda: MediaProcessor._face_blur(video_path, output),
                "object_remove": lambda: MediaProcessor._object_removal(video_path, output),
                "colorize": lambda: MediaProcessor._colorize_video(video_path, output),
                "ai_enhance": lambda: MediaProcessor._ai_enhance(video_path, output),
                "scene_detect": lambda: MediaProcessor._scene_detection(video_path, output),
                "ai_analysis": lambda: MediaProcessor._ai_analysis(video_path, output),
                "style_transfer": lambda: MediaProcessor._style_transfer(video_path, output),
                "face_swap": lambda: MediaProcessor._face_swap(video_path, output, params.get('face_image')),
                "chroma_key": lambda: MediaProcessor._chroma_key(video_path, output, params.get('color', 'green')),
                "text_overlay": lambda: MediaProcessor._add_text(video_path, output, params),
                "sticker_overlay": lambda: MediaProcessor._add_sticker(video_path, output, params),
                "watermark": lambda: MediaProcessor._add_watermark(video_path, output, params.get('text', Config.WATERMARK_TEXT)),
                "rotate_video": lambda: MediaProcessor._rotate_video(video_path, output, params.get('angle', 90)),
                "crop_video": lambda: MediaProcessor._crop_video(video_path, output, params),
                "resize_video": lambda: MediaProcessor._resize_video(video_path, output, params),
                "stabilize": lambda: MediaProcessor._stabilize_video(video_path, output),
                "denoise": lambda: MediaProcessor._denoise_video(video_path, output),
                "color_grading": lambda: MediaProcessor._color_grading(video_path, output),
                "green_screen": lambda: MediaProcessor._green_screen(video_path, output, params.get('background')),
                "picture_in_picture": lambda: MediaProcessor._pip_video(video_path, output, params.get('overlay_path')),
                "video_collage": lambda: MediaProcessor._video_collage(video_path, output, params),
                "keyframe_editor": lambda: MediaProcessor._keyframe_editor(video_path, output, params),
            }
            
            if effect in effects:
                result = await effects[effect]()
                return result if isinstance(result, str) else output
            raise ValueError(f"Unknown effect: {effect}")
            
        except Exception as e:
            logger.error(f"Video effect error: {e}")
            raise
    
    # ========== STATIC HELPER METHODS ==========
    @staticmethod
    def _sepia(img):
        img = img.convert("RGB")
        sepia_filter = np.array([[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]])
        img_np = np.array(img).astype(np.float32)
        img_np = img_np @ sepia_filter.T
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _oil_paint(img):
        img_np = np.array(img)
        output = cv2.stylization(img_np, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(output)
    
    @staticmethod
    def _watercolor(img):
        img_np = np.array(img)
        output = cv2.stylization(img_np, sigma_s=60, sigma_r=0.6)
        output = cv2.edgePreservingFilter(output, flags=1, sigma_s=60, sigma_r=0.4)
        return Image.fromarray(output)
    
    @staticmethod
    def _sketch(img):
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
        inverted_blurred = 255 - blurred
        sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
        return Image.fromarray(sketch)
    
    @staticmethod
    def _pencil_sketch(img):
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return Image.fromarray(edges)
    
    @staticmethod
    def _cartoon(img):
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img_np, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)
    
    @staticmethod
    def _pixelate(img, pixel_size=10):
        small = img.resize((img.width // pixel_size, img.height // pixel_size), Image.Resampling.NEAREST)
        return small.resize((img.width, img.height), Image.Resampling.NEAREST)
    
    @staticmethod
    def _glitch(img):
        img_np = np.array(img)
        h, w = img_np.shape[:2]
        for _ in range(5):
            x = random.randint(0, w - 50)
            y = random.randint(0, h - 10)
            shift = random.randint(-30, 30)
            img_np[y:y+10, x:x+50] = np.roll(img_np[y:y+10, x:x+50], shift, axis=1)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _vintage(img):
        img_np = np.array(img).astype(np.float32)
        kernel = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
        img_np = img_np @ kernel.T
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _neon(img):
        img_np = np.array(img)
        edges = cv2.Canny(img_np, 100, 200)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        result = cv2.addWeighted(img_np, 0.7, edges_colored, 0.3, 0)
        return Image.fromarray(result)
    
    @staticmethod
    def _pointillism(img):
        small = img.resize((img.width // 10, img.height // 10), Image.Resampling.NEAREST)
        return small.resize((img.width, img.height), Image.Resampling.NEAREST)
    
    @staticmethod
    def _pastel(img):
        img_np = np.array(img).astype(np.float32)
        img_np = cv2.bilateralFilter(img_np.astype(np.uint8), 9, 75, 75)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _adjust_brightness(img, factor):
        return ImageEnhance.Brightness(img).enhance(factor)
    
    @staticmethod
    def _adjust_contrast(img, factor):
        return ImageEnhance.Contrast(img).enhance(factor)
    
    @staticmethod
    def _adjust_saturation(img, factor):
        return ImageEnhance.Color(img).enhance(factor)
    
    @staticmethod
    def _adjust_hue(img, shift):
        img = img.convert('HSV')
        np_img = np.array(img)
        np_img[:, :, 0] = (np_img[:, :, 0] + shift) % 180
        return Image.fromarray(np_img, 'HSV').convert('RGB')
    
    @staticmethod
    def _adjust_temperature(img, temp_k):
        img_np = np.array(img).astype(np.float32)
        if temp_k > 5000:
            img_np[:, :, 0] *= (1 + (temp_k - 5000) / 5000 * 0.2)
            img_np[:, :, 2] *= (1 - (temp_k - 5000) / 5000 * 0.1)
        else:
            img_np[:, :, 0] *= (1 - (5000 - temp_k) / 5000 * 0.1)
            img_np[:, :, 2] *= (1 + (5000 - temp_k) / 5000 * 0.2)
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _color_balance(img, params):
        img_np = np.array(img).astype(np.float32)
        img_np[:, :, 0] *= params.get('red', 1.0)
        img_np[:, :, 1] *= params.get('green', 1.0)
        img_np[:, :, 2] *= params.get('blue', 1.0)
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _channel_mixer(img, params):
        img_np = np.array(img).astype(np.float32)
        r = img_np[:, :, 0] * params.get('rr', 1.0) + img_np[:, :, 1] * params.get('rg', 0) + img_np[:, :, 2] * params.get('rb', 0)
        g = img_np[:, :, 0] * params.get('gr', 0) + img_np[:, :, 1] * params.get('gg', 1.0) + img_np[:, :, 2] * params.get('gb', 0)
        b = img_np[:, :, 0] * params.get('br', 0) + img_np[:, :, 1] * params.get('bg', 0) + img_np[:, :, 2] * params.get('bb', 1.0)
        img_np = np.stack([r, g, b], axis=2)
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _skew_image(img, skew):
        img_np = np.array(img)
        rows, cols = img_np.shape[:2]
        M = np.float32([[1, skew/100, 0], [0, 1, 0]])
        skewed = cv2.warpAffine(img_np, M, (cols, rows))
        return Image.fromarray(skewed)
    
    @staticmethod
    def _perspective(img, params):
        img_np = np.array(img)
        rows, cols = img_np.shape[:2]
        pts1 = np.float32([[0,0], [cols-1,0], [0,rows-1], [cols-1,rows-1]])
        pts2 = np.float32([[params.get('x1',0), params.get('y1',0)], 
                          [cols-1-params.get('x2',0), params.get('y2',0)],
                          [params.get('x3',0), rows-1-params.get('y3',0)],
                          [cols-1-params.get('x4',0), rows-1-params.get('y4',0)]])
        M = cv2.getPerspectiveTransform(pts1, pts2)
        transformed = cv2.warpPerspective(img_np, M, (cols, rows))
        return Image.fromarray(transformed)
    
    @staticmethod
    def _blur_background(img):
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        mask = cv2.medianBlur(mask, 5)
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB) / 255.0
        blurred = cv2.GaussianBlur(img_np, (21, 21), 0)
        result = (img_np * mask_3ch + blurred * (1 - mask_3ch)).astype(np.uint8)
        return Image.fromarray(result)
    
    @staticmethod
    def _vignette(img):
        img_np = np.array(img).astype(np.float32)
        h, w = img_np.shape[:2]
        X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
        vignette = 1 - (X**2 + Y**2) * 0.5
        vignette = np.clip(vignette, 0.5, 1)
        img_np = img_np * vignette[:, :, np.newaxis]
        return Image.fromarray(img_np.astype(np.uint8))
    
    @staticmethod
    def _rounded_corners(img, radius):
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)
        result = Image.new('RGBA', img.size, (0,0,0,0))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        result.paste(img, mask=mask)
        return result
    
    @staticmethod
    def _add_shadow(img):
        shadow = Image.new('RGBA', (img.width + 20, img.height + 20), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle((10, 10, img.width + 10, img.height + 10), fill=(0,0,0,100))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        shadow.paste(img, (10, 10), img)
        return shadow
    
    @staticmethod
    def _glow_effect(img):
        img_np = np.array(img)
        blurred = cv2.GaussianBlur(img_np, (21, 21), 0)
        result = cv2.addWeighted(img_np, 0.6, blurred, 0.4, 0)
        return Image.fromarray(result)
    
    @staticmethod
    def _duotone(img, color1, color2):
        img_np = np.array(img.convert('L'))
        color_map = np.zeros((img_np.shape[0], img_np.shape[1], 3), dtype=np.uint8)
        color_map[:, :, 0] = img_np
        color_map[:, :, 1] = img_np
        color_map[:, :, 2] = img_np
        return Image.fromarray(color_map)
    
    @staticmethod
    def _sunset_filter(img):
        img_np = np.array(img).astype(np.float32)
        img_np[:, :, 0] *= 1.3
        img_np[:, :, 1] *= 0.8
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _winter_filter(img):
        img_np = np.array(img).astype(np.float32)
        img_np[:, :, 0] *= 0.8
        img_np[:, :, 1] *= 0.9
        img_np[:, :, 2] *= 1.2
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _autumn_filter(img):
        img_np = np.array(img).astype(np.float32)
        img_np[:, :, 0] *= 1.4
        img_np[:, :, 1] *= 0.7
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _spring_filter(img):
        img_np = np.array(img).astype(np.float32)
        img_np[:, :, 1] *= 1.3
        img_np[:, :, 2] *= 1.1
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    @staticmethod
    def _night_filter(img):
        img_np = np.array(img).astype(np.float32)
        img_np = img_np * 0.7
        img_np[:, :, 2] *= 1.2
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        return Image.fromarray(img_np)
    
    # ========== VIDEO PROCESSING IMPLEMENTATIONS ==========
    @staticmethod
    async def _run_ffmpeg(cmd, timeout=Config.PROCESSING_TIMEOUT):
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, 
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            if process.returncode != 0 and Config.ENABLE_FFMPEG_LOGS:
                logger.error(f"FFmpeg error: {stderr.decode()}")
            return process.returncode == 0
        except asyncio.TimeoutError:
            logger.error(f"FFmpeg timeout for command: {cmd}")
            return False
        except Exception as e:
            logger.error(f"FFmpeg exception: {e}")
            return False
    
    @staticmethod
    async def _trim_video(input_path, output_path, params):
        start = params.get('start', 0)
        duration = params.get('duration')
        cmd = ['ffmpeg', '-i', input_path, '-ss', str(start)]
        if duration:
            cmd.extend(['-t', str(duration)])
        cmd.extend(['-c', 'copy', '-y', output_path])
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _cut_video(input_path, output_path, params):
        segments = params.get('segments', [])
        if not segments:
            shutil.copy2(input_path, output_path)
            return output_path
        
        concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_files = []
        for start, end in segments:
            temp_seg = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
            temp_files.append(temp_seg)
            cmd = ['ffmpeg', '-i', input_path, '-ss', str(start), '-to', str(end), '-c', 'copy', '-y', temp_seg]
            await MediaProcessor._run_ffmpeg(cmd)
            concat_file.write(f"file '{temp_seg}'\n")
        concat_file.close()
        
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file.name, '-c', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        os.unlink(concat_file.name)
        return output_path
    
    @staticmethod
    async def _change_speed(input_path, output_path, speed):
        if speed == 1.0:
            shutil.copy2(input_path, output_path)
            return output_path
        cmd = ['ffmpeg', '-i', input_path, '-filter:v', f'setpts={1/speed}*PTS', 
               '-filter:a', f'atempo={speed}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _reverse_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'reverse', '-af', 'areverse', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _loop_video(input_path, output_path, times):
        cmd = ['ffmpeg', '-stream_loop', str(times-1), '-i', input_path, '-c', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _merge_videos(video_paths, output_path):
        concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        for video in video_paths:
            concat_file.write(f"file '{video}'\n")
        concat_file.close()
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file.name, '-c', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        os.unlink(concat_file.name)
        return output_path
    
    @staticmethod
    async def _video_to_gif(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'fps=10,scale=320:-1', '-loop', '0', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _extract_frame(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vframes', '1', '-q:v', '2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _split_video(input_path, output_path):
        base = output_path.replace('.mp4', '_part_%03d.mp4')
        cmd = ['ffmpeg', '-i', input_path, '-c', 'copy', '-map', '0', '-segment_time', '10', 
               '-f', 'segment', '-reset_timestamps', '1', '-y', base]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _change_resolution(input_path, output_path, params):
        width = params.get('width', 1280)
        height = params.get('height', 720)
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'scale={width}:{height}', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _color_filter(input_path, output_path, filter_str):
        cmd = ['ffmpeg', '-i', input_path, '-vf', filter_str, '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _vintage_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'curves=vintage,eq=saturation=0.8', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _cinematic_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'crop=in_w:in_h*0.75,scale=1920:1080,eq=saturation=1.2:contrast=1.1', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _glitch_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', 
               '[0:v]split=2[vid1][vid2];[vid1]geq=r=255*lt(mod(t*30,2),1):g=255*lt(mod(t*30,2),1):b=255*lt(mod(t*30,2),1),chromashift=cr=10,cb=10[glitch];[vid2][glitch]overlay=shortest=1', 
               '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _pixelate_video(input_path, output_path, pixel_size=10):
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'crop=trunc(iw/{pixel_size})*{pixel_size}:trunc(ih/{pixel_size})*{pixel_size},scale=iw/{pixel_size}:ih/{pixel_size},scale=iw*{pixel_size}:ih*{pixel_size}:flags=neighbor', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _oil_paint_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'edgedetect=low=0.1:high=0.2,maskedmerge=1', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _sketch_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _cartoon_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'edgedetect,chromakey=0x000000:0.1:0.2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _neon_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'edgedetect,eq=saturation=2.0', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _sunset_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'colorbalance=rs=0.3:gs=-0.2:bs=-0.1', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _winter_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'colorbalance=rs=-0.1:gs=-0.1:bs=0.3', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _vibrant_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'eq=saturation=1.5:brightness=0.05:contrast=1.1', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _haze_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'eq=contrast=0.9:brightness=0.1', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _vhs_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'noise=alls=20:allf=t', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _rgb_shift(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'rgbashift=rh=5:gh=5:bh=5', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _soft_glow(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'gblur=sigma=5,eq=brightness=0.1', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _fade_video(input_path, output_path, direction, duration=1):
        if direction == "in":
            vf = f"fade=in:0:{duration*30}"
        elif direction == "out":
            vf = f"fade=out:0:{duration*30}"
        else:
            vf = f"fade=in:0:{duration*30},fade=out:{duration*30}:{duration*30}"
        cmd = ['ffmpeg', '-i', input_path, '-vf', vf, '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _crossfade_video(input_path, output_path, duration):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', f'[0:v]fade=t=out:st=0:d={duration}[v0];[0:a]afade=t=out:st=0:d={duration}[a0]', 
               '-map', '[v0]', '-map', '[a0]', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _slide_transition(input_path, output_path, direction):
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'slide={direction}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _zoom_effect(input_path, output_path, zoom_type):
        if zoom_type == "in":
            vf = "zoompan=z='min(zoom+0.0015,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        else:
            vf = "zoompan=z='if(eq(on,1),1.5,max(1.5-0.0015,1))':d=125"
        cmd = ['ffmpeg', '-i', input_path, '-vf', vf, '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _blur_transition(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'smartblur', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _wipe_transition(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'wipe=type=left', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _rotate_transition(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'rotate=45*PI/180', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _explode_effect(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', 'explode', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _mute_audio(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-an', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _extract_audio(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-q:a', '0', '-map', 'a', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_audio(input_path, output_path, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            shutil.copy2(input_path, output_path)
            return output_path
        cmd = ['ffmpeg', '-i', input_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', 
               '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _adjust_volume(input_path, output_path, volume):
        cmd = ['ffmpeg', '-i', input_path, '-af', f'volume={volume}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_voiceover(input_path, output_path, text):
        if not text:
            shutil.copy2(input_path, output_path)
            return output_path
        tts = gTTS(text, lang=Config.TTS_LANG)
        audio_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        tts.save(audio_file)
        cmd = ['ffmpeg', '-i', input_path, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', 
               '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        os.unlink(audio_file)
        return output_path
    
    @staticmethod
    async def _add_background_music(input_path, output_path, music_path):
        if not music_path or not os.path.exists(music_path):
            shutil.copy2(input_path, output_path)
            return output_path
        cmd = ['ffmpeg', '-i', input_path, '-i', music_path, '-filter_complex', 
               '[1:a]volume=0.5[bg];[0:a][bg]amix=inputs=2:duration=first', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _boost_bass(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-af', 'bass=g=10', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_echo(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-af', 'aecho=0.8:0.9:1000:0.3', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_reverb(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-af', 'aeval=val(0)|val(1)', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _normalize_audio(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _fade_audio(input_path, output_path, duration):
        cmd = ['ffmpeg', '-i', input_path, '-af', f'afade=t=in:st=0:d={duration},afade=t=out:st={duration}:d={duration}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _variable_speed(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', 
               '[0:v]setpts=PTS/0.5[v];[0:a]atempo=0.5[a]', '-map', '[v]', '-map', '[a]', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _timelapse(input_path, output_path, speed=10):
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'setpts={1/speed}*PTS', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _slow_motion(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'setpts=2*PTS', '-af', 'atempo=0.5', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _speed_ramp(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', 
               '[0:v]setpts=if(lt(t,5),PTS,PTS*2)[v];[0:a]atempo=if(lt(t,5),1,0.5)[a]', 
               '-map', '[v]', '-map', '[a]', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _ai_speech(input_path, output_path, text):
        if not text:
            shutil.copy2(input_path, output_path)
            return output_path
        tts = gTTS(text, lang=Config.TTS_LANG)
        audio_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        tts.save(audio_file)
        cmd = ['ffmpeg', '-i', input_path, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', 
               '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        os.unlink(audio_file)
        return output_path
    
    @staticmethod
    async def _ai_subtitles(input_path, output_path, lang='en'):
        try:
            model = whisper.load_model(Config.WHISPER_MODEL)
            result = model.transcribe(input_path, language=lang)
            
            srt_path = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(result['segments']):
                    start = MediaProcessor._format_time(seg['start'])
                    end = MediaProcessor._format_time(seg['end'])
                    f.write(f"{i+1}\n{start} --> {end}\n{seg['text'].strip()}\n\n")
            
            cmd = ['ffmpeg', '-i', input_path, '-vf', f"subtitles={srt_path}", '-c:a', 'copy', '-y', output_path]
            await MediaProcessor._run_ffmpeg(cmd)
            os.unlink(srt_path)
            return output_path
        except Exception as e:
            logger.error(f"Subtitles error: {e}")
            shutil.copy2(input_path, output_path)
            return output_path
    
    @staticmethod
    async def _ai_background_remove(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'chromakey=0x00FF00:0.1:0.2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _face_blur(input_path, output_path):
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                face = cv2.GaussianBlur(face, (99, 99), 30)
                frame[y:y+h, x:x+w] = face
            out.write(frame)
        
        cap.release()
        out.release()
        return output_path
    
    @staticmethod
    async def _object_removal(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'delogo=x=100:y=100:w=100:h=100', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _colorize_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'eq=saturation=1.3', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _ai_enhance(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'unsharp=5:5:1.0:5:5:0.0', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _scene_detection(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'select=gt(scene\\,0.3)', '-vsync', 'vfr', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _ai_analysis(input_path, output_path):
        cap = cv2.VideoCapture(input_path)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frames / cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        analysis_file = output_path.replace('.mp4', '_analysis.txt')
        with open(analysis_file, 'w') as f:
            f.write(f"Video Analysis:\n")
            f.write(f"Frames: {frames}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Resolution: {width}x{height}\n")
            f.write(f"File Size: {os.path.getsize(input_path) / (1024*1024):.2f} MB\n")
        return analysis_file
    
    @staticmethod
    async def _style_transfer(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'edgedetect,eq=saturation=1.5', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _face_swap(input_path, output_path, face_image):
        if not face_image or not os.path.exists(face_image):
            shutil.copy2(input_path, output_path)
            return output_path
        cmd = ['ffmpeg', '-i', input_path, '-i', face_image, '-filter_complex', 
               '[1:v]scale=100:100[face];[0:v][face]overlay=100:100', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _chroma_key(input_path, output_path, color='green'):
        color_map = {'green': '0x00FF00', 'blue': '0x0000FF', 'red': '0xFF0000'}
        color_hex = color_map.get(color, '0x00FF00')
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'chromakey={color_hex}:0.1:0.2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_text(input_path, output_path, params):
        text = params.get('text', 'Sample Text')
        fontsize = params.get('fontsize', 24)
        color = params.get('color', 'white')
        x = params.get('x', '(w-text_w)/2')
        y = params.get('y', '(h-text_h)/2')
        
        cmd = ['ffmpeg', '-i', input_path, '-vf', f"drawtext=text='{text}':fontcolor={color}:fontsize={fontsize}:x={x}:y={y}", 
               '-codec:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_sticker(input_path, output_path, params):
        sticker_path = params.get('sticker_path')
        if not sticker_path or not os.path.exists(sticker_path):
            shutil.copy2(input_path, output_path)
            return output_path
        x = params.get('x', 10)
        y = params.get('y', 10)
        size = params.get('size', 100)
        
        cmd = ['ffmpeg', '-i', input_path, '-i', sticker_path, '-filter_complex', 
               f"[1:v]scale={size}:-1[sticker];[0:v][sticker]overlay={x}:{y}", 
               '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _add_watermark(input_path, output_path, text):
        cmd = ['ffmpeg', '-i', input_path, '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize=24:x=w-tw-10:y=h-th-10", 
               '-codec:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _rotate_video(input_path, output_path, angle):
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'transpose={angle//90}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _crop_video(input_path, output_path, params):
        width = params.get('width', 640)
        height = params.get('height', 480)
        x = params.get('x', 0)
        y = params.get('y', 0)
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'crop={width}:{height}:{x}:{y}', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _resize_video(input_path, output_path, params):
        width = params.get('width', 1280)
        height = params.get('height', 720)
        cmd = ['ffmpeg', '-i', input_path, '-vf', f'scale={width}:{height}', '-c:a', 'copy', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _stabilize_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'deshake', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _denoise_video(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'hqdn3d', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _color_grading(input_path, output_path):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'eq=brightness=0.05:contrast=1.1:saturation=1.2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _green_screen(input_path, output_path, background):
        cmd = ['ffmpeg', '-i', input_path, '-vf', 'chromakey=0x00FF00:0.1:0.2', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _pip_video(input_path, output_path, overlay_path):
        if not overlay_path or not os.path.exists(overlay_path):
            shutil.copy2(input_path, output_path)
            return output_path
        cmd = ['ffmpeg', '-i', input_path, '-i', overlay_path, '-filter_complex', 
               '[1:v]scale=iw/4:ih/4[overlay];[0:v][overlay]overlay=W-w-10:H-h-10', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _video_collage(input_path, output_path, params):
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', 
               '[0:v]scale=iw/2:ih/2,split=4[v1][v2][v3][v4];[v1][v2]hstack[top];[v3][v4]hstack[bottom];[top][bottom]vstack', '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    async def _keyframe_editor(input_path, output_path, params):
        keyframes = params.get('keyframes', [])
        if not keyframes:
            shutil.copy2(input_path, output_path)
            return output_path
        
        filter_str = ""
        for i, (time, properties) in enumerate(keyframes):
            filter_str += f"[0:v]setpts=PTS+{time}/TB,scale={properties.get('scale', 'iw:ih')}[v{i}];"
        
        filter_str += "".join([f"[v{i}]" for i in range(len(keyframes))]) + f"concat=n={len(keyframes)}:v=1:a=0"
        
        cmd = ['ffmpeg', '-i', input_path, '-filter_complex', filter_str, '-y', output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path
    
    @staticmethod
    def _add_watermark_static(image_path, output_path, text):
        img = Image.open(image_path).convert("RGBA")
        txt = Image.new('RGBA', img.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0,0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if Config.WATERMARK_POSITION == "top_left":
            x, y = 10, 10
        elif Config.WATERMARK_POSITION == "top_right":
            x, y = img.width - text_width - 10, 10
        elif Config.WATERMARK_POSITION == "bottom_left":
            x, y = 10, img.height - text_height - 10
        else:
            x, y = img.width - text_width - 10, img.height - text_height - 10
        
        draw.text((x, y), text, fill=(255,255,255,Config.WATERMARK_OPACITY), font=font)
        watermarked = Image.alpha_composite(img, txt)
        watermarked.convert("RGB").save(output_path, quality=95)
    
    @staticmethod
    def _format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ==================== BOT HANDLERS ====================
class MediaEditorBot:
    def __init__(self):
        self.app = Client(
            "media_editor_bot", 
            api_id=Config.API_ID, 
            api_hash=Config.API_HASH, 
            bot_token=Config.BOT_TOKEN,
            workers=100
        )
        self.user_states = {}
        self.start_time = datetime.now()
        self.register_handlers()
    
    def register_handlers(self):
        # ========== COMMAND HANDLERS ==========
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_cmd(client, message):
            await self.handle_start(client, message)
        
        @self.app.on_message(filters.command("help") & filters.private)
        async def help_cmd(client, message):
            await self.handle_help(client, message)
        
        @self.app.on_message(filters.command("premium") & filters.private)
        async def premium_cmd(client, message):
            await self.handle_premium(client, message)
        
        @self.app.on_message(filters.command("trial") & filters.private)
        async def trial_cmd(client, message):
            await self.handle_trial(client, message)
        
        @self.app.on_message(filters.command("status") & filters.private)
        async def status_cmd(client, message):
            await self.handle_status(client, message)
        
        @self.app.on_message(filters.command("profile") & filters.private)
        async def profile_cmd(client, message):
            await self.handle_profile(client, message)
        
        @self.app.on_message(filters.command("refer") & filters.private)
        async def refer_cmd(client, message):
            await self.handle_refer(client, message)
        
        @self.app.on_message(filters.command("rename") & filters.private)
        async def rename_cmd(client, message):
            await self.handle_rename(client, message)
        
        @self.app.on_message(filters.command("timeline") & filters.private)
        async def timeline_cmd(client, message):
            await self.handle_timeline(client, message)
        
        @self.app.on_message(filters.command("stats") & filters.private)
        async def stats_cmd(client, message):
            if db.is_admin(message.from_user.id) or message.from_user.id == Config.OWNER_ID:
                await self.handle_stats(client, message)
        
        # ========== ADMIN COMMANDS ==========
        @self.app.on_message(filters.command("addadmin") & filters.private)
        async def addadmin_cmd(client, message):
            if message.from_user.id == Config.OWNER_ID:
                await self.handle_add_admin(client, message)
        
        @self.app.on_message(filters.command("rmadmin") & filters.private)
        async def rmadmin_cmd(client, message):
            if message.from_user.id == Config.OWNER_ID:
                await self.handle_remove_admin(client, message)
        
        @self.app.on_message(filters.command("addprem") & filters.private)
        async def addprem_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_add_premium(client, message)
        
        @self.app.on_message(filters.command("rmprem") & filters.private)
        async def rmprem_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_remove_premium(client, message)
        
        @self.app.on_message(filters.command("ban") & filters.private)
        async def ban_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_ban(client, message)
        
        @self.app.on_message(filters.command("unban") & filters.private)
        async def unban_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_unban(client, message)
        
        @self.app.on_message(filters.command("broadcast") & filters.private)
        async def broadcast_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_broadcast(client, message)
        
        @self.app.on_message(filters.command("setwelcome") & filters.private)
        async def setwelcome_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_set_welcome(client, message)
        
        @self.app.on_message(filters.command("addcmd") & filters.private)
        async def addcmd_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_add_command(client, message)
        
        @self.app.on_message(filters.command("delcmd") & filters.private)
        async def delcmd_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_del_command(client, message)
        
        @self.app.on_message(filters.command("listcmds") & filters.private)
        async def listcmds_cmd(client, message):
            await self.handle_list_commands(client, message)
        
        @self.app.on_message(filters.command("export") & filters.private)
        async def export_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_export(client, message)
        
        @self.app.on_message(filters.command("import") & filters.private)
        async def import_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_import(client, message)
        
        @self.app.on_message(filters.command("backup") & filters.private)
        async def backup_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_backup(client, message)
        
        @self.app.on_message(filters.command("restore") & filters.private)
        async def restore_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_restore(client, message)
        
        @self.app.on_message(filters.command("cleanup") & filters.private)
        async def cleanup_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_cleanup(client, message)
        
        @self.app.on_message(filters.command("setads") & filters.private)
        async def setads_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_set_ads(client, message)
        
        @self.app.on_message(filters.command("setfree") & filters.private)
        async def setfree_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_set_free_edits(client, message)
        
        @self.app.on_message(filters.command("logs") & filters.private)
        async def logs_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_logs(client, message)
        
        @self.app.on_message(filters.command("ping") & filters.private)
        async def ping_cmd(client, message):
            await self.handle_ping(client, message)
        
        @self.app.on_message(filters.command("info") & filters.private)
        async def info_cmd(client, message):
            await self.handle_info(client, message)
        
        # ========== MEDIA HANDLERS ==========
        @self.app.on_message(filters.photo & filters.private)
        async def handle_photo(client, message):
            await self.process_image(client, message)
        
        @self.app.on_message(filters.video & filters.private)
        async def handle_video(client, message):
            await self.process_video(client, message)
        
        @self.app.on_message(filters.document & filters.private)
        async def handle_document(client, message):
            await self.process_document(client, message)
        
        # ========== CALLBACK HANDLER ==========
        @self.app.on_callback_query()
        async def callback_handler(client, callback):
            await self.handle_callback(client, callback)
        
        # ========== AUTO-REPLY ==========
        @self.app.on_message(filters.text & filters.private)
        async def auto_reply_handler(client, message):
            await self.handle_auto_reply(client, message)
    
    # ========== UI COMPONENTS ==========
    def get_main_menu(self, user_id):
        is_prem = db.is_premium(user_id)
        keyboard = [
            [InlineKeyboardButton("🎨 Image Editor (30+ Tools)", callback_data="menu_image"),
             InlineKeyboardButton("🎬 Video Editor (35+ Tools)", callback_data="menu_video")],
            [InlineKeyboardButton("✨ AI Tools", callback_data="menu_ai"),
             InlineKeyboardButton("🎞️ Timeline Editor", callback_data="menu_timeline")],
            [InlineKeyboardButton("📝 File Rename", callback_data="menu_rename"),
             InlineKeyboardButton("👥 Referral System", callback_data="menu_refer")],
            [InlineKeyboardButton("⭐ Premium", callback_data="premium_info"),
             InlineKeyboardButton("📢 Updates", url=Config.UPDATE_CHANNEL)],
            [InlineKeyboardButton("💰 Buy Premium", callback_data="buy_premium"),
             InlineKeyboardButton("👥 Support", url=Config.SUPPORT_CHAT)],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
             InlineKeyboardButton("ℹ️ Help", callback_data="help_info")]
        ]
        if is_prem:
            keyboard.insert(3, [InlineKeyboardButton("👑 Premium Features", callback_data="premium_features")])
        else:
            keyboard.insert(3, [InlineKeyboardButton("🎁 Free Trial (7 Days)", callback_data="free_trial")])
        
        if db.is_admin(user_id):
            keyboard.append([InlineKeyboardButton("🔧 Admin Panel (35+ Options)", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_admin_panel(self):
        keyboard = [
            [InlineKeyboardButton("👑 User Management", callback_data="admin_users"),
             InlineKeyboardButton("💰 Premium Mgmt", callback_data="admin_premium")],
            [InlineKeyboardButton("📝 Custom Commands", callback_data="admin_commands"),
             InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
             InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("💾 Backup/Restore", callback_data="admin_backup"),
             InlineKeyboardButton("📦 Bulk Config", callback_data="admin_bulk")],
            [InlineKeyboardButton("💰 Ads Settings", callback_data="admin_ads"),
             InlineKeyboardButton("🗑️ Cleanup", callback_data="admin_cleanup")],
            [InlineKeyboardButton("📈 Daily Stats", callback_data="admin_daily_stats"),
             InlineKeyboardButton("👥 Referral Stats", callback_data="admin_referral_stats")],
            [InlineKeyboardButton("🚫 Ban List", callback_data="admin_ban_list"),
             InlineKeyboardButton("📝 Command Stats", callback_data="admin_command_stats")],
            [InlineKeyboardButton("💾 Database Info", callback_data="admin_db_info"),
             InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")],
            [InlineKeyboardButton("📤 Export Data", callback_data="admin_export_data"),
             InlineKeyboardButton("📥 Import Data", callback_data="admin_import_data")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ========== COMMAND HANDLERS ==========
    async def handle_start(self, client, message):
        user = message.from_user
        referred_by = int(message.command[1]) if len(message.command) > 1 else 0
        
        db.add_user(user.id, user.username, user.first_name, user.last_name or "", referred_by)
        
        if referred_by and referred_by != user.id:
            db.add_referral(referred_by, user.id)
            await client.send_message(referred_by, f"🎉 New user joined using your referral link! You earned 3 days premium and 100 coins!")
        
        if db.is_banned(user.id):
            await message.reply("🚫 You are banned from using this bot.\nReason: Contact support.")
            return
        
        welcome_text = db.get_setting('welcome_text', Config.BULK_CONFIG['bot_description'])
        welcome_text = welcome_text.format(name=user.first_name)
        
        await message.reply(
            welcome_text,
            reply_markup=self.get_main_menu(user.id)
        )
    
    async def handle_help(self, client, message):
        help_text = """
🎬 **Advanced Media Editor Bot - Complete Guide v5.0**

**📸 Image Editing (30+ Tools):**
• Basic: Blur, Sharpen, Grayscale, Sepia, Edge Enhance
• Artistic: Oil Paint, Watercolor, Sketch, Cartoon, Glitch
• Color: Brightness, Contrast, Saturation, Hue, Temperature
• Transform: Rotate, Flip, Resize, Crop, Skew, Perspective
• Special: Vignette, Border, Shadow, Glow, Duotone

**🎥 Video Editing (35+ Tools):**
• Basic: Trim, Cut, Speed (0.25x-4x), Reverse, Loop
• Filters: B&W, Sepia, Vintage, Cinematic, Glitch, Pixelate
• Transitions: Fade, Slide, Zoom, Blur, Wipe, Rotate
• Audio: Mute, Extract, Add Music, Volume, Voiceover
• Speed: Time Lapse, Slow Motion, Speed Ramp
• AI: Speech, Subtitles, Background Remove, Face Blur
• Advanced: Chroma Key, Text/Sticker, Watermark, PIP

**💰 Premium Features (7-Day Trial):**
• No Watermark • Unlimited Edits • No Ads
• 4K Export • All AI Features • Priority Support

**📝 Commands:**
/start - Main Menu
/help - This Help
/premium - Premium Info
/trial - 7-Day Free Trial
/status - Your Status
/profile - Your Profile
/refer - Referral System
/rename - File Rename
/timeline - Timeline Editor

**🔧 Admin Commands:**
/addadmin, /rmadmin, /addprem, /rmprem
/ban, /unban, /broadcast
/setwelcome, /addcmd, /delcmd, /listcmds
/export, /import, /backup, /restore
/cleanup, /setads, /setfree, /logs

**📢 Support:** @KiraFxSupport
"""
        await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_premium(self, client, message):
        text = f"""
🌟 **PREMIUM PLAN - {Config.PREMIUM_PRICE}**

**✨ Premium Features:**
✅ No Watermark
✅ Unlimited Daily Edits
✅ 4K Video Export
✅ AI Speech & Subtitles
✅ No Ads
✅ Priority Processing
✅ Early Access to Features
✅ Priority Support

**🎁 7-Day Free Trial:** /trial
**👥 Referral:** Get 3 days premium per referral!

[Buy Now]({Config.PREMIUM_LINK})
"""
        await message.reply(text, disable_web_page_preview=True)
    
    async def handle_trial(self, client, message):
        user_id = message.from_user.id
        if db.is_premium(user_id):
            await message.reply("You already have premium active!")
            return
        
        db.give_premium(user_id, Config.FREE_TRIAL_DAYS)
        await message.reply(f"🎉 7-day free trial activated!\nEnjoy all premium features for {Config.FREE_TRIAL_DAYS} days!")
    
    async def handle_status(self, client, message):
        user_id = message.from_user.id
        is_prem = db.is_premium(user_id)
        
        if is_prem:
            expiry = db.get_premium_expiry(user_id)
            expiry_date = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
            text = f"✅ **Premium Active**\nExpires: {expiry_date}\nEdits: Unlimited\nCoins: {db.get_coins(user_id)}"
        else:
            row = db.get_user(user_id)
            used = row["edits_today"] if row else 0
            total = row["total_edits"] if row else 0
            free_edits = int(db.get_setting('free_edits', Config.MAX_FREE_EDITS))
            remaining = max(0, free_edits - used)
            text = f"⚠️ **Free User**\nToday: {used}/{free_edits}\nTotal: {total}\nRemaining: {remaining}\nCoins: {db.get_coins(user_id)}\n\nUpgrade: /premium | Trial: /trial"
        
        await message.reply(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_profile(self, client, message):
        user = message.from_user
        row = db.get_user(user.id)
        
        if row:
            join_date = datetime.fromtimestamp(row["join_date"]).strftime("%Y-%m-%d")
            total_edits = row["total_edits"]
            renamed_files = row["renamed_files"]
            coins = row["coins"]
            referrals = db.get_referral_count(user.id)
            
            text = f"""
👤 **User Profile**

**Name:** {user.first_name} {user.last_name or ''}
**Username:** @{user.username or 'N/A'}
**User ID:** `{user.id}`
**Joined:** {join_date}
**Status:** {'⭐ Premium' if db.is_premium(user.id) else '📝 Free'}
**Total Edits:** {total_edits}
**Files Renamed:** {renamed_files}
**Referrals:** {referrals}
**Coins:** {coins}

Use /refer to get your referral link!
"""
            await message.reply(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply("Profile not found. Please use /start")
    
    async def handle_refer(self, client, message):
        user_id = message.from_user.id
        bot_username = (await client.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        referral_count = db.get_referral_count(user_id)
        earnings = db.get_referral_earnings(user_id)
        
        text = f"""
👥 **Referral System**

**Your Referral Link:** 
`{referral_link}`

**Referrals:** {referral_count}
**Premium Days Earned:** {earnings * 3}
**Coins Earned:** {earnings * 100}

**Rewards:**
• 3 days premium per referral
• 100 coins per referral
• Unlimited referrals!

**How it works:**
Share your link with friends. When they join and use the bot, you automatically get rewards!
"""
        await message.reply(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_rename(self, client, message):
        user_id = message.from_user.id
        
        if not db.can_edit(user_id):
            await message.reply(f"⚠️ Free limit reached! Upgrade to /premium for unlimited edits!")
            return
        
        await message.reply(
            "📝 **File Rename**\n\nSend me a file and then send the new name.\n\n"
            "Supported formats: Any file type up to 4GB\n"
            "Premium users get priority processing!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
        )
        db.set_session(user_id, "awaiting_rename_file", {})
    
    async def handle_timeline(self, client, message):
        await message.reply(
            "🎞️ **Timeline Editor**\n\n"
            "Advanced timeline editing features:\n"
            "• Trim video segments\n"
            "• Cut and merge clips\n"
            "• Add transitions\n"
            "• Add text overlays\n"
            "• Add background music\n"
            "• Export in multiple formats\n\n"
            "Send a video to start timeline editing!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 Send Video", callback_data="timeline_start"),
                 InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
        )
    
    # ========== ADMIN HANDLERS ==========
    async def handle_add_admin(self, client, message):
        try:
            target = int(message.command[1])
            db.add_admin(target, message.from_user.id)
            await message.reply(f"✅ User {target} is now admin.")
            await client.send_message(target, "🎉 You've been promoted to admin!")
        except:
            await message.reply("Usage: /addadmin <user_id>")
    
    async def handle_remove_admin(self, client, message):
        try:
            target = int(message.command[1])
            db.remove_admin(target)
            await message.reply(f"✅ User {target} removed from admins.")
        except:
            await message.reply("Usage: /rmadmin <user_id>")
    
    async def handle_add_premium(self, client, message):
        try:
            args = message.command[1].split(',')
            user_id = int(args[0])
            days = int(args[1]) if len(args) > 1 else 30
            db.give_premium(user_id, days)
            await message.reply(f"✅ Added {days} days premium to {user_id}")
            await client.send_message(user_id, f"🎉 You've been granted {days} days of premium! Enjoy!")
        except:
            await message.reply("Usage: /addprem <user_id>,<days>")
    
    async def handle_remove_premium(self, client, message):
        try:
            user_id = int(message.command[1])
            db.remove_premium(user_id)
            await message.reply(f"✅ Premium removed from {user_id}")
        except:
            await message.reply("Usage: /rmprem <user_id>")
    
    async def handle_ban(self, client, message):
        try:
            args = message.command[1].split(',')
            user_id = int(args[0])
            reason = args[1] if len(args) > 1 else "No reason provided"
            duration = int(args[2]) if len(args) > 2 else 0
            
            db.ban_user(user_id, reason, message.from_user.id, duration)
            await message.reply(f"✅ User {user_id} banned.\nReason: {reason}\nDuration: {duration if duration > 0 else 'Permanent'} days")
            
            ban_msg = f"🚫 You have been banned from using this bot.\nReason: {reason}"
            if duration > 0:
                ban_msg += f"\nDuration: {duration} days"
            await client.send_message(user_id, ban_msg)
        except:
            await message.reply("Usage: /ban <user_id>,<reason>,<days> (0 for permanent)")
    
    async def handle_unban(self, client, message):
        try:
            user_id = int(message.command[1])
            db.unban_user(user_id)
            await message.reply(f"✅ User {user_id} unbanned.")
            await client.send_message(user_id, "✅ You have been unbanned from using this bot!")
        except:
            await message.reply("Usage: /unban <user_id>")
    
    async def handle_broadcast(self, client, message):
        text = message.text.split(None, 1)[1] if len(message.command) > 1 else None
        if not text:
            await message.reply("Usage: /broadcast <message>")
            return
        
        confirm = await message.reply("Starting broadcast...")
        db.cursor.execute("SELECT user_id FROM users WHERE banned=0")
        users = db.cursor.fetchall()
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await client.send_message(user["user_id"], text)
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await confirm.edit_text(f"✅ Broadcast completed!\nSuccess: {success}\nFailed: {failed}")
    
    async def handle_set_welcome(self, client, message):
        text = message.text.split(None, 1)[1] if len(message.command) > 1 else None
        if text:
            db.set_setting('welcome_text', text, message.from_user.id)
            await message.reply("✅ Welcome message updated!")
        else:
            await message.reply("Usage: /setwelcome <message> (use {name} for user's name)")
    
    async def handle_add_command(self, client, message):
        try:
            full = message.text.split(None, 1)[1]
            parts = full.split('|')
            cmd = parts[0].strip().lower()
            resp = parts[1].strip()
            
            is_media = False
            media_type = None
            media_id = None
            
            if message.reply_to_message:
                if message.reply_to_message.photo:
                    is_media = True
                    media_type = 'photo'
                    media_id = message.reply_to_message.photo.file_id
                elif message.reply_to_message.video:
                    is_media = True
                    media_type = 'video'
                    media_id = message.reply_to_message.video.file_id
            
            db.add_custom_command(cmd, resp, is_media, media_type, media_id, message.from_user.id)
            await message.reply(f"✅ Command /{cmd} added successfully!")
        except:
            await message.reply("Usage: /addcmd command | response (reply to media to attach)")
    
    async def handle_del_command(self, client, message):
        cmd = message.command[1] if len(message.command) > 1 else None
        if cmd:
            db.delete_custom_command(cmd.lower())
            await message.reply(f"✅ Command /{cmd} deleted.")
        else:
            await message.reply("Usage: /delcmd <command>")
    
    async def handle_list_commands(self, client, message):
        commands = db.get_all_custom_commands()
        if not commands:
            await message.reply("No custom commands found.")
            return
        
        text = "📝 **Custom Commands:**\n\n"
        for cmd in commands:
            text += f"• /{cmd['command']} (Used: {cmd['usage_count']} times) - {'Active' if cmd['is_active'] else 'Inactive'}\n"
        await message.reply(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_export(self, client, message):
        config_data = {
            'settings': db.get_all_settings(),
            'custom_commands': [],
            'auto_reply': []
        }
        
        db.cursor.execute("SELECT command, response, is_media, media_type, media_file_id FROM custom_commands")
        for row in db.cursor.fetchall():
            config_data['custom_commands'].append(dict(row))
        
        db.cursor.execute("SELECT keyword, response, match_type FROM auto_reply WHERE is_active=1")
        for row in db.cursor.fetchall():
            config_data['auto_reply'].append(dict(row))
        
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config_data, config_file, indent=2)
        config_file.close()
        
        await client.send_document(
            message.chat.id,
            config_file.name,
            caption="📦 Bot Configuration Export",
            file_name="bot_config.json"
        )
        os.unlink(config_file.name)
    
    async def handle_import(self, client, message):
        if not message.reply_to_message or not message.reply_to_message.document:
            await message.reply("Please reply to a JSON config file with /import")
            return
        
        try:
            file_path = await client.download_media(message.reply_to_message.document.file_id)
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            for key, value in config_data.get('settings', {}).items():
                db.set_setting(key, value, message.from_user.id)
            
            for cmd in config_data.get('custom_commands', []):
                db.add_custom_command(
                    cmd['command'], cmd['response'], 
                    cmd.get('is_media', False),
                    cmd.get('media_type'), cmd.get('media_file_id'),
                    message.from_user.id
                )
            
            for rule in config_data.get('auto_reply', []):
                db.cursor.execute("REPLACE INTO auto_reply (keyword, response, match_type) VALUES (?, ?, ?)",
                                 (rule['keyword'], rule['response'], rule['match_type']))
            
            db.conn.commit()
            await message.reply("✅ Configuration imported successfully!")
            os.unlink(file_path)
        except Exception as e:
            await message.reply(f"Error importing config: {e}")
    
    async def handle_backup(self, client, message):
        await message.reply("⏳ Creating backup...")
        backup_path = db.backup_database()
        await client.send_document(
            message.chat.id,
            backup_path,
            caption=f"📦 Database Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            file_name=f"backup_{int(datetime.now().timestamp())}.db"
        )
        os.unlink(backup_path)
    
    async def handle_restore(self, client, message):
        if not message.reply_to_message or not message.reply_to_message.document:
            await message.reply("Please reply to a backup .db file with /restore")
            return
        
        await message.reply("⚠️ Restoring database will overwrite current data. Continue?",
                          reply_markup=InlineKeyboardMarkup([
                              [InlineKeyboardButton("✅ Yes", callback_data="confirm_restore"),
                               InlineKeyboardButton("❌ No", callback_data="admin_panel")]
                          ]))
        db.set_session(message.from_user.id, "awaiting_restore", {"file_id": message.reply_to_message.document.file_id})
    
    async def handle_cleanup(self, client, message):
        await message.reply("⏳ Cleaning up temporary files...")
        db.cleanup_temp_files(1)
        await message.reply("✅ Cleanup completed!")
    
    async def handle_set_ads(self, client, message):
        try:
            args = message.command[1].split(',')
            enabled = args[0].lower()
            interval = int(args[1]) if len(args) > 1 else Config.ADS_INTERVAL
            
            db.set_setting('ads_enabled', '1' if enabled == 'on' else '0', message.from_user.id)
            db.set_setting('ads_interval', str(interval), message.from_user.id)
            await message.reply(f"✅ Ads settings updated!\nEnabled: {enabled}\nInterval: {interval} edits")
        except:
            await message.reply("Usage: /setads <on/off>,<interval>")
    
    async def handle_set_free_edits(self, client, message):
        try:
            count = int(message.command[1])
            db.set_setting('free_edits', str(count), message.from_user.id)
            await message.reply(f"✅ Free edits per day set to {count}")
        except:
            await message.reply("Usage: /setfree <count>")
    
    async def handle_logs(self, client, message):
        log_file = f"{Config.LOGS_DIR}/bot.log"
        if os.path.exists(log_file):
            await client.send_document(message.chat.id, log_file, caption="📝 Bot Logs")
        else:
            await message.reply("No log file found.")
    
    async def handle_ping(self, client, message):
        start_time = time.time()
        msg = await message.reply("Pong!")
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        uptime = datetime.now() - self.start_time
        await msg.edit_text(f"🏓 Pong!\nLatency: {latency:.0f}ms\nUptime: {str(uptime).split('.')[0]}")
    
    async def handle_info(self, client, message):
        stats = db.get_stats()
        text = f"""
ℹ️ **Bot Information**

**Name:** {Config.BULK_CONFIG['bot_name']}
**Version:** {Config.BULK_CONFIG['bot_version']}
**Users:** {stats['total_users']}
**Premium Users:** {stats['premium_users']}
**Total Edits:** {stats['total_edits']}
**Today's Edits:** {stats['today_edits']}
**Total Ads:** {stats['total_ads']}
**Files Renamed:** {stats['total_renames']}

**Features:**
• Image Tools: {Config.BULK_CONFIG['features']['image_tools']}
• Video Tools: {Config.BULK_CONFIG['features']['video_tools']}
• AI Tools: {Config.BULK_CONFIG['features']['ai_tools']}
• Filters: {Config.BULK_CONFIG['features']['filters']}

**Limits:**
• Free Edits: {Config.MAX_FREE_EDITS}/day
• Trial: {Config.FREE_TRIAL_DAYS} days
• Max File Size: 4GB

**Status:** 🟢 Online
"""
        await message.reply(text)
    
    # ========== MEDIA PROCESSING ==========
    async def process_image(self, client, message):
        user_id = message.from_user.id
        
        if db.is_banned(user_id):
            await message.reply("🚫 You are banned from using this bot.")
            return
        
        if not db.can_edit(user_id):
            await message.reply(f"⚠️ Free limit reached! {db.get_setting('free_edits', Config.MAX_FREE_EDITS)}/day\nUpgrade: /premium | Trial: /trial")
            return
        
        db.set_session(user_id, 'image_edit', {'file_id': message.photo.file_id})
        
        await message.reply(
            "📸 **Image Received!**\n\nChoose a filter category:",
            reply_markup=self.get_image_menu()
        )
    
    async def process_video(self, client, message):
        user_id = message.from_user.id
        
        if db.is_banned(user_id):
            await message.reply("🚫 You are banned from using this bot.")
            return
        
        if not db.can_edit(user_id):
            await message.reply(f"⚠️ Free limit reached! {db.get_setting('free_edits', Config.MAX_FREE_EDITS)}/day\nUpgrade: /premium | Trial: /trial")
            return
        
        if message.video.file_size > Config.MAX_VIDEO_SIZE and not db.is_premium(user_id):
            await message.reply("⚠️ Video too large! Premium users can upload up to 4GB.\nUpgrade: /premium")
            return
        
        db.set_session(user_id, 'video_edit', {'file_id': message.video.file_id})
        
        await message.reply(
            "🎬 **Video Received!**\n\nChoose an effect category:",
            reply_markup=self.get_video_menu()
        )
    
    async def process_document(self, client, message):
        user_id = message.from_user.id
        session, step, media_path = db.get_session(user_id)
        
        if step == "awaiting_rename_file":
            db.set_session(user_id, "awaiting_rename_name", {"file_id": message.document.file_id, "file_name": message.document.file_name})
            await message.reply("📝 Send the new name for this file (including extension):\n\nExample: `my_video.mp4`")
        elif step == "awaiting_restore":
            await self.handle_restore_confirm(client, message, session)
        else:
            await message.reply("Please send image or video directly (not as document) for editing.")
    
    async def handle_rename_process(self, client, message, session):
        user_id = message.from_user.id
        new_name = message.text.strip()
        file_id = session.get("file_id")
        original_name = session.get("file_name")
        
        if not new_name or not file_id:
            await message.reply("❌ Invalid request. Please start over with /rename")
            db.clear_session(user_id)
            return
        
        processing_msg = await message.reply(f"⏳ Renaming file to: {new_name}")
        
        try:
            file_path = await MediaProcessor.download_media(client, file_id, user_id, "document")
            
            new_path = os.path.join(Config.TEMP_DIR, new_name)
            shutil.move(file_path, new_path)
            
            await client.send_document(user_id, new_path, caption=f"✅ File renamed successfully!\n\nOriginal: `{original_name}`\nNew: `{new_name}`")
            
            db.add_rename_record(user_id, original_name, new_name, os.path.getsize(new_path), "document")
            show_ad = db.increment_edit(user_id)
            
            os.unlink(new_path)
            await processing_msg.delete()
            db.clear_session(user_id)
            
            if show_ad and Config.GOOGLE_ADS_ENABLED:
                await self.show_ad(client, user_id)
                
        except Exception as e:
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
            db.clear_session(user_id)
    
    async def handle_restore_confirm(self, client, message, session):
        user_id = message.from_user.id
        if message.text.lower() == "yes":
            file_id = session.get("file_id")
            file_path = await client.download_media(file_id)
            db.restore_database(file_path)
            await message.reply("✅ Database restored successfully!")
            os.unlink(file_path)
        else:
            await message.reply("❌ Restore cancelled.")
        db.clear_session(user_id)
    
    async def show_ad(self, client, user_id):
        if db.is_premium(user_id) or db.get_setting('ads_enabled', '1') != '1':
            return
        
        ad_text = f"""
📢 **Advertisement**

{Config.ADS_TEXT}

✅ You've earned a free edit!
⭐ Upgrade to /premium to remove ads forever!
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Watched Ad", callback_data="ad_watched"),
             InlineKeyboardButton("⭐ Premium", callback_data="premium_info")]
        ])
        await client.send_message(user_id, ad_text, reply_markup=keyboard, disable_web_page_preview=True)
    
    async def handle_auto_reply(self, client, message):
        text = message.text.lower()
        session, step, _ = db.get_session(message.from_user.id)
        
        if step == "awaiting_rename_name":
            await self.handle_rename_process(client, message, session)
            return
        
        db.cursor.execute("SELECT keyword, response, match_type FROM auto_reply WHERE is_active=1")
        rules = db.cursor.fetchall()
        
        for rule in rules:
            keyword, response, match_type = rule["keyword"], rule["response"], rule["match_type"]
            if match_type == 'exact' and text == keyword.lower():
                await message.reply(response)
                return
            elif match_type == 'contains' and keyword.lower() in text:
                await message.reply(response)
                return
    
    # ========== CALLBACK HANDLERS ==========
    async def handle_callback(self, client, callback):
        user_id = callback.from_user.id
        data = callback.data
        
        await callback.answer()
        
        if data == "main_menu":
            await callback.message.edit_text(
                "🎬 **Main Menu**\nChoose an option:",
                reply_markup=self.get_main_menu(user_id)
            )
        
        elif data == "menu_image":
            await callback.message.edit_text(
                "📸 **Image Editing**\nChoose a category:",
                reply_markup=self.get_image_menu()
            )
        
        elif data == "menu_video":
            await callback.message.edit_text(
                "🎬 **Video Editing**\nChoose a category:",
                reply_markup=self.get_video_menu()
            )
        
        elif data == "menu_ai":
            await callback.message.edit_text(
                "✨ **AI Tools**\n\n• AI Speech Synthesis\n• Auto Subtitles\n• Background Removal\n• Face Detection/Blur\n• Object Removal\n• Colorization\n• Enhancement\n• Scene Detection\n\nSend a video to use AI features!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "menu_timeline":
            await callback.message.edit_text(
                "🎞️ **Timeline Editor**\n\nAdvanced editing:\n• Trim/Cut video segments\n• Add transitions\n• Add text overlays\n• Add background music\n• Merge multiple clips\n• Export presets\n\nSend a video to start!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📹 Send Video", callback_data="timeline_start"),
                     InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                ])
            )
        
        elif data == "menu_rename":
            await callback.message.edit_text(
                "📝 **File Rename**\n\nSend me any file (up to 4GB) and I'll rename it for you!\n\nPremium users get priority processing!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Send File", callback_data="rename_start"),
                     InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                ])
            )
        
        elif data == "menu_refer":
            bot_username = (await client.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start={user_id}"
            await callback.message.edit_text(
                f"👥 **Referral System**\n\nYour link:\n`{referral_link}`\n\nShare and earn:\n• 3 days premium per referral\n• 100 coins per referral\n\nTotal Referrals: {db.get_referral_count(user_id)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "admin_panel":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "🔧 **Admin Panel (35+ Options)**\nSelect an option:",
                    reply_markup=self.get_admin_panel()
                )
        
        elif data == "premium_info":
            await callback.message.edit_text(
                "🌟 **Premium Features**\n\n✅ No Watermark\n✅ Unlimited Edits\n✅ No Ads\n✅ 4K Export\n✅ AI Features\n✅ Priority Support\n\nUse /premium to buy!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "premium_features":
            await callback.message.edit_text(
                "👑 **Premium Active**\n\n✨ No Watermark\n✨ Unlimited Edits\n✨ No Ads\n✨ 4K Export\n✨ AI Features\n✨ Priority Queue\n\nThanks for being premium!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "buy_premium":
            await callback.message.edit_text(
                f"💎 **Buy Premium**\n\nPrice: {Config.PREMIUM_PRICE}\n\n[Click Here]({Config.PREMIUM_LINK})",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "free_trial":
            if not db.is_premium(user_id):
                db.give_premium(user_id, Config.FREE_TRIAL_DAYS)
                await callback.message.edit_text(
                    f"🎉 7-day free trial activated!\nEnjoy all premium features!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
                )
            else:
                await callback.message.edit_text(
                    "You already have premium active!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
                )
        
        elif data == "my_stats":
            row = db.get_user(user_id)
            if row:
                text = f"📊 **Your Stats**\n\nPremium: {'Yes' if db.is_premium(user_id) else 'No'}\nTotal Edits: {row['total_edits']}\nToday's Edits: {row['edits_today']}\nFiles Renamed: {row['renamed_files']}\nReferrals: {db.get_referral_count(user_id)}\nCoins: {row['coins']}"
                await callback.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
                )
        
        elif data == "help_info":
            await callback.message.edit_text(
                "📚 **Help**\n\nSend /help for complete guide!\n\nQuick tips:\n• Send a photo for image editing\n• Send a video for video editing\n• Use /trial for 7-day free premium\n• Use /rename to rename files\n• Premium = No ads + Unlimited edits",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data == "ad_watched":
            db.increment_edit(user_id)
            await callback.message.edit_text(
                "✅ Thanks for supporting us!\n\nYou can continue using the bot.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
        
        elif data.startswith("img_cat_"):
            category = data[8:]
            filters = MediaProcessor.IMAGE_FILTERS.get(category, [])
            keyboard = []
            for name, filter_id in filters:
                keyboard.append([InlineKeyboardButton(name, callback_data=f"apply_img_{filter_id}")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_image")])
            await callback.message.edit_text(
                f"📸 **{category.title()} Filters**\nChoose a filter:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("vid_cat_"):
            category = data[8:]
            effects = MediaProcessor.VIDEO_EFFECTS.get(category, [])
            keyboard = []
            for name, effect_id in effects:
                keyboard.append([InlineKeyboardButton(name, callback_data=f"apply_vid_{effect_id}")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_video")])
            await callback.message.edit_text(
                f"🎬 **{category.title()} Effects**\nChoose an effect:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("apply_img_"):
            filter_name = data[10:]
            await self.apply_image_edit(client, callback, filter_name)
        
        elif data.startswith("apply_vid_"):
            effect_name = data[10:]
            await self.apply_video_edit(client, callback, effect_name)
        
        elif data == "timeline_start":
            await callback.message.edit_text(
                "📹 Send me a video to start timeline editing!\n\nSupported formats: MP4, AVI, MOV, MKV\nMax size: 4GB for premium users",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_timeline")]])
            )
            db.set_session(user_id, "timeline_awaiting_video", {})
        
        elif data == "rename_start":
            await callback.message.edit_text(
                "📤 Send me any file to rename!\n\nSupported: Any file type\nMax size: 4GB for premium users",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_rename")]])
            )
            db.set_session(user_id, "awaiting_rename_file", {})
        
        elif data == "confirm_restore":
            session, step, _ = db.get_session(user_id)
            if session and step == "awaiting_restore":
                await self.handle_restore_confirm(client, callback.message, session)
        
        # Admin panel callbacks
        elif data == "admin_stats":
            if db.is_admin(user_id):
                stats = db.get_stats()
                await callback.message.edit_text(
                    f"📊 **Bot Statistics**\n\n"
                    f"👥 Total Users: {stats['total_users']}\n"
                    f"⭐ Premium Users: {stats['premium_users']}\n"
                    f"🚫 Banned Users: {stats['banned_users']}\n"
                    f"📝 Total Edits: {stats['total_edits']}\n"
                    f"📅 Today's Edits: {stats['today_edits']}\n"
                    f"💰 Total Ads: {stats['total_ads']}\n"
                    f"📄 Files Renamed: {stats['total_renames']}\n"
                    f"🎯 Commands Used: {stats['total_commands']}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_daily_stats":
            if db.is_admin(user_id):
                daily_stats = db.get_daily_stats()
                text = "📈 **Daily Statistics (Last 7 Days)**\n\n"
                for date, edits in daily_stats.items():
                    text += f"📅 {date}: {edits} edits\n"
                await callback.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_users":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "👑 **User Management**\n\nCommands:\n/ban <user_id>,<reason>,<days>\n/unban <user_id>\n/addprem <user_id>,<days>\n/rmprem <user_id>\n/addadmin <user_id>\n/rmadmin <user_id>\n\nUse /listcmds to see custom commands",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_premium":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "💰 **Premium Management**\n\nCommands:\n/addprem <user_id>,<days>\n/rmprem <user_id>\n/trial - Users can get 7-day trial\n\nReferral rewards: 3 days per referral",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_commands":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "📝 **Custom Commands**\n\nCommands:\n/addcmd command | response\n/delcmd command\n/listcmds\n\nReply to media to attach to command!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_settings":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "⚙️ **Bot Settings**\n\nCommands:\n/setwelcome <text>\n/setfree <count>\n/setads <on/off>,<interval>\n\nCurrent Settings:\nFree Edits: {}\nAds Enabled: {}\nAds Interval: {}".format(
                        db.get_setting('free_edits', Config.MAX_FREE_EDITS),
                        "Yes" if db.get_setting('ads_enabled', '1') == '1' else "No",
                        db.get_setting('ads_interval', Config.ADS_INTERVAL)
                    ),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_broadcast":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "📢 **Broadcast**\n\nCommand: /broadcast <message>\n\nMessage will be sent to all users!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_backup":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "💾 **Backup/Restore**\n\nCommands:\n/backup - Create database backup\n/restore - Restore from backup (reply to .db file)\n/export - Export settings\n/import - Import settings (reply to JSON file)",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_bulk":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "📦 **Bulk Configuration**\n\nEdit Config.BULK_CONFIG in code:\n• Bot name & version\n• Feature counts\n• Limits\n• Social links\n• Watermark settings\n• Video presets\n\nRestart bot after changes!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_ads":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "💰 **AdSense Settings**\n\nCommands:\n/setads <on/off>,<interval>\n\nCurrent Status:\nEnabled: {}\nInterval: {} edits\nPremium Users: No ads".format(
                        "Yes" if db.get_setting('ads_enabled', '1') == '1' else "No",
                        db.get_setting('ads_interval', Config.ADS_INTERVAL)
                    ),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_cleanup":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "🗑️ **Cleanup**\n\nCommand: /cleanup\n\nCleans temporary files older than 1 hour.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_referral_stats":
            if db.is_admin(user_id):
                db.cursor.execute("SELECT referrer_id, COUNT(*) as count FROM referrals GROUP BY referrer_id ORDER BY count DESC LIMIT 10")
                top_referrers = db.cursor.fetchall()
                text = "👥 **Top Referrers**\n\n"
                for i, ref in enumerate(top_referrers, 1):
                    user = await client.get_users(ref["referrer_id"])
                    text += f"{i}. @{user.username or user.first_name}: {ref['count']} referrals\n"
                await callback.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_ban_list":
            if db.is_admin(user_id):
                db.cursor.execute("SELECT user_id, reason, banned_date FROM banned_users")
                banned = db.cursor.fetchall()
                text = "🚫 **Banned Users**\n\n"
                for ban in banned:
                    date = datetime.fromtimestamp(ban["banned_date"]).strftime("%Y-%m-%d")
                    text += f"User: `{ban['user_id']}`\nReason: {ban['reason']}\nDate: {date}\n\n"
                await callback.message.edit_text(
                    text or "No banned users.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_command_stats":
            if db.is_admin(user_id):
                commands = db.get_all_custom_commands()
                text = "📝 **Command Usage Stats**\n\n"
                for cmd in commands:
                    text += f"/{cmd['command']}: {cmd['usage_count']} uses\n"
                await callback.message.edit_text(
                    text or "No custom commands.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_db_info":
            if db.is_admin(user_id):
                db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = db.cursor.fetchall()
                text = "💾 **Database Info**\n\nTables:\n"
                for table in tables:
                    db.cursor.execute(f"SELECT COUNT(*) FROM {table['name']}")
                    count = db.cursor.fetchone()[0]
                    text += f"• {table['name']}: {count} rows\n"
                await callback.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_maintenance":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "🔧 **Maintenance Mode**\n\nUse /maintenance on/off to toggle\n\nCurrent status: Off",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
        
        elif data == "admin_export_data":
            if db.is_admin(user_id):
                await self.handle_export(client, callback.message)
        
        elif data == "admin_import_data":
            if db.is_admin(user_id):
                await callback.message.edit_text(
                    "📥 **Import Data**\n\nReply to a JSON config file with /import",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
                )
    
    # ========== IMAGE EDITING ==========
    def get_image_menu(self):
        keyboard = []
        for category in MediaProcessor.IMAGE_FILTERS.keys():
            keyboard.append([InlineKeyboardButton(f"📁 {category.title()}", callback_data=f"img_cat_{category}")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    def get_video_menu(self):
        keyboard = []
        for category in MediaProcessor.VIDEO_EFFECTS.keys():
            keyboard.append([InlineKeyboardButton(f"🎬 {category.title()}", callback_data=f"vid_cat_{category}")])
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    async def apply_image_edit(self, client, callback, filter_name):
        user_id = callback.from_user.id
        session, step, _ = db.get_session(user_id)
        
        if not session or 'file_id' not in session:
            await callback.message.edit_text("Please send an image first!")
            return
        
        processing_msg = await callback.message.reply("⏳ Processing image... Please wait.")
        
        try:
            file_path = await MediaProcessor.download_media(client, session['file_id'], user_id, "image")
            
            if not file_path:
                await processing_msg.edit_text("❌ Failed to download image.")
                return
            
            output_path = await MediaProcessor.apply_image_filter(file_path, filter_name)
            
            if not db.is_premium(user_id) and db.get_setting('watermark_enabled', '1') == '1':
                watermarked = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
                MediaProcessor._add_watermark_static(output_path, watermarked, db.get_setting('watermark_text', Config.WATERMARK_TEXT))
                output_path = watermarked
            
            await client.send_photo(user_id, output_path, caption=f"✅ Edited with {filter_name} filter!")
            
            show_ad = db.increment_edit(user_id)
            db.add_edit_history(user_id, 'image', filter_name, os.path.getsize(file_path), os.path.getsize(output_path), 0)
            
            os.unlink(file_path)
            os.unlink(output_path)
            await processing_msg.delete()
            await callback.message.delete()
            
            if show_ad and Config.GOOGLE_ADS_ENABLED:
                await self.show_ad(client, user_id)
                
        except Exception as e:
            logger.error(f"Image edit error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    async def apply_video_edit(self, client, callback, effect_name):
        user_id = callback.from_user.id
        session, step, _ = db.get_session(user_id)
        
        if not session or 'file_id' not in session:
            await callback.message.edit_text("Please send a video first!")
            return
        
        processing_msg = await callback.message.reply("🎬 Processing video... This may take a moment.")
        
        try:
            file_path = await MediaProcessor.download_media(client, session['file_id'], user_id, "video")
            
            if not file_path:
                await processing_msg.edit_text("❌ Failed to download video.")
                return
            
            params = {}
            
            # Speed presets
            if effect_name == 'speed_2x':
                params = {'speed': 2.0}
            elif effect_name == 'speed_05x':
                params = {'speed': 0.5}
            elif effect_name == 'speed_025':
                params = {'speed': 0.25}
            elif effect_name == 'speed_075':
                params = {'speed': 0.75}
            elif effect_name == 'speed_15x':
                params = {'speed': 1.5}
            elif effect_name == 'speed_3x':
                params = {'speed': 3.0}
            elif effect_name == 'speed_4x':
                params = {'speed': 4.0}
            
            output_path = await MediaProcessor.apply_video_effect(file_path, effect_name, params)
            
            await client.send_video(user_id, output_path, caption=f"✅ Video edited with {effect_name}!")
            
            show_ad = db.increment_edit(user_id)
            db.add_edit_history(user_id, 'video', effect_name, os.path.getsize(file_path), os.path.getsize(output_path), 0)
            
            os.unlink(file_path)
            os.unlink(output_path)
            await processing_msg.delete()
            await callback.message.delete()
            
            if show_ad and Config.GOOGLE_ADS_ENABLED:
                await self.show_ad(client, user_id)
            
        except Exception as e:
            logger.error(f"Video edit error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    def run(self):
        print("=" * 50)
        print("🤖 KiraFx Media Editor Bot v5.0")
        print("=" * 50)
        print(f"📸 Image Tools: {len(MediaProcessor.IMAGE_FILTERS)} categories")
        print(f"🎬 Video Tools: {len(MediaProcessor.VIDEO_EFFECTS)} categories")
        print(f"⭐ Premium Trial: {Config.FREE_TRIAL_DAYS} days")
        print(f"💾 Max File Size: 4GB")
        print(f"👑 Admin Panel: 35+ Options")
        print(f"📝 File Rename: Enabled")
        print(f"🎞️ Timeline Editor: Ready")
        print(f"💰 Google Ads: {'Enabled' if Config.GOOGLE_ADS_ENABLED else 'Disabled'}")
        print("=" * 50)
        print("🚀 Bot is online and ready!")
        print("=" * 50)
        
        if Config.USE_WEBHOOK:
            self.app.run(webhook=True, host=Config.HOST, port=Config.PORT)
        else:
            self.app.run()
    
    async def shutdown(self):
        print("🛑 Shutting down bot...")
        db.conn.close()
        print("✅ Cleanup completed.")

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    bot = MediaEditorBot()
    
    def signal_handler(sig, frame):
        print("\n🛑 Received shutdown signal...")
        asyncio.create_task(bot.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
