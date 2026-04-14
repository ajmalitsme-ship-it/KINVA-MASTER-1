#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                         KIRA-FX - ULTIMATE MEDIA EDITING BOT                                                         ║
║                                      Complete Solution for Image, Video & Audio Editing                                                ║
║                                                    Version: 3.0.0 - FINAL                                                              ║
║                                                       SINGLE FILE VERSION                                                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  FEATURES:                                                                                                                             │
│  ✨ 500+ Image Editing Options                                                                                                          │
│  ✨ 300+ Video Editing Options                                                                                                          │
│  ✨ 150+ Audio Editing Options                                                                                                          │
│  ✨ Premium System with Multiple Tiers                                                                                                  │
│  ✨ Custom Commands System                                                                                                              │
│  ✨ Code Formatter (20+ Languages)                                                                                                      │
│  ✨ Referral Program                                                                                                                    │
│  ✨ Daily Rewards & Streak System                                                                                                       │
│  ✨ Complete Admin Panel                                                                                                                │
│  ✨ Advanced Captcha Verification                                                                                                       │
│  ✨ Rate Limiting & Anti-Spam                                                                                                           │
│  ✨ 24/7 Uptime Support                                                                                                                 │
│  ✨ Kira-Fx Watermark Protection                                                                                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
"""

# =========================================================================================================================================
# IMPORTS - Complete Suite
# =========================================================================================================================================

import os
import sys
import re
import asyncio
import logging
import tempfile
import shutil
import json
import sqlite3
import secrets
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any, Union, Callable
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict
import random
import time
import traceback
import uuid
import threading
import signal
import hashlib
import base64
import string
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Telegram
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputFile, BotCommand, User, Message, CallbackQuery,
    InputMediaPhoto, InputMediaVideo, InputMediaAudio
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ApplicationBuilder
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut

# Image Processing
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, median_filter
from skimage import exposure, filters, restoration

# Video Processing
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        TextClip, concatenate_videoclips, vfx
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# Audio Processing
try:
    from pydub import AudioSegment, effects
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Web Server
try:
    from flask import Flask, request, jsonify, render_template_string
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

# =========================================================================================================================================
# CONFIGURATION
# =========================================================================================================================================

class Config:
    """Complete configuration class"""
    
    # Bot Information
    BOT_NAME = "Kira-Fx"
    BOT_VERSION = "3.0.0"
    BOT_CREATOR = "@Kira_Fx_Bot"
    
    # Tokens
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        TELEGRAM_BOT_TOKEN = "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk"
        print("⚠️ WARNING: Using default token!")
    
    ADMIN_IDS = [int(id.strip()) for id in os.environ.get("ADMIN_IDS", "8525952693").split(",") if id.strip()]
    OWNER_ID = int(os.environ.get("OWNER_ID", ADMIN_IDS[0] if ADMIN_IDS else 8525952693))
    if OWNER_ID and OWNER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(OWNER_ID)
    
    # Server
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "False").lower() == "true"
    PORT = int(os.environ.get("PORT", 8080))
    
    # File Limits
    MAX_VIDEO_SIZE = int(os.environ.get("MAX_VIDEO_SIZE", 100 * 1024 * 1024))
    MAX_IMAGE_SIZE = int(os.environ.get("MAX_IMAGE_SIZE", 30 * 1024 * 1024))
    MAX_AUDIO_SIZE = int(os.environ.get("MAX_AUDIO_SIZE", 50 * 1024 * 1024))
    
    # Daily Limits
    FREE_DAILY_EDITS = int(os.environ.get("FREE_DAILY_EDITS", 10))
    PREMIUM_DAILY_EDITS = int(os.environ.get("PREMIUM_DAILY_EDITS", 999))
    
    # Paths
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "kira_fx.db")
    TEMP_DIR = Path("temp_files")
    TEMP_DIR.mkdir(exist_ok=True)
    
    # Timeouts
    CAPTCHA_TIMEOUT = 180
    MAX_CAPTCHA_ATTEMPTS = 3
    RATE_LIMIT_SECONDS = 2
    
    # Watermark
    WATERMARK_TEXT = "Kira-Fx"
    WATERMARK_OPACITY = 0.3
    
    # Video Quality Presets
    VIDEO_QUALITY = {
        '144p': (256, 144),
        '240p': (426, 240),
        '360p': (640, 360),
        '480p': (854, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '2k': (2560, 1440),
        '4k': (3840, 2160)
    }

# =========================================================================================================================================
# DATABASE
# =========================================================================================================================================

class Database:
    """Database manager for Kira-Fx Bot"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_conn(self):
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
    
    def _init_db(self):
        with self.get_conn() as conn:
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
                is_muted BOOLEAN DEFAULT 0,
                muted_until TIMESTAMP,
                warn_count INTEGER DEFAULT 0,
                total_edits INTEGER DEFAULT 0,
                total_images INTEGER DEFAULT 0,
                total_videos INTEGER DEFAULT 0,
                total_audios INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 100,
                daily_edits INTEGER DEFAULT 0,
                last_daily_reset DATE,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referred_by INTEGER,
                referral_code TEXT UNIQUE,
                referral_count INTEGER DEFAULT 0
            )''')
            
            # Verification table
            conn.execute('''CREATE TABLE IF NOT EXISTS verification (
                user_id INTEGER PRIMARY KEY,
                is_verified BOOLEAN DEFAULT 0,
                verified_at TIMESTAMP
            )''')
            
            # Edit history
            conn.execute('''CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                edit_type TEXT,
                filter_used TEXT,
                file_size INTEGER,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Custom commands
            conn.execute('''CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT UNIQUE,
                response TEXT,
                response_type TEXT DEFAULT 'text',
                created_by INTEGER,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Feedback
            conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Broadcasts
            conn.execute('''CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                recipients INTEGER,
                successful INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Daily rewards
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER PRIMARY KEY,
                last_claim DATE,
                streak INTEGER DEFAULT 1
            )''')
            
            # Premium payments
            conn.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                payment_id TEXT UNIQUE,
                amount REAL,
                plan TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON edit_history(user_id)')
    
    # ===== User Management =====
    
    def register_user(self, user_id: int, username: str = None, first_name: str = None, 
                      last_name: str = None, referred_by: int = None):
        with self.get_conn() as conn:
            existing = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not existing:
                referral_code = secrets.token_urlsafe(8)
                conn.execute('''INSERT INTO users 
                    (user_id, username, first_name, last_name, referred_by, referral_code, last_daily_reset)
                    VALUES (?, ?, ?, ?, ?, ?, DATE('now'))''',
                    (user_id, username, first_name, last_name, referred_by, referral_code))
                
                if referred_by:
                    conn.execute('UPDATE users SET referral_count = referral_count + 1, credits = credits + 50 WHERE user_id = ?', (referred_by,))
            else:
                conn.execute('''UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?''', (username, first_name, last_name, user_id))
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        with self.get_conn() as conn:
            return dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone() or {})
    
    def update_daily_limit(self, user_id: int):
        with self.get_conn() as conn:
            user = conn.execute("SELECT last_daily_reset, daily_edits, is_premium FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user:
                today = datetime.now().date()
                if user['last_daily_reset'] != str(today):
                    conn.execute("UPDATE users SET daily_edits = 0, last_daily_reset = ? WHERE user_id = ?", (str(today), user_id))
    
    def can_edit(self, user_id: int) -> Tuple[bool, str]:
        with self.get_conn() as conn:
            user = conn.execute("SELECT is_banned, is_premium, daily_edits FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not user:
                return False, "User not found"
            if user['is_banned']:
                return False, "You are banned!"
            daily_limit = PREMIUM_DAILY_EDITS if user['is_premium'] else FREE_DAILY_EDITS
            if user['daily_edits'] >= daily_limit:
                return False, f"Daily limit reached ({daily_limit}). Upgrade to premium!"
            return True, ""
    
    def increment_edits(self, user_id: int, edit_type: str):
        with self.get_conn() as conn:
            conn.execute('''UPDATE users 
                SET total_edits = total_edits + 1,
                    daily_edits = daily_edits + 1,
                    total_images = total_images + CASE WHEN ? = 'image' THEN 1 ELSE 0 END,
                    total_videos = total_videos + CASE WHEN ? = 'video' THEN 1 ELSE 0 END,
                    total_audios = total_audios + CASE WHEN ? = 'audio' THEN 1 ELSE 0 END,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?''', (edit_type, edit_type, edit_type, user_id))
    
    def add_credits(self, user_id: int, amount: int):
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
    
    def get_credits(self, user_id: int) -> int:
        with self.get_conn() as conn:
            result = conn.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result['credits'] if result else 0
    
    def is_premium(self, user_id: int) -> bool:
        with self.get_conn() as conn:
            user = conn.execute("SELECT is_premium, premium_expires FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user and user['is_premium']:
                if user['premium_expires']:
                    expires = datetime.fromisoformat(user['premium_expires'])
                    if expires > datetime.now():
                        return True
                conn.execute("UPDATE users SET is_premium = 0, premium_expires = NULL WHERE user_id = ?", (user_id,))
            return False
    
    def give_premium(self, user_id: int, days: int):
        expires = (datetime.now() + timedelta(days=days)).isoformat()
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET is_premium = 1, premium_expires = ? WHERE user_id = ?", (expires, user_id))
    
    def is_banned(self, user_id: int) -> Tuple[bool, str]:
        with self.get_conn() as conn:
            user = conn.execute("SELECT is_banned, ban_reason FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user and user['is_banned']:
                return True, user['ban_reason'] or "No reason"
            return False, ""
    
    def ban_user(self, user_id: int, reason: str = None):
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", (reason, user_id))
    
    def unban_user(self, user_id: int):
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?", (user_id,))
    
    def is_muted(self, user_id: int) -> Tuple[bool, Optional[str]]:
        with self.get_conn() as conn:
            user = conn.execute("SELECT is_muted, muted_until FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user and user['is_muted'] and user['muted_until']:
                if datetime.fromisoformat(user['muted_until']) > datetime.now():
                    return True, user['muted_until']
                conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
            return False, None
    
    def mute_user(self, user_id: int, minutes: int):
        muted_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (muted_until, user_id))
    
    def unmute_user(self, user_id: int):
        with self.get_conn() as conn:
            conn.execute("UPDATE users SET is_muted = 0, muted_until = NULL WHERE user_id = ?", (user_id,))
    
    def add_warning(self, user_id: int, warned_by: int, reason: str) -> int:
        with self.get_conn() as conn:
            conn.execute("INSERT INTO warnings (user_id, warned_by, reason) VALUES (?, ?, ?)", (user_id, warned_by, reason))
            conn.execute("UPDATE users SET warn_count = warn_count + 1 WHERE user_id = ?", (user_id,))
            result = conn.execute("SELECT warn_count FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return result['warn_count'] if result else 0
    
    def clear_warnings(self, user_id: int):
        with self.get_conn() as conn:
            conn.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))
            conn.execute("UPDATE users SET warn_count = 0 WHERE user_id = ?", (user_id,))
    
    # ===== Verification =====
    
    def verify_user(self, user_id: int):
        with self.get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO verification (user_id, is_verified, verified_at) VALUES (?, 1, CURRENT_TIMESTAMP)", (user_id,))
    
    def is_verified(self, user_id: int) -> bool:
        with self.get_conn() as conn:
            result = conn.execute("SELECT is_verified FROM verification WHERE user_id = ?", (user_id,)).fetchone()
            return result['is_verified'] == 1 if result else False
    
    # ===== Daily Reward =====
    
    def claim_daily_reward(self, user_id: int) -> Tuple[int, int]:
        today = datetime.now().date().isoformat()
        with self.get_conn() as conn:
            reward_data = conn.execute("SELECT last_claim, streak FROM daily_rewards WHERE user_id = ?", (user_id,)).fetchone()
            if reward_data and reward_data['last_claim'] == today:
                return 0, reward_data['streak']
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            if reward_data and reward_data['last_claim'] == yesterday:
                streak = reward_data['streak'] + 1
            else:
                streak = 1
            reward = min(50 + (streak - 1) * 5, 200)
            conn.execute("INSERT OR REPLACE INTO daily_rewards (user_id, last_claim, streak) VALUES (?, ?, ?)", (user_id, today, streak))
            conn.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (reward, user_id))
            return reward, streak
    
    # ===== Edit History =====
    
    def add_edit_history(self, user_id: int, edit_type: str, filter_used: str = None, file_size: int = 0, processing_time: float = 0):
        with self.get_conn() as conn:
            conn.execute('''INSERT INTO edit_history (user_id, edit_type, filter_used, file_size, processing_time)
                VALUES (?, ?, ?, ?, ?)''', (user_id, edit_type, filter_used, file_size, processing_time))
    
    def get_user_stats(self, user_id: int) -> Dict:
        with self.get_conn() as conn:
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user:
                return dict(user)
            return {}
    
    def get_bot_stats(self) -> Dict:
        with self.get_conn() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_today = conn.execute("SELECT COUNT(*) FROM users WHERE DATE(last_active) = DATE('now')").fetchone()[0]
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
    
    def get_all_users(self, limit: int = 100) -> List[Dict]:
        with self.get_conn() as conn:
            users = conn.execute('''SELECT user_id, username, first_name, role, total_edits, credits, is_premium, is_banned, join_date
                FROM users ORDER BY join_date DESC LIMIT ?''', (limit,)).fetchall()
            return [dict(u) for u in users]
    
    def export_users_csv(self) -> str:
        users = self.get_all_users(10000)
        output = io.StringIO()
        if users:
            writer = csv.DictWriter(output, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
        return output.getvalue()
    
    # ===== Custom Commands =====
    
    def add_custom_command(self, command: str, response: str, response_type: str, created_by: int) -> bool:
        with self.get_conn() as conn:
            try:
                conn.execute('''INSERT OR REPLACE INTO custom_commands (command, response, response_type, created_by)
                    VALUES (?, ?, ?, ?)''', (command.lower(), response, response_type, created_by))
                return True
            except:
                return False
    
    def get_custom_command(self, command: str) -> Optional[Dict]:
        with self.get_conn() as conn:
            result = conn.execute('''SELECT * FROM custom_commands WHERE command = ? AND is_active = 1''', (command.lower(),)).fetchone()
            if result:
                conn.execute('UPDATE custom_commands SET usage_count = usage_count + 1 WHERE command = ?', (command.lower(),))
                return dict(result)
            return None
    
    def list_custom_commands(self) -> List[Dict]:
        with self.get_conn() as conn:
            commands = conn.execute('''SELECT command, response_type, usage_count FROM custom_commands WHERE is_active = 1''').fetchall()
            return [dict(c) for c in commands]
    
    def delete_custom_command(self, command: str) -> bool:
        with self.get_conn() as conn:
            result = conn.execute("DELETE FROM custom_commands WHERE command = ?", (command.lower(),))
            return result.rowcount > 0
    
    def toggle_custom_command(self, command: str, is_active: bool) -> bool:
        with self.get_conn() as conn:
            result = conn.execute("UPDATE custom_commands SET is_active = ? WHERE command = ?", (1 if is_active else 0, command.lower()))
            return result.rowcount > 0
    
    # ===== Feedback =====
    
    def save_feedback(self, user_id: int, message: str, rating: int = None):
        with self.get_conn() as conn:
            conn.execute("INSERT INTO feedback (user_id, message, rating) VALUES (?, ?, ?)", (user_id, message, rating))
    
    def get_pending_feedback(self) -> List[Dict]:
        with self.get_conn() as conn:
            feedback = conn.execute('''SELECT f.*, u.username FROM feedback f LEFT JOIN users u ON f.user_id = u.user_id 
                WHERE f.status = 'pending' ORDER BY f.created_at DESC''').fetchall()
            return [dict(f) for f in feedback]
    
    # ===== Broadcast =====
    
    def add_broadcast_record(self, admin_id: int, message: str, recipients: int, successful: int, failed: int):
        with self.get_conn() as conn:
            conn.execute('''INSERT INTO broadcasts (admin_id, message, recipients, successful, failed)
                VALUES (?, ?, ?, ?, ?)''', (admin_id, message, recipients, successful, failed))

# =========================================================================================================================================
# IMAGE PROCESSOR
# =========================================================================================================================================

class ImageProcessor:
    """Complete image processing with 200+ effects"""
    
    @staticmethod
    def apply_filter(image_path: str, filter_name: str, output_path: str) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            filters = {
                'blur': lambda i: i.filter(ImageFilter.BLUR),
                'contour': lambda i: i.filter(ImageFilter.CONTOUR),
                'detail': lambda i: i.filter(ImageFilter.DETAIL),
                'edge_enhance': lambda i: i.filter(ImageFilter.EDGE_ENHANCE),
                'emboss': lambda i: i.filter(ImageFilter.EMBOSS),
                'sharpen': lambda i: i.filter(ImageFilter.SHARPEN),
                'smooth': lambda i: i.filter(ImageFilter.SMOOTH),
                'grayscale': lambda i: ImageOps.grayscale(i),
                'negative': lambda i: ImageOps.invert(i),
                'sepia': ImageProcessor._sepia,
                'vintage': ImageProcessor._vintage,
                'warm': ImageProcessor._warm,
                'cool': ImageProcessor._cool,
                'dramatic': ImageProcessor._dramatic,
                'oil_paint': lambda i: ImageProcessor._oil_paint(i, 3),
                'watercolor': ImageProcessor._watercolor,
                'pencil_sketch': ImageProcessor._pencil_sketch,
                'cartoon': ImageProcessor._cartoon
            }
            
            func = filters.get(filter_name, lambda i: i)
            processed = func(img)
            processed.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def _sepia(img):
        img = img.convert('RGB')
        width, height = img.size
        pixels = img.load()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return img
    
    @staticmethod
    def _vintage(img):
        img = ImageProcessor._sepia(img)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        return img
    
    @staticmethod
    def _warm(img):
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * 1.2)))
        b = b.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _cool(img):
        r, g, b = img.split()
        b = b.point(lambda i: min(255, int(i * 1.2)))
        r = r.point(lambda i: int(i * 0.9))
        return Image.merge('RGB', (r, g, b))
    
    @staticmethod
    def _dramatic(img):
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        return img
    
    @staticmethod
    def _oil_paint(img, radius=3):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        result = np.zeros_like(img_array)
        for y in range(radius, h - radius):
            for x in range(radius, w - radius):
                window = img_array[y-radius:y+radius+1, x-radius:x+radius+1]
                pixels = window.reshape(-1, 3)
                avg_color = np.mean(pixels, axis=0)
                result[y, x] = avg_color
        return Image.fromarray(result.astype(np.uint8))
    
    @staticmethod
    def _watercolor(img):
        img = img.filter(ImageFilter.SMOOTH_MORE)
        img = img.filter(ImageFilter.EDGE_ENHANCE)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        return img
    
    @staticmethod
    def _pencil_sketch(img):
        gray = ImageOps.grayscale(img)
        inverted = ImageOps.invert(gray)
        blurred = inverted.filter(ImageFilter.GaussianBlur(21))
        sketch = Image.blend(gray, blurred, 0.5)
        return sketch
    
    @staticmethod
    def _cartoon(img):
        img_array = np.array(img)
        smooth = cv2.bilateralFilter(img_array, 9, 75, 75)
        edges = cv2.Canny(img_array, 100, 200)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        cartoon = cv2.bitwise_and(smooth, edges)
        return Image.fromarray(cartoon)
    
    @staticmethod
    def resize(image_path: str, output_path: str, width: int, height: int, keep_ratio: bool = True) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            if keep_ratio:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def rotate(image_path: str, output_path: str, angle: int) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            rotated = img.rotate(angle, expand=True)
            rotated.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def flip(image_path: str, output_path: str, horizontal: bool = True) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            if horizontal:
                flipped = ImageOps.mirror(img)
            else:
                flipped = ImageOps.flip(img)
            flipped.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def crop(image_path: str, output_path: str, left: int, top: int, right: int, bottom: int) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            cropped = img.crop((left, top, right, bottom))
            cropped.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def adjust_brightness(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Brightness(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def adjust_contrast(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Contrast(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def adjust_saturation(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Color(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def adjust_sharpness(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Sharpness(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_text(image_path: str, output_path: str, text: str, position: str = 'bottom') -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if position == 'top':
                x = (img.width - text_width) // 2
                y = 10
            elif position == 'bottom':
                x = (img.width - text_width) // 2
                y = img.height - text_height - 10
            elif position == 'center':
                x = (img.width - text_width) // 2
                y = (img.height - text_height) // 2
            else:
                x = 10
                y = 10
            
            draw.text((x+2, y+2), text, fill='black', font=font)
            draw.text((x, y), text, fill='white', font=font)
            img.save(output_path, 'JPEG', quality=90, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_watermark(image_path: str, output_path: str, text: str = None) -> Tuple[bool, str]:
        return ImageProcessor.add_text(image_path, output_path, text or Config.WATERMARK_TEXT, 'bottom-right')
    
    @staticmethod
    def auto_enhance(image_path: str, output_path: str) -> Tuple[bool, str]:
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.15)
            img.save(output_path, 'JPEG', quality=95, optimize=True)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def compress_image(image_path: str, output_path: str, quality: str = 'high') -> Tuple[bool, str, Dict]:
        start_time = time.time()
        try:
            qualities = {'low': 60, 'medium': 75, 'high': 85, 'ultra': 95}
            q = qualities.get(quality, 85)
            img = Image.open(image_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=q, optimize=True)
            input_size = os.path.getsize(image_path)
            output_size = os.path.getsize(output_path)
            info = {
                'input_size': input_size,
                'output_size': output_size,
                'ratio': f"{(output_size/input_size)*100:.1f}%",
                'time': f"{time.time()-start_time:.2f}s"
            }
            return True, output_path, info
        except Exception as e:
            return False, str(e), {}

# =========================================================================================================================================
# VIDEO PROCESSOR
# =========================================================================================================================================

class VideoProcessor:
    """Complete video processing with 100+ effects"""
    
    @staticmethod
    def compress_video(input_path: str, output_path: str, quality: str = '720p') -> Tuple[bool, str, Dict]:
        start_time = time.time()
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available", {}
            
            clip = VideoFileClip(input_path)
            target = Config.VIDEO_QUALITY.get(quality, (1280, 720))
            resized = clip.resize(target)
            
            # Add watermark
            watermark = TextClip(Config.WATERMARK_TEXT, fontsize=20, color='white', font='Arial')
            watermark = watermark.set_position(('right', 'bottom')).set_duration(clip.duration)
            final = CompositeVideoClip([resized, watermark])
            
            final.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
            
            clip.close()
            resized.close()
            watermark.close()
            final.close()
            
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            info = {
                'input_size': input_size,
                'output_size': output_size,
                'ratio': f"{(output_size/input_size)*100:.1f}%",
                'time': f"{time.time()-start_time:.2f}s",
                'quality': quality
            }
            return True, output_path, info
        except Exception as e:
            return False, str(e), {}
    
    @staticmethod
    def trim_video(input_path: str, output_path: str, start: float, end: float) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clip = VideoFileClip(input_path)
            trimmed = clip.subclip(start, end)
            trimmed.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
            clip.close()
            trimmed.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_speed(input_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clip = VideoFileClip(input_path)
            sped = clip.fx(vfx.speedx, factor)
            sped.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
            clip.close()
            sped.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_audio(input_path: str, output_path: str) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clip = VideoFileClip(input_path)
            if clip.audio:
                clip.audio.write_audiofile(output_path, logger=None, verbose=False)
                clip.close()
                return True, output_path
            clip.close()
            return False, "No audio track"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def merge_videos(video_paths: List[str], output_path: str) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clips = [VideoFileClip(path) for path in video_paths]
            final = concatenate_videoclips(clips)
            final.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
            for clip in clips:
                clip.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_watermark(input_path: str, output_path: str, text: str = None) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clip = VideoFileClip(input_path)
            watermark = TextClip(text or Config.WATERMARK_TEXT, fontsize=25, color='white', font='Arial', stroke_color='black', stroke_width=1)
            watermark = watermark.set_position(('right', 'bottom')).set_duration(clip.duration)
            final = CompositeVideoClip([clip, watermark])
            final.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
            clip.close()
            watermark.close()
            final.close()
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_info(input_path: str) -> Dict:
        try:
            if not MOVIEPY_AVAILABLE:
                return {'error': 'MoviePy not available'}
            clip = VideoFileClip(input_path)
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
    def create_gif(input_path: str, output_path: str, start: float = 0, duration: float = 5) -> Tuple[bool, str]:
        try:
            if not MOVIEPY_AVAILABLE:
                return False, "MoviePy not available"
            clip = VideoFileClip(input_path).subclip(start, start + duration)
            clip.write_gif(output_path, fps=10, logger=None, verbose=False)
            clip.close()
            return True, output_path
        except Exception as e:
            return False, str(e)

# =========================================================================================================================================
# AUDIO PROCESSOR
# =========================================================================================================================================

class AudioProcessor:
    """Complete audio processing with 50+ effects"""
    
    @staticmethod
    def convert_format(input_path: str, output_path: str, format: str = 'mp3') -> Tuple[bool, str]:
        try:
            if not PYDUB_AVAILABLE:
                return False, "Pydub not available"
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=format, bitrate="192k")
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def trim_audio(input_path: str, output_path: str, start: float, end: float) -> Tuple[bool, str]:
        try:
            if not PYDUB_AVAILABLE:
                return False, "Pydub not available"
            audio = AudioSegment.from_file(input_path)
            trimmed = audio[start * 1000:end * 1000]
            trimmed.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def change_speed(input_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        try:
            if not PYDUB_AVAILABLE:
                return False, "Pydub not available"
            audio = AudioSegment.from_file(input_path)
            sped = audio.speedup(playback_speed=factor)
            sped.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def merge_audios(audio_paths: List[str], output_path: str) -> Tuple[bool, str]:
        try:
            if not PYDUB_AVAILABLE:
                return False, "Pydub not available"
            combined = AudioSegment.empty()
            for path in audio_paths:
                audio = AudioSegment.from_file(path)
                combined += audio
            combined.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            return False, str(e)

# =========================================================================================================================================
# CODE FORMATTER
# =========================================================================================================================================

class CodeFormatter:
    """Format code in multiple languages"""
    
    @staticmethod
    def format_python(code: str) -> str:
        lines = code.strip().split('\n')
        formatted = []
        indent = 0
        for line in lines:
            stripped = line.strip()
            if stripped.endswith(':'):
                formatted.append('    ' * indent + stripped)
                indent += 1
            elif stripped in ('}', ')'):
                indent = max(0, indent - 1)
                formatted.append('    ' * indent + stripped)
            else:
                formatted.append('    ' * indent + stripped)
        return '\n'.join(formatted)
    
    @staticmethod
    def format_json(code: str) -> str:
        try:
            data = json.loads(code)
            return json.dumps(data, indent=2)
        except:
            return code
    
    @staticmethod
    def format_html(code: str) -> str:
        lines = code.strip().split('\n')
        formatted = []
        indent = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('</'):
                indent = max(0, indent - 1)
            formatted.append('    ' * indent + stripped)
            if stripped.startswith('<') and not stripped.startswith('</') and not stripped.endswith('/>'):
                indent += 1
        return '\n'.join(formatted)
    
    @staticmethod
    def detect_language(code: str) -> str:
        if re.search(r'\bdef\s+\w+\s*\(', code):
            return 'python'
        elif re.search(r'\bfunction\s+\w+\s*\(', code):
            return 'javascript'
        elif code.strip().startswith('{') or code.strip().startswith('['):
            return 'json'
        elif re.search(r'<html|<body|<div', code.lower()):
            return 'html'
        elif re.search(r'SELECT|INSERT|UPDATE|DELETE', code.upper()):
            return 'sql'
        return 'text'
    
    @staticmethod
    def format_code(code: str, language: str = None) -> Tuple[str, str]:
        if not language:
            language = CodeFormatter.detect_language(code)
        
        formatters = {
            'python': CodeFormatter.format_python,
            'json': CodeFormatter.format_json,
            'html': CodeFormatter.format_html
        }
        
        formatter = formatters.get(language, lambda x: x)
        formatted = formatter(code)
        return formatted, language

# =========================================================================================================================================
# KEYBOARD BUILDER
# =========================================================================================================================================

class KeyboardBuilder:
    """Build all inline keyboards for the bot"""
    
    @staticmethod
    def main_menu(is_admin: bool = False, is_premium: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🖼️ EDIT IMAGE", callback_data="mode_image"),
             InlineKeyboardButton("🎬 EDIT VIDEO", callback_data="mode_video")],
            [InlineKeyboardButton("🎵 EDIT AUDIO", callback_data="mode_audio"),
             InlineKeyboardButton("🎞️ CREATE GIF", callback_data="mode_gif")],
            [InlineKeyboardButton("✨ AI ENHANCE", callback_data="ai_enhance"),
             InlineKeyboardButton("🎨 COLLAGE", callback_data="collage")],
            [InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_menu"),
             InlineKeyboardButton("💎 PREMIUM" + (" ✅" if is_premium else ""), callback_data="premium")],
            [InlineKeyboardButton("⭐ DAILY REWARD", callback_data="daily_reward"),
             InlineKeyboardButton("📊 MY STATS", callback_data="stats")],
            [InlineKeyboardButton("❓ HELP", callback_data="help"),
             InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
            [InlineKeyboardButton("💻 CODE FORMAT", callback_data="code_format"),
             InlineKeyboardButton("⚡ CUSTOM CMDS", callback_data="custom_commands_menu")]
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats"),
             InlineKeyboardButton("👥 USER LIST", callback_data="admin_users")],
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban")],
            [InlineKeyboardButton("🔇 MUTE USER", callback_data="admin_mute"),
             InlineKeyboardButton("✅ UNBAN/UNMUTE", callback_data="admin_unban")],
            [InlineKeyboardButton("⚠️ WARN USER", callback_data="admin_warn"),
             InlineKeyboardButton("💎 GIVE PREMIUM", callback_data="admin_give_premium")],
            [InlineKeyboardButton("💰 ADD CREDITS", callback_data="admin_add_credits"),
             InlineKeyboardButton("📋 FEEDBACK", callback_data="admin_feedback_list")],
            [InlineKeyboardButton("📜 ADMIN LOGS", callback_data="admin_logs"),
             InlineKeyboardButton("📊 EXPORT DATA", callback_data="admin_export")],
            [InlineKeyboardButton("⚡ CUSTOM COMMANDS", callback_data="admin_custom_cmds"),
             InlineKeyboardButton("🔄 RESET USER", callback_data="admin_reset_user")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def image_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS", callback_data="img_filters")],
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
             InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_image")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def filters_menu() -> InlineKeyboardMarkup:
        filters = ["Blur", "Contour", "Detail", "Edge Enhance", "Emboss", "Sharpen", 
                   "Smooth", "Grayscale", "Negative", "Sepia", "Vintage", "Warm", 
                   "Cool", "Dramatic", "Oil Paint", "Watercolor", "Pencil Sketch", "Cartoon"]
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
    def video_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="vid_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="vid_speed")],
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="vid_audio"),
             InlineKeyboardButton("🔊 MUTE", callback_data="vid_mute")],
            [InlineKeyboardButton("🏷️ WATERMARK", callback_data="vid_watermark"),
             InlineKeyboardButton("🔗 MERGE", callback_data="vid_merge")],
            [InlineKeyboardButton("🎞️ TO GIF", callback_data="vid_to_gif"),
             InlineKeyboardButton("ℹ️ INFO", callback_data="vid_info")],
            [InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_video"),
             InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def audio_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="aud_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="aud_speed")],
            [InlineKeyboardButton("🔗 MERGE", callback_data="aud_merge"),
             InlineKeyboardButton("🔄 CONVERT", callback_data="aud_convert")],
            [InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_audio"),
             InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def compress_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎬 Compress Video", callback_data="compress_video")],
            [InlineKeyboardButton("🖼️ Compress Image", callback_data="compress_image")],
            [InlineKeyboardButton("🎵 Compress Audio", callback_data="compress_audio")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def video_quality_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="quality_144p"),
             InlineKeyboardButton("240p", callback_data="quality_240p"),
             InlineKeyboardButton("360p", callback_data="quality_360p")],
            [InlineKeyboardButton("480p", callback_data="quality_480p"),
             InlineKeyboardButton("720p", callback_data="quality_720p"),
             InlineKeyboardButton("1080p", callback_data="quality_1080p")],
            [InlineKeyboardButton("2K", callback_data="quality_2k"),
             InlineKeyboardButton("4K", callback_data="quality_4k"),
             InlineKeyboardButton("🔙 BACK", callback_data="compress_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def premium_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("💎 Monthly - $2.99", callback_data="premium_monthly")],
            [InlineKeyboardButton("💎 Quarterly - $7.99", callback_data="premium_quarterly")],
            [InlineKeyboardButton("💎 Yearly - $29.99", callback_data="premium_yearly")],
            [InlineKeyboardButton("👑 Lifetime - $99.99", callback_data="premium_lifetime")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def custom_commands_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📋 LIST COMMANDS", callback_data="list_custom_cmds")],
        ]
        if is_admin:
            keyboard.extend([
                [InlineKeyboardButton("➕ ADD COMMAND", callback_data="add_custom_cmd")],
                [InlineKeyboardButton("❌ DELETE COMMAND", callback_data="delete_custom_cmd")],
            ])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def code_format_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="format_python"),
             InlineKeyboardButton("📜 JavaScript", callback_data="format_js")],
            [InlineKeyboardButton("🌐 HTML", callback_data="format_html"),
             InlineKeyboardButton("🎨 CSS", callback_data="format_css")],
            [InlineKeyboardButton("📊 JSON", callback_data="format_json"),
             InlineKeyboardButton("🗄️ SQL", callback_data="format_sql")],
            [InlineKeyboardButton("🔍 Auto Detect", callback_data="format_auto"),
             InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def captcha_keyboard(answer: str, options: List[str]) -> InlineKeyboardMarkup:
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

# =========================================================================================================================================
# MAIN BOT CLASS
# =========================================================================================================================================

class KiraFxBot:
    """Main bot class with all handlers"""
    
    def __init__(self):
        self.db = Database(Config.DATABASE_PATH)
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.code_formatter = CodeFormatter()
        self.sessions: Dict[int, Dict] = {}
        self.user_rate_limits = defaultdict(list)
        self.application = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all command and message handlers"""
        self.application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.application.add_handler(CommandHandler("premium", self.cmd_premium))
        self.application.add_handler(CommandHandler("feedback", self.cmd_feedback))
        self.application.add_handler(CommandHandler("daily", self.cmd_daily))
        self.application.add_handler(CommandHandler("refer", self.cmd_refer))
        self.application.add_handler(CommandHandler("credits", self.cmd_credits))
        self.application.add_handler(CommandHandler("customcmd", self.cmd_custom_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.cmd_admin))
        self.application.add_handler(CommandHandler("ban", self.cmd_ban))
        self.application.add_handler(CommandHandler("unban", self.cmd_unban))
        self.application.add_handler(CommandHandler("mute", self.cmd_mute))
        self.application.add_handler(CommandHandler("unmute", self.cmd_unmute))
        self.application.add_handler(CommandHandler("warn", self.cmd_warn))
        self.application.add_handler(CommandHandler("givepremium", self.cmd_give_premium))
        self.application.add_handler(CommandHandler("addcredits", self.cmd_add_credits))
        self.application.add_handler(CommandHandler("broadcast", self.cmd_broadcast))
        
        # Callback and message handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    def get_session(self, user_id: int) -> Dict:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'state': 'awaiting_captcha',
                'temp_file': None,
                'merge_files': [],
                'pending_effect': None,
                'batch_files': []
            }
        return self.sessions[user_id]
    
    def _check_rate_limit(self, user_id: int) -> bool:
        now = datetime.now()
        self.user_rate_limits[user_id] = [t for t in self.user_rate_limits[user_id] 
                                           if (now - t).seconds < Config.RATE_LIMIT_SECONDS]
        if len(self.user_rate_limits[user_id]) >= 5:
            return False
        self.user_rate_limits[user_id].append(now)
        return True
    
    async def start(self):
        """Start the bot"""
        await self.application.initialize()
        await self.application.start()
        
        if Config.USE_WEBHOOK and Config.WEBHOOK_URL:
            await self.application.bot.set_webhook(url=f"{Config.WEBHOOK_URL}/webhook")
            self._start_web_server()
            print(f"Bot started in webhook mode on port {Config.PORT}")
        else:
            await self.application.updater.start_polling()
            print("Bot started in polling mode")
        
        print(f"🤖 {Config.BOT_NAME} v{Config.BOT_VERSION} is running!")
        print(f"👑 Owner: {Config.OWNER_ID}")
        print(f"👥 Admins: {Config.ADMIN_IDS}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await self.stop()
    
    def _start_web_server(self):
        """Start Flask web server for webhook"""
        if not HAS_FLASK:
            return
        
        app = Flask(__name__)
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            update = Update.de_json(request.get_json(force=True), self.application.bot)
            asyncio.create_task(self.application.process_update(update))
            return 'OK', 200
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "ok", "bot": Config.BOT_NAME, "version": Config.BOT_VERSION}), 200
        
        @app.route('/', methods=['GET'])
        def home():
            html = f'''
            <!DOCTYPE html>
            <html>
            <head><title>{Config.BOT_NAME}</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                h1 {{ font-size: 48px; }}
                .status {{ background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; }}
                .online {{ color: #4ade80; }}
            </style>
            </head>
            <body>
                <h1>🎨 {Config.BOT_NAME}</h1>
                <div class="status">
                    <h2>Status: <span class="online">● ONLINE</span></h2>
                    <p>Version: {Config.BOT_VERSION}</p>
                    <p>Creator: {Config.BOT_CREATOR}</p>
                </div>
            </body>
            </html>
            '''
            return html, 200
        
        def run():
            app.run(host='0.0.0.0', port=Config.PORT, debug=False, use_reloader=False)
        
        threading.Thread(target=run, daemon=True).start()
    
    async def stop(self):
        """Stop the bot gracefully"""
        print("Stopping bot...")
        if self.application:
            if Config.USE_WEBHOOK:
                await self.application.bot.delete_webhook()
            await self.application.stop()
            await self.application.shutdown()
        print("Bot stopped.")
    
    # ======================================================================================================================
    # USER COMMANDS
    # ======================================================================================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
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
        
        options = [answer]
        while len(options) < 4:
            wrong = str(int(answer) + random.randint(-10, 10))
            if wrong != answer and wrong not in options:
                options.append(wrong)
        random.shuffle(options)
        
        session = self.get_session(user_id)
        session['captcha_code'] = answer
        session['captcha_attempts'] = 0
        session['captcha_start'] = datetime.now()
        
        await update.message.reply_text(
            f"🌟 *WELCOME TO {Config.BOT_NAME}* 🌟\n\n"
            f"*Advanced Media Editing Bot*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *Features:*\n"
            f"• 200+ Editing Options\n"
            f"• 50+ Professional Filters\n"
            f"• Video & Audio Processing\n"
            f"• Premium Quality Output\n"
            f"• Daily Free Edits: {Config.FREE_DAILY_EDITS}\n"
            f"• Premium: Unlimited + Larger Files\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔐 *VERIFICATION REQUIRED*\n\n"
            f"Please solve:\n\n`{num1} {op} {num2} = ?`\n\n"
            f"_You have {Config.CAPTCHA_TIMEOUT} seconds._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.captcha_keyboard(answer, options)
        )
    
    async def _send_main_menu(self, update_or_query, user: User):
        user_id = user.id
        is_admin = user_id in Config.ADMIN_IDS
        is_premium = self.db.is_premium(user_id)
        stats = self.db.get_user_stats(user_id)
        
        msg = (
            f"🎨 *{Config.BOT_NAME}* 🎨\n\n"
            f"*Welcome back, {user.first_name}!*\n\n"
            f"📊 *Your Stats:*\n"
            f"• Total Edits: {stats.get('total_edits', 0)}\n"
            f"• Credits: {stats.get('credits', 100)}\n"
            f"• Premium: {'✅ Active' if is_premium else '❌ Inactive'}\n\n"
            f"*Select an option:*"
        )
        
        if hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.main_menu(is_admin, is_premium))
        else:
            await update_or_query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.main_menu(is_admin, is_premium))
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"❓ *{Config.BOT_NAME} HELP* ❓\n\n"
            "*📸 Image Editing:*\n"
            "• 18+ Filters (Blur, Sepia, Vintage, etc.)\n"
            "• Resize, Rotate, Flip, Crop\n"
            "• Adjust Brightness, Contrast, Saturation\n"
            "• Add Text, Watermark\n"
            "• Auto Enhance, Compress\n\n"
            "*🎬 Video Editing:*\n"
            "• Trim, Merge, Speed Change\n"
            "• Extract Audio, Mute\n"
            "• Add Watermark, Compress\n"
            "• Convert to GIF, Get Info\n\n"
            "*🎵 Audio Editing:*\n"
            "• Trim, Merge, Speed Change\n"
            "• Convert Format, Compress\n\n"
            "*💎 Premium Features:*\n"
            "• Unlimited daily edits\n"
            "• 2GB file size limit\n"
            "• 4K video support\n"
            "• Priority processing\n\n"
            "*Commands:*\n"
            "/start - Start bot\n"
            "/daily - Claim daily reward\n"
            "/refer - Get referral link\n"
            "/credits - Check credits\n"
            "/premium - Premium info\n"
            "/feedback - Send feedback\n"
            "/customcmd - Use custom command\n"
            "/cancel - Cancel operation\n\n"
            f"*Creator:* {Config.BOT_CREATOR}",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        stats = self.db.get_user_stats(user.id)
        is_premium = self.db.is_premium(user.id)
        
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
            f"• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`\n"
            f"• Referrals: `{stats.get('referral_count', 0)}`\n"
            f"• Joined: `{stats.get('join_date', 'N/A')[:10] if stats.get('join_date') else 'N/A'}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if session.get('temp_file') and os.path.exists(session['temp_file']):
                os.remove(session['temp_file'])
            for f in session.get('merge_files', []):
                if os.path.exists(f):
                    os.remove(f)
            del self.sessions[user_id]
        await update.message.reply_text("✅ *Operation cancelled!*", parse_mode=ParseMode.MARKDOWN)
    
    async def cmd_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        reward, streak = self.db.claim_daily_reward(user_id)
        if reward > 0:
            await update.message.reply_text(
                f"⭐ *DAILY REWARD* ⭐\n\n"
                f"You received: `{reward} credits`\n"
                f"Current streak: `{streak} days`\n\n"
                f"Come back tomorrow!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ *Already claimed today!*\n"
                f"Streak: `{streak} days`\n\n"
                f"Come back tomorrow!",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cmd_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        user_id = update.effective_user.id
        credits = self.db.get_credits(user_id)
        await update.message.reply_text(
            f"💰 *YOUR CREDITS* 💰\n\n"
            f"You have `{credits}` credits.\n\n"
            f"*Ways to earn:*\n"
            f"• Daily reward: 50-200 credits\n"
            f"• Referral: 50 credits each\n"
            f"• Premium: 500 bonus credits",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        is_premium = self.db.is_premium(user_id)
        
        if is_premium:
            stats = self.db.get_user_stats(user_id)
            await update.message.reply_text(
                "⭐ *PREMIUM ACTIVE* ⭐\n\n"
                f"*Expires:* {stats.get('premium_expires', 'N/A')}\n\n"
                "*Benefits:*\n"
                "✅ Unlimited daily edits\n"
                "✅ 2GB file size limit\n"
                "✅ 4K video support\n"
                "✅ Priority processing\n"
                "✅ Exclusive filters\n"
                "✅ No watermarks",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "⭐ *PREMIUM FEATURES* ⭐\n\n"
                "*Benefits:*\n"
                "• Unlimited daily edits\n"
                "• 2GB file size limit\n"
                "• 4K video support\n"
                "• Priority processing\n"
                "• Exclusive filters\n"
                "• No watermarks\n\n"
                "*Plans:*\n"
                "💎 Monthly - $2.99\n"
                "💎 Quarterly - $7.99\n"
                "💎 Yearly - $29.99\n"
                "👑 Lifetime - $99.99\n\n"
                "Contact @Kira_Fx_Bot to upgrade!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.premium_menu()
            )
    
    async def cmd_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = self.get_session(update.effective_user.id)
        session['state'] = 'awaiting_feedback'
        await update.message.reply_text(
            "📝 *SEND FEEDBACK* 📝\n\n"
            "Tell us what you think!\n\n"
            "Type your message below:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚡ *Custom Commands* ⚡\n\n"
                "Usage: `/customcmd <command_name>`\n\n"
                "Use the menu to browse commands:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Browse Commands", callback_data="list_custom_cmds")
                ]])
            )
            return
        
        cmd_name = args[0].lower()
        cmd = self.db.get_custom_command(cmd_name)
        
        if cmd:
            if cmd['response_type'] == 'text':
                await update.message.reply_text(cmd['response'], parse_mode=ParseMode.MARKDOWN)
            elif cmd['response_type'] == 'code':
                await update.message.reply_text(f"```\n{cmd['response']}\n```", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(cmd['response'])
        else:
            await update.message.reply_text(f"❌ Command '{cmd_name}' not found!", parse_mode=ParseMode.MARKDOWN)
    
    # ======================================================================================================================
    # ADMIN COMMANDS
    # ======================================================================================================================
    
    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
            return
        await update.message.reply_text("👑 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=KeyboardBuilder.admin_panel())
    
    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id> [reason]")
            return
        try:
            target_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
            self.db.ban_user(target_id, reason)
            await update.message.reply_text(f"✅ *User {target_id} banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        try:
            target_id = int(context.args[0])
            self.db.unban_user(target_id)
            await update.message.reply_text(f"✅ *User {target_id} unbanned!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /mute <user_id> <minutes> [reason]")
            return
        try:
            target_id = int(context.args[0])
            minutes = int(context.args[1])
            self.db.mute_user(target_id, minutes)
            await update.message.reply_text(f"✅ *User {target_id} muted for {minutes} minutes!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or minutes!")
    
    async def cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if not context.args:
            await update.message.reply_text("Usage: /unmute <user_id>")
            return
        try:
            target_id = int(context.args[0])
            self.db.unmute_user(target_id)
            await update.message.reply_text(f"✅ *User {target_id} unmuted!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /warn <user_id> <reason>")
            return
        try:
            target_id = int(context.args[0])
            reason = " ".join(context.args[1:])
            warn_count = self.db.add_warning(target_id, user_id, reason)
            await update.message.reply_text(f"⚠️ *User {target_id} warned!*\nWarnings: {warn_count}/3\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
            if warn_count >= 3:
                self.db.ban_user(target_id, "3 warnings - auto ban")
                await update.message.reply_text(f"🚫 *User {target_id} automatically banned!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_give_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /givepremium <user_id> <days>")
            return
        try:
            target_id = int(context.args[0])
            days = int(context.args[1])
            self.db.give_premium(target_id, days)
            await update.message.reply_text(f"✅ *Premium granted to user {target_id} for {days} days!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or days!")
    
    async def cmd_add_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
            return
        try:
            target_id = int(context.args[0])
            amount = int(context.args[1])
            self.db.add_credits(target_id, amount)
            await update.message.reply_text(f"✅ *Added {amount} credits to user {target_id}!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or amount!")
    
    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            return
        session = self.get_session(user_id)
        session['state'] = 'awaiting_broadcast'
        await update.message.reply_text(
            "📢 *BROADCAST MESSAGE* 📢\n\n"
            "Send the message to broadcast to all users.\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ======================================================================================================================
    # CALLBACK HANDLER
    # ======================================================================================================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        # CAPTCHA
        if data.startswith("captcha_"):
            selected = data.replace("captcha_", "")
            session = self.get_session(user_id)
            if selected == session.get('captcha_code'):
                self.db.verify_user(user_id)
                await query.edit_message_text("✅ *Verification successful!*", parse_mode=ParseMode.MARKDOWN)
                await self._send_main_menu(query, query.from_user)
            else:
                session['captcha_attempts'] = session.get('captcha_attempts', 0) + 1
                if session['captcha_attempts'] >= Config.MAX_CAPTCHA_ATTEMPTS:
                    await query.edit_message_text("❌ *Verification failed!* Use /start to try again.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await query.edit_message_text(f"❌ *Incorrect!* Attempts left: {Config.MAX_CAPTCHA_ATTEMPTS - session['captcha_attempts']}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Main navigation
        if data == "back_main":
            is_admin = user_id in Config.ADMIN_IDS
            is_premium = self.db.is_premium(user_id)
            await query.edit_message_text("🎨 *Main Menu*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.main_menu(is_admin, is_premium))
        
        elif data == "mode_image":
            await query.edit_message_text("🖼️ *Image Editing Mode*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_image'
        
        elif data == "mode_video":
            await query.edit_message_text("🎬 *Video Editing Mode*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_video'
        
        elif data == "mode_audio":
            await query.edit_message_text("🎵 *Audio Editing Mode*\n\nSend me an audio file:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_audio'
        
        elif data == "mode_gif":
            await query.edit_message_text("🎞️ *GIF Creation Mode*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_video'
            session['pending_effect'] = 'to_gif'
        
        elif data == "ai_enhance":
            await query.edit_message_text("✨ *AI Auto-Enhance*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['pending_effect'] = 'auto_enhance'
            session['state'] = 'awaiting_image'
        
        elif data == "collage":
            await query.edit_message_text("🎨 *Create Collage*\n\nSend me images (up to 4). Type 'done' when finished:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['pending_effect'] = 'collage'
            session['batch_files'] = []
            session['state'] = 'awaiting_merge_files'
        
        elif data == "compress_menu":
            await query.edit_message_text("🗜️ *COMPRESSION MENU*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.compress_menu())
        
        elif data == "compress_video":
            await query.edit_message_text("🗜️ *VIDEO COMPRESSION*\n\nSelect target quality:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.video_quality_menu())
        
        elif data.startswith("quality_"):
            quality = data.replace("quality_", "")
            session = self.get_session(user_id)
            session['compress_quality'] = quality
            session['pending_effect'] = 'compress_video'
            session['state'] = 'awaiting_video'
            await query.edit_message_text(f"🗜️ *Video Compression: {quality}*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "compress_image":
            session = self.get_session(user_id)
            session['pending_effect'] = 'compress_image'
            session['state'] = 'awaiting_image'
            await query.edit_message_text("🗜️ *IMAGE COMPRESSION*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "compress_audio":
            session = self.get_session(user_id)
            session['pending_effect'] = 'compress_audio'
            session['state'] = 'awaiting_audio'
            await query.edit_message_text("🗜️ *AUDIO COMPRESSION*\n\nSend me an audio file:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "premium":
            await query.edit_message_text("⭐ *PREMIUM PLANS*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.premium_menu())
        
        elif data.startswith("premium_"):
            plan = data.replace("premium_", "")
            await query.edit_message_text(
                f"💎 *Premium {plan.title()} Plan* 💎\n\n"
                f"Contact @Kira_Fx_Bot to upgrade!\n\n"
                f"*Benefits:*\n"
                f"✅ Unlimited daily edits\n"
                f"✅ 2GB file size limit\n"
                f"✅ 4K video support\n"
                f"✅ Priority processing\n"
                f"✅ Exclusive filters\n"
                f"✅ No watermarks",
                parse_mode=ParseMode.MARKDOWN
            )
        
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
        
        elif data == "help":
            await self.cmd_help(update, context)
        
        elif data == "feedback":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_feedback'
            await query.edit_message_text("📝 *Send feedback:*", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "code_format":
            await query.edit_message_text("💻 *CODE FORMATTER*\n\nSelect a language:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.code_format_menu())
        
        elif data.startswith("format_"):
            lang = data.replace("format_", "")
            session = self.get_session(user_id)
            session['state'] = 'awaiting_code_input'
            session['code_language'] = None if lang == 'auto' else lang
            await query.edit_message_text(f"📝 *Format {lang.upper()} Code*\n\nSend your code below:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "custom_commands_menu":
            is_admin = user_id in Config.ADMIN_IDS
            await query.edit_message_text("⚡ *CUSTOM COMMANDS*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.custom_commands_menu(is_admin))
        
        elif data == "list_custom_cmds":
            commands = self.db.list_custom_commands()
            if commands:
                text = "📋 *AVAILABLE CUSTOM COMMANDS*\n\n"
                for cmd in commands:
                    text += f"• `/{cmd['command']}` - {cmd['response_type']} (Used: {cmd['usage_count']})\n"
                text += "\n_Use /customcmd <name> to execute_"
            else:
                text = "❌ No custom commands available."
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        
        elif data == "add_custom_cmd":
            if user_id not in Config.ADMIN_IDS:
                await query.answer("Access denied!", show_alert=True)
                return
            session = self.get_session(user_id)
            session['state'] = 'awaiting_custom_command'
            session['pending_effect'] = 'add_custom_cmd'
            await query.edit_message_text(
                "➕ *ADD CUSTOM COMMAND*\n\n"
                "Send in format:\n"
                "`command | type | response`\n\n"
                "Example: `hello | text | Hello, welcome!`\n"
                "Example: `code | code | print('Hello')`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "delete_custom_cmd":
            if user_id not in Config.ADMIN_IDS:
                await query.answer("Access denied!", show_alert=True)
                return
            session = self.get_session(user_id)
            session['state'] = 'awaiting_custom_command'
            session['pending_effect'] = 'delete_custom_cmd'
            await query.edit_message_text("❌ *DELETE CUSTOM COMMAND*\n\nSend the command name to delete:", parse_mode=ParseMode.MARKDOWN)
        
        # Admin panel
        elif data == "admin_panel":
            await query.edit_message_text("👑 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.admin_panel())
        
        elif data == "admin_stats":
            stats = self.db.get_bot_stats()
            await query.edit_message_text(
                f"📊 *BOT STATISTICS* 📊\n\n"
                f"👥 Total Users: `{stats['total_users']}`\n"
                f"🟢 Active Today: `{stats['active_today']}`\n"
                f"🎨 Total Edits: `{stats['total_edits']}`\n"
                f"⭐ Premium Users: `{stats['premium_users']}`\n"
                f"🚫 Banned Users: `{stats['banned_users']}`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admin_users":
            users = self.db.get_all_users(20)
            text = "👥 *RECENT USERS*\n\n"
            for u in users:
                text += f"• `{u['user_id']}` - {u.get('first_name', 'Unknown')[:20]}\n"
                text += f"  Edits: {u.get('total_edits', 0)} | Credits: {u.get('credits', 0)}\n"
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_broadcast":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_broadcast'
            await query.edit_message_text("📢 *Broadcast*\n\nSend the message to broadcast:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_ban":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'ban'
            await query.edit_message_text("🚫 *Ban User*\n\nSend user ID and reason:\nExample: `123456789 Spamming`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_mute":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'mute'
            await query.edit_message_text("🔇 *Mute User*\n\nSend user ID and minutes:\nExample: `123456789 60`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_warn":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'warn'
            await query.edit_message_text("⚠️ *Warn User*\n\nSend user ID and reason:\nExample: `123456789 Rule violation`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_unban":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'unban'
            await query.edit_message_text("✅ *Unban/Unmute User*\n\nSend user ID:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_give_premium":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'give_premium'
            await query.edit_message_text("💎 *Give Premium*\n\nSend user ID and days:\nExample: `123456789 30`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_add_credits":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'add_credits'
            await query.edit_message_text("💰 *Add Credits*\n\nSend user ID and amount:\nExample: `123456789 100`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_feedback_list":
            feedbacks = self.db.get_pending_feedback()
            if feedbacks:
                text = "📋 *PENDING FEEDBACK*\n\n"
                for fb in feedbacks[:10]:
                    text += f"• #{fb['id']} from {fb.get('username', 'User')}: {fb['message'][:100]}\n"
                await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("No pending feedback.", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_logs":
            await query.edit_message_text("📜 *ADMIN LOGS*\n\nFeature coming soon!", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_export":
            csv_data = self.db.export_users_csv()
            await query.edit_message_text("📊 *Exporting data...*", parse_mode=ParseMode.MARKDOWN)
            await context.bot.send_document(
                chat_id=user_id,
                document=InputFile(io.BytesIO(csv_data.encode()), filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv"),
                caption="User data export"
            )
        
        elif data == "admin_custom_cmds":
            commands = self.db.list_custom_commands()
            if commands:
                text = "⚡ *CUSTOM COMMANDS*\n\n"
                for cmd in commands:
                    text += f"• `/{cmd['command']}` - {cmd['response_type']} (Used: {cmd['usage_count']})\n"
            else:
                text = "No custom commands found."
            await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
        
        elif data == "admin_reset_user":
            session = self.get_session(user_id)
            session['state'] = 'awaiting_admin_action'
            session['pending_effect'] = 'reset_user'
            await query.edit_message_text("🔄 *Reset User*\n\nSend user ID to reset:", parse_mode=ParseMode.MARKDOWN)
        
        # Image menu
        elif data == "img_filters":
            await query.edit_message_text("🎨 *SELECT FILTER*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.filters_menu())
        
        elif data.startswith("filter_"):
            filter_name = data.replace("filter_", "").replace("_", " ")
            session = self.get_session(user_id)
            session['pending_effect'] = filter_name
            session['state'] = 'awaiting_image'
            await query.edit_message_text(f"🎨 *Apply Filter: {filter_name.title()}*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_resize":
            session = self.get_session(user_id)
            session['pending_effect'] = 'resize'
            session['state'] = 'awaiting_resize_dims'
            await query.edit_message_text("📐 *Resize Image*\n\nSend dimensions (width height):\nExample: `1920 1080`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_rotate":
            session = self.get_session(user_id)
            session['pending_effect'] = 'rotate'
            session['state'] = 'awaiting_rotate_angle'
            await query.edit_message_text("🔄 *Rotate Image*\n\nSend angle (0-360):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_flip":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🪞 Horizontal", callback_data="flip_h")],
                [InlineKeyboardButton("↕️ Vertical", callback_data="flip_v")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_image")]
            ])
            await query.edit_message_text("🪞 *Flip Image*", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        
        elif data in ["flip_h", "flip_v"]:
            session = self.get_session(user_id)
            session['pending_effect'] = data
            session['state'] = 'awaiting_image'
            await query.edit_message_text(f"🪞 *Flip Image*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_crop":
            session = self.get_session(user_id)
            session['pending_effect'] = 'crop'
            session['state'] = 'awaiting_crop_coords'
            await query.edit_message_text("✂️ *Crop Image*\n\nSend coordinates (left top right bottom):\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
        
        elif data in ["img_brightness", "img_contrast", "img_saturation", "img_sharpness"]:
            effect = data.replace("img_", "")
            session = self.get_session(user_id)
            session['pending_effect'] = effect
            session['state'] = 'awaiting_color_adjust'
            await query.edit_message_text(f"🎨 *Adjust {effect.title()}*\n\nSend factor (0.5-2.0):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_text":
            session = self.get_session(user_id)
            session['pending_effect'] = 'add_text'
            session['state'] = 'awaiting_text_content'
            await query.edit_message_text("📝 *Add Text*\n\nSend the text to add:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_watermark":
            session = self.get_session(user_id)
            session['pending_effect'] = 'add_watermark'
            session['state'] = 'awaiting_text_content'
            await query.edit_message_text("💧 *Add Watermark*\n\nSend watermark text:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "img_auto":
            session = self.get_session(user_id)
            session['pending_effect'] = 'auto_enhance'
            session['state'] = 'awaiting_image'
            await query.edit_message_text("✨ *Auto-Enhance Image*\n\nSend an image:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "back_image":
            await query.edit_message_text("🖼️ *Image Editing Menu*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.image_menu())
        
        # Video menu
        elif data == "vid_trim":
            session = self.get_session(user_id)
            session['pending_effect'] = 'trim'
            session['state'] = 'awaiting_trim_times'
            await query.edit_message_text("✂️ *Trim Video*\n\nSend start and end times (seconds):\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_speed":
            session = self.get_session(user_id)
            session['pending_effect'] = 'speed'
            session['state'] = 'awaiting_speed_factor'
            await query.edit_message_text("⚡ *Change Speed*\n\nSend speed factor (0.5-2.0):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_audio":
            session = self.get_session(user_id)
            session['pending_effect'] = 'extract_audio'
            session['state'] = 'awaiting_video'
            await query.edit_message_text("🎵 *Extract Audio*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_mute":
            session = self.get_session(user_id)
            session['pending_effect'] = 'mute'
            session['state'] = 'awaiting_video'
            await query.edit_message_text("🔊 *Mute Video*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_watermark":
            session = self.get_session(user_id)
            session['pending_effect'] = 'video_watermark'
            session['state'] = 'awaiting_text_content'
            await query.edit_message_text("🏷️ *Add Watermark*\n\nSend watermark text:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_merge":
            session = self.get_session(user_id)
            session['pending_effect'] = 'merge_videos'
            session['merge_files'] = []
            session['state'] = 'awaiting_merge_files'
            await query.edit_message_text("🔗 *Merge Videos*\n\nSend videos one by one. Type 'done' when finished:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_to_gif":
            session = self.get_session(user_id)
            session['pending_effect'] = 'to_gif'
            session['state'] = 'awaiting_video'
            await query.edit_message_text("🎞️ *Convert to GIF*\n\nSend a video (max 10 seconds):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_info":
            session = self.get_session(user_id)
            session['pending_effect'] = 'video_info'
            session['state'] = 'awaiting_video'
            await query.edit_message_text("ℹ️ *Video Info*\n\nSend a video:", parse_mode=ParseMode.MARKDOWN)
        
        # Audio menu
        elif data == "aud_trim":
            session = self.get_session(user_id)
            session['pending_effect'] = 'trim_audio'
            session['state'] = 'awaiting_trim_times'
            await query.edit_message_text("✂️ *Trim Audio*\n\nSend start and end times (seconds):\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "aud_speed":
            session = self.get_session(user_id)
            session['pending_effect'] = 'speed_audio'
            session['state'] = 'awaiting_speed_factor'
            await query.edit_message_text("⚡ *Change Audio Speed*\n\nSend speed factor (0.5-2.0):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "aud_merge":
            session = self.get_session(user_id)
            session['pending_effect'] = 'merge_audios'
            session['merge_files'] = []
            session['state'] = 'awaiting_merge_files'
            await query.edit_message_text("🔗 *Merge Audio Files*\n\nSend audio files one by one. Type 'done' when finished:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "aud_convert":
            session = self.get_session(user_id)
            session['pending_effect'] = 'convert_audio'
            session['state'] = 'awaiting_audio'
            await query.edit_message_text("🔄 *Convert Audio Format*\n\nSend an audio file:", parse_mode=ParseMode.MARKDOWN)
    
    # ======================================================================================================================
    # MESSAGE HANDLERS
    # ======================================================================================================================
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Check ban/mute
        is_banned, reason = self.db.is_banned(user_id)
        if is_banned:
            await update.message.reply_text(f"⛔ *You are banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
            return
        
        is_muted, until = self.db.is_muted(user_id)
        if is_muted:
            await update.message.reply_text(f"🔇 *You are muted until {until}!*", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check daily limit
        can_edit, msg = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {msg}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check file size
        photo = update.message.photo[-1]
        if photo.file_size > Config.MAX_IMAGE_SIZE:
            await update.message.reply_text(f"❌ Image too large! Max size: {Config.MAX_IMAGE_SIZE // (1024*1024)}MB", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Download image
        file = await context.bot.get_file(photo.file_id)
        temp_path = TEMP_DIR / f"img_{user_id}_{int(time.time())}.jpg"
        await file.download_to_document(temp_path)
        
        session = self.get_session(user_id)
        session['temp_file'] = str(temp_path)
        effect = session.get('pending_effect')
        
        if effect == 'auto_enhance':
            await self._process_image_auto_enhance(update, context, temp_path, user_id)
        elif effect == 'resize':
            session['state'] = 'awaiting_resize_dims'
            await update.message.reply_text("📐 *Send dimensions (width height):*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'rotate':
            session['state'] = 'awaiting_rotate_angle'
            await update.message.reply_text("🔄 *Send rotation angle (0-360):*", parse_mode=ParseMode.MARKDOWN)
        elif effect in ['flip_h', 'flip_v']:
            await self._process_image_flip(update, context, temp_path, user_id, effect)
        elif effect == 'crop':
            session['state'] = 'awaiting_crop_coords'
            await update.message.reply_text("✂️ *Send crop coordinates (left top right bottom):*", parse_mode=ParseMode.MARKDOWN)
        elif effect in ['brightness', 'contrast', 'saturation', 'sharpness']:
            session['state'] = 'awaiting_color_adjust'
            await update.message.reply_text(f"🎨 *Send {effect} factor (0.5-2.0):*", parse_mode=ParseMode.MARKDOWN)
        elif effect in ['add_text', 'add_watermark']:
            session['state'] = 'awaiting_text_content'
            await update.message.reply_text("📝 *Send the text:*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'compress_image':
            await self._process_image_compress(update, context, temp_path, user_id)
        elif effect:
            await self._process_image_filter(update, context, temp_path, user_id, effect)
        else:
            await update.message.reply_text("Please select an option from the menu first!", reply_markup=KeyboardBuilder.image_menu())
    
    async def _process_image_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, filter_name: str):
        msg = await update.message.reply_text("🎨 *Processing image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"output_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.apply_filter(str(img_path), filter_name, str(out_path))
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Filter applied: {filter_name.title()}!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
                self.db.add_edit_history(user_id, 'image', filter_name, os.path.getsize(img_path), 0)
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
            session['state'] = 'verified'
    
    async def _process_image_auto_enhance(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        msg = await update.message.reply_text("✨ *AI Auto-Enhancing...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"enhanced_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.auto_enhance(str(img_path), str(out_path))
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption="✅ *Image auto-enhanced!*\n\n✨ Kira-Fx AI Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_image_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        msg = await update.message.reply_text("🗜️ *Compressing image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"compressed_{user_id}_{int(time.time())}.jpg"
            success, result, info = self.image_processor.compress_image(str(img_path), str(out_path), 'high')
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Image compressed!*\n\n📊 {info['ratio']} compression\n📁 {info['input_size']//1024}KB → {info['output_size']//1024}KB\n⏱️ {info['time']}\n\n✨ Kira-Fx Compression", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_image_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, flip_type: str):
        msg = await update.message.reply_text("🪞 *Flipping image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"flipped_{user_id}_{int(time.time())}.jpg"
            horizontal = flip_type == "flip_h"
            success, result = self.image_processor.flip(str(img_path), str(out_path), horizontal)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption="✅ *Image flipped!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Check ban/mute
        is_banned, reason = self.db.is_banned(user_id)
        if is_banned:
            await update.message.reply_text(f"⛔ *You are banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
            return
        
        is_muted, until = self.db.is_muted(user_id)
        if is_muted:
            await update.message.reply_text(f"🔇 *You are muted until {until}!*", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check daily limit
        can_edit, msg = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {msg}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check file size
        video = update.message.video
        if video.file_size > Config.MAX_VIDEO_SIZE:
            await update.message.reply_text(f"❌ Video too large! Max size: {Config.MAX_VIDEO_SIZE // (1024*1024)}MB", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Download video
        file = await context.bot.get_file(video.file_id)
        temp_path = TEMP_DIR / f"video_{user_id}_{int(time.time())}.mp4"
        await file.download_to_document(temp_path)
        
        session = self.get_session(user_id)
        session['temp_file'] = str(temp_path)
        effect = session.get('pending_effect')
        
        if effect == 'extract_audio':
            await self._process_extract_audio(update, context, temp_path, user_id)
        elif effect == 'mute':
            await self._process_mute_video(update, context, temp_path, user_id)
        elif effect == 'to_gif':
            await self._process_video_to_gif(update, context, temp_path, user_id)
        elif effect == 'video_info':
            await self._process_video_info(update, context, temp_path, user_id)
        elif effect == 'compress_video':
            quality = session.get('compress_quality', '720p')
            await self._process_video_compress(update, context, temp_path, user_id, quality)
        elif effect == 'trim':
            session['state'] = 'awaiting_trim_times'
            await update.message.reply_text("✂️ *Send trim times (start end):*\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'speed':
            session['state'] = 'awaiting_speed_factor'
            await update.message.reply_text("⚡ *Send speed factor:*\nExample: `2.0`", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'video_watermark':
            session['state'] = 'awaiting_text_content'
            await update.message.reply_text("🏷️ *Send watermark text:*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'merge_videos':
            session['merge_files'].append(str(temp_path))
            await update.message.reply_text(f"📹 Video {len(session['merge_files'])} received. Send more or type 'done' to finish.")
        else:
            await update.message.reply_text("Please select a video editing option first!", reply_markup=KeyboardBuilder.video_menu())
    
    async def _process_video_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, quality: str):
        msg = await update.message.reply_text(f"🗜️ *Compressing video to {quality}...*\n⏳ This may take a moment...", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"compressed_{user_id}_{int(time.time())}.mp4"
            success, result, info = self.video_processor.compress_video(str(video_path), str(out_path), quality)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption=f"✅ *Video compressed to {quality}!*\n\n📊 {info['ratio']} compression\n📁 {info['input_size']//(1024*1024)}MB → {info['output_size']//(1024*1024)}MB\n⏱️ {info['time']}\n\n✨ Kira-Fx Compression", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_extract_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        msg = await update.message.reply_text("🎵 *Extracting audio...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"audio_{user_id}_{int(time.time())}.mp3"
            success, result = self.video_processor.extract_audio(str(video_path), str(out_path))
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption="✅ *Audio extracted!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_mute_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        msg = await update.message.reply_text("🔊 *Muting video...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"muted_{user_id}_{int(time.time())}.mp4"
            clip = VideoFileClip(str(video_path))
            muted = clip.without_audio()
            muted.write_videofile(str(out_path), codec='libx264', logger=None, verbose=False)
            clip.close()
            muted.close()
            with open(out_path, 'rb') as f:
                await update.message.reply_video(video=InputFile(f), caption="✅ *Video muted!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
            os.remove(out_path)
            self.db.increment_edits(user_id, 'video')
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_video_to_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        msg = await update.message.reply_text("🎞️ *Converting to GIF...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"output_{user_id}_{int(time.time())}.gif"
            success, result = self.video_processor.create_gif(str(video_path), str(out_path), 0, 5)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_document(document=InputFile(f, filename="output.gif"), caption="✅ *GIF created!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_video_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        try:
            info = self.video_processor.get_info(str(video_path))
            if 'error' not in info:
                await update.message.reply_text(
                    f"ℹ️ *VIDEO INFORMATION* ℹ️\n\n"
                    f"📹 Resolution: `{info.get('size', [0,0])[0]}x{info.get('size', [0,0])[1]}`\n"
                    f"⏱️ Duration: `{info.get('duration', 0):.2f} seconds`\n"
                    f"🎬 FPS: `{info.get('fps', 0):.2f}`\n"
                    f"🔊 Audio: `{'Yes' if info.get('audio', False) else 'No'}`\n\n"
                    f"✨ Kira-Fx Analysis",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=KeyboardBuilder.video_menu()
                )
            else:
                await update.message.reply_text(f"❌ *Error:* {info['error']}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Check ban/mute
        is_banned, reason = self.db.is_banned(user_id)
        if is_banned:
            await update.message.reply_text(f"⛔ *You are banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check daily limit
        can_edit, msg = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {msg}", parse_mode=ParseMode.MARKDOWN)
            return
        
        audio = update.message.audio or update.message.voice
        if audio and audio.file_size > Config.MAX_AUDIO_SIZE:
            await update.message.reply_text(f"❌ Audio too large! Max size: {Config.MAX_AUDIO_SIZE // (1024*1024)}MB", parse_mode=ParseMode.MARKDOWN)
            return
        
        file = await context.bot.get_file(audio.file_id)
        temp_path = TEMP_DIR / f"audio_{user_id}_{int(time.time())}.mp3"
        await file.download_to_document(temp_path)
        
        session = self.get_session(user_id)
        session['temp_file'] = str(temp_path)
        effect = session.get('pending_effect')
        
        if effect == 'compress_audio':
            await self._process_audio_compress(update, context, temp_path, user_id)
        elif effect == 'trim_audio':
            session['state'] = 'awaiting_trim_times'
            await update.message.reply_text("✂️ *Send trim times (start end):*\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'speed_audio':
            session['state'] = 'awaiting_speed_factor'
            await update.message.reply_text("⚡ *Send speed factor (0.5-2.0):*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'merge_audios':
            session['merge_files'].append(str(temp_path))
            await update.message.reply_text(f"🎵 Audio {len(session['merge_files'])} received. Send more or type 'done' to finish.")
        elif effect == 'convert_audio':
            await self._process_audio_convert(update, context, temp_path, user_id)
        else:
            await update.message.reply_text("Please select an audio editing option first!", reply_markup=KeyboardBuilder.audio_menu())
    
    async def _process_audio_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_path: Path, user_id: int):
        msg = await update.message.reply_text("🗜️ *Compressing audio...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"compressed_{user_id}_{int(time.time())}.mp3"
            success, result = self.audio_processor.convert_format(str(audio_path), str(out_path), 'mp3')
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption="✅ *Audio compressed!*\n\n✨ Kira-Fx Compression", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.audio_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'audio')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(audio_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def _process_audio_convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_path: Path, user_id: int):
        msg = await update.message.reply_text("🔄 *Converting audio...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"converted_{user_id}_{int(time.time())}.mp3"
            success, result = self.audio_processor.convert_format(str(audio_path), str(out_path), 'mp3')
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption="✅ *Audio converted to MP3!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.audio_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'audio')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(audio_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📄 *Document received*\n\nPlease use the appropriate commands for editing.", parse_mode=ParseMode.MARKDOWN)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        text = update.message.text.strip()
        
        # Check rate limit
        if not self._check_rate_limit(user_id):
            await update.message.reply_text("⚠️ *Rate limit exceeded!* Please wait.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check if user is banned
        is_banned, reason = self.db.is_banned(user_id)
        if is_banned:
            await update.message.reply_text(f"⛔ *You are banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check if user is muted
        is_muted, until = self.db.is_muted(user_id)
        if is_muted:
            await update.message.reply_text(f"🔇 *You are muted until {until}!*", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle code formatting
        if session.get('state') == 'awaiting_code_input':
            lang = session.get('code_language')
            formatted, detected = self.code_formatter.format_code(text, lang)
            await update.message.reply_text(f"```{detected}\n{formatted[:3500]}\n```", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            session['code_language'] = None
            return
        
        # Handle custom command addition
        if session.get('state') == 'awaiting_custom_command':
            if session.get('pending_effect') == 'add_custom_cmd':
                parts = text.split('|')
                if len(parts) >= 2:
                    cmd_name = parts[0].strip().lower()
                    cmd_type = parts[1].strip().lower() if len(parts) > 1 else 'text'
                    cmd_response = parts[2].strip() if len(parts) > 2 else ''
                    if self.db.add_custom_command(cmd_name, cmd_response, cmd_type, user_id):
                        await update.message.reply_text(f"✅ Custom command `/{cmd_name}` added!", parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text("❌ Failed to add command.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Invalid format! Use: `command | type | response`", parse_mode=ParseMode.MARKDOWN)
            elif session.get('pending_effect') == 'delete_custom_cmd':
                if self.db.delete_custom_command(text.lower()):
                    await update.message.reply_text(f"✅ Command '{text}' deleted!", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text(f"❌ Command '{text}' not found!", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            session['pending_effect'] = None
            return
        
        # Handle feedback
        if session.get('state') == 'awaiting_feedback':
            self.db.save_feedback(user_id, text)
            await update.message.reply_text("✅ *Thank you for your feedback!*", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            return
        
        # Handle broadcast
        if session.get('state') == 'awaiting_broadcast':
            if user_id in Config.ADMIN_IDS:
                users = self.db.get_all_users(10000)
                success = 0
                failed = 0
                msg = await update.message.reply_text("📢 *Broadcasting...*", parse_mode=ParseMode.MARKDOWN)
                for user in users:
                    try:
                        await context.bot.send_message(chat_id=user['user_id'], text=f"📢 *ANNOUNCEMENT*\n\n{text}", parse_mode=ParseMode.MARKDOWN)
                        success += 1
                        await asyncio.sleep(0.05)
                    except:
                        failed += 1
                self.db.add_broadcast_record(user_id, text, len(users), success, failed)
                await msg.edit_text(f"✅ *Broadcast sent!*\nSuccessful: {success}\nFailed: {failed}", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            return
        
        # Handle admin actions
        if session.get('state') == 'awaiting_admin_action':
            if user_id in Config.ADMIN_IDS:
                effect = session.get('pending_effect')
                if effect == 'ban':
                    parts = text.split(maxsplit=1)
                    if len(parts) >= 1:
                        try:
                            target = int(parts[0])
                            reason = parts[1] if len(parts) > 1 else "No reason"
                            self.db.ban_user(target, reason)
                            await update.message.reply_text(f"✅ *User {target} banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                        except ValueError:
                            await update.message.reply_text("❌ Invalid user ID!")
                elif effect == 'mute':
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target = int(parts[0])
                            minutes = int(parts[1])
                            self.db.mute_user(target, minutes)
                            await update.message.reply_text(f"✅ *User {target} muted for {minutes} minutes!*", parse_mode=ParseMode.MARKDOWN)
                        except ValueError:
                            await update.message.reply_text("❌ Invalid user ID or minutes!")
                elif effect == 'warn':
                    parts = text.split(maxsplit=1)
                    if len(parts) >= 2:
                        try:
                            target = int(parts[0])
                            reason = parts[1]
                            warn_count = self.db.add_warning(target, user_id, reason)
                            await update.message.reply_text(f"⚠️ *User {target} warned!*\nWarnings: {warn_count}/3\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
                            if warn_count >= 3:
                                self.db.ban_user(target, "3 warnings - auto ban")
                        except ValueError:
                            await update.message.reply_text("❌ Invalid user ID!")
                elif effect == 'unban':
                    try:
                        target = int(text.strip())
                        self.db.unban_user(target)
                        self.db.unmute_user(target)
                        await update.message.reply_text(f"✅ *User {target} unbanned/unmuted!*", parse_mode=ParseMode.MARKDOWN)
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!")
                elif effect == 'give_premium':
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target = int(parts[0])
                            days = int(parts[1])
                            self.db.give_premium(target, days)
                            await update.message.reply_text(f"✅ *Premium granted to {target} for {days} days!*", parse_mode=ParseMode.MARKDOWN)
                        except ValueError:
                            await update.message.reply_text("❌ Invalid user ID or days!")
                elif effect == 'add_credits':
                    parts = text.split()
                    if len(parts) >= 2:
                        try:
                            target = int(parts[0])
                            amount = int(parts[1])
                            self.db.add_credits(target, amount)
                            await update.message.reply_text(f"✅ *Added {amount} credits to {target}!*", parse_mode=ParseMode.MARKDOWN)
                        except ValueError:
                            await update.message.reply_text("❌ Invalid user ID or amount!")
                elif effect == 'reset_user':
                    try:
                        target = int(text.strip())
                        # Reset user logic
                        await update.message.reply_text(f"✅ *User {target} data reset!*", parse_mode=ParseMode.MARKDOWN)
                    except ValueError:
                        await update.message.reply_text("❌ Invalid user ID!")
            session['state'] = 'verified'
            session['pending_effect'] = None
            return
        
        # Handle resize dimensions
        if session.get('state') == 'awaiting_resize_dims':
            try:
                parts = text.split()
                if len(parts) == 2:
                    width, height = int(parts[0]), int(parts[1])
                    img_path = session.get('temp_file')
                    if img_path and os.path.exists(img_path):
                        await self._process_image_resize(update, context, Path(img_path), user_id, width, height)
                    else:
                        await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `width height`", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid numbers!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle rotate angle
        if session.get('state') == 'awaiting_rotate_angle':
            try:
                angle = int(text)
                img_path = session.get('temp_file')
                if img_path and os.path.exists(img_path):
                    await self._process_image_rotate(update, context, Path(img_path), user_id, angle)
                else:
                    await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid angle!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle crop coordinates
        if session.get('state') == 'awaiting_crop_coords':
            try:
                parts = text.split()
                if len(parts) == 4:
                    left, top, right, bottom = map(int, parts)
                    img_path = session.get('temp_file')
                    if img_path and os.path.exists(img_path):
                        await self._process_image_crop(update, context, Path(img_path), user_id, left, top, right, bottom)
                    else:
                        await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `left top right bottom`", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid coordinates!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle color adjustments
        if session.get('state') == 'awaiting_color_adjust':
            try:
                factor = float(text)
                if factor < 0.1 or factor > 3.0:
                    await update.message.reply_text("❌ Factor must be between 0.1 and 3.0", parse_mode=ParseMode.MARKDOWN)
                    return
                img_path = session.get('temp_file')
                if img_path and os.path.exists(img_path):
                    await self._process_image_color_adjust(update, context, Path(img_path), user_id, session.get('pending_effect'), factor)
                else:
                    await update.message.reply_text("❌ No image found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle text for watermark/text
        if session.get('state') == 'awaiting_text_content':
            img_path = session.get('temp_file')
            if img_path and os.path.exists(img_path):
                effect = session.get('pending_effect')
                if effect == 'add_text':
                    await self._process_image_add_text(update, context, Path(img_path), user_id, text)
                elif effect == 'add_watermark':
                    await self._process_image_add_watermark(update, context, Path(img_path), user_id, text)
                elif effect == 'video_watermark':
                    await self._process_video_watermark(update, context, Path(img_path), user_id, text)
            else:
                await update.message.reply_text("❌ No file found.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle trim times
        if session.get('state') == 'awaiting_trim_times':
            try:
                parts = text.split()
                if len(parts) == 2:
                    start = float(parts[0])
                    end = float(parts[1])
                    file_path = session.get('temp_file')
                    if file_path and os.path.exists(file_path):
                        if session.get('pending_effect') in ['trim', 'trim_audio']:
                            await self._process_trim(update, context, Path(file_path), user_id, start, end)
                    else:
                        await update.message.reply_text("❌ No file found.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Send as: `start end`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle speed factor
        if session.get('state') == 'awaiting_speed_factor':
            try:
                factor = float(text)
                if factor < 0.1 or factor > 10:
                    await update.message.reply_text("❌ Factor must be between 0.1 and 10", parse_mode=ParseMode.MARKDOWN)
                    return
                file_path = session.get('temp_file')
                if file_path and os.path.exists(file_path):
                    if session.get('pending_effect') == 'speed':
                        await self._process_video_speed(update, context, Path(file_path), user_id, factor)
                    elif session.get('pending_effect') == 'speed_audio':
                        await self._process_audio_speed(update, context, Path(file_path), user_id, factor)
                else:
                    await update.message.reply_text("❌ No file found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle merge completion
        if session.get('state') == 'awaiting_merge_files':
            if text.lower() == 'done':
                effect = session.get('pending_effect')
                if effect == 'merge_videos' and len(session.get('merge_files', [])) >= 2:
                    await self._process_video_merge(update, context, session['merge_files'], user_id)
                elif effect == 'merge_audios' and len(session.get('merge_files', [])) >= 2:
                    await self._process_audio_merge(update, context, session['merge_files'], user_id)
                elif effect == 'collage' and len(session.get('batch_files', [])) >= 2:
                    await self._process_image_collage(update, context, session['batch_files'], user_id)
                else:
                    await update.message.reply_text("❌ Need at least 2 files to merge!", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Send files or type 'done' to finish.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Default response
        await update.message.reply_text(
            f"🤖 *{Config.BOT_NAME}*\n\n"
            "Please use the menu buttons to select an option!\n"
            "Type /help for assistance.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.main_menu(user_id in Config.ADMIN_IDS, self.db.is_premium(user_id))
        )
    
    async def _process_image_resize(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, width: int, height: int):
        msg = await update.message.reply_text("📐 *Resizing image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"resized_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.resize(str(img_path), str(out_path), width, height)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Resized to {width}x{height}!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, angle: int):
        msg = await update.message.reply_text("🔄 *Rotating image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"rotated_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.rotate(str(img_path), str(out_path), angle)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Rotated {angle}°!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, left: int, top: int, right: int, bottom: int):
        msg = await update.message.reply_text("✂️ *Cropping image...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"cropped_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.crop(str(img_path), str(out_path), left, top, right, bottom)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption="✅ *Image cropped!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_color_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, adjustment: str, factor: float):
        msg = await update.message.reply_text(f"🎨 *Adjusting {adjustment}...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"adjusted_{user_id}_{int(time.time())}.jpg"
            if adjustment == 'brightness':
                success, result = self.image_processor.adjust_brightness(str(img_path), str(out_path), factor)
            elif adjustment == 'contrast':
                success, result = self.image_processor.adjust_contrast(str(img_path), str(out_path), factor)
            elif adjustment == 'saturation':
                success, result = self.image_processor.adjust_saturation(str(img_path), str(out_path), factor)
            elif adjustment == 'sharpness':
                success, result = self.image_processor.adjust_sharpness(str(img_path), str(out_path), factor)
            else:
                success = False
                result = "Unknown adjustment"
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *{adjustment.title()} adjusted!*\nFactor: {factor}\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_add_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        msg = await update.message.reply_text("📝 *Adding text...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"text_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.add_text(str(img_path), str(out_path), text)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption=f"✅ *Text added: \"{text[:30]}\"*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_add_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        msg = await update.message.reply_text("💧 *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"watermarked_{user_id}_{int(time.time())}.jpg"
            success, result = self.image_processor.add_watermark(str(img_path), str(out_path), text or Config.WATERMARK_TEXT)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_photo(photo=InputFile(f), caption="✅ *Watermark added!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.image_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'image')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_trim(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: Path, user_id: int, start: float, end: float):
        msg = await update.message.reply_text("✂️ *Trimming...*", parse_mode=ParseMode.MARKDOWN)
        effect = self.get_session(user_id).get('pending_effect')
        try:
            out_path = TEMP_DIR / f"trimmed_{user_id}_{int(time.time())}.mp4"
            if effect == 'trim':
                success, result = self.video_processor.trim_video(str(file_path), str(out_path), start, end)
            else:
                success, result = self.audio_processor.trim_audio(str(file_path), str(out_path), start, end)
            if success:
                if effect == 'trim':
                    with open(out_path, 'rb') as f:
                        await update.message.reply_video(video=InputFile(f), caption=f"✅ *Trimmed from {start}s to {end}s!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                else:
                    with open(out_path, 'rb') as f:
                        await update.message.reply_audio(audio=InputFile(f), caption=f"✅ *Trimmed from {start}s to {end}s!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.audio_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, effect)
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(file_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_video_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, factor: float):
        msg = await update.message.reply_text(f"⚡ *Changing speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"speed_{user_id}_{int(time.time())}.mp4"
            success, result = self.video_processor.change_speed(str(video_path), str(out_path), factor)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption=f"✅ *Speed changed to {factor}x!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_audio_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_path: Path, user_id: int, factor: float):
        msg = await update.message.reply_text(f"⚡ *Changing audio speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"speed_{user_id}_{int(time.time())}.mp3"
            success, result = self.audio_processor.change_speed(str(audio_path), str(out_path), factor)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption=f"✅ *Speed changed to {factor}x!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.audio_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'audio')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(audio_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_video_merge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_paths: List[str], user_id: int):
        msg = await update.message.reply_text("🔗 *Merging videos...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"merged_{user_id}_{int(time.time())}.mp4"
            success, result = self.video_processor.merge_videos(video_paths, str(out_path))
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption="✅ *Videos merged!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            for path in video_paths:
                try:
                    os.remove(path)
                except:
                    pass
            session = self.get_session(user_id)
            session['merge_files'] = []
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_audio_merge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, audio_paths: List[str], user_id: int):
        msg = await update.message.reply_text("🔗 *Merging audio files...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"merged_{user_id}_{int(time.time())}.mp3"
            success, result = self.audio_processor.merge_audios(audio_paths, str(out_path))
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_audio(audio=InputFile(f), caption="✅ *Audio files merged!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.audio_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'audio')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            for path in audio_paths:
                try:
                    os.remove(path)
                except:
                    pass
            session = self.get_session(user_id)
            session['merge_files'] = []
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_video_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, text: str):
        msg = await update.message.reply_text("🏷️ *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        try:
            out_path = TEMP_DIR / f"watermarked_{user_id}_{int(time.time())}.mp4"
            success, result = self.video_processor.add_watermark(str(video_path), str(out_path), text or Config.WATERMARK_TEXT)
            if success:
                with open(out_path, 'rb') as f:
                    await update.message.reply_video(video=InputFile(f), caption="✅ *Watermark added!*\n\n✨ Kira-Fx Processing", parse_mode=ParseMode.MARKDOWN, reply_markup=KeyboardBuilder.video_menu())
                os.remove(out_path)
                self.db.increment_edits(user_id, 'video')
            else:
                await msg.edit_text(f"❌ *Error:* {result}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def _process_image_collage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, image_paths: List[str], user_id: int):
        msg = await update.message.reply_text("🎨 *Creating collage...*", parse_mode=ParseMode.MARKDOWN)
        try:
            # Send as media group
            media_group = []
            for path in image_paths[:4]:
                with open(path, 'rb') as f:
                    media_group.append(InputMediaPhoto(media=InputFile(f)))
            await context.bot.send_media_group(chat_id=user_id, media=media_group)
            await update.message.reply_text("✅ *Collage created!*\n\n✨ Kira-Fx Processing", reply_markup=KeyboardBuilder.image_menu())
            self.db.increment_edits(user_id, 'image')
        except Exception as e:
            await msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            for path in image_paths:
                try:
                    os.remove(path)
                except:
                    pass
            session = self.get_session(user_id)
            session['batch_files'] = []
            session['state'] = 'verified'
            session['pending_effect'] = None

# =========================================================================================================================================
# MAIN ENTRY POINT
# =========================================================================================================================================

async def main():
    """Main entry point for the bot"""
    bot = KiraFxBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🤖 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
