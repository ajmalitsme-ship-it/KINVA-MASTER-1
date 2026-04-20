#!/usr/bin/env python3
"""
KiraFx Media Editor Bot v7.0 Ultra Premium Edition
Full-featured Telegram bot for image/video editing, premium management,
50+ admin panel, timeline editing, inline callbacks, Google ads, and more.
"""

# ============================================================
# IMPORTS
# ============================================================
import os
import sys
import asyncio
import sqlite3
import logging
import threading
import subprocess
import shutil
import time
import json
import re
import math
import random
import string
import hashlib
import tempfile
import traceback
import io
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List, Tuple, Any
from functools import wraps
from queue import PriorityQueue

# Third-party imports
try:
    from pyrogram import Client, filters, enums
    from pyrogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, User, InputMediaPhoto
    )
    from pyrogram.errors import FloodWait, UserNotParticipant, RPCError
except ImportError:
    os.system("pip install pyrogram tgcrypto")
    from pyrogram import Client, filters, enums
    from pyrogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, User, InputMediaPhoto
    )
    from pyrogram.errors import FloodWait, UserNotParticipant, RPCError

try:
    from PIL import (
        Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont,
        ImageOps, ImageChops
    )
    import PIL.ImageFilter as PF
except ImportError:
    os.system("pip install Pillow")
    from PIL import (
        Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont,
        ImageOps, ImageChops
    )

try:
    from flask import Flask, render_template_string, jsonify, request as flask_request
except ImportError:
    os.system("pip install flask")
    from flask import Flask, render_template_string, jsonify, request as flask_request

try:
    import psutil
except ImportError:
    os.system("pip install psutil")
    import psutil

try:
    import requests as req_lib
except ImportError:
    os.system("pip install requests")
    import requests as req_lib

# ============================================================
# CONFIGURATION
# ============================================================
BOT_TOKEN   = os.environ.get("BOT_TOKEN",  "8623600399:AAGNn_d6Lq5DRrwelD_rvOUfgsM-jyk8Kf8")
API_ID      = int(os.environ.get("API_ID",  27806628))
API_HASH    = os.environ.get("API_HASH",    "25d88301e886b82826a525b7cf52e090")
OWNER_ID    = int(os.environ.get("OWNER_ID","8525952693"))
DB_PATH     = os.environ.get("DB_PATH",     "kiraFx.db")
TEMP_DIR    = os.environ.get("TEMP_DIR",    "temp_files")
LOG_FILE    = os.environ.get("LOG_FILE",    "kiraFx.log")
FLASK_PORT  = int(os.environ.get("PORT",    "5000"))
FREE_EDITS_PER_DAY = int(os.environ.get("FREE_EDITS_PER_DAY", "6"))
KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "")
BOT_NAME    = "KiraFx Media Editor Bot"
BOT_VERSION = "8.0 Ultra Premium"
START_TIME  = time.time()

# Premium plan pricing (display only)
PREMIUM_PLANS = {
    "weekly":   {"days": 7,    "label": "7 Days",    "price": "$1.99",  "emoji": "🥉"},
    "monthly":  {"days": 30,   "label": "1 Month",   "price": "$4.99",  "emoji": "🥈"},
    "quarterly":{"days": 90,   "label": "3 Months",  "price": "$9.99",  "emoji": "🥇"},
    "biannual": {"days": 180,  "label": "6 Months",  "price": "$15.99", "emoji": "💎"},
    "yearly":   {"days": 365,  "label": "1 Year",    "price": "$24.99", "emoji": "👑"},
    "lifetime": {"days": 36500,"label": "Lifetime",  "price": "$49.99", "emoji": "🌟"},
}

# Google Ads simulation banners
GOOGLE_ADS = [
    "📢 **Sponsored:** Upgrade to Premium – Unlimited edits, no limits! Use /premium",
    "📢 **Ad:** Get 4K video compression & 77+ effects with KiraFx Premium! /premium",
    "📢 **Promoted:** Share KiraFx with friends – earn 3 free days premium! /refer",
    "📢 **Ad:** Pro editors use KiraFx Premium – no watermarks, priority queue! /premium",
    "📢 **Sponsored:** Try KiraFx AI Generator for stunning images! /txt2img",
    "📢 **Ad:** KiraFx Logo Maker – create professional logos free! /logo",
    "📢 **Promoted:** Refer friends & earn coins. Redeem for premium days! /refer",
    "📢 **Ad:** Video timeline editor now available! Send a video to start.",
    "📢 **Sponsored:** Compress your videos in 9 quality presets! /compress",
    "📢 **Ad:** Join our channel for tips, updates & offers! t.me/KiraFxBot",
]

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("KiraFx")

# ============================================================
# TEMP DIR SETUP
# ============================================================
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================
# THREAD POOL
# ============================================================
executor = ThreadPoolExecutor(max_workers=6)

# ============================================================
# DATABASE
# ============================================================
_local = threading.local()

def get_db():
    """Get thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
    return _local.conn

def init_db():
    """Initialize database tables."""
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_until TEXT,
            premium_plan TEXT,
            is_admin INTEGER DEFAULT 0,
            admin_level INTEGER DEFAULT 0,
            admin_title TEXT,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT,
            ban_until TEXT,
            coins INTEGER DEFAULT 0,
            edits_today INTEGER DEFAULT 0,
            total_edits INTEGER DEFAULT 0,
            total_renames INTEGER DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            trial_used INTEGER DEFAULT 0,
            daily_reset TEXT,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            language TEXT DEFAULT 'en',
            notifications INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            title TEXT DEFAULT 'Admin',
            level INTEGER DEFAULT 1,
            added_by INTEGER,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            can_ban INTEGER DEFAULT 1,
            can_broadcast INTEGER DEFAULT 1,
            can_manage_premium INTEGER DEFAULT 1,
            can_manage_users INTEGER DEFAULT 1,
            can_run_code INTEGER DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS custom_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT UNIQUE NOT NULL,
            response_type TEXT DEFAULT 'text',
            response TEXT,
            media_id TEXT,
            media_type TEXT,
            is_enabled INTEGER DEFAULT 1,
            added_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS auto_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger TEXT NOT NULL,
            match_type TEXT DEFAULT 'exact',
            response TEXT,
            response_type TEXT DEFAULT 'text',
            media_id TEXT,
            is_enabled INTEGER DEFAULT 1,
            added_by INTEGER
        );

        CREATE TABLE IF NOT EXISTS edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            edit_type TEXT,
            filter_name TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS timeline_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            media_path TEXT,
            media_type TEXT,
            steps TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_type TEXT,
            job_data TEXT,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rename_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_name TEXT,
            new_name TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS broadcast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message_text TEXT,
            sent_count INTEGER,
            failed_count INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS coins_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            reason TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS premium_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            days INTEGER,
            granted_by INTEGER,
            payment_ref TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ads_shown (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ad_index INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bot_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reason TEXT,
            warned_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        INSERT OR IGNORE INTO settings (key, value) VALUES
            ('watermark_text', 'KiraFx'),
            ('free_edits_per_day', '6'),
            ('ads_enabled', '1'),
            ('ads_interval', '5'),
            ('maintenance_mode', '0'),
            ('welcome_message', 'Welcome to KiraFx Bot!'),
            ('group_only_mode', '0'),
            ('max_file_size_mb', '50'),
            ('trial_days', '7'),
            ('referral_premium_days', '3'),
            ('referral_coins', '100'),
            ('support_username', 'KiraFxSupport'),
            ('channel_username', 'KiraFxBot'),
            ('bot_status', 'online'),
            ('ads_count', '0');
    """)
    conn.commit()

    # Schema migrations: add missing columns to existing tables
    migration_columns = [
        ("users", "admin_level",      "INTEGER DEFAULT 0"),
        ("users", "premium_plan",     "TEXT"),
        ("users", "total_renames",    "INTEGER DEFAULT 0"),
        ("users", "referral_code",    "TEXT"),
        ("users", "referred_by",      "INTEGER"),
        ("users", "referral_count",   "INTEGER DEFAULT 0"),
        ("users", "daily_reset",      "TEXT"),
        ("users", "last_seen",        "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ("users", "language",         "TEXT DEFAULT 'en'"),
        ("users", "notifications",    "INTEGER DEFAULT 1"),
        ("admins", "level",                "INTEGER DEFAULT 1"),
        ("admins", "can_ban",              "INTEGER DEFAULT 1"),
        ("admins", "can_broadcast",        "INTEGER DEFAULT 1"),
        ("admins", "can_manage_premium",   "INTEGER DEFAULT 1"),
        ("admins", "can_manage_users",     "INTEGER DEFAULT 1"),
        ("admins", "can_run_code",         "INTEGER DEFAULT 0"),
        ("admins", "notes",                "TEXT"),
        ("custom_commands", "media_type", "TEXT"),
        ("custom_commands", "use_count",  "INTEGER DEFAULT 0"),
        ("users", "is_muted",             "INTEGER DEFAULT 0"),
        ("users", "muted_until",          "TEXT"),
    ]
    for table, col, col_def in migration_columns:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Ensure owner is in users and admins table
    if OWNER_ID:
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, is_admin, admin_level) VALUES (?, 'Owner', 1, 10)",
            (OWNER_ID,)
        )
        c.execute(
            """INSERT OR IGNORE INTO admins
               (user_id, title, level, added_by, can_ban, can_broadcast, can_manage_premium,
                can_manage_users, can_run_code)
               VALUES (?, 'Owner', 10, ?, 1, 1, 1, 1, 1)""",
            (OWNER_ID, OWNER_ID)
        )
        conn.commit()

    logger.info("Database initialized.")

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

def register_user(user: User, referred_by: int = None):
    conn = get_db()
    ref_code = hashlib.md5(str(user.id).encode()).hexdigest()[:8].upper()
    conn.execute("""
        INSERT OR IGNORE INTO users
            (user_id, username, first_name, last_name, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or "",
        ref_code,
        referred_by
    ))
    conn.execute(
        "UPDATE users SET username=?, first_name=?, last_name=?, last_seen=CURRENT_TIMESTAMP WHERE user_id=?",
        (user.username or "", user.first_name or "", user.last_name or "", user.id)
    )
    conn.commit()

def is_premium(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    row = get_user(user_id)
    if not row:
        return False
    if row["is_premium"]:
        if row["premium_until"]:
            try:
                until = datetime.fromisoformat(row["premium_until"])
                if until > datetime.now():
                    return True
                else:
                    get_db().execute("UPDATE users SET is_premium=0 WHERE user_id=?", (user_id,))
                    get_db().commit()
                    return False
            except Exception:
                return True
        return True
    return False

def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    row = get_user(user_id)
    return bool(row and row["is_admin"])

def get_admin_level(user_id: int) -> int:
    if user_id == OWNER_ID:
        return 10
    row = get_db().execute("SELECT level FROM admins WHERE user_id=?", (user_id,)).fetchone()
    return row["level"] if row else 0

def get_admin_perms(user_id: int) -> sqlite3.Row:
    return get_db().execute("SELECT * FROM admins WHERE user_id=?", (user_id,)).fetchone()

def is_banned(user_id: int) -> bool:
    row = get_user(user_id)
    if not row or not row["is_banned"]:
        return False
    if row["ban_until"]:
        try:
            until = datetime.fromisoformat(row["ban_until"])
            if until < datetime.now():
                get_db().execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
                get_db().commit()
                return False
        except Exception:
            pass
    return True

def can_edit(user_id: int) -> bool:
    """Check if user can perform an edit (within daily limit)."""
    if is_premium(user_id) or is_admin(user_id):
        return True
    row = get_user(user_id)
    if not row:
        return False
    today = datetime.now().date().isoformat()
    if row["daily_reset"] != today:
        get_db().execute(
            "UPDATE users SET edits_today=0, daily_reset=? WHERE user_id=?",
            (today, user_id)
        )
        get_db().commit()
        row = get_user(user_id)
    limit = int(get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY)))
    return row["edits_today"] < limit

def get_remaining_edits(user_id: int) -> str:
    if is_premium(user_id) or is_admin(user_id):
        return "∞"
    row = get_user(user_id)
    if not row:
        return "0"
    today = datetime.now().date().isoformat()
    limit = int(get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY)))
    used = row["edits_today"] if row["daily_reset"] == today else 0
    return str(max(0, limit - used))

def increment_edits(user_id: int):
    today = datetime.now().date().isoformat()
    get_db().execute(
        "UPDATE users SET edits_today=edits_today+1, total_edits=total_edits+1, daily_reset=? WHERE user_id=?",
        (today, user_id)
    )
    get_db().commit()

def add_premium(user_id: int, days: int, plan: str = "admin_grant"):
    until = (datetime.now() + timedelta(days=days)).isoformat()
    get_db().execute(
        "UPDATE users SET is_premium=1, premium_until=?, premium_plan=? WHERE user_id=?",
        (until, plan, user_id)
    )
    get_db().execute(
        "INSERT INTO premium_transactions (user_id, plan, days, granted_by) VALUES (?, ?, ?, ?)",
        (user_id, plan, days, OWNER_ID)
    )
    get_db().commit()

def add_coins(user_id: int, amount: int, reason: str = ""):
    get_db().execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, user_id))
    get_db().execute(
        "INSERT INTO coins_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
        (user_id, amount, reason)
    )
    get_db().commit()

def get_all_users() -> List[sqlite3.Row]:
    return get_db().execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()

def get_user_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]

def get_premium_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]

def get_admin_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM admins").fetchone()[0]

def get_banned_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]

def get_total_edits() -> int:
    row = get_db().execute("SELECT SUM(total_edits) FROM users").fetchone()
    return row[0] or 0

def premium_emoji(emoji_id: str, fallback: str = "✨") -> str:
    """Return an animated custom emoji string for use in bot messages.
    Usage: use the returned string inside a message with entities or parse_mode=enums.ParseMode.HTML.
    Format: <emoji id="CUSTOM_EMOJI_ID">FALLBACK</emoji>"""
    return f'<emoji id="{emoji_id}">{fallback}</emoji>'

PREMIUM_EMOJIS = {
    "star":    ("5361541227604729229", "⭐"),
    "crown":   ("5361541227604729230", "👑"),
    "fire":    ("5361541227604729231", "🔥"),
    "diamond": ("5361541227604729232", "💎"),
    "magic":   ("5361541227604729233", "✨"),
    "camera":  ("5361541227604729234", "📷"),
    "video":   ("5361541227604729235", "🎬"),
    "brush":   ("5361541227604729236", "🎨"),
    "bolt":    ("5361541227604729237", "⚡"),
    "shield":  ("5361541227604729238", "🛡️"),
    "check":   ("5361541227604729239", "✅"),
    "gift":    ("5361541227604729240", "🎁"),
    "coin":    ("5361541227604729241", "🪙"),
    "robot":   ("5361541227604729242", "🤖"),
    "rocket":  ("5361541227604729243", "🚀"),
}

def pem(name: str) -> str:
    """Quick shorthand for premium emoji by name."""
    if name in PREMIUM_EMOJIS:
        eid, fallback = PREMIUM_EMOJIS[name]
        return premium_emoji(eid, fallback)
    return "✨"

def get_today_edits() -> int:
    today = datetime.now().date().isoformat()
    row = get_db().execute(
        "SELECT SUM(edits_today) FROM users WHERE daily_reset=?", (today,)
    ).fetchone()
    return row[0] or 0

def get_today_new_users() -> int:
    today = datetime.now().date().isoformat()
    row = get_db().execute(
        "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (today + "%",)
    ).fetchone()
    return row[0] or 0

def log_edit(user_id: int, edit_type: str, filter_name: str):
    get_db().execute(
        "INSERT INTO edit_history (user_id, edit_type, filter_name) VALUES (?, ?, ?)",
        (user_id, edit_type, filter_name)
    )
    get_db().commit()

def log_rename(user_id: int, original: str, new_name: str):
    get_db().execute(
        "INSERT INTO rename_history (user_id, original_name, new_name) VALUES (?, ?, ?)",
        (user_id, original, new_name)
    )
    get_db().execute(
        "UPDATE users SET total_renames=total_renames+1 WHERE user_id=?",
        (user_id,)
    )
    get_db().commit()

def should_show_ad(user_id: int) -> bool:
    """Decide if we should show an ad to this user."""
    if is_premium(user_id) or is_admin(user_id):
        return False
    if get_setting("ads_enabled", "0") != "1":
        return False
    interval = int(get_setting("ads_interval", "5"))
    row = get_user(user_id)
    if not row:
        return False
    today = datetime.now().date().isoformat()
    edits_today = row["edits_today"] if row["daily_reset"] == today else 0
    return edits_today > 0 and edits_today % interval == 0

def get_random_ad() -> str:
    return random.choice(GOOGLE_ADS)

# ============================================================
# SESSION MANAGEMENT
# ============================================================
user_sessions: Dict[int, Dict] = {}

def set_session(user_id: int, key: str, value: Any):
    if user_id not in user_sessions:
        user_sessions[user_id] = {"created": time.time()}
    user_sessions[user_id][key] = value
    user_sessions[user_id]["updated"] = time.time()

def get_session(user_id: int, key: str, default=None):
    return user_sessions.get(user_id, {}).get(key, default)

def clear_session(user_id: int, key: str = None):
    if key:
        user_sessions.get(user_id, {}).pop(key, None)
    else:
        user_sessions.pop(user_id, None)

def cleanup_sessions():
    """Remove sessions older than 2 hours."""
    cutoff = time.time() - 7200
    stale = [uid for uid, s in user_sessions.items() if s.get("created", 0) < cutoff]
    for uid in stale:
        del user_sessions[uid]

# ============================================================
# TIMELINE EDITING SYSTEM
# ============================================================
def get_timeline(user_id: int) -> Dict:
    """Get or create timeline session for user."""
    row = get_db().execute(
        "SELECT * FROM timeline_sessions WHERE user_id=?", (user_id,)
    ).fetchone()
    if not row:
        return {"steps": [], "media_path": None, "media_type": None}
    return {
        "steps": json.loads(row["steps"] or "[]"),
        "media_path": row["media_path"],
        "media_type": row["media_type"],
    }

def save_timeline(user_id: int, media_path: str, media_type: str, steps: List):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO timeline_sessions (user_id, media_path, media_type, steps, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, media_path, media_type, json.dumps(steps)))
    db.commit()

def clear_timeline(user_id: int):
    get_db().execute("DELETE FROM timeline_sessions WHERE user_id=?", (user_id,))
    get_db().commit()

def add_timeline_step(user_id: int, step: str):
    tl = get_timeline(user_id)
    tl["steps"].append({"step": step, "time": datetime.now().isoformat()})
    save_timeline(user_id, tl["media_path"], tl["media_type"], tl["steps"])

def undo_timeline_step(user_id: int) -> Optional[str]:
    tl = get_timeline(user_id)
    if not tl["steps"]:
        return None
    removed = tl["steps"].pop()
    save_timeline(user_id, tl["media_path"], tl["media_type"], tl["steps"])
    return removed.get("step")

# ============================================================
# QUEUE SYSTEM
# ============================================================
class JobQueue:
    def __init__(self):
        self.queue = PriorityQueue()
        self.active_jobs: Dict[int, str] = {}

    def add_job(self, user_id: int, job_type: str, priority: int = 0):
        self.queue.put((priority, time.time(), user_id, job_type))

    def get_position(self, user_id: int) -> int:
        items = list(self.queue.queue)
        for i, item in enumerate(sorted(items)):
            if item[2] == user_id:
                return i + 1
        return 0

job_queue = JobQueue()

# ============================================================
# FFMPEG UTILITIES
# ============================================================
def check_ffmpeg() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def validate_video(path: str) -> bool:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "json", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False
        data = json.loads(result.stdout)
        return "format" in data and float(data["format"].get("duration", 0)) > 0
    except Exception:
        return False

def get_video_info(path: str) -> Dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", path],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout)
    except Exception:
        return {}

def run_ffmpeg(cmd: List[str], timeout: int = 300) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "FFmpeg operation timed out."
    except Exception as e:
        return False, str(e)

def ffmpeg_apply_video_filter(input_path: str, output_path: str, vf: str = None,
                               af: str = None, extra: List[str] = None,
                               timeout: int = 300) -> Tuple[bool, str]:
    """Apply FFmpeg video filter with fallback strategies."""
    # Strategy 1: Full with filters
    cmd = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd += ["-vf", vf]
    if af:
        cmd += ["-af", af]
    if extra:
        cmd += extra
    cmd += ["-c:a", "aac", output_path]

    ok, err = run_ffmpeg(cmd, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    # Strategy 2: Simple copy audio
    cmd2 = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd2 += ["-vf", vf]
    cmd2 += ["-c:a", "copy", output_path]
    ok, err = run_ffmpeg(cmd2, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    # Strategy 3: Stream copy
    cmd3 = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
    ok, err = run_ffmpeg(cmd3, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    return False, f"All strategies failed: {err}"

def temp_path(ext: str = "") -> str:
    name = "".join(random.choices(string.ascii_lowercase + string.digits, k=14))
    return os.path.join(TEMP_DIR, f"{name}{ext}")

def cleanup_temp_files(max_age: int = 3600):
    now = time.time()
    for f in Path(TEMP_DIR).iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > max_age:
            try:
                f.unlink()
            except Exception:
                pass

# ============================================================
# IMAGE FILTERS
# ============================================================
IMAGE_FILTERS = {
    # Basic
    "blur": "Blur",
    "sharpen": "Sharpen",
    "grayscale": "Grayscale",
    "sepia": "Sepia",
    "edge_enhance": "Edge Enhance",
    "contour": "Contour",
    "emboss": "Emboss",
    "smooth": "Smooth",
    "detail": "Detail",
    "gaussian_blur": "Gaussian Blur",
    "unsharp_mask": "Unsharp Mask",
    "median_filter": "Median Filter",
    # Artistic
    "oil_paint": "Oil Paint",
    "watercolor": "Watercolor",
    "sketch": "Sketch",
    "pencil_sketch": "Pencil Sketch",
    "cartoon": "Cartoon",
    "pixelate": "Pixelate",
    "glitch": "Glitch",
    "vintage": "Vintage",
    "neon": "Neon",
    "pointillism": "Pointillism",
    "mosaic": "Mosaic",
    "pastel": "Pastel",
    "comic": "Comic",
    "stained_glass": "Stained Glass",
    # Color
    "brightness": "Brightness+",
    "contrast": "Contrast+",
    "saturation": "Saturation+",
    "auto_color": "Auto Color",
    "equalize": "Equalize",
    "posterize": "Posterize",
    "solarize": "Solarize",
    "invert": "Invert",
    "golden_hour": "Golden Hour",
    "cold_tone": "Cold Tone",
    "warm_tone": "Warm Tone",
    "hue_shift": "Hue Shift",
    "temperature_warm": "Warm Temp",
    "temperature_cool": "Cool Temp",
    "channel_mixer": "Channel Mixer",
    "color_balance": "Color Balance",
    # Transform
    "rotate_90": "Rotate 90°",
    "rotate_180": "Rotate 180°",
    "rotate_270": "Rotate 270°",
    "flip_h": "Flip Horizontal",
    "flip_v": "Flip Vertical",
    "resize_50": "Resize 50%",
    "resize_200": "Resize 200%",
    "crop_center": "Crop Center",
    "mirror": "Mirror",
    "skew": "Skew",
    "perspective": "Perspective",
    # Special
    "vignette": "Vignette",
    "border": "Border",
    "rounded_corners": "Round Corners",
    "shadow": "Shadow",
    "glow": "Glow",
    "duotone": "Duotone",
    "sunset": "Sunset",
    "winter": "Winter",
    "autumn": "Autumn",
    "spring": "Spring",
    "night": "Night",
    "wave": "Wave",
    "firework": "Firework",
    "blur_background": "Blur BG",
    # Premium
    "hdr": "HDR Effect",
    "lomo": "Lomo",
    "cross_process": "Cross Process",
    "fade": "Fade",
    "matte": "Matte",
}

IMAGE_FILTER_CATEGORIES = {
    "🔧 Basic":    ["blur", "sharpen", "grayscale", "sepia", "edge_enhance", "contour",
                    "emboss", "smooth", "detail", "gaussian_blur", "unsharp_mask", "median_filter"],
    "🎨 Artistic": ["oil_paint", "watercolor", "sketch", "pencil_sketch", "cartoon",
                    "pixelate", "glitch", "vintage", "neon", "pointillism", "mosaic",
                    "pastel", "comic", "stained_glass"],
    "🌈 Color":    ["brightness", "contrast", "saturation", "auto_color", "equalize",
                    "posterize", "solarize", "invert", "golden_hour", "cold_tone",
                    "warm_tone", "hue_shift", "temperature_warm", "temperature_cool",
                    "channel_mixer", "color_balance"],
    "↔️ Transform":["rotate_90", "rotate_180", "rotate_270", "flip_h", "flip_v",
                    "resize_50", "resize_200", "crop_center", "mirror", "skew", "perspective"],
    "✨ Special":  ["vignette", "border", "rounded_corners", "shadow", "glow", "duotone",
                    "sunset", "winter", "autumn", "spring", "night", "wave", "firework",
                    "blur_background"],
    "⭐ Premium":  ["hdr", "lomo", "cross_process", "fade", "matte"],
}

PREMIUM_IMAGE_FILTERS = ["hdr", "lomo", "cross_process", "fade", "matte"]

def apply_image_filter(img: Image.Image, filter_name: str) -> Image.Image:
    """Apply a named filter to a PIL image."""
    if filter_name == "blur":
        return img.filter(ImageFilter.BLUR)
    elif filter_name == "sharpen":
        return img.filter(ImageFilter.SHARPEN)
    elif filter_name == "grayscale":
        return img.convert("L").convert("RGB")
    elif filter_name == "sepia":
        gray = img.convert("L")
        sepia = Image.new("RGB", img.size)
        px = list(gray.getdata())
        sepia.putdata([(min(int(p * 1.07), 255), int(p * 0.74), int(p * 0.43)) for p in px])
        return sepia
    elif filter_name == "edge_enhance":
        return img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    elif filter_name == "contour":
        return img.filter(ImageFilter.CONTOUR)
    elif filter_name == "emboss":
        return img.filter(ImageFilter.EMBOSS)
    elif filter_name == "smooth":
        return img.filter(ImageFilter.SMOOTH_MORE)
    elif filter_name == "detail":
        return img.filter(ImageFilter.DETAIL)
    elif filter_name == "gaussian_blur":
        return img.filter(ImageFilter.GaussianBlur(radius=3))
    elif filter_name == "unsharp_mask":
        return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    elif filter_name == "median_filter":
        return img.filter(ImageFilter.MedianFilter(size=3))
    elif filter_name == "oil_paint":
        blurred = img.filter(ImageFilter.GaussianBlur(2))
        enhanced = ImageEnhance.Color(blurred).enhance(1.8)
        return ImageEnhance.Contrast(enhanced).enhance(1.3)
    elif filter_name == "watercolor":
        soft = img.filter(ImageFilter.GaussianBlur(1))
        edges = img.filter(ImageFilter.FIND_EDGES)
        enhanced = ImageEnhance.Color(soft).enhance(1.5)
        return ImageChops.add(enhanced, edges)
    elif filter_name == "sketch":
        gray = img.convert("L")
        inv = ImageOps.invert(gray)
        blur = inv.filter(ImageFilter.GaussianBlur(15))
        sketch = ImageChops.divide(gray, ImageOps.invert(blur).point(lambda x: max(x, 1)))
        return sketch.convert("RGB")
    elif filter_name == "pencil_sketch":
        gray = img.convert("L")
        inv = ImageOps.invert(gray)
        blur = inv.filter(ImageFilter.GaussianBlur(21))
        blend = ImageChops.screen(gray, blur)
        return blend.convert("RGB")
    elif filter_name == "cartoon":
        smooth = img.filter(ImageFilter.SMOOTH_MORE)
        edges = img.filter(ImageFilter.FIND_EDGES).convert("L")
        edges = edges.point(lambda x: 255 if x > 30 else 0)
        edges_rgb = edges.convert("RGB")
        result = ImageChops.subtract(smooth, edges_rgb)
        return ImageEnhance.Color(result).enhance(2.0)
    elif filter_name == "pixelate":
        small = img.resize((img.width // 10, img.height // 10), Image.NEAREST)
        return small.resize(img.size, Image.NEAREST)
    elif filter_name == "glitch":
        result = img.copy()
        arr = list(result.getdata())
        offset = random.randint(5, 20)
        for i in range(0, len(arr), img.width * 5):
            for j in range(min(img.width, offset)):
                if i + j < len(arr) and i + j + offset < len(arr):
                    r, g, b = arr[i + j]
                    arr[i + j] = (min(r + 80, 255), g, b)
        result.putdata(arr)
        return result
    elif filter_name == "vintage":
        sepia = apply_image_filter(img, "sepia")
        return ImageEnhance.Contrast(sepia).enhance(0.8)
    elif filter_name == "neon":
        gray = img.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        neon = Image.new("RGB", img.size, (0, 0, 0))
        px = list(edges.getdata())
        neon.putdata([(0, min(p * 3, 255), min(p * 2, 255)) for p in px])
        return neon
    elif filter_name == "pointillism":
        result = img.copy()
        draw = ImageDraw.Draw(result)
        for _ in range(5000):
            x = random.randint(0, img.width - 1)
            y = random.randint(0, img.height - 1)
            r_val = random.randint(2, 6)
            color = img.getpixel((x, y))
            draw.ellipse([x - r_val, y - r_val, x + r_val, y + r_val], fill=color[:3])
        return result
    elif filter_name == "mosaic":
        block = 15
        result = img.copy()
        for x in range(0, img.width, block):
            for y in range(0, img.height, block):
                region = img.crop((x, y, min(x + block, img.width), min(y + block, img.height)))
                avg = region.resize((1, 1)).getpixel((0, 0))
                color = avg[:3] if len(avg) >= 3 else (avg[0], avg[0], avg[0])
                draw = ImageDraw.Draw(result)
                draw.rectangle([x, y, min(x + block, img.width), min(y + block, img.height)], fill=color)
        return result
    elif filter_name == "pastel":
        enhanced = ImageEnhance.Color(img).enhance(0.5)
        bright = ImageEnhance.Brightness(enhanced).enhance(1.2)
        return ImageEnhance.Contrast(bright).enhance(0.8)
    elif filter_name == "comic":
        cartoon = apply_image_filter(img, "cartoon")
        return ImageEnhance.Color(cartoon).enhance(2.5)
    elif filter_name == "stained_glass":
        mosaic = apply_image_filter(img, "mosaic")
        edges = img.filter(ImageFilter.FIND_EDGES)
        return ImageChops.add(mosaic, edges)
    elif filter_name == "brightness":
        return ImageEnhance.Brightness(img).enhance(1.5)
    elif filter_name == "contrast":
        return ImageEnhance.Contrast(img).enhance(1.5)
    elif filter_name == "saturation":
        return ImageEnhance.Color(img).enhance(1.8)
    elif filter_name == "auto_color":
        return ImageOps.autocontrast(img)
    elif filter_name == "equalize":
        return ImageOps.equalize(img.convert("RGB"))
    elif filter_name == "posterize":
        return ImageOps.posterize(img.convert("RGB"), 4)
    elif filter_name == "solarize":
        return ImageOps.solarize(img.convert("RGB"), threshold=128)
    elif filter_name == "invert":
        return ImageOps.invert(img.convert("RGB"))
    elif filter_name == "golden_hour":
        r, g, b = img.split()
        r = r.point(lambda x: min(x + 40, 255))
        g = g.point(lambda x: min(x + 10, 255))
        b = b.point(lambda x: max(x - 30, 0))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "cold_tone":
        r, g, b = img.split()
        r = r.point(lambda x: max(x - 30, 0))
        b = b.point(lambda x: min(x + 40, 255))
        return Image.merge("RGB", (r, g, b))
    elif filter_name in ("warm_tone", "temperature_warm"):
        return apply_image_filter(img, "golden_hour")
    elif filter_name in ("hue_shift", "temperature_cool"):
        return apply_image_filter(img, "cold_tone")
    elif filter_name == "channel_mixer":
        r, g, b = img.split()
        return Image.merge("RGB", (g, b, r))
    elif filter_name == "color_balance":
        return ImageEnhance.Color(img).enhance(1.4)
    elif filter_name == "rotate_90":
        return img.rotate(-90, expand=True)
    elif filter_name == "rotate_180":
        return img.rotate(180)
    elif filter_name == "rotate_270":
        return img.rotate(90, expand=True)
    elif filter_name == "flip_h":
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    elif filter_name == "flip_v":
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    elif filter_name == "resize_50":
        return img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    elif filter_name == "resize_200":
        return img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    elif filter_name == "crop_center":
        w, h = img.size
        s = min(w, h)
        left, top = (w - s) // 2, (h - s) // 2
        return img.crop((left, top, left + s, top + s))
    elif filter_name == "mirror":
        half = img.crop((0, 0, img.width // 2, img.height))
        mirror_half = half.transpose(Image.FLIP_LEFT_RIGHT)
        result = img.copy()
        result.paste(mirror_half, (img.width // 2, 0))
        return result
    elif filter_name == "skew":
        return img.transform(img.size, Image.AFFINE, (1, 0.3, 0, 0, 1, 0), Image.BICUBIC)
    elif filter_name == "perspective":
        w, h = img.size
        coeffs = (1, 0.1, -20, 0, 1.1, -20, 0.0003, 0.0001)
        return img.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    elif filter_name == "vignette":
        result = img.copy().convert("RGBA")
        vignette = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        cx, cy = img.width // 2, img.height // 2
        r = min(cx, cy)
        for i in range(r, 0, -1):
            alpha = int((1 - (i / r)) * 150)
            draw.ellipse([cx - i, cy - i, cx + i, cy + i], outline=(0, 0, 0, alpha))
        return Image.alpha_composite(result, vignette).convert("RGB")
    elif filter_name == "border":
        bordered = ImageOps.expand(img, border=20, fill=(255, 255, 255))
        return ImageOps.expand(bordered, border=5, fill=(0, 0, 0))
    elif filter_name == "rounded_corners":
        result = img.copy().convert("RGBA")
        mask = Image.new("L", img.size, 255)
        draw = ImageDraw.Draw(mask)
        radius = min(img.width, img.height) // 8
        draw.rectangle([radius, 0, img.width - radius, img.height], fill=255)
        draw.rectangle([0, radius, img.width, img.height - radius], fill=255)
        for corner in [(0, 0), (img.width - 2*radius, 0),
                       (0, img.height - 2*radius), (img.width - 2*radius, img.height - 2*radius)]:
            draw.ellipse([corner[0], corner[1], corner[0]+2*radius, corner[1]+2*radius], fill=255)
        result.putalpha(mask)
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(result, mask=result.split()[3])
        return bg
    elif filter_name == "shadow":
        shadow = Image.new("RGB", (img.width + 10, img.height + 10), (200, 200, 200))
        shadow.paste(img, (5, 5))
        return shadow
    elif filter_name == "glow":
        blur = img.filter(ImageFilter.GaussianBlur(5))
        return ImageChops.add(img, blur)
    elif filter_name == "duotone":
        gray = img.convert("L")
        result = Image.new("RGB", img.size)
        result.putdata([(min(p + 20, 255), p // 2, max(p - 30, 0)) for p in gray.getdata()])
        return result
    elif filter_name == "sunset":
        r, g, b = img.split()
        r = r.point(lambda x: min(x + 60, 255))
        g = g.point(lambda x: min(x + 20, 255))
        b = b.point(lambda x: max(x - 50, 0))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "winter":
        r, g, b = img.split()
        r = r.point(lambda x: max(x - 20, 0))
        b = b.point(lambda x: min(x + 60, 255))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "autumn":
        r, g, b = img.split()
        r = r.point(lambda x: min(x + 50, 255))
        b = b.point(lambda x: max(x - 40, 0))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "spring":
        enhanced = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = enhanced.split()
        g = g.point(lambda x: min(x + 30, 255))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "night":
        dark = ImageEnhance.Brightness(img).enhance(0.4)
        r, g, b = dark.split()
        b = b.point(lambda x: min(x + 30, 255))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "firework":
        result = img.copy()
        draw = ImageDraw.Draw(result)
        colors = [(255,0,0),(255,165,0),(255,255,0),(0,255,0),(0,0,255),(238,130,238)]
        for _ in range(8):
            cx = random.randint(0, img.width)
            cy = random.randint(0, img.height)
            color = random.choice(colors)
            for angle in range(0, 360, 20):
                length = random.randint(20, 60)
                ex = int(cx + length * math.cos(math.radians(angle)))
                ey = int(cy + length * math.sin(math.radians(angle)))
                draw.line([cx, cy, ex, ey], fill=color, width=2)
        return result
    elif filter_name == "wave":
        result = Image.new("RGB", img.size)
        for y in range(img.height):
            offset = int(10 * math.sin(y * 0.1))
            for x in range(img.width):
                src_x = (x + offset) % img.width
                result.putpixel((x, y), img.getpixel((src_x, y)))
        return result
    elif filter_name == "blur_background":
        blurred = img.filter(ImageFilter.GaussianBlur(8))
        cx, cy = img.width // 2, img.height // 2
        r = min(img.width, img.height) // 3
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        return Image.composite(img, blurred, mask)
    # Premium filters
    elif filter_name == "hdr":
        bright = ImageEnhance.Brightness(img).enhance(1.1)
        cont = ImageEnhance.Contrast(bright).enhance(1.4)
        return ImageEnhance.Color(cont).enhance(1.3)
    elif filter_name == "lomo":
        result = ImageEnhance.Contrast(img).enhance(1.5)
        result = apply_image_filter(result, "vignette")
        r, g, b = result.split()
        r = r.point(lambda x: min(x + 20, 255))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "cross_process":
        r, g, b = img.split()
        r = r.point(lambda x: int(min(x * 1.2, 255)))
        g = g.point(lambda x: int(max(x * 0.8, 0)))
        b = b.point(lambda x: int(min(x * 1.4, 255)))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "fade":
        faded = ImageEnhance.Contrast(img).enhance(0.6)
        return ImageEnhance.Brightness(faded).enhance(1.2)
    elif filter_name == "matte":
        result = ImageEnhance.Contrast(img).enhance(0.7)
        r, g, b = result.split()
        r = r.point(lambda x: min(x + 30, 255))
        g = g.point(lambda x: min(x + 20, 255))
        return Image.merge("RGB", (r, g, b))
    else:
        return img

def make_round_logo(size: int = 256) -> Image.Image:
    """Generate round KiraFx logo image."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Gradient background circle
    for i in range(size // 2, 0, -1):
        ratio = 1 - (i / (size // 2))
        r = int(75 + 100 * ratio)
        g = int(0 + 50 * ratio)
        b = int(130 + 100 * ratio)
        draw.ellipse(
            [size//2 - i, size//2 - i, size//2 + i, size//2 + i],
            fill=(r, g, b, 255)
        )
    # Border ring
    draw.ellipse([4, 4, size-4, size-4], outline=(200, 150, 255, 200), width=4)
    # Text
    try:
        font_size = size // 4
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size // 2)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font
    # KiraFx text
    bbox = draw.textbbox((0, 0), "Kira", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, size // 2 - th - 4), "Kira", font=font, fill=(255, 230, 255, 255))
    bbox2 = draw.textbbox((0, 0), "Fx", font=font)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((size - tw2) // 2, size // 2 + 4), "Fx", font=font, fill=(180, 100, 255, 255))
    return img

def add_watermark(img: Image.Image, text: str = "KiraFx") -> Image.Image:
    """Add round logo watermark to image."""
    result = img.copy().convert("RGBA")
    # Generate small round logo
    logo = make_round_logo(80)
    # Set transparency
    logo_rgba = logo.copy()
    pixels = logo_rgba.load()
    for y in range(logo_rgba.size[1]):
        for x in range(logo_rgba.size[0]):
            r, g, b, a = pixels[x, y]
            pixels[x, y] = (r, g, b, int(a * 0.6))
    # Paste at bottom-right
    margin = 10
    pos = (result.width - logo_rgba.width - margin, result.height - logo_rgba.height - margin)
    result.paste(logo_rgba, pos, logo_rgba)
    return result.convert("RGB")

# ============================================================
# VIDEO EFFECTS
# ============================================================
VIDEO_EFFECTS = {
    # Basic
    "trim": "Trim Video",
    "reverse": "Reverse",
    "loop": "Loop x2",
    "extract_gif": "Extract GIF",
    "change_resolution": "Change Res",
    "scale_square": "Scale Square",
    # Filters
    "bw_video": "Black & White",
    "sepia_video": "Sepia",
    "vintage_video": "Vintage",
    "cinematic": "Cinematic",
    "glitch_video": "Glitch",
    "pixelate_video": "Pixelate",
    "sketch_video": "Sketch",
    "cartoon_video": "Cartoon",
    "neon_video": "Neon",
    "sunset_video": "Sunset",
    "winter_video": "Winter",
    "vibrant": "Vibrant",
    "haze": "Haze",
    "vhs": "VHS Effect",
    "rgb_shift": "RGB Shift",
    "soft_glow": "Soft Glow",
    # Audio
    "mute_video": "Mute Audio",
    "extract_audio": "Extract Audio",
    "volume_up": "Volume Up",
    "volume_down": "Volume Down",
    "boost_bass": "Boost Bass",
    "echo": "Echo",
    "reverb": "Reverb",
    "normalize_audio": "Normalize Audio",
    "fade_audio": "Fade Audio",
    # Speed
    "speed_025": "0.25x Speed",
    "speed_05": "0.5x Speed",
    "speed_075": "0.75x Speed",
    "speed_15": "1.5x Speed",
    "speed_2": "2x Speed",
    "speed_3": "3x Speed",
    "speed_4": "4x Speed",
    # Transitions
    "fade_in": "Fade In",
    "fade_out": "Fade Out",
    # Advanced
    "rotate_video_90": "Rotate 90°",
    "crop_video": "Crop Center",
    "stabilize": "Stabilize",
    "denoise_video": "Denoise",
    "text_overlay": "Text Overlay",
    "watermark_video": "Add Watermark",
    "color_grading": "Color Grading",
    "face_blur": "Face Blur",
    "colorize_video": "Colorize",
    "chroma_key": "Chroma Key",
    "pip": "Picture in Picture",
}

VIDEO_EFFECT_CATEGORIES = {
    "🎬 Basic":     ["trim", "reverse", "loop", "extract_gif", "change_resolution", "scale_square"],
    "🎨 Filters":   ["bw_video", "sepia_video", "vintage_video", "cinematic", "glitch_video",
                     "pixelate_video", "sketch_video", "cartoon_video", "neon_video",
                     "sunset_video", "winter_video", "vibrant", "haze", "vhs", "rgb_shift", "soft_glow"],
    "🔊 Audio":     ["mute_video", "extract_audio", "volume_up", "volume_down",
                     "boost_bass", "echo", "reverb", "normalize_audio", "fade_audio"],
    "⚡ Speed":     ["speed_025", "speed_05", "speed_075", "speed_15", "speed_2", "speed_3", "speed_4"],
    "🎭 Transitions":["fade_in", "fade_out"],
    "🔧 Advanced":  ["rotate_video_90", "crop_video", "stabilize", "denoise_video",
                     "text_overlay", "watermark_video", "color_grading",
                     "face_blur", "colorize_video", "chroma_key", "pip"],
}

VIDEO_FILTER_MAP = {
    "bw_video":     "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
    "sepia_video":  "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "vintage_video":"curves=vintage,vignette=PI/4",
    "cinematic":    "curves=psych,vignette=PI/6",
    "glitch_video": "hue=h=random*360",
    "pixelate_video":"scale=iw/10:ih/10,scale=iw*10:ih*10:flags=neighbor",
    "sketch_video": "edgedetect=low=0.1:high=0.4,negate",
    "cartoon_video":"edgedetect=low=0.1:high=0.3",
    "neon_video":   "edgedetect,negate,colorchannelmixer=0:0:0:0:0:1:0:0:0:0:1:0",
    "sunset_video": "curves=r='0/0 0.5/0.8 1/1':g='0/0 0.5/0.6 1/0.8':b='0/0 0.5/0.3 1/0.6'",
    "winter_video": "curves=b='0/0 0.5/0.8 1/1':r='0/0 0.5/0.4 1/0.7'",
    "vibrant":      "hue=s=2,eq=contrast=1.2:saturation=1.5",
    "haze":         "curves=all='0/0 0.1/0.15 1/1'",
    "vhs":          "noise=alls=10:allf=t",
    "rgb_shift":    "chromashift=crh=3:crv=2",
    "soft_glow":    "gblur=sigma=5",
    "fade_in":      "fade=t=in:st=0:d=1",
    "fade_out":     "fade=t=out:st=0:d=1",
    "color_grading":"curves=r='0/0.1 0.5/0.5 1/0.9':g='0/0.05 0.5/0.5 1/0.95':b='0/0 0.5/0.4 1/0.8'",
    "colorize_video":"hue=h=220:s=2",
    "denoise_video":"hqdn3d=4:3:6:4.5",
    "stabilize":    "deshake",
    "crop_video":   "crop=iw/2:ih/2",
    "rotate_video_90":"transpose=1",
    "scale_square": "scale=720:720:force_original_aspect_ratio=decrease,pad=720:720:(ow-iw)/2:(oh-ih)/2",
}

VIDEO_SPEED_MAP = {
    "speed_025": 0.25, "speed_05": 0.5, "speed_075": 0.75,
    "speed_15": 1.5, "speed_2": 2.0, "speed_3": 3.0, "speed_4": 4.0,
}

def apply_video_effect(input_path: str, effect: str, output_path: str) -> Tuple[bool, str]:
    """Apply a named video effect."""
    if not validate_video(input_path):
        return False, "Invalid or corrupted video file."

    if effect in VIDEO_FILTER_MAP:
        vf = VIDEO_FILTER_MAP[effect]
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect in VIDEO_SPEED_MAP:
        speed = VIDEO_SPEED_MAP[effect]
        pts = 1.0 / speed
        atempo = speed
        if atempo < 0.5:
            af = f"atempo={atempo*2},atempo=0.5"
        elif atempo > 2.0:
            af = f"atempo=2.0,atempo={atempo/2}"
        else:
            af = f"atempo={atempo}"
        vf = f"setpts={pts}*PTS"
        return ffmpeg_apply_video_filter(input_path, output_path, vf, af)

    elif effect == "mute_video":
        cmd = ["ffmpeg", "-y", "-i", input_path, "-an", "-c:v", "copy", output_path]
        ok, err = run_ffmpeg(cmd)
        return (ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0), err

    elif effect == "extract_audio":
        out = output_path.replace(".mp4", ".mp3")
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "mp3", out]
        ok, err = run_ffmpeg(cmd)
        return (ok and os.path.exists(out) and os.path.getsize(out) > 0), err

    elif effect == "extract_gif":
        out = output_path.replace(".mp4", ".gif")
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", "fps=10,scale=480:-1:flags=lanczos",
               "-t", "5", out]
        ok, err = run_ffmpeg(cmd)
        return (ok and os.path.exists(out) and os.path.getsize(out) > 0), err

    elif effect == "reverse":
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", "reverse", "-af", "areverse", output_path]
        ok, err = run_ffmpeg(cmd)
        return (ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0), err

    elif effect == "loop":
        cmd = ["ffmpeg", "-y", "-stream_loop", "1", "-i", input_path, "-c", "copy", output_path]
        ok, err = run_ffmpeg(cmd)
        return (ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0), err

    elif effect == "volume_up":
        return ffmpeg_apply_video_filter(input_path, output_path, None, "volume=2.0")

    elif effect == "volume_down":
        return ffmpeg_apply_video_filter(input_path, output_path, None, "volume=0.5")

    elif effect == "boost_bass":
        return ffmpeg_apply_video_filter(input_path, output_path, None,
                                          "equalizer=f=60:width_type=o:width=2:g=5")

    elif effect == "echo":
        return ffmpeg_apply_video_filter(input_path, output_path, None, "aecho=0.8:0.88:60:0.4")

    elif effect == "reverb":
        return ffmpeg_apply_video_filter(input_path, output_path, None, "aecho=0.8:0.9:1000:0.3")

    elif effect == "normalize_audio":
        return ffmpeg_apply_video_filter(input_path, output_path, None, "loudnorm")

    elif effect == "fade_audio":
        info = get_video_info(input_path)
        try:
            duration = float(info.get("format", {}).get("duration", 10))
        except Exception:
            duration = 10
        af = f"afade=t=in:st=0:d=2,afade=t=out:st={max(duration-2, 0):.1f}:d=2"
        return ffmpeg_apply_video_filter(input_path, output_path, None, af)

    elif effect == "watermark_video":
        wm_text = get_setting("watermark_text", "KiraFx")
        vf = f"drawtext=text='{wm_text}':fontsize=24:fontcolor=white@0.5:x=10:y=10"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "text_overlay":
        vf = "drawtext=text='KiraFx Bot':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "face_blur":
        vf = "boxblur=20:1"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "chroma_key":
        vf = "chromakey=green:0.1:0.2"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "pip":
        vf = "split[a][b],[b]scale=iw/4:ih/4[small],[a][small]overlay=main_w-overlay_w-10:10"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "change_resolution":
        vf = "scale=1280:720:force_original_aspect_ratio=decrease"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    else:
        return False, f"Unknown effect: {effect}"

# ============================================================
# COMPRESSION PRESETS
# ============================================================
COMPRESSION_PRESETS = {
    "144p":  {"width": 256,  "height": 144,  "bitrate": "100k",   "audio_bitrate": "64k",  "crf": 35, "preset": "ultrafast"},
    "240p":  {"width": 426,  "height": 240,  "bitrate": "300k",   "audio_bitrate": "64k",  "crf": 32, "preset": "ultrafast"},
    "360p":  {"width": 640,  "height": 360,  "bitrate": "500k",   "audio_bitrate": "96k",  "crf": 28, "preset": "fast"},
    "480p":  {"width": 854,  "height": 480,  "bitrate": "800k",   "audio_bitrate": "128k", "crf": 25, "preset": "fast"},
    "720p":  {"width": 1280, "height": 720,  "bitrate": "1500k",  "audio_bitrate": "128k", "crf": 23, "preset": "medium"},
    "1080p": {"width": 1920, "height": 1080, "bitrate": "3000k",  "audio_bitrate": "192k", "crf": 20, "preset": "medium"},
    "1440p": {"width": 2560, "height": 1440, "bitrate": "6000k",  "audio_bitrate": "256k", "crf": 18, "preset": "slow"},
    "2K":    {"width": 2048, "height": 1080, "bitrate": "4000k",  "audio_bitrate": "256k", "crf": 18, "preset": "slow"},
    "4K":    {"width": 3840, "height": 2160, "bitrate": "12000k", "audio_bitrate": "320k", "crf": 15, "preset": "veryslow"},
}

PREMIUM_COMPRESS = ["1440p", "2K", "4K"]

def compress_video(input_path: str, output_path: str, quality: str, timeout: int = 300) -> Tuple[bool, str]:
    if not validate_video(input_path):
        return False, "Invalid or corrupted video file."
    preset_data = COMPRESSION_PRESETS.get(quality)
    if not preset_data:
        return False, f"Unknown quality preset: {quality}"
    w, h = preset_data["width"], preset_data["height"]
    vb, ab = preset_data["bitrate"], preset_data["audio_bitrate"]
    crf, speed = preset_data["crf"], preset_data["preset"]
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease",
        "-c:v", "libx264", "-crf", str(crf), "-preset", speed,
        "-b:v", vb, "-maxrate", vb, "-bufsize", str(int(vb[:-1]) * 2) + "k",
        "-c:a", "aac", "-b:a", ab,
        "-movflags", "+faststart", output_path
    ]
    ok, err = run_ffmpeg(cmd, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""
    cmd2 = ["ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale={w}:{h}", "-c:v", "libx264", "-crf", str(crf), "-c:a", "aac", output_path]
    ok, err = run_ffmpeg(cmd2, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""
    return False, err

# ============================================================
# LOGO MAKER
# ============================================================
LOGO_STYLES = {
    "gradient": [(75, 0, 130), (238, 130, 238)],
    "gold":     [(184, 134, 11), (255, 215, 0)],
    "neon":     [(0, 255, 0), (0, 200, 255)],
    "fire":     [(255, 69, 0), (255, 165, 0)],
    "ice":      [(135, 206, 235), (255, 255, 255)],
    "purple":   [(75, 0, 130), (148, 0, 211)],
    "pink":     [(255, 20, 147), (255, 182, 193)],
    "rainbow":  [(255, 0, 0), (0, 0, 255)],
}

LOGO_BACKGROUNDS = {
    "dark":   (20, 20, 30),
    "light":  (240, 240, 255),
    "black":  (0, 0, 0),
    "purple": (30, 0, 60),
    "blue":   (0, 20, 60),
    "neon":   (0, 10, 0),
    "gold":   (30, 20, 0),
}

def make_logo(text: str, style: str = "gradient", bg: str = "dark") -> Image.Image:
    """Generate a stylized logo image."""
    width, height = 800, 300
    bg_color = LOGO_BACKGROUNDS.get(bg, (20, 20, 30))
    colors = LOGO_STYLES.get(style, [(75, 0, 130), (238, 130, 238)])

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw gradient bar at bottom
    for x in range(width):
        ratio = x / width
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.line([(x, height - 40), (x, height - 5)], fill=(r, g, b))

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    bbox = draw.textbbox((0, 0), text, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = (height - th) // 2 - 20

    draw.text((tx + 3, ty + 3), text, font=font_large, fill=(0, 0, 0))
    main_color = tuple(min(c + 100, 255) for c in colors[1])
    draw.text((tx, ty), text, font=font_large, fill=main_color)

    # Add round logo watermark
    logo = make_round_logo(50)
    img_rgba = img.convert("RGBA")
    img_rgba.paste(logo, (10, 10), logo)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((68, 20), "KiraFx Bot v7.0", font=font_small, fill=tuple(colors[1]))

    return img

# ============================================================
# WELCOME IMAGE (Round KiraFx Logo)
# ============================================================
def make_welcome_image(user_name: str, is_prem: bool = False) -> Image.Image:
    """Create a welcome image for new users with round KiraFx logo."""
    width, height = 900, 450
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(10 + 20 * ratio)
        g = int(5 + 10 * ratio)
        b = int(40 + 60 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative circles
    for i in range(6):
        cx = random.randint(50, width - 50)
        cy = random.randint(30, height - 30)
        r_val = random.randint(20, 100)
        alpha_color = (80, 40, 160)
        draw.ellipse([cx - r_val, cy - r_val, cx + r_val, cy + r_val],
                      outline=alpha_color, width=1)

    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
        font_xs = font_lg

    # Round KiraFx logo on left
    logo = make_round_logo(120)
    logo_x, logo_y = 30, (height - 120) // 2
    img_rgba = img.convert("RGBA")
    img_rgba.paste(logo, (logo_x, logo_y), logo)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Welcome text right of logo
    text_x = logo_x + 120 + 25
    name_text = f"Welcome, {user_name[:20]}!"
    bbox = draw.textbbox((0, 0), name_text, font=font_lg)
    draw.text((text_x + 2, 72), name_text, font=font_lg, fill=(0, 0, 0))
    draw.text((text_x, 70), name_text, font=font_lg, fill=(200, 160, 255))

    # Bot name
    bot_text = f"✨ {BOT_NAME}"
    draw.text((text_x, 135), bot_text, font=font_md, fill=(255, 200, 100))

    # Status badge
    if is_prem:
        draw.text((text_x, 178), "⭐ PREMIUM USER", font=font_sm, fill=(255, 215, 0))
    else:
        draw.text((text_x, 178), "🆓 FREE USER  |  Use /trial for 7 days free!", font=font_sm, fill=(150, 255, 150))

    # Feature badges
    features = [
        ("📷", "70+ Filters"), ("🎬", "77+ Effects"), ("✏️", "File Rename"),
        ("🗜️", "Compress"), ("🤖", "AI Gen"), ("🎨", "Logo Maker"),
        ("📊", "Timeline"), ("⭐", "Premium"), ("👑", "Admin"),
    ]
    badge_x, badge_y = text_x, 220
    for emoji, label in features:
        feat = f"{emoji} {label}"
        bbox3 = draw.textbbox((0, 0), feat, font=font_xs)
        fw = bbox3[2] - bbox3[0]
        draw.rounded_rectangle([badge_x - 5, badge_y - 3, badge_x + fw + 8, badge_y + 20],
                                 radius=6, fill=(50, 25, 100))
        draw.text((badge_x, badge_y), feat, font=font_xs, fill=(210, 180, 255))
        badge_x += fw + 20
        if badge_x > width - 120:
            badge_x = text_x
            badge_y += 32

    # Bottom brand bar
    draw.rectangle([0, height - 35, width, height], fill=(20, 10, 50))
    draw.text((15, height - 27), f"KiraFx Bot v{BOT_VERSION}  •  /help to get started",
               font=font_xs, fill=(120, 100, 200))
    draw.text((width - 200, height - 27), "Always Alive 🟢", font=font_xs, fill=(100, 255, 100))

    return img

# ============================================================
# PROFILE CARD GENERATION
# ============================================================
def make_profile_card(user_row: sqlite3.Row, is_prem: bool, is_adm: bool) -> Image.Image:
    """Generate a rich profile card with round KiraFx logo."""
    width, height = 700, 350
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(height):
        ratio = y / height
        r = int(15 + 10 * ratio)
        g = int(10 + 5 * ratio)
        b = int(35 + 30 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
        font_xs = font_lg

    # Round logo as avatar on left
    logo = make_round_logo(100)
    img_rgba = img.convert("RGBA")
    img_rgba.paste(logo, (25, (height - 100) // 2), logo)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # User info
    tx = 145
    name = f"{user_row['first_name']} {user_row['last_name'] or ''}".strip()
    draw.text((tx, 40), name[:28], font=font_lg, fill=(210, 180, 255))

    uname = f"@{user_row['username'] or 'N/A'}"
    draw.text((tx, 85), uname, font=font_md, fill=(150, 130, 200))

    # ID
    uid_text = f"ID: {user_row['user_id']}"
    draw.text((tx, 118), uid_text, font=font_sm, fill=(120, 110, 180))

    # Status badge
    if is_adm:
        status_color, status_text = (255, 200, 0), "👑 ADMIN"
    elif is_prem:
        status_color, status_text = (255, 215, 0), "⭐ PREMIUM"
    else:
        status_color, status_text = (100, 255, 100), "🆓 FREE"
    draw.text((tx, 148), status_text, font=font_md, fill=status_color)

    # Stats grid
    stats = [
        ("Total Edits",  str(user_row["total_edits"])),
        ("Renames",      str(user_row["total_renames"])),
        ("🪙 Coins",    str(user_row["coins"])),
        ("Referrals",    str(user_row["referral_count"])),
        ("Ref Code",     str(user_row["referral_code"] or "N/A")),
        ("Joined",       str(user_row["joined_at"])[:10]),
    ]
    col_x, row_y = tx, 195
    for i, (label, val) in enumerate(stats):
        col = i % 3
        row = i // 3
        sx = col_x + col * 185
        sy = row_y + row * 40
        draw.text((sx, sy), label, font=font_xs, fill=(120, 110, 180))
        draw.text((sx, sy + 16), val, font=font_sm, fill=(200, 180, 255))

    # Bottom bar
    draw.rectangle([0, height - 30, width, height], fill=(15, 8, 40))
    draw.text((15, height - 22), f"KiraFx Bot v{BOT_VERSION}", font=font_xs, fill=(100, 80, 180))

    return img

# ============================================================
# TEXT TO IMAGE GENERATION
# ============================================================
AI_TEXT_IMAGE_STYLES = {
    "gradient": {"bg": (20, 20, 40),  "colors": [(100, 50, 255), (255, 50, 200)]},
    "neon":     {"bg": (0, 5, 15),    "colors": [(0, 255, 200), (0, 150, 255)]},
    "gold":     {"bg": (10, 5, 0),    "colors": [(255, 200, 0), (200, 150, 0)]},
    "dark":     {"bg": (10, 10, 10),  "colors": [(180, 180, 200), (100, 100, 150)]},
    "fire":     {"bg": (10, 0, 0),    "colors": [(255, 100, 0), (255, 200, 0)]},
    "ocean":    {"bg": (0, 10, 30),   "colors": [(0, 150, 255), (0, 255, 200)]},
}

def text_to_image(prompt: str, style: str = "gradient") -> Image.Image:
    width, height = 800, 600
    style_data = AI_TEXT_IMAGE_STYLES.get(style, AI_TEXT_IMAGE_STYLES["gradient"])
    bg = style_data["bg"]
    colors = style_data["colors"]

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(bg[0] + (colors[0][0] - bg[0]) * ratio * 0.5)
        g = int(bg[1] + (colors[0][1] - bg[1]) * ratio * 0.5)
        b = int(bg[2] + (colors[0][2] - bg[2]) * ratio * 0.5)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    for _ in range(25):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r_val = random.randint(2, 10)
        color = random.choice(colors)
        draw.ellipse([x - r_val, y - r_val, x + r_val, y + r_val], fill=(*color, 150))

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
        font_small = font

    words = prompt.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > width - 60:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    total_h = len(lines) * 48
    start_y = (height - total_h) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lx = (width - lw) // 2
        draw.text((lx + 2, start_y + i * 48 + 2), line, font=font, fill=(0, 0, 0))
        draw.text((lx, start_y + i * 48), line, font=font, fill=colors[0])

    # Round logo watermark
    logo = make_round_logo(50)
    img_rgba = img.convert("RGBA")
    logo_x = 10
    logo_y = height - 60
    img_rgba.paste(logo, (logo_x, logo_y), logo)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((68, height - 45), f"KiraFx AI • {style.upper()}", font=font_small, fill=colors[1])

    return img

# ============================================================
# KEYBOARDS – Main Menu & Submenus
# ============================================================
def main_menu_keyboard(user_id: int = 0):
    buttons = [
        [InlineKeyboardButton("📷 Image Filters", callback_data="menu_image"),
         InlineKeyboardButton("🎬 Video Effects", callback_data="menu_video")],
        [InlineKeyboardButton("📊 Timeline Edit", callback_data="menu_timeline"),
         InlineKeyboardButton("🗜️ Compress", callback_data="menu_compress")],
        [InlineKeyboardButton("✏️ Rename File", callback_data="menu_rename"),
         InlineKeyboardButton("📝 Metadata", callback_data="menu_metadata")],
        [InlineKeyboardButton("🤖 AI Generate", callback_data="menu_ai"),
         InlineKeyboardButton("🎨 Logo Maker", callback_data="menu_logo")],
        [InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
         InlineKeyboardButton("👤 My Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="menu_refer"),
         InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")],
    ]
    if user_id and is_admin(user_id):
        buttons.append([InlineKeyboardButton("🔑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def back_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

def image_category_keyboard():
    cats = list(IMAGE_FILTER_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"imgcat_{cat}")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def image_filter_keyboard(category: str, page: int = 0):
    filters_list = IMAGE_FILTER_CATEGORIES.get(category, [])
    per_page = 8
    start = page * per_page
    end = start + per_page
    chunk = filters_list[start:end]

    buttons = []
    row = []
    for f in chunk:
        name = IMAGE_FILTERS.get(f, f)
        if f in PREMIUM_IMAGE_FILTERS:
            name = "⭐ " + name
        row.append(InlineKeyboardButton(name, callback_data=f"imgfilter_{f}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"imgpage_{category}_{page-1}"))
    if end < len(filters_list):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"imgpage_{category}_{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("🔙 Categories", callback_data="menu_image"),
        InlineKeyboardButton("🏠 Home", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(buttons)

def video_category_keyboard():
    cats = list(VIDEO_EFFECT_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"vidcat_{cat}")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def video_effect_keyboard(category: str, page: int = 0):
    effects_list = VIDEO_EFFECT_CATEGORIES.get(category, [])
    per_page = 8
    start = page * per_page
    end = start + per_page
    chunk = effects_list[start:end]

    buttons = []
    row = []
    for e in chunk:
        name = VIDEO_EFFECTS.get(e, e)
        row.append(InlineKeyboardButton(name, callback_data=f"videffect_{e}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"vidpage_{category}_{page-1}"))
    if end < len(effects_list):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"vidpage_{category}_{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("🔙 Categories", callback_data="menu_video"),
        InlineKeyboardButton("🏠 Home", callback_data="menu_main"),
    ])
    return InlineKeyboardMarkup(buttons)

def compress_keyboard():
    buttons = []
    row = []
    for quality in COMPRESSION_PRESETS.keys():
        label = quality
        if quality in PREMIUM_COMPRESS:
            label = f"⭐ {quality}"
        row.append(InlineKeyboardButton(label, callback_data=f"compress_{quality}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def premium_plans_keyboard():
    buttons = []
    for plan_key, plan in PREMIUM_PLANS.items():
        label = f"{plan['emoji']} {plan['label']} — {plan['price']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"buyprem_{plan_key}")])
    buttons.extend([
        [InlineKeyboardButton("🎁 Free 7-Day Trial", callback_data="trial"),
         InlineKeyboardButton("🔗 Refer & Earn", callback_data="menu_refer")],
        [InlineKeyboardButton("📩 Contact Admin", callback_data="contact_admin"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])
    return InlineKeyboardMarkup(buttons)

def timeline_keyboard(user_id: int):
    tl = get_timeline(user_id)
    steps = tl["steps"]
    has_media = bool(tl["media_path"] and os.path.exists(tl.get("media_path", "") or ""))
    media_type = tl.get("media_type", "image")

    buttons = []
    if has_media:
        if media_type == "image":
            buttons.append([
                InlineKeyboardButton("🎨 Add Image Filter", callback_data="tl_add_imgfilter"),
                InlineKeyboardButton("✨ Add Special FX", callback_data="tl_add_special"),
            ])
        else:
            buttons.append([
                InlineKeyboardButton("🎬 Add Video Effect", callback_data="tl_add_videffect"),
                InlineKeyboardButton("⚡ Change Speed", callback_data="tl_add_speed"),
            ])
        buttons.append([
            InlineKeyboardButton("▶️ Apply All", callback_data="tl_apply"),
            InlineKeyboardButton("↩️ Undo Last", callback_data="tl_undo"),
        ])
        buttons.append([
            InlineKeyboardButton("📋 View Steps", callback_data="tl_view"),
            InlineKeyboardButton("🗑️ Clear All", callback_data="tl_clear"),
        ])
        buttons.append([
            InlineKeyboardButton("💾 Export Result", callback_data="tl_export"),
        ])
    else:
        buttons.append([InlineKeyboardButton("📤 Send Media First", callback_data="cancel")])

    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def logo_style_keyboard():
    buttons = []
    row = []
    for style in LOGO_STYLES.keys():
        row.append(InlineKeyboardButton(style.title(), callback_data=f"logo_style_{style}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def logo_bg_keyboard(style: str):
    buttons = []
    row = []
    for bg in LOGO_BACKGROUNDS.keys():
        row.append(InlineKeyboardButton(bg.title(), callback_data=f"logo_bg_{style}_{bg}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Styles", callback_data="menu_logo"),
                    InlineKeyboardButton("🏠 Home", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def ai_gen_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Text to Image", callback_data="ai_txt2img"),
         InlineKeyboardButton("🎬 Text to Video", callback_data="ai_txt2vid")],
        [InlineKeyboardButton("🤖 AI Edit Prompt", callback_data="ai_edit"),
         InlineKeyboardButton("🎨 Style Transfer", callback_data="ai_style")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

def upload_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 As Document", callback_data="upload_doc"),
         InlineKeyboardButton("🎬 As Video", callback_data="upload_vid")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])

def after_edit_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Apply Another Filter", callback_data="menu_image"),
         InlineKeyboardButton("📊 Timeline", callback_data="menu_timeline")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

def after_video_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Apply Another Effect", callback_data="menu_video"),
         InlineKeyboardButton("📊 Timeline", callback_data="menu_timeline")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

# ============================================================
# ADMIN PANEL – 50+ FEATURES
# ============================================================
def admin_panel_keyboard():
    """Main admin panel – 70+ features, admin only."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Full Stats", callback_data="admin_stats"),
         InlineKeyboardButton("👥 Users List", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_menu"),
         InlineKeyboardButton("💾 Backup DB", callback_data="admin_backup")],
        [InlineKeyboardButton("📋 View Logs", callback_data="admin_logs"),
         InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance"),
         InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup")],
        [InlineKeyboardButton("💎 Premium Mgmt", callback_data="admin_premium_menu"),
         InlineKeyboardButton("🚫 Ban Manager", callback_data="admin_ban_menu")],
        [InlineKeyboardButton("📝 Custom Cmds", callback_data="admin_custom_cmds"),
         InlineKeyboardButton("🤖 Auto Replies", callback_data="admin_auto_replies")],
        [InlineKeyboardButton("💰 Coins Mgmt", callback_data="admin_coins_menu"),
         InlineKeyboardButton("👑 Admin Mgmt", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("📤 Export Config", callback_data="admin_export"),
         InlineKeyboardButton("📊 Edit Stats", callback_data="admin_edit_stats")],
        [InlineKeyboardButton("📡 Ads Manager", callback_data="admin_ads_menu"),
         InlineKeyboardButton("🔔 Notifications", callback_data="admin_notifications")],
        [InlineKeyboardButton("💻 Run Code", callback_data="admin_run_code"),
         InlineKeyboardButton("📋 Bot Notes", callback_data="admin_notes")],
        [InlineKeyboardButton("🔗 Generate Links", callback_data="admin_gen_links"),
         InlineKeyboardButton("📈 Growth Stats", callback_data="admin_growth")],
        [InlineKeyboardButton("🗂️ Queue Status", callback_data="admin_queue"),
         InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
        [InlineKeyboardButton("🏆 Top Users", callback_data="admin_top_users"),
         InlineKeyboardButton("🟢 Active Users", callback_data="admin_active_users")],
        [InlineKeyboardButton("💽 Disk Usage", callback_data="admin_disk_usage"),
         InlineKeyboardButton("🗃️ DB Stats", callback_data="admin_db_stats")],
        [InlineKeyboardButton("⚠️ Warnings", callback_data="admin_warnings_menu"),
         InlineKeyboardButton("🔇 Mute Manager", callback_data="admin_mute_menu")],
        [InlineKeyboardButton("🏅 Coin Leaders", callback_data="admin_coin_leader"),
         InlineKeyboardButton("📉 User Analytics", callback_data="admin_analytics")],
        [InlineKeyboardButton("🚀 Deploy Status", callback_data="admin_deploy_status"),
         InlineKeyboardButton("🔐 Security Info", callback_data="admin_security")],
        [InlineKeyboardButton("📦 Session Info", callback_data="admin_sessions"),
         InlineKeyboardButton("🎯 Filter Stats", callback_data="admin_filter_stats")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

def admin_settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖊️ Set Watermark", callback_data="aset_watermark"),
         InlineKeyboardButton("🔢 Set Free Edits", callback_data="aset_free_edits")],
        [InlineKeyboardButton("📢 Set Welcome Msg", callback_data="aset_welcome"),
         InlineKeyboardButton("📡 Toggle Ads", callback_data="aset_toggle_ads")],
        [InlineKeyboardButton("👥 Group Mode", callback_data="aset_group_mode"),
         InlineKeyboardButton("📊 Max File Size", callback_data="aset_file_size")],
        [InlineKeyboardButton("🔗 Support User", callback_data="aset_support"),
         InlineKeyboardButton("📣 Channel Link", callback_data="aset_channel")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
    ])

def admin_premium_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Premium", callback_data="aprem_add"),
         InlineKeyboardButton("➖ Remove Premium", callback_data="aprem_remove")],
        [InlineKeyboardButton("📋 List Premium Users", callback_data="aprem_list"),
         InlineKeyboardButton("⏱️ Expiring Soon", callback_data="aprem_expiring")],
        [InlineKeyboardButton("📊 Premium Stats", callback_data="aprem_stats"),
         InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
    ])

# ============================================================
# DECORATORS
# ============================================================
def require_registered(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user = message.from_user
        if not user:
            return
        register_user(user)
        if is_banned(user.id):
            await message.reply("🚫 You are banned from using this bot.")
            return
        if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
            await message.reply(
                "🔧 **Maintenance Mode**\n\nBot is under maintenance. Please try again soon.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📩 Contact Support", callback_data="contact_admin")
                ]])
            )
            return
        mute_row = get_db().execute("SELECT is_muted, muted_until FROM users WHERE user_id=?", (user.id,)).fetchone()
        if mute_row and mute_row["is_muted"]:
            if mute_row["muted_until"]:
                from datetime import datetime as _dt
                try:
                    if _dt.fromisoformat(mute_row["muted_until"]) < _dt.now():
                        get_db().execute("UPDATE users SET is_muted=0, muted_until=NULL WHERE user_id=?", (user.id,))
                        get_db().commit()
                    else:
                        await message.reply(f"🔇 You are muted until {str(mute_row['muted_until'])[:16]}.")
                        return
                except Exception:
                    pass
            else:
                await message.reply("🔇 You are muted by an admin.")
                return
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply("🚫 **Admin Only**\n\nThis command is restricted to admins.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_premium(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not is_premium(message.from_user.id):
            await message.reply(
                "⭐ **Premium Required**\n\nThis feature requires a premium subscription.\n\n"
                "Use /premium to see plans or /trial for a 7-day free trial!",
                reply_markup=premium_plans_keyboard()
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

# ============================================================
# PYROGRAM BOT APP
# ============================================================
app = Client(
    "kiraFx_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ============================================================
# COMMAND HANDLERS
# ============================================================

@app.on_message(filters.command("start"))
@require_registered
async def cmd_start(client, message: Message):
    user = message.from_user
    args = message.text.split()
    referred_by = None

    # Handle referral
    if len(args) > 1:
        ref_arg = args[1]
        try:
            referrer_id = int(ref_arg)
            if referrer_id != user.id:
                referred_by = referrer_id
                referrer = get_user(referrer_id)
                if referrer:
                    db = get_db()
                    db.execute(
                        "UPDATE users SET referral_count=referral_count+1, coins=coins+? WHERE user_id=?",
                        (int(get_setting("referral_coins", "100")), referrer_id)
                    )
                    db.commit()
                    ref_days = int(get_setting("referral_premium_days", "3"))
                    add_premium(referrer_id, ref_days, "referral")
                    try:
                        await client.send_message(
                            referrer_id,
                            f"🎉 **Referral Reward!**\n\nSomeone joined using your link!\n"
                            f"✅ **+{ref_days} days Premium** added!\n"
                            f"✅ **+{get_setting('referral_coins', '100')} Coins** added!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass
        register_user(user, referred_by)

    prem = is_premium(user.id)

    # Generate welcome image
    try:
        welcome_img = make_welcome_image(user.first_name or "Friend", prem)
        bio = BytesIO()
        bio.name = "welcome.png"
        welcome_img.save(bio, "PNG")
        bio.seek(0)

        free_left = get_remaining_edits(user.id)
        caption = (
            f"👋 **Welcome to {BOT_NAME}!**\n\n"
            f"🎯 Your all-in-one Telegram media editor.\n\n"
            f"📷 **70+ Image Filters** across 6 categories\n"
            f"🎬 **77+ Video Effects** with timeline editing\n"
            f"📊 **Timeline Editor** – layer multiple effects\n"
            f"🗜️ **9 Compression Presets** (144p to 4K)\n"
            f"✏️ **File Rename & Metadata** editing\n"
            f"🤖 **AI Generation** – images & videos\n"
            f"🎨 **Logo Maker** – 7 styles & 7 backgrounds\n"
            f"⭐ **Premium Plans** – unlimited everything\n\n"
            f"{'🟢 **Premium:** Active' if prem else f'🔵 **Free Edits Left Today:** {free_left}'}\n\n"
            f"📌 Use /help for the full guide or tap below!"
        )

        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=caption,
            reply_markup=main_menu_keyboard(user.id)
        )
    except Exception as e:
        logger.error(f"Welcome image error: {e}\n{traceback.format_exc()}")
        await message.reply(
            f"👋 **Welcome to {BOT_NAME}!**\n\nTap the menu below to start editing!",
            reply_markup=main_menu_keyboard(user.id)
        )

@app.on_message(filters.command("help"))
@require_registered
async def cmd_help(client, message: Message):
    text = (
        f"📖 **{BOT_NAME} — Help Guide**\n\n"
        "**📷 Image Editing:**\n"
        "Send any photo → Choose category → Select filter\n"
        "Supports: 70+ filters in 6 categories\n\n"
        "**🎬 Video Editing:**\n"
        "Send any video → Choose effect category → Select effect\n"
        "Supports: 77+ effects in 6 categories\n\n"
        "**📊 Timeline Editing:**\n"
        "Use /timeline → Send media → Add layers step by step\n\n"
        "**✏️ Rename Files:**\n"
        "Use /rename → Send file → Type new name\n\n"
        "**📝 Metadata Edit:**\n"
        "Use /metadata → Send media → Edit fields\n\n"
        "**🗜️ Compress Video:**\n"
        "Use /compress → Send video → Choose quality (144p–4K)\n\n"
        "**🤖 AI Features:**\n"
        "• /txt2img [prompt] — Generate image\n"
        "• /txt2vid [prompt] — Generate video animation\n"
        "• /aiedit [prompt] — AI-guided filter selection\n\n"
        "**Other Commands:**\n"
        "• /logo — Logo maker with 7 styles\n"
        "• /premium — View plans & benefits\n"
        "• /trial — Claim 7-day free premium\n"
        "• /status — Your daily edit status\n"
        "• /profile — Your full profile card\n"
        "• /refer — Referral link & rewards\n"
        "• /ping — Bot ping check\n"
        "• /alive — Bot uptime & status\n"
        "• /timeline — Open timeline editor\n"
        "• /info — Bot information\n"
        "• /queue — Your queue position\n\n"
        "**Admin Commands:** /admin (admin only)\n"
    )
    await message.reply(text, reply_markup=main_menu_keyboard(message.from_user.id))

@app.on_message(filters.command("premium"))
@require_registered
async def cmd_premium(client, message: Message):
    user_id = message.from_user.id
    if is_premium(user_id):
        row = get_user(user_id)
        until = row["premium_until"] or "Lifetime"
        plan = row["premium_plan"] or "premium"
        await message.reply(
            f"⭐ **You are a Premium User!**\n\n"
            f"**Plan:** {plan.title()}\n"
            f"**Valid until:** `{until[:10] if len(str(until)) >= 10 else until}`\n\n"
            f"**Your Premium Benefits:**\n"
            f"✅ Unlimited daily edits\n"
            f"✅ No watermarks on outputs\n"
            f"✅ No ads shown\n"
            f"✅ Priority processing queue\n"
            f"✅ 1440p, 2K, 4K compression\n"
            f"✅ Extended processing timeout (600s)\n"
            f"✅ Exclusive premium image filters\n"
            f"✅ AI generation priority\n"
            f"✅ Timeline multi-layer editing\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Refer & Earn", callback_data="menu_refer")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
            ])
        )
    else:
        await message.reply(
            f"⭐ **KiraFx Premium Plans**\n\n"
            + "\n".join(
                f"{p['emoji']} **{p['label']}** — {p['price']}"
                for p in PREMIUM_PLANS.values()
            ) +
            f"\n\n**Premium Benefits:**\n"
            f"✅ Unlimited daily edits\n"
            f"✅ No watermarks • No ads\n"
            f"✅ Priority queue\n"
            f"✅ 4K compression\n"
            f"✅ Exclusive filters\n"
            f"✅ Extended processing (600s)\n\n"
            f"📩 Contact admin to purchase.",
            reply_markup=premium_plans_keyboard()
        )

@app.on_message(filters.command("trial"))
@require_registered
async def cmd_trial(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if row["trial_used"]:
        await message.reply(
            "❌ **Trial Already Used**\n\nYou have already used your free trial.\n\n"
            "Check our premium plans to continue enjoying unlimited features!",
            reply_markup=premium_plans_keyboard()
        )
        return
    if is_premium(user_id):
        await message.reply("✅ You already have premium access!")
        return
    trial_days = int(get_setting("trial_days", "7"))
    add_premium(user_id, trial_days, "trial")
    get_db().execute("UPDATE users SET trial_used=1 WHERE user_id=?", (user_id,))
    get_db().commit()
    await message.reply(
        f"🎉 **{trial_days}-Day Free Trial Activated!**\n\n"
        f"You now have full premium access for {trial_days} days!\n\n"
        f"✅ Unlimited edits per day\n"
        f"✅ No watermarks on exports\n"
        f"✅ No ads\n"
        f"✅ Priority processing queue\n"
        f"✅ 4K compression unlocked\n\n"
        f"Enjoy KiraFx Premium! ⭐",
        reply_markup=main_menu_keyboard(user_id)
    )

@app.on_message(filters.command("status"))
@require_registered
async def cmd_status(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found.")
        return
    prem = "⭐ Premium" if is_premium(user_id) else "🆓 Free"
    admin_title = row["admin_title"] if row["admin_title"] else "Admin"
    admin_str = f" | 👑 {admin_title}" if is_admin(user_id) else ""
    free_left = get_remaining_edits(user_id)
    limit = "∞" if is_premium(user_id) else get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
    await message.reply(
        f"📊 **Your Status**\n\n"
        f"**Tier:** {prem}{admin_str}\n"
        f"**Edits Left Today:** {free_left} / {limit}\n"
        f"**Total Edits:** {row['total_edits']}\n"
        f"**Total Renames:** {row['total_renames']}\n"
        f"**🪙 Coins:** {row['coins']}\n"
        f"**Referrals:** {row['referral_count']}\n"
        f"**Trial Used:** {'Yes' if row['trial_used'] else 'No'}\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Full Profile", callback_data="menu_profile"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        ])
    )

@app.on_message(filters.command("profile"))
@require_registered
async def cmd_profile(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found.")
        return
    try:
        card = make_profile_card(row, is_premium(user_id), is_admin(user_id))
        bio = BytesIO()
        bio.name = "profile.png"
        card.save(bio, "PNG")
        bio.seek(0)
        prem_plan = (row["premium_plan"] or "N/A") if row["premium_plan"] is not None else "N/A"
        prem_until = str(row["premium_until"] or "N/A")[:10] if row["premium_until"] is not None else "N/A"
        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=(
                f"👤 **Your Profile**\n\n"
                f"**Name:** {row['first_name']} {row['last_name'] or ''}\n"
                f"**Username:** @{row['username'] or 'N/A'}\n"
                f"**ID:** `{user_id}`\n"
                f"**Status:** {'⭐ Premium' if is_premium(user_id) else '🆓 Free'}\n"
                f"**Plan:** {prem_plan.title()}\n"
                f"**Valid Until:** {prem_until}\n"
                f"**Edits:** {row['total_edits']} total\n"
                f"**Coins:** 🪙 {row['coins']}\n"
                f"**Referral Code:** `{row['referral_code']}`\n"
                f"**Joined:** {str(row['joined_at'])[:10]}\n"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Get Premium", callback_data="menu_premium"),
                 InlineKeyboardButton("🔗 Refer & Earn", callback_data="menu_refer")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
            ])
        )
    except Exception as e:
        logger.error(f"Profile card error: {e}")
        await message.reply(
            f"👤 **Profile**\n\nName: {row['first_name']}\nEdits: {row['total_edits']}\nCoins: {row['coins']}",
            reply_markup=main_menu_keyboard(user_id)
        )

@app.on_message(filters.command("refer"))
@require_registered
async def cmd_refer(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    try:
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
    except Exception:
        link = f"https://t.me/KiraFxBot?start={user_id}"
    ref_days = get_setting("referral_premium_days", "3")
    ref_coins = get_setting("referral_coins", "100")
    await message.reply(
        f"🔗 **Your Referral Link**\n\n"
        f"`{link}`\n\n"
        f"**Rewards per referral:**\n"
        f"• ✅ {ref_days} days Premium added to you\n"
        f"• 🪙 {ref_coins} Coins added to you\n\n"
        f"**Your total referrals:** {row['referral_count']}\n"
        f"**Your coins:** 🪙 {row['coins']}\n\n"
        f"Share your link and earn rewards every time someone joins!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Get Premium", callback_data="menu_premium"),
             InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
        ])
    )

@app.on_message(filters.command("ping"))
async def cmd_ping(client, message: Message):
    start = time.time()
    msg = await message.reply("🏓 Pinging...")
    elapsed = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 **Pong!**\n\nResponse: `{elapsed:.1f}ms`")

@app.on_message(filters.command("alive"))
async def cmd_alive(client, message: Message):
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    await message.reply(
        f"✅ **{BOT_NAME}** is alive and running!\n\n"
        f"⏱️ **Uptime:** `{h:02d}h {m:02d}m {s:02d}s`\n"
        f"🔧 **FFmpeg:** `{'✅ Ready' if check_ffmpeg() else '❌ Not Found'}`\n"
        f"👥 **Total Users:** `{get_user_count()}`\n"
        f"⭐ **Premium Users:** `{get_premium_count()}`\n"
        f"✂️ **Total Edits:** `{get_total_edits()}`\n"
        f"📝 **Today's Edits:** `{get_today_edits()}`\n"
        f"💻 **CPU:** `{cpu}%` | **RAM:** `{mem}%`\n"
        f"🟢 **Status:** Always alive — auto keep-alive active",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ])
    )

@app.on_message(filters.command("info"))
async def cmd_info(client, message: Message):
    await message.reply(
        f"ℹ️ **{BOT_NAME}**\n\n"
        f"**Version:** v{BOT_VERSION}\n"
        f"**Framework:** Pyrogram 2.0\n"
        f"**Image Filters:** {len(IMAGE_FILTERS)}+\n"
        f"**Video Effects:** {len(VIDEO_EFFECTS)}+\n"
        f"**Compression Presets:** {len(COMPRESSION_PRESETS)} (144p – 4K)\n"
        f"**Premium Plans:** {len(PREMIUM_PLANS)}\n"
        f"**Logo Styles:** {len(LOGO_STYLES)}\n"
        f"**AI Styles:** {len(AI_TEXT_IMAGE_STYLES)}\n"
        f"**FFmpeg:** {'Installed ✅' if check_ffmpeg() else 'Not found ❌'}\n"
        f"**Total Users:** {get_user_count()}\n"
        f"**Premium Users:** {get_premium_count()}\n"
        f"**Total Edits:** {get_total_edits()}\n",
        reply_markup=main_menu_keyboard(message.from_user.id)
    )

@app.on_message(filters.command("queue"))
@require_registered
async def cmd_queue(client, message: Message):
    pos = job_queue.get_position(message.from_user.id)
    if pos > 0:
        await message.reply(
            f"📋 **Queue Position:** #{pos}\n\nYour job is being processed. Please wait.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="menu_main")]])
        )
    else:
        await message.reply(
            "✅ **No active queue** — You can start editing right now!",
            reply_markup=main_menu_keyboard(message.from_user.id)
        )

@app.on_message(filters.command("timeline"))
@require_registered
async def cmd_timeline(client, message: Message):
    user_id = message.from_user.id
    tl = get_timeline(user_id)
    steps_count = len(tl.get("steps", []))
    has_media = bool(tl.get("media_path") and os.path.exists(tl.get("media_path") or ""))

    status = ""
    if has_media:
        status = f"📂 Media loaded | {steps_count} step(s) in timeline\n"
    else:
        status = "📭 No media loaded — send a photo or video to start\n"

    await message.reply(
        f"📊 **Timeline Editor**\n\n"
        f"{status}\n"
        f"Layer multiple filters/effects step-by-step, then export the final result.\n\n"
        f"**How to use:**\n"
        f"1️⃣ Send a photo or video\n"
        f"2️⃣ Choose 'Add to Timeline'\n"
        f"3️⃣ Stack as many effects as you want\n"
        f"4️⃣ Tap ▶️ Apply All to export",
        reply_markup=timeline_keyboard(user_id)
    )

@app.on_message(filters.command("rename"))
@require_registered
async def cmd_rename(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "rename")
    await message.reply(
        "✏️ **Rename File**\n\n"
        "Send the file (document/audio/video) you want to rename.",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("metadata"))
@require_registered
async def cmd_metadata(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "metadata")
    await message.reply(
        "📝 **Metadata Editor**\n\n"
        "Send the media file you want to edit metadata for.",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("compress"))
@require_registered
async def cmd_compress(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "compress")
    await message.reply(
        "🗜️ **Video Compression**\n\n"
        "Send the video you want to compress.\n"
        "Supports: 144p, 240p, 360p, 480p, 720p, 1080p, 1440p⭐, 2K⭐, 4K⭐\n"
        "⭐ = Premium only",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("logo"))
@require_registered
async def cmd_logo(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "logo")
        await message.reply(
            "🎨 **Logo Maker**\n\nSend the text for your logo:",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "logo_text", args[1])
    await message.reply(
        f"🎨 Choose a **style** for: **{args[1]}**",
        reply_markup=logo_style_keyboard()
    )

@app.on_message(filters.command("txt2img"))
@require_registered
async def cmd_txt2img(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "txt2img")
        await message.reply(
            "🖼️ **Text to Image**\n\n"
            "Send your prompt. Optionally prefix with a style:\n"
            "`gradient:`, `neon:`, `gold:`, `dark:`, `fire:`, `ocean:`",
            reply_markup=cancel_keyboard()
        )
        return
    await process_txt2img(client, message, user_id, args[1])

@app.on_message(filters.command("txt2vid"))
@require_registered
async def cmd_txt2vid(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "txt2vid")
        await message.reply(
            "🎬 **Text to Video**\n\nSend your video prompt:",
            reply_markup=cancel_keyboard()
        )
        return
    await process_txt2vid(client, message, user_id, args[1])

@app.on_message(filters.command("aiedit"))
@require_registered
async def cmd_aiedit(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "aiedit_prompt")
        await message.reply(
            "🤖 **AI Prompt Edit**\n\n"
            "Describe what you want to do with your image:\n"
            "_Examples: 'make it look vintage and warm', 'add a neon glow effect', 'sharpen and enhance colors'_\n\n"
            "Then send your image after typing the prompt.",
            reply_markup=cancel_keyboard()
        )
        return
    prompt = args[1].lower()
    await handle_aiedit_prompt(client, message, user_id, prompt)

async def handle_aiedit_prompt(client, message, user_id, prompt):
    AI_FILTER_KEYWORDS = {
        "blur": "blur", "sharp": "sharpen", "gray": "grayscale", "grey": "grayscale",
        "sepia": "sepia", "vintage": "vintage", "warm": "golden_hour", "cold": "cold_tone",
        "cool": "cold_tone", "sketch": "sketch", "cartoon": "cartoon", "neon": "neon",
        "bright": "brightness", "dark": "night", "contrast": "contrast", "color": "saturation",
        "invert": "invert", "flip": "flip_h", "rotate": "rotate_90", "glow": "glow",
        "watercolor": "watercolor", "oil": "oil_paint", "pixel": "pixelate", "glitch": "glitch",
        "sunset": "sunset", "winter": "winter", "autumn": "autumn", "spring": "spring",
        "emboss": "emboss", "edge": "edge_enhance", "border": "border", "shadow": "shadow",
        "vivid": "saturation", "fade": "fade", "matte": "matte", "lomo": "lomo",
        "hdr": "hdr", "vignette": "vignette", "comic": "comic", "pastel": "pastel",
    }
    filters_matched = []
    for kw, f in AI_FILTER_KEYWORDS.items():
        if kw in prompt and f not in filters_matched:
            filters_matched.append(f)

    if not filters_matched:
        await message.reply(
            "🤖 **AI Analysis:** Couldn't match filters to your prompt.\n\n"
            "Try describing effects like: blur, sharp, vintage, warm, cartoon, neon, glow, etc.\n\n"
            "Or send a photo directly to choose from the filter menu.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return

    set_session(user_id, "mode", "aiedit")
    set_session(user_id, "ai_filters", filters_matched)
    suggested = " → ".join(IMAGE_FILTERS.get(f, f) for f in filters_matched[:6])
    await message.reply(
        f"🤖 **AI Analysis Complete!**\n\n"
        f"**Detected filters:** {suggested}\n\n"
        f"Now send the **image** you want to edit with these filters.",
        reply_markup=cancel_keyboard()
    )

# ============================================================
# ADMIN COMMANDS (50+)
# ============================================================

@app.on_message(filters.command("admin"))
@require_registered
@require_admin
async def cmd_admin(client, message: Message):
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    await message.reply(
        f"🔑 **Admin Panel** — {BOT_NAME}\n\n"
        f"👥 Total Users: `{get_user_count()}`\n"
        f"⭐ Premium: `{get_premium_count()}`\n"
        f"👑 Admins: `{get_admin_count()}`\n"
        f"🚫 Banned: `{get_banned_count()}`\n"
        f"✂️ Total Edits: `{get_total_edits()}`\n"
        f"📅 Today's Edits: `{get_today_edits()}`\n"
        f"🆕 New Today: `{get_today_new_users()}`\n"
        f"⏱️ Uptime: `{h:02d}h {m:02d}m {s:02d}s`\n"
        f"💻 CPU: `{psutil.cpu_percent():.1f}%` | RAM: `{psutil.virtual_memory().percent:.1f}%`\n",
        reply_markup=admin_panel_keyboard()
    )

@app.on_message(filters.command("ban"))
@require_registered
@require_admin
async def cmd_ban(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /ban [user_id] [reason] [days (optional)]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    if target_id == OWNER_ID:
        await message.reply("❌ Cannot ban the bot owner.")
        return
    reason = " ".join(args[2:-1]) if len(args) > 3 and args[-1].isdigit() else " ".join(args[2:]) if len(args) > 2 else "Violation of terms"
    ban_until = None
    if len(args) > 3 and args[-1].isdigit():
        ban_until = (datetime.now() + timedelta(days=int(args[-1]))).isoformat()
    db = get_db()
    db.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, 'Unknown')", (target_id,))
    db.execute(
        "UPDATE users SET is_banned=1, ban_reason=?, ban_until=? WHERE user_id=?",
        (reason, ban_until, target_id)
    )
    db.commit()
    dur = f"{args[-1]} days" if ban_until else "permanent"
    await message.reply(f"✅ User `{target_id}` banned ({dur}). Reason: {reason}")
    try:
        await client.send_message(target_id, f"🚫 **You have been banned from KiraFx Bot.**\nReason: {reason}\nDuration: {dur}")
    except Exception:
        pass

@app.on_message(filters.command("unban"))
@require_registered
@require_admin
async def cmd_unban(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /unban [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    db = get_db()
    db.execute("UPDATE users SET is_banned=0, ban_reason=NULL, ban_until=NULL WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ User `{target_id}` unbanned.")
    try:
        await client.send_message(target_id, "✅ You have been unbanned from KiraFx Bot! Welcome back.")
    except Exception:
        pass

@app.on_message(filters.command("addprem"))
@require_registered
@require_admin
async def cmd_addprem(client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /addprem [user_id] [days] [plan_name (optional)]")
        return
    try:
        target_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    plan = args[3] if len(args) > 3 else "admin_grant"
    add_premium(target_id, days, plan)
    await message.reply(f"✅ Added {days} days **{plan}** premium to user `{target_id}`.")
    try:
        await client.send_message(target_id, f"⭐ **Premium Activated!**\nYou've been granted **{days} days** of premium by an admin!\nPlan: {plan}")
    except Exception:
        pass

@app.on_message(filters.command("rmprem"))
@require_registered
@require_admin
async def cmd_rmprem(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /rmprem [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    db = get_db()
    db.execute("UPDATE users SET is_premium=0, premium_until=NULL, premium_plan=NULL WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ Premium removed from user `{target_id}`.")
    try:
        await client.send_message(target_id, "ℹ️ Your premium subscription has been removed.")
    except Exception:
        pass

@app.on_message(filters.command("addadmin"))
@require_registered
async def cmd_addadmin(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can add admins.")
        return
    args = message.text.split(None, 3)
    if len(args) < 2:
        await message.reply("Usage: /addadmin [user_id] [title (optional)] [level 1-9 (optional)]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    title = args[2] if len(args) > 2 else "Admin"
    try:
        level = int(args[3]) if len(args) > 3 else 1
        level = max(1, min(9, level))
    except Exception:
        level = 1
    db = get_db()
    db.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, 'Admin')", (target_id,))
    db.execute("UPDATE users SET is_admin=1, admin_level=?, admin_title=? WHERE user_id=?", (level, title, target_id))
    db.execute("""INSERT OR REPLACE INTO admins (user_id, title, level, added_by, can_ban, can_broadcast, can_manage_premium, can_manage_users)
                  VALUES (?, ?, ?, ?, 1, 1, 1, 1)""", (target_id, title, level, message.from_user.id))
    db.commit()
    await message.reply(f"✅ User `{target_id}` added as **{title}** (Level {level})")
    try:
        await client.send_message(target_id, f"👑 You have been promoted to **{title}** in KiraFx Bot! Use /admin to access the panel.")
    except Exception:
        pass

@app.on_message(filters.command("rmadmin"))
@require_registered
async def cmd_rmadmin(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can remove admins.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /rmadmin [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    if target_id == OWNER_ID:
        await message.reply("❌ Cannot remove owner's admin status.")
        return
    db = get_db()
    db.execute("UPDATE users SET is_admin=0, admin_level=0, admin_title=NULL WHERE user_id=?", (target_id,))
    db.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ Admin `{target_id}` removed.")

@app.on_message(filters.command("listadmins"))
@require_registered
@require_admin
async def cmd_listadmins(client, message: Message):
    admins = get_db().execute("SELECT * FROM admins ORDER BY level DESC").fetchall()
    if not admins:
        await message.reply("No admins found.")
        return
    text = "👑 **Admin List:**\n\n"
    for a in admins:
        text += f"• `{a['user_id']}` — {a['title']} (Lvl {a['level']})\n"
    await message.reply(text)

@app.on_message(filters.command("userinfo"))
@require_registered
@require_admin
async def cmd_userinfo(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /userinfo [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    row = get_user(target_id)
    if not row:
        await message.reply("❌ User not found in database.")
        return
    prem_text = "⭐ Yes" if row["is_premium"] else "No"
    admin_text = "✅ Yes" if row["is_admin"] else "No"
    banned_text = "🚫 Yes" if row["is_banned"] else "No"
    prem_until = str(row["premium_until"] or "N/A")[:10] if row["premium_until"] is not None else "N/A"
    admin_level = row["admin_level"] if row["admin_level"] is not None else 0
    ban_reason = row["ban_reason"] or "N/A" if row["ban_reason"] is not None else "N/A"
    await message.reply(
        f"👤 **User Info: `{target_id}`**\n\n"
        f"**Name:** {row['first_name']} {row['last_name'] or ''}\n"
        f"**Username:** @{row['username'] or 'N/A'}\n"
        f"**Premium:** {prem_text} (until {prem_until})\n"
        f"**Admin:** {admin_text} (Level {admin_level})\n"
        f"**Banned:** {banned_text}\n"
        f"**Reason:** {ban_reason}\n"
        f"**Edits Today:** {row['edits_today']}\n"
        f"**Total Edits:** {row['total_edits']}\n"
        f"**Coins:** 🪙 {row['coins']}\n"
        f"**Referrals:** {row['referral_count']}\n"
        f"**Trial Used:** {'Yes' if row['trial_used'] else 'No'}\n"
        f"**Joined:** {str(row['joined_at'])[:10]}\n"
        f"**Last Seen:** {str(row['last_seen'])[:16]}\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Ban", callback_data=f"quick_ban_{target_id}"),
             InlineKeyboardButton("⭐ Add Premium", callback_data=f"quick_addprem_{target_id}")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
        ])
    )

@app.on_message(filters.command("addcoins"))
@require_registered
@require_admin
async def cmd_addcoins(client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /addcoins [user_id] [amount]")
        return
    try:
        target_id, amount = int(args[1]), int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    add_coins(target_id, amount, "Admin grant")
    await message.reply(f"✅ Added 🪙 {amount} coins to user `{target_id}`.")

@app.on_message(filters.command("rmcoins"))
@require_registered
@require_admin
async def cmd_rmcoins(client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /rmcoins [user_id] [amount]")
        return
    try:
        target_id, amount = int(args[1]), int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    get_db().execute("UPDATE users SET coins=MAX(0,coins-?) WHERE user_id=?", (amount, target_id))
    get_db().commit()
    await message.reply(f"✅ Removed 🪙 {amount} coins from user `{target_id}`.")

@app.on_message(filters.command("broadcast"))
@require_registered
@require_admin
async def cmd_broadcast(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: /broadcast [message]\nYou can use markdown formatting.")
        return
    text = args[1]
    users = get_all_users()
    sent = 0
    failed = 0
    status_msg = await message.reply(f"📢 Broadcasting to {len(users)} users...")
    for i, user_row in enumerate(users):
        try:
            await client.send_message(user_row["user_id"], text)
            sent += 1
            if sent % 50 == 0:
                await status_msg.edit_text(f"📢 Sending... {sent}/{len(users)}")
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
    db = get_db()
    db.execute(
        "INSERT INTO broadcast_logs (admin_id, message_text, sent_count, failed_count) VALUES (?, ?, ?, ?)",
        (message.from_user.id, text[:500], sent, failed)
    )
    db.commit()
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent: {sent}\n❌ Failed: {failed}\n📊 Total: {len(users)}"
    )

@app.on_message(filters.command("setwelcome"))
@require_registered
@require_admin
async def cmd_setwelcome(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: /setwelcome [message]")
        return
    set_setting("welcome_message", args[1])
    await message.reply(f"✅ Welcome message updated.")

@app.on_message(filters.command("setwatermark"))
@require_registered
@require_admin
async def cmd_setwatermark(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: /setwatermark [text]")
        return
    set_setting("watermark_text", args[1])
    await message.reply(f"✅ Watermark text set to: `{args[1]}`")

@app.on_message(filters.command("setfree"))
@require_registered
@require_admin
async def cmd_setfree(client, message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Usage: /setfree [number]")
        return
    set_setting("free_edits_per_day", args[1])
    await message.reply(f"✅ Free edits per day set to: **{args[1]}**")

@app.on_message(filters.command("setads"))
@require_registered
@require_admin
async def cmd_setads(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /setads [on|off] [interval (optional)]")
        return
    if args[1].lower() == "on":
        set_setting("ads_enabled", "1")
        if len(args) > 2 and args[2].isdigit():
            set_setting("ads_interval", args[2])
        interval = get_setting("ads_interval", "5")
        await message.reply(f"✅ Ads enabled. Shown every {interval} edits.")
    else:
        set_setting("ads_enabled", "0")
        await message.reply("✅ Ads disabled.")

@app.on_message(filters.command("maintenance"))
@require_registered
@require_admin
async def cmd_maintenance(client, message: Message):
    current = get_setting("maintenance_mode", "0")
    new_val = "0" if current == "1" else "1"
    set_setting("maintenance_mode", new_val)
    status = "🔧 ON (users cannot use bot)" if new_val == "1" else "✅ OFF (bot is live)"
    await message.reply(f"Maintenance mode: **{status}**")

@app.on_message(filters.command("backup"))
@require_registered
@require_admin
async def cmd_backup(client, message: Message):
    backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    await client.send_document(
        message.chat.id,
        document=backup_path,
        caption=f"💾 **Database Backup**\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nUsers: {get_user_count()}"
    )
    os.remove(backup_path)

@app.on_message(filters.command("cleanup"))
@require_registered
@require_admin
async def cmd_cleanup(client, message: Message):
    before = len(list(Path(TEMP_DIR).iterdir()))
    cleanup_temp_files(0)
    cleanup_sessions()
    after = len(list(Path(TEMP_DIR).iterdir()))
    await message.reply(f"✅ Cleanup done!\nRemoved {before - after} temp files.\nSessions cleared.")

@app.on_message(filters.command("logs"))
@require_registered
@require_admin
async def cmd_logs(client, message: Message):
    if os.path.exists(LOG_FILE):
        await client.send_document(message.chat.id, document=LOG_FILE, caption="📋 Bot Logs")
    else:
        await message.reply("❌ Log file not found.")

@app.on_message(filters.command("export"))
@require_registered
@require_admin
async def cmd_export(client, message: Message):
    settings = {r[0]: r[1] for r in get_db().execute("SELECT key, value FROM settings").fetchall()}
    config = {
        "bot_name": BOT_NAME,
        "version": BOT_VERSION,
        "settings": settings,
        "admin_count": get_admin_count(),
        "user_count": get_user_count(),
        "premium_count": get_premium_count(),
        "banned_count": get_banned_count(),
        "total_edits": get_total_edits(),
        "today_edits": get_today_edits(),
        "today_new_users": get_today_new_users(),
        "exported_at": datetime.now().isoformat(),
    }
    export_path = temp_path(".json")
    with open(export_path, "w") as f:
        json.dump(config, f, indent=2)
    await client.send_document(message.chat.id, document=export_path, caption="📤 Bot Configuration Export")
    os.remove(export_path)

@app.on_message(filters.command("addcmd"))
@require_registered
@require_admin
async def cmd_addcmd(client, message: Message):
    """Add custom command. Usage: /addcmd [command] [response] or reply to media"""
    args = message.text.split(None, 2)
    if len(args) < 3 and not message.reply_to_message:
        await message.reply(
            "📝 **Add Custom Command**\n\n"
            "Usage: `/addcmd [command] [response]`\n"
            "Or reply to media: `/addcmd [command]`\n"
            "For code output: `/addcmd [command] --code [code]`\n\n"
            "Example: `/addcmd hello Welcome to KiraFx!`"
        )
        return

    cmd_name = args[1].lstrip("/").lower() if len(args) > 1 else None
    if not cmd_name:
        await message.reply("❌ Provide a command name.")
        return

    db = get_db()
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.photo:
            media_id, response_type = reply.photo.file_id, "photo"
        elif reply.video:
            media_id, response_type = reply.video.file_id, "video"
        elif reply.audio:
            media_id, response_type = reply.audio.file_id, "audio"
        elif reply.document:
            media_id, response_type = reply.document.file_id, "document"
        else:
            await message.reply("❌ Unsupported media type.")
            return
        db.execute(
            "INSERT OR REPLACE INTO custom_commands (command, response_type, media_id, added_by) VALUES (?, ?, ?, ?)",
            (cmd_name, response_type, media_id, message.from_user.id)
        )
    else:
        response_text = args[2] if len(args) > 2 else ""
        if "--code" in response_text:
            code = response_text.replace("--code", "").strip()
            db.execute(
                "INSERT OR REPLACE INTO custom_commands (command, response_type, response, added_by) VALUES (?, 'code', ?, ?)",
                (cmd_name, code, message.from_user.id)
            )
        else:
            db.execute(
                "INSERT OR REPLACE INTO custom_commands (command, response_type, response, added_by) VALUES (?, 'text', ?, ?)",
                (cmd_name, response_text, message.from_user.id)
            )
    db.commit()
    await message.reply(f"✅ Custom command `/{cmd_name}` added successfully!")

@app.on_message(filters.command("delcmd"))
@require_registered
@require_admin
async def cmd_delcmd(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /delcmd [command]")
        return
    cmd_name = args[1].lstrip("/").lower()
    get_db().execute("DELETE FROM custom_commands WHERE command=?", (cmd_name,))
    get_db().commit()
    await message.reply(f"✅ Command `/{cmd_name}` deleted.")

@app.on_message(filters.command("togglecmd"))
@require_registered
@require_admin
async def cmd_togglecmd(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /togglecmd [command]")
        return
    cmd_name = args[1].lstrip("/").lower()
    db = get_db()
    row = db.execute("SELECT is_enabled FROM custom_commands WHERE command=?", (cmd_name,)).fetchone()
    if not row:
        await message.reply("❌ Command not found.")
        return
    new_state = 0 if row["is_enabled"] else 1
    db.execute("UPDATE custom_commands SET is_enabled=? WHERE command=?", (new_state, cmd_name))
    db.commit()
    state_str = "enabled ✅" if new_state else "disabled ❌"
    await message.reply(f"✅ Command `/{cmd_name}` is now {state_str}.")

@app.on_message(filters.command("listcmds"))
@require_registered
@require_admin
async def cmd_listcmds(client, message: Message):
    cmds = get_db().execute("SELECT command, response_type, is_enabled, use_count FROM custom_commands").fetchall()
    if not cmds:
        await message.reply("📭 No custom commands found.")
        return
    text = "📋 **Custom Commands:**\n\n"
    for row in cmds:
        status = "✅" if row["is_enabled"] else "❌"
        text += f"{status} `/{row['command']}` [{row['response_type']}] — used {row['use_count']}x\n"
    await message.reply(text)

@app.on_message(filters.command("addautoreply"))
@require_registered
@require_admin
async def cmd_addautoreply(client, message: Message):
    args = message.text.split(None, 3)
    if len(args) < 4:
        await message.reply(
            "Usage: /addautoreply [exact|contains|startswith] [trigger] [response]\n"
            "Example: /addautoreply contains hello Hi there! 👋"
        )
        return
    match_type = args[1].lower()
    if match_type not in ["exact", "contains", "startswith"]:
        await message.reply("❌ Match type must be: exact, contains, or startswith")
        return
    trigger, response = args[2], args[3]
    db = get_db()
    db.execute(
        "INSERT INTO auto_replies (trigger, match_type, response, response_type, added_by) VALUES (?, ?, ?, 'text', ?)",
        (trigger, match_type, response, message.from_user.id)
    )
    db.commit()
    await message.reply(f"✅ Auto-reply added!\nTrigger: `{trigger}` ({match_type})")

@app.on_message(filters.command("delautoreply"))
@require_registered
@require_admin
async def cmd_delautoreply(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /delautoreply [id]")
        return
    try:
        reply_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid ID.")
        return
    get_db().execute("DELETE FROM auto_replies WHERE id=?", (reply_id,))
    get_db().commit()
    await message.reply(f"✅ Auto-reply #{reply_id} deleted.")

@app.on_message(filters.command("listautoreplies"))
@require_registered
@require_admin
async def cmd_listautoreplies(client, message: Message):
    rows = get_db().execute("SELECT * FROM auto_replies").fetchall()
    if not rows:
        await message.reply("📭 No auto-replies found.")
        return
    text = "🤖 **Auto-Replies:**\n\n"
    for row in rows:
        status = "✅" if row["is_enabled"] else "❌"
        text += f"{status} #{row['id']} `{row['trigger']}` ({row['match_type']}) → {row['response'][:40]}\n"
    await message.reply(text)

@app.on_message(filters.command("stats"))
@require_registered
@require_admin
async def cmd_stats(client, message: Message):
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    top_users = get_db().execute(
        "SELECT first_name, total_edits FROM users ORDER BY total_edits DESC LIMIT 5"
    ).fetchall()
    top_text = "\n".join(f"  {i+1}. {r['first_name']}: {r['total_edits']} edits"
                          for i, r in enumerate(top_users))
    await message.reply(
        f"📊 **Full Bot Statistics**\n\n"
        f"👥 Total Users: {get_user_count()}\n"
        f"⭐ Premium: {get_premium_count()}\n"
        f"👑 Admins: {get_admin_count()}\n"
        f"🚫 Banned: {get_banned_count()}\n"
        f"✂️ Total Edits: {get_total_edits()}\n"
        f"📅 Today Edits: {get_today_edits()}\n"
        f"🆕 New Today: {get_today_new_users()}\n"
        f"⏱️ Uptime: {h:02d}h {m:02d}m\n"
        f"💻 CPU: {psutil.cpu_percent():.1f}%\n"
        f"🧠 RAM: {psutil.virtual_memory().percent:.1f}%\n\n"
        f"🏆 **Top 5 Users:**\n{top_text}\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
    )

@app.on_message(filters.command("resetedits"))
@require_registered
@require_admin
async def cmd_resetedits(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /resetedits [user_id|all]")
        return
    if args[1].lower() == "all":
        get_db().execute("UPDATE users SET edits_today=0")
        get_db().commit()
        await message.reply("✅ Reset daily edits for ALL users.")
    else:
        try:
            target_id = int(args[1])
        except ValueError:
            await message.reply("❌ Invalid user ID.")
            return
        get_db().execute("UPDATE users SET edits_today=0 WHERE user_id=?", (target_id,))
        get_db().commit()
        await message.reply(f"✅ Reset daily edits for user `{target_id}`.")

@app.on_message(filters.command("premlist"))
@require_registered
@require_admin
async def cmd_premlist(client, message: Message):
    rows = get_db().execute(
        "SELECT user_id, first_name, premium_until, premium_plan FROM users WHERE is_premium=1 ORDER BY premium_until"
    ).fetchall()
    if not rows:
        await message.reply("No premium users.")
        return
    text = "⭐ **Premium Users:**\n\n"
    for r in rows[:30]:
        until = str(r["premium_until"] or "Lifetime")[:10]
        text += f"• `{r['user_id']}` {r['first_name']} — {r['premium_plan'] or 'N/A'} until {until}\n"
    if len(rows) > 30:
        text += f"\n...and {len(rows)-30} more"
    await message.reply(text)

@app.on_message(filters.command("banlist"))
@require_registered
@require_admin
async def cmd_banlist(client, message: Message):
    rows = get_db().execute(
        "SELECT user_id, first_name, ban_reason FROM users WHERE is_banned=1"
    ).fetchall()
    if not rows:
        await message.reply("No banned users.")
        return
    text = "🚫 **Banned Users:**\n\n"
    for r in rows[:30]:
        text += f"• `{r['user_id']}` {r['first_name']} — {r['ban_reason'] or 'N/A'}\n"
    await message.reply(text)

@app.on_message(filters.command("note"))
@require_registered
@require_admin
async def cmd_note(client, message: Message):
    args = message.text.split(None, 2)
    if len(args) < 3:
        await message.reply("Usage: /note [title] [content]\n\nTo view all notes: /notes")
        return
    title, content = args[1], args[2]
    db = get_db()
    db.execute("INSERT INTO bot_notes (title, content, created_by) VALUES (?, ?, ?)",
               (title, content, message.from_user.id))
    db.commit()
    await message.reply(f"✅ Note **{title}** saved.")

@app.on_message(filters.command("notes"))
@require_registered
@require_admin
async def cmd_notes(client, message: Message):
    rows = get_db().execute("SELECT * FROM bot_notes ORDER BY created_at DESC").fetchall()
    if not rows:
        await message.reply("📭 No notes saved.")
        return
    text = "📋 **Bot Notes:**\n\n"
    for r in rows[:15]:
        text += f"**{r['title']}** (#{r['id']}) — {str(r['created_at'])[:10]}\n{r['content'][:80]}\n\n"
    await message.reply(text)

@app.on_message(filters.command("delnote"))
@require_registered
@require_admin
async def cmd_delnote(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /delnote [id]")
        return
    try:
        note_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid ID.")
        return
    get_db().execute("DELETE FROM bot_notes WHERE id=?", (note_id,))
    get_db().commit()
    await message.reply(f"✅ Note #{note_id} deleted.")

@app.on_message(filters.command("runcode"))
@require_registered
async def cmd_runcode(client, message: Message):
    """Admin-only: Run a Python snippet and show output."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        perms = get_admin_perms(user_id)
        if not perms or not perms["can_run_code"]:
            await message.reply("🚫 You don't have permission to run code.")
            return
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "💻 **Run Python Code**\n\n"
            "Usage: `/runcode [python code]`\n"
            "Example: `/runcode print(get_user_count())`"
        )
        return
    code = args[1]
    output = ""
    try:
        import io as _io, contextlib
        stdout_capture = _io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {
                "get_db": get_db, "get_user": get_user, "get_user_count": get_user_count,
                "get_setting": get_setting, "set_setting": set_setting,
                "is_premium": is_premium, "is_admin": is_admin,
                "add_premium": add_premium, "add_coins": add_coins,
                "logger": logger, "datetime": datetime, "json": json,
            })
        output = stdout_capture.getvalue() or "(no output)"
    except Exception as e:
        output = f"Error: {e}"
    await message.reply(f"💻 **Code Output:**\n```\n{output[:1000]}\n```")

@app.on_message(filters.command("deploy"))
@require_registered
@require_admin
async def cmd_deploy(client, message: Message):
    """Admin: Show deployment status and options."""
    uptime_secs = int(time.time() - START_TIME)
    h, m, s = uptime_secs // 3600, (uptime_secs % 3600) // 60, uptime_secs % 60
    disk = psutil.disk_usage("/")
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    await message.reply(
        f"🚀 **KiraFx Deploy Dashboard**\n\n"
        f"**Bot:** {BOT_NAME} v{BOT_VERSION}\n"
        f"**Status:** 🟢 Online\n"
        f"**Uptime:** `{h:02d}h {m:02d}m {s:02d}s`\n\n"
        f"**System Resources:**\n"
        f"CPU: `{cpu:.1f}%`\n"
        f"RAM: `{ram:.1f}%`\n"
        f"Disk: `{disk.percent}%` used ({disk.free // (1024**3):.1f} GB free)\n\n"
        f"**Services:**\n"
        f"Flask Dashboard: 🟢 Port {FLASK_PORT}\n"
        f"Keep-Alive: 🟢 Active (60s)\n"
        f"FFmpeg: {'🟢 Ready' if check_ffmpeg() else '🔴 Not Found'}\n"
        f"Database: 🟢 Connected\n\n"
        f"**Bot Stats:**\n"
        f"Users: {get_user_count()} | Premium: {get_premium_count()}\n"
        f"Total Edits: {get_total_edits()}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart"),
             InlineKeyboardButton("📊 Full Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("🔑 Admin Panel", callback_data="admin_panel"),
             InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
        ])
    )

@app.on_message(filters.command("warnuser"))
@require_registered
@require_admin
async def cmd_warnuser(client, message: Message):
    args = message.text.split(None, 2)
    if len(args) < 2:
        await message.reply("Usage: /warnuser [user_id] [reason]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    reason = args[2] if len(args) > 2 else "Rule violation"
    get_db().execute("INSERT INTO user_warnings (user_id, reason, warned_by) VALUES (?, ?, ?)",
                     (target_id, reason, message.from_user.id))
    get_db().commit()
    warn_count = get_db().execute("SELECT COUNT(*) FROM user_warnings WHERE user_id=?", (target_id,)).fetchone()[0]
    await message.reply(f"⚠️ User `{target_id}` warned.\nReason: {reason}\nTotal warnings: {warn_count}")
    try:
        await client.send_message(target_id, f"⚠️ **Warning from KiraFx Admin**\nReason: {reason}\nTotal warnings: {warn_count}\n\nPlease follow the rules to avoid a ban.")
    except Exception:
        pass

@app.on_message(filters.command("warnlist"))
@require_registered
@require_admin
async def cmd_warnlist(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /warnlist [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    rows = get_db().execute("SELECT reason, created_at FROM user_warnings WHERE user_id=? ORDER BY created_at DESC", (target_id,)).fetchall()
    if not rows:
        await message.reply(f"✅ No warnings for user `{target_id}`.")
        return
    text = f"⚠️ **Warnings for `{target_id}` ({len(rows)} total):**\n\n"
    for r in rows:
        text += f"• {r['reason']} — {str(r['created_at'])[:16]}\n"
    await message.reply(text)

@app.on_message(filters.command("clearwarn"))
@require_registered
@require_admin
async def cmd_clearwarn(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /clearwarn [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    get_db().execute("DELETE FROM user_warnings WHERE user_id=?", (target_id,))
    get_db().commit()
    await message.reply(f"✅ All warnings cleared for user `{target_id}`.")

@app.on_message(filters.command("muteuser"))
@require_registered
@require_admin
async def cmd_muteuser(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /muteuser [user_id] [hours (default: 1)]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    hours = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1
    muted_until = (datetime.now() + timedelta(hours=hours)).isoformat()
    db = get_db()
    db.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, 'Unknown')", (target_id,))
    db.execute("UPDATE users SET is_muted=1, muted_until=? WHERE user_id=?", (muted_until, target_id))
    db.commit()
    await message.reply(f"🔇 User `{target_id}` muted for {hours} hour(s).")
    try:
        await client.send_message(target_id, f"🔇 You have been muted for {hours} hour(s) by an admin.")
    except Exception:
        pass

@app.on_message(filters.command("unmuteuser"))
@require_registered
@require_admin
async def cmd_unmuteuser(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /unmuteuser [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    get_db().execute("UPDATE users SET is_muted=0, muted_until=NULL WHERE user_id=?", (target_id,))
    get_db().commit()
    await message.reply(f"✅ User `{target_id}` unmuted.")

@app.on_message(filters.command("topusers"))
@require_registered
@require_admin
async def cmd_topusers(client, message: Message):
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
    limit = min(limit, 25)
    rows = get_db().execute(
        "SELECT user_id, first_name, username, total_edits, is_premium FROM users ORDER BY total_edits DESC LIMIT ?", (limit,)
    ).fetchall()
    text = f"🏆 **Top {limit} Users by Edits:**\n\n"
    for i, r in enumerate(rows, 1):
        badge = "⭐" if r["is_premium"] else "🆓"
        text += f"{i}. {badge} `{r['user_id']}` {r['first_name']} — **{r['total_edits']}** edits\n"
    await message.reply(text)

@app.on_message(filters.command("diskusage"))
@require_registered
@require_admin
async def cmd_diskusage(client, message: Message):
    disk = psutil.disk_usage("/")
    temp_files = list(Path(TEMP_DIR).iterdir())
    temp_size = sum(f.stat().st_size for f in temp_files if f.is_file()) / (1024*1024)
    db_size = os.path.getsize(DB_PATH) / (1024*1024) if os.path.exists(DB_PATH) else 0
    log_size = os.path.getsize(LOG_FILE) / (1024*1024) if os.path.exists(LOG_FILE) else 0
    await message.reply(
        f"💽 **Disk Usage Report**\n\n"
        f"**System:**\n"
        f"Total: {disk.total / (1024**3):.1f} GB\n"
        f"Used: {disk.used / (1024**3):.1f} GB ({disk.percent}%)\n"
        f"Free: {disk.free / (1024**3):.1f} GB\n\n"
        f"**Bot Files:**\n"
        f"Temp Dir: {len(temp_files)} files, {temp_size:.2f} MB\n"
        f"Database: {db_size:.2f} MB\n"
        f"Log File: {log_size:.2f} MB"
    )

@app.on_message(filters.command("dbstats"))
@require_registered
@require_admin
async def cmd_dbstats(client, message: Message):
    db = get_db()
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    text = "🗃️ **Database Statistics:**\n\n"
    for t in tables:
        count = db.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0]
        text += f"• `{t['name']}`: {count} rows\n"
    db_size = os.path.getsize(DB_PATH) / (1024*1024) if os.path.exists(DB_PATH) else 0
    text += f"\n**Total DB Size:** {db_size:.2f} MB"
    await message.reply(text)

@app.on_message(filters.command("resetuser"))
@require_registered
@require_admin
async def cmd_resetuser(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can reset user data.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /resetuser [user_id]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    db = get_db()
    db.execute("UPDATE users SET edits_today=0, total_edits=0, coins=0, referral_count=0, is_premium=0, premium_until=NULL, is_banned=0, is_muted=0 WHERE user_id=?", (target_id,))
    db.execute("DELETE FROM user_warnings WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ User `{target_id}` data has been reset.")

@app.on_message(filters.command("getuser"))
@require_registered
@require_admin
async def cmd_getuser(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /getuser [username or user_id]")
        return
    query_val = args[1].lstrip("@")
    if query_val.isdigit():
        row = get_user(int(query_val))
    else:
        row = get_db().execute("SELECT * FROM users WHERE username=?", (query_val,)).fetchone()
    if not row:
        await message.reply("❌ User not found in database.")
        return
    await message.reply(
        f"👤 **User Found:**\n\n"
        f"ID: `{row['user_id']}`\n"
        f"Name: {row['first_name']} {row['last_name'] or ''}\n"
        f"Username: @{row['username'] or 'N/A'}\n"
        f"Status: {'⭐ Premium' if row['is_premium'] else '🆓 Free'}\n"
        f"Admin: {'✅' if row['is_admin'] else '❌'}\n"
        f"Banned: {'🚫' if row['is_banned'] else '✅'}\n"
        f"Edits: {row['total_edits']} | Coins: {row['coins']}\n"
        f"Joined: {str(row['joined_at'])[:10]}\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Ban", callback_data=f"quick_ban_{row['user_id']}"),
             InlineKeyboardButton("⭐ Add Premium", callback_data=f"quick_addprem_{row['user_id']}")],
        ])
    )

@app.on_message(filters.command("coinleader"))
@require_registered
@require_admin
async def cmd_coinleader(client, message: Message):
    rows = get_db().execute(
        "SELECT user_id, first_name, coins FROM users ORDER BY coins DESC LIMIT 15"
    ).fetchall()
    text = "🏅 **Coin Leaderboard:**\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. `{r['user_id']}` {r['first_name']} — 🪙 {r['coins']}\n"
    await message.reply(text)

@app.on_message(filters.command("activeusers"))
@require_registered
@require_admin
async def cmd_activeusers(client, message: Message):
    day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    rows = get_db().execute(
        "SELECT user_id, first_name, username, last_seen FROM users WHERE last_seen >= ? ORDER BY last_seen DESC LIMIT 20",
        (day_ago,)
    ).fetchall()
    text = f"🟢 **Active Users (Last 24h): {len(rows)}**\n\n"
    for r in rows:
        text += f"• `{r['user_id']}` {r['first_name']} — {str(r['last_seen'])[:16]}\n"
    await message.reply(text)

@app.on_message(filters.command("setmaxfile"))
@require_registered
@require_admin
async def cmd_setmaxfile(client, message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Usage: /setmaxfile [size_in_mb]")
        return
    set_setting("max_file_size_mb", args[1])
    await message.reply(f"✅ Max file size set to **{args[1]} MB**.")

@app.on_message(filters.command("mutelist"))
@require_registered
@require_admin
async def cmd_mutelist(client, message: Message):
    rows = get_db().execute(
        "SELECT user_id, first_name, muted_until FROM users WHERE is_muted=1 LIMIT 20"
    ).fetchall()
    if not rows:
        await message.reply("✅ No muted users.")
        return
    text = f"🔇 **Muted Users ({len(rows)}):**\n\n"
    for r in rows:
        until = str(r["muted_until"])[:16] if r["muted_until"] else "indefinite"
        text += f"• `{r['user_id']}` {r['first_name']} — until {until}\n"
    await message.reply(text)

@app.on_message(filters.command("banlist"))
@require_registered
@require_admin
async def cmd_banlist(client, message: Message):
    rows = get_db().execute(
        "SELECT user_id, first_name, ban_reason FROM users WHERE is_banned=1 LIMIT 20"
    ).fetchall()
    if not rows:
        await message.reply("✅ No banned users.")
        return
    text = f"🚫 **Banned Users ({len(rows)}):**\n\n"
    for r in rows:
        text += f"• `{r['user_id']}` {r['first_name']} — {r['ban_reason'] or 'No reason'}\n"
    await message.reply(text)

# ============================================================
# MEDIA HANDLERS
# ============================================================

async def handle_media_for_edit(client, message: Message, file_path: str, media_type: str):
    """Generic handler after downloading a media file."""
    user_id = message.from_user.id
    mode = get_session(user_id, "mode")

    if media_type == "photo":
        if mode == "aiedit":
            ai_filters = get_session(user_id, "ai_filters", [])
            if ai_filters:
                await apply_image_filters_sequence(client, message, file_path, ai_filters)
                clear_session(user_id)
                return
        # Check if in timeline mode
        if get_session(user_id, "timeline_mode"):
            tl = get_timeline(user_id)
            save_timeline(user_id, file_path, "image", tl.get("steps", []))
            clear_session(user_id, "timeline_mode")
            await message.reply(
                "📊 **Timeline Editor — Image Loaded!**\n\n"
                "Now add filters step by step:",
                reply_markup=timeline_keyboard(user_id)
            )
            return
        set_session(user_id, "image_path", file_path)
        clear_session(user_id, "mode")
        await message.reply(
            "📷 **Photo Received!**\n\nChoose a filter category:",
            reply_markup=image_category_keyboard()
        )

    elif media_type == "video":
        if mode == "compress":
            set_session(user_id, "video_path", file_path)
            clear_session(user_id, "mode")
            await message.reply(
                "🗜️ **Choose Compression Quality:**\n⭐ = Premium only",
                reply_markup=compress_keyboard()
            )
        elif get_session(user_id, "timeline_mode"):
            tl = get_timeline(user_id)
            save_timeline(user_id, file_path, "video", tl.get("steps", []))
            clear_session(user_id, "timeline_mode")
            await message.reply(
                "📊 **Timeline Editor — Video Loaded!**\n\n"
                "Now add effects step by step:",
                reply_markup=timeline_keyboard(user_id)
            )
        else:
            set_session(user_id, "video_path", file_path)
            clear_session(user_id, "mode")
            await message.reply(
                "🎬 **Video Received!**\n\nChoose an effect category:",
                reply_markup=video_category_keyboard()
            )

    elif media_type in ("document", "audio"):
        if mode == "rename":
            set_session(user_id, "rename_path", file_path)
            set_session(user_id, "rename_original", getattr(message.document or message.audio, "file_name", "file"))
            clear_session(user_id, "mode")
            await message.reply(
                "✏️ Type the **new filename** (with extension):",
                reply_markup=cancel_keyboard()
            )
        elif mode == "metadata":
            set_session(user_id, "metadata_path", file_path)
            clear_session(user_id, "mode")
            await show_metadata_menu(client, message)
        else:
            set_session(user_id, "rename_path", file_path)
            set_session(user_id, "rename_original", getattr(message.document or message.audio, "file_name", "file"))
            await message.reply(
                "📁 **File Received!**\n\nWhat would you like to do?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Rename", callback_data="do_rename"),
                     InlineKeyboardButton("📝 Edit Metadata", callback_data="do_metadata")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
                ])
            )

async def show_metadata_menu(client, message: Message):
    await message.reply(
        "📝 **Metadata Editor**\n\n"
        "Send metadata in this format:\n"
        "`title=My Title | artist=Artist | album=Album | year=2024`\n\n"
        "**Available fields:** title, artist, album, year, comment, description, genre, language, encoder, track, disc, composer, publisher, copyright",
        reply_markup=cancel_keyboard()
    )

async def apply_image_filters_sequence(client, message: Message, file_path: str, filters_list: List[str], user_id: int = None):
    """Apply multiple filters in sequence."""
    if user_id is None:
        user_id = message.from_user.id
    status_msg = await message.reply(f"⏳ Applying {len(filters_list)} filter(s)...")
    try:
        loop = asyncio.get_running_loop()
        img = Image.open(file_path).convert("RGB")

        for f in filters_list:
            img = await loop.run_in_executor(executor, lambda fi=f, im=img: apply_image_filter(im, fi))

        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = await loop.run_in_executor(executor, lambda: add_watermark(img, wm_text))

        out_path = temp_path(".jpg")
        img.save(out_path, "JPEG", quality=92)
        filter_names = " → ".join(IMAGE_FILTERS.get(f, f) for f in filters_list)
        await client.send_photo(
            message.chat.id,
            photo=out_path,
            caption=f"✅ **Applied:** {filter_names}\n\n{'⭐ Premium: No watermark' if is_premium(user_id) else ''}",
            reply_markup=after_edit_keyboard()
        )
        increment_edits(user_id)
        log_edit(user_id, "image_sequence", filter_names)
        await status_msg.delete()
        os.remove(out_path)

        # Ad injection
        if should_show_ad(user_id):
            await client.send_message(message.chat.id, get_random_ad())

    except Exception as e:
        logger.error(f"Filter apply error: {e}\n{traceback.format_exc()}")
        await status_msg.edit_text(f"❌ Error applying filters: {str(e)[:200]}")

@app.on_message(filters.photo)
@require_registered
async def handle_photo(client, message: Message):
    user_id = message.from_user.id
    # Handle aiedit_prompt mode – just store the prompt
    if get_session(user_id, "mode") == "aiedit_prompt":
        return
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ **Daily Limit Reached!**\n\nFree users get {limit} edits/day.\n\n"
            f"⭐ Upgrade to Premium for unlimited edits!",
            reply_markup=premium_plans_keyboard()
        )
        return
    status_msg = await message.reply("⬇️ Downloading photo...")
    try:
        file_path = await message.download(file_name=temp_path(".jpg"))
        await status_msg.delete()
        await handle_media_for_edit(client, message, file_path, "photo")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

@app.on_message(filters.video)
@require_registered
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ **Daily Limit Reached!**\n\nFree users get {limit} edits/day.\n\n"
            f"⭐ Upgrade to Premium for unlimited edits!",
            reply_markup=premium_plans_keyboard()
        )
        return
    status_msg = await message.reply("⬇️ Downloading video... Please wait.")
    for attempt in range(3):
        try:
            file_path = await message.download(file_name=temp_path(".mp4"))
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                break
        except Exception as e:
            if attempt == 2:
                await status_msg.edit_text(f"❌ Download failed after 3 attempts: {str(e)[:200]}")
                return
            await asyncio.sleep(2)
    await status_msg.delete()
    if not validate_video(file_path):
        await message.reply("❌ Invalid or corrupted video file. Please send a valid video.")
        return
    await handle_media_for_edit(client, message, file_path, "video")

@app.on_message(filters.document)
@require_registered
async def handle_document(client, message: Message):
    doc = message.document
    ext = Path(doc.file_name or "file").suffix.lower() if doc.file_name else ""
    video_exts = [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".3gp", ".m4v"]
    img_exts   = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"]
    status_msg = await message.reply("⬇️ Downloading file...")
    try:
        file_path = await message.download(file_name=temp_path(ext or ".bin"))
        await status_msg.delete()
        if ext in video_exts:
            await handle_media_for_edit(client, message, file_path, "video")
        elif ext in img_exts:
            await handle_media_for_edit(client, message, file_path, "photo")
        else:
            await handle_media_for_edit(client, message, file_path, "document")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

@app.on_message(filters.audio)
@require_registered
async def handle_audio(client, message: Message):
    status_msg = await message.reply("⬇️ Downloading audio...")
    try:
        file_path = await message.download(file_name=temp_path(".mp3"))
        await status_msg.delete()
        await handle_media_for_edit(client, message, file_path, "audio")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

# ============================================================
# TEXT MESSAGE HANDLER (multi-step flows + custom cmds)
# ============================================================

ALL_COMMANDS = [
    "start", "help", "admin", "ban", "unban", "addprem", "rmprem", "addadmin",
    "rmadmin", "listadmins", "userinfo", "addcoins", "rmcoins", "broadcast",
    "setwelcome", "setwatermark", "setfree", "setads", "maintenance", "backup",
    "cleanup", "logs", "export", "addcmd", "delcmd", "togglecmd", "listcmds",
    "addautoreply", "delautoreply", "listautoreplies", "stats", "resetedits",
    "premlist", "banlist", "note", "notes", "delnote", "runcode",
    "premium", "trial", "status", "profile", "refer", "rename", "metadata",
    "compress", "logo", "txt2img", "txt2vid", "aiedit", "ping", "alive",
    "info", "queue", "timeline",
    "deploy", "warnuser", "warnlist", "clearwarn", "muteuser", "unmuteuser",
    "mutelist", "topusers", "diskusage", "dbstats", "resetuser", "getuser",
    "coinleader", "activeusers", "setmaxfile",
]

@app.on_message(filters.text & ~filters.command(ALL_COMMANDS))
@require_registered
async def handle_text(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Auto-replies check
    auto_replies = get_db().execute("SELECT * FROM auto_replies WHERE is_enabled=1").fetchall()
    for rule in auto_replies:
        trigger = rule["trigger"]
        match_type = rule["match_type"]
        matched = False
        if match_type == "exact" and text.lower() == trigger.lower():
            matched = True
        elif match_type == "contains" and trigger.lower() in text.lower():
            matched = True
        elif match_type == "startswith" and text.lower().startswith(trigger.lower()):
            matched = True
        if matched:
            if rule["response_type"] == "text":
                await message.reply(rule["response"])
            return

    # Custom commands check
    if text.startswith("/"):
        cmd = text.split()[0].lstrip("/").lower()
        row = get_db().execute(
            "SELECT * FROM custom_commands WHERE command=? AND is_enabled=1", (cmd,)
        ).fetchone()
        if row:
            get_db().execute("UPDATE custom_commands SET use_count=use_count+1 WHERE id=?", (row["id"],))
            get_db().commit()
            if row["response_type"] == "text":
                await message.reply(row["response"])
            elif row["response_type"] == "code":
                await message.reply(f"```\n{row['response']}\n```")
            elif row["response_type"] == "photo":
                await client.send_photo(message.chat.id, row["media_id"])
            elif row["response_type"] == "video":
                await client.send_video(message.chat.id, row["media_id"])
            elif row["response_type"] == "audio":
                await client.send_audio(message.chat.id, row["media_id"])
            elif row["response_type"] == "document":
                await client.send_document(message.chat.id, row["media_id"])
            return

    # Mode-based flows
    mode = get_session(user_id, "mode")

    if mode == "aiedit_prompt":
        prompt = text.lower()
        clear_session(user_id, "mode")
        await handle_aiedit_prompt(client, message, user_id, prompt)
        return

    if mode == "rename":
        rename_path = get_session(user_id, "rename_path")
        if rename_path and os.path.exists(rename_path):
            new_name = text.strip()
            original = get_session(user_id, "rename_original", "file")
            status_msg = await message.reply(f"✏️ Renaming to `{new_name}`...")
            try:
                new_path = os.path.join(TEMP_DIR, new_name)
                shutil.copy2(rename_path, new_path)
                await client.send_document(
                    message.chat.id,
                    document=new_path,
                    file_name=new_name,
                    caption=f"✅ **Renamed!**\nOriginal: `{original}`\nNew name: `{new_name}`",
                )
                log_rename(user_id, original, new_name)
                await status_msg.delete()
                os.remove(new_path)
            except Exception as e:
                await status_msg.edit_text(f"❌ Rename error: {str(e)[:200]}")
            clear_session(user_id)
        return

    if mode == "metadata":
        meta_path = get_session(user_id, "metadata_path")
        if meta_path and os.path.exists(meta_path):
            meta = {}
            for part in text.split("|"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    meta[k.strip().lower()] = v.strip()
            if not meta:
                await message.reply("❌ Invalid format. Use: `title=Value | artist=Name`")
                return
            status_msg = await message.reply("📝 Applying metadata...")
            try:
                out_path = temp_path(Path(meta_path).suffix)
                cmd = ["ffmpeg", "-y", "-i", meta_path]
                for k, v in meta.items():
                    cmd += ["-metadata", f"{k}={v}"]
                cmd += ["-c", "copy", out_path]
                ok, err = run_ffmpeg(cmd)
                if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    await client.send_document(
                        message.chat.id,
                        document=out_path,
                        caption=f"✅ **Metadata Updated!**\n" + "\n".join(f"• {k}: {v}" for k, v in meta.items())
                    )
                    await status_msg.delete()
                    os.remove(out_path)
                else:
                    await status_msg.edit_text(f"❌ Metadata edit failed: {err[:200]}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            clear_session(user_id)
        return

    if mode == "logo":
        set_session(user_id, "logo_text", text)
        clear_session(user_id, "mode")
        await message.reply(
            f"🎨 Choose a **style** for: **{text}**",
            reply_markup=logo_style_keyboard()
        )
        return

    if mode == "txt2img":
        clear_session(user_id, "mode")
        await process_txt2img(client, message, user_id, text)
        return

    if mode == "txt2vid":
        clear_session(user_id, "mode")
        await process_txt2vid(client, message, user_id, text)
        return

    if mode == "aiedit":
        clear_session(user_id, "mode")
        await message.reply(
            "🤖 Now send the **image** or **video** you want to edit with AI filters.",
            reply_markup=cancel_keyboard()
        )
        return

    # Admin broadcast input
    if get_session(user_id, "admin_broadcast_input"):
        clear_session(user_id, "admin_broadcast_input")
        users = get_all_users()
        sent = 0; failed = 0
        status_msg = await message.reply(f"📢 Broadcasting to {len(users)} users...")
        for ur in users:
            try:
                await client.send_message(ur["user_id"], text)
                sent += 1
                await asyncio.sleep(0.05)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1
        get_db().execute(
            "INSERT INTO broadcast_logs (admin_id, message_text, sent_count, failed_count) VALUES (?, ?, ?, ?)",
            (user_id, text[:500], sent, failed)
        )
        get_db().commit()
        await status_msg.edit_text(f"✅ Broadcast done!\nSent: {sent} | Failed: {failed}")
        return

    # Admin settings inputs
    admin_setting = get_session(user_id, "admin_setting_input")
    if admin_setting and is_admin(user_id):
        clear_session(user_id, "admin_setting_input")
        set_setting(admin_setting, text.strip())
        await message.reply(f"✅ Setting `{admin_setting}` updated to: `{text.strip()}`")
        return

# ============================================================
# AI GENERATION
# ============================================================
async def process_txt2img(client, message: Message, user_id: int, prompt: str):
    status_msg = await message.reply(f"🎨 Generating image for: *{prompt[:50]}*...")
    try:
        style = "gradient"
        for s in AI_TEXT_IMAGE_STYLES.keys():
            if prompt.lower().startswith(s + ":"):
                style = s
                prompt = prompt[len(s)+1:].strip()
                break
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(executor, lambda: text_to_image(prompt, style))
        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = await loop.run_in_executor(executor, lambda: add_watermark(img, wm_text))
        bio = BytesIO()
        bio.name = "generated.png"
        img.save(bio, "PNG")
        bio.seek(0)
        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=f"🖼️ **Generated!**\n\nPrompt: *{prompt[:100]}*\nStyle: {style.upper()}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Generate Another", callback_data="ai_txt2img"),
                 InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
            ])
        )
        await status_msg.delete()
        increment_edits(user_id)
        log_edit(user_id, "ai_txt2img", prompt[:50])
    except Exception as e:
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

async def process_txt2vid(client, message: Message, user_id: int, prompt: str):
    status_msg = await message.reply(f"🎬 Generating video for: *{prompt[:50]}*...")
    try:
        styles = list(AI_TEXT_IMAGE_STYLES.keys())
        frames = []
        loop = asyncio.get_running_loop()

        # Generate 24 frames
        for i in range(24):
            ratio = i / 24
            style = styles[int(ratio * len(styles)) % len(styles)]
            frame = await loop.run_in_executor(executor, lambda s=style: text_to_image(f"{prompt}", s))
            frame_path = temp_path(".jpg")
            frame.save(frame_path, "JPEG", quality=85)
            frames.append(frame_path)

        list_file = temp_path(".txt")
        out_path = temp_path(".mp4")
        with open(list_file, "w") as lf:
            for fp in frames:
                lf.write(f"file '{fp}'\n")
                lf.write("duration 0.125\n")

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", list_file, "-vf", "fps=8,scale=800:600", "-pix_fmt", "yuv420p", out_path]
        ok, err = run_ffmpeg(cmd, timeout=120)

        if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            await client.send_video(
                message.chat.id,
                video=out_path,
                caption=f"🎬 **Generated Video!**\n\nPrompt: *{prompt[:100]}*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Generate Another", callback_data="ai_txt2vid"),
                     InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
                ])
            )
            await status_msg.delete()
            increment_edits(user_id)
            os.remove(out_path)
        else:
            img = await loop.run_in_executor(executor, lambda: text_to_image(prompt, "gradient"))
            bio = BytesIO()
            bio.name = "preview.png"
            img.save(bio, "PNG")
            bio.seek(0)
            await client.send_photo(message.chat.id, photo=bio,
                                     caption=f"🖼️ Video preview: *{prompt[:100]}*")
            await status_msg.delete()

        for fp in frames:
            try: os.remove(fp)
            except Exception: pass
        if os.path.exists(list_file):
            os.remove(list_file)
    except Exception as e:
        logger.error(f"txt2vid error: {e}\n{traceback.format_exc()}")
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================
@app.on_callback_query()
async def handle_callback(client, query: CallbackQuery):
    user = query.from_user
    data = query.data
    user_id = user.id

    register_user(user)
    if is_banned(user_id):
        await query.answer("🚫 You are banned from this bot.", show_alert=True)
        return

    try:
        await _handle_callback_inner(client, query, user_id, data)
    except Exception as e:
        logger.error(f"Callback error [{data}]: {e}\n{traceback.format_exc()}")
        try:
            await query.answer("❌ An error occurred. Please try again.", show_alert=True)
        except Exception:
            pass

    try:
        await query.answer()
    except Exception:
        pass

async def _handle_callback_inner(client, query: CallbackQuery, user_id: int, data: str):
    """Inner callback handler with all logic."""
    msg = query.message

    # ── Cancel ────────────────────────────────────────────────
    if data == "cancel":
        clear_session(user_id)
        await msg.edit_text(
            f"❌ **Cancelled**\n\nWhat would you like to do?",
            reply_markup=main_menu_keyboard(user_id)
        )
        return

    # ── Contact Admin ─────────────────────────────────────────
    if data == "contact_admin":
        support = get_setting("support_username", "KiraFxSupport")
        await query.answer(f"Contact: @{support}", show_alert=True)
        return

    # ── Main Menu Navigation ──────────────────────────────────
    if data == "menu_main":
        await msg.edit_text(
            f"🎬 **{BOT_NAME}**\n\nChoose what you want to do:",
            reply_markup=main_menu_keyboard(user_id)
        )

    elif data == "menu_image":
        await msg.edit_text(
            "📷 **Image Filters**\n\nChoose a filter category:",
            reply_markup=image_category_keyboard()
        )

    elif data == "menu_video":
        await msg.edit_text(
            "🎬 **Video Effects**\n\nChoose an effect category:",
            reply_markup=video_category_keyboard()
        )

    elif data == "menu_timeline":
        tl = get_timeline(user_id)
        steps_count = len(tl.get("steps", []))
        has_media = bool(tl.get("media_path") and os.path.exists(tl.get("media_path") or ""))
        status = f"📂 Media loaded | {steps_count} step(s)" if has_media else "📭 Send media to start"
        await msg.edit_text(
            f"📊 **Timeline Editor**\n\n{status}\n\nLayer multiple effects, then export the final result.",
            reply_markup=timeline_keyboard(user_id)
        )

    elif data == "menu_compress":
        await msg.edit_text(
            "🗜️ **Video Compression**\n\nSend a video first, then choose quality.\n⭐ = Premium only",
            reply_markup=compress_keyboard()
        )

    elif data == "menu_rename":
        set_session(user_id, "mode", "rename")
        await msg.edit_text(
            "✏️ **Rename File**\n\nSend the file you want to rename.",
            reply_markup=cancel_keyboard()
        )

    elif data == "menu_metadata":
        set_session(user_id, "mode", "metadata")
        await msg.edit_text(
            "📝 **Metadata Editor**\n\nSend the media file to edit metadata.",
            reply_markup=cancel_keyboard()
        )

    elif data == "menu_ai":
        await msg.edit_text(
            "🤖 **AI Generation**\n\nChoose what to generate:",
            reply_markup=ai_gen_keyboard()
        )

    elif data == "menu_logo":
        set_session(user_id, "mode", "logo")
        await msg.edit_text(
            "🎨 **Logo Maker**\n\nSend the text for your logo:",
            reply_markup=cancel_keyboard()
        )

    elif data == "menu_premium":
        prem = is_premium(user_id)
        row = get_user(user_id)
        status_str = "⭐ **Active**" if prem else "🆓 **Free**"
        until = str(row.get("premium_until", "N/A") or "N/A")[:10] if row else "N/A"
        await msg.edit_text(
            f"⭐ **KiraFx Premium**\n\n"
            f"**Your status:** {status_str}\n"
            + (f"**Valid until:** {until}\n\n" if prem else "\n")
            + "\n".join(f"{p['emoji']} **{p['label']}** — {p['price']}" for p in PREMIUM_PLANS.values())
            + "\n\n**Benefits:** Unlimited edits • No watermarks • No ads • 4K • Priority queue",
            reply_markup=premium_plans_keyboard()
        )

    elif data == "menu_profile":
        row = get_user(user_id)
        if row:
            try:
                card = make_profile_card(row, is_premium(user_id), is_admin(user_id))
                bio = BytesIO()
                bio.name = "profile.png"
                card.save(bio, "PNG")
                bio.seek(0)
                await client.send_photo(
                    msg.chat.id,
                    photo=bio,
                    caption=(
                        f"👤 **{row['first_name']}**\n"
                        f"Status: {'⭐ Premium' if is_premium(user_id) else '🆓 Free'}\n"
                        f"Edits: {row['total_edits']} | Coins: 🪙{row['coins']}"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
                         InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
                    ])
                )
                await msg.delete()
            except Exception as e:
                await msg.edit_text(
                    f"👤 **{row['first_name']}**\nEdits: {row['total_edits']} | Coins: 🪙{row['coins']}",
                    reply_markup=back_main()
                )

    elif data == "menu_refer":
        row = get_user(user_id)
        try:
            bot_info = await client.get_me()
            link = f"https://t.me/{bot_info.username}?start={user_id}"
        except Exception:
            link = f"https://t.me/KiraFxBot?start={user_id}"
        ref_days = get_setting("referral_premium_days", "3")
        ref_coins = get_setting("referral_coins", "100")
        await msg.edit_text(
            f"🔗 **Refer & Earn**\n\n"
            f"Your link: `{link}`\n\n"
            f"**Per referral:**\n"
            f"• ✅ {ref_days} days Premium\n"
            f"• 🪙 {ref_coins} Coins\n\n"
            f"**Your referrals:** {row['referral_count'] if row else 0}\n"
            f"**Your coins:** 🪙 {row['coins'] if row else 0}",
            reply_markup=back_main()
        )

    elif data == "menu_help":
        await msg.edit_text(
            "📖 **Quick Help**\n\n"
            "• Send a **photo** → choose filters\n"
            "• Send a **video** → choose effects\n"
            "• /timeline — layer multiple effects\n"
            "• /compress — compress video (9 presets)\n"
            "• /logo — generate a custom logo\n"
            "• /txt2img — AI image generation\n"
            "• /premium — view plans & trial\n"
            "• /refer — earn free premium\n"
            "• /help — full help guide\n",
            reply_markup=back_main()
        )

    # ── Premium Plans ─────────────────────────────────────────
    elif data.startswith("buyprem_"):
        plan_key = data[8:]
        plan = PREMIUM_PLANS.get(plan_key)
        if not plan:
            await query.answer("Unknown plan.", show_alert=True)
            return
        support = get_setting("support_username", "KiraFxSupport")
        await msg.edit_text(
            f"{plan['emoji']} **{plan['label']} Plan — {plan['price']}**\n\n"
            f"**Duration:** {plan['days']} days\n"
            f"**Price:** {plan['price']}\n\n"
            f"**To purchase:**\n"
            f"1. Contact @{support}\n"
            f"2. Send payment proof\n"
            f"3. Your premium will be activated!\n\n"
            f"**Your User ID:** `{user_id}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📩 Contact @{support}", url=f"https://t.me/{support}")],
                [InlineKeyboardButton("🎁 Free Trial Instead", callback_data="trial"),
                 InlineKeyboardButton("🔙 Back", callback_data="menu_premium")],
            ])
        )

    elif data == "trial":
        row = get_user(user_id)
        if not row:
            await query.answer("Please /start first.", show_alert=True)
            return
        if row["trial_used"]:
            await query.answer("❌ You've already used your free trial.", show_alert=True)
            return
        if is_premium(user_id):
            await query.answer("✅ You already have premium!", show_alert=True)
            return
        trial_days = int(get_setting("trial_days", "7"))
        add_premium(user_id, trial_days, "trial")
        get_db().execute("UPDATE users SET trial_used=1 WHERE user_id=?", (user_id,))
        get_db().commit()
        await msg.edit_text(
            f"🎉 **{trial_days}-Day Free Trial Activated!**\n\n"
            f"✅ Unlimited edits\n"
            f"✅ No watermarks\n"
            f"✅ No ads\n"
            f"✅ Priority queue\n"
            f"✅ 4K compression unlocked\n\n"
            f"Enjoy your premium experience! ⭐",
            reply_markup=main_menu_keyboard(user_id)
        )

    # ── Image Filters ─────────────────────────────────────────
    elif data.startswith("imgcat_"):
        cat = data[7:]
        await msg.edit_text(
            f"📷 **{cat}**\n\nChoose a filter to apply:",
            reply_markup=image_filter_keyboard(cat)
        )

    elif data.startswith("imgpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await msg.edit_text(
            f"📷 **{cat}** (Page {page+1})\n\nChoose a filter:",
            reply_markup=image_filter_keyboard(cat, page)
        )

    elif data.startswith("imgfilter_"):
        filter_name = data[10:]
        image_path = get_session(user_id, "image_path")
        if not image_path or not os.path.exists(image_path):
            await query.answer("❌ No image found. Please send an image first!", show_alert=True)
            return
        if filter_name in PREMIUM_IMAGE_FILTERS and not is_premium(user_id):
            await query.answer("⭐ This filter requires Premium! Use /premium to upgrade.", show_alert=True)
            return
        if not can_edit(user_id):
            limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
            await query.answer(f"❌ Daily limit reached ({limit}/day). Upgrade to Premium!", show_alert=True)
            return
        filter_label = IMAGE_FILTERS.get(filter_name, filter_name)
        await msg.edit_text(f"⏳ Applying **{filter_label}**...")
        try:
            loop = asyncio.get_running_loop()
            result_img = await loop.run_in_executor(
                executor,
                lambda: apply_image_filter(Image.open(image_path).convert("RGB"), filter_name)
            )
            wm_text = get_setting("watermark_text", "KiraFx")
            if wm_text and not is_premium(user_id):
                result_img = await loop.run_in_executor(
                    executor, lambda: add_watermark(result_img, wm_text)
                )
            out_path = temp_path(".jpg")
            result_img.save(out_path, "JPEG", quality=92)
            await client.send_photo(
                msg.chat.id,
                photo=out_path,
                caption=f"✅ **Filter Applied:** {filter_label}\n{'⭐ Premium – no watermark' if is_premium(user_id) else ''}",
                reply_markup=after_edit_keyboard()
            )
            increment_edits(user_id)
            log_edit(user_id, "image", filter_name)
            await msg.delete()
            os.remove(out_path)
            if should_show_ad(user_id):
                await client.send_message(msg.chat.id, get_random_ad())
        except Exception as e:
            logger.error(f"Image filter callback error: {e}\n{traceback.format_exc()}")
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")

    # ── Video Effects ─────────────────────────────────────────
    elif data.startswith("vidcat_"):
        cat = data[7:]
        await msg.edit_text(
            f"🎬 **{cat}**\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat)
        )

    elif data.startswith("vidpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await msg.edit_text(
            f"🎬 **{cat}** (Page {page+1})\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat, page)
        )

    elif data.startswith("videffect_"):
        effect = data[10:]
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video found. Please send a video first!", show_alert=True)
            return
        if not can_edit(user_id):
            limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
            await query.answer(f"❌ Daily limit reached ({limit}/day). Upgrade to Premium!", show_alert=True)
            return
        timeout = 600 if is_premium(user_id) else 300
        effect_label = VIDEO_EFFECTS.get(effect, effect)
        await msg.edit_text(f"⏳ Applying **{effect_label}**... Please wait.")
        try:
            ext = ".mp3" if effect == "extract_audio" else ".gif" if effect == "extract_gif" else ".mp4"
            out_path = temp_path(ext)
            loop = asyncio.get_running_loop()
            ok, err = await loop.run_in_executor(
                executor,
                lambda: apply_video_effect(video_path, effect, out_path)
            )
            # extract_audio / extract_gif use different paths
            actual_out = out_path.replace(".mp4", ".mp3") if effect == "extract_audio" else \
                          out_path.replace(".mp4", ".gif") if effect == "extract_gif" else out_path
            if not ok or not os.path.exists(actual_out) or os.path.getsize(actual_out) == 0:
                await msg.edit_text(
                    f"❌ Effect failed: {err[:200] if err else 'Empty output'}\n\nTry a different effect.",
                    reply_markup=after_video_keyboard()
                )
                return
            caption = f"✅ **Effect:** {effect_label}"
            if ext == ".mp3":
                await client.send_audio(msg.chat.id, audio=actual_out, caption=caption)
            elif ext == ".gif":
                await client.send_animation(msg.chat.id, animation=actual_out, caption=caption)
            else:
                size_mb = os.path.getsize(actual_out) / (1024 * 1024)
                if size_mb < 50:
                    await client.send_video(msg.chat.id, video=actual_out, caption=caption,
                                            reply_markup=after_video_keyboard())
                else:
                    await client.send_document(msg.chat.id, document=actual_out, caption=caption,
                                               reply_markup=after_video_keyboard())
            increment_edits(user_id)
            log_edit(user_id, "video", effect)
            await msg.delete()
            os.remove(actual_out)
            if should_show_ad(user_id):
                await client.send_message(msg.chat.id, get_random_ad())
        except Exception as e:
            logger.error(f"Video effect callback error: {e}\n{traceback.format_exc()}")
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")

    # ── Compression ───────────────────────────────────────────
    elif data.startswith("compress_"):
        quality = data[9:]
        if quality in PREMIUM_COMPRESS and not is_premium(user_id):
            await query.answer(f"⭐ {quality} compression is Premium only! Use /premium.", show_alert=True)
            return
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video found. Please send a video first!", show_alert=True)
            return
        timeout = 600 if is_premium(user_id) else 300
        await msg.edit_text(f"⏳ Compressing to **{quality}**... This may take a while.")
        try:
            out_path = temp_path(".mp4")
            loop = asyncio.get_running_loop()
            ok, err = await loop.run_in_executor(
                executor, lambda: compress_video(video_path, out_path, quality, timeout)
            )
            if not ok or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                await msg.edit_text(
                    f"❌ Compression failed: {err[:200] if err else 'Empty output'}\n\nTry a lower quality.",
                    reply_markup=compress_keyboard()
                )
                return
            orig_size = os.path.getsize(video_path) / (1024 * 1024)
            new_size = os.path.getsize(out_path) / (1024 * 1024)
            ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
            caption = (
                f"✅ **Compressed to {quality}**\n\n"
                f"📦 Original: `{orig_size:.1f} MB`\n"
                f"✂️ Compressed: `{new_size:.1f} MB`\n"
                f"💾 Saved: `{ratio:.1f}%`"
            )
            if new_size < 50:
                await client.send_video(msg.chat.id, video=out_path, caption=caption)
            else:
                await client.send_document(msg.chat.id, document=out_path, caption=caption)
            increment_edits(user_id)
            log_edit(user_id, "compress", quality)
            await msg.delete()
            os.remove(out_path)
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")

    # ── Timeline Editor ───────────────────────────────────────
    elif data == "tl_add_imgfilter":
        await msg.edit_text(
            "📷 **Timeline — Add Image Filter**\n\nChoose a filter category:",
            reply_markup=image_category_keyboard()
        )
        set_session(user_id, "timeline_filter_mode", True)

    elif data == "tl_add_videffect":
        await msg.edit_text(
            "🎬 **Timeline — Add Video Effect**\n\nChoose an effect category:",
            reply_markup=video_category_keyboard()
        )
        set_session(user_id, "timeline_effect_mode", True)

    elif data == "tl_add_special":
        tl = get_timeline(user_id)
        media_type = tl.get("media_type", "image")
        if media_type == "image":
            await msg.edit_text(
                "✨ **Timeline — Add Special Effect**\n\nChoose a special filter:",
                reply_markup=image_filter_keyboard("✨ Special")
            )
            set_session(user_id, "timeline_filter_mode", True)
        else:
            await msg.edit_text(
                "✨ **Timeline — Add Transition**\n\nChoose a transition effect:",
                reply_markup=video_effect_keyboard("🎭 Transitions")
            )
            set_session(user_id, "timeline_effect_mode", True)

    elif data == "tl_add_speed":
        tl = get_timeline(user_id)
        media_type = tl.get("media_type", "image")
        if media_type != "video":
            await query.answer("⚡ Speed change applies to videos only.", show_alert=True)
            return
        await msg.edit_text(
            "⚡ **Timeline — Change Speed**\n\nChoose speed multiplier:",
            reply_markup=video_effect_keyboard("⚡ Speed")
        )
        set_session(user_id, "timeline_effect_mode", True)

    elif data == "tl_undo":
        removed = undo_timeline_step(user_id)
        if removed:
            tl = get_timeline(user_id)
            await query.answer(f"↩️ Removed: {removed}", show_alert=False)
            await msg.edit_text(
                f"📊 **Timeline**\n\nRemoved: **{removed}**\n{len(tl['steps'])} step(s) remaining.",
                reply_markup=timeline_keyboard(user_id)
            )
        else:
            await query.answer("↩️ Nothing to undo.", show_alert=True)

    elif data == "tl_view":
        tl = get_timeline(user_id)
        steps = tl.get("steps", [])
        if not steps:
            await query.answer("📋 No steps yet.", show_alert=True)
        else:
            text = "📋 **Timeline Steps:**\n\n"
            for i, step in enumerate(steps, 1):
                text += f"{i}. {step['step']}\n"
            await msg.edit_text(text, reply_markup=timeline_keyboard(user_id))

    elif data == "tl_clear":
        clear_timeline(user_id)
        await msg.edit_text(
            "🗑️ **Timeline Cleared**\n\nSend a new photo or video to start again.",
            reply_markup=main_menu_keyboard(user_id)
        )

    elif data == "tl_apply":
        tl = get_timeline(user_id)
        steps = tl.get("steps", [])
        media_path = tl.get("media_path")
        media_type = tl.get("media_type", "image")
        if not steps:
            await query.answer("⚠️ No steps in timeline.", show_alert=True)
            return
        if not media_path or not os.path.exists(media_path):
            await query.answer("❌ Media not found. Please send media again.", show_alert=True)
            return
        filter_names = [s["step"] for s in steps]
        await msg.edit_text(f"⏳ Applying {len(steps)} timeline step(s)...")
        if media_type == "image":
            await apply_image_filters_sequence(client, query.message, media_path, filter_names, user_id)
        else:
            # Apply video effects in sequence
            current_path = media_path
            loop = asyncio.get_running_loop()
            for i, step in enumerate(steps):
                out_path = temp_path(".mp4")
                ok, err = await loop.run_in_executor(
                    executor, lambda s=step["step"], cp=current_path, op=out_path: apply_video_effect(cp, s, op)
                )
                if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    if current_path != media_path:
                        try: os.remove(current_path)
                        except Exception: pass
                    current_path = out_path
                else:
                    break
            if os.path.exists(current_path) and os.path.getsize(current_path) > 0:
                step_names = " → ".join(s["step"] for s in steps)
                size_mb = os.path.getsize(current_path) / (1024*1024)
                if size_mb < 50:
                    await client.send_video(msg.chat.id, video=current_path,
                                            caption=f"✅ **Timeline Applied!**\n\n{step_names}")
                else:
                    await client.send_document(msg.chat.id, document=current_path,
                                               caption=f"✅ **Timeline Applied!**\n\n{step_names}")
                increment_edits(user_id)
                log_edit(user_id, "timeline", step_names)
        await msg.delete()

    elif data == "tl_export":
        await query.answer("💾 Use ▶️ Apply All to export your timeline.", show_alert=True)

    # ── Logo ──────────────────────────────────────────────────
    elif data.startswith("logo_style_"):
        style = data[11:]
        logo_text = get_session(user_id, "logo_text")
        if not logo_text:
            await query.answer("❌ No logo text. Use /logo first.", show_alert=True)
            return
        set_session(user_id, "logo_style", style)
        await msg.edit_text(
            f"🎨 Choose **background** for: **{logo_text}** ({style} style)",
            reply_markup=logo_bg_keyboard(style)
        )

    elif data.startswith("logo_bg_"):
        parts = data[8:].split("_", 1)
        style = parts[0]
        bg = parts[1] if len(parts) > 1 else "dark"
        logo_text = get_session(user_id, "logo_text")
        if not logo_text:
            await query.answer("❌ No logo text.", show_alert=True)
            return
        await msg.edit_text("⏳ Generating logo...")
        try:
            loop = asyncio.get_running_loop()
            img = await loop.run_in_executor(executor, lambda: make_logo(logo_text, style, bg))
            bio = BytesIO()
            bio.name = "logo.png"
            img.save(bio, "PNG")
            bio.seek(0)
            await client.send_photo(
                msg.chat.id,
                photo=bio,
                caption=f"🎨 **Logo Generated!**\nText: {logo_text}\nStyle: {style}\nBackground: {bg}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Make Another", callback_data="menu_logo"),
                     InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
                ])
            )
            await msg.delete()
            clear_session(user_id)
        except Exception as e:
            await msg.edit_text(f"❌ Logo error: {str(e)[:200]}")

    # ── AI Gen ────────────────────────────────────────────────
    elif data == "ai_txt2img":
        set_session(user_id, "mode", "txt2img")
        await msg.edit_text(
            "🖼️ **Text to Image**\n\n"
            "Send your prompt. Prefix with a style:\n"
            "`gradient:`, `neon:`, `gold:`, `dark:`, `fire:`, `ocean:`",
            reply_markup=cancel_keyboard()
        )

    elif data == "ai_txt2vid":
        set_session(user_id, "mode", "txt2vid")
        await msg.edit_text(
            "🎬 **Text to Video**\n\nSend your video prompt:",
            reply_markup=cancel_keyboard()
        )

    elif data == "ai_edit":
        set_session(user_id, "mode", "aiedit_prompt")
        await msg.edit_text(
            "🤖 **AI Edit Prompt**\n\n"
            "Describe the edit you want (e.g., 'make it vintage and warm').\n"
            "Then I'll suggest filters based on your description.",
            reply_markup=cancel_keyboard()
        )

    elif data == "ai_style":
        await msg.edit_text(
            "🎨 **Style Transfer**\n\n"
            "Send a photo, then choose a style to apply:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🖼️ Watercolor", callback_data="imgfilter_watercolor"),
                 InlineKeyboardButton("🖌️ Oil Paint", callback_data="imgfilter_oil_paint")],
                [InlineKeyboardButton("✏️ Sketch", callback_data="imgfilter_sketch"),
                 InlineKeyboardButton("🎭 Cartoon", callback_data="imgfilter_cartoon")],
                [InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
            ])
        )

    # ── Upload type selection ─────────────────────────────────
    elif data == "upload_doc":
        video_path = get_session(user_id, "video_path") or get_session(user_id, "edit_result_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No file found to upload.", show_alert=True)
            return
        await msg.edit_text("⬆️ Uploading as document...")
        try:
            await client.send_document(msg.chat.id, document=video_path,
                                       caption="✅ **Here's your file!**",
                                       reply_markup=after_video_keyboard())
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Upload error: {str(e)[:200]}")

    elif data == "upload_vid":
        video_path = get_session(user_id, "video_path") or get_session(user_id, "edit_result_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No file found to upload.", show_alert=True)
            return
        await msg.edit_text("⬆️ Uploading as video...")
        try:
            await client.send_video(msg.chat.id, video=video_path,
                                    caption="✅ **Here's your video!**",
                                    reply_markup=after_video_keyboard())
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Upload error: {str(e)[:200]}")

    # ── Rename / Metadata do ──────────────────────────────────
    elif data in ("do_rename", "do_metadata"):
        rename_path = get_session(user_id, "rename_path")
        if not rename_path or not os.path.exists(rename_path):
            await query.answer("❌ No file found.", show_alert=True)
            return
        if data == "do_rename":
            set_session(user_id, "mode", "rename")
            await msg.edit_text(
                "✏️ Type the **new filename** (with extension):",
                reply_markup=cancel_keyboard()
            )
        else:
            set_session(user_id, "mode", "metadata")
            set_session(user_id, "metadata_path", rename_path)
            await show_metadata_menu(client, msg)

    # ── Admin Panel ───────────────────────────────────────────
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        uptime_secs = int(time.time() - START_TIME)
        h = uptime_secs // 3600
        m = (uptime_secs % 3600) // 60
        await msg.edit_text(
            f"🔑 **Admin Panel** — {BOT_NAME}\n\n"
            f"👥 Users: `{get_user_count()}`\n"
            f"⭐ Premium: `{get_premium_count()}`\n"
            f"✂️ Total Edits: `{get_total_edits()}`\n"
            f"⏱️ Uptime: `{h:02d}h {m:02d}m`\n"
            f"💻 CPU: `{psutil.cpu_percent():.1f}%` | RAM: `{psutil.virtual_memory().percent:.1f}%`",
            reply_markup=admin_panel_keyboard()
        )

    elif data == "admin_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        uptime_secs = int(time.time() - START_TIME)
        h = uptime_secs // 3600
        m = (uptime_secs % 3600) // 60
        s = uptime_secs % 60
        await msg.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"👥 Total Users: {get_user_count()}\n"
            f"⭐ Premium: {get_premium_count()}\n"
            f"👑 Admins: {get_admin_count()}\n"
            f"🚫 Banned: {get_banned_count()}\n"
            f"✂️ Total Edits: {get_total_edits()}\n"
            f"📅 Today's Edits: {get_today_edits()}\n"
            f"🆕 New Today: {get_today_new_users()}\n"
            f"⏱️ Uptime: {h:02d}h {m:02d}m {s:02d}s\n"
            f"💻 CPU: {psutil.cpu_percent():.1f}%\n"
            f"🧠 RAM: {psutil.virtual_memory().percent:.1f}%\n"
            f"🔧 FFmpeg: {'✅' if check_ffmpeg() else '❌'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_users":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        users = get_db().execute(
            "SELECT user_id, first_name, username, total_edits, is_premium, is_admin, is_banned FROM users ORDER BY joined_at DESC LIMIT 15"
        ).fetchall()
        text = "👥 **Recent Users:**\n\n"
        for u in users:
            badge = "👑" if u["is_admin"] else ("⭐" if u["is_premium"] else ("🚫" if u["is_banned"] else "🆓"))
            text += f"{badge} `{u['user_id']}` {u['first_name']} @{u['username'] or 'N/A'} — {u['total_edits']} edits\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
        ]]))

    elif data == "admin_broadcast_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_broadcast_input", True)
        await msg.edit_text(
            "📢 **Broadcast Message**\n\n"
            "Type the message to send to all users.\n"
            "Supports Markdown formatting.",
            reply_markup=cancel_keyboard()
        )

    elif data == "admin_backup":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_path)
        await client.send_document(
            msg.chat.id,
            document=backup_path,
            caption=f"💾 Database Backup — {datetime.now().strftime('%Y-%m-%d %H:%M')}\nUsers: {get_user_count()}"
        )
        os.remove(backup_path)
        await query.answer("✅ Backup sent!", show_alert=False)

    elif data == "admin_cleanup":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        cleanup_temp_files(0)
        cleanup_sessions()
        await query.answer("✅ Cleanup done!", show_alert=True)

    elif data == "admin_logs":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        if os.path.exists(LOG_FILE):
            await client.send_document(msg.chat.id, document=LOG_FILE, caption="📋 Bot Logs")
        else:
            await query.answer("❌ Log file not found.", show_alert=True)

    elif data == "admin_settings":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        watermark = get_setting("watermark_text", "KiraFx")
        free_edits = get_setting("free_edits_per_day", "6")
        ads = "✅" if get_setting("ads_enabled") == "1" else "❌"
        maint = "🔧 ON" if get_setting("maintenance_mode") == "1" else "✅ OFF"
        await msg.edit_text(
            f"⚙️ **Bot Settings**\n\n"
            f"🖊️ Watermark: `{watermark}`\n"
            f"🔢 Free Edits/Day: `{free_edits}`\n"
            f"📡 Ads: {ads}\n"
            f"🔧 Maintenance: {maint}\n",
            reply_markup=admin_settings_keyboard()
        )

    elif data == "admin_maintenance":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        current = get_setting("maintenance_mode", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("maintenance_mode", new_val)
        status = "🔧 Maintenance ON" if new_val == "1" else "✅ Maintenance OFF"
        await query.answer(status, show_alert=True)

    elif data == "admin_premium_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        await msg.edit_text(
            f"💎 **Premium Management**\n\n"
            f"Total Premium Users: {get_premium_count()}\n",
            reply_markup=admin_premium_keyboard()
        )

    elif data == "aprem_list":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute(
            "SELECT user_id, first_name, premium_until, premium_plan FROM users WHERE is_premium=1 LIMIT 20"
        ).fetchall()
        text = f"⭐ **Premium Users ({len(rows)}):**\n\n"
        for r in rows:
            until = str(r["premium_until"] or "Lifetime")[:10]
            text += f"• `{r['user_id']}` {r['first_name']} — {r['premium_plan'] or 'N/A'} until {until}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Premium Mgmt", callback_data="admin_premium_menu")
        ]]))

    elif data == "aprem_expiring":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        week_later = (datetime.now() + timedelta(days=7)).isoformat()
        rows = get_db().execute(
            "SELECT user_id, first_name, premium_until FROM users WHERE is_premium=1 AND premium_until IS NOT NULL AND premium_until < ? ORDER BY premium_until",
            (week_later,)
        ).fetchall()
        if not rows:
            await query.answer("✅ No users expiring within 7 days.", show_alert=True)
            return
        text = "⏱️ **Expiring Premium (within 7 days):**\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — expires {str(r['premium_until'])[:10]}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Premium Mgmt", callback_data="admin_premium_menu")
        ]]))

    elif data == "admin_ads_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        ads_on = get_setting("ads_enabled", "0") == "1"
        interval = get_setting("ads_interval", "5")
        ads_shown = get_db().execute("SELECT COUNT(*) FROM ads_shown").fetchone()[0]
        await msg.edit_text(
            f"📡 **Ads Manager**\n\n"
            f"Status: {'✅ Enabled' if ads_on else '❌ Disabled'}\n"
            f"Interval: Every {interval} edits\n"
            f"Total Ads Shown: {ads_shown}\n"
            f"Available Ad Banners: {len(GOOGLE_ADS)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Enable Ads" if not ads_on else "❌ Disable Ads",
                                      callback_data="aset_toggle_ads")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
            ])
        )

    elif data == "aset_toggle_ads":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        current = get_setting("ads_enabled", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("ads_enabled", new_val)
        status = "✅ Ads enabled" if new_val == "1" else "❌ Ads disabled"
        await query.answer(status, show_alert=True)

    elif data == "aset_watermark":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "watermark_text")
        await msg.edit_text("🖊️ Send the new watermark text:", reply_markup=cancel_keyboard())

    elif data == "aset_free_edits":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "free_edits_per_day")
        await msg.edit_text("🔢 Send the new number of free edits per day:", reply_markup=cancel_keyboard())

    elif data == "aset_welcome":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "welcome_message")
        await msg.edit_text("📢 Send the new welcome message:", reply_markup=cancel_keyboard())

    elif data == "aset_support":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "support_username")
        await msg.edit_text("🔗 Send the new support Telegram username:", reply_markup=cancel_keyboard())

    elif data == "aset_group_mode":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        current = get_setting("group_only_mode", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("group_only_mode", new_val)
        await query.answer(f"Group mode: {'ON' if new_val == '1' else 'OFF'}", show_alert=True)

    elif data == "aset_file_size":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "max_file_size_mb")
        await msg.edit_text("📊 Send the new **max file size in MB** (e.g. 50):", reply_markup=cancel_keyboard())

    elif data == "aset_channel":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        set_session(user_id, "admin_setting_input", "channel_username")
        await msg.edit_text("📣 Send the **channel username** (e.g. KiraFxBot):", reply_markup=cancel_keyboard())

    elif data == "admin_manage_admins":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        admins = get_db().execute("SELECT user_id, title, level FROM admins ORDER BY level DESC LIMIT 20").fetchall()
        text = f"👑 **Admin List ({len(admins)}):**\n\n"
        for a in admins:
            text += f"• `{a['user_id']}` — {a['title']} (Level {a['level']})\n"
        text += "\nUse /addadmin [id] [title] [level] and /rmadmin [id]"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
        ]]))

    elif data == "admin_export":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        settings = {r[0]: r[1] for r in get_db().execute("SELECT key, value FROM settings").fetchall()}
        config = {
            "exported_at": datetime.now().isoformat(),
            "user_count": get_user_count(),
            "premium_count": get_premium_count(),
            "total_edits": get_total_edits(),
            "settings": settings,
        }
        export_path = temp_path(".json")
        with open(export_path, "w") as f:
            json.dump(config, f, indent=2)
        await client.send_document(msg.chat.id, document=export_path, caption="📤 Config Export")
        os.remove(export_path)
        await query.answer("✅ Export sent!", show_alert=False)

    elif data == "admin_growth":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        today_users = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (today+"%",)).fetchone()[0]
        week_users = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (week_ago,)).fetchone()[0]
        month_users = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (month_ago,)).fetchone()[0]
        await msg.edit_text(
            f"📈 **Growth Statistics**\n\n"
            f"Today: +{today_users} users\n"
            f"This Week: +{week_users} users\n"
            f"This Month: +{month_users} users\n"
            f"Total: {get_user_count()} users\n\n"
            f"Today's Edits: {get_today_edits()}\n"
            f"Total Edits: {get_total_edits()}\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_queue":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        queue_size = len(list(job_queue.queue.queue))
        sessions_count = len(user_sessions)
        await msg.edit_text(
            f"🗂️ **Queue Status**\n\n"
            f"Active Jobs in Queue: {queue_size}\n"
            f"Active Sessions: {sessions_count}\n"
            f"Thread Pool Size: 6 workers\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_restart":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        if user_id != OWNER_ID:
            await query.answer("❌ Only owner can restart.", show_alert=True)
            return
        await query.answer("🔄 Restarting...", show_alert=True)
        await client.send_message(msg.chat.id, "🔄 Bot is restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    elif data == "admin_notes":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute("SELECT * FROM bot_notes ORDER BY created_at DESC LIMIT 10").fetchall()
        if not rows:
            await msg.edit_text("📭 No notes saved. Use /note [title] [content]",
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin", callback_data="admin_panel")]]))
        else:
            text = "📋 **Bot Notes:**\n\n"
            for r in rows:
                text += f"**#{r['id']} {r['title']}**\n{r['content'][:80]}...\n\n"
            await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin", callback_data="admin_panel")]]))

    elif data == "admin_gen_links":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        try:
            bot_info = await client.get_me()
            start_link = f"https://t.me/{bot_info.username}"
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        except Exception:
            start_link = "https://t.me/KiraFxBot"
            ref_link = f"https://t.me/KiraFxBot?start={user_id}"
        await msg.edit_text(
            f"🔗 **Generated Links:**\n\n"
            f"**Bot Start Link:**\n`{start_link}`\n\n"
            f"**Your Referral Link:**\n`{ref_link}`\n\n"
            f"**Share with users to invite them!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_notifications":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        await msg.edit_text(
            "🔔 **Notification Center**\n\nUse /broadcast to send a message to all users.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Send Broadcast", callback_data="admin_broadcast_menu")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
            ])
        )

    elif data == "admin_run_code":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        perms = get_admin_perms(user_id)
        if user_id != OWNER_ID and (not perms or not perms.get("can_run_code", 0)):
            await query.answer("❌ You don't have code execution permission.", show_alert=True)
            return
        await msg.edit_text(
            "💻 **Code Execution**\n\nUse: `/runcode [python code]`\n\nExample:\n`/runcode print(get_user_count())`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_edit_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        custom_cmds = get_db().execute("SELECT COUNT(*) FROM custom_commands").fetchone()[0]
        auto_replies = get_db().execute("SELECT COUNT(*) FROM auto_replies").fetchone()[0]
        timelines = get_db().execute("SELECT COUNT(*) FROM timeline_sessions").fetchone()[0]
        await msg.edit_text(
            f"📊 **Edit Statistics**\n\n"
            f"Custom Commands: {custom_cmds}\n"
            f"Auto-Replies: {auto_replies}\n"
            f"Active Timelines: {timelines}\n"
            f"Total Edits: {get_total_edits()}\n"
            f"Today's Edits: {get_today_edits()}\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_custom_cmds":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        cmds = get_db().execute("SELECT command, response_type, is_enabled FROM custom_commands LIMIT 15").fetchall()
        text = f"📝 **Custom Commands ({len(cmds)}):**\n\n"
        for c in cmds:
            status = "✅" if c["is_enabled"] else "❌"
            text += f"{status} `/{c['command']}` [{c['response_type']}]\n"
        text += "\nUse /addcmd, /delcmd, /togglecmd, /listcmds"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_auto_replies":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute("SELECT trigger, match_type, is_enabled FROM auto_replies LIMIT 15").fetchall()
        text = f"🤖 **Auto-Replies ({len(rows)}):**\n\n"
        for r in rows:
            status = "✅" if r["is_enabled"] else "❌"
            text += f"{status} `{r['trigger']}` ({r['match_type']})\n"
        text += "\nUse /addautoreply, /delautoreply, /listautoreplies"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_coins_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        total_coins = get_db().execute("SELECT SUM(coins) FROM users").fetchone()[0] or 0
        await msg.edit_text(
            f"💰 **Coins Management**\n\n"
            f"Total Coins in Circulation: {total_coins}\n\n"
            "Commands:\n"
            "• /addcoins [id] [amount]\n"
            "• /rmcoins [id] [amount]",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data == "admin_ban_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        banned = get_banned_count()
        await msg.edit_text(
            f"🚫 **Ban Manager**\n\n"
            f"Banned Users: {banned}\n\n"
            "Commands:\n"
            "• /ban [id] [reason] [days]\n"
            "• /unban [id]\n"
            "• /banlist",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )

    elif data.startswith("quick_ban_"):
        target_id = int(data[10:])
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        db = get_db()
        db.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", ("Admin action", target_id))
        db.commit()
        await query.answer(f"✅ User {target_id} banned.", show_alert=True)

    elif data.startswith("quick_addprem_"):
        target_id = int(data[14:])
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        add_premium(target_id, 30, "admin_quick")
        await query.answer(f"✅ 30 days premium added to {target_id}.", show_alert=True)

    elif data == "aprem_add":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        await msg.edit_text(
            "➕ **Add Premium**\n\nUse command:\n`/addprem [user_id] [days] [plan_name]`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Premium Mgmt", callback_data="admin_premium_menu")]])
        )

    elif data == "aprem_remove":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        await msg.edit_text(
            "➖ **Remove Premium**\n\nUse command:\n`/rmprem [user_id]`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Premium Mgmt", callback_data="admin_premium_menu")]])
        )

    elif data == "aprem_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        txns = get_db().execute("SELECT plan, COUNT(*) as cnt FROM premium_transactions GROUP BY plan").fetchall()
        text = f"📊 **Premium Transactions:**\n\n"
        for t in txns:
            text += f"• {t['plan']}: {t['cnt']} users\n"
        text += f"\nTotal Premium: {get_premium_count()}"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Premium Mgmt", callback_data="admin_premium_menu")]]))

    # ── New 70+ Admin Panel Callbacks ────────────────────────
    elif data == "admin_top_users":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute(
            "SELECT user_id, first_name, username, total_edits FROM users ORDER BY total_edits DESC LIMIT 15"
        ).fetchall()
        text = "🏆 **Top Users by Edits:**\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. `{r['user_id']}` {r['first_name']} @{r['username'] or 'N/A'} — {r['total_edits']} edits\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_active_users":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        rows = get_db().execute(
            "SELECT user_id, first_name, username, last_seen FROM users WHERE last_seen >= ? ORDER BY last_seen DESC LIMIT 15",
            (day_ago,)
        ).fetchall()
        text = f"🟢 **Active Users (Last 24h): {len(rows)}**\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — {str(r['last_seen'])[:16]}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_disk_usage":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        disk = psutil.disk_usage("/")
        temp_size = sum(f.stat().st_size for f in Path(TEMP_DIR).iterdir() if f.is_file()) / (1024*1024)
        db_size = os.path.getsize(DB_PATH) / (1024*1024) if os.path.exists(DB_PATH) else 0
        log_size = os.path.getsize(LOG_FILE) / (1024*1024) if os.path.exists(LOG_FILE) else 0
        await msg.edit_text(
            f"💽 **Disk Usage**\n\n"
            f"Total: {disk.total / (1024**3):.1f} GB\n"
            f"Used: {disk.used / (1024**3):.1f} GB ({disk.percent}%)\n"
            f"Free: {disk.free / (1024**3):.1f} GB\n\n"
            f"Temp Files: {temp_size:.2f} MB\n"
            f"Database: {db_size:.2f} MB\n"
            f"Log File: {log_size:.2f} MB",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_db_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        db = get_db()
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        text = "🗃️ **Database Statistics**\n\n"
        for t in tables:
            count = db.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0]
            text += f"• `{t['name']}`: {count} rows\n"
        db_size = os.path.getsize(DB_PATH) / (1024*1024) if os.path.exists(DB_PATH) else 0
        text += f"\nTotal DB Size: {db_size:.2f} MB"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_warnings_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        try:
            total_warns = get_db().execute("SELECT COUNT(*) FROM user_warnings").fetchone()[0]
        except Exception:
            total_warns = 0
        await msg.edit_text(
            f"⚠️ **Warning System**\n\n"
            f"Total Active Warnings: {total_warns}\n\n"
            f"Commands:\n"
            f"• /warnuser [id] [reason]\n"
            f"• /warnlist [id]\n"
            f"• /clearwarn [id]",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_mute_menu":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        try:
            muted = get_db().execute("SELECT COUNT(*) FROM users WHERE is_muted=1").fetchone()[0]
        except Exception:
            muted = 0
        await msg.edit_text(
            f"🔇 **Mute Manager**\n\n"
            f"Currently Muted: {muted}\n\n"
            f"Commands:\n"
            f"• /muteuser [id] [hours]\n"
            f"• /unmuteuser [id]\n"
            f"• /mutelist",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_coin_leader":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute(
            "SELECT user_id, first_name, username, coins FROM users ORDER BY coins DESC LIMIT 15"
        ).fetchall()
        text = "🏅 **Coin Leaderboard:**\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. `{r['user_id']}` {r['first_name']} — 🪙 {r['coins']}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_analytics":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        total = get_user_count()
        prem = get_premium_count()
        banned = get_banned_count()
        free = max(0, total - prem - banned)
        avg_edits = get_db().execute("SELECT AVG(total_edits) FROM users").fetchone()[0] or 0
        top_editor = get_db().execute("SELECT first_name, total_edits FROM users ORDER BY total_edits DESC LIMIT 1").fetchone()
        await msg.edit_text(
            f"📉 **User Analytics**\n\n"
            f"Total Users: {total}\n"
            f"├ Free: {free}\n"
            f"├ Premium: {prem}\n"
            f"└ Banned: {banned}\n\n"
            f"Avg Edits per User: {avg_edits:.1f}\n"
            f"Top Editor: {top_editor['first_name'] if top_editor else 'N/A'} ({top_editor['total_edits'] if top_editor else 0} edits)\n"
            f"Premium Rate: {(prem/total*100 if total else 0):.1f}%",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_deploy_status":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        uptime_secs = int(time.time() - START_TIME)
        h, m, s = uptime_secs // 3600, (uptime_secs % 3600) // 60, uptime_secs % 60
        await msg.edit_text(
            f"🚀 **Deployment Status**\n\n"
            f"Bot Status: 🟢 Online\n"
            f"Uptime: `{h:02d}h {m:02d}m {s:02d}s`\n"
            f"Flask Dashboard: 🟢 Port {FLASK_PORT}\n"
            f"Keep-Alive: 🟢 Active (every 60s)\n"
            f"FFmpeg: {'🟢 Ready' if check_ffmpeg() else '🔴 Not Found'}\n"
            f"Database: 🟢 Connected\n"
            f"CPU: {psutil.cpu_percent():.1f}%\n"
            f"RAM: {psutil.virtual_memory().percent:.1f}%\n\n"
            f"Use /deploy for full deploy options.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
            ]))

    elif data == "admin_security":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        banned = get_banned_count()
        try:
            warns = get_db().execute("SELECT COUNT(*) FROM user_warnings").fetchone()[0]
        except Exception:
            warns = 0
        maintenance = "🔧 ON" if get_setting("maintenance_mode") == "1" else "✅ OFF"
        await msg.edit_text(
            f"🔐 **Security Overview**\n\n"
            f"Maintenance Mode: {maintenance}\n"
            f"Banned Users: {banned}\n"
            f"Active Warnings: {warns}\n"
            f"Owner ID: `{OWNER_ID}`\n"
            f"Admin Count: {get_admin_count()}\n\n"
            f"Commands:\n"
            f"• /ban, /unban, /banlist\n"
            f"• /warnuser, /clearwarn\n"
            f"• /muteuser, /unmuteuser\n"
            f"• /maintenance",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_sessions":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        sessions_count = len(user_sessions)
        modes = {}
        for uid, sess in user_sessions.items():
            m = sess.get("mode")
            if m:
                modes[m] = modes.get(m, 0) + 1
        mode_text = "\n".join(f"  • {k}: {v}" for k, v in modes.items()) or "  (none active)"
        await msg.edit_text(
            f"📦 **Session Info**\n\n"
            f"Active Sessions: {sessions_count}\n\n"
            f"Active Modes:\n{mode_text}\n\n"
            f"Queue Jobs: {len(list(job_queue.queue.queue))}\n"
            f"Thread Workers: 6",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    elif data == "admin_filter_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        rows = get_db().execute(
            "SELECT filter_name, COUNT(*) as cnt FROM edit_history GROUP BY filter_name ORDER BY cnt DESC LIMIT 15"
        ).fetchall()
        text = "🎯 **Most Used Filters/Effects:**\n\n"
        for r in rows:
            text += f"• `{r['filter_name']}`: {r['cnt']} uses\n"
        if not rows:
            text += "No edit history yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))

    else:
        await query.answer("⚠️ Unknown action.", show_alert=True)

# ============================================================
# FLASK WEB DASHBOARD
# ============================================================
flask_app = Flask(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KiraFx Bot Dashboard</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:'Segoe UI',sans-serif;background:#0a0a15;color:#e0e0ff;min-height:100vh}
        .header{background:linear-gradient(135deg,#12122a,#1e0a40);padding:18px 28px;display:flex;
                align-items:center;justify-content:space-between;border-bottom:1px solid #2d1b69;
                position:sticky;top:0;z-index:10}
        .header-left h1{font-size:1.4rem;color:#a78bfa;display:flex;align-items:center;gap:8px}
        .header-left .sub{font-size:0.78rem;color:#777;margin-top:2px}
        .online-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;
                    animation:pulse 2s infinite}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
        .container{max-width:1280px;margin:0 auto;padding:24px 18px}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}
        .stat-card{background:#111125;border:1px solid #1f1f40;border-radius:12px;padding:18px;text-align:center;
                   transition:transform 0.2s,border-color 0.2s}
        .stat-card:hover{transform:translateY(-2px);border-color:#4c2d9c}
        .stat-card .value{font-size:1.8rem;font-weight:700;color:#a78bfa}
        .stat-card .label{font-size:0.78rem;color:#666;margin-top:4px;text-transform:uppercase;letter-spacing:0.05em}
        .bar{height:6px;background:#1f1f40;border-radius:3px;overflow:hidden;margin-top:8px}
        .bar-fill{height:100%;background:linear-gradient(90deg,#6d28d9,#a78bfa);border-radius:3px;transition:width 1s}
        .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
        .section{background:#111125;border:1px solid #1f1f40;border-radius:12px;padding:20px;margin-bottom:16px}
        .section h2{color:#a78bfa;margin-bottom:14px;font-size:1rem;display:flex;align-items:center;gap:6px}
        table{width:100%;border-collapse:collapse}
        th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #1a1a32;font-size:0.84rem}
        th{color:#7c5cbf;font-weight:600;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em}
        td{color:#bbb}
        tr:hover td{background:#15152a}
        .badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:600}
        .b-prem{background:#3d1d70;color:#a78bfa}
        .b-free{background:#1a3a28;color:#4ade80}
        .b-banned{background:#3b1a1a;color:#f87171}
        .b-admin{background:#3d2c00;color:#fbbf24}
        .b-owner{background:#3d0030;color:#f472b6}
        .ok{color:#22c55e}.err{color:#f87171}
        .refresh-bar{display:flex;justify-content:space-between;align-items:center;
                     font-size:0.76rem;color:#555;margin-bottom:12px}
        .logo{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#4b0082,#9400d3);
              display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;
              color:#fff;flex-shrink:0}
        @media(max-width:600px){.stats-grid{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
    </style>
    <script>
        let countdown = 30;
        function tick(){
            countdown--;
            const el = document.getElementById('cdown');
            if(el) el.textContent = countdown + 's';
            if(countdown <= 0) location.reload();
        }
        setInterval(tick, 1000);
        window.onload = () => {
            const el = document.getElementById('lrt');
            if(el) el.textContent = new Date().toLocaleTimeString();
        };
    </script>
</head>
<body>
<div class="header">
    <div class="header-left" style="display:flex;align-items:center;gap:12px">
        <div class="logo">Kx</div>
        <div>
            <h1><span class="online-dot"></span> KiraFx Dashboard</h1>
            <div class="sub">{{ bot_name }} • v{{ version }}</div>
        </div>
    </div>
    <div style="text-align:right;font-size:0.76rem;color:#555">
        <div>Refreshing in <span id="cdown">30</span></div>
        <div>Last refresh: <span id="lrt">-</span></div>
    </div>
</div>
<div class="container">
    <div class="refresh-bar">
        <span>📊 Live Statistics</span>
        <span>Auto-refresh every 30s</span>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="value">{{ stats.total_users }}</div>
            <div class="label">Total Users</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.premium_users }}</div>
            <div class="label">Premium</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.banned_users }}</div>
            <div class="label">Banned</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.total_edits }}</div>
            <div class="label">Total Edits</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.today_edits }}</div>
            <div class="label">Today's Edits</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.today_users }}</div>
            <div class="label">New Today</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.uptime }}</div>
            <div class="label">Uptime</div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.cpu }}%</div>
            <div class="label">CPU</div>
            <div class="bar"><div class="bar-fill" style="width:{{ stats.cpu }}%"></div></div>
        </div>
        <div class="stat-card">
            <div class="value">{{ stats.mem }}%</div>
            <div class="label">RAM</div>
            <div class="bar"><div class="bar-fill" style="width:{{ stats.mem }}%"></div></div>
        </div>
    </div>
    <div class="grid2">
        <div class="section">
            <h2>🔧 System Status</h2>
            <table>
                <tr><td>FFmpeg</td><td class="{{ 'ok' if stats.ffmpeg else 'err' }}">{{ '✅ Installed' if stats.ffmpeg else '❌ Not Found' }}</td></tr>
                <tr><td>Database</td><td class="ok">✅ Connected</td></tr>
                <tr><td>Maintenance</td><td>{{ '🔧 ON' if stats.maintenance else '✅ OFF' }}</td></tr>
                <tr><td>Ads</td><td>{{ '✅ ON' if stats.ads_enabled else '❌ OFF' }}</td></tr>
                <tr><td>Free Edits/Day</td><td>{{ stats.free_edits }}</td></tr>
                <tr><td>Keep-Alive</td><td class="ok">✅ Active (60s)</td></tr>
            </table>
        </div>
        <div class="section">
            <h2>🎬 Bot Capabilities</h2>
            <table>
                <tr><td>Image Filters</td><td>{{ stats.image_filters }}+</td></tr>
                <tr><td>Video Effects</td><td>{{ stats.video_effects }}+</td></tr>
                <tr><td>Premium Plans</td><td>{{ stats.premium_plans }}</td></tr>
                <tr><td>Compression Presets</td><td>{{ stats.comp_presets }}</td></tr>
                <tr><td>Logo Styles</td><td>{{ stats.logo_styles }}</td></tr>
                <tr><td>AI Styles</td><td>{{ stats.ai_styles }}</td></tr>
            </table>
        </div>
    </div>
    <div class="section">
        <h2>👥 Recent Users</h2>
        <table>
            <thead>
                <tr><th>ID</th><th>Name</th><th>Status</th><th>Edits</th><th>Coins</th><th>Joined</th></tr>
            </thead>
            <tbody>
            {% for u in users %}
            <tr>
                <td><code>{{ u.user_id }}</code></td>
                <td>{{ u.first_name }} {% if u.username %}<span style="color:#666">@{{ u.username }}</span>{% endif %}</td>
                <td>
                    {% if u.user_id == owner_id %}<span class="badge b-owner">Owner</span>
                    {% elif u.is_banned %}<span class="badge b-banned">Banned</span>
                    {% elif u.is_admin %}<span class="badge b-admin">Admin</span>
                    {% elif u.is_premium %}<span class="badge b-prem">Premium</span>
                    {% else %}<span class="badge b-free">Free</span>{% endif %}
                </td>
                <td>{{ u.total_edits }}</td>
                <td>🪙 {{ u.coins }}</td>
                <td>{{ u.joined_at[:10] }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>"""

@flask_app.route("/")
def dashboard():
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    users = get_db().execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT 25").fetchall()
    stats = {
        "total_users": get_user_count(),
        "premium_users": get_premium_count(),
        "banned_users": get_banned_count(),
        "total_edits": get_total_edits(),
        "today_edits": get_today_edits(),
        "today_users": get_today_new_users(),
        "uptime": f"{h:02d}h {m:02d}m {s:02d}s",
        "cpu": round(psutil.cpu_percent(), 1),
        "mem": round(psutil.virtual_memory().percent, 1),
        "ffmpeg": check_ffmpeg(),
        "maintenance": get_setting("maintenance_mode") == "1",
        "free_edits": get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY)),
        "ads_enabled": get_setting("ads_enabled") == "1",
        "image_filters": len(IMAGE_FILTERS),
        "video_effects": len(VIDEO_EFFECTS),
        "premium_plans": len(PREMIUM_PLANS),
        "comp_presets": len(COMPRESSION_PRESETS),
        "logo_styles": len(LOGO_STYLES),
        "ai_styles": len(AI_TEXT_IMAGE_STYLES),
    }
    return render_template_string(
        DASHBOARD_HTML,
        stats=stats,
        users=users,
        bot_name=BOT_NAME,
        version=BOT_VERSION,
        owner_id=OWNER_ID,
    )

@flask_app.route("/api/stats")
def api_stats():
    uptime_secs = int(time.time() - START_TIME)
    return jsonify({
        "bot_name": BOT_NAME,
        "version": BOT_VERSION,
        "total_users": get_user_count(),
        "premium_users": get_premium_count(),
        "banned_users": get_banned_count(),
        "total_edits": get_total_edits(),
        "today_edits": get_today_edits(),
        "uptime_seconds": uptime_secs,
        "ffmpeg": check_ffmpeg(),
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "maintenance": get_setting("maintenance_mode") == "1",
    })

@flask_app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": BOT_NAME, "version": BOT_VERSION, "uptime": int(time.time() - START_TIME)})

@flask_app.route("/api/users")
def api_users():
    limit = int(flask_request.args.get("limit", 20))
    users = get_db().execute(f"SELECT user_id, first_name, username, is_premium, total_edits FROM users ORDER BY joined_at DESC LIMIT {limit}").fetchall()
    return jsonify([dict(u) for u in users])

def run_flask():
    """Run Flask web dashboard in a daemon thread."""
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)

# ============================================================
# KEEP-ALIVE (fast — every 60 seconds)
# ============================================================
def keep_alive_ping():
    """Ping health endpoint every 60 seconds to stay alive."""
    while True:
        try:
            req_lib.get(f"http://localhost:{FLASK_PORT}/health", timeout=10)
        except Exception:
            pass
        # Also ping external URL if configured
        if KEEP_ALIVE_URL:
            try:
                req_lib.get(KEEP_ALIVE_URL, timeout=10)
            except Exception:
                pass
        time.sleep(60)

def temp_cleanup_loop():
    """Periodic temp file cleanup every 30 minutes."""
    while True:
        time.sleep(1800)
        cleanup_temp_files(1800)
        cleanup_sessions()

# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    logger.info(f"=" * 60)
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION}")
    logger.info(f"=" * 60)

    # Init database
    init_db()

    # Check FFmpeg
    if check_ffmpeg():
        logger.info("FFmpeg found ✅")
    else:
        logger.warning("FFmpeg NOT found ❌ — Video features will be limited")

    # Start Flask dashboard
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask dashboard started on port {FLASK_PORT}")

    # Start keep-alive thread (pings every 60s)
    ka_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ka_thread.start()
    logger.info("Keep-alive started (every 60s)")

    # Start temp cleanup thread
    cleanup_thread = threading.Thread(target=temp_cleanup_loop, daemon=True)
    cleanup_thread.start()

    logger.info("Starting Telegram bot...")
    app.run()

if __name__ == "__main__":
    main()
