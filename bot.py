#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██╗  ██╗██╗███╗   ██╗██╗   ██╗ █████╗     ███████╗██╗  ██╗
║     ██║ ██╔╝██║████╗  ██║██║   ██║██╔══██╗    ██╔════╝╚██╗██╔╝
║     █████╔╝ ██║██╔██╗ ██║██║   ██║███████║    █████╗   ╚███╔╝ 
║     ██╔═██╗ ██║██║╚██╗██║╚██╗ ██╔╝██╔══██║    ██╔══╝   ██╔██╗ 
║     ██║  ██╗██║██║ ╚████║ ╚████╔╝ ██║  ██║    ██║      ██╔╝ ██╗
║     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝    ╚═╝      ╚═╝  ╚═╝
║                                                               ║
║              KIRA-FX ULTRA BOT - COMPLETE EDITION            ║
║                    Version: 8.0.0 - FINAL                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

FEATURES:
├── 🖼️ IMAGE EDITING (100+ Filters & Effects)
├── 🎬 VIDEO EDITING (Trim, Speed, Compress, Watermark)
├── 🎵 AUDIO EDITING (Extract, Convert, Mix)
├── 🤖 AI ENHANCEMENT (Auto Enhance, Background Remove)
├── 💻 CODE FORMATTER (Python, JS, JSON, HTML, CSS, SQL)
├── ⚡ CUSTOM COMMANDS (/addcmd, /run)
├── 👑 ADMIN PANEL (Ban, Mute, Warn, Broadcast)
├── 💰 CREDITS SYSTEM (Daily Rewards, Referrals)
├── 🎨 COLLAGE MAKER (Merge multiple images)
├── 📊 STATISTICS (User stats, Bot stats)
└── 🔐 SECURITY (CAPTCHA, Rate Limiting, Anti-Spam)
"""

import os
import re
import asyncio
import logging
import shutil
import json
import sqlite3
import csv
import io
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict
import random
import time
import traceback
import threading
import subprocess
from functools import wraps
from io import BytesIO

# ==================== TELEGRAM IMPORTS ====================
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputFile, BotCommand, User, Chat, ChatMember,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    BotCommandScopeChat, BotCommandScopeDefault
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler,
    ApplicationBuilder, PreCheckoutQueryHandler, ShippingQueryHandler,
    PollAnswerHandler, PollHandler, ChatMemberHandler
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError, NetworkError, TimedOut

# ==================== IMAGE PROCESSING ====================
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available. Some filters will be disabled.")

try:
    from scipy.ndimage import convolve, gaussian_filter, median_filter
    from skimage import exposure, filters as skfilters, morphology, color
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ SciPy/Skimage not available. Some filters will be disabled.")

# ==================== VIDEO PROCESSING ====================
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
        TextClip, concatenate_videoclips, concatenate_audioclips, vfx, afx,
        ImageSequenceClip, clips_array, ColorClip, VideoClip
    )
    from moviepy.video.fx import resize, rotate, crop, fadein, fadeout
    from moviepy.audio.fx import audio_loop, audio_fadein, audio_fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available. Video editing will be disabled.")

# ==================== AUDIO PROCESSING ====================
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, low_pass_filter, high_pass_filter
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ Pydub not available. Audio editing will be disabled.")

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ Librosa not available. Advanced audio features disabled.")

# ==================== WEB SERVER ====================
try:
    from flask import Flask, request, jsonify, render_template_string, send_file
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask not available. Web server disabled.")

# ==================== UTILITIES ====================
try:
    import aiohttp
    import aiofiles
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ==================== CONFIGURATION ====================

# Bot Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
    print("Please set your bot token: export TELEGRAM_BOT_TOKEN='your_token_here'")
    exit(1)

ADMIN_IDS = [int(id.strip()) for id in os.environ.get("ADMIN_IDS", "").split(",") if id.strip()]
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
if OWNER_ID and OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(OWNER_ID)

if not ADMIN_IDS:
    print("⚠️ No admin IDs configured! Please set ADMIN_IDS environment variable.")

# Server Configuration
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "False").lower() == "true"

# Database
DATABASE_PATH = os.environ.get("DATABASE_PATH", "kira_fx.db")
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# File Limits (in bytes)
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100MB

# Rate Limiting
RATE_LIMIT_SECONDS = 2
MAX_COMMANDS_PER_MINUTE = 30

# CAPTCHA Settings
CAPTCHA_TIMEOUT = 180  # 3 minutes
MAX_CAPTCHA_ATTEMPTS = 3

# Credits System
DEFAULT_CREDITS = 100
DAILY_REWARD_MIN = 50
DAILY_REWARD_MAX = 200
REFERRAL_BONUS = 50
PREMIUM_COST = 29900  # 299.00 INR (in paise)

# Video Quality Presets (144p to 4K)
VIDEO_QUALITIES = {
    "144p": {"width": 256, "height": 144, "bitrate": "100k", "label": "📱 144p", "fps": 15},
    "240p": {"width": 426, "height": 240, "bitrate": "300k", "label": "📱 240p", "fps": 24},
    "360p": {"width": 640, "height": 360, "bitrate": "500k", "label": "📱 360p", "fps": 24},
    "480p": {"width": 854, "height": 480, "bitrate": "1000k", "label": "📱 480p", "fps": 30},
    "720p": {"width": 1280, "height": 720, "bitrate": "2500k", "label": "💻 720p HD", "fps": 30},
    "1080p": {"width": 1920, "height": 1080, "bitrate": "5000k", "label": "💻 1080p Full HD", "fps": 30},
    "2K": {"width": 2560, "height": 1440, "bitrate": "8000k", "label": "🖥️ 2K QHD", "fps": 30},
    "4K": {"width": 3840, "height": 2160, "bitrate": "16000k", "label": "🖥️ 4K UHD", "fps": 30}
}

# Audio Quality Presets
AUDIO_QUALITIES = {
    "low": {"bitrate": "64k", "sample_rate": 22050, "label": "🔊 Low (64kbps)"},
    "medium": {"bitrate": "128k", "sample_rate": 44100, "label": "🔊 Medium (128kbps)"},
    "high": {"bitrate": "320k", "sample_rate": 48000, "label": "🔊 High (320kbps)"},
    "lossless": {"bitrate": "1411k", "sample_rate": 96000, "label": "🎵 Lossless (FLAC)"}
}

# Image Filters Categories
IMAGE_FILTERS_CATEGORIES = {
    "basic": ["blur", "contour", "detail", "edge_enhance", "emboss", "sharpen", "smooth"],
    "color": ["grayscale", "sepia", "negative", "vintage", "warm", "cool", "pastel", "hdr"],
    "artistic": ["oil_paint", "watercolor", "pencil_sketch", "cartoon", "neon", "glitch", "vhs"],
    "effects": ["glow", "noise", "vignette", "bokeh", "halftone", "pixelate", "mosaic"],
    "edge": ["sobel", "canny", "laplacian", "prewitt", "roberts"],
    "distortion": ["fisheye", "tilt_shift", "bulge", "pinch", "twirl", "wave", "ripple"],
    "special": ["infrared", "thermal", "xray", "dream", "fire", "ice", "magic", "nebula"]
}

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suppress noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("moviepy").setLevel(logging.WARNING)

# ==================== ENUMS ====================

class UserState(Enum):
    """User session states for conversation handling"""
    AWAITING_CAPTCHA = "awaiting_captcha"
    AWAITING_IMAGE = "awaiting_image"
    AWAITING_VIDEO = "awaiting_video"
    AWAITING_AUDIO = "awaiting_audio"
    AWAITING_CROP = "awaiting_crop"
    AWAITING_TRIM = "awaiting_trim"
    AWAITING_SPEED = "awaiting_speed"
    AWAITING_TEXT = "awaiting_text"
    AWAITING_MERGE = "awaiting_merge"
    AWAITING_RESIZE = "awaiting_resize"
    AWAITING_ROTATE = "awaiting_rotate"
    AWAITING_ADJUST = "awaiting_adjust"
    AWAITING_ADMIN = "awaiting_admin"
    AWAITING_FEEDBACK = "awaiting_feedback"
    AWAITING_BROADCAST = "awaiting_broadcast"
    AWAITING_CUSTOM_CMD = "awaiting_custom_cmd"
    AWAITING_CODE = "awaiting_code"
    AWAITING_QUALITY = "awaiting_quality"
    AWAITING_REFERRAL = "awaiting_referral"
    AWAITING_PREMIUM = "awaiting_premium"
    VERIFIED = "verified"

class UserRole(Enum):
    """User role levels"""
    USER = "user"
    PREMIUM = "premium"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"

class MediaType(Enum):
    """Media types supported"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    GIF = "gif"

# ==================== DATA CLASSES ====================

@dataclass
class UserSession:
    """User session data for tracking ongoing operations"""
    user_id: int
    state: UserState = UserState.AWAITING_CAPTCHA
    media_type: MediaType = MediaType.IMAGE
    temp_files: List[str] = field(default_factory=list)
    pending_effect: Optional[str] = None
    pending_params: Dict[str, Any] = field(default_factory=dict)
    captcha_code: Optional[str] = None
    captcha_attempts: int = 0
    captcha_time: Optional[datetime] = None
    last_active: datetime = field(default_factory=datetime.now)
    command_count: int = 0
    command_reset: datetime = field(default_factory=datetime.now)
    batch_files: List[str] = field(default_factory=list)
    code_language: Optional[str] = None
    quality_preset: Optional[str] = None
    merge_files: List[str] = field(default_factory=list)

@dataclass
class UserData:
    """User data structure from database"""
    user_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str = "user"
    is_premium: bool = False
    premium_expires: Optional[datetime] = None
    is_banned: bool = False
    ban_reason: Optional[str] = None
    is_muted: bool = False
    muted_until: Optional[datetime] = None
    warn_count: int = 0
    total_edits: int = 0
    total_images: int = 0
    total_videos: int = 0
    total_audios: int = 0
    credits: int = DEFAULT_CREDITS
    referral_count: int = 0
    referred_by: Optional[int] = None
    join_date: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    language: str = "en"
    theme: str = "dark"

# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    """Manages all database operations with connection pooling and retry logic"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self, timeout: int = 30):
        """Get database connection with timeout and retry"""
        conn = sqlite3.connect(self.db_path, timeout=timeout)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            # Users table
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                is_premium BOOLEAN DEFAULT 0,
                premium_expires TIMESTAMP,
                is_banned BOOLEAN DEFAULT 0,
                ban_reason TEXT,
                banned_at TIMESTAMP,
                is_muted BOOLEAN DEFAULT 0,
                muted_until TIMESTAMP,
                warn_count INTEGER DEFAULT 0,
                total_edits INTEGER DEFAULT 0,
                total_images INTEGER DEFAULT 0,
                total_videos INTEGER DEFAULT 0,
                total_audios INTEGER DEFAULT 0,
                credits INTEGER DEFAULT ?,
                referral_count INTEGER DEFAULT 0,
                referred_by INTEGER,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language TEXT DEFAULT 'en',
                theme TEXT DEFAULT 'dark'
            )''', (DEFAULT_CREDITS,))
            
            # Verification table
            conn.execute('''CREATE TABLE IF NOT EXISTS verification (
                user_id INTEGER PRIMARY KEY,
                is_verified BOOLEAN DEFAULT 0,
                verified_at TIMESTAMP,
                method TEXT
            )''')
            
            # Edit history table
            conn.execute('''CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_type TEXT,
                operation TEXT,
                filter_used TEXT,
                processing_time REAL,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Feedback table
            conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'pending',
                admin_response TEXT,
                responded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Admin logs table
            conn.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_user INTEGER,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Broadcasts table
            conn.execute('''CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                media_type TEXT,
                media_id TEXT,
                recipients INTEGER,
                successful INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Warnings table
            conn.execute('''CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                warned_by INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Referrals table
            conn.execute('''CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                reward_claimed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Daily rewards table
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER PRIMARY KEY,
                last_claim DATE,
                streak INTEGER DEFAULT 0
            )''')
            
            # Auto responses table
            conn.execute('''CREATE TABLE IF NOT EXISTS auto_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE,
                response TEXT,
                media_type TEXT DEFAULT 'text',
                media_id TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Custom commands table
            conn.execute('''CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT UNIQUE,
                response_type TEXT,
                response_content TEXT,
                language TEXT,
                created_by INTEGER,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Scheduled messages table
            conn.execute('''CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                media_type TEXT,
                media_id TEXT,
                schedule_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Payments table
            conn.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                payment_id TEXT UNIQUE,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_edit_history_user ON edit_history(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_broadcasts_created ON broadcasts(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_custom_commands_active ON custom_commands(is_active)')
            
            logger.info("Database initialized successfully")
    
    # ==================== USER MANAGEMENT ====================
    
    def register_user(self, user_id: int, username: str = None, first_name: str = None, 
                      last_name: str = None, referred_by: int = None) -> bool:
        """Register a new user or update existing user info"""
        try:
            with self.get_connection() as conn:
                existing = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
                
                if not existing:
                    conn.execute('''INSERT INTO users 
                        (user_id, username, first_name, last_name, referred_by, last_active)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                        (user_id, username, first_name, last_name, referred_by))
                    
                    # Handle referral bonus
                    if referred_by:
                        conn.execute('''UPDATE users 
                            SET referral_count = referral_count + 1,
                                credits = credits + ?
                            WHERE user_id = ?''', (REFERRAL_BONUS, referred_by))
                        conn.execute('''INSERT INTO referrals (referrer_id, referred_id, reward_claimed)
                            VALUES (?, ?, 1)''', (referred_by, user_id))
                        logger.info(f"Referral bonus given: {referred_by} referred {user_id}")
                    
                    logger.info(f"New user registered: {user_id} ({username})")
                    return True
                else:
                    conn.execute('''UPDATE users 
                        SET username = ?, first_name = ?, last_name = ?, last_active = CURRENT_TIMESTAMP
                        WHERE user_id = ?''', (username, first_name, last_name, user_id))
                    return True
        except Exception as e:
            logger.error(f"Register user error: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data by user_id"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(result) if result else None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields dynamically"""
        if not kwargs:
            return False
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        with self.get_connection() as conn:
            conn.execute(f"UPDATE users SET {fields} WHERE user_id = ?", values)
            return True
    
    def get_user_role(self, user_id: int) -> str:
        """Get user role"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result["role"] if result else "user"
    
    def set_user_role(self, user_id: int, role: str) -> bool:
        """Set user role"""
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            logger.info(f"User {user_id} role changed to {role}")
            return True
    
    # ==================== VERIFICATION ====================
    
    def is_verified(self, user_id: int) -> bool:
        """Check if user is verified"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_verified FROM verification WHERE user_id = ?", (user_id,)).fetchone()
            return result["is_verified"] == 1 if result else False
    
    def verify_user(self, user_id: int, method: str = "captcha") -> bool:
        """Mark user as verified"""
        with self.get_connection() as conn:
            conn.execute('''INSERT OR REPLACE INTO verification (user_id, is_verified, verified_at, method)
                VALUES (?, 1, CURRENT_TIMESTAMP, ?)''', (user_id, method))
            logger.info(f"User {user_id} verified via {method}")
            return True
    
    # ==================== BAN/MUTE SYSTEM ====================
    
    def is_banned(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if user is banned and return ban reason"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_banned, ban_reason FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if result and result["is_banned"]:
                return True, result["ban_reason"]
            return False, None
    
    def ban_user(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """Ban a user"""
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_banned = 1, ban_reason = ?, banned_at = CURRENT_TIMESTAMP
                WHERE user_id = ?''', (reason, user_id))
            self.log_admin_action(admin_id, "ban_user", user_id, reason)
            logger.info(f"User {user_id} banned by {admin_id}: {reason}")
            return True
    
    def unban_user(self, user_id: int, admin_id: int) -> bool:
        """Unban a user"""
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_banned = 0, ban_reason = NULL, banned_at = NULL
                WHERE user_id = ?''', (user_id,))
            self.log_admin_action(admin_id, "unban_user", user_id)
            logger.info(f"User {user_id} unbanned by {admin_id}")
            return True
    
    def is_muted(self, user_id: int) -> Tuple[bool, Optional[datetime]]:
        """Check if user is muted and return mute expiry"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_muted, muted_until FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if result and result["is_muted"]:
                if result["muted_until"]:
                    try:
                        muted_until = datetime.fromisoformat(result["muted_until"])
                        if muted_until > datetime.now():
                            return True, muted_until
                    except:
                        pass
                # Auto-unmute if expired
                conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
            return False, None
    
    def mute_user(self, user_id: int, admin_id: int, duration_minutes: int, reason: str = None) -> bool:
        """Mute a user for specified duration"""
        muted_until = datetime.now() + timedelta(minutes=duration_minutes)
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_muted = 1, muted_until = ?
                WHERE user_id = ?''', (muted_until.isoformat(), user_id))
            self.log_admin_action(admin_id, "mute_user", user_id, f"{duration_minutes} min: {reason}")
            logger.info(f"User {user_id} muted for {duration_minutes} minutes by {admin_id}")
            return True
    
    def unmute_user(self, user_id: int, admin_id: int) -> bool:
        """Unmute a user"""
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
            self.log_admin_action(admin_id, "unmute_user", user_id)
            logger.info(f"User {user_id} unmuted by {admin_id}")
            return True
    
    # ==================== WARNING SYSTEM ====================
    
    def add_warning(self, user_id: int, admin_id: int, reason: str) -> int:
        """Add a warning to user and return new warning count"""
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO warnings (user_id, warned_by, reason)
                VALUES (?, ?, ?)''', (user_id, admin_id, reason))
            conn.execute('UPDATE users SET warn_count = warn_count + 1 WHERE user_id = ?', (user_id,))
            result = conn.execute("SELECT warn_count FROM users WHERE user_id = ?", (user_id,)).fetchone()
            self.log_admin_action(admin_id, "warn_user", user_id, reason)
            logger.info(f"Warning added to {user_id} by {admin_id}. Total: {result['warn_count']}")
            return result["warn_count"] if result else 0
    
    def clear_warnings(self, user_id: int, admin_id: int) -> bool:
        """Clear all warnings for user"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))
            conn.execute("UPDATE users SET warn_count = 0 WHERE user_id = ?", (user_id,))
            self.log_admin_action(admin_id, "clear_warnings", user_id)
            logger.info(f"Warnings cleared for {user_id} by {admin_id}")
            return True
    
    def get_warnings(self, user_id: int) -> List[Dict]:
        """Get all warnings for user"""
        with self.get_connection() as conn:
            warnings = conn.execute('''SELECT w.*, u.username as admin_name 
                FROM warnings w
                LEFT JOIN users u ON w.warned_by = u.user_id
                WHERE w.user_id = ? ORDER BY w.created_at DESC''', (user_id,)).fetchall()
            return [dict(w) for w in warnings]
    
    # ==================== CREDITS SYSTEM ====================
    
    def get_credits(self, user_id: int) -> int:
        """Get user's current credits"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result["credits"] if result else DEFAULT_CREDITS
    
    def add_credits(self, user_id: int, amount: int, admin_id: int = None) -> bool:
        """Add credits to user"""
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (amount, user_id))
            if admin_id:
                self.log_admin_action(admin_id, "add_credits", user_id, f"+{amount}")
            logger.info(f"Added {amount} credits to user {user_id}")
            return True
    
    def deduct_credits(self, user_id: int, amount: int) -> bool:
        """Deduct credits from user if sufficient balance"""
        with self.get_connection() as conn:
            result = conn.execute('''UPDATE users 
                SET credits = credits - ? 
                WHERE user_id = ? AND credits >= ?''', (amount, user_id, amount))
            if result.rowcount > 0:
                logger.info(f"Deducted {amount} credits from user {user_id}")
                return True
            return False
    
    # ==================== PREMIUM SYSTEM ====================
    
    def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium subscription"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_premium, premium_expires FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if result and result["is_premium"]:
                if result["premium_expires"]:
                    try:
                        expires = datetime.fromisoformat(result["premium_expires"])
                        if expires > datetime.now():
                            return True
                    except:
                        pass
                    # Auto-expire if passed
                    conn.execute("UPDATE users SET is_premium = 0, premium_expires = NULL WHERE user_id = ?", (user_id,))
            return False
    
    def give_premium(self, user_id: int, days: int, admin_id: int = None) -> bool:
        """Grant premium subscription to user"""
        with self.get_connection() as conn:
            expires = (datetime.now() + timedelta(days=days)).isoformat()
            conn.execute('''UPDATE users 
                SET is_premium = 1, premium_expires = ?
                WHERE user_id = ?''', (expires, user_id))
            if admin_id:
                self.log_admin_action(admin_id, "give_premium", user_id, f"{days} days")
            logger.info(f"Premium granted to {user_id} for {days} days")
            return True
    
    def remove_premium(self, user_id: int, admin_id: int = None) -> bool:
        """Remove premium subscription from user"""
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_premium = 0, premium_expires = NULL
                WHERE user_id = ?''', (user_id,))
            if admin_id:
                self.log_admin_action(admin_id, "remove_premium", user_id)
            logger.info(f"Premium removed from {user_id}")
            return True
    
    # ==================== DAILY REWARD ====================
    
    def claim_daily_reward(self, user_id: int) -> Tuple[int, int]:
        """Claim daily reward and return (reward_amount, streak)"""
        today = datetime.now().date().isoformat()
        with self.get_connection() as conn:
            result = conn.execute("SELECT last_claim, streak FROM daily_rewards WHERE user_id = ?", (user_id,)).fetchone()
            
            if result and result["last_claim"] == today:
                return 0, result["streak"]
            
            if result and result["last_claim"] == (datetime.now().date() - timedelta(days=1)).isoformat():
                streak = result["streak"] + 1
            else:
                streak = 1
            
            reward = min(DAILY_REWARD_MIN + (streak - 1) * 10, DAILY_REWARD_MAX)
            conn.execute('''INSERT OR REPLACE INTO daily_rewards (user_id, last_claim, streak)
                VALUES (?, ?, ?)''', (user_id, today, streak))
            conn.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (reward, user_id))
            
            logger.info(f"Daily reward claimed by {user_id}: {reward} credits (streak: {streak})")
            return reward, streak
    
    # ==================== EDIT HISTORY ====================
    
    def add_edit_record(self, user_id: int, media_type: str, operation: str, 
                        filter_used: str = None, processing_time: float = 0,
                        file_size: int = 0) -> bool:
        """Record an edit operation in history"""
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO edit_history 
                (user_id, media_type, operation, filter_used, processing_time, file_size)
                VALUES (?, ?, ?, ?, ?, ?)''', 
                (user_id, media_type, operation, filter_used, processing_time, file_size))
            
            # Update user totals
            if media_type == "image":
                conn.execute('UPDATE users SET total_images = total_images + 1 WHERE user_id = ?', (user_id,))
            elif media_type == "video":
                conn.execute('UPDATE users SET total_videos = total_videos + 1 WHERE user_id = ?', (user_id,))
            elif media_type == "audio":
                conn.execute('UPDATE users SET total_audios = total_audios + 1 WHERE user_id = ?', (user_id,))
            
            conn.execute('''UPDATE users 
                SET total_edits = total_edits + 1, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?''', (user_id,))
            return True
    
    # ==================== FEEDBACK ====================
    
    def save_feedback(self, user_id: int, feedback: str, rating: int = None) -> bool:
        """Save user feedback"""
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO feedback (user_id, feedback, rating)
                VALUES (?, ?, ?)''', (user_id, feedback, rating))
            logger.info(f"Feedback received from {user_id}")
            return True
    
    def get_feedback(self, status: str = "pending") -> List[Dict]:
        """Get feedback by status"""
        with self.get_connection() as conn:
            feedback = conn.execute('''SELECT f.*, u.username, u.first_name 
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.user_id
                WHERE f.status = ?
                ORDER BY f.created_at DESC''', (status,)).fetchall()
            return [dict(f) for f in feedback]
    
    def respond_feedback(self, feedback_id: int, response: str, admin_id: int) -> bool:
        """Respond to feedback"""
        with self.get_connection() as conn:
            conn.execute('''UPDATE feedback 
                SET status = 'responded', admin_response = ?, responded_at = CURRENT_TIMESTAMP
                WHERE id = ?''', (response, feedback_id))
            self.log_admin_action(admin_id, "respond_feedback", None, f"Feedback #{feedback_id}")
            return True
    
    # ==================== AUTO RESPONSES ====================
    
    def add_auto_response(self, keyword: str, response: str, admin_id: int, 
                          media_type: str = "text", media_id: str = None) -> bool:
        """Add or update auto response"""
        with self.get_connection() as conn:
            conn.execute('''INSERT OR REPLACE INTO auto_responses 
                (keyword, response, media_type, media_id, created_by)
                VALUES (?, ?, ?, ?, ?)''', 
                (keyword.lower(), response, media_type, media_id, admin_id))
            self.log_admin_action(admin_id, "add_auto_response", None, keyword)
            logger.info(f"Auto response added: {keyword}")
            return True
    
    def remove_auto_response(self, keyword: str, admin_id: int) -> bool:
        """Remove auto response"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM auto_responses WHERE keyword = ?", (keyword.lower(),))
            self.log_admin_action(admin_id, "remove_auto_response", None, keyword)
            logger.info(f"Auto response removed: {keyword}")
            return True
    
    def get_auto_response(self, text: str) -> Optional[Dict]:
        """Get auto response for matching text"""
        with self.get_connection() as conn:
            for row in conn.execute("SELECT * FROM auto_responses").fetchall():
                if row["keyword"].lower() in text.lower():
                    return dict(row)
            return None
    
    def list_auto_responses(self) -> List[Dict]:
        """List all auto responses"""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM auto_responses ORDER BY keyword").fetchall()]
    
    # ==================== CUSTOM COMMANDS ====================
    
    def add_custom_command(self, command: str, response_type: str, response_content: str, 
                           language: str, created_by: int) -> Tuple[bool, str]:
        """Add a custom command"""
        try:
            with self.get_connection() as conn:
                existing = conn.execute("SELECT command FROM custom_commands WHERE command = ?", 
                                       (command.lower(),)).fetchone()
                if existing:
                    return False, f"❌ Command '/{command}' already exists!"
                
                conn.execute('''INSERT INTO custom_commands 
                    (command, response_type, response_content, language, created_by)
                    VALUES (?, ?, ?, ?, ?)''', 
                    (command.lower(), response_type, response_content, language, created_by))
                self.log_admin_action(created_by, "add_custom_command", None, command)
                logger.info(f"Custom command added: /{command}")
                return True, f"✅ Custom command '/{command}' added successfully!"
        except Exception as e:
            logger.error(f"Error adding custom command: {e}")
            return False, f"❌ Error: {str(e)}"
    
    def get_custom_command(self, command: str) -> Optional[Dict]:
        """Get custom command by name"""
        with self.get_connection() as conn:
            result = conn.execute('''SELECT * FROM custom_commands 
                WHERE command = ? AND is_active = 1''', (command.lower(),)).fetchone()
            if result:
                conn.execute('UPDATE custom_commands SET usage_count = usage_count + 1 WHERE command = ?', 
                           (command.lower(),))
            return dict(result) if result else None
    
    def list_custom_commands(self, active_only: bool = True) -> List[Dict]:
        """List all custom commands"""
        with self.get_connection() as conn:
            if active_only:
                commands = conn.execute('''SELECT * FROM custom_commands 
                    WHERE is_active = 1 ORDER BY usage_count DESC, created_at DESC''').fetchall()
            else:
                commands = conn.execute('''SELECT * FROM custom_commands 
                    ORDER BY created_at DESC''').fetchall()
            return [dict(c) for c in commands]
    
    def delete_custom_command(self, command: str, admin_id: int) -> Tuple[bool, str]:
        """Delete custom command"""
        with self.get_connection() as conn:
            result = conn.execute('DELETE FROM custom_commands WHERE command = ?', (command.lower(),))
            if result.rowcount > 0:
                self.log_admin_action(admin_id, "delete_custom_command", None, command)
                logger.info(f"Custom command deleted: /{command}")
                return True, f"✅ Command '/{command}' deleted!"
            return False, f"❌ Command '/{command}' not found!"
    
    def toggle_custom_command(self, command: str, is_active: bool, admin_id: int) -> Tuple[bool, str]:
        """Toggle custom command active status"""
        with self.get_connection() as conn:
            result = conn.execute('UPDATE custom_commands SET is_active = ? WHERE command = ?', 
                                 (1 if is_active else 0, command.lower()))
            if result.rowcount > 0:
                status = "activated" if is_active else "deactivated"
                self.log_admin_action(admin_id, f"{status}_custom_command", None, command)
                logger.info(f"Custom command {status}: /{command}")
                return True, f"✅ Command '/{command}' {status}!"
            return False, f"❌ Command '/{command}' not found!"
    
    # ==================== BROADCAST ====================
    
    def add_broadcast_record(self, admin_id: int, message: str, recipients: int, 
                             successful: int, failed: int, media_type: str = "text", 
                             media_id: str = None) -> bool:
        """Record broadcast in history"""
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO broadcasts 
                (admin_id, message, media_type, media_id, recipients, successful, failed)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                (admin_id, message, media_type, media_id, recipients, successful, failed))
            return True
    
    def get_broadcast_history(self, limit: int = 50) -> List[Dict]:
        """Get broadcast history"""
        with self.get_connection() as conn:
            broadcasts = conn.execute('''SELECT b.*, u.username as admin_name
                FROM broadcasts b
                LEFT JOIN users u ON b.admin_id = u.user_id
                ORDER BY b.created_at DESC LIMIT ?''', (limit,)).fetchall()
            return [dict(b) for b in broadcasts]
    
    # ==================== STATISTICS ====================
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        with self.get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(user) if user else {}
    
    def get_bot_stats(self) -> Dict:
        """Get bot global statistics"""
        with self.get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_today = conn.execute("SELECT COUNT(*) FROM users WHERE date(last_active) = date('now')").fetchone()[0]
            total_edits = conn.execute("SELECT SUM(total_edits) FROM users").fetchone()[0] or 0
            premium_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1").fetchone()[0]
            banned_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]
            total_images = conn.execute("SELECT SUM(total_images) FROM users").fetchone()[0] or 0
            total_videos = conn.execute("SELECT SUM(total_videos) FROM users").fetchone()[0] or 0
            total_audios = conn.execute("SELECT SUM(total_audios) FROM users").fetchone()[0] or 0
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "total_edits": total_edits,
                "total_images": total_images,
                "total_videos": total_videos,
                "total_audios": total_audios,
                "premium_users": premium_users,
                "banned_users": banned_users
            }
    
    def get_all_users(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        with self.get_connection() as conn:
            query = '''SELECT user_id, username, first_name, last_name, role,
                total_edits, total_images, total_videos, credits, is_premium, is_banned,
                join_date, last_active, referral_count
                FROM users ORDER BY join_date DESC'''
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            users = conn.execute(query).fetchall()
            return [dict(user) for user in users]
    
    def export_users_csv(self) -> str:
        """Export all users to CSV string"""
        users = self.get_all_users(limit=10000)
        output = io.StringIO()
        if users:
            writer = csv.DictWriter(output, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
        return output.getvalue()
    
    # ==================== ADMIN LOGS ====================
    
    def log_admin_action(self, admin_id: int, action: str, target_user: int = None, 
                         details: str = None, ip: str = None) -> bool:
        """Log admin action with retry logic for database locks"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    conn.execute('''INSERT INTO admin_logs (admin_id, action, target_user, details, ip_address)
                        VALUES (?, ?, ?, ?, ?)''', 
                        (admin_id, action, target_user, details, ip))
                return True
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                logger.error(f"Failed to log admin action: {e}")
                return False
    
    def get_admin_logs(self, limit: int = 100) -> List[Dict]:
        """Get admin action logs"""
        with self.get_connection() as conn:
            logs = conn.execute('''SELECT al.*, u.username as admin_name
                FROM admin_logs al
                LEFT JOIN users u ON al.admin_id = u.user_id
                ORDER BY al.created_at DESC LIMIT ?''', (limit,)).fetchall()
            return [dict(log) for log in logs]
    
    # ==================== SCHEDULED MESSAGES ====================
    
    def add_scheduled_message(self, message: str, schedule_time: datetime, 
                              admin_id: int, media_type: str = "text", 
                              media_id: str = None) -> bool:
        """Schedule a message for future sending"""
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO scheduled_messages 
                (message, media_type, media_id, schedule_time, created_by)
                VALUES (?, ?, ?, ?, ?)''', 
                (message, media_type, media_id, schedule_time.isoformat(), admin_id))
            self.log_admin_action(admin_id, "schedule_message", None, message[:50])
            logger.info(f"Message scheduled by {admin_id} for {schedule_time}")
            return True
    
    def get_pending_scheduled_messages(self) -> List[Dict]:
        """Get pending scheduled messages that are due"""
        with self.get_connection() as conn:
            messages = conn.execute('''SELECT * FROM scheduled_messages 
                WHERE status = 'pending' AND schedule_time <= datetime('now')
                ORDER BY schedule_time ASC''').fetchall()
            return [dict(m) for m in messages]
    
    def mark_scheduled_sent(self, message_id: int) -> bool:
        """Mark scheduled message as sent"""
        with self.get_connection() as conn:
            conn.execute("UPDATE scheduled_messages SET status = 'sent' WHERE id = ?", (message_id,))
            return True
# ==================== IMAGE PROCESSOR ====================

class ImageProcessor:
    """Professional image processing with 100+ editing options"""
    
    @staticmethod
    def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
        """Apply any filter from 100+ options"""
        
        # Basic Filters
        basic_filters = {
            "blur": lambda img: img.filter(ImageFilter.BLUR),
            "contour": lambda img: img.filter(ImageFilter.CONTOUR),
            "detail": lambda img: img.filter(ImageFilter.DETAIL),
            "edge_enhance": lambda img: img.filter(ImageFilter.EDGE_ENHANCE),
            "edge_enhance_more": lambda img: img.filter(ImageFilter.EDGE_ENHANCE_MORE),
            "emboss": lambda img: img.filter(ImageFilter.EMBOSS),
            "find_edges": lambda img: img.filter(ImageFilter.FIND_EDGES),
            "sharpen": lambda img: img.filter(ImageFilter.SHARPEN),
            "smooth": lambda img: img.filter(ImageFilter.SMOOTH),
            "smooth_more": lambda img: img.filter(ImageFilter.SMOOTH_MORE),
            "unsharp_mask": lambda img: img.filter(ImageFilter.UnsharpMask),
            "box_blur": lambda img: img.filter(ImageFilter.BoxBlur(5)),
            "gaussian_blur": lambda img: img.filter(ImageFilter.GaussianBlur(5)),
            "mode_filter": lambda img: img.filter(ImageFilter.ModeFilter(5)),
            "rank_filter": lambda img: img.filter(ImageFilter.RankFilter(5, 5)),
            "max_filter": lambda img: img.filter(ImageFilter.MaxFilter(5)),
            "min_filter": lambda img: img.filter(ImageFilter.MinFilter(5)),
            "median_filter": lambda img: img.filter(ImageFilter.MedianFilter(5)),
        }
        
        # Color Filters
        color_filters = {
            "grayscale": lambda img: ImageOps.grayscale(img),
            "invert": lambda img: ImageOps.invert(img.convert('RGB')),
            "equalize": lambda img: ImageOps.equalize(img),
            "autocontrast": lambda img: ImageOps.autocontrast(img),
            "posterize": lambda img: ImageOps.posterize(img, 4),
            "solarize": lambda img: ImageOps.solarize(img, 128),
            "colorize": lambda img: ImageOps.colorize(ImageOps.grayscale(img), (255, 100, 100), (100, 100, 255)),
            "decolor": lambda img: ImageOps.decolor(img),
            "mirror": lambda img: ImageOps.mirror(img),
            "flip": lambda img: ImageOps.flip(img),
        }
        
        # Artistic Filters
        artistic_filters = {
            "sepia": ImageProcessor._sepia,
            "vintage": ImageProcessor._vintage,
            "warm": ImageProcessor._warm,
            "cool": ImageProcessor._cool,
            "dramatic": ImageProcessor._dramatic,
            "cinematic": ImageProcessor._cinematic,
            "teal_orange": ImageProcessor._teal_orange,
            "sunset": ImageProcessor._sunset,
            "golden_hour": ImageProcessor._golden_hour,
            "moody": ImageProcessor._moody,
            "pastel": ImageProcessor._pastel,
            "neon": ImageProcessor._neon if CV2_AVAILABLE else lambda img: img,
            "hdr": ImageProcessor._hdr,
            "matte": ImageProcessor._matte,
            "fade": ImageProcessor._fade,
            "polaroid": ImageProcessor._polaroid,
            "lomo": ImageProcessor._lomo,
            "cross_process": ImageProcessor._cross_process,
            "desert": ImageProcessor._desert,
            "forest": ImageProcessor._forest,
            "ocean": ImageProcessor._ocean,
        }
        
        # Effect Filters
        effect_filters = {
            "glow": ImageProcessor._glow,
            "noise": lambda img: ImageProcessor._add_noise(img, 25),
            "vignette": ImageProcessor._vignette,
            "bokeh": ImageProcessor._bokeh,
            "halftone": ImageProcessor._halftone,
            "pixelate": lambda img: ImageProcessor._pixelate(img, 10),
            "mosaic": lambda img: ImageProcessor._mosaic(img, 20),
            "oil_paint": lambda img: ImageProcessor._oil_paint(img, 5) if CV2_AVAILABLE else img,
            "watercolor": ImageProcessor._watercolor,
            "pencil_sketch": ImageProcessor._pencil_sketch,
            "cartoon": ImageProcessor._cartoon if CV2_AVAILABLE else lambda img: img,
            "glitch": ImageProcessor._glitch,
            "vhs": ImageProcessor._vhs,
            "chromatic_aberration": ImageProcessor._chromatic_aberration,
            "scanlines": ImageProcessor._scanlines,
            "retro": ImageProcessor._retro,
            "dreamy": ImageProcessor._dreamy,
            "grain": lambda img: ImageProcessor._add_grain(img, 15),
        }
        
        # Edge Detection
        edge_filters = {
            "sobel": ImageProcessor._sobel_edge,
            "canny": ImageProcessor._canny_edge if CV2_AVAILABLE else lambda img: img,
            "laplacian": ImageProcessor._laplacian,
            "prewitt": ImageProcessor._prewitt_edge,
            "roberts": ImageProcessor._roberts_edge,
        }
        
        # Distortion Filters
        distortion_filters = {
            "fisheye": ImageProcessor._fisheye,
            "tilt_shift": ImageProcessor._tilt_shift,
            "bulge": ImageProcessor._bulge,
            "pinch": ImageProcessor._pinch,
            "twirl": ImageProcessor._twirl,
            "wave": ImageProcessor._wave,
            "ripple": ImageProcessor._ripple,
        }
        
        # Special Filters
        special_filters = {
            "infrared": ImageProcessor._infrared,
            "thermal": ImageProcessor._thermal if CV2_AVAILABLE else lambda img: img,
            "xray": ImageProcessor._xray,
            "dream": ImageProcessor._dream,
            "fire": ImageProcessor._fire,
            "ice": ImageProcessor._ice,
            "magic": ImageProcessor._magic,
            "nebula": ImageProcessor._nebula,
            "aurora": ImageProcessor._aurora,
            "sunrise": ImageProcessor._sunrise,
            "twilight": ImageProcessor._twilight,
        }
        
        # Combine all filters
        all_filters = {**basic_filters, **color_filters, **artistic_filters, 
                       **effect_filters, **edge_filters, **distortion_filters, 
                       **special_filters}
        
        func = all_filters.get(filter_name, lambda img: img)
        return func(image)
    
    # ==================== COLOR FILTERS ====================
    
    @staticmethod
    def _sepia(image: Image.Image) -> Image.Image:
        """Apply sepia tone"""
        image = image.convert('RGB')
        width, height = image.size
        pixels = image.load()
        for py in range(height):
            for px in range(width):
                r, g, b = pixels[px, py]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return image
    
    @staticmethod
    def _vintage(image: Image.Image) -> Image.Image:
        """Apply vintage filter"""
        image = ImageProcessor._sepia(image)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.95)
        return image
    
    @staticmethod
    def _warm(image: Image.Image) -> Image.Image:
        """Apply warm tone"""
        r, g, b = image.split()
        r = r.point(lambda i: min(255, int(i * 1.2)))
        b = b.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _cool(image: Image.Image) -> Image.Image:
        """Apply cool tone"""
        r, g, b = image.split()
        b = b.point(lambda i: min(255, int(i * 1.2)))
        r = r.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _dramatic(image: Image.Image) -> Image.Image:
        """Apply dramatic effect"""
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2)
        return image
    
    @staticmethod
    def _cinematic(image: Image.Image) -> Image.Image:
        """Apply cinematic color grading"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = (img_array - 127.5) * 1.2 + 127.5
        img_array = np.clip(img_array, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _teal_orange(image: Image.Image) -> Image.Image:
        """Apply teal and orange effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = img_array[:, :, 0] * 0.8 + 50  # Red
        img_array[:, :, 2] = img_array[:, :, 2] * 0.9 + 30  # Blue
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _sunset(image: Image.Image) -> Image.Image:
        """Apply sunset effect"""
        r, g, b = image.split()
        r = r.point(lambda i: min(255, int(i * 1.3)))
        g = g.point(lambda i: int(i * 0.9))
        b = b.point(lambda i: int(i * 0.7))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _golden_hour(image: Image.Image) -> Image.Image:
        """Apply golden hour effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.4, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.2, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.7, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _moody(image: Image.Image) -> Image.Image:
        """Apply moody dark effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = img_array * 0.8
        img_array[:, :, 1] = img_array[:, :, 1] * 0.7  # Green
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _pastel(image: Image.Image) -> Image.Image:
        """Apply pastel effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = img_array * 0.7 + 76
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _neon(image: Image.Image) -> Image.Image:
        """Apply neon effect"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.8, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.5, 0, 255)
        neon = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return Image.fromarray(neon)
    
    @staticmethod
    def _hdr(image: Image.Image) -> Image.Image:
        """Apply HDR effect"""
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.15)
        return image
    
    @staticmethod
    def _matte(image: Image.Image) -> Image.Image:
        """Apply matte finish"""
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.85)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(0.95)
        return image
    
    @staticmethod
    def _fade(image: Image.Image) -> Image.Image:
        """Apply fade effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = img_array * 0.85 + 38
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _polaroid(image: Image.Image) -> Image.Image:
        """Apply polaroid effect"""
        border_size = 30
        result = Image.new('RGB', (image.width + border_size * 2, image.height + border_size * 2), (255, 255, 255))
        result.paste(image, (border_size, border_size))
        # Add slight vignette
        result = ImageProcessor._vignette(result)
        return result
    
    @staticmethod
    def _lomo(image: Image.Image) -> Image.Image:
        """Apply lomo effect"""
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        image = ImageProcessor._vignette(image)
        return image
    
    @staticmethod
    def _cross_process(image: Image.Image) -> Image.Image:
        """Apply cross processing effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.1, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.9, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.2, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _desert(image: Image.Image) -> Image.Image:
        """Apply desert warm tone"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.3, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.1, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.8, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _forest(image: Image.Image) -> Image.Image:
        """Apply forest green tone"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.8, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.2, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.7, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _ocean(image: Image.Image) -> Image.Image:
        """Apply ocean blue tone"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.7, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.9, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.3, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    # ==================== EFFECT FILTERS ====================
    
    @staticmethod
    def _glow(image: Image.Image) -> Image.Image:
        """Apply glow effect"""
        blur = image.filter(ImageFilter.GaussianBlur(10))
        return Image.blend(image, blur, 0.3)
    
    @staticmethod
    def _add_noise(image: Image.Image, intensity: int = 25) -> Image.Image:
        """Add noise to image"""
        img_array = np.array(image.convert('RGB'))
        noise = np.random.normal(0, intensity, img_array.shape)
        noisy = img_array + noise
        return Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _add_grain(image: Image.Image, intensity: int = 15) -> Image.Image:
        """Add film grain"""
        img_array = np.array(image.convert('RGB'))
        grain = np.random.randint(-intensity, intensity, img_array.shape)
        grainy = img_array + grain
        return Image.fromarray(np.clip(grainy, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _vignette(image: Image.Image) -> Image.Image:
        """Apply vignette effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        height, width = img_array.shape[:2]
        
        X, Y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        vignette = 1 - (dist / max_dist) * 0.5
        
        for c in range(3):
            img_array[:, :, c] *= vignette
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _bokeh(image: Image.Image) -> Image.Image:
        """Apply bokeh effect"""
        for _ in range(3):
            image = image.filter(ImageFilter.GaussianBlur(2))
        return image
    
    @staticmethod
    def _halftone(image: Image.Image) -> Image.Image:
        """Apply halftone effect"""
        gray = ImageOps.grayscale(image)
        return gray.convert('1', dither=Image.FLOYDSTEINBERG)
    
    @staticmethod
    def _pixelate(image: Image.Image, pixel_size: int = 10) -> Image.Image:
        """Apply pixelation effect"""
        small = image.resize((image.width // pixel_size, image.height // pixel_size), Image.NEAREST)
        return small.resize(image.size, Image.NEAREST)
    
    @staticmethod
    def _mosaic(image: Image.Image, block_size: int = 20) -> Image.Image:
        """Apply mosaic effect"""
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                block = img_array[y:y+block_size, x:x+block_size]
                if block.size > 0:
                    avg_color = block.mean(axis=(0, 1))
                    img_array[y:y+block_size, x:x+block_size] = avg_color
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _oil_paint(image: Image.Image, radius: int = 5) -> Image.Image:
        """Apply oil painting effect"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        result = np.zeros_like(img_array)
        
        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                window = img_array[y - radius:y + radius + 1, x - radius:x + radius + 1]
                pixels = window.reshape(-1, 3)
                avg_color = np.mean(pixels, axis=0)
                result[y, x] = avg_color
        
        return Image.fromarray(result.astype(np.uint8))
    
    @staticmethod
    def _watercolor(image: Image.Image) -> Image.Image:
        """Apply watercolor effect"""
        image = image.filter(ImageFilter.SMOOTH_MORE)
        image = image.filter(ImageFilter.EDGE_ENHANCE)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        return image
    
    @staticmethod
    def _pencil_sketch(image: Image.Image) -> Image.Image:
        """Apply pencil sketch effect"""
        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        blurred = inverted.filter(ImageFilter.GaussianBlur(21))
        sketch = Image.blend(gray, blurred, 0.5)
        return sketch
    
    @staticmethod
    def _cartoon(image: Image.Image) -> Image.Image:
        """Apply cartoon effect"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        smooth = cv2.bilateralFilter(img_array, 9, 75, 75)
        edges = cv2.Canny(img_array, 100, 200)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        cartoon = cv2.bitwise_and(smooth, edges)
        return Image.fromarray(cartoon)
    
    @staticmethod
    def _glitch(image: Image.Image) -> Image.Image:
        """Apply glitch effect"""
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        shift = 15
        img_array[:, :-shift, 0] = img_array[:, shift:, 0]
        img_array[:, shift:, 1] = img_array[:, :-shift, 1]
        
        for _ in range(20):
            y = random.randint(0, height - 10)
            shift_x = random.randint(-30, 30)
            img_array[y:y+5, :] = np.roll(img_array[y:y+5, :], shift_x, axis=1)
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _vhs(image: Image.Image) -> Image.Image:
        """Apply VHS effect"""
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        for y in range(0, height, 2):
            img_array[y:y+1, :] = img_array[y:y+1, :] * 0.7
        
        img_array[:, :, 0] = np.roll(img_array[:, :, 0], 3, axis=1)
        img_array[:, :, 2] = np.roll(img_array[:, :, 2], -3, axis=1)
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _chromatic_aberration(image: Image.Image) -> Image.Image:
        """Apply chromatic aberration effect"""
        img_array = np.array(image.convert('RGB'))
        shift = 5
        img_array[:, :, 0] = np.roll(img_array[:, :, 0], shift, axis=1)
        img_array[:, :, 2] = np.roll(img_array[:, :, 2], -shift, axis=1)
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _scanlines(image: Image.Image) -> Image.Image:
        """Apply scanlines effect"""
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        for y in range(0, height, 4):
            img_array[y:y+1, :] = img_array[y:y+1, :] * 0.5
        return Image.fromarray(img_array)
    
    @staticmethod
    def _retro(image: Image.Image) -> Image.Image:
        """Apply retro effect"""
        image = ImageProcessor._sepia(image)
        image = ImageProcessor._scanlines(image)
        return image
    
    @staticmethod
    def _dreamy(image: Image.Image) -> Image.Image:
        """Apply dreamy effect"""
        blur = image.filter(ImageFilter.GaussianBlur(5))
        blended = Image.blend(image, blur, 0.4)
        enhancer = ImageEnhance.Brightness(blended)
        return enhancer.enhance(1.1)
    
    # ==================== EDGE DETECTION ====================
    
    @staticmethod
    def _sobel_edge(image: Image.Image) -> Image.Image:
        """Apply Sobel edge detection"""
        if not SCIPY_AVAILABLE:
            return image
        img_array = np.array(ImageOps.grayscale(image)).astype(np.float32)
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
        
        grad_x = convolve(img_array, sobel_x)
        grad_y = convolve(img_array, sobel_y)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
        
        return Image.fromarray(magnitude, mode='L')
    
    @staticmethod
    def _canny_edge(image: Image.Image) -> Image.Image:
        """Apply Canny edge detection"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(ImageOps.grayscale(image))
        edges = cv2.Canny(img_array, 50, 150)
        return Image.fromarray(edges, mode='L')
    
    @staticmethod
    def _laplacian(image: Image.Image) -> Image.Image:
        """Apply Laplacian edge detection"""
        if not SCIPY_AVAILABLE:
            return image
        img_array = np.array(ImageOps.grayscale(image)).astype(np.float32)
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        edges = convolve(img_array, laplacian)
        edges = np.abs(edges)
        edges = (edges / edges.max() * 255).astype(np.uint8)
        return Image.fromarray(edges, mode='L')
    
    @staticmethod
    def _prewitt_edge(image: Image.Image) -> Image.Image:
        """Apply Prewitt edge detection"""
        if not SCIPY_AVAILABLE:
            return image
        img_array = np.array(ImageOps.grayscale(image)).astype(np.float32)
        prewitt_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        prewitt_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
        
        grad_x = convolve(img_array, prewitt_x)
        grad_y = convolve(img_array, prewitt_y)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
        
        return Image.fromarray(magnitude, mode='L')
    
    @staticmethod
    def _roberts_edge(image: Image.Image) -> Image.Image:
        """Apply Roberts edge detection"""
        if not SCIPY_AVAILABLE:
            return image
        img_array = np.array(ImageOps.grayscale(image)).astype(np.float32)
        roberts_x = np.array([[1, 0], [0, -1]])
        roberts_y = np.array([[0, 1], [-1, 0]])
        
        grad_x = convolve(img_array, roberts_x)
        grad_y = convolve(img_array, roberts_y)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
        
        return Image.fromarray(magnitude, mode='L')
    
    # ==================== DISTORTION FILTERS ====================
    
    @staticmethod
    def _fisheye(image: Image.Image) -> Image.Image:
        """Apply fisheye distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        radius = min(center_x, center_y)
        
        dx = (map_x - center_x) / radius
        dy = (map_y - center_y) / radius
        r = np.sqrt(dx**2 + dy**2)
        theta = np.arctan2(dy, dx)
        
        r_new = r ** 0.8
        map_x_new = center_x + r_new * np.cos(theta) * radius
        map_y_new = center_y + r_new * np.sin(theta) * radius
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    @staticmethod
    def _tilt_shift(image: Image.Image) -> Image.Image:
        """Apply tilt-shift effect"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        Y = np.arange(height)
        focus_center = height // 2
        focus_width = height // 4
        
        mask = np.exp(-((Y - focus_center) ** 2) / (2 * focus_width ** 2))
        mask = np.tile(mask[:, np.newaxis], (1, width))
        
        blurred = cv2.GaussianBlur(img_array, (25, 25), 0)
        
        mask_3d = np.stack([mask] * 3, axis=2)
        result = (img_array * (1 - mask_3d) + blurred * mask_3d).astype(np.uint8)
        
        return Image.fromarray(result)
    
    @staticmethod
    def _bulge(image: Image.Image) -> Image.Image:
        """Apply bulge distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        
        dx = (map_x - center_x) / (width // 2)
        dy = (map_y - center_y) / (height // 2)
        r = np.sqrt(dx**2 + dy**2)
        
        r_new = r ** 1.5
        map_x_new = center_x + dx / (r + 0.0001) * r_new * (width // 2)
        map_y_new = center_y + dy / (r + 0.0001) * r_new * (height // 2)
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    @staticmethod
    def _pinch(image: Image.Image) -> Image.Image:
        """Apply pinch distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        
        dx = (map_x - center_x) / (width // 2)
        dy = (map_y - center_y) / (height // 2)
        r = np.sqrt(dx**2 + dy**2)
        
        r_new = r ** 0.7
        map_x_new = center_x + dx / (r + 0.0001) * r_new * (width // 2)
        map_y_new = center_y + dy / (r + 0.0001) * r_new * (height // 2)
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    @staticmethod
    def _twirl(image: Image.Image) -> Image.Image:
        """Apply twirl distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        radius = min(center_x, center_y)
        
        dx = map_x - center_x
        dy = map_y - center_y
        r = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        twist_angle = angle + (r / radius) * np.pi
        map_x_new = center_x + r * np.cos(twist_angle)
        map_y_new = center_y + r * np.sin(twist_angle)
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    @staticmethod
    def _wave(image: Image.Image) -> Image.Image:
        """Apply wave distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        amplitude = 20
        frequency = 0.05
        
        map_x_new = map_x + amplitude * np.sin(map_y * frequency * np.pi * 2)
        map_y_new = map_y + amplitude * np.sin(map_x * frequency * np.pi * 2)
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    @staticmethod
    def _ripple(image: Image.Image) -> Image.Image:
        """Apply ripple distortion"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        map_x, map_y = np.meshgrid(np.arange(width), np.arange(height))
        amplitude = 10
        frequency = 0.1
        
        map_x_new = map_x + amplitude * np.sin(map_y * frequency * np.pi * 2)
        map_y_new = map_y + amplitude * np.cos(map_x * frequency * np.pi * 2)
        
        map_x_new = np.clip(map_x_new, 0, width - 1).astype(np.float32)
        map_y_new = np.clip(map_y_new, 0, height - 1).astype(np.float32)
        
        result = cv2.remap(img_array, map_x_new, map_y_new, cv2.INTER_LINEAR)
        return Image.fromarray(result)
    
    # ==================== SPECIAL FILTERS ====================
    
    @staticmethod
    def _infrared(image: Image.Image) -> Image.Image:
        """Apply infrared effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        result = np.stack([
            img_array[:, :, 0] * 1.5,
            img_array[:, :, 1] * 0.8,
            img_array[:, :, 2] * 0.3
        ], axis=2)
        result = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
        return ImageOps.grayscale(result)
    
    @staticmethod
    def _thermal(image: Image.Image) -> Image.Image:
        """Apply thermal imaging effect"""
        if not CV2_AVAILABLE:
            return image
        gray = np.array(ImageOps.grayscale(image))
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return Image.fromarray(cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB))
    
    @staticmethod
    def _xray(image: Image.Image) -> Image.Image:
        """Apply x-ray effect"""
        img_array = np.array(ImageOps.grayscale(image))
        inverted = 255 - img_array
        return Image.fromarray(inverted, mode='L')
    
    @staticmethod
    def _dream(image: Image.Image) -> Image.Image:
        """Apply dream effect"""
        blur = image.filter(ImageFilter.GaussianBlur(5))
        blended = Image.blend(image, blur, 0.4)
        enhancer = ImageEnhance.Brightness(blended)
        return enhancer.enhance(1.1)
    
    @staticmethod
    def _fire(image: Image.Image) -> Image.Image:
        """Apply fire effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.5, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.6, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.3, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _ice(image: Image.Image) -> Image.Image:
        """Apply ice effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.5, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.8, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.5, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _magic(image: Image.Image) -> Image.Image:
        """Apply magic effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = (img_array - 127.5) * 1.5 + 127.5
        img_array = np.clip(img_array, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _nebula(image: Image.Image) -> Image.Image:
        """Apply nebula effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.8 + 50, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.5 + 100, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.2 + 30, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _aurora(image: Image.Image) -> Image.Image:
        """Apply aurora effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.5 + 30, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.3, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.7 + 50, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _sunrise(image: Image.Image) -> Image.Image:
        """Apply sunrise effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.4, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.1, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.6, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _twilight(image: Image.Image) -> Image.Image:
        """Apply twilight effect"""
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.7, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.8, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.3, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    # ==================== BASIC EDITING FUNCTIONS ====================
    
    @staticmethod
    def resize(image: Image.Image, width: int = None, height: int = None, keep_ratio: bool = True) -> Image.Image:
        """Resize image"""
        original_w, original_h = image.size
        if width is None and height is None:
            return image
        
        if keep_ratio:
            if width and height:
                ratio = min(width / original_w, height / original_h)
                new_w, new_h = int(original_w * ratio), int(original_h * ratio)
            elif width:
                ratio = width / original_w
                new_w, new_h = width, int(original_h * ratio)
            else:
                ratio = height / original_h
                new_w, new_h = int(original_w * ratio), height
        else:
            new_w, new_h = width or original_w, height or original_h
        
        return image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    @staticmethod
    def rotate(image: Image.Image, angle: int, expand: bool = True) -> Image.Image:
        """Rotate image"""
        return image.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)
    
    @staticmethod
    def flip_horizontal(image: Image.Image) -> Image.Image:
        """Flip horizontally"""
        return ImageOps.mirror(image)
    
    @staticmethod
    def flip_vertical(image: Image.Image) -> Image.Image:
        """Flip vertically"""
        return ImageOps.flip(image)
    
    @staticmethod
    def crop(image: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
        """Crop image"""
        return image.crop((left, top, right, bottom))
    
    @staticmethod
    def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
        """Adjust brightness"""
        return ImageEnhance.Brightness(image).enhance(factor)
    
    @staticmethod
    def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
        """Adjust contrast"""
        return ImageEnhance.Contrast(image).enhance(factor)
    
    @staticmethod
    def adjust_saturation(image: Image.Image, factor: float) -> Image.Image:
        """Adjust saturation"""
        return ImageEnhance.Color(image).enhance(factor)
    
    @staticmethod
    def adjust_sharpness(image: Image.Image, factor: float) -> Image.Image:
        """Adjust sharpness"""
        return ImageEnhance.Sharpness(image).enhance(factor)
    
    @staticmethod
    def add_text(image: Image.Image, text: str, x: int = 10, y: int = 10, 
                 font_size: int = 30, color: str = 'white') -> Image.Image:
        """Add text to image"""
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Add stroke for better visibility
        draw.text((x-1, y-1), text, fill='black', font=font)
        draw.text((x+1, y+1), text, fill='black', font=font)
        draw.text((x, y), text, fill=color, font=font)
        return image
    
    @staticmethod
    def add_watermark(image: Image.Image, text: str, opacity: float = 0.5) -> Image.Image:
        """Add watermark to image"""
        watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255, int(255 * opacity)), font=font)
        
        return Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')
    
    @staticmethod
    def auto_enhance(image: Image.Image) -> Image.Image:
        """Auto enhance image"""
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.15)
        return image
    
    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        """Remove background (basic implementation)"""
        if not CV2_AVAILABLE:
            return image
        img_array = np.array(image.convert('RGB'))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.dilate(edges, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=1)
        result = cv2.bitwise_and(img_array, img_array, mask=mask)
        return Image.fromarray(result)
    
    @staticmethod
    def create_collage(images: List[Image.Image], layout: str = 'grid') -> Image.Image:
        """Create collage from multiple images"""
        if not images:
            return None
        if len(images) == 1:
            return images[0]
        
        if layout == 'grid':
            per_row = min(2, len(images))
            rows = (len(images) + per_row - 1) // per_row
            target_size = (500, 500)
            resized = [img.resize(target_size, Image.Resampling.LANCZOS) for img in images[:4]]
            collage = Image.new('RGB', (target_size[0] * per_row, target_size[1] * rows), (255, 255, 255))
            for i, img in enumerate(resized):
                x = (i % per_row) * target_size[0]
                y = (i // per_row) * target_size[1]
                collage.paste(img, (x, y))
            return collage
        elif layout == 'horizontal':
            total_width = sum(img.width for img in images)
            max_height = max(img.height for img in images)
            collage = Image.new('RGB', (total_width, max_height), (255, 255, 255))
            x_offset = 0
            for img in images:
                collage.paste(img, (x_offset, 0))
                x_offset += img.width
            return collage
        elif layout == 'vertical':
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            collage = Image.new('RGB', (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in images:
                collage.paste(img, (0, y_offset))
                y_offset += img.height
            return collage
        
        return images[0]
# ==================== VIDEO PROCESSOR ====================

class VideoProcessor:
    """Professional video processing with compression, editing, and quality encoding"""
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict:
        """Get detailed video information"""
        if not MOVIEPY_AVAILABLE:
            return {'error': 'MoviePy not available'}
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': round(clip.duration, 2),
                'fps': round(clip.fps, 2),
                'width': clip.size[0],
                'height': clip.size[1],
                'size_mb': round(os.path.getsize(video_path) / (1024 * 1024), 2),
                'has_audio': clip.audio is not None,
                'aspect_ratio': round(clip.size[0] / clip.size[1], 2)
            }
            if clip.audio:
                info['audio_duration'] = round(clip.audio.duration, 2)
            clip.close()
            return info
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def trim(video_path: str, start_time: float, end_time: float, output_path: str) -> Tuple[bool, str]:
        """Trim video from start to end time"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            start = max(0, min(start_time, duration))
            end = min(end_time, duration)
            
            if start >= end:
                clip.close()
                return False, "Start time must be less than end time"
            
            trimmed = clip.subclip(start, end)
            trimmed.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None,
                threads=4
            )
            trimmed.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_speed(video_path: str, speed_factor: float, output_path: str) -> Tuple[bool, str]:
        """Change video speed (slow motion or fast motion)"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            if speed_factor < 0.1 or speed_factor > 10:
                clip.close()
                return False, "Speed factor must be between 0.1 and 10"
            
            sped = clip.fx(vfx.speedx, speed_factor)
            sped.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None,
                threads=4
            )
            sped.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_audio(video_path: str, output_path: str, format: str = 'mp3') -> Tuple[bool, str]:
        """Extract audio from video"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                clip.close()
                return False, "No audio track found in video"
            
            audio_codec = 'mp3' if format == 'mp3' else 'aac'
            clip.audio.write_audiofile(
                output_path, 
                codec=audio_codec,
                logger=None
            )
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def mute(video_path: str, output_path: str) -> Tuple[bool, str]:
        """Remove audio from video"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            muted = clip.without_audio()
            muted.write_videofile(
                output_path, 
                codec='libx264',
                logger=None,
                threads=4
            )
            muted.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_watermark(video_path: str, text: str, output_path: str, 
                      position: str = 'bottom-right') -> Tuple[bool, str]:
        """Add text watermark to video"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            
            position_map = {
                'top-left': ('left', 'top'),
                'top-right': ('right', 'top'),
                'bottom-left': ('left', 'bottom'),
                'bottom-right': ('right', 'bottom'),
                'center': ('center', 'center')
            }
            pos = position_map.get(position, ('right', 'bottom'))
            
            txt = TextClip(
                text, 
                fontsize=30, 
                color='white', 
                font='Arial',
                stroke_color='black',
                stroke_width=1
            )
            txt = txt.set_position(pos).set_duration(clip.duration)
            
            final = CompositeVideoClip([clip, txt])
            final.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            clip.close()
            txt.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def to_gif(video_path: str, start: float, end: float, output_path: str, 
               fps: int = 10, width: int = 480) -> Tuple[bool, str]:
        """Convert video segment to GIF"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            duration = min(end - start, 15)  # Max 15 seconds for GIF
            clip = VideoFileClip(video_path).subclip(start, start + duration)
            
            # Resize if needed
            if clip.size[0] > width:
                clip = clip.resize(width=width)
            
            clip.write_gif(
                output_path, 
                fps=fps,
                logger=None,
                program='ffmpeg'
            )
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def compress(video_path: str, output_path: str, quality: str = '720p') -> Tuple[bool, str]:
        """Compress video using ffmpeg with quality presets"""
        if quality not in VIDEO_QUALITIES:
            quality = '720p'
        
        preset = VIDEO_QUALITIES[quality]
        width = preset['width']
        height = preset['height']
        bitrate = preset['bitrate']
        fps = preset.get('fps', 30)
        
        # ffmpeg command for compression
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', f'{int(bitrate[:-1]) * 2}k',
            '-r', str(fps),
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return True, output_path
            else:
                return False, f"FFmpeg error: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return False, "Compression timeout (5 minutes)"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def merge_videos(video_paths: List[str], output_path: str) -> Tuple[bool, str]:
        """Merge multiple videos into one"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        if len(video_paths) < 2:
            return False, "Need at least 2 videos to merge"
        
        try:
            clips = [VideoFileClip(path) for path in video_paths]
            final = concatenate_videoclips(clips)
            final.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            final.close()
            for clip in clips:
                clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_audio(video_path: str, audio_path: str, output_path: str) -> Tuple[bool, str]:
        """Add external audio to video"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # Loop audio if shorter than video
            if audio.duration < video.duration:
                audio = audio.fx(audio_loop, duration=video.duration)
            else:
                audio = audio.subclip(0, video.duration)
            
            final = video.set_audio(audio)
            final.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            video.close()
            audio.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def resize(video_path: str, width: int, height: int, output_path: str) -> Tuple[bool, str]:
        """Resize video to specific dimensions"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            resized = clip.resize((width, height))
            resized.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            resized.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def rotate(video_path: str, angle: int, output_path: str) -> Tuple[bool, str]:
        """Rotate video by angle"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            rotated = clip.rotate(angle)
            rotated.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            rotated.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def crop(video_path: str, x1: int, y1: int, x2: int, y2: int, output_path: str) -> Tuple[bool, str]:
        """Crop video to specified region"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
            cropped.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            cropped.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_fade(video_path: str, fade_in: float = 1, fade_out: float = 1, 
                 output_path: str) -> Tuple[bool, str]:
        """Add fade in and fade out effects"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            faded = clip.fx(fadein, fade_in).fx(fadeout, fade_out)
            faded.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            faded.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def reverse(video_path: str, output_path: str) -> Tuple[bool, str]:
        """Reverse video playback"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            reversed_clip = clip.fx(vfx.time_mirror)
            reversed_clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                logger=None,
                threads=4
            )
            reversed_clip.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_frames(video_path: str, output_dir: str, interval: float = 1) -> Tuple[bool, str]:
        """Extract frames from video at regular intervals"""
        if not MOVIEPY_AVAILABLE:
            return False, "MoviePy not available"
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            frame_count = 0
            
            for t in range(0, int(duration), int(interval)):
                frame = clip.get_frame(t)
                frame_img = Image.fromarray(frame)
                frame_path = os.path.join(output_dir, f"frame_{t}.jpg")
                frame_img.save(frame_path)
                frame_count += 1
            
            clip.close()
            return True, f"Extracted {frame_count} frames"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def _parse_time(time_str: str) -> float:
        """Parse time string to seconds"""
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
        return float(time_str)


# ==================== AUDIO PROCESSOR ====================

class AudioProcessor:
    """Professional audio processing with various effects"""
    
    @staticmethod
    def get_audio_info(audio_path: str) -> Dict:
        """Get audio file information"""
        if not PYDUB_AVAILABLE:
            return {'error': 'Pydub not available'}
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                'duration': round(len(audio) / 1000, 2),
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'size_mb': round(os.path.getsize(audio_path) / (1024 * 1024), 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def convert_format(audio_path: str, output_path: str, format: str = 'mp3') -> Tuple[bool, str]:
        """Convert audio to different format"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            audio.export(output_path, format=format)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_volume(audio_path: str, factor: float, output_path: str) -> Tuple[bool, str]:
        """Change audio volume"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            louder = audio + (factor * 10)  # dB adjustment
            louder.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def trim_audio(audio_path: str, start: float, end: float, output_path: str) -> Tuple[bool, str]:
        """Trim audio segment"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            start_ms = int(start * 1000)
            end_ms = int(end * 1000)
            trimmed = audio[start_ms:end_ms]
            trimmed.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_speed(audio_path: str, speed_factor: float, output_path: str) -> Tuple[bool, str]:
        """Change audio playback speed"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            # Change speed using ffmpeg
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-filter:a', f'atempo={speed_factor}',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, output_path
            return False, "Speed change failed"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def reverse_audio(audio_path: str, output_path: str) -> Tuple[bool, str]:
        """Reverse audio playback"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            reversed_audio = audio.reverse()
            reversed_audio.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def fade(audio_path: str, fade_in: float, fade_out: float, output_path: str) -> Tuple[bool, str]:
        """Add fade in and fade out effects"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            audio = AudioSegment.from_file(audio_path)
            fade_in_ms = int(fade_in * 1000)
            fade_out_ms = int(fade_out * 1000)
            faded = audio.fade_in(fade_in_ms).fade_out(fade_out_ms)
            faded.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def compress_audio(audio_path: str, output_path: str, quality: str = 'medium') -> Tuple[bool, str]:
        """Compress audio quality"""
        if quality not in AUDIO_QUALITIES:
            quality = 'medium'
        
        preset = AUDIO_QUALITIES[quality]
        bitrate = preset['bitrate']
        sample_rate = preset['sample_rate']
        
        cmd = [
            'ffmpeg', '-i', audio_path,
            '-b:a', bitrate,
            '-ar', str(sample_rate),
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, output_path
            return False, "Compression failed"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def merge_audios(audio_paths: List[str], output_path: str) -> Tuple[bool, str]:
        """Merge multiple audio files"""
        if not PYDUB_AVAILABLE:
            return False, "Pydub not available"
        try:
            combined = AudioSegment.empty()
            for path in audio_paths:
                audio = AudioSegment.from_file(path)
                combined += audio
            combined.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_voice(audio_path: str, output_path: str) -> Tuple[bool, str]:
        """Extract voice/vocals from audio (basic implementation)"""
        if not LIBROSA_AVAILABLE:
            return False, "Librosa not available"
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Simple voice extraction (high-pass filter)
            from scipy import signal
            b, a = signal.butter(4, 300, 'hp', fs=sr)
            y_voice = signal.filtfilt(b, a, y)
            
            # Save
            sf.write(output_path, y_voice, sr)
            return True, output_path
        except Exception as e:
            return False, str(e)


# ==================== CODE FORMATTER ====================

class CodeFormatter:
    """Format and beautify code in multiple languages"""
    
    @staticmethod
    def format_python(code: str) -> Tuple[str, bool]:
        """Format Python code"""
        try:
            import autopep8
            formatted = autopep8.fix_code(code, options={'aggressive': 2})
            return formatted, True
        except ImportError:
            # Manual indentation
            lines = code.strip().split('\n')
            formatted = []
            indent = 0
            for line in lines:
                stripped = line.strip()
                if stripped.endswith(':'):
                    formatted.append('    ' * indent + stripped)
                    indent += 1
                elif stripped in ['}', ')', ']']:
                    indent = max(0, indent - 1)
                    formatted.append('    ' * indent + stripped)
                else:
                    formatted.append('    ' * indent + stripped)
                    if stripped.endswith('{') or stripped.endswith('(') or stripped.endswith('['):
                        indent += 1
            return '\n'.join(formatted), True
    
    @staticmethod
    def format_javascript(code: str) -> Tuple[str, bool]:
        """Format JavaScript code"""
        try:
            import jsbeautifier
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            formatted = jsbeautifier.beautify(code, opts)
            return formatted, True
        except ImportError:
            return code, False
    
    @staticmethod
    def format_json(code: str) -> Tuple[str, bool]:
        """Format JSON"""
        try:
            parsed = json.loads(code)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return formatted, True
        except:
            return code, False
    
    @staticmethod
    def format_html(code: str) -> Tuple[str, bool]:
        """Format HTML"""
        try:
            import jsbeautifier
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            formatted = jsbeautifier.beautify(code, opts)
            return formatted, True
        except ImportError:
            return code, False
    
    @staticmethod
    def format_css(code: str) -> Tuple[str, bool]:
        """Format CSS"""
        try:
            import jsbeautifier
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            formatted = jsbeautifier.beautify(code, opts)
            return formatted, True
        except ImportError:
            return code, False
    
    @staticmethod
    def format_sql(code: str) -> Tuple[str, bool]:
        """Format SQL"""
        try:
            import sqlparse
            formatted = sqlparse.format(code, reindent=True, keyword_case='upper')
            return formatted, True
        except ImportError:
            return code, False
    
    @staticmethod
    def detect_language(code: str) -> str:
        """Auto-detect programming language"""
        code_lower = code.lower().strip()
        
        # Check for specific patterns
        if code_lower.startswith('<?php'):
            return 'php'
        elif '<html' in code_lower or '<!doctype' in code_lower:
            return 'html'
        elif code_lower.startswith('select') or code_lower.startswith('insert'):
            return 'sql'
        elif code_lower.startswith('{') or code_lower.startswith('['):
            try:
                json.loads(code)
                return 'json'
            except:
                pass
        
        patterns = {
            'python': [r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+', r'\bimport\s+\w+', r'\bprint\s*\('],
            'javascript': [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=', r'\bconsole\.log'],
            'typescript': [r'\binterface\s+\w+', r'\btype\s+\w+\s*=', r':\s*(string|number|boolean)\b'],
            'css': [r'[.#][\w-]+\s*\{', r'\b(margin|padding|color|font-size)\s*:'],
        }
        
        for lang, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, code, re.IGNORECASE):
                    return lang
        
        return 'text'
    
    @staticmethod
    def format_code(code: str, language: str = None) -> Tuple[str, str, bool]:
        """Format code in specified language"""
        if not language or language == 'auto':
            language = CodeFormatter.detect_language(code)
        
        formatters = {
            'python': CodeFormatter.format_python,
            'py': CodeFormatter.format_python,
            'javascript': CodeFormatter.format_javascript,
            'js': CodeFormatter.format_javascript,
            'typescript': CodeFormatter.format_javascript,
            'ts': CodeFormatter.format_javascript,
            'json': CodeFormatter.format_json,
            'html': CodeFormatter.format_html,
            'css': CodeFormatter.format_css,
            'sql': CodeFormatter.format_sql,
        }
        
        formatter = formatters.get(language.lower())
        if formatter:
            formatted, success = formatter(code)
            return formatted, language, success
        
        return code, language, False


# ==================== KEYBOARD BUILDER ====================

class KeyboardBuilder:
    """Build inline keyboards for bot menus"""
    
    @staticmethod
    def get_main_menu(is_admin: bool = False, is_premium: bool = False) -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("🖼️ EDIT IMAGE", callback_data="mode_image"),
             InlineKeyboardButton("🎬 EDIT VIDEO", callback_data="mode_video")],
            [InlineKeyboardButton("🎵 EDIT AUDIO", callback_data="mode_audio"),
             InlineKeyboardButton("🎞️ CREATE GIF", callback_data="mode_gif")],
            [InlineKeyboardButton("✨ AI ENHANCE", callback_data="ai_enhance"),
             InlineKeyboardButton("🎨 COLLAGE", callback_data="collage")],
            [InlineKeyboardButton("⭐ DAILY REWARD", callback_data="daily_reward"),
             InlineKeyboardButton("📊 MY STATS", callback_data="stats")],
            [InlineKeyboardButton("💎 PREMIUM" + (" ✅" if is_premium else ""), callback_data="premium"),
             InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
            [InlineKeyboardButton("💻 CODE FORMAT", callback_data="code_format"),
             InlineKeyboardButton("⚡ CUSTOM CMD", callback_data="custom_commands_menu")],
            [InlineKeyboardButton("📝 FEEDBACK", callback_data="feedback"),
             InlineKeyboardButton("❓ HELP", callback_data="help")],
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        """Get admin panel keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats"),
             InlineKeyboardButton("👥 USER LIST", callback_data="admin_users")],
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("📅 SCHEDULE", callback_data="admin_schedule")],
            [InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban"),
             InlineKeyboardButton("✅ UNBAN USER", callback_data="admin_unban")],
            [InlineKeyboardButton("🔇 MUTE USER", callback_data="admin_mute"),
             InlineKeyboardButton("🔊 UNMUTE USER", callback_data="admin_unmute")],
            [InlineKeyboardButton("⚠️ WARN USER", callback_data="admin_warn"),
             InlineKeyboardButton("📋 WARNINGS", callback_data="admin_warnings")],
            [InlineKeyboardButton("💎 GIVE PREMIUM", callback_data="admin_give_premium"),
             InlineKeyboardButton("💰 ADD CREDITS", callback_data="admin_add_credits")],
            [InlineKeyboardButton("📝 AUTO RESPONSE", callback_data="admin_auto_responses"),
             InlineKeyboardButton("⚡ CUSTOM CMDS", callback_data="admin_custom_cmds")],
            [InlineKeyboardButton("📋 FEEDBACK", callback_data="admin_feedback"),
             InlineKeyboardButton("📜 ADMIN LOGS", callback_data="admin_logs")],
            [InlineKeyboardButton("📊 EXPORT DATA", callback_data="admin_export"),
             InlineKeyboardButton("🔄 RESET USER", callback_data="admin_reset")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_commands_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Get custom commands menu"""
        keyboard = [
            [InlineKeyboardButton("📋 LIST COMMANDS", callback_data="list_custom_cmds")],
            [InlineKeyboardButton("🔍 SEARCH COMMAND", callback_data="search_custom_cmd")],
        ]
        if is_admin:
            keyboard.extend([
                [InlineKeyboardButton("➕ ADD COMMAND", callback_data="add_custom_cmd")],
                [InlineKeyboardButton("❌ DELETE COMMAND", callback_data="delete_custom_cmd")],
                [InlineKeyboardButton("🔧 TOGGLE COMMAND", callback_data="toggle_custom_cmd")],
                [InlineKeyboardButton("📋 ALL COMMANDS", callback_data="list_all_custom_cmds")],
            ])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_image_menu() -> InlineKeyboardMarkup:
        """Get image editing menu"""
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS", callback_data="img_filters")],
            [InlineKeyboardButton("📐 RESIZE", callback_data="img_resize"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="img_rotate")],
            [InlineKeyboardButton("🪞 FLIP H", callback_data="img_flip_h"),
             InlineKeyboardButton("↕️ FLIP V", callback_data="img_flip_v")],
            [InlineKeyboardButton("✂️ CROP", callback_data="img_crop"),
             InlineKeyboardButton("☀️ BRIGHTNESS", callback_data="img_brightness")],
            [InlineKeyboardButton("🌓 CONTRAST", callback_data="img_contrast"),
             InlineKeyboardButton("🎨 SATURATION", callback_data="img_saturation")],
            [InlineKeyboardButton("✏️ SHARPNESS", callback_data="img_sharpness"),
             InlineKeyboardButton("📝 ADD TEXT", callback_data="img_text")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="img_watermark"),
             InlineKeyboardButton("✨ AUTO ENHANCE", callback_data="img_auto")],
            [InlineKeyboardButton("🎭 REMOVE BG", callback_data="img_remove_bg"),
             InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_video_menu() -> InlineKeyboardMarkup:
        """Get video editing menu"""
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="vid_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="vid_speed")],
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="vid_audio"),
             InlineKeyboardButton("🔊 MUTE", callback_data="vid_mute")],
            [InlineKeyboardButton("📐 RESIZE", callback_data="vid_resize"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="vid_rotate")],
            [InlineKeyboardButton("🏷️ WATERMARK", callback_data="vid_watermark"),
             InlineKeyboardButton("🎞️ TO GIF", callback_data="vid_to_gif")],
            [InlineKeyboardButton("📦 COMPRESS", callback_data="vid_compress"),
             InlineKeyboardButton("🔗 MERGE", callback_data="vid_merge")],
            [InlineKeyboardButton("🎵 ADD AUDIO", callback_data="vid_add_audio"),
             InlineKeyboardButton("ℹ️ INFO", callback_data="vid_info")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_quality_menu() -> InlineKeyboardMarkup:
        """Get video quality menu for compression"""
        keyboard = [
            [InlineKeyboardButton("📱 144p", callback_data="quality_144p"),
             InlineKeyboardButton("📱 240p", callback_data="quality_240p")],
            [InlineKeyboardButton("📱 360p", callback_data="quality_360p"),
             InlineKeyboardButton("📱 480p", callback_data="quality_480p")],
            [InlineKeyboardButton("💻 720p", callback_data="quality_720p"),
             InlineKeyboardButton("💻 1080p", callback_data="quality_1080p")],
            [InlineKeyboardButton("🖥️ 2K", callback_data="quality_2K"),
             InlineKeyboardButton("🖥️ 4K", callback_data="quality_4K")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_video")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_filters_menu() -> InlineKeyboardMarkup:
        """Get image filters menu"""
        filters = [
            "Blur", "Sharpen", "Grayscale", "Sepia", "Negative", "Vintage",
            "Warm", "Cool", "Dramatic", "Cinematic", "Neon", "Glow",
            "Vignette", "Pixelate", "Oil Paint", "Watercolor", "Pencil Sketch",
            "Cartoon", "Glitch", "VHS", "Fisheye", "Tilt Shift", "HDR"
        ]
        keyboard = []
        row = []
        for f in filters:
            row.append(InlineKeyboardButton(f[:12], callback_data=f"filter_{f.lower().replace(' ', '_')}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_image")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_audio_menu() -> InlineKeyboardMarkup:
        """Get audio editing menu"""
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="aud_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="aud_speed")],
            [InlineKeyboardButton("🔊 VOLUME", callback_data="aud_volume"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="aud_reverse")],
            [InlineKeyboardButton("🎵 CONVERT", callback_data="aud_convert"),
             InlineKeyboardButton("📦 COMPRESS", callback_data="aud_compress")],
            [InlineKeyboardButton("🔗 MERGE", callback_data="aud_merge"),
             InlineKeyboardButton("ℹ️ INFO", callback_data="aud_info")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_code_format_menu() -> InlineKeyboardMarkup:
        """Get code formatting menu"""
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="format_python"),
             InlineKeyboardButton("📜 JavaScript", callback_data="format_js")],
            [InlineKeyboardButton("📘 TypeScript", callback_data="format_ts"),
             InlineKeyboardButton("🌐 HTML", callback_data="format_html")],
            [InlineKeyboardButton("🎨 CSS", callback_data="format_css"),
             InlineKeyboardButton("📊 JSON", callback_data="format_json")],
            [InlineKeyboardButton("🗄️ SQL", callback_data="format_sql"),
             InlineKeyboardButton("🔍 Auto Detect", callback_data="format_auto")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_captcha_keyboard(correct: str, options: List[str]) -> InlineKeyboardMarkup:
        """Get CAPTCHA keyboard with options"""
        keyboard = []
        row = []
        for opt in options:
            row.append(InlineKeyboardButton(opt, callback_data=f"captcha_{opt}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
# ==================== MAIN BOT CLASS ====================

class KinvaMasterBot:
    """Main bot class handling all commands and callbacks"""
    
    def __init__(self):
        self.db = DatabaseManager(DATABASE_PATH)
        self.sessions: Dict[int, UserSession] = {}
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.code_formatter = CodeFormatter()
        self.application = None
        self.flask_app = None
        self.user_rate_limits = defaultdict(list)
        self._background_tasks = []
    
    async def start(self):
        """Start the bot with polling mode"""
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        self._register_handlers()
        await self._set_bot_commands()
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("✅ KIRA-FX Bot started in polling mode")
        
        self._start_web_server()
        self._background_tasks.append(asyncio.create_task(self._cleanup_sessions_loop()))
        self._background_tasks.append(asyncio.create_task(self._process_scheduled_messages()))
        
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await self.stop()
    
    def _start_web_server(self):
        """Start Flask web server for health checks"""
        if not FLASK_AVAILABLE:
            logger.warning("Flask not available. Web server disabled.")
            return
        
        try:
            self.flask_app = Flask(__name__)
            
            @self.flask_app.route('/health', methods=['GET'])
            def health():
                return jsonify({"status": "ok", "time": datetime.now().isoformat()}), 200
            
            @self.flask_app.route('/stats', methods=['GET'])
            def stats():
                return jsonify(self.db.get_bot_stats()), 200
            
            @self.flask_app.route('/', methods=['GET'])
            def home():
                return "KIRA-FX BOT - RUNNING ✅", 200
            
            def run_flask():
                self.flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
            
            thread = threading.Thread(target=run_flask, daemon=True)
            thread.start()
            logger.info(f"🌐 Web server started on port {PORT}")
        except Exception as e:
            logger.error(f"Web server error: {e}")
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        for task in self._background_tasks:
            task.cancel()
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        logger.info("✅ Bot stopped.")
    
    def _register_handlers(self):
        """Register all command and message handlers"""
        # User commands
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.application.add_handler(CommandHandler("daily", self.cmd_daily))
        self.application.add_handler(CommandHandler("refer", self.cmd_refer))
        self.application.add_handler(CommandHandler("credits", self.cmd_credits))
        self.application.add_handler(CommandHandler("premium", self.cmd_premium))
        self.application.add_handler(CommandHandler("feedback", self.cmd_feedback))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.cmd_admin))
        self.application.add_handler(CommandHandler("broadcast", self.cmd_broadcast))
        self.application.add_handler(CommandHandler("ban", self.cmd_ban))
        self.application.add_handler(CommandHandler("unban", self.cmd_unban))
        self.application.add_handler(CommandHandler("mute", self.cmd_mute))
        self.application.add_handler(CommandHandler("unmute", self.cmd_unmute))
        self.application.add_handler(CommandHandler("warn", self.cmd_warn))
        self.application.add_handler(CommandHandler("clearwarns", self.cmd_clear_warns))
        self.application.add_handler(CommandHandler("givepremium", self.cmd_give_premium))
        self.application.add_handler(CommandHandler("addcredits", self.cmd_add_credits))
        
        # Custom commands
        self.application.add_handler(CommandHandler("customcmd", self.cmd_custom_command))
        self.application.add_handler(CommandHandler("run", self.cmd_custom_command))
        self.application.add_handler(CommandHandler("addcmd", self.cmd_add_custom_command))
        
        # Callbacks and messages
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    async def _set_bot_commands(self):
        """Set bot commands menu"""
        commands = [
            BotCommand("start", "🚀 Start the bot"),
            BotCommand("help", "❓ Get help"),
            BotCommand("stats", "📊 Your statistics"),
            BotCommand("daily", "⭐ Claim daily reward"),
            BotCommand("refer", "👥 Referral info"),
            BotCommand("credits", "💰 Check credits"),
            BotCommand("premium", "💎 Premium features"),
            BotCommand("feedback", "📝 Send feedback"),
            BotCommand("cancel", "❌ Cancel operation"),
            BotCommand("customcmd", "⚡ Use custom command"),
            BotCommand("run", "⚡ Run custom command"),
            BotCommand("addcmd", "➕ Add custom command (admin)"),
            BotCommand("admin", "👑 Admin panel (admin)"),
        ]
        await self.application.bot.set_my_commands(commands)
    
    def get_session(self, user_id: int) -> UserSession:
        """Get or create user session"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        self.user_rate_limits[user_id] = [
            t for t in self.user_rate_limits[user_id] 
            if (now - t).seconds < RATE_LIMIT_SECONDS
        ]
        if len(self.user_rate_limits[user_id]) >= MAX_COMMANDS_PER_MINUTE:
            return False
        self.user_rate_limits[user_id].append(now)
        return True
    
    async def _cleanup_sessions_loop(self):
        """Clean up expired sessions periodically"""
        while True:
            try:
                await asyncio.sleep(60)
                now = datetime.now()
                expired = []
                for user_id, session in self.sessions.items():
                    if session.state == UserState.AWAITING_CAPTCHA:
                        if session.captcha_time and (now - session.captcha_time).seconds > CAPTCHA_TIMEOUT:
                            expired.append(user_id)
                    elif (now - session.last_active).seconds > 3600:  # 1 hour timeout
                        expired.append(user_id)
                
                for user_id in expired:
                    if user_id in self.sessions:
                        session = self.sessions[user_id]
                        for f in session.temp_files:
                            if os.path.exists(f):
                                try:
                                    os.remove(f)
                                except:
                                    pass
                        del self.sessions[user_id]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _process_scheduled_messages(self):
        """Process scheduled messages"""
        while True:
            try:
                await asyncio.sleep(30)
                messages = self.db.get_pending_scheduled_messages()
                for msg in messages:
                    users = self.db.get_all_users(limit=10000)
                    success = 0
                    for user in users:
                        try:
                            if msg['media_type'] == 'text':
                                await self.application.bot.send_message(
                                    chat_id=user['user_id'],
                                    text=f"📅 *SCHEDULED MESSAGE*\n\n{msg['message']}",
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            elif msg['media_type'] == 'photo' and msg['media_id']:
                                await self.application.bot.send_photo(
                                    chat_id=user['user_id'],
                                    photo=msg['media_id'],
                                    caption=msg['message']
                                )
                            success += 1
                            await asyncio.sleep(0.05)
                        except:
                            pass
                    self.db.mark_scheduled_sent(msg['id'])
                    logger.info(f"Scheduled message sent to {success} users")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduled messages error: {e}")
    
    # ==================== USER COMMANDS ====================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Check referral
        args = context.args
        referred_by = int(args[0]) if args and args[0].isdigit() and int(args[0]) != user_id else None
        
        self.db.register_user(user_id, user.username, user.first_name, user.last_name, referred_by)
        
        if self.db.is_verified(user_id):
            await self._send_main_menu(update, user)
            return
        
        # Generate CAPTCHA
        num1, num2 = random.randint(5, 20), random.randint(5, 20)
        op = random.choice(['+', '-'])
        if op == '+':
            answer = str(num1 + num2)
        else:
            answer = str(num1 - num2)
        
        options = [answer]
        while len(options) < 4:
            wrong = str(int(answer) + random.randint(-5, 5))
            if wrong != answer and wrong not in options:
                options.append(wrong)
        random.shuffle(options)
        
        session = self.get_session(user_id)
        session.captcha_code = answer
        session.captcha_attempts = 0
        session.captcha_time = datetime.now()
        session.state = UserState.AWAITING_CAPTCHA
        
        await update.message.reply_text(
            f"🌟 *WELCOME TO KIRA-FX ULTRA BOT* 🌟\n\n"
            f"*Advanced Media Editing Bot*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *Features:*\n"
            f"• 🖼️ 100+ Image Filters\n"
            f"• 🎬 Video Editing & Compression\n"
            f"• 🎵 Audio Processing\n"
            f"• 💻 Code Formatter\n"
            f"• ⚡ Custom Commands\n"
            f"• 💰 Credits & Rewards\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔐 *VERIFICATION REQUIRED*\n\n"
            f"Please solve:\n\n`{num1} {op} {num2} = ?`\n\n"
            f"_You have {CAPTCHA_TIMEOUT} seconds._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_captcha_keyboard(answer, options)
        )
    
    async def _send_main_menu(self, update: Update, user: User):
        """Send main menu to user"""
        user_id = user.id
        is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
        is_premium = self.db.is_premium(user_id)
        stats = self.db.get_user_stats(user_id)
        
        menu_msg = (
            f"🎨 *KIRA-FX ULTRA BOT* 🎨\n\n"
            f"*Welcome back, {user.first_name}!*\n\n"
            f"📊 *Your Stats:*\n"
            f"• Total Edits: `{stats.get('total_edits', 0)}`\n"
            f"• Images: `{stats.get('total_images', 0)}`\n"
            f"• Videos: `{stats.get('total_videos', 0)}`\n"
            f"• Credits: `{stats.get('credits', 100)}`\n"
            f"• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Select an option:*"
        )
        await update.message.reply_text(
            menu_msg, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium)
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "❓ *KIRA-FX ULTRA BOT HELP* ❓\n\n"
            "*Image Editing:*\n"
            "• 100+ professional filters\n"
            "• Resize, rotate, flip, crop\n"
            "• Adjust brightness, contrast, saturation\n"
            "• Add text or watermark\n"
            "• Auto-enhance, remove background\n\n"
            "*Video Editing:*\n"
            "• Trim, merge, speed change\n"
            "• Extract audio, mute, add audio\n"
            "• Add watermark, resize, rotate\n"
            "• Convert to GIF\n"
            "• Compress video (144p to 4K)\n\n"
            "*Audio Editing:*\n"
            "• Trim, speed change, volume\n"
            "• Convert format, compress\n"
            "• Reverse, merge audio\n\n"
            "*Other Features:*\n"
            "• 💻 Code Formatter (Python, JS, JSON, HTML, CSS, SQL)\n"
            "• ⚡ Custom Commands (/addcmd, /run)\n"
            "• 💰 Daily Rewards & Credits System\n"
            "• 👥 Referral Program\n\n"
            "*Commands:*\n"
            "/start - Start bot\n"
            "/daily - Claim daily reward\n"
            "/refer - Get referral link\n"
            "/credits - Check credits\n"
            "/premium - Premium info\n"
            "/feedback - Send feedback\n"
            "/customcmd <name> - Use custom command\n"
            "/addcmd - Add custom command (admin)\n"
            "/cancel - Cancel operation\n\n"
            "*Support:* @KiraFXSupport",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        stats = self.db.get_user_stats(user.id)
        is_premium = self.db.is_premium(user.id)
        is_banned, _ = self.db.is_banned(user.id)
        is_muted, _ = self.db.is_muted(user.id)
        
        await update.message.reply_text(
            f"📊 *YOUR STATISTICS* 📊\n\n"
            f"*User:* {user.first_name}\n"
            f"*ID:* `{user.id}`\n\n"
            f"*Activity:*\n"
            f"• Total Edits: `{stats.get('total_edits', 0)}`\n"
            f"• Images: `{stats.get('total_images', 0)}`\n"
            f"• Videos: `{stats.get('total_videos', 0)}`\n"
            f"• Audio: `{stats.get('total_audios', 0)}`\n\n"
            f"*Account:*\n"
            f"• Credits: `{stats.get('credits', 100)}`\n"
            f"• Premium: `{'✅' if is_premium else '❌'}`\n"
            f"• Referrals: `{stats.get('referral_count', 0)}`\n"
            f"• Member Since: `{stats.get('join_date', 'N/A')[:10] if stats.get('join_date') else 'N/A'}`\n\n"
            f"*Status:*\n"
            f"• Banned: `{'⚠️ Yes' if is_banned else '✅ No'}`\n"
            f"• Muted: `{'⚠️ Yes' if is_muted else '✅ No'}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user_id = update.effective_user.id
        if user_id in self.sessions:
            session = self.sessions[user_id]
            for f in session.temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
            del self.sessions[user_id]
        await update.message.reply_text("✅ *Operation cancelled!*", parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command"""
        user_id = update.effective_user.id
        reward, streak = self.db.claim_daily_reward(user_id)
        if reward > 0:
            await update.message.reply_text(
                f"⭐ *DAILY REWARD* ⭐\n\n"
                f"You received: `{reward} credits`\n"
                f"Current streak: `{streak} days`\n\n"
                f"Come back tomorrow for more!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ *Already claimed today!*\n\n"
                f"Current streak: `{streak} days`\n"
                f"Come back tomorrow for more!",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cmd_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refer command"""
        user_id = update.effective_user.id
        stats = self.db.get_user_stats(user_id)
        bot_username = (await self.application.bot.get_me()).username
        
        await update.message.reply_text(
            f"👥 *REFERRAL PROGRAM* 👥\n\n"
            f"*Your referral link:*\n"
            f"`https://t.me/{bot_username}?start={user_id}`\n\n"
            f"*Your stats:*\n"
            f"• Total Referrals: `{stats.get('referral_count', 0)}`\n"
            f"• Credits Earned: `{stats.get('referral_count', 0) * 50}`\n\n"
            f"*Rewards:*\n"
            f"• 50 credits per referral\n"
            f"• 100 credits for 5 referrals\n"
            f"• 1 week premium for 10 referrals",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /credits command"""
        user_id = update.effective_user.id
        credits = self.db.get_credits(user_id)
        await update.message.reply_text(
            f"💰 *YOUR CREDITS* 💰\n\n"
            f"You have `{credits}` credits.\n\n"
            f"*Ways to earn:*\n"
            f"• Daily reward: 50-200 credits\n"
            f"• Referral: 50 credits each\n"
            f"• Premium: 500 bonus credits\n"
            f"• Active usage: bonus rewards",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command"""
        user_id = update.effective_user.id
        is_premium = self.db.is_premium(user_id)
        
        if is_premium:
            stats = self.db.get_user_stats(user_id)
            await update.message.reply_text(
                "⭐ *PREMIUM ACTIVE* ⭐\n\n"
                f"*Expires:* {stats.get('premium_expires', 'N/A')[:19] if stats.get('premium_expires') else 'N/A'}\n\n"
                "*Benefits:*\n"
                "✅ Unlimited edits\n"
                "✅ Priority processing\n"
                "✅ 4K video support\n"
                "✅ Batch processing\n"
                "✅ No watermarks\n"
                "✅ Exclusive filters",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "⭐ *PREMIUM FEATURES* ⭐\n\n"
                "*Benefits:*\n"
                "• Unlimited edits\n"
                "• Priority processing\n"
                "• 4K video support\n"
                "• Batch processing\n"
                "• No watermarks\n"
                "• Exclusive filters\n\n"
                "*Price:* ₹299 for 30 days\n\n"
                "Contact @KiraFXSupport to upgrade!",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cmd_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command"""
        session = self.get_session(update.effective_user.id)
        session.state = UserState.AWAITING_FEEDBACK
        await update.message.reply_text(
            "📝 *SEND FEEDBACK* 📝\n\n"
            "Tell us what you think, suggest features, or report bugs.\n\n"
            "Type your message below (or /cancel to cancel):",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ==================== CUSTOM COMMANDS ====================
    
    async def cmd_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /customcmd and /run commands"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚡ *Custom Commands* ⚡\n\n"
                "Usage: `/run <command_name>` or `/customcmd <command_name>`\n\n"
                "Use the menu to browse available custom commands:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Browse Commands", callback_data="list_custom_cmds")
                ]])
            )
            return
        
        cmd_name = args[0].lower()
        cmd_data = self.db.get_custom_command(cmd_name)
        
        if cmd_data:
            response_type = cmd_data['response_type']
            response_content = cmd_data['response_content']
            
            if response_type == 'text':
                await update.message.reply_text(response_content, parse_mode=ParseMode.MARKDOWN)
            elif response_type == 'code':
                lang = cmd_data.get('language', 'text')
                await update.message.reply_text(f"```{lang}\n{response_content}\n```", parse_mode=ParseMode.MARKDOWN)
            elif response_type == 'photo':
                await update.message.reply_photo(response_content)
            elif response_type == 'video':
                await update.message.reply_video(response_content)
        else:
            await update.message.reply_text(
                f"❌ Command '/{cmd_name}' not found!\n\n"
                f"Use `/addcmd {cmd_name} text | Your response` to create it.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cmd_add_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addcmd command - Add custom command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "➕ *ADD CUSTOM COMMAND* ➕\n\n"
                "Usage: `/addcmd <name> <type> [language] | <content>`\n\n"
                "Types: `text`, `code`, `photo`, `video`\n\n"
                "Examples:\n"
                "• `/addcmd hello text | Hello World!`\n"
                "• `/addcmd pycode code python | print('Hello')`\n"
                "• `/addcmd welcome photo | https://example.com/image.jpg`\n\n"
                "For multi-line content, use quotes or send as separate message.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Parse command: /addcmd name type [language] | content
        full_text = ' '.join(args)
        if '|' not in full_text:
            await update.message.reply_text("❌ Use '|' to separate command info from content!", parse_mode=ParseMode.MARKDOWN)
            return
        
        parts = full_text.split('|', 1)
        cmd_parts = parts[0].strip().split()
        content = parts[1].strip()
        
        if len(cmd_parts) < 2:
            await update.message.reply_text("❌ Need command name and type!", parse_mode=ParseMode.MARKDOWN)
            return
        
        cmd_name = cmd_parts[0].lower()
        cmd_type = cmd_parts[1].lower()
        language = cmd_parts[2] if len(cmd_parts) > 2 else None
        
        if cmd_type not in ['text', 'code', 'photo', 'video']:
            await update.message.reply_text("❌ Type must be: text, code, photo, or video", parse_mode=ParseMode.MARKDOWN)
            return
        
        success, msg = self.db.add_custom_command(cmd_name, cmd_type, content, language, user_id)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    # ==================== ADMIN COMMANDS ====================
    
    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
            return
        await update.message.reply_text(
            "👑 *ADMIN PANEL* 👑\n\nSelect an option:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_admin_panel()
        )
    
    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        session = self.get_session(user_id)
        session.state = UserState.AWAITING_BROADCAST
        await update.message.reply_text(
            "📢 *BROADCAST MESSAGE* 📢\n\n"
            "Send the message to broadcast to all users.\n"
            "You can send text, photos, or videos.\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id> [reason]")
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
        
        self.db.ban_user(target_id, user_id, reason)
        await update.message.reply_text(f"✅ *User {target_id} banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        
        try:
            await context.bot.send_message(target_id, f"⛔ *You have been banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    async def cmd_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        self.db.unban_user(target_id, user_id)
        await update.message.reply_text(f"✅ *User {target_id} unbanned!*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            await context.bot.send_message(target_id, "✅ *You have been unbanned!*", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    async def cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mute command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /mute <user_id> <minutes> [reason]")
            return
        
        try:
            target_id = int(context.args[0])
            minutes = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or minutes!")
            return
        
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "No reason"
        
        self.db.mute_user(target_id, user_id, minutes, reason)
        await update.message.reply_text(f"✅ *User {target_id} muted for {minutes} minutes!*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            await context.bot.send_message(target_id, f"🔇 *You have been muted for {minutes} minutes!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    async def cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unmute command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unmute <user_id>")
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        self.db.unmute_user(target_id, user_id)
        await update.message.reply_text(f"✅ *User {target_id} unmuted!*", parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /warn command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /warn <user_id> <reason>")
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        reason = " ".join(context.args[1:])
        
        warn_count = self.db.add_warning(target_id, user_id, reason)
        await update.message.reply_text(f"⚠️ *User {target_id} warned!*\nWarnings: {warn_count}/3\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        
        if warn_count >= 3:
            self.db.ban_user(target_id, user_id, "3 warnings - auto ban")
            await update.message.reply_text(f"🚫 *User {target_id} automatically banned (3 warnings)!*", parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_clear_warns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clearwarns command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /clearwarns <user_id>")
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        self.db.clear_warnings(target_id, user_id)
        await update.message.reply_text(f"✅ *Warnings cleared for user {target_id}!*", parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_give_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /givepremium command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /givepremium <user_id> <days>")
            return
        
        try:
            target_id = int(context.args[0])
            days = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or days!")
            return
        
        self.db.give_premium(target_id, days, user_id)
        await update.message.reply_text(f"✅ *Premium granted to user {target_id} for {days} days!*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            await context.bot.send_message(target_id, f"🎉 *You have been granted premium access for {days} days!* 🎉", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    async def cmd_add_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addcredits command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
            return
        
        try:
            target_id = int(context.args[0])
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or amount!")
            return
        
        self.db.add_credits(target_id, amount, user_id)
        await update.message.reply_text(f"✅ *Added {amount} credits to user {target_id}!*", parse_mode=ParseMode.MARKDOWN)
# ==================== CALLBACK HANDLER ====================

async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    session = self.get_session(user_id)
    
    # Check if user is banned
    is_banned, ban_reason = self.db.is_banned(user_id)
    if is_banned:
        await query.edit_message_text(
            f"⛔ *You are banned from using this bot!*\nReason: {ban_reason}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if user is muted (except for basic commands)
    is_muted, muted_until = self.db.is_muted(user_id)
    if is_muted and data not in ["stats", "help", "daily_reward", "back_main"]:
        time_str = f" until {muted_until.strftime('%Y-%m-%d %H:%M')}" if muted_until else ""
        await query.edit_message_text(
            f"🔇 *You are muted{time_str}!*",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== CAPTCHA HANDLER ====================
    if data.startswith("captcha_"):
        selected = data.replace("captcha_", "")
        if selected == session.captcha_code:
            self.db.verify_user(user_id, "captcha")
            session.state = UserState.VERIFIED
            await query.edit_message_text(
                "✅ *Verification successful!*",
                parse_mode=ParseMode.MARKDOWN
            )
            await self._send_main_menu(update, query.from_user)
        else:
            session.captcha_attempts += 1
            if session.captcha_attempts >= MAX_CAPTCHA_ATTEMPTS:
                await query.edit_message_text(
                    "❌ *Verification failed!* Use /start to try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                if user_id in self.sessions:
                    del self.sessions[user_id]
            else:
                await query.edit_message_text(
                    f"❌ *Incorrect!* Attempts left: {MAX_CAPTCHA_ATTEMPTS - session.captcha_attempts}",
                    parse_mode=ParseMode.MARKDOWN
                )
        return
    
    # ==================== CODE FORMATTER ====================
    if data == "code_format":
        await query.edit_message_text(
            "💻 *CODE FORMATTER* 💻\n\n"
            "Select a language to format your code:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_code_format_menu()
        )
        return
    
    if data.startswith("format_"):
        lang = data.replace("format_", "")
        session.state = UserState.AWAITING_CODE
        session.code_language = lang if lang != "auto" else None
        lang_names = {
            "python": "Python", "js": "JavaScript", "ts": "TypeScript",
            "html": "HTML", "css": "CSS", "json": "JSON", "sql": "SQL",
            "auto": "Auto-detect"
        }
        await query.edit_message_text(
            f"📝 *Format {lang_names.get(lang, lang.title())} Code*\n\n"
            "Send your code below:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== CUSTOM COMMANDS MENU ====================
    if data == "custom_commands_menu":
        is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
        await query.edit_message_text(
            "⚡ *CUSTOM COMMANDS* ⚡\n\n"
            "Browse and use custom commands created by admins.\n\n"
            "• Use `/run <name>` to execute\n"
            "• Use `/addcmd` to create (admin only)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_custom_commands_menu(is_admin)
        )
        return
    
    if data == "list_custom_cmds":
        commands = self.db.list_custom_commands(active_only=True)
        if commands:
            text = "📋 *AVAILABLE CUSTOM COMMANDS*\n\n"
            for cmd in commands[:30]:
                text += f"• `/{cmd['command']}` - {cmd['response_type']}"
                if cmd.get('language'):
                    text += f" ({cmd['language']})"
                text += f"\n  Usage: {cmd.get('usage_count', 0)} times\n\n"
            text += "\n_Use /run <name> to execute_"
        else:
            text = "❌ No custom commands available.\n\nUse `/addcmd name type | content` to create one.\n\nExample:\n`/addcmd hello text | Hello World!`"
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "list_all_custom_cmds":
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await query.answer("Access denied!", show_alert=True)
            return
        commands = self.db.list_custom_commands(active_only=False)
        if commands:
            text = "📋 *ALL CUSTOM COMMANDS (Admin)*\n\n"
            for cmd in commands:
                status = "✅" if cmd.get('is_active') else "❌"
                text += f"{status} `/{cmd['command']}` - {cmd['response_type']}\n"
                text += f"  Created: {cmd.get('created_at', 'N/A')[:10]}\n"
                text += f"  Usage: {cmd.get('usage_count', 0)}\n\n"
        else:
            text = "No custom commands found."
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "add_custom_cmd":
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await query.answer("Access denied!", show_alert=True)
            return
        session.state = UserState.AWAITING_CUSTOM_CMD
        session.pending_effect = "add_custom_cmd"
        await query.edit_message_text(
            "➕ *ADD CUSTOM COMMAND* ➕\n\n"
            "Send in format:\n"
            "`<name> <type> [language] | <content>`\n\n"
            "Types: `text`, `code`, `photo`, `video`\n\n"
            "Examples:\n"
            "• `hello text | Hello World!`\n"
            "• `pycode code python | print('Hello')`\n"
            "• `welcome photo | https://example.com/image.jpg`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "delete_custom_cmd":
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await query.answer("Access denied!", show_alert=True)
            return
        session.state = UserState.AWAITING_CUSTOM_CMD
        session.pending_effect = "delete_custom_cmd"
        await query.edit_message_text(
            "❌ *DELETE CUSTOM COMMAND*\n\n"
            "Send the command name to delete:\n\nExample: `hello`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "toggle_custom_cmd":
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await query.answer("Access denied!", show_alert=True)
            return
        session.state = UserState.AWAITING_CUSTOM_CMD
        session.pending_effect = "toggle_custom_cmd"
        await query.edit_message_text(
            "🔧 *TOGGLE CUSTOM COMMAND*\n\n"
            "Send command name to toggle on/off:\n\nExample: `hello`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== MAIN MENU NAVIGATION ====================
    if data == "mode_image":
        session.editing_mode = EditingMode.IMAGE
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "🖼️ *Image Editing Mode*\n\n"
            "Send me an image to edit, or select an option below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_image_menu()
        )
        return
    
    if data == "mode_video":
        session.editing_mode = EditingMode.VIDEO
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "🎬 *Video Editing Mode*\n\n"
            "Send me a video to edit, or select an option below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_video_menu()
        )
        return
    
    if data == "mode_audio":
        session.editing_mode = EditingMode.AUDIO
        session.state = UserState.AWAITING_AUDIO
        await query.edit_message_text(
            "🎵 *Audio Editing Mode*\n\n"
            "Send me an audio file to edit:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_audio_menu()
        )
        return
    
    if data == "mode_gif":
        session.editing_mode = EditingMode.GIF
        session.state = UserState.AWAITING_VIDEO
        session.pending_effect = "to_gif"
        await query.edit_message_text(
            "🎞️ *GIF Creation Mode*\n\n"
            "Send me a video to convert to GIF:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "ai_enhance":
        session.pending_effect = "auto_enhance"
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "✨ *AI Auto-Enhance*\n\n"
            "Send me an image to auto-enhance:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "collage":
        session.pending_effect = "collage"
        session.batch_files = []
        session.state = UserState.AWAITING_MERGE
        await query.edit_message_text(
            "🎨 *Create Collage*\n\n"
            "Send me images (up to 4). Type 'done' when finished:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== REWARDS & STATS ====================
    if data == "daily_reward":
        reward, streak = self.db.claim_daily_reward(user_id)
        if reward > 0:
            await query.edit_message_text(
                f"⭐ *DAILY REWARD* ⭐\n\n"
                f"You received: `{reward} credits`\n"
                f"Streak: `{streak} days`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                f"❌ *Already claimed today!*\n\n"
                f"Streak: `{streak} days`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    if data == "referral":
        await self.cmd_refer(update, context)
        return
    
    if data == "stats":
        await self.cmd_stats(update, context)
        return
    
    if data == "premium":
        await self.cmd_premium(update, context)
        return
    
    if data == "help":
        await self.cmd_help(update, context)
        return
    
    if data == "feedback":
        session.state = UserState.AWAITING_FEEDBACK
        await query.edit_message_text(
            "📝 *Send Feedback*\n\n"
            "Tell us what you think:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== IMAGE EDITING ====================
    if data == "img_filters":
        await query.edit_message_text(
            "🎨 *Select a filter:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_filters_menu()
        )
        return
    
    if data.startswith("filter_"):
        filter_name = data.replace("filter_", "").replace("_", " ")
        session.pending_effect = filter_name
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            f"🎨 *Apply Filter: {filter_name.title()}*\n\n"
            "Send me an image:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_resize":
        session.pending_effect = "resize"
        session.state = UserState.AWAITING_RESIZE
        await query.edit_message_text(
            "📐 *Resize Image*\n\n"
            "Send dimensions (width height):\n"
            "Example: `1920 1080`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_rotate":
        session.pending_effect = "rotate"
        session.state = UserState.AWAITING_ROTATE
        await query.edit_message_text(
            "🔄 *Rotate Image*\n\n"
            "Send angle (0-360):\n"
            "Example: `90`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_flip_h":
        session.pending_effect = "flip_h"
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "🪞 *Flip Horizontally*\n\n"
            "Send an image:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_flip_v":
        session.pending_effect = "flip_v"
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "↕️ *Flip Vertically*\n\n"
            "Send an image:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_crop":
        session.pending_effect = "crop"
        session.state = UserState.AWAITING_CROP
        await query.edit_message_text(
            "✂️ *Crop Image*\n\n"
            "Send coordinates (left top right bottom):\n"
            "Example: `100 100 500 500`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_brightness":
        session.pending_effect = "brightness"
        session.state = UserState.AWAITING_ADJUST
        await query.edit_message_text(
            "☀️ *Adjust Brightness*\n\n"
            "Send factor (0.5-2.0):\n"
            "• 0.5 = Darker\n"
            "• 1.0 = Normal\n"
            "• 2.0 = Brighter",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_contrast":
        session.pending_effect = "contrast"
        session.state = UserState.AWAITING_ADJUST
        await query.edit_message_text(
            "🌓 *Adjust Contrast*\n\n"
            "Send factor (0.5-2.0):\n"
            "• 0.5 = Less contrast\n"
            "• 1.0 = Normal\n"
            "• 2.0 = More contrast",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_saturation":
        session.pending_effect = "saturation"
        session.state = UserState.AWAITING_ADJUST
        await query.edit_message_text(
            "🎨 *Adjust Saturation*\n\n"
            "Send factor (0.5-2.0):\n"
            "• 0.5 = Less color\n"
            "• 1.0 = Normal\n"
            "• 2.0 = More color",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_sharpness":
        session.pending_effect = "sharpness"
        session.state = UserState.AWAITING_ADJUST
        await query.edit_message_text(
            "✏️ *Adjust Sharpness*\n\n"
            "Send factor (0.5-2.0):\n"
            "• 0.5 = Softer\n"
            "• 1.0 = Normal\n"
            "• 2.0 = Sharper",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_text":
        session.pending_effect = "add_text"
        session.state = UserState.AWAITING_TEXT
        await query.edit_message_text(
            "📝 *Add Text to Image*\n\n"
            "Send the text you want to add:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_watermark":
        session.pending_effect = "add_watermark"
        session.state = UserState.AWAITING_TEXT
        await query.edit_message_text(
            "💧 *Add Watermark*\n\n"
            "Send the watermark text:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_auto":
        session.pending_effect = "auto_enhance"
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "✨ *Auto Enhance*\n\n"
            "Send an image to auto-enhance:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "img_remove_bg":
        session.pending_effect = "remove_bg"
        session.state = UserState.AWAITING_IMAGE
        await query.edit_message_text(
            "🎭 *Remove Background*\n\n"
            "Send an image to remove background:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== VIDEO EDITING ====================
    if data == "vid_trim":
        session.pending_effect = "trim"
        session.state = UserState.AWAITING_TRIM
        await query.edit_message_text(
            "✂️ *Trim Video*\n\n"
            "Send start and end times (seconds or HH:MM:SS):\n"
            "Example: `10 30` or `00:00:10 00:00:30`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_speed":
        session.pending_effect = "speed"
        session.state = UserState.AWAITING_SPEED
        await query.edit_message_text(
            "⚡ *Change Video Speed*\n\n"
            "Send speed factor:\n"
            "• 0.5 = Slow motion\n"
            "• 1.0 = Normal\n"
            "• 2.0 = Fast motion",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_audio":
        session.pending_effect = "extract_audio"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "🎵 *Extract Audio*\n\n"
            "Send a video to extract audio:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_mute":
        session.pending_effect = "mute"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "🔊 *Mute Video*\n\n"
            "Send a video to remove audio:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_resize":
        session.pending_effect = "resize_video"
        session.state = UserState.AWAITING_RESIZE
        await query.edit_message_text(
            "📐 *Resize Video*\n\n"
            "Send dimensions (width height):\n"
            "Example: `1280 720`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_rotate":
        session.pending_effect = "rotate_video"
        session.state = UserState.AWAITING_ROTATE
        await query.edit_message_text(
            "🔄 *Rotate Video*\n\n"
            "Send angle (90, 180, 270):",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_watermark":
        session.pending_effect = "video_watermark"
        session.state = UserState.AWAITING_TEXT
        await query.edit_message_text(
            "🏷️ *Add Watermark to Video*\n\n"
            "Send watermark text:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_to_gif":
        session.pending_effect = "to_gif"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "🎞️ *Convert to GIF*\n\n"
            "Send a video (first 10 seconds will be used):",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_compress":
        session.pending_effect = "compress"
        session.state = UserState.AWAITING_QUALITY
        await query.edit_message_text(
            "📦 *Compress Video*\n\n"
            "Select output quality:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_quality_menu()
        )
        return
    
    if data.startswith("quality_"):
        quality = data.replace("quality_", "")
        session.quality_preset = quality
        session.pending_effect = "compress"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            f"📦 *Compress to {VIDEO_QUALITIES[quality]['label']}*\n\n"
            f"Resolution: {VIDEO_QUALITIES[quality]['width']}x{VIDEO_QUALITIES[quality]['height']}\n"
            f"Bitrate: {VIDEO_QUALITIES[quality]['bitrate']}\n\n"
            "Send the video to compress:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_merge":
        session.pending_effect = "merge_videos"
        session.merge_files = []
        session.state = UserState.AWAITING_MERGE
        await query.edit_message_text(
            "🔗 *Merge Videos*\n\n"
            "Send videos one by one. Type 'done' when finished:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_add_audio":
        session.pending_effect = "add_audio"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "🎵 *Add Audio to Video*\n\n"
            "Send the video file first:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "vid_info":
        session.pending_effect = "video_info"
        session.state = UserState.AWAITING_VIDEO
        await query.edit_message_text(
            "ℹ️ *Video Info*\n\n"
            "Send a video to get information:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== AUDIO EDITING ====================
    if data == "aud_trim":
        session.pending_effect = "audio_trim"
        session.state = UserState.AWAITING_TRIM
        await query.edit_message_text(
            "✂️ *Trim Audio*\n\n"
            "Send start and end times (seconds):\n"
            "Example: `10 30`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_speed":
        session.pending_effect = "audio_speed"
        session.state = UserState.AWAITING_SPEED
        await query.edit_message_text(
            "⚡ *Change Audio Speed*\n\n"
            "Send speed factor (0.5-2.0):",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_volume":
        session.pending_effect = "audio_volume"
        session.state = UserState.AWAITING_ADJUST
        await query.edit_message_text(
            "🔊 *Change Volume*\n\n"
            "Send volume factor (0.5-2.0):\n"
            "• 0.5 = Half volume\n"
            "• 1.0 = Normal\n"
            "• 2.0 = Double volume",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_reverse":
        session.pending_effect = "audio_reverse"
        session.state = UserState.AWAITING_AUDIO
        await query.edit_message_text(
            "🔄 *Reverse Audio*\n\n"
            "Send an audio file to reverse:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_convert":
        session.pending_effect = "audio_convert"
        session.state = UserState.AWAITING_AUDIO
        await query.edit_message_text(
            "🎵 *Convert Audio*\n\n"
            "Send an audio file to convert:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_compress":
        session.pending_effect = "audio_compress"
        session.state = UserState.AWAITING_AUDIO
        await query.edit_message_text(
            "📦 *Compress Audio*\n\n"
            "Send an audio file to compress:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_merge":
        session.pending_effect = "merge_audios"
        session.merge_files = []
        session.state = UserState.AWAITING_MERGE
        await query.edit_message_text(
            "🔗 *Merge Audio Files*\n\n"
            "Send audio files one by one. Type 'done' when finished:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "aud_info":
        session.pending_effect = "audio_info"
        session.state = UserState.AWAITING_AUDIO
        await query.edit_message_text(
            "ℹ️ *Audio Info*\n\n"
            "Send an audio file to get information:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== ADMIN PANEL ====================
    if data == "admin_panel":
        await query.edit_message_text(
            "👑 *ADMIN PANEL* 👑\n\nSelect an option:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_admin_panel()
        )
        return
    
    if data == "admin_stats":
        stats = self.db.get_bot_stats()
        await query.edit_message_text(
            f"📊 *BOT STATISTICS* 📊\n\n"
            f"👥 Total Users: `{stats['total_users']}`\n"
            f"🟢 Active Today: `{stats['active_today']}`\n"
            f"🎨 Total Edits: `{stats['total_edits']}`\n"
            f"🖼️ Images: `{stats['total_images']}`\n"
            f"🎬 Videos: `{stats['total_videos']}`\n"
            f"🎵 Audio: `{stats['total_audios']}`\n"
            f"⭐ Premium Users: `{stats['premium_users']}`\n"
            f"🚫 Banned Users: `{stats['banned_users']}`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_users":
        users = self.db.get_all_users(limit=30)
        text = "👥 *RECENT USERS*\n\n"
        for u in users:
            premium = "⭐" if u.get('is_premium') else ""
            banned = "🚫" if u.get('is_banned') else ""
            text += f"• `{u['user_id']}` {premium}{banned} - {u.get('first_name', 'Unknown')[:20]}\n"
            text += f"  Edits: {u.get('total_edits', 0)} | Credits: {u.get('credits', 0)}\n\n"
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "admin_broadcast":
        session.state = UserState.AWAITING_BROADCAST
        await query.edit_message_text(
            "📢 *Broadcast*\n\n"
            "Send the message to broadcast to all users:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_schedule":
        session.state = UserState.AWAITING_ANNOUNCEMENT
        await query.edit_message_text(
            "📅 *Schedule Message*\n\n"
            "Send message and time (format: MM/DD HH:MM):\n"
            "Example: `12/25 10:00 Happy Holidays!`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_ban":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "ban"
        await query.edit_message_text(
            "🚫 *Ban User*\n\n"
            "Send user ID and reason:\n"
            "Example: `123456789 Spamming`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_unban":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "unban"
        await query.edit_message_text(
            "✅ *Unban User*\n\n"
            "Send user ID:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_mute":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "mute"
        await query.edit_message_text(
            "🔇 *Mute User*\n\n"
            "Send user ID and minutes:\n"
            "Example: `123456789 60`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_unmute":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "unmute"
        await query.edit_message_text(
            "🔊 *Unmute User*\n\n"
            "Send user ID:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_warn":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "warn"
        await query.edit_message_text(
            "⚠️ *Warn User*\n\n"
            "Send user ID and reason:\n"
            "Example: `123456789 Rule violation`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_warnings":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "warnings"
        await query.edit_message_text(
            "📋 *View Warnings*\n\n"
            "Send user ID:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_give_premium":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "give_premium"
        await query.edit_message_text(
            "💎 *Give Premium*\n\n"
            "Send user ID and days:\n"
            "Example: `123456789 30`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_add_credits":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "add_credits"
        await query.edit_message_text(
            "💰 *Add Credits*\n\n"
            "Send user ID and amount:\n"
            "Example: `123456789 100`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data == "admin_auto_responses":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "auto_response"
        responses = self.db.list_auto_responses()
        if responses:
            text = "📝 *AUTO RESPONSES*\n\n"
            for r in responses[:20]:
                text += f"• `{r['keyword']}` -> {r['response'][:50]}...\n"
            text += "\nCommands:\n`add keyword: response`\n`remove keyword`"
        else:
            text = "📝 *AUTO RESPONSES*\n\nNo auto responses yet.\n\nCommands:\n`add keyword: response`\n`remove keyword`"
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "admin_custom_cmds":
        if user_id not in ADMIN_IDS and user_id != OWNER_ID:
            await query.answer("Access denied!", show_alert=True)
            return
        await query.edit_message_text(
            "⚡ *CUSTOM COMMANDS ADMIN* ⚡\n\n"
            "Manage custom commands:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_custom_commands_menu(True)
        )
        return
    
    if data == "admin_feedback":
        feedbacks = self.db.get_feedback(status="pending")
        if feedbacks:
            text = "📋 *PENDING FEEDBACK*\n\n"
            for fb in feedbacks[:10]:
                text += f"• #{fb['id']} from {fb.get('first_name', 'User')}:\n"
                text += f"  {fb['feedback'][:100]}\n\n"
        else:
            text = "No pending feedback."
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "admin_logs":
        logs = self.db.get_admin_logs(30)
        text = "📜 *RECENT ADMIN LOGS*\n\n"
        for log in logs:
            text += f"• {log['created_at'][:16]} - {log.get('admin_name', log['admin_id'])}: {log['action']}\n"
        await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        return
    
    if data == "admin_export":
        csv_data = self.db.export_users_csv()
        await query.edit_message_text("📊 *Exporting data...*", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_document(
            chat_id=user_id,
            document=InputFile(io.BytesIO(csv_data.encode()), filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv"),
            caption="User data export"
        )
        return
    
    if data == "admin_reset":
        session.state = UserState.AWAITING_ADMIN
        session.pending_effect = "reset_user"
        await query.edit_message_text(
            "🔄 *Reset User*\n\n"
            "Send user ID to reset all data:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # ==================== NAVIGATION ====================
    if data == "back_image":
        await query.edit_message_text(
            "🖼️ *Image Editing Menu*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_image_menu()
        )
        return
    
    if data == "back_video":
        await query.edit_message_text(
            "🎬 *Video Editing Menu*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_video_menu()
        )
        return
    
    if data == "back_audio":
        await query.edit_message_text(
            "🎵 *Audio Editing Menu*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_audio_menu()
        )
        return
    
    if data == "back_main":
        is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
        is_premium = self.db.is_premium(user_id)
        await query.edit_message_text(
            "🎨 *Main Menu*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium)
        )
        return
  # ==================== IMAGE HANDLERS ====================

async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming image messages"""
    user_id = update.effective_user.id
    
    # Check verification
    if not self.db.is_verified(user_id):
        await update.message.reply_text("❌ Please verify first with /start")
        return
    
    # Check ban status
    is_banned, ban_reason = self.db.is_banned(user_id)
    if is_banned:
        await update.message.reply_text(f"⛔ You are banned! Reason: {ban_reason}")
        return
    
    session = self.get_session(user_id)
    
    # Check if user is in correct state
    if session.state not in [UserState.AWAITING_IMAGE, UserState.AWAITING_MERGE]:
        await update.message.reply_text(
            "Please select an option from the menu first!",
            reply_markup=KeyboardBuilder.get_image_menu()
        )
        return
    
    # Download image
    processing_msg = await update.message.reply_text("📥 *Downloading image...*", parse_mode=ParseMode.MARKDOWN)
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    temp_path = TEMP_DIR / f"img_{user_id}_{datetime.now().timestamp()}.jpg"
    
    # Download file
    file_content = await file.download_as_bytearray()
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    session.temp_files.append(str(temp_path))
    
    # Handle collage collection
    if session.state == UserState.AWAITING_MERGE and session.pending_effect == "collage":
        session.batch_files.append(str(temp_path))
        if len(session.batch_files) >= 4:
            await self._process_collage(update, context, session.batch_files, user_id)
        else:
            await processing_msg.edit_text(
                f"📸 Image {len(session.batch_files)}/4 received. Send more or type 'done' to finish."
            )
        return
    
    session.temp_file_path = str(temp_path)
    effect = session.pending_effect
    
    # Process based on effect
    if effect == "auto_enhance":
        await self._process_auto_enhance(update, context, temp_path, user_id)
    elif effect == "remove_bg":
        await self._process_remove_bg(update, context, temp_path, user_id)
    elif effect in ["flip_h", "flip_v"]:
        await self._process_flip(update, context, temp_path, user_id, effect)
    elif effect in ["brightness", "contrast", "saturation", "sharpness"]:
        session.state = UserState.AWAITING_ADJUST
        await processing_msg.edit_text(f"Send {effect} factor (0.5-2.0):")
    elif effect in ["resize", "rotate", "crop", "add_text", "add_watermark"]:
        # Already in correct state
        await processing_msg.edit_text("Ready for processing. Send the required parameters.")
    else:
        await self._apply_image_filter(update, context, temp_path, user_id, effect)

async def _apply_image_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               img_path: Path, user_id: int, filter_name: str):
    """Apply image filter"""
    processing_msg = await update.message.reply_text("🎨 *Applying filter...*", parse_mode=ParseMode.MARKDOWN)
    
    try:
        img = Image.open(img_path)
        processed = self.image_processor.apply_filter(img, filter_name)
        
        output_path = TEMP_DIR / f"output_{user_id}_{datetime.now().timestamp()}.jpg"
        processed.save(output_path, quality=90)
        
        # Check file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption=f"✅ *Filter applied: {filter_name.title()}!*\n📦 Size: {file_size:.1f}MB",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_image_menu()
            )
        
        # Record edit
        self.db.add_edit_record(user_id, "image", filter_name)
        self.db.add_credits(user_id, 1)  # Reward 1 credit per edit
        
        os.remove(output_path)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(img_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_auto_enhance(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 img_path: Path, user_id: int):
    """Process auto enhance"""
    processing_msg = await update.message.reply_text("✨ *AI Auto-Enhancing...*", parse_mode=ParseMode.MARKDOWN)
    try:
        img = Image.open(img_path)
        enhanced = self.image_processor.auto_enhance(img)
        output_path = TEMP_DIR / f"enhanced_{user_id}_{datetime.now().timestamp()}.jpg"
        enhanced.save(output_path, quality=90)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ *Image auto-enhanced!*",
                reply_markup=KeyboardBuilder.get_image_menu()
            )
        
        self.db.add_edit_record(user_id, "image", "auto_enhance")
        self.db.add_credits(user_id, 2)
        os.remove(output_path)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(img_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_remove_bg(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              img_path: Path, user_id: int):
    """Process background removal"""
    processing_msg = await update.message.reply_text("🎭 *Removing background...*", parse_mode=ParseMode.MARKDOWN)
    try:
        img = Image.open(img_path)
        processed = self.image_processor.remove_background(img)
        output_path = TEMP_DIR / f"nobg_{user_id}_{datetime.now().timestamp()}.png"
        processed.save(output_path, "PNG")
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ *Background removed!*",
                reply_markup=KeyboardBuilder.get_image_menu()
            )
        
        self.db.add_edit_record(user_id, "image", "remove_bg")
        self.db.add_credits(user_id, 5)
        os.remove(output_path)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(img_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                        img_path: Path, user_id: int, flip_type: str):
    """Process image flip"""
    processing_msg = await update.message.reply_text("🪞 *Flipping image...*", parse_mode=ParseMode.MARKDOWN)
    try:
        img = Image.open(img_path)
        if flip_type == "flip_h":
            flipped = self.image_processor.flip_horizontal(img)
            flip_name = "Horizontal"
        else:
            flipped = self.image_processor.flip_vertical(img)
            flip_name = "Vertical"
        
        output_path = TEMP_DIR / f"flipped_{user_id}_{datetime.now().timestamp()}.jpg"
        flipped.save(output_path, quality=90)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption=f"✅ *{flip_name} flip applied!*",
                reply_markup=KeyboardBuilder.get_image_menu()
            )
        
        self.db.add_edit_record(user_id, "image", f"flip_{flip_type}")
        os.remove(output_path)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(img_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_collage(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                            image_paths: List[str], user_id: int):
    """Process collage creation"""
    processing_msg = await update.message.reply_text("🎨 *Creating collage...*", parse_mode=ParseMode.MARKDOWN)
    try:
        images = [Image.open(path) for path in image_paths]
        collage = self.image_processor.create_collage(images, layout='grid')
        output_path = TEMP_DIR / f"collage_{user_id}_{datetime.now().timestamp()}.jpg"
        collage.save(output_path, quality=90)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption=f"✅ *Collage created from {len(images)} images!*",
                reply_markup=KeyboardBuilder.get_image_menu()
            )
        
        self.db.add_edit_record(user_id, "image", "collage")
        self.db.add_credits(user_id, 3)
        os.remove(output_path)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        for path in image_paths:
            try:
                os.remove(path)
            except:
                pass
        session = self.get_session(user_id)
        session.batch_files = []
        session.pending_effect = None
        session.state = UserState.VERIFIED

# ==================== VIDEO HANDLERS ====================

async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video messages"""
    user_id = update.effective_user.id
    
    if not self.db.is_verified(user_id):
        await update.message.reply_text("❌ Please verify first with /start")
        return
    
    is_banned, _ = self.db.is_banned(user_id)
    if is_banned:
        await update.message.reply_text("⛔ You are banned from using this bot!")
        return
    
    session = self.get_session(user_id)
    
    if session.state not in [UserState.AWAITING_VIDEO, UserState.AWAITING_MERGE]:
        await update.message.reply_text(
            "Please select a video editing option first!",
            reply_markup=KeyboardBuilder.get_video_menu()
        )
        return
    
    video = update.message.video
    if video.file_size > MAX_VIDEO_SIZE:
        await update.message.reply_text(f"❌ Video too large! Max size: {MAX_VIDEO_SIZE // (1024*1024)}MB")
        return
    
    processing_msg = await update.message.reply_text("📥 *Downloading video...*", parse_mode=ParseMode.MARKDOWN)
    
    file = await context.bot.get_file(video.file_id)
    temp_path = TEMP_DIR / f"video_{user_id}_{datetime.now().timestamp()}.mp4"
    
    file_content = await file.download_as_bytearray()
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    session.temp_files.append(str(temp_path))
    
    # Handle merge collection
    if session.state == UserState.AWAITING_MERGE and session.pending_effect == "merge_videos":
        session.merge_files.append(str(temp_path))
        await processing_msg.edit_text(
            f"📹 Video {len(session.merge_files)} received. Send more or type 'done' to finish."
        )
        return
    
    session.temp_file_path = str(temp_path)
    effect = session.pending_effect
    
    if effect == "extract_audio":
        await self._process_extract_audio(update, context, temp_path, user_id)
    elif effect == "mute":
        await self._process_mute_video(update, context, temp_path, user_id)
    elif effect == "to_gif":
        await self._process_video_to_gif(update, context, temp_path, user_id)
    elif effect == "video_info":
        await self._process_video_info(update, context, temp_path, user_id)
    elif effect == "compress":
        quality = session.quality_preset or "720p"
        await self._process_compress_video(update, context, temp_path, user_id, quality)
    elif effect == "add_audio":
        session.pending_effect = "add_audio_wait"
        session.state = UserState.AWAITING_AUDIO
        await processing_msg.edit_text("🎵 *Video received! Now send the audio file:*", parse_mode=ParseMode.MARKDOWN)
    elif effect in ["trim", "speed", "resize_video", "rotate_video"]:
        # Already in correct state
        await processing_msg.edit_text("Ready for processing. Send the required parameters.")
    elif effect == "video_watermark":
        session.state = UserState.AWAITING_TEXT
        await processing_msg.edit_text("🏷️ *Video received! Now send the watermark text:*", parse_mode=ParseMode.MARKDOWN)
    else:
        await processing_msg.edit_text("Ready for processing. Send the required parameters.")

async def _process_extract_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  video_path: Path, user_id: int):
    """Extract audio from video"""
    processing_msg = await update.message.reply_text("🎵 *Extracting audio...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"audio_{user_id}_{datetime.now().timestamp()}.mp3"
        success, result = self.video_processor.extract_audio(str(video_path), str(output_path))
        
        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            with open(output_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=InputFile(f),
                    caption=f"✅ *Audio extracted!*\n📦 Size: {file_size:.1f}MB",
                    reply_markup=KeyboardBuilder.get_video_menu()
                )
            self.db.add_edit_record(user_id, "audio", "extract")
            self.db.add_credits(user_id, 2)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(video_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_mute_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               video_path: Path, user_id: int):
    """Mute video"""
    processing_msg = await update.message.reply_text("🔊 *Muting video...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"muted_{user_id}_{datetime.now().timestamp()}.mp4"
        success, result = self.video_processor.mute(str(video_path), str(output_path))
        
        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=InputFile(f),
                    caption=f"✅ *Video muted!*\n📦 Size: {file_size:.1f}MB",
                    reply_markup=KeyboardBuilder.get_video_menu()
                )
            self.db.add_edit_record(user_id, "video", "mute")
            self.db.add_credits(user_id, 2)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(video_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_video_to_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 video_path: Path, user_id: int):
    """Convert video to GIF"""
    processing_msg = await update.message.reply_text("🎞️ *Converting to GIF...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"output_{user_id}_{datetime.now().timestamp()}.gif"
        success, result = self.video_processor.to_gif(str(video_path), 0, 10, str(output_path))
        
        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f, filename="output.gif"),
                    caption=f"✅ *GIF created!*\n📦 Size: {file_size:.1f}MB",
                    reply_markup=KeyboardBuilder.get_video_menu()
                )
            self.db.add_edit_record(user_id, "video", "to_gif")
            self.db.add_credits(user_id, 3)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(video_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_video_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               video_path: Path, user_id: int):
    """Get video information"""
    try:
        info = self.video_processor.get_video_info(str(video_path))
        if 'error' in info:
            await update.message.reply_text(f"❌ *Error:* {info['error']}", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(
                f"ℹ️ *VIDEO INFO* ℹ️\n\n"
                f"• Duration: `{info.get('duration', 0)} seconds`\n"
                f"• Resolution: `{info.get('width', 0)}x{info.get('height', 0)}`\n"
                f"• FPS: `{info.get('fps', 0)}`\n"
                f"• Size: `{info.get('size_mb', 0)} MB`\n"
                f"• Audio: `{'Yes' if info.get('has_audio', False) else 'No'}`\n"
                f"• Aspect Ratio: `{info.get('aspect_ratio', 0)}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_video_menu()
            )
    except Exception as e:
        await update.message.reply_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(video_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_compress_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   video_path: Path, user_id: int, quality: str):
    """Compress video to specified quality"""
    processing_msg = await update.message.reply_text(
        f"📦 *Compressing video to {VIDEO_QUALITIES[quality]['label']}...*\n_This may take a few minutes._",
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        output_path = TEMP_DIR / f"compressed_{user_id}_{datetime.now().timestamp()}.mp4"
        start_time = time.time()
        success, result = self.video_processor.compress(str(video_path), str(output_path), quality)
        processing_time = time.time() - start_time
        
        if success:
            original_size = os.path.getsize(video_path) / (1024 * 1024)
            compressed_size = os.path.getsize(output_path) / (1024 * 1024)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=InputFile(f),
                    caption=f"✅ *Video compressed to {VIDEO_QUALITIES[quality]['label']}!*\n"
                            f"📦 Original: `{original_size:.1f}MB` → Compressed: `{compressed_size:.1f}MB`\n"
                            f"📉 Saved: `{compression_ratio:.1f}%`\n"
                            f"⏱️ Time: `{processing_time:.1f}s`",
                    reply_markup=KeyboardBuilder.get_video_menu()
                )
            self.db.add_edit_record(user_id, "video", f"compress_{quality}", processing_time=processing_time)
            self.db.add_credits(user_id, 5)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Compression failed:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(video_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.quality_preset = None
        session.state = UserState.VERIFIED

# ==================== AUDIO HANDLERS ====================

async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming audio messages"""
    user_id = update.effective_user.id
    
    if not self.db.is_verified(user_id):
        await update.message.reply_text("❌ Please verify first with /start")
        return
    
    is_banned, _ = self.db.is_banned(user_id)
    if is_banned:
        await update.message.reply_text("⛔ You are banned from using this bot!")
        return
    
    session = self.get_session(user_id)
    
    audio = update.message.audio or update.message.voice
    if not audio:
        return
    
    processing_msg = await update.message.reply_text("📥 *Downloading audio...*", parse_mode=ParseMode.MARKDOWN)
    
    file = await context.bot.get_file(audio.file_id)
    temp_path = TEMP_DIR / f"audio_{user_id}_{datetime.now().timestamp()}.mp3"
    
    file_content = await file.download_as_bytearray()
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    session.temp_files.append(str(temp_path))
    
    # Handle merge collection
    if session.state == UserState.AWAITING_MERGE and session.pending_effect == "merge_audios":
        session.merge_files.append(str(temp_path))
        await processing_msg.edit_text(
            f"🎵 Audio {len(session.merge_files)} received. Send more or type 'done' to finish."
        )
        return
    
    # Handle add audio to video
    if session.pending_effect == "add_audio_wait":
        video_path = session.temp_file_path
        if video_path and os.path.exists(video_path):
            await self._process_add_audio(update, context, Path(video_path), temp_path, user_id)
        else:
            await processing_msg.edit_text("❌ Video file not found. Please try again.")
        return
    
    session.temp_file_path = str(temp_path)
    effect = session.pending_effect
    
    if effect == "audio_info":
        await self._process_audio_info(update, context, temp_path, user_id)
    elif effect == "audio_reverse":
        await self._process_audio_reverse(update, context, temp_path, user_id)
    elif effect == "audio_convert":
        await self._process_audio_convert(update, context, temp_path, user_id)
    elif effect == "audio_compress":
        await self._process_audio_compress(update, context, temp_path, user_id)
    elif effect in ["audio_trim", "audio_speed", "audio_volume"]:
        await processing_msg.edit_text("Ready for processing. Send the required parameters.")
    else:
        await processing_msg.edit_text("Ready for processing. Send the required parameters.")

async def _process_audio_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               audio_path: Path, user_id: int):
    """Get audio information"""
    try:
        info = self.audio_processor.get_audio_info(str(audio_path))
        if 'error' in info:
            await update.message.reply_text(f"❌ *Error:* {info['error']}", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(
                f"ℹ️ *AUDIO INFO* ℹ️\n\n"
                f"• Duration: `{info.get('duration', 0)} seconds`\n"
                f"• Channels: `{info.get('channels', 0)}`\n"
                f"• Sample Rate: `{info.get('frame_rate', 0)} Hz`\n"
                f"• Size: `{info.get('size_mb', 0)} MB`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_audio_menu()
            )
    except Exception as e:
        await update.message.reply_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(audio_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_audio_reverse(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  audio_path: Path, user_id: int):
    """Reverse audio"""
    processing_msg = await update.message.reply_text("🔄 *Reversing audio...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"reversed_{user_id}_{datetime.now().timestamp()}.mp3"
        success, result = self.audio_processor.reverse_audio(str(audio_path), str(output_path))
        
        if success:
            with open(output_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=InputFile(f),
                    caption="✅ *Audio reversed!*",
                    reply_markup=KeyboardBuilder.get_audio_menu()
                )
            self.db.add_edit_record(user_id, "audio", "reverse")
            self.db.add_credits(user_id, 2)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(audio_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_audio_convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  audio_path: Path, user_id: int):
    """Convert audio format"""
    processing_msg = await update.message.reply_text("🎵 *Converting audio...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"converted_{user_id}_{datetime.now().timestamp()}.mp3"
        success, result = self.audio_processor.convert_format(str(audio_path), str(output_path), 'mp3')
        
        if success:
            with open(output_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=InputFile(f),
                    caption="✅ *Audio converted to MP3!*",
                    reply_markup=KeyboardBuilder.get_audio_menu()
                )
            self.db.add_edit_record(user_id, "audio", "convert")
            self.db.add_credits(user_id, 2)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(audio_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED

async def _process_audio_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   audio_path: Path, user_id: int):
    """Compress audio"""
    processing_msg = await update.message.reply_text("📦 *Compressing audio...*", parse_mode=ParseMode.MARKDOWN)
    try:
        output_path = TEMP_DIR / f"compressed_audio_{user_id}_{datetime.now().timestamp()}.mp3"
        success, result = self.audio_processor.compress_audio(str(audio_path), str(output_path), 'medium')
        
        if success:
            original_size = os.path.getsize(audio_path) / (1024 * 1024)
            compressed_size = os.path.getsize(output_path) / (1024 * 1024)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=InputFile(f),
                    caption=f"✅ *Audio compressed!*\n📦 Original: {original_size:.1f}MB → Compressed: {compressed_size:.1f}MB",
                    reply_markup=KeyboardBuilder.get_audio_menu()
                )
            self.db.add_edit_record(user_id, "audio", "compress")
            self.db.add_credits(user_id, 3)
            os.remove(output_path)
        else:
            await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
    finally:
        try:
            os.remove(audio_path)
        except:
            pass
        session = self.get_session(user_id)
        session.pending_effect = None
        session.state = UserState.VERIFIED
    # ==================== DOCUMENT HANDLER ====================
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages (for code formatting)"""
        user_id = update.effective_user.id
        
        if not self.db.is_verified(user_id):
            await update.message.reply_text("❌ Please verify first with /start")
            return
        
        session = self.get_session(user_id)
        
        if session.state == UserState.AWAITING_CODE:
            document = update.message.document
            if document and document.file_name:
                # Detect language from file extension
                ext = document.file_name.split('.')[-1].lower() if '.' in document.file_name else ''
                lang_map = {
                    'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                    'html': 'html', 'htm': 'html', 'css': 'css',
                    'json': 'json', 'sql': 'sql', 'txt': 'text',
                    'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
                    'rs': 'rust', 'rb': 'ruby', 'php': 'php', 'swift': 'swift'
                }
                lang = lang_map.get(ext, 'text')
                
                processing_msg = await update.message.reply_text("📥 *Downloading file...*", parse_mode=ParseMode.MARKDOWN)
                
                file = await context.bot.get_file(document.file_id)
                temp_path = TEMP_DIR / f"code_{user_id}_{datetime.now().timestamp()}.txt"
                
                file_content = await file.download_as_bytearray()
                with open(temp_path, 'wb') as f:
                    f.write(file_content)
                
                with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                await self._process_code_format(update, context, code, lang, user_id)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
            else:
                await update.message.reply_text("❌ Please send a valid code file.")
            return
        
        await update.message.reply_text("📄 *Document received!*\n\nUse /code to format code files.", parse_mode=ParseMode.MARKDOWN)
    
    # ==================== TEXT HANDLER ====================
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        text = update.message.text.strip()
        
        # Check rate limit
        if not self._check_rate_limit(user_id):
            await update.message.reply_text(
                "⚠️ *Rate limit exceeded!* Please wait a moment.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Update last active
        session.last_active = datetime.now()
        
        # Check for auto responses (only in verified state)
        if session.state == UserState.VERIFIED:
            auto_response = self.db.get_auto_response(text)
            if auto_response:
                if auto_response['media_type'] == 'text':
                    await update.message.reply_text(auto_response['response'], parse_mode=ParseMode.MARKDOWN)
                elif auto_response['media_type'] == 'photo' and auto_response['media_id']:
                    await update.message.reply_photo(auto_response['media_id'], caption=auto_response['response'])
                elif auto_response['media_type'] == 'video' and auto_response['media_id']:
                    await update.message.reply_video(auto_response['media_id'], caption=auto_response['response'])
                return
        
        # ==================== CODE FORMATTING ====================
        if session.state == UserState.AWAITING_CODE:
            lang = session.code_language
            await self._process_code_format(update, context, text, lang, user_id)
            return
        
        # ==================== CUSTOM COMMAND MANAGEMENT ====================
        if session.state == UserState.AWAITING_CUSTOM_CMD:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
                session.state = UserState.VERIFIED
                return
            
            if session.pending_effect == "add_custom_cmd":
                await self._process_add_custom_command(update, context, text, user_id)
            elif session.pending_effect == "delete_custom_cmd":
                success, msg = self.db.delete_custom_command(text.lower(), user_id)
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            elif session.pending_effect == "toggle_custom_cmd":
                cmd = self.db.get_custom_command(text.lower())
                if cmd:
                    new_state = not cmd.get('is_active', True)
                    success, msg = self.db.toggle_custom_command(text.lower(), new_state, user_id)
                    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text(f"❌ Command '/{text}' not found!", parse_mode=ParseMode.MARKDOWN)
            
            session.state = UserState.VERIFIED
            session.pending_effect = None
            return
        
        # ==================== FEEDBACK ====================
        if session.state == UserState.AWAITING_FEEDBACK:
            self.db.save_feedback(user_id, text)
            await update.message.reply_text(
                "✅ *Thank you for your feedback!*\n\n"
                "Your feedback helps us improve the bot.",
                parse_mode=ParseMode.MARKDOWN
            )
            session.state = UserState.VERIFIED
            return
        
        # ==================== BROADCAST ====================
        if session.state == UserState.AWAITING_BROADCAST:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                return
            
            users = self.db.get_all_users(limit=10000)
            success = 0
            failed = 0
            processing_msg = await update.message.reply_text("📢 *Broadcasting...*", parse_mode=ParseMode.MARKDOWN)
            
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=f"📢 *ANNOUNCEMENT*\n\n{text}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success += 1
                    await asyncio.sleep(0.05)  # Avoid hitting rate limits
                except Exception as e:
                    failed += 1
            
            self.db.add_broadcast_record(user_id, text, len(users), success, failed)
            await processing_msg.edit_text(
                f"✅ *Broadcast sent!*\n\n"
                f"📊 Successful: `{success}`\n"
                f"❌ Failed: `{failed}`",
                parse_mode=ParseMode.MARKDOWN
            )
            session.state = UserState.VERIFIED
            return
        
        # ==================== SCHEDULED ANNOUNCEMENT ====================
        if session.state == UserState.AWAITING_ANNOUNCEMENT:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                return
            
            try:
                parts = text.split(" ", 2)
                if len(parts) >= 3:
                    date_time = parts[0] + " " + parts[1]
                    message = parts[2]
                    schedule_time = datetime.strptime(f"{datetime.now().year} {date_time}", "%Y %m/%d %H:%M")
                    
                    if schedule_time > datetime.now():
                        self.db.add_scheduled_message(message, schedule_time, user_id)
                        await update.message.reply_text(
                            f"✅ *Message scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M')}!*",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Schedule time must be in the future!",
                            parse_mode=ParseMode.MARKDOWN
                        )
                else:
                    await update.message.reply_text(
                        "❌ Invalid format! Use: `MM/DD HH:MM Your message`",
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)
            
            session.state = UserState.VERIFIED
            return
        
        # ==================== ADMIN ACTIONS ====================
        if session.state == UserState.AWAITING_ADMIN:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                return
            
            if session.pending_effect == "ban":
                parts = text.split(maxsplit=1)
                if len(parts) >= 1:
                    try:
                        target_id = int(parts[0])
                        reason = parts[1] if len(parts) > 1 else "No reason"
                        self.db.ban_user(target_id, user_id, reason)
                        await update.message.reply_text(
                            f"✅ *User {target_id} banned!*\nReason: {reason}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        try:
                            await context.bot.send_message(
                                target_id,
                                f"⛔ *You have been banned!*\nReason: {reason}",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "unban":
                try:
                    target_id = int(text.strip())
                    self.db.unban_user(target_id, user_id)
                    await update.message.reply_text(
                        f"✅ *User {target_id} unbanned!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    try:
                        await context.bot.send_message(
                            target_id,
                            "✅ *You have been unbanned!*",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "mute":
                parts = text.split()
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        minutes = int(parts[1])
                        reason = " ".join(parts[2:]) if len(parts) > 2 else "No reason"
                        self.db.mute_user(target_id, user_id, minutes, reason)
                        await update.message.reply_text(
                            f"✅ *User {target_id} muted for {minutes} minutes!*",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        try:
                            await context.bot.send_message(
                                target_id,
                                f"🔇 *You have been muted for {minutes} minutes!*\nReason: {reason}",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or minutes!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "unmute":
                try:
                    target_id = int(text.strip())
                    self.db.unmute_user(target_id, user_id)
                    await update.message.reply_text(
                        f"✅ *User {target_id} unmuted!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "warn":
                parts = text.split(maxsplit=1)
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        reason = parts[1]
                        warn_count = self.db.add_warning(target_id, user_id, reason)
                        await update.message.reply_text(
                            f"⚠️ *User {target_id} warned!*\nWarnings: {warn_count}/3\nReason: {reason}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        if warn_count >= 3:
                            self.db.ban_user(target_id, user_id, "3 warnings - auto ban")
                            await update.message.reply_text(
                                f"🚫 *User {target_id} automatically banned (3 warnings)!*",
                                parse_mode=ParseMode.MARKDOWN
                            )
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "warnings":
                try:
                    target_id = int(text.strip())
                    warnings = self.db.get_warnings(target_id)
                    if warnings:
                        warn_text = f"⚠️ *WARNINGS FOR USER {target_id}* ⚠️\n\n"
                        for w in warnings:
                            warn_text += f"• {w['created_at'][:16]} - {w.get('admin_name', w['warned_by'])}: {w['reason']}\n"
                        await update.message.reply_text(warn_text[:4000], parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text(f"✅ User {target_id} has no warnings!", parse_mode=ParseMode.MARKDOWN)
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "give_premium":
                parts = text.split()
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        days = int(parts[1])
                        self.db.give_premium(target_id, days, user_id)
                        await update.message.reply_text(
                            f"✅ *Premium granted to {target_id} for {days} days!*",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        try:
                            await context.bot.send_message(
                                target_id,
                                f"🎉 *You have been granted premium access for {days} days!* 🎉",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or days!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "add_credits":
                parts = text.split()
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        amount = int(parts[1])
                        self.db.add_credits(target_id, amount, user_id)
                        await update.message.reply_text(
                            f"✅ *Added {amount} credits to {target_id}!*",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or amount!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "reset_user":
                try:
                    target_id = int(text.strip())
                    with self.db.get_connection() as conn:
                        conn.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM verification WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM edit_history WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM warnings WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM daily_rewards WHERE user_id = ?", (target_id,))
                    await update.message.reply_text(
                        f"✅ *User {target_id} data reset!*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            
            elif session.pending_effect == "auto_response":
                if text.startswith("add "):
                    parts = text[4:].split(": ", 1)
                    if len(parts) == 2:
                        keyword, response = parts
                        self.db.add_auto_response(keyword, response, user_id)
                        await update.message.reply_text(
                            f"✅ *Auto response added!*\nKeyword: `{keyword}`",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Invalid format! Use: `add keyword: response`",
                            parse_mode=ParseMode.MARKDOWN
                        )
                elif text.startswith("remove "):
                    keyword = text[7:].strip()
                    self.db.remove_auto_response(keyword, user_id)
                    await update.message.reply_text(
                        f"✅ *Auto response removed!*\nKeyword: `{keyword}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text(
                        "❌ Invalid format! Use:\n`add keyword: response`\n`remove keyword`",
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            session.state = UserState.VERIFIED
            session.pending_effect = None
            return
        
        # ==================== IMAGE EDITING PARAMETERS ====================
        
        # Resize image
        if session.state == UserState.AWAITING_RESIZE:
            try:
                parts = text.split()
                if len(parts) == 2:
                    width, height = int(parts[0]), int(parts[1])
                    img_path = session.temp_file_path
                    if img_path and os.path.exists(img_path):
                        await self._process_resize(update, context, Path(img_path), user_id, width, height)
                    else:
                        await update.message.reply_text("❌ No image found. Please try again.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `width height`", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid dimensions!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Rotate image
        if session.state == UserState.AWAITING_ROTATE:
            try:
                angle = int(text)
                img_path = session.temp_file_path
                if img_path and os.path.exists(img_path):
                    await self._process_rotate(update, context, Path(img_path), user_id, angle)
                else:
                    await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid angle! (0-360)", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Crop image
        if session.state == UserState.AWAITING_CROP:
            try:
                parts = text.split()
                if len(parts) == 4:
                    left, top, right, bottom = map(int, parts)
                    img_path = session.temp_file_path
                    if img_path and os.path.exists(img_path):
                        await self._process_crop(update, context, Path(img_path), user_id, left, top, right, bottom)
                    else:
                        await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `left top right bottom`", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid coordinates!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Color adjustments
        if session.state == UserState.AWAITING_ADJUST:
            try:
                factor = float(text)
                if factor < 0.1 or factor > 3.0:
                    await update.message.reply_text("❌ Factor must be between 0.1 and 3.0", parse_mode=ParseMode.MARKDOWN)
                    return
                img_path = session.temp_file_path
                if img_path and os.path.exists(img_path):
                    await self._process_color_adjust(update, context, Path(img_path), user_id, session.pending_effect, factor)
                else:
                    await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Add text to image
        if session.state == UserState.AWAITING_TEXT:
            img_path = session.temp_file_path
            if img_path and os.path.exists(img_path):
                if session.pending_effect == "add_text":
                    await self._process_add_text(update, context, Path(img_path), user_id, text)
                elif session.pending_effect == "add_watermark":
                    await self._process_add_watermark(update, context, Path(img_path), user_id, text)
                elif session.pending_effect == "video_watermark":
                    video_path = Path(img_path)
                    await self._process_video_watermark(update, context, video_path, user_id, text)
            else:
                await update.message.reply_text("❌ No file found.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # ==================== VIDEO EDITING PARAMETERS ====================
        
        # Trim video
        if session.state == UserState.AWAITING_TRIM:
            try:
                parts = text.split()
                if len(parts) == 2:
                    start = self.video_processor._parse_time(parts[0])
                    end = self.video_processor._parse_time(parts[1])
                    video_path = session.temp_file_path
                    if video_path and os.path.exists(video_path):
                        await self._process_trim_video(update, context, Path(video_path), user_id, start, end)
                    else:
                        await update.message.reply_text("❌ No video found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `start end`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Change video speed
        if session.state == UserState.AWAITING_SPEED:
            try:
                factor = float(text)
                if factor < 0.1 or factor > 10:
                    await update.message.reply_text("❌ Factor must be between 0.1 and 10", parse_mode=ParseMode.MARKDOWN)
                    return
                video_path = session.temp_file_path
                if video_path and os.path.exists(video_path):
                    await self._process_speed_video(update, context, Path(video_path), user_id, factor)
                else:
                    await update.message.reply_text("❌ No video found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # ==================== AUDIO EDITING PARAMETERS ====================
        
        # Trim audio
        if session.state == UserState.AWAITING_TRIM and session.pending_effect == "audio_trim":
            try:
                parts = text.split()
                if len(parts) == 2:
                    start = float(parts[0])
                    end = float(parts[1])
                    audio_path = session.temp_file_path
                    if audio_path and os.path.exists(audio_path):
                        await self._process_trim_audio(update, context, Path(audio_path), user_id, start, end)
                    else:
                        await update.message.reply_text("❌ No audio found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `start end`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Change audio speed
        if session.state == UserState.AWAITING_SPEED and session.pending_effect == "audio_speed":
            try:
                factor = float(text)
                if factor < 0.5 or factor > 2.0:
                    await update.message.reply_text("❌ Factor must be between 0.5 and 2.0", parse_mode=ParseMode.MARKDOWN)
                    return
                audio_path = session.temp_file_path
                if audio_path and os.path.exists(audio_path):
                    await self._process_speed_audio(update, context, Path(audio_path), user_id, factor)
                else:
                    await update.message.reply_text("❌ No audio found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Change audio volume
        if session.state == UserState.AWAITING_ADJUST and session.pending_effect == "audio_volume":
            try:
                factor = float(text)
                if factor < 0.5 or factor > 2.0:
                    await update.message.reply_text("❌ Factor must be between 0.5 and 2.0", parse_mode=ParseMode.MARKDOWN)
                    return
                audio_path = session.temp_file_path
                if audio_path and os.path.exists(audio_path):
                    await self._process_volume_audio(update, context, Path(audio_path), user_id, factor)
                else:
                    await update.message.reply_text("❌ No audio found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # ==================== MERGE OPERATIONS ====================
        
        # Handle merge/collage completion
        if session.state == UserState.AWAITING_MERGE:
            if text.lower() == 'done':
                if session.pending_effect == "merge_videos":
                    if len(session.merge_files) >= 2:
                        await self._process_merge_videos(update, context, session.merge_files, user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 videos to merge!", parse_mode=ParseMode.MARKDOWN)
                elif session.pending_effect == "merge_audios":
                    if len(session.merge_files) >= 2:
                        await self._process_merge_audios(update, context, session.merge_files, user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 audio files to merge!", parse_mode=ParseMode.MARKDOWN)
                elif session.pending_effect == "collage":
                    if len(session.batch_files) >= 2:
                        await self._process_collage(update, context, session.batch_files, user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 images for collage!", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Send files or type 'done' to finish.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # ==================== CAPTCHA ====================
        if session.state == UserState.AWAITING_CAPTCHA:
            if text == session.captcha_code:
                self.db.verify_user(user_id, "captcha")
                session.state = UserState.VERIFIED
                await update.message.reply_text("✅ *Verification successful!*", parse_mode=ParseMode.MARKDOWN)
                await self._send_main_menu(update, update.effective_user)
            else:
                session.captcha_attempts += 1
                if session.captcha_attempts >= MAX_CAPTCHA_ATTEMPTS:
                    await update.message.reply_text(
                        "❌ *Verification failed!* Use /start to try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    if user_id in self.sessions:
                        del self.sessions[user_id]
                else:
                    await update.message.reply_text(
                        f"❌ *Incorrect!* Attempts left: {MAX_CAPTCHA_ATTEMPTS - session.captcha_attempts}",
                        parse_mode=ParseMode.MARKDOWN
                    )
            return
        
        # Default response for unknown commands
        await update.message.reply_text(
            "❓ *Unknown command or input*\n\n"
            "Use /help to see available commands, or /start to begin.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ==================== ADDITIONAL PROCESSING METHODS ====================
    
    async def _process_code_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     code: str, language: str, user_id: int):
        """Process code formatting"""
        processing_msg = await update.message.reply_text("💻 *Formatting code...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            formatted, detected_lang, success = self.code_formatter.format_code(code, language)
            
            if success:
                lang_display = detected_lang or language or 'text'
                response = f"✅ *Code formatted!* ({lang_display})\n\n```{lang_display}\n{formatted[:3500]}\n```"
                if len(formatted) > 3500:
                    response += "\n\n_Code truncated due to length._"
            else:
                lang_display = detected_lang or language or 'text'
                response = f"⚠️ *Could not auto-format (formatter not available)*\n\n```{lang_display}\n{formatted[:3500]}\n```"
            
            await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
            self.db.add_edit_record(user_id, "code", "format")
            self.db.add_credits(user_id, 1)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error formatting code:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
            session.code_language = None
    
    async def _process_add_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           text: str, user_id: int):
        """Process adding a custom command"""
        # Parse: name type [language] | content
        parts = text.split('|', 1)
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ Invalid format! Use: `name type [language] | content`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        cmd_parts = parts[0].strip().split()
        content = parts[1].strip()
        
        if len(cmd_parts) < 2:
            await update.message.reply_text(
                "❌ Need command name and type!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        cmd_name = cmd_parts[0].lower()
        cmd_type = cmd_parts[1].lower()
        language = cmd_parts[2] if len(cmd_parts) > 2 else None
        
        if cmd_type not in ['text', 'code', 'photo', 'video']:
            await update.message.reply_text(
                "❌ Type must be: text, code, photo, or video",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        success, msg = self.db.add_custom_command(cmd_name, cmd_type, content, language, user_id)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    async def _process_resize(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               img_path: Path, user_id: int, width: int, height: int):
        """Process image resize"""
        processing_msg = await update.message.reply_text("📐 *Resizing...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            resized = self.image_processor.resize(img, width, height)
            output_path = TEMP_DIR / f"resized_{user_id}_{datetime.now().timestamp()}.jpg"
            resized.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=f"✅ *Resized to {width}x{height}!*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", "resize")
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               img_path: Path, user_id: int, angle: int):
        """Process image rotate"""
        processing_msg = await update.message.reply_text("🔄 *Rotating...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            rotated = self.image_processor.rotate(img, angle)
            output_path = TEMP_DIR / f"rotated_{user_id}_{datetime.now().timestamp()}.jpg"
            rotated.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=f"✅ *Rotated {angle}°!*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", "rotate")
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             img_path: Path, user_id: int, left: int, top: int, right: int, bottom: int):
        """Process image crop"""
        processing_msg = await update.message.reply_text("✂️ *Cropping...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            cropped = self.image_processor.crop(img, left, top, right, bottom)
            output_path = TEMP_DIR / f"cropped_{user_id}_{datetime.now().timestamp()}.jpg"
            cropped.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption="✅ *Cropped!*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", "crop")
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_color_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     img_path: Path, user_id: int, adjustment: str, factor: float):
        """Process color adjustment"""
        processing_msg = await update.message.reply_text(f"🎨 *Adjusting {adjustment}...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            if adjustment == "brightness":
                adjusted = self.image_processor.adjust_brightness(img, factor)
            elif adjustment == "contrast":
                adjusted = self.image_processor.adjust_contrast(img, factor)
            elif adjustment == "saturation":
                adjusted = self.image_processor.adjust_saturation(img, factor)
            elif adjustment == "sharpness":
                adjusted = self.image_processor.adjust_sharpness(img, factor)
            else:
                adjusted = img
            
            output_path = TEMP_DIR / f"adjusted_{user_id}_{datetime.now().timestamp()}.jpg"
            adjusted.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=f"✅ *{adjustment.title()} adjusted to {factor}!*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", adjustment)
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_add_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 img_path: Path, user_id: int, text: str):
        """Process adding text to image"""
        processing_msg = await update.message.reply_text("📝 *Adding text...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            position = (img.width // 2 - 100, img.height - 50)
            with_text = self.image_processor.add_text(img, text, position[0], position[1], 40)
            output_path = TEMP_DIR / f"text_{user_id}_{datetime.now().timestamp()}.jpg"
            with_text.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=f"✅ *Text added: \"{text[:30]}\"*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", "add_text")
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_add_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      img_path: Path, user_id: int, text: str):
        """Process adding watermark to image"""
        processing_msg = await update.message.reply_text("💧 *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            watermarked = self.image_processor.add_watermark(img, text)
            output_path = TEMP_DIR / f"watermarked_{user_id}_{datetime.now().timestamp()}.jpg"
            watermarked.save(output_path, quality=90)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption="✅ *Watermark added!*",
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", "watermark")
            self.db.add_credits(user_id, 1)
            os.remove(output_path)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(img_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_trim_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   video_path: Path, user_id: int, start: float, end: float):
        """Process video trim"""
        processing_msg = await update.message.reply_text("✂️ *Trimming video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"trimmed_{user_id}_{datetime.now().timestamp()}.mp4"
            start_time = time.time()
            success, result = self.video_processor.trim(str(video_path), start, end, str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Trimmed from {start}s to {end}s!*\n📦 Size: {file_size:.1f}MB\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                self.db.add_edit_record(user_id, "video", "trim", processing_time=processing_time)
                self.db.add_credits(user_id, 2)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(video_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_speed_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    video_path: Path, user_id: int, factor: float):
        """Process video speed change"""
        processing_msg = await update.message.reply_text(f"⚡ *Changing speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"speed_{user_id}_{datetime.now().timestamp()}.mp4"
            start_time = time.time()
            success, result = self.video_processor.change_speed(str(video_path), factor, str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Speed changed to {factor}x!*\n📦 Size: {file_size:.1f}MB\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                self.db.add_edit_record(user_id, "video", f"speed_{factor}", processing_time=processing_time)
                self.db.add_credits(user_id, 2)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(video_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_merge_videos(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     video_paths: List[str], user_id: int):
        """Process video merge"""
        processing_msg = await update.message.reply_text("🔗 *Merging videos...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"merged_{user_id}_{datetime.now().timestamp()}.mp4"
            start_time = time.time()
            success, result = self.video_processor.merge_videos(video_paths, str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Merged {len(video_paths)} videos!*\n📦 Size: {file_size:.1f}MB\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                self.db.add_edit_record(user_id, "video", "merge", processing_time=processing_time)
                self.db.add_credits(user_id, 5)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            for path in video_paths:
                try:
                    os.remove(path)
                except:
                    pass
            session = self.get_session(user_id)
            session.merge_files = []
            session.state = UserState.VERIFIED
    
    async def _process_video_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        video_path: Path, user_id: int, text: str):
        """Process video watermark"""
        processing_msg = await update.message.reply_text("🏷️ *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"watermarked_{user_id}_{datetime.now().timestamp()}.mp4"
            start_time = time.time()
            success, result = self.video_processor.add_watermark(str(video_path), text, str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Watermark added!*\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                self.db.add_edit_record(user_id, "video", "watermark", processing_time=processing_time)
                self.db.add_credits(user_id, 2)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(video_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_add_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  video_path: Path, audio_path: Path, user_id: int):
        """Add audio to video"""
        processing_msg = await update.message.reply_text("🎵 *Adding audio to video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"with_audio_{user_id}_{datetime.now().timestamp()}.mp4"
            start_time = time.time()
            success, result = self.video_processor.add_audio(str(video_path), str(audio_path), str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Audio added to video!*\n📦 Size: {file_size:.1f}MB\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                self.db.add_edit_record(user_id, "video", "add_audio", processing_time=processing_time)
                self.db.add_credits(user_id, 3)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(video_path)
                os.remove(audio_path)
            except:
                pass
            session = self.get_session(user_id)
            session.pending_effect = None
            session.state = UserState.VERIFIED
    
    async def _process_trim_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   audio_path: Path, user_id: int, start: float, end: float):
        """Process audio trim"""
        processing_msg = await update.message.reply_text("✂️ *Trimming audio...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"trimmed_audio_{user_id}_{datetime.now().timestamp()}.mp3"
            success, result = self.audio_processor.trim_audio(str(audio_path), start, end, str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=InputFile(f),
                        caption=f"✅ *Audio trimmed from {start}s to {end}s!*",
                        reply_markup=KeyboardBuilder.get_audio_menu()
                    )
                self.db.add_edit_record(user_id, "audio", "trim")
                self.db.add_credits(user_id, 2)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(audio_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_speed_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    audio_path: Path, user_id: int, factor: float):
        """Process audio speed change"""
        processing_msg = await update.message.reply_text(f"⚡ *Changing audio speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"speed_audio_{user_id}_{datetime.now().timestamp()}.mp3"
            success, result = self.audio_processor.change_speed(str(audio_path), factor, str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=InputFile(f),
                        caption=f"✅ *Audio speed changed to {factor}x!*",
                        reply_markup=KeyboardBuilder.get_audio_menu()
                    )
                self.db.add_edit_record(user_id, "audio", f"speed_{factor}")
                self.db.add_credits(user_id, 2)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(audio_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_volume_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     audio_path: Path, user_id: int, factor: float):
        """Process audio volume change"""
        processing_msg = await update.message.reply_text(f"🔊 *Changing volume to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"volume_audio_{user_id}_{datetime.now().timestamp()}.mp3"
            success, result = self.audio_processor.change_volume(str(audio_path), factor, str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=InputFile(f),
                        caption=f"✅ *Volume changed to {factor}x!*",
                        reply_markup=KeyboardBuilder.get_audio_menu()
                    )
                self.db.add_edit_record(user_id, "audio", f"volume_{factor}")
                self.db.add_credits(user_id, 1)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            try:
                os.remove(audio_path)
            except:
                pass
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
    
    async def _process_merge_audios(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     audio_paths: List[str], user_id: int):
        """Process audio merge"""
        processing_msg = await update.message.reply_text("🔗 *Merging audio files...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"merged_audio_{user_id}_{datetime.now().timestamp()}.mp3"
            start_time = time.time()
            success, result = self.audio_processor.merge_audios(audio_paths, str(output_path))
            processing_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=InputFile(f),
                        caption=f"✅ *Merged {len(audio_paths)} audio files!*\n📦 Size: {file_size:.1f}MB\n⏱️ Time: {processing_time:.1f}s",
                        reply_markup=KeyboardBuilder.get_audio_menu()
                    )
                self.db.add_edit_record(user_id, "audio", "merge", processing_time=processing_time)
                self.db.add_credits(user_id, 3)
                os.remove(output_path)
            else:
                await processing_msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            for path in audio_paths:
                try:
                    os.remove(path)
                except:
                    pass
            session = self.get_session(user_id)
            session.merge_files = []
            session.state = UserState.VERIFIED


# ==================== MAIN ENTRY POINT ====================

async def main():
    """Main entry point for the bot"""
    bot = KinvaMasterBot()
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
