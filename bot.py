#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KINVA MASTER PRO ULTIMATE - Complete Telegram Bot
Version: 6.1.0 - FIXED & ENHANCED
Features: 100+ Editing Options, 30+ Admin Features, Custom Commands, Code Formatter
"""

import os
import re
import asyncio
import logging
import tempfile
import shutil
import math
import json
import sqlite3
import hashlib
import secrets
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict
import string
import random
import time
import traceback
from io import BytesIO

# Telegram
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputFile, BotCommand, BotCommandScopeDefault, User,
    Chat, ChatMember, InputMediaPhoto, InputMediaVideo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler,
    ApplicationBuilder
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Image Processing
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
import numpy as np
import cv2
from scipy import ndimage
from scipy.ndimage import convolve, gaussian_filter
from skimage import exposure, filters as skfilters, morphology, color, restoration
from skimage.util import random_noise
from skimage.transform import rotate as skrotate, resize as skresize

# Video Processing
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    TextClip, concatenate_videoclips, concatenate_audioclips, vfx, afx,
    ImageSequenceClip, clips_array, ColorClip
)
from moviepy.video.fx import resize, rotate, crop, fadein, fadeout
from moviepy.audio.fx import audio_loop, audio_fadein, audio_fadeout

# Audio Processing
from pydub import AudioSegment
import librosa
import soundfile as sf

# Utilities
import requests
from aiohttp import ClientSession
import aiofiles

# Web Server
from flask import Flask, request, jsonify, render_template_string

# Check if Flask is available
try:
    from flask import Flask, request, jsonify, render_template_string
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    logger.warning("Flask not installed. Webhook mode disabled.")

# ==================== Configuration ====================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "8525952693").split(",") if id]
OWNER_ID = int(os.environ.get("OWNER_ID", 8525952693))
if OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(OWNER_ID)

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://KINVA-MASTER-1.onrender.com")
USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8080))

DATABASE_PATH = os.environ.get("DATABASE_PATH", "kinva_master.db")
MAX_VIDEO_SIZE = 100 * 1024 * 1024
MAX_IMAGE_SIZE = 30 * 1024 * 1024
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

CAPTCHA_TIMEOUT = 180
MAX_CAPTCHA_ATTEMPTS = 3
PROCESSING_TIMEOUT = 600
RATE_LIMIT_SECONDS = 2

PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN", "")
PREMIUM_PRICE = [{"label": "Premium - 30 Days", "amount": 29900}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== Enums ====================

class UserState(Enum):
    AWAITING_CAPTCHA = "awaiting_captcha"
    AWAITING_IMAGE = "awaiting_image"
    AWAITING_VIDEO = "awaiting_video"
    AWAITING_AUDIO = "awaiting_audio"
    AWAITING_CROP_COORDS = "awaiting_crop_coords"
    AWAITING_TRIM_TIMES = "awaiting_trim_times"
    AWAITING_SPEED_FACTOR = "awaiting_speed_factor"
    AWAITING_TEXT_CONTENT = "awaiting_text_content"
    AWAITING_MERGE_FILES = "awaiting_merge_files"
    AWAITING_RESIZE_DIMS = "awaiting_resize_dims"
    AWAITING_ROTATE_ANGLE = "awaiting_rotate_angle"
    AWAITING_COLOR_ADJUST = "awaiting_color_adjust"
    AWAITING_ADMIN_ACTION = "awaiting_admin_action"
    AWAITING_FEEDBACK = "awaiting_feedback"
    AWAITING_BROADCAST = "awaiting_broadcast"
    AWAITING_ANNOUNCEMENT = "awaiting_announcement"
    AWAITING_BAN_REASON = "awaiting_ban_reason"
    AWAITING_WARN_REASON = "awaiting_warn_reason"
    AWAITING_MUTE_DURATION = "awaiting_mute_duration"
    AWAITING_CREDITS_AMOUNT = "awaiting_credits_amount"
    AWAITING_CUSTOM_COMMAND = "awaiting_custom_command"
    AWAITING_CODE_INPUT = "awaiting_code_input"
    VERIFIED = "verified"

class EditingMode(Enum):
    NONE = "none"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    GIF = "gif"

class UserRole(Enum):
    USER = "user"
    PREMIUM = "premium"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"

# ==================== Data Classes ====================

@dataclass
class UserSession:
    user_id: int
    state: UserState = UserState.AWAITING_CAPTCHA
    editing_mode: EditingMode = EditingMode.NONE
    temp_file_path: Optional[str] = None
    original_file_id: Optional[str] = None
    message_id: Optional[int] = None
    captcha_code: Optional[str] = None
    captcha_attempts: int = 0
    captcha_start_time: Optional[datetime] = None
    merge_files: List[str] = field(default_factory=list)
    pending_effect: Optional[str] = None
    last_command_time: datetime = field(default_factory=datetime.now)
    command_count: int = 0
    preferred_quality: int = 90
    auto_save: bool = True
    batch_files: List[str] = field(default_factory=list)
    code_language: Optional[str] = None

@dataclass
class WarnRecord:
    user_id: int
    warned_by: int
    reason: str
    timestamp: datetime

# ==================== Database Manager ====================

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
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
                credits INTEGER DEFAULT 100,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferred_language TEXT DEFAULT 'en',
                preferred_resolution TEXT DEFAULT '1080p',
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0
            )''')
            
            # Verification table
            conn.execute('''CREATE TABLE IF NOT EXISTS verification (
                user_id INTEGER PRIMARY KEY,
                is_verified BOOLEAN DEFAULT 0,
                verified_at TIMESTAMP,
                verification_method TEXT
            )''')
            
            # Edit history
            conn.execute('''CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                edit_type TEXT,
                filter_used TEXT,
                processing_time REAL,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Feedback table
            conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_text TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'pending',
                admin_response TEXT,
                responded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Admin logs
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
                message_type TEXT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Daily rewards table
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER PRIMARY KEY,
                last_claim_date TEXT,
                streak INTEGER DEFAULT 0
            )''')
            
            # Auto responses table
            conn.execute('''CREATE TABLE IF NOT EXISTS auto_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE,
                response TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Scheduled messages table
            conn.execute('''CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Custom commands table - NEW FEATURE
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

    # ========== Custom Commands Methods (NEW FEATURE) ==========
    def add_custom_command(self, command: str, response_type: str, response_content: str, language: str, created_by: int) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute('''INSERT OR REPLACE INTO custom_commands 
                    (command, response_type, response_content, language, created_by)
                    VALUES (?, ?, ?, ?, ?)''', 
                    (command.lower(), response_type, response_content, language, created_by))
                return True
        except Exception as e:
            logger.error(f"Error adding custom command: {e}")
            return False
    
    def get_custom_command(self, command: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            result = conn.execute('''SELECT * FROM custom_commands 
                WHERE command = ? AND is_active = 1''', (command.lower(),)).fetchone()
            if result:
                conn.execute('UPDATE custom_commands SET usage_count = usage_count + 1 WHERE command = ?', (command.lower(),))
            return dict(result) if result else None
    
    def list_custom_commands(self) -> List[Dict]:
        with self.get_connection() as conn:
            commands = conn.execute('''SELECT * FROM custom_commands 
                WHERE is_active = 1 ORDER BY created_at DESC''').fetchall()
            return [dict(c) for c in commands]
    
    def delete_custom_command(self, command: str) -> bool:
        with self.get_connection() as conn:
            result = conn.execute('DELETE FROM custom_commands WHERE command = ?', (command.lower(),))
            return result.rowcount > 0
    
    def toggle_custom_command(self, command: str, is_active: bool) -> bool:
        with self.get_connection() as conn:
            result = conn.execute('UPDATE custom_commands SET is_active = ? WHERE command = ?', 
                                 (1 if is_active else 0, command.lower()))
            return result.rowcount > 0

    # User Management
    def register_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None, referred_by: int = None):
        with self.get_connection() as conn:
            existing = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            
            if not existing:
                conn.execute('''INSERT INTO users 
                    (user_id, username, first_name, last_name, last_active, referred_by)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)''',
                    (user_id, username, first_name, last_name, referred_by))
                
                if referred_by:
                    conn.execute('UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?', (referred_by,))
                    conn.execute('INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)', (referred_by, user_id))
                    conn.execute('UPDATE users SET credits = credits + 50 WHERE user_id = ?', (referred_by,))
            else:
                conn.execute('''UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?''', (username, first_name, last_name, user_id))
    
    def get_user_role(self, user_id: int) -> str:
        with self.get_connection() as conn:
            result = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result["role"] if result else "user"
    
    def set_user_role(self, user_id: int, role: str):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
    
    def is_banned(self, user_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_banned, ban_reason FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if result and result["is_banned"]:
                return True, result["ban_reason"] or "No reason provided"
            return False, ""
    
    def ban_user(self, user_id: int, admin_id: int, reason: str = None):
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_banned = 1, ban_reason = ?, banned_at = CURRENT_TIMESTAMP
                WHERE user_id = ?''', (reason, user_id))
            self.log_admin_action(admin_id, "ban_user", user_id, reason)
    
    def unban_user(self, user_id: int, admin_id: int):
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_banned = 0, ban_reason = NULL, banned_at = NULL
                WHERE user_id = ?''', (user_id,))
            self.log_admin_action(admin_id, "unban_user", user_id)
    
    def is_muted(self, user_id: int) -> Tuple[bool, Optional[datetime]]:
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
                conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
            return False, None
    
    def mute_user(self, user_id: int, admin_id: int, duration_minutes: int, reason: str = None):
        muted_until = datetime.now() + timedelta(minutes=duration_minutes)
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_muted = 1, muted_until = ?
                WHERE user_id = ?''', (muted_until.isoformat(), user_id))
            self.log_admin_action(admin_id, "mute_user", user_id, f"{duration_minutes} min: {reason}")
    
    def unmute_user(self, user_id: int, admin_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
            self.log_admin_action(admin_id, "unmute_user", user_id)
    
    def add_warning(self, user_id: int, admin_id: int, reason: str) -> int:
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO warnings (user_id, warned_by, reason)
                VALUES (?, ?, ?)''', (user_id, admin_id, reason))
            conn.execute('UPDATE users SET warn_count = warn_count + 1 WHERE user_id = ?', (user_id,))
            result = conn.execute("SELECT warn_count FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result["warn_count"] if result else 0
    
    def clear_warnings(self, user_id: int, admin_id: int):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))
            conn.execute("UPDATE users SET warn_count = 0 WHERE user_id = ?", (user_id,))
            self.log_admin_action(admin_id, "clear_warnings", user_id)
    
    def get_warnings(self, user_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            warnings = conn.execute('''SELECT w.*, u.username as admin_name 
                FROM warnings w
                LEFT JOIN users u ON w.warned_by = u.user_id
                WHERE w.user_id = ? ORDER BY w.created_at DESC''', (user_id,)).fetchall()
            return [dict(w) for w in warnings]
    
    def verify_user(self, user_id: int, method: str = "captcha"):
        with self.get_connection() as conn:
            conn.execute('''INSERT OR REPLACE INTO verification (user_id, is_verified, verified_at, verification_method)
                VALUES (?, 1, CURRENT_TIMESTAMP, ?)''', (user_id, method))
    
    def is_verified(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            result = conn.execute("SELECT is_verified FROM verification WHERE user_id = ?", (user_id,)).fetchone()
            return result["is_verified"] == 1 if result else False
    
    # Credits System
    def add_credits(self, user_id: int, amount: int, admin_id: int = None):
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (amount, user_id))
            if admin_id:
                self.log_admin_action(admin_id, "add_credits", user_id, f"+{amount}")
    
    def deduct_credits(self, user_id: int, amount: int) -> bool:
        with self.get_connection() as conn:
            result = conn.execute('''UPDATE users 
                SET credits = credits - ? 
                WHERE user_id = ? AND credits >= ?''', (amount, user_id, amount))
            return result.rowcount > 0
    
    def get_credits(self, user_id: int) -> int:
        with self.get_connection() as conn:
            result = conn.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result["credits"] if result else 0
    
    # Premium Management
    def give_premium(self, user_id: int, days: int, admin_id: int = None):
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_premium = 1, 
                    premium_expires = datetime('now', '+' || ? || ' days')
                WHERE user_id = ?''', (days, user_id))
            if admin_id:
                self.log_admin_action(admin_id, "give_premium", user_id, f"{days} days")
    
    def remove_premium(self, user_id: int, admin_id: int = None):
        with self.get_connection() as conn:
            conn.execute('''UPDATE users 
                SET is_premium = 0, premium_expires = NULL
                WHERE user_id = ?''', (user_id,))
            if admin_id:
                self.log_admin_action(admin_id, "remove_premium", user_id)
    
    def is_premium(self, user_id: int) -> bool:
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
                    conn.execute("UPDATE users SET is_premium = 0, premium_expires = NULL WHERE user_id = ?", (user_id,))
            return False
    
    # Daily Reward
    def claim_daily_reward(self, user_id: int) -> Tuple[int, int]:
        today = datetime.now().date().isoformat()
        with self.get_connection() as conn:
            result = conn.execute("SELECT last_claim_date, streak FROM daily_rewards WHERE user_id = ?", (user_id,)).fetchone()
            
            if result and result["last_claim_date"] == today:
                return 0, result["streak"]
            
            if result and result["last_claim_date"] == (datetime.now().date() - timedelta(days=1)).isoformat():
                streak = result["streak"] + 1
            else:
                streak = 1
            
            reward = min(50 + (streak - 1) * 5, 200)
            conn.execute('''INSERT OR REPLACE INTO daily_rewards (user_id, last_claim_date, streak)
                VALUES (?, ?, ?)''', (user_id, today, streak))
            conn.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (reward, user_id))
            
            return reward, streak
    
    # Edit Recording
    def add_edit_record(self, user_id: int, edit_type: str, 
                        filter_used: str = None, processing_time: float = 0,
                        file_size: int = 0):
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO edit_history (user_id, edit_type, filter_used, processing_time, file_size)
                VALUES (?, ?, ?, ?, ?)''', (user_id, edit_type, filter_used, processing_time, file_size))
            conn.execute('''UPDATE users 
                SET total_edits = total_edits + 1,
                    total_images = total_images + CASE WHEN ? = 'image' THEN 1 ELSE 0 END,
                    total_videos = total_videos + CASE WHEN ? = 'video' THEN 1 ELSE 0 END,
                    total_audios = total_audios + CASE WHEN ? = 'audio' THEN 1 ELSE 0 END,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?''', (edit_type, edit_type, edit_type, user_id))
    
    # Feedback
    def save_feedback(self, user_id: int, feedback: str, rating: int = None):
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO feedback (user_id, feedback_text, rating)
                VALUES (?, ?, ?)''', (user_id, feedback, rating))
    
    def respond_to_feedback(self, feedback_id: int, response: str, admin_id: int):
        with self.get_connection() as conn:
            conn.execute('''UPDATE feedback 
                SET status = 'responded', admin_response = ?, responded_at = CURRENT_TIMESTAMP
                WHERE id = ?''', (response, feedback_id))
            self.log_admin_action(admin_id, "respond_feedback", None, f"Feedback #{feedback_id}")
    
    def get_pending_feedback(self) -> List[Dict]:
        with self.get_connection() as conn:
            feedback = conn.execute('''SELECT f.*, u.username, u.first_name 
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.user_id
                WHERE f.status = 'pending'
                ORDER BY f.created_at DESC''').fetchall()
            return [dict(f) for f in feedback]
    
    # Auto Responses
    def add_auto_response(self, keyword: str, response: str, admin_id: int):
        with self.get_connection() as conn:
            conn.execute('''INSERT OR REPLACE INTO auto_responses (keyword, response, created_by)
                VALUES (?, ?, ?)''', (keyword.lower(), response, admin_id))
            self.log_admin_action(admin_id, "add_auto_response", None, keyword)
    
    def remove_auto_response(self, keyword: str, admin_id: int):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM auto_responses WHERE keyword = ?", (keyword.lower(),))
            self.log_admin_action(admin_id, "remove_auto_response", None, keyword)
    
    def get_auto_response(self, text: str) -> Optional[str]:
        with self.get_connection() as conn:
            for keyword, response in conn.execute("SELECT keyword, response FROM auto_responses").fetchall():
                if keyword.lower() in text.lower():
                    return response
            return None
    
    # Statistics
    def get_user_stats(self, user_id: int) -> Dict:
        with self.get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(user) if user else {}
    
    def get_bot_stats(self) -> Dict:
        with self.get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_today = conn.execute("SELECT COUNT(*) FROM users WHERE date(last_active) = date('now')").fetchone()[0]
            total_edits = conn.execute("SELECT SUM(total_edits) FROM users").fetchone()[0] or 0
            premium_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1").fetchone()[0]
            banned_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "total_edits": total_edits,
                "premium_users": premium_users,
                "banned_users": banned_users
            }
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        with self.get_connection() as conn:
            users = conn.execute('''SELECT user_id, username, first_name, last_name, role,
                total_edits, total_images, total_videos, credits, is_premium, is_banned,
                join_date, last_active, referral_count
                FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?''', (limit, offset)).fetchall()
            return [dict(user) for user in users]
    
    def export_users_csv(self) -> str:
        users = self.get_all_users(limit=10000)
        output = io.StringIO()
        if users:
            writer = csv.DictWriter(output, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
        return output.getvalue()
    
    # Admin Logs
    def log_admin_action(self, admin_id: int, action: str, target_user: int = None, details: str = None, ip: str = None):
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO admin_logs (admin_id, action, target_user, details, ip_address)
                VALUES (?, ?, ?, ?, ?)''', (admin_id, action, target_user, details, ip))
    
    def get_admin_logs(self, limit: int = 100) -> List[Dict]:
        with self.get_connection() as conn:
            logs = conn.execute('''SELECT al.*, u.username as admin_name
                FROM admin_logs al
                LEFT JOIN users u ON al.admin_id = u.user_id
                ORDER BY al.created_at DESC LIMIT ?''', (limit,)).fetchall()
            return [dict(log) for log in logs]
    
    # Broadcast
    def add_broadcast_record(self, admin_id: int, message: str, message_type: str, recipients: int, successful: int, failed: int):
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO broadcasts (admin_id, message, message_type, recipients, successful, failed)
                VALUES (?, ?, ?, ?, ?, ?)''', (admin_id, message, message_type, recipients, successful, failed))
    
    def get_broadcast_history(self, limit: int = 50) -> List[Dict]:
        with self.get_connection() as conn:
            broadcasts = conn.execute('''SELECT b.*, u.username as admin_name
                FROM broadcasts b
                LEFT JOIN users u ON b.admin_id = u.user_id
                ORDER BY b.created_at DESC LIMIT ?''', (limit,)).fetchall()
            return [dict(b) for b in broadcasts]
    
    # Scheduled Messages
    def add_scheduled_message(self, message: str, schedule_time: datetime, admin_id: int):
        with self.get_connection() as conn:
            conn.execute('''INSERT INTO scheduled_messages (message, scheduled_time, created_by)
                VALUES (?, ?, ?)''', (message, schedule_time.isoformat(), admin_id))
            self.log_admin_action(admin_id, "schedule_message", None, message[:50])
    
    def get_pending_scheduled_messages(self) -> List[Dict]:
        with self.get_connection() as conn:
            messages = conn.execute('''SELECT * FROM scheduled_messages 
                WHERE status = 'pending' AND scheduled_time <= datetime('now')
                ORDER BY scheduled_time ASC''').fetchall()
            return [dict(m) for m in messages]
    
    def mark_scheduled_sent(self, message_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE scheduled_messages SET status = 'sent' WHERE id = ?", (message_id,))

# ==================== Code Formatter (NEW FEATURE) ====================

class CodeFormatter:
    """Format and beautify code in various languages"""
    
    @staticmethod
    def format_python(code: str) -> Tuple[str, bool]:
        """Format Python code"""
        try:
            import autopep8
            formatted = autopep8.fix_code(code, options={'aggressive': 2})
            return formatted, True
        except ImportError:
            try:
                import black
                formatted = black.format_str(code, mode=black.Mode())
                return formatted, True
            except ImportError:
                return code, False
    
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
        """Auto-detect code language"""
        code_lower = code.lower().strip()
        
        if code_lower.startswith('<?php'):
            return 'php'
        elif '<html' in code_lower or '<!doctype' in code_lower:
            return 'html'
        elif code_lower.startswith('select') or code_lower.startswith('insert') or code_lower.startswith('update'):
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
        if not language:
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

# ==================== Advanced Image Processor ====================

class AdvancedImageProcessor:
    """Professional image processing with 100+ editing options"""
    
    @staticmethod
    def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
        """Apply any filter from 50+ options"""
        
        filters_map = {
            "blur": lambda img: img.filter(ImageFilter.BLUR),
            "contour": lambda img: img.filter(ImageFilter.CONTOUR),
            "detail": lambda img: img.filter(ImageFilter.DETAIL),
            "edge_enhance": lambda img: img.filter(ImageFilter.EDGE_ENHANCE),
            "emboss": lambda img: img.filter(ImageFilter.EMBOSS),
            "sharpen": lambda img: img.filter(ImageFilter.SHARPEN),
            "smooth": lambda img: img.filter(ImageFilter.SMOOTH),
            "smooth_more": lambda img: img.filter(ImageFilter.SMOOTH_MORE),
            "find_edges": lambda img: img.filter(ImageFilter.FIND_EDGES),
            "grayscale": lambda img: ImageOps.grayscale(img),
            "negative": lambda img: ImageOps.invert(img.convert('RGB')),
            "sepia": AdvancedImageProcessor._sepia,
            "vintage": AdvancedImageProcessor._vintage,
            "warm": AdvancedImageProcessor._warm,
            "cool": AdvancedImageProcessor._cool,
            "dramatic": AdvancedImageProcessor._dramatic,
            "cinematic": AdvancedImageProcessor._cinematic,
            "teal_orange": AdvancedImageProcessor._teal_orange,
            "sunset": AdvancedImageProcessor._sunset,
            "golden_hour": AdvancedImageProcessor._golden_hour,
            "moody": AdvancedImageProcessor._moody,
            "pastel": AdvancedImageProcessor._pastel,
            "neon": AdvancedImageProcessor._neon,
            "oil_paint": lambda img: AdvancedImageProcessor._oil_paint(img, 5),
            "watercolor": AdvancedImageProcessor._watercolor,
            "pencil_sketch": AdvancedImageProcessor._pencil_sketch,
            "cartoon": AdvancedImageProcessor._cartoon,
            "glitch": AdvancedImageProcessor._glitch,
            "vhs": AdvancedImageProcessor._vhs,
            "pixelate": lambda img: AdvancedImageProcessor._pixelate(img, 10),
            "mosaic": lambda img: AdvancedImageProcessor._mosaic(img, 20),
            "glow": AdvancedImageProcessor._glow,
            "noise": lambda img: AdvancedImageProcessor._add_noise(img, 25),
            "vignette": AdvancedImageProcessor._vignette,
            "bokeh": AdvancedImageProcessor._bokeh,
            "halftone": AdvancedImageProcessor._halftone,
            "color_splash": lambda img: AdvancedImageProcessor._color_splash(img, "red"),
            "sobel": AdvancedImageProcessor._sobel_edge,
            "canny": AdvancedImageProcessor._canny_edge,
            "laplacian": AdvancedImageProcessor._laplacian,
            "fisheye": AdvancedImageProcessor._fisheye,
            "tilt_shift": AdvancedImageProcessor._tilt_shift,
            "infrared": AdvancedImageProcessor._infrared,
            "thermal": AdvancedImageProcessor._thermal,
            "xray": AdvancedImageProcessor._xray,
            "dream": AdvancedImageProcessor._dream,
            "fire": AdvancedImageProcessor._fire,
            "ice": AdvancedImageProcessor._ice,
        }
        
        func = filters_map.get(filter_name, lambda img: img)
        return func(image)
    
    @staticmethod
    def _sepia(image: Image.Image) -> Image.Image:
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
        image = AdvancedImageProcessor._sepia(image)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        return image
    
    @staticmethod
    def _warm(image: Image.Image) -> Image.Image:
        r, g, b = image.split()
        r = r.point(lambda i: min(255, int(i * 1.2)))
        b = b.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _cool(image: Image.Image) -> Image.Image:
        r, g, b = image.split()
        b = b.point(lambda i: min(255, int(i * 1.2)))
        r = r.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _dramatic(image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)
        return image
    
    @staticmethod
    def _cinematic(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = (img_array - 127.5) * 1.2 + 127.5
        img_array = np.clip(img_array, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _teal_orange(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = img_array[:, :, 0] * 0.8 + 50
        img_array[:, :, 2] = img_array[:, :, 2] * 0.9 + 30
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _sunset(image: Image.Image) -> Image.Image:
        r, g, b = image.split()
        r = r.point(lambda i: min(255, int(i * 1.3)))
        g = g.point(lambda i: int(i * 0.9))
        b = b.point(lambda i: int(i * 0.8))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _golden_hour(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.4, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.2, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.7, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _moody(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = img_array * 0.8
        img_array[:, :, 1] = img_array[:, :, 1] * 0.7
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _pastel(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array = img_array * 0.7 + 76
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _neon(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB'))
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.8, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.5, 0, 255)
        neon = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return Image.fromarray(neon)
    
    @staticmethod
    def _oil_paint(image: Image.Image, radius: int = 5) -> Image.Image:
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
        image = image.filter(ImageFilter.SMOOTH_MORE)
        image = image.filter(ImageFilter.EDGE_ENHANCE)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        return image
    
    @staticmethod
    def _pencil_sketch(image: Image.Image) -> Image.Image:
        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        blurred = inverted.filter(ImageFilter.GaussianBlur(21))
        sketch = Image.blend(gray, blurred, 0.5)
        return sketch
    
    @staticmethod
    def _cartoon(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB'))
        smooth = cv2.bilateralFilter(img_array, 9, 75, 75)
        edges = cv2.Canny(img_array, 100, 200)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        cartoon = cv2.bitwise_and(smooth, edges)
        return Image.fromarray(cartoon)
    
    @staticmethod
    def _glitch(image: Image.Image) -> Image.Image:
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
        img_array = np.array(image.convert('RGB'))
        height, width = img_array.shape[:2]
        
        for y in range(0, height, 2):
            img_array[y:y+1, :] = img_array[y:y+1, :] * 0.7
        
        img_array[:, :, 0] = np.roll(img_array[:, :, 0], 3, axis=1)
        img_array[:, :, 2] = np.roll(img_array[:, :, 2], -3, axis=1)
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _pixelate(image: Image.Image, pixel_size: int = 10) -> Image.Image:
        small = image.resize((image.width // pixel_size, image.height // pixel_size), Image.NEAREST)
        return small.resize(image.size, Image.NEAREST)
    
    @staticmethod
    def _mosaic(image: Image.Image, block_size: int = 20) -> Image.Image:
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
    def _glow(image: Image.Image) -> Image.Image:
        blur = image.filter(ImageFilter.GaussianBlur(10))
        return Image.blend(image, blur, 0.3)
    
    @staticmethod
    def _add_noise(image: Image.Image, intensity: int = 25) -> Image.Image:
        img_array = np.array(image.convert('RGB'))
        noise = np.random.normal(0, intensity, img_array.shape)
        noisy = img_array + noise
        return Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _vignette(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        height, width = img_array.shape[:2]
        
        X, Y = np.meshgrid(np.arange(width), np.arange(height))
        center_x, center_y = width // 2, height // 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        vignette = 1 - (dist / max_dist) * 0.6
        
        for c in range(3):
            img_array[:, :, c] *= vignette
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
    
    @staticmethod
    def _bokeh(image: Image.Image) -> Image.Image:
        for _ in range(3):
            image = image.filter(ImageFilter.GaussianBlur(2))
        return image
    
    @staticmethod
    def _halftone(image: Image.Image) -> Image.Image:
        gray = ImageOps.grayscale(image)
        return gray.convert('1', dither=Image.FLOYDSTEINBERG)
    
    @staticmethod
    def _color_splash(image: Image.Image, keep_color: str = "red") -> Image.Image:
        img_array = np.array(image.convert('RGB'))
        gray = np.array(ImageOps.grayscale(image))
        
        if keep_color == "red":
            mask = img_array[:, :, 0] > (img_array[:, :, 1] + img_array[:, :, 2]) / 2
        elif keep_color == "blue":
            mask = img_array[:, :, 2] > (img_array[:, :, 0] + img_array[:, :, 1]) / 2
        elif keep_color == "green":
            mask = img_array[:, :, 1] > (img_array[:, :, 0] + img_array[:, :, 2]) / 2
        else:
            return image
        
        result = np.stack([gray] * 3, axis=2)
        result[mask] = img_array[mask]
        return Image.fromarray(result)
    
    @staticmethod
    def _sobel_edge(image: Image.Image) -> Image.Image:
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
        img_array = np.array(ImageOps.grayscale(image))
        edges = cv2.Canny(img_array, 50, 150)
        return Image.fromarray(edges, mode='L')
    
    @staticmethod
    def _laplacian(image: Image.Image) -> Image.Image:
        img_array = np.array(ImageOps.grayscale(image)).astype(np.float32)
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        edges = convolve(img_array, laplacian)
        edges = np.abs(edges)
        edges = (edges / edges.max() * 255).astype(np.uint8)
        return Image.fromarray(edges, mode='L')
    
    @staticmethod
    def _fisheye(image: Image.Image) -> Image.Image:
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
    def _infrared(image: Image.Image) -> Image.Image:
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
        gray = np.array(ImageOps.grayscale(image))
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        return Image.fromarray(cv2.cvtColor(thermal, cv2.COLOR_BGR2RGB))
    
    @staticmethod
    def _xray(image: Image.Image) -> Image.Image:
        img_array = np.array(ImageOps.grayscale(image))
        inverted = 255 - img_array
        return Image.fromarray(inverted, mode='L')
    
    @staticmethod
    def _dream(image: Image.Image) -> Image.Image:
        blur = image.filter(ImageFilter.GaussianBlur(5))
        blended = Image.blend(image, blur, 0.4)
        enhancer = ImageEnhance.Brightness(blended)
        return enhancer.enhance(1.1)
    
    @staticmethod
    def _fire(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.5, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.6, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.3, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def _ice(image: Image.Image) -> Image.Image:
        img_array = np.array(image.convert('RGB')).astype(np.float32)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.5, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.8, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.5, 0, 255)
        return Image.fromarray(img_array.astype(np.uint8))
    
    @staticmethod
    def resize(image: Image.Image, width: int = None, height: int = None, keep_ratio: bool = True) -> Image.Image:
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
        return image.rotate(angle, expand=expand)
    
    @staticmethod
    def flip(image: Image.Image, horizontal: bool = True) -> Image.Image:
        if horizontal:
            return ImageOps.mirror(image)
        return ImageOps.flip(image)
    
    @staticmethod
    def crop(image: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
        return image.crop((left, top, right, bottom))
    
    @staticmethod
    def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    @staticmethod
    def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    @staticmethod
    def adjust_saturation(image: Image.Image, factor: float) -> Image.Image:
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)
    
    @staticmethod
    def adjust_sharpness(image: Image.Image, factor: float) -> Image.Image:
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
    
    @staticmethod
    def add_text(image: Image.Image, text: str, position: Tuple[int, int] = (10, 10),
                 font_size: int = 30, color: str = 'white') -> Image.Image:
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        for offset in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            draw.text((position[0]+offset[0], position[1]+offset[1]), text, fill='black', font=font)
        draw.text(position, text, fill=color, font=font)
        return image
    
    @staticmethod
    def add_watermark(image: Image.Image, watermark_text: str, opacity: float = 0.5) -> Image.Image:
        watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2
        
        draw.text((x, y), watermark_text, fill=(255, 255, 255, int(255 * opacity)), font=font)
        
        return Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')
    
    @staticmethod
    def auto_enhance(image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.15)
        return image
    
    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
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
        if layout == 'grid':
            per_row = min(2, len(images))
            rows = (len(images) + per_row - 1) // per_row
            target_size = (500, 500)
            resized = [img.resize(target_size, Image.Resampling.LANCZOS) for img in images[:4]]
            collage = Image.new('RGB', (target_size[0] * per_row, target_size[1] * rows))
            for i, img in enumerate(resized):
                x = (i % per_row) * target_size[0]
                y = (i // per_row) * target_size[1]
                collage.paste(img, (x, y))
            return collage
        return images[0]

# ==================== Video Processor ====================

class AdvancedVideoProcessor:
    @staticmethod
    def trim(video_path: str, start_time: float, end_time: float, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            trimmed = clip.subclip(start_time, end_time)
            trimmed.write_videofile(output_path, codec='libx264', audio_codec='aac')
            trimmed.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_speed(video_path: str, speed_factor: float, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            sped = clip.fx(vfx.speedx, speed_factor)
            sped.write_videofile(output_path, codec='libx264', audio_codec='aac')
            sped.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_audio(video_path: str, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            if clip.audio:
                clip.audio.write_audiofile(output_path)
                clip.close()
                return True, output_path
            clip.close()
            return False, "No audio track"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def merge_videos(video_paths: List[str], output_path: str) -> Tuple[bool, str]:
        try:
            clips = [VideoFileClip(path) for path in video_paths]
            final = concatenate_videoclips(clips)
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            final.close()
            for clip in clips:
                clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_watermark(video_path: str, watermark_text: str, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            txt_clip = TextClip(watermark_text, fontsize=30, color='white', 
                                font='Arial', stroke_color='black', stroke_width=1)
            txt_clip = txt_clip.set_position(('right', 'bottom')).set_duration(clip.duration)
            final = CompositeVideoClip([clip, txt_clip])
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            txt_clip.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def resize(video_path: str, width: int, height: int, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            resized = clip.resize((width, height))
            resized.write_videofile(output_path, codec='libx264', audio_codec='aac')
            resized.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_audio(video_path: str, audio_path: str, output_path: str) -> Tuple[bool, str]:
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            if audio.duration < video.duration:
                audio = audio.fx(audio_loop, duration=video.duration)
            final_audio = CompositeAudioClip([audio])
            final = video.set_audio(final_audio)
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            video.close()
            audio.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def apply_filter(video_path: str, filter_name: str, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path)
            filters_map = {
                "grayscale": lambda c: c.fx(vfx.blackwhite),
                "invert": lambda c: c.fx(vfx.invert_colors),
                "mirror": lambda c: c.fx(vfx.mirror_x),
                "flip": lambda c: c.fx(vfx.mirror_y),
                "fade_in": lambda c: c.fx(fadein, duration=1),
                "fade_out": lambda c: c.fx(fadeout, duration=1),
                "slow_motion": lambda c: c.fx(vfx.speedx, 0.5),
                "fast_motion": lambda c: c.fx(vfx.speedx, 2.0)
            }
            func = filters_map.get(filter_name, lambda c: c)
            processed = func(clip)
            processed.write_videofile(output_path, codec='libx264', audio_codec='aac')
            processed.close()
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def create_gif(video_path: str, start_time: float, end_time: float, output_path: str) -> Tuple[bool, str]:
        try:
            clip = VideoFileClip(video_path).subclip(start_time, end_time)
            clip.write_gif(output_path, fps=10)
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_info(video_path: str) -> Dict:
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'size': clip.size,
                'fps': clip.fps,
                'audio': clip.audio is not None
            }
            clip.close()
            return info
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _parse_time(time_str: str) -> float:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
        return float(time_str)

# ==================== Keyboard Builder ====================

class KeyboardBuilder:
    @staticmethod
    def get_main_menu(is_admin: bool = False, is_premium: bool = False) -> InlineKeyboardMarkup:
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
             InlineKeyboardButton("❓ HELP", callback_data="help")],
            [InlineKeyboardButton("📝 FEEDBACK", callback_data="feedback"),
             InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
            [InlineKeyboardButton("💻 CODE FORMAT", callback_data="code_format"),
             InlineKeyboardButton("⚡ CUSTOM CMDS", callback_data="custom_commands_menu")]
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats"),
             InlineKeyboardButton("👥 USER LIST", callback_data="admin_users")],
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("📅 SCHEDULE", callback_data="admin_schedule")],
            [InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban"),
             InlineKeyboardButton("🔇 MUTE USER", callback_data="admin_mute")],
            [InlineKeyboardButton("⚠️ WARN USER", callback_data="admin_warn"),
             InlineKeyboardButton("✅ UNBAN/UNMUTE", callback_data="admin_unban")],
            [InlineKeyboardButton("💎 GIVE PREMIUM", callback_data="admin_give_premium"),
             InlineKeyboardButton("💰 ADD CREDITS", callback_data="admin_add_credits")],
            [InlineKeyboardButton("📝 AUTO RESPONSES", callback_data="admin_auto_responses"),
             InlineKeyboardButton("📋 FEEDBACK", callback_data="admin_feedback_list")],
            [InlineKeyboardButton("📜 ADMIN LOGS", callback_data="admin_logs"),
             InlineKeyboardButton("📊 EXPORT DATA", callback_data="admin_export")],
            [InlineKeyboardButton("⚡ CUSTOM COMMANDS", callback_data="admin_custom_cmds"),
             InlineKeyboardButton("🔄 RESET USER", callback_data="admin_reset_user")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_commands_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📋 LIST COMMANDS", callback_data="list_custom_cmds")],
            [InlineKeyboardButton("🔍 SEARCH COMMAND", callback_data="search_custom_cmd")],
        ]
        if is_admin:
            keyboard.extend([
                [InlineKeyboardButton("➕ ADD COMMAND", callback_data="add_custom_cmd")],
                [InlineKeyboardButton("❌ DELETE COMMAND", callback_data="delete_custom_cmd")],
                [InlineKeyboardButton("🔧 TOGGLE COMMAND", callback_data="toggle_custom_cmd")],
            ])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_code_format_menu() -> InlineKeyboardMarkup:
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
    def get_image_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="img_filters")],
            [InlineKeyboardButton("📐 RESIZE", callback_data="img_resize"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="img_rotate")],
            [InlineKeyboardButton("🪞 FLIP", callback_data="img_flip"),
             InlineKeyboardButton("✂️ CROP", callback_data="img_crop")],
            [InlineKeyboardButton("☀️ BRIGHTNESS", callback_data="img_brightness"),
             InlineKeyboardButton("🌓 CONTRAST", callback_data="img_contrast")],
            [InlineKeyboardButton("🎨 SATURATION", callback_data="img_saturation"),
             InlineKeyboardButton("✏️ SHARPNESS", callback_data="img_sharpness")],
            [InlineKeyboardButton("📝 ADD TEXT", callback_data="img_text"),
             InlineKeyboardButton("💧 WATERMARK", callback_data="img_watermark")],
            [InlineKeyboardButton("✨ AUTO ENHANCE", callback_data="img_auto"),
             InlineKeyboardButton("🎭 REMOVE BG", callback_data="img_remove_bg")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_filters_menu() -> InlineKeyboardMarkup:
        filters = [
            "Blur", "Contour", "Detail", "Edge", "Emboss", "Sharpen",
            "Smooth", "Grayscale", "Sepia", "Negative", "Vintage",
            "Oil Paint", "Watercolor", "Pencil Sketch", "Cartoon", "Neon",
            "Glitch", "VHS", "Pixelate", "Mosaic", "Glow", "Noise",
            "Vignette", "Bokeh", "Halftone", "Color Splash",
            "Warm", "Cool", "Dramatic", "Cinematic", "Teal Orange",
            "Sunset", "Golden Hour", "Moody", "Pastel",
            "Sobel", "Canny", "Laplacian",
            "Fisheye", "Tilt Shift", "Infrared", "Thermal", "Xray",
            "Dream", "Fire", "Ice"
        ]
        keyboard = []
        row = []
        for f in filters:
            callback = f"filter_{f.lower().replace(' ', '_')}"
            row.append(InlineKeyboardButton(f[:12], callback_data=callback))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_image")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_video_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="vid_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="vid_speed")],
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="vid_audio"),
             InlineKeyboardButton("🔊 MUTE", callback_data="vid_mute")],
            [InlineKeyboardButton("📐 RESIZE", callback_data="vid_resize"),
             InlineKeyboardButton("🏷️ WATERMARK", callback_data="vid_watermark")],
            [InlineKeyboardButton("🔗 MERGE", callback_data="vid_merge"),
             InlineKeyboardButton("🎵 ADD AUDIO", callback_data="vid_add_audio")],
            [InlineKeyboardButton("🎞️ TO GIF", callback_data="vid_to_gif"),
             InlineKeyboardButton("ℹ️ INFO", callback_data="vid_info")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_captcha_keyboard(correct: str, options: List[str]) -> InlineKeyboardMarkup:
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

# ==================== Main Bot Class ====================

class KinvaMasterBot:
    def __init__(self):
        self.db = DatabaseManager(DATABASE_PATH)
        self.sessions: Dict[int, UserSession] = {}
        self.image_processor = AdvancedImageProcessor()
        self.video_processor = AdvancedVideoProcessor()
        self.code_formatter = CodeFormatter()
        self.application = None
        self.flask_app = None
        self.user_rate_limits = defaultdict(list)
        self._background_tasks = []
    
    async def start(self):
        """Start the bot with proper async handling"""
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        self._register_handlers()
        await self._set_bot_commands()
        
        if USE_WEBHOOK and WEBHOOK_URL and HAS_FLASK:
            await self.application.initialize()
            await self.application.start()
            await self.application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            self._start_web_server()
            logger.info(f"Bot started in webhook mode on port {PORT}")
        else:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Bot started in polling mode")
        
        # Start background tasks properly
        self._background_tasks.append(asyncio.create_task(self._process_scheduled_messages()))
        self._background_tasks.append(asyncio.create_task(self._cleanup_sessions_loop()))
        
        try:
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await self.stop()
    
    def _start_web_server(self):
        """Start Flask web server for webhook"""
        if not HAS_FLASK:
            logger.warning("Flask not installed. Webhook mode disabled.")
            return
            
        self.flask_app = Flask(__name__)
        
        @self.flask_app.route('/webhook', methods=['POST'])
        async def webhook():
            update = Update.de_json(request.get_json(force=True), self.application.bot)
            await self.application.process_update(update)
            return 'OK', 200
        
        @self.flask_app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "ok", "time": datetime.now().isoformat()}), 200
        
        @self.flask_app.route('/stats', methods=['GET'])
        def stats():
            stats = self.db.get_bot_stats()
            return jsonify(stats), 200
        
        @self.flask_app.route('/', methods=['GET'])
        def home():
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>KINVA MASTER PRO</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                        h1 { font-size: 48px; }
                        .status { background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin: 20px; }
                        .online { color: #4ade80; }
                    </style>
                </head>
                <body>
                    <h1>🎨 KINVA MASTER PRO</h1>
                    <div class="status">
                        <h2>Bot Status: <span class="online">● ONLINE</span></h2>
                        <p>Advanced Image & Video Editing Bot</p>
                        <p>Version: 6.1.0</p>
                    </div>
                    <p>🤖 Bot is running and ready to process your media!</p>
                </body>
                </html>
            ''')
        
        def run_flask():
            self.flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Clean up sessions
        for session in self.sessions.values():
            if session.temp_file_path and os.path.exists(session.temp_file_path):
                try:
                    os.remove(session.temp_file_path)
                except:
                    pass
            for f in session.merge_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
        
        if self.application:
            if USE_WEBHOOK:
                await self.application.bot.delete_webhook()
            await self.application.stop()
            await self.application.shutdown()
        
        # Clean temp directory
        try:
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        except:
            pass
        
        logger.info("Bot stopped.")
    
    def _register_handlers(self):
        """Register all handlers"""
        # User commands
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.application.add_handler(CommandHandler("premium", self.cmd_premium))
        self.application.add_handler(CommandHandler("feedback", self.cmd_feedback))
        self.application.add_handler(CommandHandler("daily", self.cmd_daily))
        self.application.add_handler(CommandHandler("refer", self.cmd_refer))
        self.application.add_handler(CommandHandler("credits", self.cmd_credits))
        
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
        self.application.add_handler(CommandHandler("customcmd", self.cmd_custom_command))
        
        # Callbacks and messages
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    async def _set_bot_commands(self):
        """Set bot commands"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help"),
            BotCommand("stats", "Your statistics"),
            BotCommand("daily", "Claim daily reward"),
            BotCommand("refer", "Referral info"),
            BotCommand("credits", "Check credits"),
            BotCommand("premium", "Premium info"),
            BotCommand("feedback", "Send feedback"),
            BotCommand("cancel", "Cancel operation"),
            BotCommand("customcmd", "Use custom command"),
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
        self.user_rate_limits[user_id] = [t for t in self.user_rate_limits[user_id] 
                                           if (now - t).seconds < RATE_LIMIT_SECONDS]
        if len(self.user_rate_limits[user_id]) >= 5:
            return False
        self.user_rate_limits[user_id].append(now)
        return True
    
    async def _cleanup_sessions_loop(self):
        """Clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(60)
                now = datetime.now()
                expired = []
                for user_id, session in self.sessions.items():
                    if session.state == UserState.AWAITING_CAPTCHA:
                        if session.captcha_start_time and (now - session.captcha_start_time).seconds > CAPTCHA_TIMEOUT:
                            expired.append(user_id)
                for user_id in expired:
                    if user_id in self.sessions:
                        session = self.sessions[user_id]
                        if session.temp_file_path and os.path.exists(session.temp_file_path):
                            try:
                                os.remove(session.temp_file_path)
                            except:
                                pass
                        del self.sessions[user_id]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
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
                            await self.application.bot.send_message(
                                chat_id=user['user_id'],
                                text=f"📢 *SCHEDULED ANNOUNCEMENT*\n\n{msg['message']}",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            success += 1
                            await asyncio.sleep(0.05)
                        except:
                            pass
                    self.db.mark_scheduled_sent(msg['id'])
                    logger.info(f"Scheduled message sent: {success} recipients")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing scheduled messages: {e}")
    
    # ==================== User Commands ====================
    
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
        
        # CAPTCHA
        num1, num2 = random.randint(5, 25), random.randint(5, 25)
        op = random.choice(['+', '-', '*'])
        if op == '+':
            answer = str(num1 + num2)
        elif op == '-':
            answer = str(num1 - num2)
        else:
            answer = str(num1 * num2)
        
        # Generate wrong options
        options = [answer]
        while len(options) < 4:
            wrong = str(int(answer) + random.randint(-10, 10))
            if wrong != answer and wrong not in options:
                options.append(wrong)
        random.shuffle(options)
        
        session = self.get_session(user_id)
        session.captcha_code = answer
        session.captcha_attempts = 0
        session.captcha_start_time = datetime.now()
        session.state = UserState.AWAITING_CAPTCHA
        
        await update.message.reply_text(
            f"🌟 *WELCOME TO KINVA MASTER PRO* 🌟\n\n"
            f"*Advanced Image & Video Editing Bot*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *Features:*\n"
            f"• 100+ Editing Options\n"
            f"• 50+ Professional Filters\n"
            f"• Video & Audio Processing\n"
            f"• GIF Creation\n"
            f"• AI Auto-Enhance\n"
            f"• Code Formatter (New!)\n"
            f"• Custom Commands (New!)\n"
            f"• Daily Rewards\n"
            f"• Referral Program\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔐 *VERIFICATION REQUIRED*\n\n"
            f"Please solve:\n\n`{num1} {op} {num2} = ?`\n\n"
            f"_You have {CAPTCHA_TIMEOUT} seconds._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_captcha_keyboard(answer, options)
        )
    
    async def _send_main_menu(self, update: Update, user: User):
        """Send main menu"""
        user_id = user.id
        is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
        is_premium = self.db.is_premium(user_id)
        
        stats = self.db.get_user_stats(user_id)
        menu_msg = (
            f"🎨 *KINVA MASTER PRO* 🎨\n\n"
            f"*Welcome back, {user.first_name}!*\n\n"
            f"📊 *Your Stats:*\n"
            f"• Total Edits: {stats.get('total_edits', 0)}\n"
            f"• Images: {stats.get('total_images', 0)}\n"
            f"• Videos: {stats.get('total_videos', 0)}\n"
            f"• Credits: {stats.get('credits', 100)}\n"
            f"• Premium: {'✅ Active' if is_premium else '❌ Inactive'}\n\n"
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
            "❓ *KINVA MASTER PRO HELP* ❓\n\n"
            "*Image Editing:*\n"
            "• 50+ professional filters\n"
            "• Resize, rotate, flip, crop\n"
            "• Adjust brightness, contrast, saturation\n"
            "• Add text or watermark\n"
            "• Auto-enhance, remove background\n\n"
            "*Video Editing:*\n"
            "• Trim, merge, speed change\n"
            "• Extract audio, add audio\n"
            "• Add watermark, resize\n"
            "• Convert to GIF\n\n"
            "*New Features:*\n"
            "• 💻 Code Formatter - Format Python, JS, HTML, CSS, JSON, SQL\n"
            "• ⚡ Custom Commands - Create your own commands\n\n"
            "*Commands:*\n"
            "/start - Start bot\n"
            "/daily - Claim daily reward\n"
            "/refer - Get referral link\n"
            "/credits - Check credits\n"
            "/premium - Premium info\n"
            "/feedback - Send feedback\n"
            "/customcmd <name> - Use custom command\n"
            "/cancel - Cancel operation\n\n"
            "*Support:* @KinvaMasterSupport",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        stats = self.db.get_user_stats(user.id)
        is_premium = self.db.is_premium(user.id)
        is_banned, ban_reason = self.db.is_banned(user.id)
        is_muted, muted_until = self.db.is_muted(user.id)
        
        await update.message.reply_text(
            f"📊 *YOUR STATISTICS* 📊\n\n"
            f"*User:* {user.first_name}\n"
            f"*ID:* `{user.id}`\n\n"
            f"*Activity:*\n"
            f"• Total Edits: `{stats.get('total_edits', 0)}`\n"
            f"• Images: `{stats.get('total_images', 0)}`\n"
            f"• Videos: `{stats.get('total_videos', 0)}`\n\n"
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
            if session.temp_file_path and os.path.exists(session.temp_file_path):
                try:
                    os.remove(session.temp_file_path)
                except:
                    pass
            for f in session.merge_files:
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
                f"❌ *Already claimed!*\n\n"
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
                f"*Expires:* {stats.get('premium_expires', 'N/A')}\n\n"
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
                "*Price:* $2.99 for 30 days\n\n"
                "Contact @KinvaMasterSupport to upgrade!",
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
    
    async def cmd_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /customcmd command"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚡ *Custom Commands* ⚡\n\n"
                "Usage: `/customcmd <command_name>`\n\n"
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
            await update.message.reply_text(f"❌ Custom command '{cmd_name}' not found!", parse_mode=ParseMode.MARKDOWN)
    
    # ==================== Admin Commands ====================
    
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
    
    # ==================== Callback Handler ====================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        # Check mute status
        is_muted, muted_until = self.db.is_muted(user_id)
        if is_muted and data not in ["stats", "help", "daily_reward"]:
            await query.edit_message_text(f"🔇 *You are muted until {muted_until.strftime('%Y-%m-%d %H:%M') if muted_until else 'further notice'}*", parse_mode=ParseMode.MARKDOWN)
            return
        
        # CAPTCHA
        if data.startswith("captcha_"):
            selected = data.replace("captcha_", "")
            session = self.get_session(user_id)
            if selected == session.captcha_code:
                self.db.verify_user(user_id, "captcha")
                session.state = UserState.VERIFIED
                await query.edit_message_text("✅ *Verification successful!*", parse_mode=ParseMode.MARKDOWN)
                await self._send_main_menu(update, query.from_user)
            else:
                session.captcha_attempts += 1
                if session.captcha_attempts >= MAX_CAPTCHA_ATTEMPTS:
                    await query.edit_message_text("❌ *Verification failed!* Use /start to try again.", parse_mode=ParseMode.MARKDOWN)
                    del self.sessions[user_id]
                else:
                    await query.edit_message_text(f"❌ *Incorrect!* Attempts left: {MAX_CAPTCHA_ATTEMPTS - session.captcha_attempts}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Code Formatter (NEW)
        if data == "code_format":
            await query.edit_message_text(
                "💻 *CODE FORMATTER* 💻\n\n"
                "Select a language to format your code:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_code_format_menu()
            )
        
        elif data.startswith("format_"):
            lang = data.replace("format_", "")
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_CODE_INPUT
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
        
        # Custom Commands Menu (NEW)
        elif data == "custom_commands_menu":
            is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
            await query.edit_message_text(
                "⚡ *CUSTOM COMMANDS* ⚡\n\n"
                "Browse and use custom commands created by admins.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_custom_commands_menu(is_admin)
            )
        
        elif data == "list_custom_cmds":
            commands = self.db.list_custom_commands()
            if commands:
                text = "📋 *AVAILABLE CUSTOM COMMANDS*\n\n"
                for cmd in commands[:20]:
                    text += f"• `/{cmd['command']}` - {cmd['response_type']}"
                    if cmd.get('language'):
                        text += f" ({cmd['language']})"
                    text += f"\n  Usage count: {cmd.get('usage_count', 0)}\n"
                text += "\n_Use /customcmd <name> to execute_"
            else:
                text = "❌ No custom commands available."
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        
        elif data == "add_custom_cmd":
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                await query.answer("Access denied!", show_alert=True)
                return
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_CUSTOM_COMMAND
            session.pending_effect = "add_custom_cmd"
            await query.edit_message_text(
                "➕ *ADD CUSTOM COMMAND*\n\n"
                "Send in format:\n"
                "`/addcmd <name> <type> <language?> | <content>`\n\n"
                "Types: text, code, photo, video\n"
                "Example: `/addcmd welcome text | Welcome to the bot!`\n"
                "Example: `/addcmd pycode code python | print('Hello')`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "delete_custom_cmd":
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                await query.answer("Access denied!", show_alert=True)
                return
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_CUSTOM_COMMAND
            session.pending_effect = "delete_custom_cmd"
            await query.edit_message_text(
                "❌ *DELETE CUSTOM COMMAND*\n\n"
                "Send the command name to delete:",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admin_custom_cmds":
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                await query.answer("Access denied!", show_alert=True)
                return
            commands = self.db.list_custom_commands()
            if commands:
                text = "⚡ *MANAGE CUSTOM COMMANDS*\n\n"
                for cmd in commands:
                    status = "✅" if cmd.get('is_active') else "❌"
                    text += f"{status} `{cmd['command']}` - {cmd['response_type']} (Used: {cmd.get('usage_count', 0)})\n"
            else:
                text = "No custom commands found."
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        
        # Main menu navigation
        elif data == "mode_image":
            await query.edit_message_text("🖼️ *Image Editing Mode*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.editing_mode = EditingMode.IMAGE
            session.state = UserState.AWAITING_IMAGE
        
        elif data == "mode_video":
            await query.edit_message_text("🎬 *Video Editing Mode*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.editing_mode = EditingMode.VIDEO
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "mode_audio":
            await query.edit_message_text("🎵 *Audio Editing Mode*\n\nSend me an audio file:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.editing_mode = EditingMode.AUDIO
            session.state = UserState.AWAITING_AUDIO
        
        elif data == "mode_gif":
            await query.edit_message_text("🎞️ *GIF Creation Mode*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.editing_mode = EditingMode.GIF
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "ai_enhance":
            await query.edit_message_text("✨ *AI Auto-Enhance*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "auto_enhance"
            session.state = UserState.AWAITING_IMAGE
        
        elif data == "collage":
            await query.edit_message_text("🎨 *Create Collage*\n\nSend me images (up to 4). Type 'done' when finished:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "collage"
            session.batch_files = []
            session.state = UserState.AWAITING_MERGE_FILES
        
        elif data == "daily_reward":
            reward, streak = self.db.claim_daily_reward(user_id)
            if reward > 0:
                await query.edit_message_text(f"⭐ *DAILY REWARD* ⭐\n\nYou received: `{reward} credits`\nStreak: `{streak} days`", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(f"❌ *Already claimed today!*\nStreak: `{streak} days`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "referral":
            await self.cmd_refer(update, context)
        
        elif data == "stats":
            await self.cmd_stats(update, context)
        
        elif data == "premium":
            await self.cmd_premium(update, context)
        
        elif data == "help":
            await self.cmd_help(update, context)
        
        elif data == "feedback":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_FEEDBACK
            await query.edit_message_text("📝 *Send feedback:*", parse_mode=ParseMode.MARKDOWN)
        
        # Image editing
        elif data == "img_filters":
            await query.edit_message_text("🎨 *Select a filter:*", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.get_filters_menu())
        
        elif data == "img_resize":
            await query.edit_message_text("📐 *Resize*\n\nSend dimensions (width height):\nExample: `1920 1080`", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "resize"
            session.state = UserState.AWAITING_RESIZE_DIMS
        
        elif data == "img_rotate":
            await query.edit_message_text("🔄 *Rotate*\n\nSend angle (0-360):", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "rotate"
            session.state = UserState.AWAITING_ROTATE_ANGLE
        
        elif data == "img_flip":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🪞 Horizontal", callback_data="flip_h")],
                [InlineKeyboardButton("↕️ Vertical", callback_data="flip_v")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_image")]
            ])
            await query.edit_message_text("🪞 *Flip Image*", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        
        elif data == "img_crop":
            await query.edit_message_text("✂️ *Crop*\n\nSend coordinates (left top right bottom):\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "crop"
            session.state = UserState.AWAITING_CROP_COORDS
        
        elif data in ["img_brightness", "img_contrast", "img_saturation", "img_sharpness"]:
            effect = data.replace("img_", "")
            await query.edit_message_text(f"🎨 *Adjust {effect.title()}*\n\nSend factor (0.5-2.0):", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = effect
            session.state = UserState.AWAITING_COLOR_ADJUST
        
        elif data == "img_text":
            await query.edit_message_text("📝 *Add Text*\n\nSend the text to add:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "add_text"
            session.state = UserState.AWAITING_TEXT_CONTENT
        
        elif data == "img_watermark":
            await query.edit_message_text("💧 *Add Watermark*\n\nSend watermark text:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "add_watermark"
            session.state = UserState.AWAITING_TEXT_CONTENT
        
        elif data == "img_auto":
            await query.edit_message_text("✨ *Auto-Enhance*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "auto_enhance"
            session.state = UserState.AWAITING_IMAGE
        
        elif data == "img_remove_bg":
            await query.edit_message_text("🎭 *Remove Background*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "remove_bg"
            session.state = UserState.AWAITING_IMAGE
        
        # Filters
        elif data.startswith("filter_"):
            filter_name = data.replace("filter_", "")
            session = self.get_session(user_id)
            session.pending_effect = filter_name
            session.state = UserState.AWAITING_IMAGE
            await query.edit_message_text(f"🎨 *Apply Filter: {filter_name.title()}*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
        
        # Flip
        elif data in ["flip_h", "flip_v"]:
            session = self.get_session(user_id)
            session.pending_effect = data
            session.state = UserState.AWAITING_IMAGE
            await query.edit_message_text(f"🪞 *Flip {('Horizontal' if data == 'flip_h' else 'Vertical')}*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
        
        # Video editing
        elif data == "vid_trim":
            await query.edit_message_text("✂️ *Trim Video*\n\nSend start and end times (seconds or HH:MM:SS):\nExample: `10 30` or `00:00:10 00:00:30`", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "trim"
            session.state = UserState.AWAITING_TRIM_TIMES
        
        elif data == "vid_speed":
            await query.edit_message_text("⚡ *Change Speed*\n\nSend speed factor:\n• 0.5 = Slow motion\n• 1.0 = Normal\n• 2.0 = Fast", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "speed"
            session.state = UserState.AWAITING_SPEED_FACTOR
        
        elif data == "vid_audio":
            await query.edit_message_text("🎵 *Extract Audio*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "extract_audio"
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "vid_mute":
            await query.edit_message_text("🔊 *Mute Video*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "mute"
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "vid_resize":
            await query.edit_message_text("📐 *Resize Video*\n\nSend dimensions (width height):\nExample: `1920 1080`", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "resize_video"
            session.state = UserState.AWAITING_RESIZE_DIMS
        
        elif data == "vid_watermark":
            await query.edit_message_text("🏷️ *Add Watermark*\n\nSend watermark text:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "video_watermark"
            session.state = UserState.AWAITING_TEXT_CONTENT
        
        elif data == "vid_merge":
            await query.edit_message_text("🔗 *Merge Videos*\n\nSend videos one by one. Type 'done' when finished:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "merge_videos"
            session.merge_files = []
            session.state = UserState.AWAITING_MERGE_FILES
        
        elif data == "vid_add_audio":
            await query.edit_message_text("🎵 *Add Audio to Video*\n\nSend the video file:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "add_audio"
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "vid_to_gif":
            await query.edit_message_text("🎞️ *Convert to GIF*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "to_gif"
            session.state = UserState.AWAITING_VIDEO
        
        elif data == "vid_info":
            await query.edit_message_text("ℹ️ *Video Info*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session.pending_effect = "video_info"
            session.state = UserState.AWAITING_VIDEO
        
        # Admin panel
        elif data == "admin_panel":
            await query.edit_message_text("👑 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.get_admin_panel())
        
        elif data == "admin_stats":
            stats = self.db.get_bot_stats()
            await query.edit_message_text(
                f"📊 *BOT STATISTICS* 📊\n\n"
                f"👥 Total Users: `{stats['total_users']}`\n"
                f"🟢 Active Today: `{stats['active_today']}`\n"
                f"🎨 Total Edits: `{stats['total_edits']}`\n"
                f"⭐ Premium Users: `{stats['premium_users']}`\n"
                f"🚫 Banned Users: `{stats['banned_users']}`\n"
                f"📈 Avg Edits/User: `{stats['total_edits'] // stats['total_users'] if stats['total_users'] > 0 else 0}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
        
        elif data == "admin_users":
            users = self.db.get_all_users(limit=20)
            text = "👥 *RECENT USERS*\n\n"
            for u in users:
                text += f"• `{u['user_id']}` - {u.get('first_name', 'Unknown')[:20]}\n"
                text += f"  Edits: {u.get('total_edits', 0)} | Credits: {u.get('credits', 0)}\n"
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]))
        
        elif data == "admin_broadcast":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_BROADCAST
            await query.edit_message_text("📢 *Broadcast*\n\nSend the message to broadcast:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_schedule":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ANNOUNCEMENT
            await query.edit_message_text("📅 *Schedule Message*\n\nSend message and time (format: MM/DD HH:MM):\nExample: `12/25 10:00 Happy Holidays!`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_ban":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "ban"
            await query.edit_message_text("🚫 *Ban User*\n\nSend user ID and reason:\nExample: `123456789 Spamming`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_mute":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "mute"
            await query.edit_message_text("🔇 *Mute User*\n\nSend user ID, minutes, and reason:\nExample: `123456789 60 Spamming`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_warn":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "warn"
            await query.edit_message_text("⚠️ *Warn User*\n\nSend user ID and reason:\nExample: `123456789 Rule violation`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_unban":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "unban"
            await query.edit_message_text("✅ *Unban/Unmute User*\n\nSend user ID:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_give_premium":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "give_premium"
            await query.edit_message_text("💎 *Give Premium*\n\nSend user ID and days:\nExample: `123456789 30`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_add_credits":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "add_credits"
            await query.edit_message_text("💰 *Add Credits*\n\nSend user ID and amount:\nExample: `123456789 100`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_auto_responses":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "auto_response"
            await query.edit_message_text("📝 *Auto Responses*\n\nTo add: `add keyword: response`\nTo remove: `remove keyword`\n\nExample: `add hello: Hi there!`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_feedback_list":
            feedbacks = self.db.get_pending_feedback()
            if feedbacks:
                text = "📋 *PENDING FEEDBACK*\n\n"
                for fb in feedbacks[:10]:
                    text += f"• #{fb['id']} from {fb.get('first_name', 'User')}: {fb['feedback_text'][:100]}\n"
                await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("No pending feedback.", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_logs":
            logs = self.db.get_admin_logs(20)
            text = "📜 *RECENT ADMIN LOGS*\n\n"
            for log in logs:
                text += f"• {log['created_at'][:16] if log['created_at'] else 'N/A'} - {log['admin_name']}: {log['action']}\n"
                if log.get('details'):
                    text += f"  {log['details'][:50]}\n"
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]))
        
        elif data == "admin_export":
            csv_data = self.db.export_users_csv()
            await query.edit_message_text("📊 *Exporting data...*", parse_mode=ParseMode.MARKDOWN)
            await context.bot.send_document(
                chat_id=user_id,
                document=InputFile(io.BytesIO(csv_data.encode()), filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv"),
                caption="User data export"
            )
        
        elif data == "admin_settings":
            await query.edit_message_text(
                "⚙️ *ADMIN SETTINGS* ⚙️\n\n"
                "Available commands:\n"
                "/ban - Ban user\n"
                "/unban - Unban user\n"
                "/mute - Mute user\n"
                "/unmute - Unmute user\n"
                "/warn - Warn user\n"
                "/clearwarns - Clear warnings\n"
                "/givepremium - Give premium\n"
                "/addcredits - Add credits\n"
                "/broadcast - Broadcast message\n"
                "/customcmd - Manage custom commands\n"
                "/admin - Admin panel",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admin_reset_user":
            session = self.get_session(user_id)
            session.state = UserState.AWAITING_ADMIN_ACTION
            session.pending_effect = "reset_user"
            await query.edit_message_text("🔄 *Reset User*\n\nSend user ID to reset all data:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "back_image":
            await query.edit_message_text("🖼️ *Image Editing Menu*", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.get_image_menu())
        
        elif data == "back_main":
            is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
            is_premium = self.db.is_premium(user_id)
            await query.edit_message_text("🎨 *Main Menu*", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium))
    
    # ==================== Message Handlers ====================
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages"""
        user_id = update.effective_user.id
        
        if not self.db.is_verified(user_id):
            await update.message.reply_text("❌ Please verify first with /start")
            return
        
        session = self.get_session(user_id)
        
        if session.state != UserState.AWAITING_IMAGE and session.state != UserState.AWAITING_MERGE_FILES:
            await update.message.reply_text("Please select an option from the menu first!", reply_markup=KeyboardBuilder.get_image_menu())
            return
        
        # Download image
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        temp_path = TEMP_DIR / f"img_{user_id}_{datetime.now().timestamp()}.jpg"
        await file.download_to_document(temp_path)
        
        # Handle collage collection
        if session.state == UserState.AWAITING_MERGE_FILES and session.pending_effect == "collage":
            session.batch_files.append(str(temp_path))
            if len(session.batch_files) >= 4:
                await self._process_collage(update, context, session.batch_files, user_id)
            else:
                await update.message.reply_text(f"📸 Image {len(session.batch_files)}/4 received. Send more or type 'done' to finish.")
            return
        
        session.temp_file_path = str(temp_path)
        effect = session.pending_effect
        
        if effect == "auto_enhance":
            await self._process_auto_enhance(update, context, temp_path, user_id)
        elif effect == "remove_bg":
            await self._process_remove_bg(update, context, temp_path, user_id)
        elif effect == "resize":
            session.state = UserState.AWAITING_RESIZE_DIMS
            await update.message.reply_text("Send dimensions (width height):", parse_mode=ParseMode.MARKDOWN)
        elif effect == "rotate":
            session.state = UserState.AWAITING_ROTATE_ANGLE
            await update.message.reply_text("Send rotation angle (0-360):", parse_mode=ParseMode.MARKDOWN)
        elif effect in ["flip_h", "flip_v"]:
            await self._process_flip(update, context, temp_path, user_id, effect)
        elif effect == "crop":
            session.state = UserState.AWAITING_CROP_COORDS
            await update.message.reply_text("Send crop coordinates (left top right bottom):", parse_mode=ParseMode.MARKDOWN)
        elif effect in ["brightness", "contrast", "saturation", "sharpness"]:
            session.state = UserState.AWAITING_COLOR_ADJUST
            await update.message.reply_text(f"Send {effect} factor (0.5-2.0):", parse_mode=ParseMode.MARKDOWN)
        elif effect in ["add_text", "add_watermark"]:
            session.state = UserState.AWAITING_TEXT_CONTENT
            await update.message.reply_text("Send the text:", parse_mode=ParseMode.MARKDOWN)
        else:
            await self._apply_image_filter(update, context, temp_path, user_id, effect)
    
    async def _apply_image_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, filter_name: str):
        """Apply image filter"""
        processing_msg = await update.message.reply_text("🎨 *Processing image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            img = Image.open(img_path)
            processed = self.image_processor.apply_filter(img, filter_name)
            
            output_path = TEMP_DIR / f"output_{user_id}_{datetime.now().timestamp()}.jpg"
            processed.save(output_path, quality=95)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=f"✅ *Filter applied: {filter_name.title()}!*",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=KeyboardBuilder.get_image_menu()
                )
            
            self.db.add_edit_record(user_id, "image", filter_name)
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
    
    async def _process_auto_enhance(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        """Process auto enhance"""
        processing_msg = await update.message.reply_text("✨ *AI Auto-Enhancing...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            enhanced = self.image_processor.auto_enhance(img)
            output_path = TEMP_DIR / f"enhanced_{user_id}_{datetime.now().timestamp()}.jpg"
            enhanced.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Image auto-enhanced!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_remove_bg(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        """Process background removal"""
        processing_msg = await update.message.reply_text("🎭 *Removing background...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            processed = self.image_processor.remove_background(img)
            output_path = TEMP_DIR / f"nobg_{user_id}_{datetime.now().timestamp()}.png"
            processed.save(output_path, "PNG")
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Background removed!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, flip_type: str):
        """Process flip"""
        processing_msg = await update.message.reply_text("🪞 *Flipping image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            horizontal = flip_type == "flip_h"
            flipped = self.image_processor.flip(img, horizontal)
            output_path = TEMP_DIR / f"flipped_{user_id}_{datetime.now().timestamp()}.jpg"
            flipped.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Image flipped!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_collage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, image_paths: List[str], user_id: int):
        """Process collage creation"""
        processing_msg = await update.message.reply_text("🎨 *Creating collage...*", parse_mode=ParseMode.MARKDOWN)
        try:
            images = [Image.open(path) for path in image_paths]
            collage = self.image_processor.create_collage(images)
            output_path = TEMP_DIR / f"collage_{user_id}_{datetime.now().timestamp()}.jpg"
            collage.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Collage created!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user_id = update.effective_user.id
        
        if not self.db.is_verified(user_id):
            await update.message.reply_text("❌ Please verify first with /start")
            return
        
        session = self.get_session(user_id)
        
        if session.state != UserState.AWAITING_VIDEO and session.state != UserState.AWAITING_MERGE_FILES:
            await update.message.reply_text("Please select a video editing option first!", reply_markup=KeyboardBuilder.get_video_menu())
            return
        
        video = update.message.video
        if video.file_size > MAX_VIDEO_SIZE:
            await update.message.reply_text(f"❌ Video too large! Max size: {MAX_VIDEO_SIZE // (1024*1024)}MB")
            return
        
        file = await context.bot.get_file(video.file_id)
        temp_path = TEMP_DIR / f"video_{user_id}_{datetime.now().timestamp()}.mp4"
        await file.download_to_document(temp_path)
        
        # Handle merge collection
        if session.state == UserState.AWAITING_MERGE_FILES and session.pending_effect == "merge_videos":
            session.merge_files.append(str(temp_path))
            await update.message.reply_text(f"📹 Video {len(session.merge_files)} received. Send more or type 'done' to finish.")
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
        elif effect == "add_audio":
            session.pending_effect = "add_audio_wait"
            session.state = UserState.AWAITING_AUDIO
            await update.message.reply_text("🎵 *Video received! Now send the audio file:*", parse_mode=ParseMode.MARKDOWN)
        elif effect == "trim":
            session.state = UserState.AWAITING_TRIM_TIMES
            await update.message.reply_text("✂️ *Send trim times (start end):*\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        elif effect == "speed":
            session.state = UserState.AWAITING_SPEED_FACTOR
            await update.message.reply_text("⚡ *Send speed factor:*\nExample: `2.0`", parse_mode=ParseMode.MARKDOWN)
        elif effect == "resize_video":
            session.state = UserState.AWAITING_RESIZE_DIMS
            await update.message.reply_text("📐 *Send dimensions (width height):*\nExample: `1920 1080`", parse_mode=ParseMode.MARKDOWN)
        elif effect == "video_watermark":
            session.state = UserState.AWAITING_TEXT_CONTENT
            await update.message.reply_text("🏷️ *Send watermark text:*", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Ready for processing. Send the required parameters.")
    
    async def _process_extract_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Extract audio from video"""
        processing_msg = await update.message.reply_text("🎵 *Extracting audio...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"audio_{user_id}_{datetime.now().timestamp()}.mp3"
            success, result = self.video_processor.extract_audio(str(video_path), str(output_path))
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption="✅ *Audio extracted!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def _process_mute_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Mute video"""
        processing_msg = await update.message.reply_text("🔊 *Muting video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"muted_{user_id}_{datetime.now().timestamp()}.mp4"
            clip = VideoFileClip(str(video_path))
            muted = clip.without_audio()
            muted.write_videofile(str(output_path), codec='libx264')
            muted.close()
            clip.close()
            with open(output_path, 'rb') as f:
                await update.message.reply_video(video=InputFile(f), caption="✅ *Video muted!*", reply_markup=KeyboardBuilder.get_video_menu())
            os.remove(output_path)
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
    
    async def _process_video_to_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Convert video to GIF"""
        processing_msg = await update.message.reply_text("🎞️ *Converting to GIF...*", parse_mode=ParseMode.MARKDOWN)
        try:
            clip = VideoFileClip(str(video_path))
            duration = min(clip.duration, 10)
            clip.close()
            output_path = TEMP_DIR / f"output_{user_id}_{datetime.now().timestamp()}.gif"
            success, result = self.video_processor.create_gif(str(video_path), 0, duration, str(output_path))
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_document(document=InputFile(f, filename="output.gif"), caption="✅ *GIF created!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def _process_video_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Get video info"""
        try:
            info = self.video_processor.get_info(str(video_path))
            if 'error' in info:
                await update.message.reply_text(f"❌ *Error:* {info['error']}", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(
                    f"ℹ️ *VIDEO INFO* ℹ️\n\n"
                    f"• Duration: `{info.get('duration', 0):.2f} seconds`\n"
                    f"• Resolution: `{info.get('size', [0,0])[0]}x{info.get('size', [0,0])[1]}`\n"
                    f"• FPS: `{info.get('fps', 0):.2f}`\n"
                    f"• Audio: `{'Yes' if info.get('audio', False) else 'No'}`",
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
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        
        if session.pending_effect == "add_audio_wait":
            audio = update.message.audio or update.message.voice
            if audio:
                file = await context.bot.get_file(audio.file_id)
                audio_path = TEMP_DIR / f"audio_{user_id}_{datetime.now().timestamp()}.mp3"
                await file.download_to_document(audio_path)
                video_path = session.temp_file_path
                if video_path and os.path.exists(video_path):
                    await self._process_add_audio(update, context, Path(video_path), audio_path, user_id)
                else:
                    await update.message.reply_text("❌ Video file not found. Please try again.")
    
    async def _process_add_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, audio_path: Path, user_id: int):
        """Add audio to video"""
        processing_msg = await update.message.reply_text("🎵 *Adding audio to video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"with_audio_{user_id}_{datetime.now().timestamp()}.mp4"
            success, result = self.video_processor.add_audio(str(video_path), str(audio_path), str(output_path))
            if success:
                if output_path.stat().st_size > 50 * 1024 * 1024:
                    compressed_path = TEMP_DIR / f"compressed_{user_id}_{datetime.now().timestamp()}.mp4"
                    clip = VideoFileClip(str(output_path))
                    compressed = clip.resize(height=720)
                    compressed.write_videofile(str(compressed_path), codec='libx264', audio_codec='aac')
                    compressed.close()
                    clip.close()
                    output_path = compressed_path
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption="✅ *Audio added!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages (for code formatting)"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        
        if session.state == UserState.AWAITING_CODE_INPUT:
            document = update.message.document
            if document and document.file_name:
                # Check file extension
                ext = document.file_name.split('.')[-1].lower() if '.' in document.file_name else ''
                lang_map = {
                    'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                    'html': 'html', 'htm': 'html', 'css': 'css',
                    'json': 'json', 'sql': 'sql', 'txt': 'text'
                }
                lang = lang_map.get(ext, 'text')
                
                file = await context.bot.get_file(document.file_id)
                temp_path = TEMP_DIR / f"code_{user_id}_{datetime.now().timestamp()}.txt"
                await file.download_to_document(temp_path)
                
                with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                await self._process_code_format(update, context, code, lang, user_id)
                try:
                    os.remove(temp_path)
                except:
                    pass
            else:
                await update.message.reply_text("❌ Please send a valid code file.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        text = update.message.text.strip()
        
        # Check rate limit
        if not self._check_rate_limit(user_id):
            await update.message.reply_text("⚠️ *Rate limit exceeded!* Please wait a moment.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check auto responses
        if session.state == UserState.VERIFIED:
            response = self.db.get_auto_response(text)
            if response:
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                return
        
        # Handle code formatting (NEW)
        if session.state == UserState.AWAITING_CODE_INPUT:
            lang = session.code_language
            await self._process_code_format(update, context, text, lang, user_id)
            return
        
        # Handle custom command management (NEW)
        if session.state == UserState.AWAITING_CUSTOM_COMMAND:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
                session.state = UserState.VERIFIED
                return
            
            if session.pending_effect == "add_custom_cmd":
                await self._process_add_custom_command(update, context, text, user_id)
            elif session.pending_effect == "delete_custom_cmd":
                if self.db.delete_custom_command(text.lower()):
                    await update.message.reply_text(f"✅ Custom command '{text}' deleted!", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text(f"❌ Command '{text}' not found!", parse_mode=ParseMode.MARKDOWN)
            
            session.state = UserState.VERIFIED
            session.pending_effect = None
            return
        
        # Handle feedback
        if session.state == UserState.AWAITING_FEEDBACK:
            self.db.save_feedback(user_id, text)
            await update.message.reply_text("✅ *Thank you for your feedback!*", parse_mode=ParseMode.MARKDOWN)
            session.state = UserState.VERIFIED
            return
        
        # Handle broadcast
        if session.state == UserState.AWAITING_BROADCAST:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                return
            users = self.db.get_all_users(limit=10000)
            success = 0
            failed = 0
            processing_msg = await update.message.reply_text("📢 *Broadcasting...*", parse_mode=ParseMode.MARKDOWN)
            
            for user in users:
                try:
                    await context.bot.send_message(chat_id=user['user_id'], text=f"📢 *ANNOUNCEMENT*\n\n{text}", parse_mode=ParseMode.MARKDOWN)
                    success += 1
                    await asyncio.sleep(0.05)
                except:
                    failed += 1
            
            self.db.add_broadcast_record(user_id, text, "text", len(users), success, failed)
            await processing_msg.edit_text(f"✅ *Broadcast sent!*\nSuccessful: {success}\nFailed: {failed}", parse_mode=ParseMode.MARKDOWN)
            session.state = UserState.VERIFIED
            return
        
        # Handle admin actions
        if session.state == UserState.AWAITING_ADMIN_ACTION:
            if user_id not in ADMIN_IDS and user_id != OWNER_ID:
                return
            
            if session.pending_effect == "ban":
                parts = text.split(maxsplit=1)
                if len(parts) >= 1:
                    try:
                        target_id = int(parts[0])
                        reason = parts[1] if len(parts) > 1 else "No reason"
                        self.db.ban_user(target_id, user_id, reason)
                        await update.message.reply_text(f"✅ *User {target_id} banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                        try:
                            await context.bot.send_message(target_id, f"⛔ *You have been banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!")
            
            elif session.pending_effect == "mute":
                parts = text.split(maxsplit=2)
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        minutes = int(parts[1])
                        reason = parts[2] if len(parts) > 2 else "No reason"
                        self.db.mute_user(target_id, user_id, minutes, reason)
                        await update.message.reply_text(f"✅ *User {target_id} muted for {minutes} minutes!*", parse_mode=ParseMode.MARKDOWN)
                        try:
                            await context.bot.send_message(target_id, f"🔇 *You have been muted for {minutes} minutes!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or minutes!")
            
            elif session.pending_effect == "warn":
                parts = text.split(maxsplit=1)
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        reason = parts[1]
                        warn_count = self.db.add_warning(target_id, user_id, reason)
                        await update.message.reply_text(f"⚠️ *User {target_id} warned!*\nWarnings: {warn_count}/3\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                        if warn_count >= 3:
                            self.db.ban_user(target_id, user_id, "3 warnings - auto ban")
                            await update.message.reply_text(f"🚫 *User {target_id} automatically banned!*", parse_mode=ParseMode.MARKDOWN)
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!")
            
            elif session.pending_effect == "unban":
                try:
                    target_id = int(text.strip())
                    self.db.unban_user(target_id, user_id)
                    self.db.unmute_user(target_id, user_id)
                    await update.message.reply_text(f"✅ *User {target_id} unbanned/unmuted!*", parse_mode=ParseMode.MARKDOWN)
                    try:
                        await context.bot.send_message(target_id, "✅ *You have been unbanned!*", parse_mode=ParseMode.MARKDOWN)
                    except:
                        pass
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!")
            
            elif session.pending_effect == "give_premium":
                parts = text.split()
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        days = int(parts[1])
                        self.db.give_premium(target_id, days, user_id)
                        await update.message.reply_text(f"✅ *Premium granted to {target_id} for {days} days!*", parse_mode=ParseMode.MARKDOWN)
                        try:
                            await context.bot.send_message(target_id, f"🎉 *You have been granted premium access for {days} days!* 🎉", parse_mode=ParseMode.MARKDOWN)
                        except:
                            pass
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or days!")
            
            elif session.pending_effect == "add_credits":
                parts = text.split()
                if len(parts) >= 2:
                    try:
                        target_id = int(parts[0])
                        amount = int(parts[1])
                        self.db.add_credits(target_id, amount, user_id)
                        await update.message.reply_text(f"✅ *Added {amount} credits to {target_id}!*", parse_mode=ParseMode.MARKDOWN)
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID or amount!")
            
            elif session.pending_effect == "reset_user":
                try:
                    target_id = int(text.strip())
                    with self.db.get_connection() as conn:
                        conn.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM verification WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM edit_history WHERE user_id = ?", (target_id,))
                        conn.execute("DELETE FROM warnings WHERE user_id = ?", (target_id,))
                    await update.message.reply_text(f"✅ *User {target_id} data reset!*", parse_mode=ParseMode.MARKDOWN)
                except ValueError:
                    await update.message.reply_text("❌ Invalid user ID!")
            
            elif session.pending_effect == "auto_response":
                if text.startswith("add "):
                    parts = text[4:].split(": ", 1)
                    if len(parts) == 2:
                        keyword, response = parts
                        self.db.add_auto_response(keyword, response, user_id)
                        await update.message.reply_text(f"✅ *Auto response added!*\nKeyword: {keyword}", parse_mode=ParseMode.MARKDOWN)
                elif text.startswith("remove "):
                    keyword = text[7:]
                    self.db.remove_auto_response(keyword, user_id)
                    await update.message.reply_text(f"✅ *Auto response removed!*\nKeyword: {keyword}", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Invalid format! Use: `add keyword: response` or `remove keyword`", parse_mode=ParseMode.MARKDOWN)
            
            session.pending_effect = None
            session.state = UserState.VERIFIED
            return
        
        # Handle scheduled announcement
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
                        await update.message.reply_text(f"✅ *Message scheduled for {schedule_time.strftime('%Y-%m-%d %H:%M')}!*", parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text("❌ Schedule time must be in the future!", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Invalid format! Use: `MM/DD HH:MM Your message`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)
            session.state = UserState.VERIFIED
            return
        
        # Handle resize dimensions
        if session.state == UserState.AWAITING_RESIZE_DIMS:
            try:
                parts = text.split()
                if len(parts) == 2:
                    width, height = int(parts[0]), int(parts[1])
                    img_path = session.temp_file_path
                    if img_path and os.path.exists(img_path):
                        await self._process_resize(update, context, Path(img_path), user_id, width, height)
                    else:
                        await update.message.reply_text("❌ No image found. Please try again.")
                else:
                    await update.message.reply_text("❌ Send as: `width height`", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid numbers!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle rotate angle
        if session.state == UserState.AWAITING_ROTATE_ANGLE:
            try:
                angle = int(text)
                img_path = session.temp_file_path
                if img_path and os.path.exists(img_path):
                    await self._process_rotate(update, context, Path(img_path), user_id, angle)
                else:
                    await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid angle!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle crop coordinates
        if session.state == UserState.AWAITING_CROP_COORDS:
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
        
        # Handle color adjustments
        if session.state == UserState.AWAITING_COLOR_ADJUST:
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
        
        # Handle text for watermark/text
        if session.state == UserState.AWAITING_TEXT_CONTENT:
            img_path = session.temp_file_path
            if img_path and os.path.exists(img_path):
                if session.pending_effect == "add_text":
                    await self._process_add_text(update, context, Path(img_path), user_id, text)
                elif session.pending_effect == "add_watermark":
                    await self._process_add_watermark(update, context, Path(img_path), user_id, text)
                elif session.pending_effect == "video_watermark":
                    await self._process_video_watermark(update, context, Path(img_path), user_id, text)
            else:
                await update.message.reply_text("❌ No file found.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle trim times
        if session.state == UserState.AWAITING_TRIM_TIMES:
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
        
        # Handle speed factor
        if session.state == UserState.AWAITING_SPEED_FACTOR:
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
        
        # Handle merge/collage completion
        if session.state == UserState.AWAITING_MERGE_FILES:
            if text.lower() == 'done':
                if session.pending_effect == "merge_videos":
                    if len(session.merge_files) >= 2:
                        await self._process_merge_videos(update, context, session.merge_files, user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 videos to merge!", parse_mode=ParseMode.MARKDOWN)
                elif session.pending_effect == "collage":
                    if len(session.batch_files) >= 2:
                        await self._process_collage(update, context, session.batch_files, user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 images for collage!", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Send files or type 'done' to finish.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # CAPTCHA
        if session.state == UserState.AWAITING_CAPTCHA:
            if text == session.captcha_code:
                self.db.verify_user(user_id, "captcha")
                session.state = UserState.VERIFIED
                await update.message.reply_text("✅ *Verification successful!*", parse_mode=ParseMode.MARKDOWN)
                await self._send_main_menu(update, update.effective_user)
            else:
                session.captcha_attempts += 1
                if session.captcha_attempts >= MAX_CAPTCHA_ATTEMPTS:
                    await update.message.reply_text("❌ *Verification failed!* Use /start to try again.", parse_mode=ParseMode.MARKDOWN)
                    del self.sessions[user_id]
                else:
                    await update.message.reply_text(f"❌ *Incorrect!* Attempts left: {MAX_CAPTCHA_ATTEMPTS - session.captcha_attempts}", parse_mode=ParseMode.MARKDOWN)
    
    async def _process_code_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE, code: str, language: str, user_id: int):
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
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error formatting code:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            session = self.get_session(user_id)
            session.state = UserState.VERIFIED
            session.code_language = None
    
    async def _process_add_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user_id: int):
        """Process adding a custom command"""
        # Format: /addcmd name type language? | content
        # Or from text: addcmd name type language? | content
        text = text.replace('/addcmd', '').strip()
        
        parts = text.split('|', 1)
        if len(parts) != 2:
            await update.message.reply_text("❌ Invalid format! Use: `name type language? | content`", parse_mode=ParseMode.MARKDOWN)
            return
        
        cmd_parts = parts[0].strip().split()
        content = parts[1].strip()
        
        if len(cmd_parts) < 2:
            await update.message.reply_text("❌ Invalid format! Need command name and type.", parse_mode=ParseMode.MARKDOWN)
            return
        
        cmd_name = cmd_parts[0].lower()
        cmd_type = cmd_parts[1].lower()
        language = cmd_parts[2] if len(cmd_parts) > 2 else None
        
        if cmd_type not in ['text', 'code', 'photo', 'video']:
            await update.message.reply_text("❌ Type must be: text, code, photo, or video", parse_mode=ParseMode.MARKDOWN)
            return
        
        if self.db.add_custom_command(cmd_name, cmd_type, content, language, user_id):
            await update.message.reply_text(
                f"✅ Custom command `/{cmd_name}` added!\n"
                f"Type: {cmd_type}\n"
                f"Use with: /customcmd {cmd_name}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Failed to add custom command.", parse_mode=ParseMode.MARKDOWN)
    
    async def _process_resize(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, width: int, height: int):
        """Process image resize"""
        processing_msg = await update.message.reply_text("📐 *Resizing...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            resized = self.image_processor.resize(img, width, height)
            output_path = TEMP_DIR / f"resized_{user_id}_{datetime.now().timestamp()}.jpg"
            resized.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Resized to {width}x{height}!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, angle: int):
        """Process image rotate"""
        processing_msg = await update.message.reply_text("🔄 *Rotating...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            rotated = self.image_processor.rotate(img, angle)
            output_path = TEMP_DIR / f"rotated_{user_id}_{datetime.now().timestamp()}.jpg"
            rotated.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Rotated {angle}°!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, left: int, top: int, right: int, bottom: int):
        """Process image crop"""
        processing_msg = await update.message.reply_text("✂️ *Cropping...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            cropped = self.image_processor.crop(img, left, top, right, bottom)
            output_path = TEMP_DIR / f"cropped_{user_id}_{datetime.now().timestamp()}.jpg"
            cropped.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Cropped!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_color_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, adjustment: str, factor: float):
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
            adjusted.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *{adjustment.title()} adjusted!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_add_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        """Process adding text to image"""
        processing_msg = await update.message.reply_text("📝 *Adding text...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            position = (img.width // 2 - 100, img.height - 50)
            with_text = self.image_processor.add_text(img, text, position, font_size=40)
            output_path = TEMP_DIR / f"text_{user_id}_{datetime.now().timestamp()}.jpg"
            with_text.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Text added: \"{text[:30]}\"*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_add_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        """Process adding watermark to image"""
        processing_msg = await update.message.reply_text("💧 *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            img = Image.open(img_path)
            watermarked = self.image_processor.add_watermark(img, text)
            output_path = TEMP_DIR / f"watermarked_{user_id}_{datetime.now().timestamp()}.jpg"
            watermarked.save(output_path, quality=95)
            with open(output_path, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), caption="✅ *Watermark added!*", reply_markup=KeyboardBuilder.get_image_menu())
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
    
    async def _process_trim_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, start: float, end: float):
        """Process video trim"""
        processing_msg = await update.message.reply_text("✂️ *Trimming video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"trimmed_{user_id}_{datetime.now().timestamp()}.mp4"
            success, result = self.video_processor.trim(str(video_path), start, end, str(output_path))
            if success:
                if output_path.stat().st_size > 50 * 1024 * 1024:
                    compressed_path = TEMP_DIR / f"compressed_{user_id}_{datetime.now().timestamp()}.mp4"
                    clip = VideoFileClip(str(output_path))
                    compressed = clip.resize(height=720)
                    compressed.write_videofile(str(compressed_path), codec='libx264', audio_codec='aac')
                    compressed.close()
                    clip.close()
                    output_path = compressed_path
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption=f"✅ *Trimmed from {start}s to {end}s!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def _process_speed_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, factor: float):
        """Process video speed change"""
        processing_msg = await update.message.reply_text(f"⚡ *Changing speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"speed_{user_id}_{datetime.now().timestamp()}.mp4"
            success, result = self.video_processor.change_speed(str(video_path), factor, str(output_path))
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption=f"✅ *Speed changed to {factor}x!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def _process_merge_videos(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_paths: List[str], user_id: int):
        """Process video merge"""
        processing_msg = await update.message.reply_text("🔗 *Merging videos...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"merged_{user_id}_{datetime.now().timestamp()}.mp4"
            success, result = self.video_processor.merge_videos(video_paths, str(output_path))
            if success:
                if output_path.stat().st_size > 50 * 1024 * 1024:
                    compressed_path = TEMP_DIR / f"compressed_{user_id}_{datetime.now().timestamp()}.mp4"
                    clip = VideoFileClip(str(output_path))
                    compressed = clip.resize(height=720)
                    compressed.write_videofile(str(compressed_path), codec='libx264', audio_codec='aac')
                    compressed.close()
                    clip.close()
                    output_path = compressed_path
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption="✅ *Videos merged!*", reply_markup=KeyboardBuilder.get_video_menu())
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
    
    async def _process_video_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, text: str):
        """Process video watermark"""
        processing_msg = await update.message.reply_text("🏷️ *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            output_path = TEMP_DIR / f"watermarked_{user_id}_{datetime.now().timestamp()}.mp4"
            success, result = self.video_processor.add_watermark(str(video_path), text, str(output_path))
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption="✅ *Watermark added!*", reply_markup=KeyboardBuilder.get_video_menu())
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

# ==================== Main Entry Point ====================

async def main():
    """Main entry point"""
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

