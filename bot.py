#!/usr/bin/env python3
"""
KiraFx Media Editor Bot v6.0 - ULTRA PREMIUM EDITION
Complete Video & Image Editing Suite with 50+ Admin Tools
Features: Advanced Rename+Metadata, 144p-4K Compression, Fixed Inline Buttons,
          Fixed addcmd (text/code/media), Web App Dashboard, Font Welcome Menus
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
import threading
import hashlib
import platform
import psutil
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
from flask import Flask, jsonify, render_template_string
from threading import Thread
from collections import deque
import heapq

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

BOT_START_TIME = datetime.now()

# ==================== FLASK WEB DASHBOARD ====================
flask_app = Flask(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KiraFx Bot Dashboard</title>
<meta http-equiv="refresh" content="30">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',sans-serif; background:linear-gradient(135deg,#0f0c29,#302b63,#24243e); min-height:100vh; color:#fff; }
.header { background:rgba(255,255,255,0.05); padding:20px; text-align:center; border-bottom:1px solid rgba(255,255,255,0.1); }
.header h1 { font-size:2em; background:linear-gradient(90deg,#f093fb,#f5576c,#4facfe); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.header p { color:#aaa; margin-top:5px; }
.badge { display:inline-block; background:#00c853; color:#fff; padding:3px 12px; border-radius:20px; font-size:0.8em; margin-left:10px; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.7} }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; padding:30px; max-width:1200px; margin:0 auto; }
.card { background:rgba(255,255,255,0.07); border-radius:16px; padding:25px; border:1px solid rgba(255,255,255,0.1); transition:transform 0.2s,box-shadow 0.2s; }
.card:hover { transform:translateY(-3px); box-shadow:0 10px 30px rgba(0,0,0,0.3); }
.card .icon { font-size:2.5em; margin-bottom:10px; }
.card .value { font-size:2em; font-weight:700; color:#4facfe; }
.card .label { color:#aaa; font-size:0.9em; margin-top:5px; }
.section { max-width:1200px; margin:0 auto; padding:0 30px 30px; }
.section h2 { font-size:1.3em; color:#f093fb; margin-bottom:15px; border-left:3px solid #f093fb; padding-left:10px; }
.info-table { width:100%; border-collapse:collapse; }
.info-table tr { border-bottom:1px solid rgba(255,255,255,0.05); }
.info-table td { padding:10px 15px; }
.info-table td:first-child { color:#aaa; width:40%; }
.info-table td:last-child { color:#fff; font-weight:500; }
.status-dot { display:inline-block; width:10px; height:10px; border-radius:50%; background:#00c853; margin-right:8px; animation:pulse 2s infinite; }
.footer { text-align:center; padding:20px; color:#666; font-size:0.85em; }
.tools-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }
.tool-badge { background:rgba(79,172,254,0.15); border:1px solid rgba(79,172,254,0.3); border-radius:8px; padding:8px 12px; text-align:center; font-size:0.85em; color:#4facfe; }
</style>
</head>
<body>
<div class="header">
  <h1>🤖 KiraFx Media Editor Bot <span class="badge">● ONLINE</span></h1>
  <p>Premium Priority Edition v6.0 &nbsp;|&nbsp; Refreshes every 30s</p>
</div>

<div class="grid">
  <div class="card"><div class="icon">👥</div><div class="value">{{ stats.total_users }}</div><div class="label">Total Users</div></div>
  <div class="card"><div class="icon">⭐</div><div class="value">{{ stats.premium_users }}</div><div class="label">Premium Users</div></div>
  <div class="card"><div class="icon">✏️</div><div class="value">{{ stats.total_edits }}</div><div class="label">Total Edits</div></div>
  <div class="card"><div class="icon">📅</div><div class="value">{{ stats.today_edits }}</div><div class="label">Today's Edits</div></div>
  <div class="card"><div class="icon">📝</div><div class="value">{{ stats.total_renames }}</div><div class="label">Files Renamed</div></div>
  <div class="card"><div class="icon">🚫</div><div class="value">{{ stats.banned_users }}</div><div class="label">Banned Users</div></div>
</div>

<div class="section">
  <h2>⚡ Bot Status</h2>
  <table class="info-table">
    <tr><td>Status</td><td><span class="status-dot"></span>Online & Running</td></tr>
    <tr><td>Uptime</td><td>{{ uptime }}</td></tr>
    <tr><td>Platform</td><td>{{ platform }}</td></tr>
    <tr><td>Python Version</td><td>{{ python_version }}</td></tr>
    <tr><td>Memory Usage</td><td>{{ memory_mb }} MB</td></tr>
    <tr><td>CPU Usage</td><td>{{ cpu_percent }}%</td></tr>
    <tr><td>Queue Pending</td><td>{{ stats.queue_pending }}</td></tr>
    <tr><td>FFmpeg</td><td>{{ ffmpeg_status }}</td></tr>
    <tr><td>Whisper AI</td><td>{{ whisper_status }}</td></tr>
  </table>
</div>

<div class="section">
  <h2>🛠️ Available Tools</h2>
  <div class="tools-grid">
    <div class="tool-badge">30+ Image Filters</div>
    <div class="tool-badge">35+ Video Effects</div>
    <div class="tool-badge">10+ AI Tools</div>
    <div class="tool-badge">144p-4K Export</div>
    <div class="tool-badge">File Rename</div>
    <div class="tool-badge">Metadata Edit</div>
    <div class="tool-badge">50+ Admin Tools</div>
    <div class="tool-badge">Custom Commands</div>
    <div class="tool-badge">Auto-Reply</div>
    <div class="tool-badge">Referral System</div>
    <div class="tool-badge">Priority Queue</div>
    <div class="tool-badge">Broadcast</div>
  </div>
</div>

<div class="footer">
  KiraFx Media Editor Bot v6.0 &nbsp;|&nbsp; Last updated: {{ now }}
</div>
</body>
</html>"""

def get_uptime():
    delta = datetime.now() - BOT_START_TIME
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    d = delta.days
    if d > 0:
        return f"{d}d {h%24}h {m}m"
    return f"{h}h {m}m {s}s"

@flask_app.route('/')
def dashboard():
    try:
        stats = db.get_stats()
    except:
        stats = {'total_users':0,'premium_users':0,'total_edits':0,'today_edits':0,
                 'total_renames':0,'banned_users':0,'queue_pending':0,'total_ads':0,'total_commands':0}
    proc = psutil.Process(os.getpid())
    mem = proc.memory_info().rss / (1024*1024)
    cpu = psutil.cpu_percent(interval=0.1)
    ffmpeg_ok = "✅ Available" if shutil.which('ffmpeg') else "❌ Not Found"
    whisper_ok = "✅ Available" if WHISPER_AVAILABLE else "❌ Not Installed"
    return render_template_string(DASHBOARD_HTML,
        stats=stats, uptime=get_uptime(),
        platform=platform.system() + " " + platform.release(),
        python_version=platform.python_version(),
        memory_mb=f"{mem:.1f}", cpu_percent=f"{cpu:.1f}",
        ffmpeg_status=ffmpeg_ok, whisper_status=whisper_ok,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@flask_app.route('/health')
def health():
    return jsonify({'status': 'alive', 'uptime': get_uptime(), 'timestamp': datetime.now().isoformat()})

@flask_app.route('/stats')
def stats_api():
    try:
        return jsonify(db.get_stats())
    except:
        return jsonify({'error': 'db not ready'})

@flask_app.route('/alive')
def alive():
    return jsonify({'alive': True, 'bot': 'KiraFx Media Editor Bot v6.0', 'uptime': get_uptime()})

def run_flask():
    import logging as lg
    log = lg.getLogger('werkzeug')
    log.setLevel(lg.ERROR)
    flask_app.run(host='0.0.0.0', port=5000, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ==================== LOGGING SETUP ====================
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== PRIORITY QUEUE ====================
class PriorityQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.processing = False

    def add_task(self, user_id, task_func, priority=0):
        with self.lock:
            heapq.heappush(self.queue, (-priority, time.time(), user_id, task_func))
        return True

    async def process_next(self):
        with self.lock:
            if self.processing or not self.queue:
                return False
            self.processing = True
        try:
            _, _, user_id, task_func = heapq.heappop(self.queue)
            await task_func()
            return True
        except Exception as e:
            logger.error(f"Queue error: {e}")
            return False
        finally:
            with self.lock:
                self.processing = False

task_queue = PriorityQueue()

# ==================== CONFIGURATION ====================
class Config:
    API_ID = int(os.environ.get("API_ID", "27806628"))
    API_HASH = os.environ.get("API_HASH", "25d88301e886b82826a525b7cf52e090")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8623600399:AAGNn_d6Lq5DRrwelD_rvOUfgsM-jyk8Kf8")
    OWNER_ID = int(os.environ.get("OWNER_ID", 8525952693))

    DB_PATH = "media_bot.db"
    TEMP_DIR = "temp_media"
    THUMB_DIR = "thumbnails"
    FONTS_DIR = "fonts"
    STICKERS_DIR = "stickers"
    EFFECTS_DIR = "effects"
    BACKUP_DIR = "backups"
    LOGS_DIR = "logs"

    MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024
    MAX_IMAGE_SIZE = 100 * 1024 * 1024
    MAX_DOCUMENT_SIZE = 2 * 1024 * 1024 * 1024

    PREMIUM_PRICE = os.environ.get("PREMIUM_PRICE", "$9.99/month | $49.99/year")
    PREMIUM_LINK = os.environ.get("PREMIUM_LINK", "https://t.me/yourpaymentbot")
    FREE_TRIAL_DAYS = 7
    MAX_FREE_EDITS = 10

    PREMIUM_PRIORITY = 1
    NORMAL_PRIORITY = 0
    ADMIN_PRIORITY = 2

    PREMIUM_TIMEOUT = 600
    NORMAL_TIMEOUT = 300

    INLINE_CACHE_TIME = 0
    INLINE_PAGE_SIZE = 8
    INLINE_PRELOAD = True

    GOOGLE_ADS_ENABLED = os.environ.get("GOOGLE_ADS_ENABLED", "True") == "True"
    ADS_CLIENT_ID = os.environ.get("ADS_CLIENT_ID", "ca-pub-xxxxxxxxxxxxx")
    ADS_SLOT_ID = os.environ.get("ADS_SLOT_ID", "1234567890")
    ADS_TEXT = "⭐ **Premium Users:** No ads ever!\n\n[Click Here to Support](https://www.google.com)"
    ADS_INTERVAL = 3

    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")
    FORCE_SUB_CHANNEL_ID = int(os.environ.get("FORCE_SUB_CHANNEL_ID", "0")) if os.environ.get("FORCE_SUB_CHANNEL_ID") else None
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/yourchannel")
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "https://t.me/yourgroup")

    WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "KiraFx")
    WATERMARK_OPACITY = 128
    WATERMARK_POSITION = "bottom_right"
    WATERMARK_ENABLED = os.environ.get("WATERMARK_ENABLED", "True") == "True"

    ENABLE_CACHE = True
    CACHE_DURATION_HOURS = 24
    MAX_PARALLEL_JOBS = 5
    PROCESSING_TIMEOUT = 300
    ENABLE_FFMPEG_LOGS = False

    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
    TTS_LANG = os.environ.get("TTS_LANG", "en")

    SUPPORTED_VIDEO = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"]
    SUPPORTED_IMAGE = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".ico"]
    SUPPORTED_AUDIO = [".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus"]

    VIDEO_QUALITY_PRESETS = {
        "144p":  {"width": 256,  "height": 144,  "bitrate": "200k",   "audio": "64k",  "crf": 30, "preset": "ultrafast"},
        "240p":  {"width": 426,  "height": 240,  "bitrate": "400k",   "audio": "96k",  "crf": 28, "preset": "superfast"},
        "360p":  {"width": 640,  "height": 360,  "bitrate": "800k",   "audio": "96k",  "crf": 26, "preset": "veryfast"},
        "480p":  {"width": 854,  "height": 480,  "bitrate": "1200k",  "audio": "128k", "crf": 24, "preset": "fast"},
        "720p":  {"width": 1280, "height": 720,  "bitrate": "2500k",  "audio": "128k", "crf": 23, "preset": "fast"},
        "1080p": {"width": 1920, "height": 1080, "bitrate": "5000k",  "audio": "192k", "crf": 22, "preset": "medium"},
        "1440p": {"width": 2560, "height": 1440, "bitrate": "8000k",  "audio": "256k", "crf": 21, "preset": "medium"},
        "2k":    {"width": 2560, "height": 1440, "bitrate": "8000k",  "audio": "256k", "crf": 21, "preset": "medium"},
        "4k":    {"width": 3840, "height": 2160, "bitrate": "20000k", "audio": "320k", "crf": 18, "preset": "slow"},
    }

    TIMELINE_PRESETS = {
        "instagram": {"width": 1080, "height": 1080, "fps": 30, "duration": 60},
        "youtube":   {"width": 1920, "height": 1080, "fps": 30, "duration": 600},
        "tiktok":    {"width": 1080, "height": 1920, "fps": 30, "duration": 60},
        "facebook":  {"width": 1280, "height": 720,  "fps": 30, "duration": 120},
        "twitter":   {"width": 1280, "height": 720,  "fps": 30, "duration": 140},
        "reels":     {"width": 1080, "height": 1920, "fps": 30, "duration": 90},
    }

    BOT_NAME = os.environ.get("BOT_NAME", "KiraFx Media Editor Bot")
    BOT_VERSION = "6.0.0"

    for d in [TEMP_DIR, THUMB_DIR, FONTS_DIR, STICKERS_DIR, EFFECTS_DIR, BACKUP_DIR, LOGS_DIR]:
        os.makedirs(d, exist_ok=True)


# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_all_tables()
        self._migrate_database()

    def _create_all_tables(self):
        self.cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
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
            renamed_files INTEGER DEFAULT 0,
            processing_priority INTEGER DEFAULT 0,
            trial_used INTEGER DEFAULT 0,
            bio TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_date INTEGER,
            permissions TEXT DEFAULT 'full',
            can_manage_users INTEGER DEFAULT 1,
            can_manage_premium INTEGER DEFAULT 1,
            can_broadcast INTEGER DEFAULT 1,
            can_manage_commands INTEGER DEFAULT 1,
            can_view_stats INTEGER DEFAULT 1,
            can_backup INTEGER DEFAULT 1,
            title TEXT DEFAULT 'Admin'
        );
        CREATE TABLE IF NOT EXISTS custom_commands (
            command TEXT PRIMARY KEY,
            response TEXT DEFAULT '',
            response_type TEXT DEFAULT 'text',
            media_type TEXT,
            media_file_id TEXT,
            is_code INTEGER DEFAULT 0,
            code_language TEXT DEFAULT '',
            buttons TEXT DEFAULT '',
            created_by INTEGER,
            created_date INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            description TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_by INTEGER,
            updated_date INTEGER
        );
        CREATE TABLE IF NOT EXISTS edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_type TEXT,
            operation TEXT,
            input_size INTEGER DEFAULT 0,
            output_size INTEGER DEFAULT 0,
            processing_time REAL DEFAULT 0,
            timestamp INTEGER,
            status TEXT DEFAULT 'completed'
        );
        CREATE TABLE IF NOT EXISTS processing_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_path TEXT,
            operation TEXT,
            params TEXT,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            config TEXT,
            created_by INTEGER,
            is_public INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            thumbnail TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            session_data TEXT,
            step TEXT,
            updated_at INTEGER,
            media_path TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS auto_reply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            response TEXT,
            match_type TEXT DEFAULT 'exact',
            is_active INTEGER DEFAULT 1,
            media_file_id TEXT DEFAULT '',
            media_type TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            timestamp INTEGER,
            reward_given INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rename_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_name TEXT,
            new_name TEXT,
            file_size INTEGER DEFAULT 0,
            file_type TEXT,
            timestamp INTEGER
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount TEXT,
            transaction_id TEXT,
            plan TEXT,
            status TEXT,
            timestamp INTEGER
        );
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT DEFAULT '',
            banned_by INTEGER DEFAULT 0,
            banned_date INTEGER DEFAULT 0,
            ban_duration INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS broadcast_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message_text TEXT,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            timestamp INTEGER
        );
        CREATE TABLE IF NOT EXISTS user_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            file_type TEXT,
            file_name TEXT,
            file_size INTEGER DEFAULT 0,
            timestamp INTEGER
        );
        ''')
        self.conn.commit()

    def _migrate_database(self):
        columns = [
            ("users", "trial_used", "INTEGER DEFAULT 0"),
            ("users", "bio", "TEXT DEFAULT ''"),
            ("admins", "title", "TEXT DEFAULT 'Admin'"),
            ("custom_commands", "response_type", "TEXT DEFAULT 'text'"),
            ("custom_commands", "is_code", "INTEGER DEFAULT 0"),
            ("custom_commands", "code_language", "TEXT DEFAULT ''"),
            ("custom_commands", "buttons", "TEXT DEFAULT ''"),
            ("custom_commands", "description", "TEXT DEFAULT ''"),
            ("auto_reply", "media_file_id", "TEXT DEFAULT ''"),
            ("auto_reply", "media_type", "TEXT DEFAULT ''"),
        ]
        for table, col, col_type in columns:
            try:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def get_priority(self, user_id):
        if self.is_admin(user_id):
            return Config.ADMIN_PRIORITY
        if self.is_premium(user_id):
            return Config.PREMIUM_PRIORITY
        return Config.NORMAL_PRIORITY

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
            logger.error(f"add_user error: {e}")
            return False

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()

    def search_user(self, query):
        try:
            uid = int(query)
            self.cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
            r = self.cursor.fetchone()
            return [r] if r else []
        except ValueError:
            self.cursor.execute("SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ?",
                               (f"%{query}%", f"%{query}%"))
            return self.cursor.fetchall()

    def is_premium(self, user_id):
        self.cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result and result["premium_until"]:
            return result["premium_until"] > int(datetime.now().timestamp())
        return False

    def get_premium_expiry(self, user_id):
        self.cursor.execute("SELECT premium_until FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result["premium_until"] if result else 0

    def give_premium(self, user_id, days, source="admin"):
        now = int(datetime.now().timestamp())
        current = self.get_premium_expiry(user_id)
        base = max(now, current)
        until = base + (days * 86400)
        self.cursor.execute("UPDATE users SET premium_until=?, processing_priority=? WHERE user_id=?",
                           (until, Config.PREMIUM_PRIORITY, user_id))
        self.conn.commit()
        return until

    def remove_premium(self, user_id):
        self.cursor.execute("UPDATE users SET premium_until=0, processing_priority=0 WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_all_premium_users(self):
        now = int(datetime.now().timestamp())
        self.cursor.execute("SELECT user_id, username, first_name, premium_until FROM users WHERE premium_until > ?", (now,))
        return self.cursor.fetchall()

    def can_edit(self, user_id):
        if self.is_premium(user_id) or self.is_admin(user_id):
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
            SET edits_today=edits_today+1, total_edits=total_edits+1, edit_count=edit_count+1,
                last_edit_date=?
            WHERE user_id=?''', (today, user_id))
        self.conn.commit()
        self.cursor.execute("SELECT edits_today FROM users WHERE user_id=?", (user_id,))
        row = self.cursor.fetchone()
        edits = row["edits_today"] if row else 0
        interval = int(self.get_setting('ads_interval', Config.ADS_INTERVAL))
        return edits % interval == 0 and not self.is_premium(user_id)

    def add_coins(self, user_id, amount):
        self.cursor.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, user_id))
        self.conn.commit()

    def get_coins(self, user_id):
        self.cursor.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result["coins"] if result else 0

    def add_edit_history(self, user_id, file_type, operation, input_size, output_size, processing_time, status='completed'):
        self.cursor.execute('''INSERT INTO edit_history
            (user_id, file_type, operation, input_size, output_size, processing_time, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, file_type, operation, input_size, output_size, processing_time,
             int(datetime.now().timestamp()), status))
        self.conn.commit()

    def add_to_queue(self, user_id, file_path, operation, params):
        priority = self.get_priority(user_id)
        self.cursor.execute('''INSERT INTO processing_queue
            (user_id, file_path, operation, params, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, file_path, operation, json.dumps(params), priority, int(datetime.now().timestamp())))
        self.conn.commit()
        return self.cursor.lastrowid

    def is_admin(self, user_id):
        if user_id == Config.OWNER_ID:
            return True
        self.cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
        return self.cursor.fetchone() is not None

    def add_admin(self, user_id, added_by, permissions="full", title="Admin"):
        self.cursor.execute('''INSERT OR IGNORE INTO admins
            (user_id, added_by, added_date, permissions, title)
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, added_by, int(datetime.now().timestamp()), permissions, title))
        self.conn.commit()

    def remove_admin(self, user_id):
        self.cursor.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_all_admins(self):
        self.cursor.execute("SELECT user_id, title FROM admins")
        return self.cursor.fetchall()

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
            self.cursor.execute("SELECT ban_duration, banned_date FROM banned_users WHERE user_id=?", (user_id,))
            ban_info = self.cursor.fetchone()
            if ban_info and ban_info["ban_duration"] > 0:
                expiry = ban_info["banned_date"] + (ban_info["ban_duration"] * 86400)
                if expiry < int(datetime.now().timestamp()):
                    self.unban_user(user_id)
                    return False
            return True
        return False

    def get_banned_users(self):
        self.cursor.execute("SELECT b.*, u.username, u.first_name FROM banned_users b LEFT JOIN users u ON b.user_id=u.user_id")
        return self.cursor.fetchall()

    def add_rename_record(self, user_id, original_name, new_name, file_size, file_type):
        self.cursor.execute('''INSERT INTO rename_history
            (user_id, original_name, new_name, file_size, file_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, original_name, new_name, file_size, file_type, int(datetime.now().timestamp())))
        self.cursor.execute("UPDATE users SET renamed_files=renamed_files+1 WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_rename_history(self, user_id, limit=10):
        self.cursor.execute("SELECT * FROM rename_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        return self.cursor.fetchall()

    def get_custom_command(self, command):
        self.cursor.execute('''SELECT * FROM custom_commands WHERE command=? AND is_active=1''', (command,))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE custom_commands SET usage_count=usage_count+1 WHERE command=?", (command,))
            self.conn.commit()
            return dict(result)
        return None

    def add_custom_command(self, command, response="", response_type="text", media_type=None,
                           media_id=None, is_code=False, code_lang="", buttons="",
                           created_by=None, description=""):
        self.cursor.execute('''REPLACE INTO custom_commands
            (command, response, response_type, media_type, media_file_id, is_code, code_language,
             buttons, created_by, created_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (command, response, response_type, media_type, media_id, 1 if is_code else 0,
             code_lang, buttons, created_by, int(datetime.now().timestamp()), description))
        self.conn.commit()

    def delete_custom_command(self, command):
        self.cursor.execute("DELETE FROM custom_commands WHERE command=?", (command,))
        self.conn.commit()

    def toggle_custom_command(self, command):
        self.cursor.execute("SELECT is_active FROM custom_commands WHERE command=?", (command,))
        row = self.cursor.fetchone()
        if row:
            new_state = 0 if row["is_active"] else 1
            self.cursor.execute("UPDATE custom_commands SET is_active=? WHERE command=?", (new_state, command))
            self.conn.commit()
            return new_state
        return None

    def get_all_custom_commands(self):
        self.cursor.execute("SELECT * FROM custom_commands ORDER BY command")
        return self.cursor.fetchall()

    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = self.cursor.fetchone()
        return result["value"] if result else default

    def set_setting(self, key, value, updated_by=None):
        self.cursor.execute('''REPLACE INTO settings (key, value, updated_by, updated_date)
            VALUES (?, ?, ?, ?)''',
            (key, str(value), updated_by, int(datetime.now().timestamp())))
        self.conn.commit()

    def get_all_settings(self):
        self.cursor.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in self.cursor.fetchall()}

    def set_session(self, user_id, step, data, media_path=None):
        self.cursor.execute('''REPLACE INTO user_sessions
            (user_id, session_data, step, updated_at, media_path)
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, json.dumps(data), step, int(datetime.now().timestamp()), media_path or ""))
        self.conn.commit()

    def get_session(self, user_id):
        self.cursor.execute("SELECT session_data, step, media_path FROM user_sessions WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            try:
                data = json.loads(result["session_data"])
            except:
                data = {}
            return data, result["step"], result["media_path"]
        return None, None, None

    def clear_session(self, user_id):
        self.cursor.execute("DELETE FROM user_sessions WHERE user_id=?", (user_id,))
        self.conn.commit()

    def add_referral(self, referrer_id, referred_id):
        self.cursor.execute("SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,))
        if self.cursor.fetchone():
            return False
        self.cursor.execute('''INSERT INTO referrals (referrer_id, referred_id, timestamp, reward_given)
            VALUES (?, ?, ?, 1)''',
            (referrer_id, referred_id, int(datetime.now().timestamp())))
        if self.cursor.rowcount > 0:
            self.give_premium(referrer_id, 3, "referral")
            self.add_coins(referrer_id, 100)
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def get_referral_count(self, user_id):
        self.cursor.execute("SELECT COUNT(*) as c FROM referrals WHERE referrer_id=?", (user_id,))
        return self.cursor.fetchone()["c"]

    def get_top_users(self, limit=10):
        self.cursor.execute("SELECT user_id, username, first_name, total_edits FROM users ORDER BY total_edits DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_top_referrers(self, limit=10):
        self.cursor.execute("SELECT referrer_id, COUNT(*) as cnt FROM referrals GROUP BY referrer_id ORDER BY cnt DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_stats(self):
        now = int(datetime.now().timestamp())
        total_users = self.cursor.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        premium_users = self.cursor.execute("SELECT COUNT(*) as c FROM users WHERE premium_until > ?", (now,)).fetchone()["c"]
        banned_users = self.cursor.execute("SELECT COUNT(*) as c FROM users WHERE banned=1").fetchone()["c"]
        total_edits = self.cursor.execute("SELECT SUM(total_edits) as t FROM users").fetchone()["t"] or 0
        today = datetime.now().strftime("%Y-%m-%d")
        today_edits = self.cursor.execute("SELECT SUM(edits_today) as t FROM users WHERE last_edit_date=?", (today,)).fetchone()["t"] or 0
        total_ads = self.cursor.execute("SELECT SUM(total_ads_watched) as t FROM users").fetchone()["t"] or 0
        total_renames = self.cursor.execute("SELECT COUNT(*) as c FROM rename_history").fetchone()["c"]
        total_commands = self.cursor.execute("SELECT SUM(usage_count) as t FROM custom_commands").fetchone()["t"] or 0
        queue_pending = self.cursor.execute("SELECT COUNT(*) as c FROM processing_queue WHERE status='pending'").fetchone()["c"]
        return {
            'total_users': total_users, 'premium_users': premium_users, 'banned_users': banned_users,
            'total_edits': total_edits, 'today_edits': today_edits, 'total_ads': total_ads,
            'total_renames': total_renames, 'total_commands': total_commands, 'queue_pending': queue_pending
        }

    def get_daily_stats(self):
        stats = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            edits = self.cursor.execute("SELECT SUM(edits_today) as t FROM users WHERE last_edit_date=?", (date,)).fetchone()["t"] or 0
            stats[date] = edits
        return stats

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

    def cleanup_temp_files(self, age_hours=1):
        cutoff = time.time() - (age_hours * 3600)
        count = 0
        if os.path.exists(Config.TEMP_DIR):
            for f in os.listdir(Config.TEMP_DIR):
                fp = os.path.join(Config.TEMP_DIR, f)
                try:
                    if os.path.getctime(fp) < cutoff:
                        os.unlink(fp)
                        count += 1
                except:
                    pass
        return count

    def get_db_size(self):
        return os.path.getsize(Config.DB_PATH) if os.path.exists(Config.DB_PATH) else 0

    def get_recent_edits(self, limit=10):
        self.cursor.execute('''SELECT h.user_id, u.username, u.first_name, h.operation, h.file_type, h.timestamp
            FROM edit_history h LEFT JOIN users u ON h.user_id=u.user_id
            ORDER BY h.timestamp DESC LIMIT ?''', (limit,))
        return self.cursor.fetchall()

    def add_auto_reply(self, keyword, response, match_type="exact", media_file_id="", media_type=""):
        self.cursor.execute('''INSERT OR REPLACE INTO auto_reply
            (keyword, response, match_type, is_active, media_file_id, media_type)
            VALUES (?, ?, ?, 1, ?, ?)''',
            (keyword, response, match_type, media_file_id, media_type))
        self.conn.commit()

    def delete_auto_reply(self, keyword):
        self.cursor.execute("DELETE FROM auto_reply WHERE keyword=?", (keyword,))
        self.conn.commit()

    def get_all_auto_replies(self):
        self.cursor.execute("SELECT * FROM auto_reply WHERE is_active=1")
        return self.cursor.fetchall()


db = Database()

# Initialize default settings
_defaults = {
    'welcome_text': f"""╔══════════════════════════╗
║  🎬 KiraFx Media Editor  ║
╚══════════════════════════╝

✨ <b>Complete Media Editing Suite v6.0</b>

📸 <b>30+ Image Editing Tools</b>
🎬 <b>35+ Video Editing Tools</b>
🎥 <b>144p → 4K Compression</b>
🤖 <b>AI-Powered Features</b>
📝 <b>Advanced Rename + Metadata</b>
👑 <b>50+ Admin Panel Tools</b>

⚡ <b>Premium Priority Processing</b>
• Faster queue processing
• Unlimited daily edits
• No watermark • No ads
• 4K export • All AI tools

🎁 <b>7-Day Free Trial:</b> /trial
📢 Send any photo or video to start!

<i>Made with ❤️ by KiraFx Team</i>""",
    'watermark_enabled': '1',
    'watermark_text': Config.WATERMARK_TEXT,
    'ads_enabled': '1',
    'ads_interval': str(Config.ADS_INTERVAL),
    'free_edits': str(Config.MAX_FREE_EDITS),
    'maintenance_mode': '0',
    'bot_name': Config.BOT_NAME,
}
for k, v in _defaults.items():
    if db.get_setting(k) is None:
        db.set_setting(k, v)


# ==================== FAST INLINE KEYBOARD MANAGER ====================
class InlineKB:
    @staticmethod
    def paginate(items, page, per_page=8):
        start = page * per_page
        end = start + per_page
        return items[start:end], len(items) > end

    @staticmethod
    def back_row(target="main_menu", label="🔙 Main Menu"):
        return [InlineKeyboardButton(label, callback_data=target)]

    @staticmethod
    def main_menu(user_id):
        is_prem = db.is_premium(user_id)
        is_adm = db.is_admin(user_id)
        rows = [
            [InlineKeyboardButton("🎨 Image Editor (30+)", callback_data="menu_image"),
             InlineKeyboardButton("🎬 Video Editor (35+)", callback_data="menu_video")],
            [InlineKeyboardButton("🗜️ Compress Video", callback_data="menu_compress"),
             InlineKeyboardButton("✨ AI Tools", callback_data="menu_ai")],
            [InlineKeyboardButton("📝 Rename + Metadata", callback_data="menu_rename"),
             InlineKeyboardButton("🎞️ Timeline", callback_data="menu_timeline")],
            [InlineKeyboardButton("👥 Referrals", callback_data="menu_refer"),
             InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("⭐ Premium", callback_data="premium_info"),
             InlineKeyboardButton("ℹ️ Help", callback_data="help_info")],
            [InlineKeyboardButton("📢 Updates", url=Config.UPDATE_CHANNEL),
             InlineKeyboardButton("💬 Support", url=Config.SUPPORT_CHAT)],
        ]
        if is_prem:
            rows.insert(4, [InlineKeyboardButton("👑 Premium Features", callback_data="premium_features")])
        else:
            rows.insert(4, [InlineKeyboardButton("🎁 Free Trial (7 Days)", callback_data="free_trial")])
        if is_adm:
            rows.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def image_categories(page=0):
        cats = list(MediaProcessor.IMAGE_FILTERS.keys())
        items, has_next = InlineKB.paginate(cats, page, 6)
        emoji_map = {'basic':'🔧','artistic':'🎨','color':'🌈','transform':'🔄','special':'✨'}
        rows = []
        for cat in items:
            em = emoji_map.get(cat, '📁')
            rows.append([InlineKeyboardButton(f"{em} {cat.title()} Filters", callback_data=f"img_cat:{cat}:{page}")])
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"img_catpage:{page-1}"))
        if has_next: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"img_catpage:{page+1}"))
        if nav: rows.append(nav)
        rows.append(InlineKB.back_row())
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def image_filters(category, page=0):
        filters_list = MediaProcessor.IMAGE_FILTERS.get(category, [])
        items, has_next = InlineKB.paginate(filters_list, page)
        rows = []
        row = []
        for i, (name, fid) in enumerate(items):
            row.append(InlineKeyboardButton(name, callback_data=f"apply_img:{fid}"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"img_filterpage:{category}:{page-1}"))
        if has_next: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"img_filterpage:{category}:{page+1}"))
        if nav: rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Categories", callback_data="menu_image"),
                     InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def video_categories(page=0):
        cats = list(MediaProcessor.VIDEO_EFFECTS.keys())
        items, has_next = InlineKB.paginate(cats, page, 6)
        emoji_map = {'basic':'✂️','filters':'🎨','transitions':'🌊','audio':'🎵','speed':'⚡','ai':'🤖','advanced':'🔧'}
        rows = []
        for cat in items:
            em = emoji_map.get(cat, '🎬')
            rows.append([InlineKeyboardButton(f"{em} {cat.title()}", callback_data=f"vid_cat:{cat}:{page}")])
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"vid_catpage:{page-1}"))
        if has_next: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"vid_catpage:{page+1}"))
        if nav: rows.append(nav)
        rows.append(InlineKB.back_row())
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def video_effects(category, page=0):
        effects_list = MediaProcessor.VIDEO_EFFECTS.get(category, [])
        items, has_next = InlineKB.paginate(effects_list, page)
        rows = []
        row = []
        for i, (name, eid) in enumerate(items):
            row.append(InlineKeyboardButton(name, callback_data=f"apply_vid:{eid}"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"vid_effectpage:{category}:{page-1}"))
        if has_next: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"vid_effectpage:{category}:{page+1}"))
        if nav: rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Categories", callback_data="menu_video"),
                     InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def compress_menu():
        presets = list(Config.VIDEO_QUALITY_PRESETS.keys())
        rows = []
        row = []
        for p in presets:
            row.append(InlineKeyboardButton(p.upper(), callback_data=f"compress:{p}"))
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append(InlineKB.back_row())
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def rename_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Rename File", callback_data="rename_start"),
             InlineKeyboardButton("🏷️ Edit Metadata", callback_data="metadata_start")],
            [InlineKeyboardButton("📜 Rename History", callback_data="rename_history"),
             InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
        ])

    @staticmethod
    def admin_panel():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 User Management", callback_data="adm:users"),
             InlineKeyboardButton("⭐ Premium Mgmt", callback_data="adm:premium")],
            [InlineKeyboardButton("📝 Commands", callback_data="adm:commands"),
             InlineKeyboardButton("🤖 Auto-Reply", callback_data="adm:autoreply")],
            [InlineKeyboardButton("📊 Statistics", callback_data="adm:stats"),
             InlineKeyboardButton("📈 Daily Stats", callback_data="adm:daily")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="adm:broadcast"),
             InlineKeyboardButton("⚙️ Bot Settings", callback_data="adm:settings")],
            [InlineKeyboardButton("💾 Backup/Restore", callback_data="adm:backup"),
             InlineKeyboardButton("📤 Export/Import", callback_data="adm:export")],
            [InlineKeyboardButton("🚫 Ban Management", callback_data="adm:bans"),
             InlineKeyboardButton("👑 Admin List", callback_data="adm:adminlist")],
            [InlineKeyboardButton("💰 Ads Settings", callback_data="adm:ads"),
             InlineKeyboardButton("🗑️ Cleanup", callback_data="adm:cleanup")],
            [InlineKeyboardButton("💾 DB Info", callback_data="adm:dbinfo"),
             InlineKeyboardButton("🔧 Maintenance", callback_data="adm:maintenance")],
            [InlineKeyboardButton("📜 Bot Logs", callback_data="adm:logs"),
             InlineKeyboardButton("🏃 Bot Status", callback_data="adm:botstatus")],
            [InlineKeyboardButton("👥 Top Users", callback_data="adm:topusers"),
             InlineKeyboardButton("🔗 Top Referrers", callback_data="adm:topreferrers")],
            [InlineKeyboardButton("⭐ Premium Users", callback_data="adm:premiumlist"),
             InlineKeyboardButton("📝 Recent Edits", callback_data="adm:recentedits")],
            [InlineKeyboardButton("🔍 Search User", callback_data="adm:searchuser"),
             InlineKeyboardButton("💎 Give Premium", callback_data="adm:givepremium")],
            [InlineKeyboardButton("🔇 Bot Queue", callback_data="adm:queue"),
             InlineKeyboardButton("⚡ Clear Queue", callback_data="adm:clearqueue")],
            [InlineKeyboardButton("🌐 Web Dashboard", url=f"http://localhost:5000"),
             InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
        ])

    @staticmethod
    def admin_user_mgmt():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search User", callback_data="adm:searchuser"),
             InlineKeyboardButton("📋 User Info", callback_data="adm:userinfo")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="adm:banuser"),
             InlineKeyboardButton("✅ Unban User", callback_data="adm:unbanuser")],
            [InlineKeyboardButton("⭐ Add Premium", callback_data="adm:givepremium"),
             InlineKeyboardButton("❌ Remove Premium", callback_data="adm:rmpremium")],
            [InlineKeyboardButton("👑 Add Admin", callback_data="adm:addadmin"),
             InlineKeyboardButton("👤 Remove Admin", callback_data="adm:rmadmin")],
            [InlineKeyboardButton("💰 Add Coins", callback_data="adm:addcoins"),
             InlineKeyboardButton("🚫 View Bans", callback_data="adm:bans")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
        ])

    @staticmethod
    def admin_settings():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Set Welcome", callback_data="adm:setwelcome"),
             InlineKeyboardButton("💧 Set Watermark", callback_data="adm:setwatermark")],
            [InlineKeyboardButton("🔘 Toggle Watermark", callback_data="adm:togglewatermark"),
             InlineKeyboardButton("🔢 Set Free Edits", callback_data="adm:setfreeedits")],
            [InlineKeyboardButton("📢 Toggle Ads", callback_data="adm:toggleads"),
             InlineKeyboardButton("⏱️ Ads Interval", callback_data="adm:setadsinterval")],
            [InlineKeyboardButton("🔒 Maintenance ON", callback_data="adm:maintenanceon"),
             InlineKeyboardButton("🔓 Maintenance OFF", callback_data="adm:maintenanceoff")],
            [InlineKeyboardButton("📋 View All Settings", callback_data="adm:viewsettings"),
             InlineKeyboardButton("🔄 Reset Settings", callback_data="adm:resetsettings")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
        ])


# ==================== MEDIA PROCESSOR ====================
class MediaProcessor:
    IMAGE_FILTERS = {
        'basic': [
            ("🌫️ Blur", "blur"), ("🔪 Sharpen", "sharpen"), ("⚪ Grayscale", "grayscale"),
            ("📜 Sepia", "sepia"), ("✨ Edge Enhance", "edge_enhance"), ("🌀 Contour", "contour"),
            ("🔘 Emboss", "emboss"), ("✨ Smooth", "smooth"), ("🔍 Detail", "detail"),
            ("🌊 Gaussian Blur", "gaussian_blur"), ("✨ Unsharp Mask", "unsharp_mask"),
            ("🔲 Median Filter", "median"),
        ],
        'artistic': [
            ("🎨 Oil Paint", "oil_paint"), ("💧 Watercolor", "watercolor"), ("📝 Sketch", "sketch"),
            ("✏️ Pencil Sketch", "pencil_sketch"), ("🎭 Cartoon", "cartoon"), ("📱 Pixelate", "pixelate"),
            ("✨ Glitch", "glitch"), ("📸 Vintage", "vintage"), ("💡 Neon", "neon"),
            ("🎨 Pointillism", "pointillism"), ("🖼️ Mosaic", "mosaic"), ("🎨 Pastel", "pastel"),
            ("🎨 Comic", "comic"), ("🖼️ Stained Glass", "stained_glass"),
        ],
        'color': [
            ("💡 Brightness", "brightness"), ("🌞 Contrast", "contrast"), ("🌈 Saturation", "saturation"),
            ("🎨 Hue", "hue"), ("🌡️ Temperature", "temperature"), ("🎨 Auto Color", "auto_color"),
            ("⚡ Equalize", "equalize"), ("🎨 Posterize", "posterize"), ("🌓 Solarize", "solarize"),
            ("🔄 Invert", "invert"), ("🎨 Color Balance", "color_balance"), ("🌈 Channel Mixer", "channel_mixer"),
            ("🌅 Golden Hour", "golden_hour"), ("❄️ Cold Tone", "cold_tone"),
        ],
        'transform': [
            ("🔄 Rotate 90°", "rotate_90"), ("🔄 Rotate 180°", "rotate_180"), ("🔄 Rotate 270°", "rotate_270"),
            ("↔️ Flip H", "flip_h"), ("↕️ Flip V", "flip_v"), ("📏 Resize 50%", "resize_50"),
            ("📏 Resize 200%", "resize_200"), ("✂️ Crop Center", "crop_center"), ("🔄 Mirror", "mirror"),
            ("🌀 Skew", "skew"), ("🌀 Perspective", "perspective"), ("🔄 Auto Rotate", "auto_rotate"),
        ],
        'special': [
            ("🎭 Blur BG", "blur_bg"), ("🎭 Vignette", "vignette"), ("🖼️ Border", "border"),
            ("⚪ Rounded", "rounded"), ("📦 Shadow", "shadow"), ("✨ Glow", "glow"),
            ("🎨 Duotone", "duotone"), ("🌅 Sunset", "sunset"), ("❄️ Winter", "winter"),
            ("🍂 Autumn", "autumn"), ("🌸 Spring", "spring"), ("🌙 Night", "night"),
            ("🎇 Firework", "firework"), ("🌊 Wave", "wave"),
        ]
    }

    VIDEO_EFFECTS = {
        'basic': [
            ("✂️ Trim", "trim"), ("✂️ Cut", "cut"), ("🔀 Speed 2x", "speed_2x"),
            ("🐢 Speed 0.5x", "speed_05x"), ("🔄 Reverse", "reverse"), ("🔄 Loop", "loop"),
            ("🔗 Merge", "merge"), ("🎬 Extract GIF", "extract_gif"), ("📸 Extract Frame", "extract_frame"),
            ("✂️ Split Video", "split_video"), ("📏 Change Resolution", "change_resolution"),
            ("🔳 Scale to Square", "scale_square"),
        ],
        'filters': [
            ("⚫ B&W", "black_white"), ("📜 Sepia", "sepia"), ("📽️ Vintage", "vintage"),
            ("🎬 Cinematic", "cinematic"), ("✨ Glitch", "glitch"), ("📱 Pixelate", "pixelate"),
            ("🎨 Oil Paint", "oil_paint_video"), ("📝 Sketch", "sketch_video"), ("🎭 Cartoon", "cartoon_video"),
            ("💡 Neon", "neon_video"), ("🌅 Sunset", "sunset_video"), ("❄️ Winter", "winter_video"),
            ("🎨 Vibrant", "vibrant"), ("🌫️ Haze", "haze"), ("🔮 VHS", "vhs"),
            ("🌈 RGB Shift", "rgb_shift"), ("✨ Soft Glow", "soft_glow"),
        ],
        'transitions': [
            ("🌅 Fade In", "fade_in"), ("🌄 Fade Out", "fade_out"), ("🌌 Fade Black", "fade_black"),
            ("✨ Crossfade", "crossfade"), ("🌀 Zoom In", "zoom_in"), ("🌀 Zoom Out", "zoom_out"),
            ("⬅️ Slide Left", "slide_left"), ("➡️ Slide Right", "slide_right"),
            ("⬆️ Slide Up", "slide_up"), ("⬇️ Slide Down", "slide_down"),
        ],
        'audio': [
            ("🔇 Mute", "mute"), ("🎵 Extract Audio", "extract_audio"), ("🎧 Add Music", "add_audio"),
            ("📢 Volume Up", "volume_up"), ("🔉 Volume Down", "volume_down"), ("🎤 Voiceover", "voiceover"),
            ("🔊 Boost Bass", "boost_bass"), ("🎧 Echo Effect", "echo"), ("🌀 Reverb", "reverb"),
            ("🎚️ Normalize Audio", "normalize_audio"), ("🎵 Fade Audio", "fade_audio"),
        ],
        'speed': [
            ("🐢 0.25x", "speed_025"), ("🐢 0.5x", "speed_05x"), ("⚡ 0.75x", "speed_075"),
            ("⚡ 1.5x", "speed_15x"), ("🐇 2x", "speed_2x"), ("🚀 3x", "speed_3x"),
            ("🚀 4x", "speed_4x"), ("🎬 Time Lapse", "timelapse"), ("🎥 Slow Motion", "slow_motion"),
        ],
        'ai': [
            ("🗣️ AI Speech", "ai_speech"), ("📝 AI Subtitles", "ai_subtitles"),
            ("👤 AI Face Blur", "face_blur"), ("🎨 AI Enhance", "ai_enhance"),
            ("🎬 AI Scene Detect", "scene_detect"), ("📊 AI Analysis", "ai_analysis"),
            ("🎨 AI Colorize", "colorize"), ("🎭 Style Transfer", "style_transfer"),
        ],
        'advanced': [
            ("🎨 Chroma Key", "chroma_key"), ("📝 Text Overlay", "text_overlay"),
            ("💧 Watermark", "watermark"), ("🔄 Rotate", "rotate_video"),
            ("📏 Crop", "crop_video"), ("🎞️ Resize", "resize_video"),
            ("📊 Stabilize", "stabilize"), ("✨ Denoise", "denoise"),
            ("🎨 Color Grading", "color_grading"), ("🎬 PIP", "picture_in_picture"),
        ]
    }

    @staticmethod
    async def download_media(client, file_id, user_id, file_type="video"):
        try:
            os.makedirs(Config.TEMP_DIR, exist_ok=True)
            ext_map = {"video": ".mp4", "image": ".jpg", "document": ".file",
                       "photo": ".jpg", "audio": ".mp3"}
            ext = ext_map.get(file_type, ".mp4")
            ts = int(datetime.now().timestamp())
            rand = random.randint(1000, 9999)
            file_path = os.path.join(Config.TEMP_DIR, f"{user_id}_{ts}_{rand}{ext}")
            downloaded = await client.download_media(message=file_id, file_name=file_path)
            if downloaded and os.path.exists(downloaded):
                return downloaded
            return None
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await MediaProcessor.download_media(client, file_id, user_id, file_type)
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
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            output = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=Config.TEMP_DIR).name

            filters_map = {
                "blur": lambda: img.filter(ImageFilter.BLUR),
                "sharpen": lambda: img.filter(ImageFilter.SHARPEN),
                "grayscale": lambda: img.convert("L").convert("RGB"),
                "sepia": lambda: MediaProcessor._sepia(img),
                "edge_enhance": lambda: img.filter(ImageFilter.EDGE_ENHANCE_MORE),
                "contour": lambda: img.filter(ImageFilter.CONTOUR),
                "emboss": lambda: img.filter(ImageFilter.EMBOSS),
                "smooth": lambda: img.filter(ImageFilter.SMOOTH_MORE),
                "detail": lambda: img.filter(ImageFilter.DETAIL),
                "gaussian_blur": lambda: img.filter(ImageFilter.GaussianBlur(radius=params.get('radius', 3))),
                "unsharp_mask": lambda: img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)),
                "median": lambda: img.filter(ImageFilter.MedianFilter(size=3)),
                "oil_paint": lambda: MediaProcessor._oil_paint(img),
                "watercolor": lambda: MediaProcessor._watercolor(img),
                "sketch": lambda: MediaProcessor._sketch(img),
                "pencil_sketch": lambda: MediaProcessor._pencil_sketch(img),
                "cartoon": lambda: MediaProcessor._cartoon(img),
                "pixelate": lambda: MediaProcessor._pixelate(img, params.get('size', 10)),
                "glitch": lambda: MediaProcessor._glitch(img),
                "vintage": lambda: MediaProcessor._vintage(img),
                "neon": lambda: MediaProcessor._neon(img),
                "pointillism": lambda: MediaProcessor._pixelate(img, 8),
                "mosaic": lambda: MediaProcessor._pixelate(img, 20),
                "pastel": lambda: MediaProcessor._pastel(img),
                "comic": lambda: MediaProcessor._comic(img),
                "stained_glass": lambda: MediaProcessor._stained_glass(img),
                "brightness": lambda: ImageEnhance.Brightness(img).enhance(params.get('factor', 1.5)),
                "contrast": lambda: ImageEnhance.Contrast(img).enhance(params.get('factor', 1.5)),
                "saturation": lambda: ImageEnhance.Color(img).enhance(params.get('factor', 1.8)),
                "hue": lambda: MediaProcessor._adjust_hue(img, params.get('shift', 30)),
                "temperature": lambda: MediaProcessor._adjust_temperature(img, params.get('temp', 7000)),
                "auto_color": lambda: ImageOps.autocontrast(img),
                "equalize": lambda: ImageOps.equalize(img),
                "posterize": lambda: ImageOps.posterize(img, params.get('bits', 4)),
                "solarize": lambda: ImageOps.solarize(img, params.get('threshold', 128)),
                "invert": lambda: ImageOps.invert(img),
                "color_balance": lambda: MediaProcessor._color_balance(img, params),
                "channel_mixer": lambda: MediaProcessor._channel_mixer(img, params),
                "golden_hour": lambda: MediaProcessor._golden_hour(img),
                "cold_tone": lambda: MediaProcessor._cold_tone(img),
                "rotate_90": lambda: img.rotate(90, expand=True),
                "rotate_180": lambda: img.rotate(180, expand=True),
                "rotate_270": lambda: img.rotate(270, expand=True),
                "flip_h": lambda: img.transpose(Image.FLIP_LEFT_RIGHT),
                "flip_v": lambda: img.transpose(Image.FLIP_TOP_BOTTOM),
                "mirror": lambda: img.transpose(Image.FLIP_LEFT_RIGHT),
                "resize_50": lambda: img.resize((img.width//2, img.height//2), Image.Resampling.LANCZOS),
                "resize_200": lambda: img.resize((img.width*2, img.height*2), Image.Resampling.LANCZOS),
                "crop_center": lambda: img.crop((img.width//4, img.height//4, img.width*3//4, img.height*3//4)),
                "skew": lambda: MediaProcessor._skew_image(img, params.get('skew', 20)),
                "perspective": lambda: MediaProcessor._perspective(img, params),
                "auto_rotate": lambda: ImageOps.exif_transpose(img),
                "blur_bg": lambda: MediaProcessor._blur_background(img),
                "vignette": lambda: MediaProcessor._vignette(img),
                "border": lambda: ImageOps.expand(img, border=params.get('size', 15), fill=params.get('color', 'white')),
                "rounded": lambda: MediaProcessor._rounded_corners(img, params.get('radius', 40)),
                "shadow": lambda: MediaProcessor._add_shadow(img),
                "glow": lambda: MediaProcessor._glow_effect(img),
                "duotone": lambda: MediaProcessor._duotone(img),
                "sunset": lambda: MediaProcessor._sunset_filter(img),
                "winter": lambda: MediaProcessor._winter_filter(img),
                "autumn": lambda: MediaProcessor._autumn_filter(img),
                "spring": lambda: MediaProcessor._spring_filter(img),
                "night": lambda: MediaProcessor._night_filter(img),
                "firework": lambda: MediaProcessor._firework_effect(img),
                "wave": lambda: MediaProcessor._wave_effect(img),
            }

            if filter_name in filters_map:
                result = filters_map[filter_name]()
                if isinstance(result, Image.Image):
                    if result.mode != 'RGB':
                        result = result.convert('RGB')
                    result.save(output, quality=95, optimize=True)
                return output
            raise ValueError(f"Unknown filter: {filter_name}")
        except Exception as e:
            logger.error(f"Image filter error [{filter_name}]: {e}")
            raise

    @staticmethod
    async def apply_video_effect(video_path: str, effect: str, params: dict = None) -> str:
        if params is None:
            params = {}
        try:
            output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=Config.TEMP_DIR).name
            effects_map = {
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
                "extract_gif": lambda: MediaProcessor._video_to_gif(video_path, output.replace('.mp4', '.gif')),
                "extract_frame": lambda: MediaProcessor._extract_frame(video_path, output.replace('.mp4', '.jpg')),
                "split_video": lambda: MediaProcessor._split_video(video_path, output),
                "change_resolution": lambda: MediaProcessor._change_resolution(video_path, output, params),
                "scale_square": lambda: MediaProcessor._scale_square(video_path, output),
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
                "vibrant": lambda: MediaProcessor._color_filter(video_path, output, "eq=saturation=1.5:brightness=0.05:contrast=1.1"),
                "haze": lambda: MediaProcessor._color_filter(video_path, output, "eq=contrast=0.9:brightness=0.1"),
                "vhs": lambda: MediaProcessor._vhs_video(video_path, output),
                "rgb_shift": lambda: MediaProcessor._rgb_shift(video_path, output),
                "soft_glow": lambda: MediaProcessor._soft_glow(video_path, output),
                "fade_in": lambda: MediaProcessor._fade_video(video_path, output, "in", params.get('duration', 1.5)),
                "fade_out": lambda: MediaProcessor._fade_video(video_path, output, "out", params.get('duration', 1.5)),
                "fade_black": lambda: MediaProcessor._fade_video(video_path, output, "both", params.get('duration', 1.5)),
                "crossfade": lambda: MediaProcessor._crossfade_video(video_path, output, params.get('duration', 1)),
                "zoom_in": lambda: MediaProcessor._zoom_effect(video_path, output, "in"),
                "zoom_out": lambda: MediaProcessor._zoom_effect(video_path, output, "out"),
                "slide_left": lambda: MediaProcessor._slide_transition(video_path, output, "left"),
                "slide_right": lambda: MediaProcessor._slide_transition(video_path, output, "right"),
                "slide_up": lambda: MediaProcessor._slide_transition(video_path, output, "up"),
                "slide_down": lambda: MediaProcessor._slide_transition(video_path, output, "down"),
                "mute": lambda: MediaProcessor._mute_audio(video_path, output),
                "extract_audio": lambda: MediaProcessor._extract_audio(video_path, output.replace('.mp4', '.mp3')),
                "add_audio": lambda: MediaProcessor._add_audio(video_path, output, params.get('audio_path')),
                "volume_up": lambda: MediaProcessor._adjust_volume(video_path, output, 2.0),
                "volume_down": lambda: MediaProcessor._adjust_volume(video_path, output, 0.5),
                "voiceover": lambda: MediaProcessor._add_voiceover(video_path, output, params.get('text', '')),
                "boost_bass": lambda: MediaProcessor._boost_bass(video_path, output),
                "echo": lambda: MediaProcessor._add_echo(video_path, output),
                "reverb": lambda: MediaProcessor._add_reverb(video_path, output),
                "normalize_audio": lambda: MediaProcessor._normalize_audio(video_path, output),
                "fade_audio": lambda: MediaProcessor._fade_audio(video_path, output, params.get('duration', 3)),
                "timelapse": lambda: MediaProcessor._timelapse(video_path, output, params.get('speed', 10)),
                "slow_motion": lambda: MediaProcessor._slow_motion(video_path, output),
                "ai_speech": lambda: MediaProcessor._ai_speech(video_path, output, params.get('text', '')),
                "ai_subtitles": lambda: MediaProcessor._ai_subtitles(video_path, output, params.get('lang', 'en')),
                "face_blur": lambda: MediaProcessor._face_blur(video_path, output),
                "ai_enhance": lambda: MediaProcessor._color_filter(video_path, output, "unsharp=5:5:1.0:5:5:0.0"),
                "scene_detect": lambda: MediaProcessor._scene_detection(video_path, output),
                "ai_analysis": lambda: MediaProcessor._ai_analysis(video_path, output),
                "colorize": lambda: MediaProcessor._color_filter(video_path, output, "eq=saturation=1.3"),
                "style_transfer": lambda: MediaProcessor._color_filter(video_path, output, "edgedetect,eq=saturation=1.5"),
                "chroma_key": lambda: MediaProcessor._chroma_key(video_path, output, params.get('color', 'green')),
                "text_overlay": lambda: MediaProcessor._add_text(video_path, output, params),
                "watermark": lambda: MediaProcessor._add_watermark(video_path, output, params.get('text', Config.WATERMARK_TEXT)),
                "rotate_video": lambda: MediaProcessor._rotate_video(video_path, output, params.get('angle', 90)),
                "crop_video": lambda: MediaProcessor._crop_video(video_path, output, params),
                "resize_video": lambda: MediaProcessor._resize_video(video_path, output, params),
                "stabilize": lambda: MediaProcessor._stabilize_video(video_path, output),
                "denoise": lambda: MediaProcessor._denoise_video(video_path, output),
                "color_grading": lambda: MediaProcessor._color_filter(video_path, output, "eq=brightness=0.05:contrast=1.1:saturation=1.2"),
                "picture_in_picture": lambda: MediaProcessor._pip_video(video_path, output, params.get('overlay_path', '')),
            }
            if effect in effects_map:
                result = await effects_map[effect]()
                return result if (result and os.path.exists(result)) else output
            raise ValueError(f"Unknown effect: {effect}")
        except Exception as e:
            logger.error(f"Video effect error [{effect}]: {e}")
            raise

    @staticmethod
    async def compress_video(input_path: str, quality: str) -> str:
        preset = Config.VIDEO_QUALITY_PRESETS.get(quality, Config.VIDEO_QUALITY_PRESETS['720p'])
        w = preset['width']
        h = preset['height']
        bitrate = preset['bitrate']
        audio_br = preset['audio']
        crf = preset['crf']
        speed = preset['preset']
        output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=Config.TEMP_DIR).name
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264', '-crf', str(crf), '-preset', speed,
            '-b:v', bitrate, '-maxrate', bitrate, '-bufsize', str(int(bitrate[:-1])*2)+'k',
            '-c:a', 'aac', '-b:a', audio_br,
            '-movflags', '+faststart',
            '-y', output
        ]
        success = await MediaProcessor._run_ffmpeg(cmd, timeout=Config.PREMIUM_TIMEOUT)
        if success and os.path.exists(output):
            return output
        raise RuntimeError(f"Compression to {quality} failed")

    @staticmethod
    async def get_video_metadata(video_path: str) -> dict:
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            data = json.loads(stdout.decode())
            fmt = data.get('format', {})
            streams = data.get('streams', [])
            vid = next((s for s in streams if s.get('codec_type') == 'video'), {})
            aud = next((s for s in streams if s.get('codec_type') == 'audio'), {})
            tags = fmt.get('tags', {})
            return {
                'title': tags.get('title', ''),
                'artist': tags.get('artist', ''),
                'album': tags.get('album', ''),
                'comment': tags.get('comment', ''),
                'duration': float(fmt.get('duration', 0)),
                'size': int(fmt.get('size', 0)),
                'bitrate': int(fmt.get('bit_rate', 0)),
                'width': vid.get('width', 0),
                'height': vid.get('height', 0),
                'fps': eval(vid.get('r_frame_rate', '0/1')) if vid.get('r_frame_rate') else 0,
                'video_codec': vid.get('codec_name', ''),
                'audio_codec': aud.get('codec_name', ''),
            }
        except Exception as e:
            logger.error(f"Metadata read error: {e}")
            return {}

    @staticmethod
    async def set_video_metadata(input_path: str, metadata: dict) -> str:
        output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=Config.TEMP_DIR).name
        cmd = ['ffmpeg', '-i', input_path]
        for k, v in metadata.items():
            if v:
                cmd.extend(['-metadata', f'{k}={v}'])
        cmd.extend(['-c', 'copy', '-y', output])
        success = await MediaProcessor._run_ffmpeg(cmd)
        return output if success else input_path

    @staticmethod
    async def set_audio_metadata(input_path: str, metadata: dict) -> str:
        ext = os.path.splitext(input_path)[1] or '.mp3'
        output = tempfile.NamedTemporaryFile(suffix=ext, delete=False, dir=Config.TEMP_DIR).name
        cmd = ['ffmpeg', '-i', input_path]
        for k, v in metadata.items():
            if v:
                cmd.extend(['-metadata', f'{k}={v}'])
        cmd.extend(['-c', 'copy', '-y', output])
        success = await MediaProcessor._run_ffmpeg(cmd)
        return output if success else input_path

    # ========== IMAGE HELPERS ==========
    @staticmethod
    def _sepia(img):
        img = img.convert("RGB")
        m = np.array([[0.393,0.769,0.189],[0.349,0.686,0.168],[0.272,0.534,0.131]])
        arr = np.array(img).astype(np.float32) @ m.T
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    @staticmethod
    def _oil_paint(img):
        arr = np.array(img)
        out = cv2.stylization(arr, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(out)

    @staticmethod
    def _watercolor(img):
        arr = np.array(img)
        out = cv2.stylization(arr, sigma_s=60, sigma_r=0.6)
        out = cv2.edgePreservingFilter(out, flags=1, sigma_s=60, sigma_r=0.4)
        return Image.fromarray(out)

    @staticmethod
    def _sketch(img):
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blurred = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blurred, scale=256.0)
        return Image.fromarray(cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB))

    @staticmethod
    def _pencil_sketch(img):
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, color = cv2.pencilSketch(arr, sigma_s=10, sigma_r=0.07, shade_factor=0.05)
        return Image.fromarray(color)

    @staticmethod
    def _cartoon(img):
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(arr, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)

    @staticmethod
    def _pixelate(img, size=10):
        small = img.resize((max(1, img.width//size), max(1, img.height//size)), Image.Resampling.NEAREST)
        return small.resize((img.width, img.height), Image.Resampling.NEAREST)

    @staticmethod
    def _glitch(img):
        arr = np.array(img)
        h, w = arr.shape[:2]
        for _ in range(8):
            x = random.randint(0, max(0, w-60))
            y = random.randint(0, max(0, h-15))
            shift = random.randint(-40, 40)
            arr[y:y+15, x:x+60] = np.roll(arr[y:y+15, x:x+60], shift, axis=1)
        return Image.fromarray(arr)

    @staticmethod
    def _vintage(img):
        arr = np.array(img).astype(np.float32)
        m = np.array([[0.272,0.534,0.131],[0.349,0.686,0.168],[0.393,0.769,0.189]])
        arr = arr @ m.T
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    @staticmethod
    def _neon(img):
        arr = np.array(img)
        edges = cv2.Canny(arr, 80, 180)
        edges_c = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        edges_c[:, :, 0] = 0
        result = cv2.addWeighted(arr, 0.6, edges_c, 0.4, 0)
        return Image.fromarray(result)

    @staticmethod
    def _pastel(img):
        arr = np.array(img)
        smooth = cv2.bilateralFilter(arr, 9, 75, 75)
        bright = np.clip(smooth.astype(np.float32) * 1.1 + 20, 0, 255).astype(np.uint8)
        return Image.fromarray(bright)

    @staticmethod
    def _comic(img):
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 7)
        color = cv2.bilateralFilter(arr, 5, 50, 50)
        edges_c = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(cv2.bitwise_and(color, edges_c))

    @staticmethod
    def _stained_glass(img):
        arr = np.array(img)
        quant = (arr // 64) * 64
        edges = cv2.Canny(arr, 50, 150)
        edges_inv = cv2.cvtColor(255 - edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(cv2.bitwise_and(quant, edges_inv))

    @staticmethod
    def _adjust_hue(img, shift):
        arr = np.array(img.convert('HSV'))
        arr[:, :, 0] = (arr[:, :, 0].astype(int) + shift) % 180
        return Image.fromarray(arr, 'HSV').convert('RGB')

    @staticmethod
    def _adjust_temperature(img, temp_k):
        arr = np.array(img).astype(np.float32)
        if temp_k > 6500:
            arr[:,:,0] *= min(1.3, 1+(temp_k-6500)/10000*0.3)
            arr[:,:,2] *= max(0.7, 1-(temp_k-6500)/10000*0.3)
        else:
            arr[:,:,0] *= max(0.7, 1-(6500-temp_k)/6500*0.3)
            arr[:,:,2] *= min(1.3, 1+(6500-temp_k)/6500*0.3)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    @staticmethod
    def _color_balance(img, params):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] *= params.get('red', 1.0)
        arr[:,:,1] *= params.get('green', 1.0)
        arr[:,:,2] *= params.get('blue', 1.0)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    @staticmethod
    def _channel_mixer(img, params):
        arr = np.array(img).astype(np.float32)
        r = arr[:,:,0]*params.get('rr',1)+arr[:,:,1]*params.get('rg',0)+arr[:,:,2]*params.get('rb',0)
        g = arr[:,:,0]*params.get('gr',0)+arr[:,:,1]*params.get('gg',1)+arr[:,:,2]*params.get('gb',0)
        b = arr[:,:,0]*params.get('br',0)+arr[:,:,1]*params.get('bg',0)+arr[:,:,2]*params.get('bb',1)
        return Image.fromarray(np.clip(np.stack([r,g,b],axis=2),0,255).astype(np.uint8))

    @staticmethod
    def _golden_hour(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0]*1.4, 0, 255)
        arr[:,:,1] = np.clip(arr[:,:,1]*1.1, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.6, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _cold_tone(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0]*0.7, 0, 255)
        arr[:,:,1] = np.clip(arr[:,:,1]*0.9, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*1.3, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _skew_image(img, skew):
        arr = np.array(img)
        rows, cols = arr.shape[:2]
        M = np.float32([[1, skew/100, 0], [0, 1, 0]])
        return Image.fromarray(cv2.warpAffine(arr, M, (cols, rows)))

    @staticmethod
    def _perspective(img, params):
        arr = np.array(img)
        r, c = arr.shape[:2]
        pts1 = np.float32([[0,0],[c,0],[0,r],[c,r]])
        pts2 = np.float32([[params.get('x1',20),params.get('y1',20)],[c-params.get('x2',20),params.get('y2',20)],
                           [params.get('x3',20),r-params.get('y3',20)],[c-params.get('x4',20),r-params.get('y4',20)]])
        M = cv2.getPerspectiveTransform(pts1, pts2)
        return Image.fromarray(cv2.warpPerspective(arr, M, (c, r)))

    @staticmethod
    def _blur_background(img):
        arr = np.array(img)
        blurred = cv2.GaussianBlur(arr, (51, 51), 0)
        mask = np.zeros(arr.shape[:2], dtype=np.uint8)
        h, w = mask.shape
        cv2.ellipse(mask, (w//2, h//2), (w//3, h//3), 0, 0, 360, 255, -1)
        mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB) / 255.0
        result = (arr * mask_3 + blurred * (1-mask_3)).astype(np.uint8)
        return Image.fromarray(result)

    @staticmethod
    def _vignette(img):
        arr = np.array(img).astype(np.float32)
        h, w = arr.shape[:2]
        X, Y = np.meshgrid(np.linspace(-1,1,w), np.linspace(-1,1,h))
        vig = np.clip(1-(X**2+Y**2)*0.6, 0.3, 1)
        return Image.fromarray((arr * vig[:,:,np.newaxis]).astype(np.uint8))

    @staticmethod
    def _rounded_corners(img, radius):
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)
        result = Image.new('RGBA', img.size, (0,0,0,0))
        img_rgba = img.convert('RGBA')
        result.paste(img_rgba, mask=mask)
        return result

    @staticmethod
    def _add_shadow(img):
        shadow = Image.new('RGBA', (img.width+20, img.height+20), (0,0,0,0))
        draw = ImageDraw.Draw(shadow)
        draw.rectangle((15,15,img.width+15,img.height+15), fill=(0,0,0,120))
        img_rgba = img.convert('RGBA')
        shadow.paste(img_rgba, (5,5), img_rgba)
        return shadow

    @staticmethod
    def _glow_effect(img):
        arr = np.array(img)
        blurred = cv2.GaussianBlur(arr, (25, 25), 0)
        return Image.fromarray(cv2.addWeighted(arr, 0.7, blurred, 0.3, 0))

    @staticmethod
    def _duotone(img):
        gray = np.array(img.convert('L'))
        colored = np.zeros((*gray.shape, 3), dtype=np.uint8)
        colored[:,:,0] = gray // 2
        colored[:,:,2] = 255 - gray // 2
        return Image.fromarray(colored)

    @staticmethod
    def _sunset_filter(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0]*1.4, 0, 255)
        arr[:,:,1] = np.clip(arr[:,:,1]*0.8, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.6, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _winter_filter(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0]*0.8, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*1.3, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _autumn_filter(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0]*1.4, 0, 255)
        arr[:,:,1] = np.clip(arr[:,:,1]*0.75, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.5, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _spring_filter(img):
        arr = np.array(img).astype(np.float32)
        arr[:,:,1] = np.clip(arr[:,:,1]*1.3, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2]*1.1, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _night_filter(img):
        arr = np.array(img).astype(np.float32)
        arr = arr * 0.6
        arr[:,:,2] = np.clip(arr[:,:,2]*1.4, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    @staticmethod
    def _firework_effect(img):
        arr = np.array(img)
        overlay = np.zeros_like(arr)
        for _ in range(30):
            x = random.randint(0, arr.shape[1]-1)
            y = random.randint(0, arr.shape[0]-1)
            color = [random.randint(150,255), random.randint(50,255), random.randint(50,255)]
            cv2.circle(overlay, (x,y), random.randint(3,15), color, -1)
        return Image.fromarray(cv2.addWeighted(arr, 0.8, overlay, 0.2, 0))

    @staticmethod
    def _wave_effect(img):
        arr = np.array(img)
        h, w = arr.shape[:2]
        result = np.zeros_like(arr)
        for i in range(h):
            shift = int(10 * np.sin(2 * np.pi * i / 60))
            result[i] = np.roll(arr[i], shift, axis=0)
        return Image.fromarray(result)

    @staticmethod
    def _add_watermark_static(image_path, output_path, text):
        img = Image.open(image_path).convert("RGBA")
        txt = Image.new('RGBA', img.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0,0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x, y = img.width-tw-15, img.height-th-15
        draw.text((x+2, y+2), text, fill=(0,0,0,100), font=font)
        draw.text((x, y), text, fill=(255,255,255,180), font=font)
        watermarked = Image.alpha_composite(img, txt)
        watermarked.convert("RGB").save(output_path, quality=92)

    # ========== VIDEO HELPERS ==========
    @staticmethod
    async def _run_ffmpeg(cmd, timeout=Config.PROCESSING_TIMEOUT):
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if proc.returncode != 0 and Config.ENABLE_FFMPEG_LOGS:
                logger.error(f"FFmpeg stderr: {stderr.decode()[:500]}")
            return proc.returncode == 0
        except asyncio.TimeoutError:
            logger.error(f"FFmpeg timeout")
            return False
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
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
        parts = []
        for start, end in segments:
            tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False, dir=Config.TEMP_DIR).name
            await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-ss',str(start),'-to',str(end),'-c','copy','-y',tmp])
            parts.append(tmp)
        concat_txt = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False).name
        with open(concat_txt, 'w') as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        await MediaProcessor._run_ffmpeg(['ffmpeg','-f','concat','-safe','0','-i',concat_txt,'-c','copy','-y',output_path])
        for p in parts:
            try: os.unlink(p)
            except: pass
        try: os.unlink(concat_txt)
        except: pass
        return output_path

    @staticmethod
    async def _change_speed(input_path, output_path, speed):
        if speed == 1.0:
            shutil.copy2(input_path, output_path)
            return output_path
        vf = f'setpts={1/speed}*PTS'
        speed_clamped = max(0.5, min(2.0, speed))
        if speed > 2.0:
            atempo = f'atempo=2.0,atempo={speed/2}'
        elif speed < 0.5:
            atempo = f'atempo=0.5,atempo={speed*2}'
        else:
            atempo = f'atempo={speed_clamped}'
        cmd = ['ffmpeg','-i',input_path,'-filter:v',vf,'-filter:a',atempo,'-y',output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path

    @staticmethod
    async def _reverse_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','reverse','-af','areverse','-y',output_path])
        return output_path

    @staticmethod
    async def _loop_video(input_path, output_path, times):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-stream_loop',str(times-1),'-i',input_path,'-c','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _merge_videos(paths, output_path):
        concat_txt = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False).name
        with open(concat_txt, 'w') as f:
            for p in paths:
                if p and os.path.exists(p):
                    f.write(f"file '{p}'\n")
        await MediaProcessor._run_ffmpeg(['ffmpeg','-f','concat','-safe','0','-i',concat_txt,'-c','copy','-y',output_path])
        try: os.unlink(concat_txt)
        except: pass
        return output_path

    @staticmethod
    async def _video_to_gif(input_path, output_path):
        cmd = ['ffmpeg','-i',input_path,'-vf','fps=12,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse','-loop','0','-y',output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path

    @staticmethod
    async def _extract_frame(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vframes','1','-q:v','2','-y',output_path])
        return output_path

    @staticmethod
    async def _split_video(input_path, output_path):
        base = output_path.replace('.mp4','_part_%03d.mp4')
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-c','copy','-map','0','-segment_time','30','-f','segment','-reset_timestamps','1','-y',base])
        return output_path

    @staticmethod
    async def _change_resolution(input_path, output_path, params):
        w = params.get('width', 1280)
        h = params.get('height', 720)
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'scale={w}:{h}','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _scale_square(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','crop=min(iw\\,ih):min(iw\\,ih),scale=1080:1080','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _color_filter(input_path, output_path, filter_str):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',filter_str,'-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _vintage_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','curves=vintage,eq=saturation=0.8','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _cinematic_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','crop=in_w:in_h*0.78,scale=1920:816,eq=saturation=1.2:contrast=1.1','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _glitch_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','noise=alls=15:allf=t,rgbashift=rh=5:gh=0:bh=-5','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _pixelate_video(input_path, output_path, pixel_size=10):
        cmd = ['ffmpeg','-i',input_path,'-vf',f'scale=iw/{pixel_size}:ih/{pixel_size},scale=iw*{pixel_size}:ih*{pixel_size}:flags=neighbor','-y',output_path]
        await MediaProcessor._run_ffmpeg(cmd)
        return output_path

    @staticmethod
    async def _oil_paint_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','edgedetect=low=0.1:high=0.4','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _sketch_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','edgedetect,negate','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _cartoon_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','edgedetect,eq=saturation=1.8:contrast=1.5','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _neon_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','edgedetect,eq=saturation=2.5:brightness=0.1','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _sunset_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','colorbalance=rs=0.4:gs=-0.2:bs=-0.3','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _winter_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','colorbalance=rs=-0.2:gs=-0.1:bs=0.4','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _vhs_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','noise=alls=25:allf=t,eq=saturation=0.7:contrast=1.1','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _rgb_shift(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','rgbashift=rh=8:bh=-8','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _soft_glow(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','gblur=sigma=6,eq=brightness=0.1:contrast=1.05','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _fade_video(input_path, output_path, direction, duration=1.5):
        try:
            cmd_probe = ['ffprobe','-v','quiet','-print_format','json','-show_format',input_path]
            proc = await asyncio.create_subprocess_exec(*cmd_probe, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await proc.communicate()
            total = float(json.loads(out.decode()).get('format',{}).get('duration',10))
        except:
            total = 10
        d = int(duration * 30)
        start_out = int((total - duration) * 30)
        if direction == "in":
            vf = f"fade=in:0:{d}"
        elif direction == "out":
            vf = f"fade=out:{start_out}:{d}"
        else:
            vf = f"fade=in:0:{d},fade=out:{start_out}:{d}"
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',vf,'-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _crossfade_video(input_path, output_path, duration=1):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'fade=in:0:{int(duration*30)}','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _slide_transition(input_path, output_path, direction):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'fade=in:0:30','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _zoom_effect(input_path, output_path, zoom_type):
        if zoom_type == "in":
            vf = "zoompan=z='min(zoom+0.001,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        else:
            vf = "zoompan=z='if(eq(on,1),1.5,max(1.5-0.001,1))':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',vf,'-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _mute_audio(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-an','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _extract_audio(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-q:a','0','-map','a','-y',output_path])
        return output_path

    @staticmethod
    async def _add_audio(input_path, output_path, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            shutil.copy2(input_path, output_path)
            return output_path
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-i',audio_path,'-c:v','copy','-c:a','aac','-map','0:v:0','-map','1:a:0','-shortest','-y',output_path])
        return output_path

    @staticmethod
    async def _adjust_volume(input_path, output_path, vol):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af',f'volume={vol}','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _add_voiceover(input_path, output_path, text):
        if not text:
            shutil.copy2(input_path, output_path)
            return output_path
        tts = gTTS(text, lang=Config.TTS_LANG)
        af = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False).name
        tts.save(af)
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-i',af,'-c:v','copy','-c:a','aac','-map','0:v:0','-map','1:a:0','-shortest','-y',output_path])
        try: os.unlink(af)
        except: pass
        return output_path

    @staticmethod
    async def _boost_bass(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af','bass=g=10:f=100','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _add_echo(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af','aecho=0.8:0.9:1000:0.3','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _add_reverb(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af','aecho=0.8:0.88:60:0.4','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _normalize_audio(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af','loudnorm=I=-16:LRA=11:TP=-1.5','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _fade_audio(input_path, output_path, duration=3):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-af',f'afade=t=in:st=0:d={duration}','-c:v','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _timelapse(input_path, output_path, speed=10):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'setpts={1/speed}*PTS','-an','-y',output_path])
        return output_path

    @staticmethod
    async def _slow_motion(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','setpts=2*PTS','-af','atempo=0.5','-y',output_path])
        return output_path

    @staticmethod
    async def _ai_speech(input_path, output_path, text):
        return await MediaProcessor._add_voiceover(input_path, output_path, text)

    @staticmethod
    async def _ai_subtitles(input_path, output_path, lang='en'):
        if not WHISPER_AVAILABLE:
            shutil.copy2(input_path, output_path)
            return output_path
        try:
            model = whisper.load_model(Config.WHISPER_MODEL)
            result = model.transcribe(input_path, language=lang)
            srt = tempfile.NamedTemporaryFile(suffix='.srt', delete=False).name
            def fmt(s):
                h,rem = divmod(int(s),3600); m,sec = divmod(rem,60); ms = int((s-int(s))*1000)
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
            with open(srt,'w',encoding='utf-8') as f:
                for i,seg in enumerate(result['segments']):
                    f.write(f"{i+1}\n{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text'].strip()}\n\n")
            await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f"subtitles='{srt}'",'-c:a','copy','-y',output_path])
            try: os.unlink(srt)
            except: pass
            return output_path
        except Exception as e:
            logger.error(f"Subtitles error: {e}")
            shutil.copy2(input_path, output_path)
            return output_path

    @staticmethod
    async def _face_blur(input_path, output_path):
        try:
            cap = cv2.VideoCapture(input_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False, dir=Config.TEMP_DIR).name
            out = cv2.VideoWriter(tmp, fourcc, fps, (w, h))
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            while True:
                ret, frame = cap.read()
                if not ret: break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(gray, 1.1, 4)
                for (x,y,fw,fh) in faces:
                    face = frame[y:y+fh, x:x+fw]
                    frame[y:y+fh, x:x+fw] = cv2.GaussianBlur(face, (99,99), 30)
                out.write(frame)
            cap.release()
            out.release()
            await MediaProcessor._run_ffmpeg(['ffmpeg','-i',tmp,'-i',input_path,'-c:v','copy','-c:a','copy','-map','0:v','-map','1:a','-shortest','-y',output_path])
            try: os.unlink(tmp)
            except: pass
            return output_path
        except Exception as e:
            shutil.copy2(input_path, output_path)
            return output_path

    @staticmethod
    async def _scene_detection(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','select=gt(scene\\,0.3)','-vsync','vfr','-y',output_path])
        return output_path

    @staticmethod
    async def _ai_analysis(input_path, output_path):
        meta = await MediaProcessor.get_video_metadata(input_path)
        analysis_file = output_path.replace('.mp4','_analysis.txt')
        with open(analysis_file,'w') as f:
            f.write("=== KiraFx Video Analysis ===\n\n")
            for k,v in meta.items():
                f.write(f"{k}: {v}\n")
            f.write(f"\nFile Size: {os.path.getsize(input_path)/(1024*1024):.2f} MB\n")
        return analysis_file

    @staticmethod
    async def _chroma_key(input_path, output_path, color='green'):
        cm = {'green':'0x00FF00','blue':'0x0000FF','red':'0xFF0000','white':'0xFFFFFF'}
        hex_c = cm.get(color,'0x00FF00')
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'chromakey={hex_c}:0.15:0.2','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _add_text(input_path, output_path, params):
        text = params.get('text','Sample Text').replace("'","\\'")
        fs = params.get('fontsize', 36)
        color = params.get('color','white')
        x = params.get('x','(w-text_w)/2')
        y = params.get('y','(h-text_h)/2')
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',
            f"drawtext=text='{text}':fontcolor={color}:fontsize={fs}:x={x}:y={y}:shadowcolor=black:shadowx=2:shadowy=2",
            '-codec:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _add_watermark(input_path, output_path, text):
        txt = text.replace("'","\\'")
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',
            f"drawtext=text='{txt}':fontcolor=white@0.7:fontsize=28:x=w-tw-15:y=h-th-15:shadowcolor=black@0.7:shadowx=2:shadowy=2",
            '-codec:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _rotate_video(input_path, output_path, angle):
        t = (angle//90) % 4
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'transpose={t}','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _crop_video(input_path, output_path, params):
        w = params.get('width', 'iw/2')
        h = params.get('height', 'ih/2')
        x = params.get('x', 0)
        y = params.get('y', 0)
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'crop={w}:{h}:{x}:{y}','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _resize_video(input_path, output_path, params):
        w = params.get('width', 1280)
        h = params.get('height', 720)
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf',f'scale={w}:{h}','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _stabilize_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','deshake','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _denoise_video(input_path, output_path):
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-vf','hqdn3d','-c:a','copy','-y',output_path])
        return output_path

    @staticmethod
    async def _pip_video(input_path, output_path, overlay_path):
        if not overlay_path or not os.path.exists(overlay_path):
            shutil.copy2(input_path, output_path)
            return output_path
        await MediaProcessor._run_ffmpeg(['ffmpeg','-i',input_path,'-i',overlay_path,'-filter_complex',
            '[1:v]scale=iw/4:ih/4[ov];[0:v][ov]overlay=W-w-20:H-h-20','-c:a','copy','-y',output_path])
        return output_path


# ==================== BOT CLASS ====================
class MediaEditorBot:
    def __init__(self):
        self.app = Client(
            "media_editor_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=100
        )
        self.start_time = datetime.now()
        self.register_handlers()

    def register_handlers(self):
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
            await self.handle_rename_menu(client, message)

        @self.app.on_message(filters.command("metadata") & filters.private)
        async def metadata_cmd(client, message):
            await self.handle_metadata_menu(client, message)

        @self.app.on_message(filters.command("compress") & filters.private)
        async def compress_cmd(client, message):
            await self.handle_compress_menu(client, message)

        @self.app.on_message(filters.command("timeline") & filters.private)
        async def timeline_cmd(client, message):
            await self.handle_timeline(client, message)

        @self.app.on_message(filters.command("queue") & filters.private)
        async def queue_cmd(client, message):
            await self.handle_queue_status(client, message)

        @self.app.on_message(filters.command("ping") & filters.private)
        async def ping_cmd(client, message):
            await self.handle_ping(client, message)

        @self.app.on_message(filters.command("alive") & filters.private)
        async def alive_cmd(client, message):
            await self.handle_alive(client, message)

        @self.app.on_message(filters.command("info") & filters.private)
        async def info_cmd(client, message):
            await self.handle_info(client, message)

        @self.app.on_message(filters.command("stats") & filters.private)
        async def stats_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.handle_admin_stats(client, message)

        # ---- ADMIN COMMANDS ----
        @self.app.on_message(filters.command("admin") & filters.private)
        async def admin_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await message.reply("🔧 **Admin Panel**\nSelect an option:", reply_markup=InlineKB.admin_panel())

        @self.app.on_message(filters.command("addadmin") & filters.private)
        async def addadmin_cmd(client, message):
            if message.from_user.id == Config.OWNER_ID:
                await self.cmd_add_admin(client, message)

        @self.app.on_message(filters.command("rmadmin") & filters.private)
        async def rmadmin_cmd(client, message):
            if message.from_user.id == Config.OWNER_ID:
                await self.cmd_rm_admin(client, message)

        @self.app.on_message(filters.command("addprem") & filters.private)
        async def addprem_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_add_premium(client, message)

        @self.app.on_message(filters.command("rmprem") & filters.private)
        async def rmprem_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_rm_premium(client, message)

        @self.app.on_message(filters.command("ban") & filters.private)
        async def ban_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_ban(client, message)

        @self.app.on_message(filters.command("unban") & filters.private)
        async def unban_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_unban(client, message)

        @self.app.on_message(filters.command("broadcast") & filters.private)
        async def broadcast_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_broadcast(client, message)

        @self.app.on_message(filters.command("setwelcome") & filters.private)
        async def setwelcome_cmd(client, message):
            if db.is_admin(message.from_user.id):
                text = message.text.split(None, 1)[1] if len(message.command) > 1 else None
                if text:
                    db.set_setting('welcome_text', text, message.from_user.id)
                    await message.reply("✅ Welcome message updated!")
                else:
                    await message.reply("Usage: /setwelcome <message>\n\nUse {name} for user's first name")

        @self.app.on_message(filters.command("setwatermark") & filters.private)
        async def setwm_cmd(client, message):
            if db.is_admin(message.from_user.id):
                wm = message.text.split(None, 1)[1] if len(message.command) > 1 else None
                if wm:
                    db.set_setting('watermark_text', wm, message.from_user.id)
                    await message.reply(f"✅ Watermark text set to: {wm}")
                else:
                    await message.reply("Usage: /setwatermark <text>")

        @self.app.on_message(filters.command("setfree") & filters.private)
        async def setfree_cmd(client, message):
            if db.is_admin(message.from_user.id):
                try:
                    n = int(message.command[1])
                    db.set_setting('free_edits', str(n), message.from_user.id)
                    await message.reply(f"✅ Free edits per day set to {n}")
                except:
                    await message.reply("Usage: /setfree <count>")

        @self.app.on_message(filters.command("setads") & filters.private)
        async def setads_cmd(client, message):
            if db.is_admin(message.from_user.id):
                try:
                    args = message.command[1].split(',')
                    enabled = '1' if args[0].lower() == 'on' else '0'
                    interval = int(args[1]) if len(args) > 1 else Config.ADS_INTERVAL
                    db.set_setting('ads_enabled', enabled, message.from_user.id)
                    db.set_setting('ads_interval', str(interval), message.from_user.id)
                    await message.reply(f"✅ Ads: {'On' if enabled=='1' else 'Off'} | Interval: {interval}")
                except:
                    await message.reply("Usage: /setads <on/off>,<interval>")

        @self.app.on_message(filters.command("maintenance") & filters.private)
        async def maint_cmd(client, message):
            if db.is_admin(message.from_user.id):
                mode = message.command[1].lower() if len(message.command) > 1 else "status"
                if mode == "on":
                    db.set_setting('maintenance_mode', '1', message.from_user.id)
                    await message.reply("🔒 Maintenance mode: ON")
                elif mode == "off":
                    db.set_setting('maintenance_mode', '0', message.from_user.id)
                    await message.reply("🔓 Maintenance mode: OFF")
                else:
                    status = db.get_setting('maintenance_mode', '0')
                    await message.reply(f"Maintenance mode: {'ON' if status=='1' else 'OFF'}\n/maintenance on|off")

        @self.app.on_message(filters.command("backup") & filters.private)
        async def backup_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await message.reply("⏳ Creating backup...")
                bp = db.backup_database()
                await client.send_document(message.chat.id, bp, caption=f"📦 Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                try: os.unlink(bp)
                except: pass

        @self.app.on_message(filters.command("cleanup") & filters.private)
        async def cleanup_cmd(client, message):
            if db.is_admin(message.from_user.id):
                count = db.cleanup_temp_files(1)
                await message.reply(f"✅ Cleaned {count} temp files.")

        @self.app.on_message(filters.command("logs") & filters.private)
        async def logs_cmd(client, message):
            if db.is_admin(message.from_user.id):
                log_path = f"{Config.LOGS_DIR}/bot.log"
                if os.path.exists(log_path):
                    await client.send_document(message.chat.id, log_path, caption="📝 Bot Logs")
                else:
                    await message.reply("No log file found.")

        @self.app.on_message(filters.command("export") & filters.private)
        async def export_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.do_export(client, message)

        @self.app.on_message(filters.command("addautoreply") & filters.private)
        async def addautoreply_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_add_auto_reply(client, message)

        @self.app.on_message(filters.command("listcmds") & filters.private)
        async def listcmds_cmd(client, message):
            await self.cmd_list_commands(client, message)

        # ---- ADDCMD (FULLY FIXED) ----
        @self.app.on_message(filters.command("addcmd") & filters.private)
        async def addcmd_cmd(client, message):
            if db.is_admin(message.from_user.id):
                await self.cmd_add_command(client, message)

        @self.app.on_message(filters.command("delcmd") & filters.private)
        async def delcmd_cmd(client, message):
            if db.is_admin(message.from_user.id):
                cmd_name = message.command[1].lower() if len(message.command) > 1 else None
                if cmd_name:
                    db.delete_custom_command(cmd_name)
                    await message.reply(f"✅ Command /{cmd_name} deleted.")
                else:
                    await message.reply("Usage: /delcmd <command>")

        @self.app.on_message(filters.command("togglecmd") & filters.private)
        async def togglecmd_cmd(client, message):
            if db.is_admin(message.from_user.id):
                cmd_name = message.command[1].lower() if len(message.command) > 1 else None
                if cmd_name:
                    state = db.toggle_custom_command(cmd_name)
                    status = "enabled" if state else "disabled"
                    await message.reply(f"✅ Command /{cmd_name} {status}.")
                else:
                    await message.reply("Usage: /togglecmd <command>")

        @self.app.on_message(filters.command("userinfo") & filters.private)
        async def userinfo_cmd(client, message):
            if db.is_admin(message.from_user.id):
                target = message.command[1] if len(message.command) > 1 else None
                if target:
                    await self.cmd_user_info(client, message, target)
                else:
                    await message.reply("Usage: /userinfo <user_id or @username>")

        @self.app.on_message(filters.command("addcoins") & filters.private)
        async def addcoins_cmd(client, message):
            if db.is_admin(message.from_user.id):
                try:
                    uid = int(message.command[1])
                    amt = int(message.command[2]) if len(message.command) > 2 else 100
                    db.add_coins(uid, amt)
                    await message.reply(f"✅ Added {amt} coins to {uid}")
                except:
                    await message.reply("Usage: /addcoins <user_id> <amount>")

        # ---- MEDIA HANDLERS ----
        @self.app.on_message(filters.photo & filters.private)
        async def photo_handler(client, message):
            await self.process_image(client, message)

        @self.app.on_message(filters.video & filters.private)
        async def video_handler(client, message):
            await self.process_video(client, message)

        @self.app.on_message(filters.document & filters.private)
        async def doc_handler(client, message):
            await self.process_document(client, message)

        @self.app.on_message(filters.audio & filters.private)
        async def audio_handler(client, message):
            await self.process_audio(client, message)

        # ---- CALLBACK HANDLER ----
        @self.app.on_callback_query()
        async def callback_handler(client, callback):
            await self.handle_callback(client, callback)

        # ---- TEXT / CUSTOM COMMANDS HANDLER ----
        @self.app.on_message(filters.text & filters.private)
        async def text_handler(client, message):
            await self.handle_text(client, message)

    # ==================== COMMAND HANDLERS ====================
    async def handle_start(self, client, message):
        user = message.from_user
        referred_by = 0
        if len(message.command) > 1:
            try:
                referred_by = int(message.command[1])
            except:
                pass

        db.add_user(user.id, user.username, user.first_name, user.last_name or "", referred_by)

        if referred_by and referred_by != user.id:
            if db.add_referral(referred_by, user.id):
                try:
                    await client.send_message(referred_by, "🎉 Someone joined using your referral link!\nYou earned **3 days premium** + **100 coins**!")
                except:
                    pass

        if db.is_banned(user.id):
            await message.reply("🚫 You are banned from using this bot.\nContact support if you believe this is an error.")
            return

        if db.get_setting('maintenance_mode', '0') == '1' and not db.is_admin(user.id):
            await message.reply("🔧 Bot is currently under maintenance. Please try again later.")
            return

        welcome = db.get_setting('welcome_text', '')
        name = user.first_name
        try:
            welcome = welcome.replace('{name}', name).replace('{username}', f"@{user.username or name}")
        except:
            pass

        await message.reply(
            welcome,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKB.main_menu(user.id)
        )

    async def handle_help(self, client, message):
        text = """<blockquote>
🎬 <b>KiraFx Media Editor Bot v6.0</b>

<b>📸 Image Tools (30+):</b>
• Basic: Blur, Sharpen, Grayscale, Sepia, Edge Enhance, Emboss, Smooth, Detail, Gaussian Blur
• Artistic: Oil Paint, Watercolor, Sketch, Cartoon, Glitch, Vintage, Neon, Mosaic, Comic, Pastel
• Color: Brightness, Contrast, Saturation, Hue, Temperature, Auto Color, Equalize, Posterize, Invert, Color Balance
• Transform: Rotate, Flip, Resize, Crop, Skew, Mirror, Auto Rotate
• Special: Blur BG, Vignette, Border, Rounded, Shadow, Glow, Duotone, Sunset, Winter, Autumn, Spring, Night

<b>🎥 Video Tools (35+):</b>
• Basic: Trim, Cut, Speed (0.25x-4x), Reverse, Loop, Merge, GIF, Frame Extract
• Filters: B&amp;W, Sepia, Vintage, Cinematic, Glitch, Pixelate, VHS, RGB Shift, Soft Glow
• Transitions: Fade In/Out, Crossfade, Zoom In/Out, Slide
• Audio: Mute, Extract, Add Music, Volume, Voiceover, Bass, Echo, Reverb, Normalize
• Speed: 0.25x-4x, Timelapse, Slow Motion
• AI: Speech, Subtitles, Face Blur, Enhance, Scene Detect, Analysis

<b>🗜️ Video Compression (144p to 4K):</b>
/compress - Send video then choose quality

<b>📝 Advanced Rename + Metadata:</b>
/rename - Rename any file (up to 4GB)
/metadata - Edit video/audio metadata (title, artist, album...)

<b>📝 Commands:</b>
/start /help /premium /trial /status /profile
/refer /rename /metadata /compress /ping /alive
/queue - Queue status

<b>📢 Admin:</b>
/admin - Admin panel (50+ tools)
/addcmd command | response [--code lang] [reply to media]
/delcmd /togglecmd /listcmds
/ban /unban /addprem /rmprem /broadcast
/setwelcome /setwatermark /setfree /setads /maintenance
/addadmin /rmadmin /backup /cleanup /logs /export
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def handle_premium(self, client, message):
        text = f"""<blockquote>
🌟 <b>PREMIUM PLAN - {Config.PREMIUM_PRICE}</b>

<b>✨ Premium Features:</b>
✅ FASTEST Processing Speed
✅ Priority Queue
✅ No Watermark
✅ Unlimited Daily Edits
✅ No Ads
✅ 4K Video Export (Up to 4K/2160p)
✅ All Compression Presets (144p→4K)
✅ AI Speech &amp; Subtitles
✅ Advanced Metadata Editing
✅ Priority Support

<b>⚡ Speed Comparison:</b>
• Premium: 10-30s ⚡ FAST
• Normal: 30-120s 📝 Standard

<b>🎁 7-Day Free Trial:</b> /trial
<b>👥 Refer a friend:</b> Get 3 days premium!

<a href="{Config.PREMIUM_LINK}">🔗 Buy Premium Now</a>
</blockquote>"""
        await message.reply(text, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)

    async def handle_trial(self, client, message):
        uid = message.from_user.id
        if db.is_premium(uid):
            exp = datetime.fromtimestamp(db.get_premium_expiry(uid)).strftime('%Y-%m-%d')
            await message.reply(f"⭐ You already have premium active until {exp}!")
            return
        row = db.get_user(uid)
        if row and row["trial_used"]:
            await message.reply("❌ You have already used your 7-day free trial.\n\nUpgrade with /premium!")
            return
        db.give_premium(uid, Config.FREE_TRIAL_DAYS)
        db.cursor.execute("UPDATE users SET trial_used=1 WHERE user_id=?", (uid,))
        db.conn.commit()
        await message.reply(f"🎉 **7-Day Free Trial Activated!**\n\n⚡ You now have PREMIUM PRIORITY PROCESSING for {Config.FREE_TRIAL_DAYS} days!\n\nEnjoy:\n• Unlimited edits\n• No watermark\n• No ads\n• Fastest processing\n• 4K export")

    async def handle_status(self, client, message):
        uid = message.from_user.id
        is_prem = db.is_premium(uid)
        row = db.get_user(uid)
        coins = db.get_coins(uid)
        free_edits = int(db.get_setting('free_edits', Config.MAX_FREE_EDITS))

        if is_prem:
            exp = datetime.fromtimestamp(db.get_premium_expiry(uid)).strftime('%Y-%m-%d %H:%M')
            text = f"""<blockquote>
✅ <b>Premium Active</b>

⚡ Processing Speed: FAST
📅 Expires: {exp}
✏️ Edits: Unlimited
💰 Coins: {coins}
👑 Priority: HIGH
</blockquote>"""
        else:
            used = row["edits_today"] if row else 0
            total = row["total_edits"] if row else 0
            rem = max(0, free_edits - used)
            text = f"""<blockquote>
📝 <b>Free User</b>

📊 Today's Edits: {used}/{free_edits}
📈 Total Edits: {total}
🔢 Remaining: {rem}
💰 Coins: {coins}
🔄 Priority: NORMAL

⚡ Upgrade: /premium | Trial: /trial
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def handle_profile(self, client, message):
        user = message.from_user
        row = db.get_user(user.id)
        if not row:
            await message.reply("Profile not found. Use /start first.")
            return
        join = datetime.fromtimestamp(row["join_date"]).strftime("%Y-%m-%d")
        prio = "⚡ HIGH (Premium)" if db.is_premium(user.id) else "📝 NORMAL (Free)"
        text = f"""<blockquote>
👤 <b>User Profile</b>

<b>Name:</b> {user.first_name} {user.last_name or ''}
<b>Username:</b> @{user.username or 'N/A'}
<b>ID:</b> <code>{user.id}</code>
<b>Joined:</b> {join}
<b>Status:</b> {'⭐ Premium' if db.is_premium(user.id) else '📝 Free'}
<b>Priority:</b> {prio}
<b>Total Edits:</b> {row['total_edits']}
<b>Files Renamed:</b> {row['renamed_files']}
<b>Referrals:</b> {db.get_referral_count(user.id)}
<b>Coins:</b> {row['coins']}
<b>Trial Used:</b> {'Yes' if row['trial_used'] else 'No'}
<b>Ads Watched:</b> {row['total_ads_watched']}
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML,
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]]))

    async def handle_refer(self, client, message):
        uid = message.from_user.id
        me = await client.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        count = db.get_referral_count(uid)
        text = f"""<blockquote>
👥 <b>Referral System</b>

<b>Your Referral Link:</b>
<code>{link}</code>

<b>Total Referrals:</b> {count}
<b>Premium Days Earned:</b> {count * 3}
<b>Coins Earned:</b> {count * 100}

<b>Rewards per referral:</b>
• 3 days premium
• 100 coins
• No limit!
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML,
                           disable_web_page_preview=True,
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]]))

    async def handle_rename_menu(self, client, message):
        uid = message.from_user.id
        if not db.can_edit(uid):
            await message.reply(f"⚠️ Free limit reached! Upgrade to /premium for unlimited edits.")
            return
        await message.reply(
            "📝 **Rename & Metadata**\n\nChoose what you want to do:",
            reply_markup=InlineKB.rename_menu()
        )

    async def handle_metadata_menu(self, client, message):
        await message.reply(
            "🏷️ **Metadata Editor**\n\nSend a video or audio file to edit its metadata (title, artist, album, year, etc.)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
        )
        db.set_session(message.from_user.id, "awaiting_metadata_file", {})

    async def handle_compress_menu(self, client, message):
        uid = message.from_user.id
        if not db.can_edit(uid):
            await message.reply(f"⚠️ Free limit reached! Upgrade to /premium for unlimited edits.")
            return
        await message.reply(
            "🗜️ **Video Compression**\n\nFirst send your video, then choose quality:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
        )
        db.set_session(uid, "awaiting_compress_video", {})

    async def handle_timeline(self, client, message):
        await message.reply(
            "🎞️ **Timeline Editor**\n\n• Trim video segments\n• Cut and merge clips\n• Add transitions\n• Add text overlays\n• Add background music\n\n⚡ Premium = FASTER processing!\n\nSend a video to start!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
        )

    async def handle_queue_status(self, client, message):
        uid = message.from_user.id
        db.cursor.execute("SELECT COUNT(*) as c FROM processing_queue WHERE status='pending' AND user_id=?", (uid,))
        mine = db.cursor.fetchone()["c"]
        db.cursor.execute("SELECT COUNT(*) as c FROM processing_queue WHERE status='pending'")
        total = db.cursor.fetchone()["c"]
        est = "10-30s" if db.is_premium(uid) else "30-120s"
        prio = "⚡ HIGH" if db.is_premium(uid) else "📝 NORMAL"
        text = f"""<blockquote>
📊 <b>Queue Status</b>

<b>Your Priority:</b> {prio}
<b>Your Queue:</b> {mine}
<b>Total Queue:</b> {total}
<b>Estimated Time:</b> {est}
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def handle_ping(self, client, message):
        t0 = time.time()
        msg = await message.reply("🏓 Pong!")
        lat = (time.time() - t0) * 1000
        up = datetime.now() - self.start_time
        await msg.edit_text(f"🏓 **Pong!**\n\nLatency: `{lat:.0f}ms`\nUptime: `{str(up).split('.')[0]}`")

    async def handle_alive(self, client, message):
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info().rss / (1024*1024)
        up = get_uptime()
        stats = db.get_stats()
        text = f"""<blockquote>
✅ <b>{Config.BOT_NAME} is ALIVE!</b>

🕐 Uptime: {up}
💾 Memory: {mem:.1f} MB
👥 Users: {stats['total_users']}
✏️ Total Edits: {stats['total_edits']}
⭐ Premium Users: {stats['premium_users']}
🌐 Dashboard: Port 5000

<b>Status: 🟢 Online</b>
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def handle_info(self, client, message):
        stats = db.get_stats()
        up = get_uptime()
        ffmpeg = "✅" if shutil.which('ffmpeg') else "❌"
        text = f"""<blockquote>
ℹ️ <b>Bot Information</b>

<b>Name:</b> {Config.BOT_NAME}
<b>Version:</b> {Config.BOT_VERSION}
<b>Uptime:</b> {up}

<b>Statistics:</b>
• Users: {stats['total_users']}
• Premium: {stats['premium_users']}
• Total Edits: {stats['total_edits']}
• Today's Edits: {stats['today_edits']}
• Files Renamed: {stats['total_renames']}

<b>Features:</b>
• Image Tools: 30+
• Video Tools: 35+
• AI Tools: 8+
• Compression: 144p → 4K
• Admin Tools: 50+

<b>System:</b>
• FFmpeg: {ffmpeg}
• Whisper AI: {'✅' if WHISPER_AVAILABLE else '❌'}
• Python: {platform.python_version()}
• Free Edits/Day: {db.get_setting('free_edits', Config.MAX_FREE_EDITS)}
• Trial: {Config.FREE_TRIAL_DAYS} days

<b>Status: 🟢 Online</b>
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def handle_admin_stats(self, client, message):
        stats = db.get_stats()
        up = get_uptime()
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info().rss / (1024*1024)
        text = f"""<blockquote>
📊 <b>Admin Statistics</b>

👥 Total Users: {stats['total_users']}
⭐ Premium Users: {stats['premium_users']}
🚫 Banned Users: {stats['banned_users']}
✏️ Total Edits: {stats['total_edits']}
📅 Today's Edits: {stats['today_edits']}
💰 Total Ads: {stats['total_ads']}
📄 Files Renamed: {stats['total_renames']}
🎯 Commands Used: {stats['total_commands']}
⏳ Queue Pending: {stats['queue_pending']}

🕐 Uptime: {up}
💾 Memory: {mem:.1f} MB
💾 DB Size: {db.get_db_size()/(1024):.1f} KB
</blockquote>"""
        await message.reply(text, parse_mode=enums.ParseMode.HTML)

    # ==================== ADMIN COMMAND HANDLERS ====================
    async def cmd_add_admin(self, client, message):
        try:
            target = int(message.command[1])
            title = ' '.join(message.command[2:]) if len(message.command) > 2 else "Admin"
            db.add_admin(target, message.from_user.id, title=title)
            await message.reply(f"✅ User `{target}` is now admin with title: {title}")
            try:
                await client.send_message(target, f"🎉 You've been promoted to **{title}** of {Config.BOT_NAME}!")
            except:
                pass
        except:
            await message.reply("Usage: /addadmin <user_id> [title]")

    async def cmd_rm_admin(self, client, message):
        try:
            target = int(message.command[1])
            db.remove_admin(target)
            await message.reply(f"✅ User `{target}` removed from admins.")
        except:
            await message.reply("Usage: /rmadmin <user_id>")

    async def cmd_add_premium(self, client, message):
        try:
            args = message.command[1].split(',')
            uid = int(args[0])
            days = int(args[1]) if len(args) > 1 else 30
            until = db.give_premium(uid, days)
            exp = datetime.fromtimestamp(until).strftime('%Y-%m-%d')
            await message.reply(f"✅ {days} days premium added to `{uid}`\nExpires: {exp}")
            try:
                await client.send_message(uid, f"🎉 You've been granted **{days} days of Premium**!\nExpires: {exp}\n\n⚡ Enjoy faster processing + all premium features!")
            except:
                pass
        except:
            await message.reply("Usage: /addprem <user_id>,<days>")

    async def cmd_rm_premium(self, client, message):
        try:
            uid = int(message.command[1])
            db.remove_premium(uid)
            await message.reply(f"✅ Premium removed from `{uid}`")
        except:
            await message.reply("Usage: /rmprem <user_id>")

    async def cmd_ban(self, client, message):
        try:
            args = message.command[1].split(',')
            uid = int(args[0])
            reason = args[1].strip() if len(args) > 1 else "Violation of rules"
            duration = int(args[2]) if len(args) > 2 else 0
            db.ban_user(uid, reason, message.from_user.id, duration)
            dur_str = f"{duration} days" if duration > 0 else "Permanent"
            await message.reply(f"✅ User `{uid}` banned.\nReason: {reason}\nDuration: {dur_str}")
            try:
                msg = f"🚫 You have been banned.\nReason: {reason}\nDuration: {dur_str}"
                await client.send_message(uid, msg)
            except:
                pass
        except:
            await message.reply("Usage: /ban <user_id>,<reason>,<days> (0=permanent)")

    async def cmd_unban(self, client, message):
        try:
            uid = int(message.command[1])
            db.unban_user(uid)
            await message.reply(f"✅ User `{uid}` unbanned.")
            try:
                await client.send_message(uid, "✅ You have been unbanned!")
            except:
                pass
        except:
            await message.reply("Usage: /unban <user_id>")

    async def cmd_broadcast(self, client, message):
        text_content = None
        media_id = None
        media_type = None

        if message.reply_to_message:
            rm = message.reply_to_message
            if rm.text:
                text_content = rm.text
            elif rm.caption:
                text_content = rm.caption
            if rm.photo:
                media_id = rm.photo.file_id
                media_type = 'photo'
                if not text_content:
                    text_content = rm.caption or ""
            elif rm.video:
                media_id = rm.video.file_id
                media_type = 'video'
                if not text_content:
                    text_content = rm.caption or ""
        else:
            text_content = message.text.split(None, 1)[1] if len(message.command) > 1 else None

        if not text_content and not media_id:
            await message.reply("Usage: /broadcast <message> OR reply to a message")
            return

        confirm_msg = await message.reply("📢 Broadcasting...")
        db.cursor.execute("SELECT user_id FROM users WHERE banned=0")
        users = db.cursor.fetchall()
        success = 0
        failed = 0

        for user in users:
            try:
                if media_type == 'photo':
                    await client.send_photo(user["user_id"], media_id, caption=text_content)
                elif media_type == 'video':
                    await client.send_video(user["user_id"], media_id, caption=text_content)
                else:
                    await client.send_message(user["user_id"], text_content)
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1

        db.cursor.execute("INSERT INTO broadcast_log (admin_id, message_text, sent_count, failed_count, timestamp) VALUES (?,?,?,?,?)",
                         (message.from_user.id, text_content or "", success, failed, int(datetime.now().timestamp())))
        db.conn.commit()
        await confirm_msg.edit_text(f"✅ Broadcast complete!\n\nSent: {success}\nFailed: {failed}")

    async def cmd_add_command(self, client, message):
        """
        FULLY FIXED addcmd supporting:
        - Text response: /addcmd cmd | response text
        - Code response: /addcmd cmd | ```python\ncode``` --code python
        - Media response: reply to photo/video/audio/document with /addcmd cmd | caption
        Usage examples:
          /addcmd hello | Hello World!
          /addcmd info | Here is some info --code python\nprint("hello")
          (reply to a photo) /addcmd logo | Our bot logo
        """
        try:
            full = message.text.split(None, 1)
            if len(full) < 2:
                raise ValueError("no args")
            args = full[1]

            # Parse command and response
            if '|' in args:
                cmd_name, response = args.split('|', 1)
                cmd_name = cmd_name.strip().lstrip('/').lower()
                response = response.strip()
            else:
                parts = args.split(None, 1)
                cmd_name = parts[0].strip().lstrip('/').lower()
                response = parts[1].strip() if len(parts) > 1 else ""

            if not cmd_name:
                raise ValueError("no command name")

            # Detect --code flag
            is_code = False
            code_lang = ""
            if '--code' in response:
                is_code = True
                parts = response.split('--code', 1)
                response = parts[0].strip()
                code_lang = parts[1].strip().split()[0] if parts[1].strip() else "python"
                rest = parts[1].strip()[len(code_lang):].strip()
                if rest:
                    response = rest

            # Detect media from reply
            media_type = None
            media_id = None
            response_type = "text"

            if message.reply_to_message:
                rm = message.reply_to_message
                if rm.photo:
                    media_id = rm.photo.file_id
                    media_type = "photo"
                    response_type = "photo"
                    if not response and rm.caption:
                        response = rm.caption
                elif rm.video:
                    media_id = rm.video.file_id
                    media_type = "video"
                    response_type = "video"
                    if not response and rm.caption:
                        response = rm.caption
                elif rm.audio:
                    media_id = rm.audio.file_id
                    media_type = "audio"
                    response_type = "audio"
                    if not response and rm.caption:
                        response = rm.caption
                elif rm.document:
                    media_id = rm.document.file_id
                    media_type = "document"
                    response_type = "document"
                    if not response and rm.caption:
                        response = rm.caption
                elif rm.sticker:
                    media_id = rm.sticker.file_id
                    media_type = "sticker"
                    response_type = "sticker"
                elif rm.voice:
                    media_id = rm.voice.file_id
                    media_type = "voice"
                    response_type = "voice"

            if is_code:
                response_type = "code"

            db.add_custom_command(
                command=cmd_name,
                response=response,
                response_type=response_type,
                media_type=media_type,
                media_id=media_id,
                is_code=is_code,
                code_lang=code_lang,
                created_by=message.from_user.id
            )

            type_str = {"text":"📝 Text","photo":"🖼️ Photo","video":"🎬 Video","audio":"🎵 Audio",
                       "document":"📄 Document","sticker":"🎭 Sticker","code":"💻 Code","voice":"🎤 Voice"}.get(response_type, response_type)
            await message.reply(
                f"✅ **Command Added!**\n\n"
                f"Command: `/{cmd_name}`\n"
                f"Type: {type_str}\n"
                f"Response: {response[:100] + '...' if len(response) > 100 else response or '(media only)'}\n"
                f"{'Code Lang: ' + code_lang if is_code else ''}\n\n"
                f"Users can now use `/{cmd_name}` to trigger this!"
            )
        except Exception as e:
            await message.reply(
                "**Usage: /addcmd**\n\n"
                "**Text response:**\n`/addcmd hello | Hello World!`\n\n"
                "**Code response:**\n`/addcmd snippet | print('hello') --code python`\n\n"
                "**Media response:**\nReply to a photo/video/audio/document:\n`/addcmd logo | Here is our logo`\n\n"
                "**Text only (no caption):**\nReply to media with just: `/addcmd logo`"
            )

    async def cmd_list_commands(self, client, message):
        cmds = db.get_all_custom_commands()
        if not cmds:
            await message.reply("No custom commands found.\n\nUse /addcmd to add one!")
            return
        text = "📝 **Custom Commands:**\n\n"
        for cmd in cmds:
            status = "✅" if cmd["is_active"] else "❌"
            t = cmd["response_type"] or "text"
            text += f"{status} `/{cmd['command']}` [{t}] — {cmd['usage_count']} uses\n"
        await message.reply(text)

    async def cmd_add_auto_reply(self, client, message):
        try:
            args = message.text.split(None, 1)[1]
            parts = args.split('|')
            keyword = parts[0].strip()
            response = parts[1].strip() if len(parts) > 1 else ""
            match = parts[2].strip() if len(parts) > 2 else "contains"
            db.add_auto_reply(keyword, response, match)
            await message.reply(f"✅ Auto-reply added!\nKeyword: `{keyword}`\nMatch: {match}")
        except:
            await message.reply("Usage: /addautoreply keyword | response | exact/contains")

    async def cmd_user_info(self, client, message, query):
        results = db.search_user(query)
        if not results:
            await message.reply(f"User not found: `{query}`")
            return
        for row in results[:3]:
            uid = row["user_id"]
            is_prem = db.is_premium(uid)
            is_ban = db.is_banned(uid)
            is_adm = db.is_admin(uid)
            join = datetime.fromtimestamp(row["join_date"]).strftime("%Y-%m-%d") if row["join_date"] else "Unknown"
            text = f"""<blockquote>
👤 <b>User Info</b>

<b>ID:</b> <code>{uid}</code>
<b>Name:</b> {row['first_name']} {row.get('last_name','') or ''}
<b>Username:</b> @{row['username'] or 'N/A'}
<b>Joined:</b> {join}
<b>Status:</b> {'⭐ Premium' if is_prem else '📝 Free'}
<b>Admin:</b> {'Yes ✅' if is_adm else 'No'}
<b>Banned:</b> {'Yes 🚫' if is_ban else 'No'}
<b>Total Edits:</b> {row['total_edits']}
<b>Coins:</b> {row['coins']}
<b>Referrals:</b> {db.get_referral_count(uid)}
<b>Trial Used:</b> {'Yes' if row.get('trial_used') else 'No'}
</blockquote>"""
            await message.reply(text, parse_mode=enums.ParseMode.HTML)

    async def do_export(self, client, message):
        data = {
            'settings': db.get_all_settings(),
            'custom_commands': [],
            'auto_reply': []
        }
        for cmd in db.get_all_custom_commands():
            data['custom_commands'].append(dict(cmd))
        for ar in db.get_all_auto_replies():
            data['auto_reply'].append(dict(ar))
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, f, indent=2, default=str)
        f.close()
        await client.send_document(message.chat.id, f.name,
            caption="📦 Bot Configuration Export", file_name="bot_config.json")
        try: os.unlink(f.name)
        except: pass

    # ==================== MEDIA PROCESSING ====================
    async def process_image(self, client, message):
        uid = message.from_user.id
        if db.is_banned(uid):
            await message.reply("🚫 You are banned.")
            return
        if db.get_setting('maintenance_mode','0') == '1' and not db.is_admin(uid):
            await message.reply("🔧 Bot is under maintenance.")
            return
        if not db.can_edit(uid):
            free_edits = db.get_setting('free_edits', Config.MAX_FREE_EDITS)
            await message.reply(f"⚠️ Free limit reached ({free_edits} edits/day)!\nUpgrade to /premium for unlimited edits.")
            return

        db.set_session(uid, 'image_edit', {'file_id': message.photo.file_id, 'type': 'photo'})
        speed = "⚡ FAST" if db.is_premium(uid) else "📝 Normal"
        await message.reply(
            f"📸 **Image Received!**\n\nProcessing Speed: {speed}\n\nChoose a filter category:",
            reply_markup=InlineKB.image_categories()
        )

    async def process_video(self, client, message):
        uid = message.from_user.id
        if db.is_banned(uid):
            await message.reply("🚫 You are banned.")
            return
        if db.get_setting('maintenance_mode','0') == '1' and not db.is_admin(uid):
            await message.reply("🔧 Bot is under maintenance.")
            return
        if not db.can_edit(uid):
            free_edits = db.get_setting('free_edits', Config.MAX_FREE_EDITS)
            await message.reply(f"⚠️ Free limit reached ({free_edits} edits/day)!\nUpgrade to /premium for unlimited edits.")
            return
        if message.video.file_size > Config.MAX_VIDEO_SIZE and not db.is_premium(uid):
            await message.reply("⚠️ Video too large (>4GB). Premium users can upload up to 4GB.\nUpgrade: /premium")
            return

        session, step, _ = db.get_session(uid)

        # Check if waiting for compress video
        if step == "awaiting_compress_video":
            db.set_session(uid, 'compress_edit', {'file_id': message.video.file_id})
            await message.reply(
                "🗜️ **Choose compression quality:**\n\n• 144p - Minimum size\n• 4K - Maximum quality",
                reply_markup=InlineKB.compress_menu()
            )
            return

        db.set_session(uid, 'video_edit', {'file_id': message.video.file_id})
        speed = "⚡ FAST" if db.is_premium(uid) else "📝 Normal"
        await message.reply(
            f"🎬 **Video Received!**\n\nProcessing Speed: {speed}\n\nChoose an effect category:",
            reply_markup=InlineKB.video_categories()
        )

    async def process_document(self, client, message):
        uid = message.from_user.id
        session, step, _ = db.get_session(uid)

        if step == "awaiting_rename_file":
            fname = message.document.file_name or "file"
            db.set_session(uid, "awaiting_rename_name", {
                "file_id": message.document.file_id,
                "file_name": fname,
                "file_size": message.document.file_size or 0
            })
            ext = os.path.splitext(fname)[1] if fname else ""
            await message.reply(
                f"📝 **File Received!**\n\nOriginal name: `{fname}`\n\nNow send the **new name** (with extension):\n\nExample: `my_video{ext}`"
            )
        elif step == "awaiting_metadata_file":
            db.set_session(uid, "awaiting_metadata_tags", {
                "file_id": message.document.file_id,
                "file_name": message.document.file_name or "file",
                "file_type": "document"
            })
            await self.show_metadata_prompt(client, uid, message)
        else:
            # Also check if it's a video document for editing
            fname = message.document.file_name or ""
            ext = os.path.splitext(fname)[1].lower()
            if ext in Config.SUPPORTED_VIDEO and db.can_edit(uid):
                db.set_session(uid, 'video_edit', {'file_id': message.document.file_id})
                await message.reply(
                    "🎬 **Video Document Received!**\n\nChoose an effect:",
                    reply_markup=InlineKB.video_categories()
                )
            elif ext in Config.SUPPORTED_IMAGE and db.can_edit(uid):
                db.set_session(uid, 'image_edit', {'file_id': message.document.file_id, 'type': 'document'})
                await message.reply(
                    "📸 **Image Document Received!**\n\nChoose a filter:",
                    reply_markup=InlineKB.image_categories()
                )
            else:
                await message.reply(
                    "📁 **File received!**\n\nWhat would you like to do?",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📝 Rename File", callback_data="rename_start")],
                        [InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]
                    ])
                )
                db.set_session(uid, "got_file", {
                    "file_id": message.document.file_id,
                    "file_name": message.document.file_name or "file"
                })

    async def process_audio(self, client, message):
        uid = message.from_user.id
        session, step, _ = db.get_session(uid)

        if step == "awaiting_metadata_file":
            db.set_session(uid, "awaiting_metadata_tags", {
                "file_id": message.audio.file_id,
                "file_name": message.audio.file_name or "audio.mp3",
                "file_type": "audio",
                "title": message.audio.title or "",
                "artist": message.audio.performer or ""
            })
            await self.show_metadata_prompt(client, uid, message)
        else:
            db.set_session(uid, "awaiting_metadata_file_queued", {"file_id": message.audio.file_id, "file_name": message.audio.file_name or "audio.mp3"})
            await message.reply(
                "🎵 **Audio received!**\n\nWhat do you want to do?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏷️ Edit Metadata", callback_data="metadata_start")],
                    [InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]
                ])
            )

    async def show_metadata_prompt(self, client, uid, message):
        await message.reply(
            "🏷️ **Metadata Editor**\n\n"
            "Send the metadata in this format:\n\n"
            "`title: My Video Title`\n"
            "`artist: Artist Name`\n"
            "`album: Album Name`\n"
            "`year: 2024`\n"
            "`comment: My comment`\n\n"
            "You can send one or multiple fields. Fields not included will remain unchanged."
        )

    async def handle_text(self, client, message):
        uid = message.from_user.id
        text = message.text or ""

        # Check maintenance (admins bypass)
        if db.get_setting('maintenance_mode','0') == '1' and not db.is_admin(uid):
            return

        # Handle custom commands (text starting with /)
        if text.startswith('/'):
            cmd_part = text.split()[0][1:].split('@')[0].lower()
            cmd_data = db.get_custom_command(cmd_part)
            if cmd_data:
                await self.execute_custom_command(client, message, cmd_data)
                return

        # Handle session steps
        session, step, media_path = db.get_session(uid)

        if step == "awaiting_rename_name":
            await self.do_rename(client, message, session)
            return

        if step == "awaiting_metadata_tags":
            await self.do_metadata_edit(client, message, session)
            return

        # Check auto-reply
        lower_text = text.lower()
        for rule in db.get_all_auto_replies():
            kw = rule["keyword"]
            mt = rule["match_type"]
            if mt == "exact" and lower_text == kw.lower():
                if rule.get("media_file_id") and rule.get("media_type"):
                    await self.send_media_reply(client, message, rule["media_type"], rule["media_file_id"], rule["response"])
                else:
                    await message.reply(rule["response"])
                return
            elif mt == "contains" and kw.lower() in lower_text:
                if rule.get("media_file_id") and rule.get("media_type"):
                    await self.send_media_reply(client, message, rule["media_type"], rule["media_file_id"], rule["response"])
                else:
                    await message.reply(rule["response"])
                return
            elif mt == "startswith" and lower_text.startswith(kw.lower()):
                await message.reply(rule["response"])
                return

    async def execute_custom_command(self, client, message, cmd_data):
        rtype = cmd_data.get("response_type", "text")
        response = cmd_data.get("response", "")
        media_id = cmd_data.get("media_file_id")

        try:
            if rtype == "photo" and media_id:
                await client.send_photo(message.chat.id, media_id, caption=response or None)
            elif rtype == "video" and media_id:
                await client.send_video(message.chat.id, media_id, caption=response or None)
            elif rtype == "audio" and media_id:
                await client.send_audio(message.chat.id, media_id, caption=response or None)
            elif rtype == "document" and media_id:
                await client.send_document(message.chat.id, media_id, caption=response or None)
            elif rtype == "sticker" and media_id:
                await client.send_sticker(message.chat.id, media_id)
                if response:
                    await message.reply(response)
            elif rtype == "voice" and media_id:
                await client.send_voice(message.chat.id, media_id, caption=response or None)
            elif rtype == "code":
                lang = cmd_data.get("code_language", "")
                code_text = f"```{lang}\n{response}\n```" if lang else f"```\n{response}\n```"
                await message.reply(code_text, parse_mode=enums.ParseMode.MARKDOWN)
                if media_id:
                    await self.send_media_reply(client, message, cmd_data.get("media_type",""), media_id, "")
            else:
                if response:
                    await message.reply(response, parse_mode=enums.ParseMode.HTML)
                elif media_id:
                    await self.send_media_reply(client, message, cmd_data.get("media_type",""), media_id, "")
        except Exception as e:
            logger.error(f"Custom command error: {e}")
            if response:
                try:
                    await message.reply(response)
                except:
                    pass

    async def send_media_reply(self, client, message, media_type, media_id, caption=""):
        try:
            if media_type == "photo":
                await client.send_photo(message.chat.id, media_id, caption=caption or None)
            elif media_type == "video":
                await client.send_video(message.chat.id, media_id, caption=caption or None)
            elif media_type == "audio":
                await client.send_audio(message.chat.id, media_id, caption=caption or None)
            elif media_type == "document":
                await client.send_document(message.chat.id, media_id, caption=caption or None)
            elif media_type == "sticker":
                await client.send_sticker(message.chat.id, media_id)
            elif media_type == "voice":
                await client.send_voice(message.chat.id, media_id, caption=caption or None)
        except Exception as e:
            logger.error(f"Media reply error: {e}")

    async def do_rename(self, client, message, session):
        uid = message.from_user.id
        new_name = message.text.strip()
        file_id = session.get("file_id")
        orig_name = session.get("file_name", "file")
        file_size = session.get("file_size", 0)

        if not new_name or not file_id:
            await message.reply("❌ Invalid. Start over with /rename")
            db.clear_session(uid)
            return

        speed = "⚡ FAST" if db.is_premium(uid) else "📝 Normal"
        pm = await message.reply(f"⏳ Renaming to `{new_name}`...\n\nSpeed: {speed}")

        try:
            file_path = await MediaProcessor.download_media(client, file_id, uid, "document")
            if not file_path:
                await pm.edit_text("❌ Failed to download file.")
                db.clear_session(uid)
                return

            new_path = os.path.join(Config.TEMP_DIR, new_name)
            if os.path.exists(new_path):
                new_path = os.path.join(Config.TEMP_DIR, f"{uid}_{new_name}")
            shutil.move(file_path, new_path)

            size_mb = os.path.getsize(new_path) / (1024*1024)
            await client.send_document(
                uid, new_path,
                caption=f"✅ **File Renamed!**\n\n📁 Original: `{orig_name}`\n📝 New: `{new_name}`\n💾 Size: {size_mb:.2f} MB"
            )
            db.add_rename_record(uid, orig_name, new_name, int(size_mb*1024*1024), "document")
            db.increment_edit(uid)

            try: os.unlink(new_path)
            except: pass
            await pm.delete()
            db.clear_session(uid)
        except Exception as e:
            logger.error(f"Rename error: {e}")
            await pm.edit_text(f"❌ Error: {str(e)[:200]}")
            db.clear_session(uid)

    async def do_metadata_edit(self, client, message, session):
        uid = message.from_user.id
        file_id = session.get("file_id")
        file_name = session.get("file_name", "file")
        file_type = session.get("file_type", "document")

        # Parse metadata from text
        meta = {}
        for line in message.text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                meta[key.strip().lower()] = val.strip()

        if not meta:
            await message.reply("❌ No valid metadata fields found.\n\nFormat: `title: My Title`")
            return
        if not file_id:
            await message.reply("❌ No file found. Please send a file first.")
            db.clear_session(uid)
            return

        pm = await message.reply("⏳ Editing metadata...")

        try:
            file_path = await MediaProcessor.download_media(client, file_id, uid, file_type)
            if not file_path:
                await pm.edit_text("❌ Failed to download file.")
                db.clear_session(uid)
                return

            ext = os.path.splitext(file_name)[1].lower()
            if ext in Config.SUPPORTED_AUDIO:
                output = await MediaProcessor.set_audio_metadata(file_path, meta)
            else:
                output = await MediaProcessor.set_video_metadata(file_path, meta)

            meta_str = "\n".join([f"• {k}: {v}" for k, v in meta.items()])
            await client.send_document(
                uid, output,
                caption=f"✅ **Metadata Updated!**\n\n📝 Changes:\n{meta_str}",
                file_name=file_name
            )

            try: os.unlink(file_path)
            except: pass
            try: os.unlink(output)
            except: pass
            await pm.delete()
            db.clear_session(uid)
        except Exception as e:
            logger.error(f"Metadata edit error: {e}")
            await pm.edit_text(f"❌ Error: {str(e)[:200]}")
            db.clear_session(uid)

    # ==================== CALLBACK HANDLER ====================
    async def handle_callback(self, client, callback):
        uid = callback.from_user.id
        data = callback.data

        try:
            await callback.answer()
        except:
            pass

        # Maintenance check
        if db.get_setting('maintenance_mode','0') == '1' and not db.is_admin(uid):
            try:
                await callback.answer("🔧 Bot is under maintenance.", show_alert=True)
            except:
                pass
            return

        # ---- MAIN MENU ----
        if data == "main_menu":
            try:
                await callback.message.edit_text(
                    f"🎬 **{Config.BOT_NAME}**\n\nChoose an option:",
                    reply_markup=InlineKB.main_menu(uid)
                )
            except:
                pass

        # ---- IMAGE MENUS ----
        elif data == "menu_image":
            await callback.message.edit_text(
                "📸 **Image Editor**\n\nChoose a filter category:",
                reply_markup=InlineKB.image_categories()
            )

        elif data.startswith("img_catpage:"):
            page = int(data.split(":")[1])
            await callback.message.edit_reply_markup(InlineKB.image_categories(page))

        elif data.startswith("img_cat:"):
            parts = data.split(":")
            cat = parts[1]
            page = int(parts[2]) if len(parts) > 2 else 0
            await callback.message.edit_text(
                f"📸 **{cat.title()} Filters**\n\nChoose a filter:",
                reply_markup=InlineKB.image_filters(cat, page)
            )

        elif data.startswith("img_filterpage:"):
            parts = data.split(":")
            cat = parts[1]
            page = int(parts[2])
            await callback.message.edit_reply_markup(InlineKB.image_filters(cat, page))

        elif data.startswith("apply_img:"):
            filter_name = data[10:]
            await self.apply_image_edit(client, callback, filter_name)

        # ---- VIDEO MENUS ----
        elif data == "menu_video":
            await callback.message.edit_text(
                "🎬 **Video Editor**\n\nChoose an effect category:",
                reply_markup=InlineKB.video_categories()
            )

        elif data.startswith("vid_catpage:"):
            page = int(data.split(":")[1])
            await callback.message.edit_reply_markup(InlineKB.video_categories(page))

        elif data.startswith("vid_cat:"):
            parts = data.split(":")
            cat = parts[1]
            page = int(parts[2]) if len(parts) > 2 else 0
            await callback.message.edit_text(
                f"🎬 **{cat.title()} Effects**\n\nChoose an effect:",
                reply_markup=InlineKB.video_effects(cat, page)
            )

        elif data.startswith("vid_effectpage:"):
            parts = data.split(":")
            cat = parts[1]
            page = int(parts[2])
            await callback.message.edit_reply_markup(InlineKB.video_effects(cat, page))

        elif data.startswith("apply_vid:"):
            effect_name = data[10:]
            await self.apply_video_edit(client, callback, effect_name)

        # ---- COMPRESS ----
        elif data == "menu_compress":
            session, step, _ = db.get_session(uid)
            if step == 'video_edit' and session and 'file_id' in session:
                # Has video, show compress directly
                db.set_session(uid, 'compress_edit', {'file_id': session['file_id']})
                await callback.message.edit_text(
                    "🗜️ **Compress Video**\n\nChoose quality preset:",
                    reply_markup=InlineKB.compress_menu()
                )
            else:
                db.set_session(uid, "awaiting_compress_video", {})
                await callback.message.edit_text(
                    "🗜️ **Video Compression (144p → 4K)**\n\n"
                    "Send your video and I'll compress it to the quality you choose.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
                )

        elif data.startswith("compress:"):
            quality = data[9:]
            await self.apply_compression(client, callback, quality)

        # ---- RENAME ----
        elif data == "menu_rename":
            await callback.message.edit_text(
                "📝 **Rename + Metadata**\n\nChoose what you want to do:",
                reply_markup=InlineKB.rename_menu()
            )

        elif data == "rename_start":
            db.set_session(uid, "awaiting_rename_file", {})
            await callback.message.edit_text(
                "📤 **Send me any file to rename!**\n\nSupported: Any file type | Up to 4GB\n⚡ Premium users get priority processing!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_rename")]])
            )

        elif data == "metadata_start":
            db.set_session(uid, "awaiting_metadata_file", {})
            await callback.message.edit_text(
                "🏷️ **Metadata Editor**\n\nSend a video or audio file to edit its metadata.\n\nSupported fields: title, artist, album, year, comment",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_rename")]])
            )

        elif data == "rename_history":
            history = db.get_rename_history(uid, 10)
            if not history:
                text = "📜 No rename history found."
            else:
                text = "📜 **Last 10 Renames:**\n\n"
                for row in history:
                    d = datetime.fromtimestamp(row['timestamp']).strftime('%m/%d %H:%M')
                    text += f"`{d}` {row['original_name']} → `{row['new_name']}`\n"
            await callback.message.edit_text(
                text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_rename")]])
            )

        # ---- AI TOOLS ----
        elif data == "menu_ai":
            await callback.message.edit_text(
                "✨ **AI Tools**\n\n• 🗣️ AI Speech Synthesis\n• 📝 AI Auto-Subtitles\n• 👤 Face Blur\n• 🎨 AI Enhance\n• 🎬 Scene Detection\n• 📊 Video Analysis\n\n⚡ Premium users get faster AI processing!\n\nSend a video to use AI features!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎬 AI Video Effects", callback_data="vid_cat:ai:0")],
                    [InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]
                ])
            )

        # ---- TIMELINE ----
        elif data == "menu_timeline":
            await callback.message.edit_text(
                "🎞️ **Timeline Editor**\n\n• Trim/Cut segments\n• Add transitions\n• Text overlays\n• Background music\n• Merge clips\n• Export presets\n\n⚡ Premium = FASTER!\n\nSend a video to start!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        # ---- REFER ----
        elif data == "menu_refer":
            me = await client.get_me()
            link = f"https://t.me/{me.username}?start={uid}"
            count = db.get_referral_count(uid)
            await callback.message.edit_text(
                f"👥 **Referral System**\n\nYour link:\n`{link}`\n\nReferrals: {count}\nPremium earned: {count*3} days\nCoins earned: {count*100}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        # ---- MY STATS ----
        elif data == "my_stats":
            row = db.get_user(uid)
            if row:
                prio = "⚡ HIGH" if db.is_premium(uid) else "📝 NORMAL"
                await callback.message.edit_text(
                    f"📊 **Your Stats**\n\nPremium: {'⭐ Yes' if db.is_premium(uid) else '📝 No'}\nPriority: {prio}\nTotal Edits: {row['total_edits']}\nToday: {row['edits_today']}\nRenames: {row['renamed_files']}\nReferrals: {db.get_referral_count(uid)}\nCoins: {row['coins']}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
                )

        # ---- PREMIUM ----
        elif data == "premium_info":
            await callback.message.edit_text(
                f"🌟 **Premium - {Config.PREMIUM_PRICE}**\n\n✅ FASTEST Processing\n✅ Priority Queue\n✅ No Watermark\n✅ Unlimited Edits\n✅ No Ads\n✅ 4K Export\n✅ All AI Features\n\nUse /premium or /trial",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Buy Premium", url=Config.PREMIUM_LINK)],
                    [InlineKeyboardButton("🎁 Free Trial", callback_data="free_trial")],
                    [InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]
                ])
            )

        elif data == "premium_features":
            exp = datetime.fromtimestamp(db.get_premium_expiry(uid)).strftime('%Y-%m-%d')
            await callback.message.edit_text(
                f"👑 **Premium Active**\n\nExpires: {exp}\n\n✨ FASTEST Processing\n✨ Priority Queue\n✨ No Watermark\n✨ Unlimited Edits\n✨ No Ads\n✨ 4K Export\n\nThank you for being premium! ❤️",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        elif data == "free_trial":
            if db.is_premium(uid):
                await callback.answer("You already have premium!", show_alert=True)
                return
            row = db.get_user(uid)
            if row and row["trial_used"]:
                await callback.answer("Trial already used! Use /premium to upgrade.", show_alert=True)
                return
            db.give_premium(uid, Config.FREE_TRIAL_DAYS)
            db.cursor.execute("UPDATE users SET trial_used=1 WHERE user_id=?", (uid,))
            db.conn.commit()
            await callback.message.edit_text(
                f"🎉 **7-Day Trial Activated!**\n\n⚡ PREMIUM PRIORITY PROCESSING for {Config.FREE_TRIAL_DAYS} days!\n\n✅ Unlimited edits\n✅ No watermark\n✅ No ads\n✅ Fastest processing\n✅ 4K export",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        elif data == "help_info":
            await callback.message.edit_text(
                "📚 **Quick Help**\n\n• Send photo → Image editing\n• Send video → Video editing\n• /rename → File rename\n• /metadata → Edit metadata\n• /compress → Video compression\n• /trial → 7-day free premium\n• /help → Full guide",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        elif data == "ad_watched":
            db.cursor.execute("UPDATE users SET ads_watched=ads_watched+1, total_ads_watched=total_ads_watched+1 WHERE user_id=?", (uid,))
            db.conn.commit()
            await callback.message.edit_text(
                "✅ Thanks for your support!\n\n⚡ Upgrade to /premium for no ads!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main_menu")]])
            )

        # ==================== ADMIN PANEL CALLBACKS ====================
        elif data == "admin_panel":
            if not db.is_admin(uid):
                await callback.answer("❌ Not authorized.", show_alert=True)
                return
            await callback.message.edit_text(
                "🔧 **Admin Panel (50+ Tools)**\n\nSelect an option:",
                reply_markup=InlineKB.admin_panel()
            )

        elif data.startswith("adm:"):
            if not db.is_admin(uid):
                await callback.answer("❌ Not authorized.", show_alert=True)
                return
            action = data[4:]
            await self.handle_admin_callback(client, callback, uid, action)

    async def handle_admin_callback(self, client, callback, uid, action):
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])

        if action == "stats":
            stats = db.get_stats()
            up = get_uptime()
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info().rss / (1024*1024)
            text = f"""<blockquote>
📊 <b>Bot Statistics</b>

👥 Total Users: <b>{stats['total_users']}</b>
⭐ Premium Users: <b>{stats['premium_users']}</b>
🚫 Banned Users: <b>{stats['banned_users']}</b>
✏️ Total Edits: <b>{stats['total_edits']}</b>
📅 Today Edits: <b>{stats['today_edits']}</b>
💰 Total Ads: <b>{stats['total_ads']}</b>
📄 Files Renamed: <b>{stats['total_renames']}</b>
🎯 Commands Used: <b>{stats['total_commands']}</b>
⏳ Queue Pending: <b>{stats['queue_pending']}</b>

🕐 Uptime: {up}
💾 Memory: {mem:.1f} MB
</blockquote>"""
            await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "daily":
            daily = db.get_daily_stats()
            text = "📈 <b>Daily Stats (Last 7 Days)</b>\n\n"
            for date, edits in sorted(daily.items(), reverse=True):
                bar = "█" * min(20, edits // 5) if edits > 0 else "░"
                text += f"📅 {date}: <b>{edits}</b> {bar}\n"
            await callback.message.edit_text(f"<blockquote>{text}</blockquote>",
                parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "users":
            await callback.message.edit_text(
                "👥 **User Management**\n\nAvailable commands:\n"
                "/ban id,reason,days\n/unban id\n/addprem id,days\n/rmprem id\n"
                "/addadmin id [title]\n/rmadmin id\n/userinfo id\n/addcoins id amount",
                reply_markup=back_btn
            )

        elif action == "premium":
            rows = db.get_all_premium_users()
            if not rows:
                text = "⭐ **No premium users found.**"
            else:
                text = f"⭐ <b>Premium Users ({len(rows)})</b>\n\n"
                for row in rows[:20]:
                    exp = datetime.fromtimestamp(row['premium_until']).strftime('%Y-%m-%d')
                    uname = f"@{row['username']}" if row['username'] else row['first_name']
                    text += f"• <code>{row['user_id']}</code> {uname} — expires {exp}\n"
                if len(rows) > 20:
                    text += f"\n... and {len(rows)-20} more"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "premiumlist":
            await self.handle_admin_callback(client, callback, uid, "premium")

        elif action == "commands":
            cmds = db.get_all_custom_commands()
            if not cmds:
                text = "📝 **No custom commands found.**\n\nUse /addcmd to add one!"
            else:
                text = f"📝 <b>Custom Commands ({len(cmds)})</b>\n\n"
                for cmd in cmds:
                    status = "✅" if cmd['is_active'] else "❌"
                    text += f"{status} /{cmd['command']} [{cmd['response_type']}] — {cmd['usage_count']} uses\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Command", callback_data="adm:addcmd_info")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
                ])
            )

        elif action == "addcmd_info":
            await callback.message.edit_text(
                "📝 **Add Custom Command**\n\n"
                "**Text response:**\n`/addcmd hello | Hello World!`\n\n"
                "**Code response:**\n`/addcmd snippet | print('hi') --code python`\n\n"
                "**Media response:**\nReply to photo/video/audio with:\n`/addcmd logo | Caption here`",
                reply_markup=back_btn
            )

        elif action == "autoreply":
            rules = db.get_all_auto_replies()
            if not rules:
                text = "🤖 **No auto-reply rules.**\n\nUse /addautoreply to add one!"
            else:
                text = f"🤖 <b>Auto-Reply Rules ({len(rules)})</b>\n\n"
                for r in rules[:15]:
                    text += f"• `{r['keyword']}` [{r['match_type']}]\n"
            await callback.message.edit_text(
                f"<blockquote>{text}\n\n/addautoreply keyword | response | exact/contains</blockquote>",
                parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "bans":
            banned = db.get_banned_users()
            if not banned:
                text = "✅ No banned users."
            else:
                text = f"🚫 <b>Banned Users ({len(banned)})</b>\n\n"
                for b in banned[:15]:
                    date = datetime.fromtimestamp(b['banned_date']).strftime('%Y-%m-%d') if b['banned_date'] else 'Unknown'
                    uname = f"@{b['username']}" if b.get('username') else b.get('first_name','') or ''
                    text += f"• <code>{b['user_id']}</code> {uname}\n  Reason: {b['reason'][:30]}\n  Date: {date}\n\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "adminlist":
            admins = db.get_all_admins()
            text = f"👑 <b>Admin List ({len(admins)+1})</b>\n\n"
            text += f"• <code>{Config.OWNER_ID}</code> 👑 Owner\n"
            for a in admins:
                text += f"• <code>{a['user_id']}</code> — {a.get('title','Admin')}\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "topusers":
            top = db.get_top_users(10)
            text = "🏆 <b>Top 10 Users by Edits</b>\n\n"
            for i, u in enumerate(top, 1):
                uname = f"@{u['username']}" if u['username'] else u['first_name']
                text += f"{i}. {uname} — <b>{u['total_edits']}</b> edits\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "topreferrers":
            top = db.get_top_referrers(10)
            text = "🔗 <b>Top Referrers</b>\n\n"
            for i, r in enumerate(top, 1):
                try:
                    user = await client.get_users(r['referrer_id'])
                    name = f"@{user.username}" if user.username else user.first_name
                except:
                    name = f"User {r['referrer_id']}"
                text += f"{i}. {name} — <b>{r['cnt']}</b> referrals\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "recentedits":
            edits = db.get_recent_edits(10)
            text = "📝 <b>Recent Edits</b>\n\n"
            for e in edits:
                date = datetime.fromtimestamp(e['timestamp']).strftime('%m/%d %H:%M') if e['timestamp'] else ''
                uname = f"@{e['username']}" if e.get('username') else str(e['user_id'])
                text += f"• {uname} — {e['operation']} [{e['file_type']}] {date}\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "settings":
            await callback.message.edit_text(
                "⚙️ **Bot Settings**\n\nChoose a setting to change:",
                reply_markup=InlineKB.admin_settings()
            )

        elif action == "viewsettings":
            settings = db.get_all_settings()
            text = "⚙️ <b>All Settings</b>\n\n"
            for k, v in settings.items():
                val_str = v[:30] + "..." if len(str(v)) > 30 else str(v)
                text += f"• {k}: <code>{val_str}</code>\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "togglewatermark":
            current = db.get_setting('watermark_enabled', '1')
            new_val = '0' if current == '1' else '1'
            db.set_setting('watermark_enabled', new_val, uid)
            status = "Enabled ✅" if new_val == '1' else "Disabled ❌"
            await callback.answer(f"Watermark: {status}", show_alert=True)
            await callback.message.edit_text("⚙️ Settings updated!", reply_markup=back_btn)

        elif action == "toggleads":
            current = db.get_setting('ads_enabled', '1')
            new_val = '0' if current == '1' else '1'
            db.set_setting('ads_enabled', new_val, uid)
            status = "Enabled ✅" if new_val == '1' else "Disabled ❌"
            await callback.answer(f"Ads: {status}", show_alert=True)

        elif action == "maintenanceon":
            db.set_setting('maintenance_mode', '1', uid)
            await callback.answer("🔒 Maintenance mode ON", show_alert=True)
            await callback.message.edit_text("🔒 Maintenance mode is now ON.\n\nOnly admins can use the bot.", reply_markup=back_btn)

        elif action == "maintenanceoff":
            db.set_setting('maintenance_mode', '0', uid)
            await callback.answer("🔓 Maintenance mode OFF", show_alert=True)
            await callback.message.edit_text("🔓 Maintenance mode is now OFF.\n\nBot is back for everyone!", reply_markup=back_btn)

        elif action in ("setwelcome","setwatermark","setfreeedits","setadsinterval","addadmin","rmadmin",
                         "banuser","unbanuser","givepremium","rmpremium","addcoins","searchuser","userinfo",
                         "broadcast","resetsettings"):
            cmd_map = {
                "setwelcome": "/setwelcome <text>",
                "setwatermark": "/setwatermark <text>",
                "setfreeedits": "/setfree <count>",
                "setadsinterval": "/setads <on/off>,<interval>",
                "addadmin": "/addadmin <user_id> [title]",
                "rmadmin": "/rmadmin <user_id>",
                "banuser": "/ban <user_id>,<reason>,<days>",
                "unbanuser": "/unban <user_id>",
                "givepremium": "/addprem <user_id>,<days>",
                "rmpremium": "/rmprem <user_id>",
                "addcoins": "/addcoins <user_id> <amount>",
                "searchuser": "/userinfo <user_id or @username>",
                "userinfo": "/userinfo <user_id or @username>",
                "broadcast": "/broadcast <message> (or reply to media)",
                "resetsettings": "Contact developer to reset all settings",
            }
            usage = cmd_map.get(action, f"/{action}")
            await callback.message.edit_text(
                f"📝 **{action.title()}**\n\nUsage: `{usage}`",
                reply_markup=back_btn
            )

        elif action == "backup":
            await callback.message.edit_text("⏳ Creating backup...", reply_markup=back_btn)
            bp = db.backup_database()
            await client.send_document(callback.message.chat.id, bp,
                caption=f"📦 Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            try: os.unlink(bp)
            except: pass
            await callback.message.edit_text("✅ Backup created and sent!", reply_markup=back_btn)

        elif action == "export":
            await self.do_export(client, callback.message)
            await callback.message.edit_text("✅ Config exported!", reply_markup=back_btn)

        elif action == "cleanup":
            count = db.cleanup_temp_files(1)
            await callback.message.edit_text(f"✅ Cleaned {count} temp files.", reply_markup=back_btn)

        elif action == "dbinfo":
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = db.cursor.fetchall()
            text = f"💾 <b>Database Info</b>\n\n📁 File: {Config.DB_PATH}\n💾 Size: {db.get_db_size()/1024:.1f} KB\n\n<b>Tables:</b>\n"
            for t in tables:
                db.cursor.execute(f"SELECT COUNT(*) FROM {t['name']}")
                cnt = db.cursor.fetchone()[0]
                text += f"• {t['name']}: {cnt} rows\n"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "maintenance":
            current = db.get_setting('maintenance_mode','0')
            status = "ON 🔒" if current == '1' else "OFF 🔓"
            await callback.message.edit_text(
                f"🔧 **Maintenance Mode**: {status}\n\nToggle with buttons below:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔒 Turn ON", callback_data="adm:maintenanceon"),
                     InlineKeyboardButton("🔓 Turn OFF", callback_data="adm:maintenanceoff")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
                ])
            )

        elif action == "logs":
            log_path = f"{Config.LOGS_DIR}/bot.log"
            if os.path.exists(log_path):
                await client.send_document(callback.message.chat.id, log_path, caption="📝 Bot Logs")
                await callback.message.edit_text("📝 Logs sent!", reply_markup=back_btn)
            else:
                await callback.message.edit_text("❌ No log file found.", reply_markup=back_btn)

        elif action == "botstatus":
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info().rss / (1024*1024)
            cpu = psutil.cpu_percent(interval=0.1)
            up = get_uptime()
            stats = db.get_stats()
            text = f"""<blockquote>
🤖 <b>Bot Status</b>

✅ Status: Online
🕐 Uptime: {up}
💾 Memory: {mem:.1f} MB
⚡ CPU: {cpu:.1f}%
🐍 Python: {platform.python_version()}
🖥️ OS: {platform.system()} {platform.release()}
📁 DB: {db.get_db_size()/1024:.1f} KB
🔧 FFmpeg: {'✅' if shutil.which('ffmpeg') else '❌'}
🤖 Whisper: {'✅' if WHISPER_AVAILABLE else '❌'}

👥 Users: {stats['total_users']}
⭐ Premium: {stats['premium_users']}
✏️ Total Edits: {stats['total_edits']}
</blockquote>"""
            await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "queue":
            db.cursor.execute("SELECT user_id, operation, status, created_at FROM processing_queue WHERE status='pending' ORDER BY created_at ASC LIMIT 20")
            queue = db.cursor.fetchall()
            text = f"🔇 <b>Processing Queue ({len(queue)} pending)</b>\n\n"
            for item in queue:
                text += f"• User {item['user_id']}: {item['operation']}\n"
            if not queue:
                text += "Queue is empty! ✅"
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML, reply_markup=back_btn)

        elif action == "clearqueue":
            db.cursor.execute("UPDATE processing_queue SET status='cancelled' WHERE status='pending'")
            db.conn.commit()
            await callback.message.edit_text("✅ Queue cleared!", reply_markup=back_btn)

        elif action == "ads":
            ads_on = db.get_setting('ads_enabled','1') == '1'
            interval = db.get_setting('ads_interval', Config.ADS_INTERVAL)
            text = f"""⚙️ <b>Ads Settings</b>

Status: {'✅ Enabled' if ads_on else '❌ Disabled'}
Interval: Every {interval} edits
Premium users: Always ad-free

Commands:
/setads on,3 - Enable with 3-edit interval
/setads off - Disable all ads"""
            await callback.message.edit_text(
                f"<blockquote>{text}</blockquote>", parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Enable Ads", callback_data="adm:toggleads"),
                     InlineKeyboardButton("❌ Disable Ads", callback_data="adm:toggleads")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
                ])
            )

        elif action == "broadcast":
            await callback.message.edit_text(
                "📢 **Broadcast**\n\nUse:\n`/broadcast <message>` — text broadcast\n\nOr reply to a photo/video with `/broadcast` — media broadcast",
                reply_markup=back_btn
            )

    # ==================== APPLY EDITS ====================
    async def apply_image_edit(self, client, callback, filter_name):
        uid = callback.from_user.id
        session, step, _ = db.get_session(uid)

        if not session or 'file_id' not in session:
            await callback.answer("❌ Please send an image first!", show_alert=True)
            return

        is_prem = db.is_premium(uid)
        speed_text = "⚡ FAST (Premium)" if is_prem else "📝 Normal Speed"

        try:
            pm = await callback.message.reply(f"⏳ Applying **{filter_name}** filter...\n\nSpeed: {speed_text}")
        except:
            return

        try:
            file_path = await MediaProcessor.download_media(client, session['file_id'], uid, "image")
            if not file_path:
                await pm.edit_text("❌ Failed to download image. Please send the image again.")
                return

            t0 = time.time()
            output_path = await MediaProcessor.apply_image_filter(file_path, filter_name)
            proc_time = time.time() - t0

            # Apply watermark for free users
            wm_enabled = db.get_setting('watermark_enabled','1') == '1'
            if not is_prem and wm_enabled:
                wm_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=Config.TEMP_DIR).name
                MediaProcessor._add_watermark_static(output_path, wm_path, db.get_setting('watermark_text', Config.WATERMARK_TEXT))
                try: os.unlink(output_path)
                except: pass
                output_path = wm_path

            await client.send_photo(
                uid, output_path,
                caption=f"✅ **{filter_name.replace('_',' ').title()}** applied!\n\n⏱️ Time: {proc_time:.1f}s | {speed_text}"
            )

            show_ad = db.increment_edit(uid)
            db.add_edit_history(uid, 'image', filter_name, os.path.getsize(file_path), os.path.getsize(output_path), proc_time)

            try: os.unlink(file_path)
            except: pass
            try: os.unlink(output_path)
            except: pass
            try: await pm.delete()
            except: pass

            if show_ad and Config.GOOGLE_ADS_ENABLED and db.get_setting('ads_enabled','1') == '1':
                await self.show_ad(client, uid)

        except Exception as e:
            logger.error(f"Image edit error [{filter_name}]: {e}")
            try:
                await pm.edit_text(f"❌ Error processing image: {str(e)[:200]}\n\nTry another filter or re-send the image.")
            except:
                pass

    async def apply_video_edit(self, client, callback, effect_name):
        uid = callback.from_user.id
        session, step, _ = db.get_session(uid)

        if not session or 'file_id' not in session:
            await callback.answer("❌ Please send a video first!", show_alert=True)
            return

        is_prem = db.is_premium(uid)
        speed_text = "⚡ FAST (Premium)" if is_prem else "📝 Normal Speed"

        try:
            pm = await callback.message.reply(f"🎬 Processing **{effect_name}**...\n\nSpeed: {speed_text}\nThis may take a moment...")
        except:
            return

        try:
            file_path = await MediaProcessor.download_media(client, session['file_id'], uid, "video")
            if not file_path:
                await pm.edit_text("❌ Failed to download video. Please send the video again.")
                return

            params = {}
            t0 = time.time()
            output_path = await MediaProcessor.apply_video_effect(file_path, effect_name, params)
            proc_time = time.time() - t0

            if not output_path or not os.path.exists(output_path):
                await pm.edit_text("❌ Processing failed. Try a different effect.")
                return

            output_size = os.path.getsize(output_path)
            # Send as appropriate type
            ext = os.path.splitext(output_path)[1].lower()
            cap = f"✅ **{effect_name.replace('_',' ').title()}** applied!\n\n⏱️ Time: {proc_time:.1f}s | {speed_text}\n💾 Size: {output_size/(1024*1024):.1f} MB"

            if ext == '.gif':
                await client.send_animation(uid, output_path, caption=cap)
            elif ext == '.mp3':
                await client.send_audio(uid, output_path, caption=cap)
            elif ext in ('.jpg', '.png'):
                await client.send_photo(uid, output_path, caption=cap)
            elif ext == '.txt':
                await client.send_document(uid, output_path, caption=cap)
            else:
                await client.send_video(uid, output_path, caption=cap, supports_streaming=True)

            show_ad = db.increment_edit(uid)
            db.add_edit_history(uid, 'video', effect_name, os.path.getsize(file_path), output_size, proc_time)

            try: os.unlink(file_path)
            except: pass
            try: os.unlink(output_path)
            except: pass
            try: await pm.delete()
            except: pass

            if show_ad and Config.GOOGLE_ADS_ENABLED and db.get_setting('ads_enabled','1') == '1':
                await self.show_ad(client, uid)

        except Exception as e:
            logger.error(f"Video edit error [{effect_name}]: {e}")
            try:
                await pm.edit_text(f"❌ Error: {str(e)[:200]}\n\nTry a different effect or re-send the video.")
            except:
                pass

    async def apply_compression(self, client, callback, quality):
        uid = callback.from_user.id
        session, step, _ = db.get_session(uid)

        if not session or 'file_id' not in session:
            await callback.answer("❌ Please send a video first!", show_alert=True)
            return

        preset = Config.VIDEO_QUALITY_PRESETS.get(quality, {})
        if not preset:
            await callback.answer(f"❌ Unknown quality: {quality}", show_alert=True)
            return

        is_prem = db.is_premium(uid)
        # 4K only for premium
        if quality == "4k" and not is_prem:
            await callback.answer("❌ 4K export is a Premium feature!\nUse /premium or /trial", show_alert=True)
            return

        try:
            pm = await callback.message.reply(
                f"🗜️ Compressing to **{quality.upper()}** ({preset['width']}x{preset['height']})...\n\n"
                f"Bitrate: {preset['bitrate']}\nThis may take a while for large videos..."
            )
        except:
            return

        try:
            file_path = await MediaProcessor.download_media(client, session['file_id'], uid, "video")
            if not file_path:
                await pm.edit_text("❌ Failed to download video.")
                return

            orig_size = os.path.getsize(file_path)
            t0 = time.time()
            output_path = await MediaProcessor.compress_video(file_path, quality)
            proc_time = time.time() - t0
            new_size = os.path.getsize(output_path)

            ratio = (1 - new_size/orig_size) * 100 if orig_size > 0 else 0
            cap = (f"✅ **Compressed to {quality.upper()}!**\n\n"
                   f"📐 Resolution: {preset['width']}x{preset['height']}\n"
                   f"📦 Original: {orig_size/(1024*1024):.1f} MB\n"
                   f"📦 Compressed: {new_size/(1024*1024):.1f} MB\n"
                   f"💡 Saved: {ratio:.1f}%\n"
                   f"⏱️ Time: {proc_time:.1f}s")

            await client.send_video(uid, output_path, caption=cap, supports_streaming=True)
            db.increment_edit(uid)
            db.add_edit_history(uid, 'video', f'compress_{quality}', orig_size, new_size, proc_time)

            try: os.unlink(file_path)
            except: pass
            try: os.unlink(output_path)
            except: pass
            try: await pm.delete()
            except: pass

        except Exception as e:
            logger.error(f"Compression error [{quality}]: {e}")
            try:
                await pm.edit_text(f"❌ Compression failed: {str(e)[:200]}")
            except:
                pass

    async def show_ad(self, client, user_id):
        if db.is_premium(user_id) or db.get_setting('ads_enabled','1') != '1':
            return
        text = f"📢 **Support Our Bot**\n\n{Config.ADS_TEXT}\n\n⭐ Upgrade to /premium to remove ads!"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Watched Ad", callback_data="ad_watched"),
             InlineKeyboardButton("⭐ Premium", callback_data="premium_info")]
        ])
        try:
            await client.send_message(user_id, text, reply_markup=kb, disable_web_page_preview=True)
        except:
            pass

    def run(self):
        print("=" * 65)
        print(f"🤖 {Config.BOT_NAME} v{Config.BOT_VERSION}")
        print("=" * 65)
        print(f"📸 Image Tools: {sum(len(v) for v in MediaProcessor.IMAGE_FILTERS.values())}+")
        print(f"🎬 Video Tools: {sum(len(v) for v in MediaProcessor.VIDEO_EFFECTS.values())}+")
        print(f"🗜️ Compression: 144p → 4K ({len(Config.VIDEO_QUALITY_PRESETS)} presets)")
        print(f"👑 Admin Panel: 50+ tools")
        print(f"📝 File Rename: ✅ | Metadata Edit: ✅")
        print(f"💰 Ads: {'On' if Config.GOOGLE_ADS_ENABLED else 'Off'}")
        print(f"🤖 Whisper AI: {'Available' if WHISPER_AVAILABLE else 'Not Installed'}")
        print(f"🌐 Web Dashboard: http://0.0.0.0:5000")
        print("=" * 65)
        print("🚀 Bot is ALIVE and READY!")
        print("=" * 65)

        if not db.is_admin(Config.OWNER_ID):
            db.add_admin(Config.OWNER_ID, Config.OWNER_ID, title="Owner")
            print(f"✅ Owner {Config.OWNER_ID} added as admin")

        self.app.run()

    async def shutdown(self):
        print("🛑 Shutting down...")
        db.conn.close()


# ==================== MAIN ====================
if __name__ == "__main__":
    if not shutil.which('ffmpeg'):
        print("⚠️ WARNING: FFmpeg not found! Video features will be limited.")

    bot = MediaEditorBot()

    def signal_handler(sig, frame):
        print("\n🛑 Shutdown signal received...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
