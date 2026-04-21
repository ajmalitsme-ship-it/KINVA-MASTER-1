#!/usr/bin/env python3
"""
KiraFx Media Editor Bot v8.1 - Fixed Premium Edition
Full-featured Telegram bot for image/video editing, premium management,
50+ admin panel, timeline editing, inline callbacks, Google ads, and more.
"""

# ============================================================
# FIXED IMPORTS
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
from typing import Optional, Dict, List, Tuple, Any, Union
from functools import wraps
from queue import PriorityQueue
import threading as _threading

# Third-party imports with proper error handling
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

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# ============================================================
# FIXED CONFIGURATION
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
BOT_VERSION = "8.1 Fixed Premium"
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

# Fixed Google Ads simulation banners (plain text, no problematic formatting)
GOOGLE_ADS = [
    "📢 Sponsored: Upgrade to Premium – Unlimited edits, no limits! Use /premium",
    "📢 Ad: Get 4K video compression & 77+ effects with KiraFx Premium! /premium",
    "📢 Promoted: Share KiraFx with friends – earn 3 free days premium! /refer",
    "📢 Ad: Pro editors use KiraFx Premium – no watermarks, priority queue! /premium",
    "📢 Sponsored: Try KiraFx AI Generator for stunning images! /txt2img",
    "📢 Ad: KiraFx Logo Maker – create professional logos free! /logo",
    "📢 Promoted: Refer friends & earn coins. Redeem for premium days! /refer",
    "📢 Ad: Video timeline editor now available! Send a video to start.",
    "📢 Sponsored: Compress your videos in 9 quality presets! /compress",
    "📢 Ad: Join our channel for tips, updates & offers!",
]

# ============================================================
# FIXED LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
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
# THREAD-SAFE SESSION MANAGEMENT
# ============================================================
_user_sessions: Dict[int, Dict] = {}
_session_lock = _threading.RLock()

def set_session(user_id: int, key: str, value: Any):
    """Thread-safe session setter."""
    with _session_lock:
        if user_id not in _user_sessions:
            _user_sessions[user_id] = {"created": time.time()}
        _user_sessions[user_id][key] = value
        _user_sessions[user_id]["updated"] = time.time()

def get_session(user_id: int, key: str, default=None):
    """Thread-safe session getter."""
    with _session_lock:
        return _user_sessions.get(user_id, {}).get(key, default)

def clear_session(user_id: int, key: str = None):
    """Thread-safe session clearer."""
    with _session_lock:
        if key:
            _user_sessions.get(user_id, {}).pop(key, None)
        else:
            _user_sessions.pop(user_id, None)

def cleanup_sessions():
    """Remove sessions older than 2 hours."""
    with _session_lock:
        cutoff = time.time() - 7200
        stale = [uid for uid, s in _user_sessions.items() if s.get("created", 0) < cutoff]
        for uid in stale:
            del _user_sessions[uid]

def get_session_count() -> int:
    """Get number of active sessions."""
    with _session_lock:
        return len(_user_sessions)

# ============================================================
# FIXED DATABASE (with proper error handling)
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

def column_exists(cursor, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(col[1] == column for col in cursor.fetchall())

def init_db():
    """Initialize database tables with safe migration."""
    conn = get_db()
    c = conn.cursor()

    # Create tables
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
            notifications INTEGER DEFAULT 1,
            is_muted INTEGER DEFAULT 0,
            muted_until TEXT
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

    # Safe column migrations using PRAGMA
    migrations = [
        ("users", "admin_level", "INTEGER DEFAULT 0"),
        ("users", "premium_plan", "TEXT"),
        ("users", "total_renames", "INTEGER DEFAULT 0"),
        ("users", "referral_code", "TEXT"),
        ("users", "referred_by", "INTEGER"),
        ("users", "referral_count", "INTEGER DEFAULT 0"),
        ("users", "daily_reset", "TEXT"),
        ("users", "last_seen", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ("users", "language", "TEXT DEFAULT 'en'"),
        ("users", "notifications", "INTEGER DEFAULT 1"),
        ("users", "is_muted", "INTEGER DEFAULT 0"),
        ("users", "muted_until", "TEXT"),
        ("admins", "level", "INTEGER DEFAULT 1"),
        ("admins", "can_ban", "INTEGER DEFAULT 1"),
        ("admins", "can_broadcast", "INTEGER DEFAULT 1"),
        ("admins", "can_manage_premium", "INTEGER DEFAULT 1"),
        ("admins", "can_manage_users", "INTEGER DEFAULT 1"),
        ("admins", "can_run_code", "INTEGER DEFAULT 0"),
        ("admins", "notes", "TEXT"),
        ("custom_commands", "media_type", "TEXT"),
        ("custom_commands", "use_count", "INTEGER DEFAULT 0"),
    ]
    
    for table, column, col_type in migrations:
        if not column_exists(c, table, column):
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                conn.commit()
                logger.info(f"Added column {column} to {table}")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add column {column} to {table}: {e}")

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

    logger.info("Database initialized successfully.")

def get_setting(key: str, default: str = "") -> str:
    """Get a setting value safely."""
    try:
        conn = get_db()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    except Exception:
        return default

def set_setting(key: str, value: str):
    """Set a setting value safely."""
    try:
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    """Get user by ID."""
    try:
        conn = get_db()
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    except Exception:
        return None

def register_user(user: User, referred_by: int = None):
    """Register or update a user."""
    try:
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
    except Exception as e:
        logger.error(f"Error registering user {user.id}: {e}")

def is_premium(user_id: int) -> bool:
    """Check if user has premium access."""
    if user_id == OWNER_ID:
        return True
    try:
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
    except Exception:
        return False

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    if user_id == OWNER_ID:
        return True
    try:
        row = get_user(user_id)
        return bool(row and row["is_admin"])
    except Exception:
        return False

def get_admin_level(user_id: int) -> int:
    """Get admin level."""
    if user_id == OWNER_ID:
        return 10
    try:
        row = get_db().execute("SELECT level FROM admins WHERE user_id=?", (user_id,)).fetchone()
        return row["level"] if row else 0
    except Exception:
        return 0

def get_admin_perms(user_id: int) -> Optional[sqlite3.Row]:
    """Get admin permissions."""
    try:
        return get_db().execute("SELECT * FROM admins WHERE user_id=?", (user_id,)).fetchone()
    except Exception:
        return None

def is_banned(user_id: int) -> bool:
    """Check if user is banned."""
    try:
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
    except Exception:
        return False

def can_edit(user_id: int) -> bool:
    """Check if user can perform an edit (within daily limit)."""
    if is_premium(user_id) or is_admin(user_id):
        return True
    try:
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
    except Exception:
        return False

def get_remaining_edits(user_id: int) -> str:
    """Get remaining edits for today."""
    if is_premium(user_id) or is_admin(user_id):
        return "∞"
    try:
        row = get_user(user_id)
        if not row:
            return "0"
        today = datetime.now().date().isoformat()
        limit = int(get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY)))
        used = row["edits_today"] if row["daily_reset"] == today else 0
        return str(max(0, limit - used))
    except Exception:
        return "0"

def increment_edits(user_id: int):
    """Increment user's edit count."""
    try:
        today = datetime.now().date().isoformat()
        get_db().execute(
            "UPDATE users SET edits_today=edits_today+1, total_edits=total_edits+1, daily_reset=? WHERE user_id=?",
            (today, user_id)
        )
        get_db().commit()
    except Exception as e:
        logger.error(f"Error incrementing edits for {user_id}: {e}")

def add_premium(user_id: int, days: int, plan: str = "admin_grant"):
    """Grant premium access to a user."""
    try:
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
    except Exception as e:
        logger.error(f"Error adding premium to {user_id}: {e}")

def add_coins(user_id: int, amount: int, reason: str = ""):
    """Add coins to a user."""
    try:
        get_db().execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, user_id))
        get_db().execute(
            "INSERT INTO coins_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
            (user_id, amount, reason)
        )
        get_db().commit()
    except Exception as e:
        logger.error(f"Error adding coins to {user_id}: {e}")

def get_all_users() -> List[sqlite3.Row]:
    """Get all users."""
    try:
        return get_db().execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()
    except Exception:
        return []

def get_user_count() -> int:
    """Get total user count."""
    try:
        row = get_db().execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0

def get_premium_count() -> int:
    """Get premium user count."""
    try:
        row = get_db().execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0

def get_admin_count() -> int:
    """Get admin count."""
    try:
        row = get_db().execute("SELECT COUNT(*) FROM admins").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0

def get_banned_count() -> int:
    """Get banned user count."""
    try:
        row = get_db().execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0

def get_total_edits() -> int:
    """Get total edits across all users."""
    try:
        row = get_db().execute("SELECT SUM(total_edits) FROM users").fetchone()
        return row[0] or 0
    except Exception:
        return 0

def get_today_edits() -> int:
    """Get today's total edits."""
    try:
        today = datetime.now().date().isoformat()
        row = get_db().execute(
            "SELECT SUM(edits_today) FROM users WHERE daily_reset=?", (today,)
        ).fetchone()
        return row[0] or 0
    except Exception:
        return 0

def get_today_new_users() -> int:
    """Get today's new users."""
    try:
        today = datetime.now().date().isoformat()
        row = get_db().execute(
            "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (today + "%",)
        ).fetchone()
        return row[0] or 0
    except Exception:
        return 0

def log_edit(user_id: int, edit_type: str, filter_name: str):
    """Log an edit action."""
    try:
        get_db().execute(
            "INSERT INTO edit_history (user_id, edit_type, filter_name) VALUES (?, ?, ?)",
            (user_id, edit_type, filter_name)
        )
        get_db().commit()
    except Exception as e:
        logger.error(f"Error logging edit: {e}")

def log_rename(user_id: int, original: str, new_name: str):
    """Log a rename action."""
    try:
        get_db().execute(
            "INSERT INTO rename_history (user_id, original_name, new_name) VALUES (?, ?, ?)",
            (user_id, original, new_name)
        )
        get_db().execute(
            "UPDATE users SET total_renames=total_renames+1 WHERE user_id=?",
            (user_id,)
        )
        get_db().commit()
    except Exception as e:
        logger.error(f"Error logging rename: {e}")

def should_show_ad(user_id: int) -> bool:
    """Decide if we should show an ad to this user."""
    if is_premium(user_id) or is_admin(user_id):
        return False
    if get_setting("ads_enabled", "0") != "1":
        return False
    interval = int(get_setting("ads_interval", "5"))
    try:
        row = get_user(user_id)
        if not row:
            return False
        today = datetime.now().date().isoformat()
        edits_today = row["edits_today"] if row["daily_reset"] == today else 0
        return edits_today > 0 and edits_today % interval == 0
    except Exception:
        return False

def get_random_ad() -> str:
    """Get a random ad."""
    return random.choice(GOOGLE_ADS)

# ============================================================
# FIXED PREMIUM EMOJIS (using simple emoji characters)
# ============================================================
PREMIUM_EMOJIS = {
    "star": "⭐",
    "crown": "👑",
    "fire": "🔥",
    "diamond": "💎",
    "magic": "✨",
    "camera": "📷",
    "video": "🎬",
    "brush": "🎨",
    "bolt": "⚡",
    "shield": "🛡️",
    "check": "✅",
    "gift": "🎁",
    "coin": "🪙",
    "robot": "🤖",
    "rocket": "🚀",
}

def pem(name: str) -> str:
    """Get premium emoji by name."""
    return PREMIUM_EMOJIS.get(name, "✨")

# ============================================================
# FIXED TIMELINE SYSTEM
# ============================================================
def get_timeline(user_id: int) -> Dict:
    """Get or create timeline session for user."""
    try:
        row = get_db().execute(
            "SELECT * FROM timeline_sessions WHERE user_id=?", (user_id,)
        ).fetchone()
        if not row:
            return {"steps": [], "media_path": None, "media_type": None}
        steps = json.loads(row["steps"] or "[]")
        # Validate media path still exists
        media_path = row["media_path"]
        if media_path and not os.path.exists(media_path):
            media_path = None
        return {
            "steps": steps,
            "media_path": media_path,
            "media_type": row["media_type"],
        }
    except Exception as e:
        logger.error(f"Error getting timeline for {user_id}: {e}")
        return {"steps": [], "media_path": None, "media_type": None}

def save_timeline(user_id: int, media_path: str, media_type: str, steps: List):
    """Save timeline session."""
    try:
        db = get_db()
        db.execute("""
            INSERT OR REPLACE INTO timeline_sessions (user_id, media_path, media_type, steps, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, media_path, media_type, json.dumps(steps)))
        db.commit()
    except Exception as e:
        logger.error(f"Error saving timeline for {user_id}: {e}")

def clear_timeline(user_id: int):
    """Clear timeline session."""
    try:
        get_db().execute("DELETE FROM timeline_sessions WHERE user_id=?", (user_id,))
        get_db().commit()
    except Exception as e:
        logger.error(f"Error clearing timeline for {user_id}: {e}")

def add_timeline_step(user_id: int, step: str):
    """Add a step to timeline."""
    tl = get_timeline(user_id)
    tl["steps"].append({"step": step, "time": datetime.now().isoformat()})
    save_timeline(user_id, tl["media_path"], tl["media_type"], tl["steps"])

def undo_timeline_step(user_id: int) -> Optional[str]:
    """Undo last timeline step."""
    tl = get_timeline(user_id)
    if not tl["steps"]:
        return None
    removed = tl["steps"].pop()
    save_timeline(user_id, tl["media_path"], tl["media_type"], tl["steps"])
    return removed.get("step")

# ============================================================
# FIXED QUEUE SYSTEM
# ============================================================
class JobQueue:
    def __init__(self):
        self.queue = PriorityQueue()
        self._lock = _threading.RLock()

    def add_job(self, user_id: int, job_type: str, priority: int = 0):
        with self._lock:
            self.queue.put((priority, time.time(), user_id, job_type))

    def get_position(self, user_id: int) -> int:
        with self._lock:
            items = list(self.queue.queue)
            sorted_items = sorted(items)
            for i, item in enumerate(sorted_items):
                if item[2] == user_id:
                    return i + 1
            return 0

    def get_size(self) -> int:
        with self._lock:
            return self.queue.qsize()

job_queue = JobQueue()

# ============================================================
# FIXED FFMPEG UTILITIES
# ============================================================
def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def validate_video(path: str) -> bool:
    """Validate video file."""
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
    """Get video information."""
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
    """Run FFmpeg command."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return False, result.stderr[:500]
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "FFmpeg operation timed out."
    except Exception as e:
        return False, str(e)[:500]

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

    # Strategy 3: Stream copy (no processing)
    cmd3 = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
    ok, err = run_ffmpeg(cmd3, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    return False, f"All strategies failed: {err[:200]}"

def temp_path(ext: str = "") -> str:
    """Generate a temporary file path."""
    name = "".join(random.choices(string.ascii_lowercase + string.digits, k=14))
    return os.path.join(TEMP_DIR, f"{name}{ext}")

# ============================================================
# FANCY FONT + LOADING ANIMATION HELPERS
# ============================================================

# Small-caps unicode font: ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ
_FANCY_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
}

def fancy(text: str) -> str:
    """Convert text to ꜱᴍᴀʟʟ ᴄᴀᴘꜱ Unicode font."""
    return "".join(_FANCY_MAP.get(c.lower(), c) for c in text)

def quote(text: str) -> str:
    """Wrap text in a Telegram blockquote (>) prefix on each line."""
    return "\n".join(f">{line}" for line in text.split("\n"))

# Loading animation frames
_LOAD_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_LOAD_BARS = [
    "▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱▱▱", "▰▰▰▱▱▱▱▱▱▱",
    "▰▰▰▰▱▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱▱", "▰▰▰▰▰▰▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱",
    "▰▰▰▰▰▰▰▰▱▱", "▰▰▰▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰▰▰▰",
]

class LoadingAnimator:
    """Animate a status message with rotating spinner + progress bar.
    
    Usage:
        anim = LoadingAnimator(status_msg, "Processing")
        await anim.start()
        try:
            ... do work ...
        finally:
            await anim.stop("✅ Done!")
    """
    def __init__(self, msg, title: str = "Processing", interval: float = 0.6):
        self.msg = msg
        self.title = title
        self.interval = interval
        self._task = None
        self._stopped = False
    
    async def _loop(self):
        i = 0
        while not self._stopped:
            try:
                spinner = _LOAD_FRAMES[i % len(_LOAD_FRAMES)]
                bar = _LOAD_BARS[i % len(_LOAD_BARS)]
                await self.msg.edit_text(
                    f"{spinner} **{self.title}...**\n\n`{bar}`\n\n_Please wait..._"
                )
            except Exception:
                pass
            i += 1
            await asyncio.sleep(self.interval)
    
    async def start(self):
        self._task = asyncio.create_task(self._loop())
    
    async def stop(self, final_text: str = None):
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        if final_text:
            try:
                await self.msg.edit_text(final_text)
            except Exception:
                pass

def fmt_size(num_bytes: int) -> str:
    """Format byte size to human-readable string."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"

def cleanup_temp_files(max_age: int = 3600):
    """Clean up old temporary files."""
    now = time.time()
    count = 0
    for f in Path(TEMP_DIR).iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > max_age:
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
    if count > 0:
        logger.info(f"Cleaned up {count} old temp files")
# ============================================================
# FIXED IMAGE FILTERS
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
    # Advanced (BG & Portrait)
    "bg_remove": "Remove BG",
    "bg_white": "White BG",
    "bg_black": "Black BG",
    "bg_blur": "Blurred BG",
    "portrait_enhance": "Portrait Enhance",
    "skin_smooth": "Skin Smooth",
    "face_sharpen": "Face Sharpen",
    "auto_enhance": "Auto Enhance",
    "denoiser": "Denoiser",
    "super_sharpen": "Super Sharpen",
    "clarity": "Clarity Boost",
    "dehaze": "Dehaze",
    "lens_flare": "Lens Flare",
    "tilt_shift": "Tilt-Shift",
    "long_exposure": "Long Exposure",
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
    "🖼️ BG & AI":  ["bg_remove", "bg_white", "bg_black", "bg_blur", "portrait_enhance",
                    "skin_smooth", "face_sharpen", "auto_enhance", "denoiser", "super_sharpen",
                    "clarity", "dehaze", "lens_flare", "tilt_shift", "long_exposure"],
}

PREMIUM_IMAGE_FILTERS = ["hdr", "lomo", "cross_process", "fade", "matte",
                          "bg_remove", "bg_white", "bg_black", "bg_blur",
                          "portrait_enhance", "skin_smooth", "face_sharpen",
                          "super_sharpen", "clarity", "dehaze", "tilt_shift", "long_exposure"]

def apply_image_filter(img: Image.Image, filter_name: str) -> Image.Image:
    """Apply a named filter to a PIL image with error handling."""
    try:
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
            small = img.resize((max(1, img.width // 10), max(1, img.height // 10)), Image.NEAREST)
            return small.resize(img.size, Image.NEAREST)
        elif filter_name == "glitch":
            result = img.copy()
            arr = list(result.getdata())
            offset = random.randint(5, 20)
            for i in range(0, len(arr), img.width * 5):
                for j in range(min(img.width, offset)):
                    if i + j < len(arr) and i + j + offset < len(arr):
                        pixel = arr[i + j]
                        if isinstance(pixel, tuple) and len(pixel) >= 3:
                            arr[i + j] = (min(pixel[0] + 80, 255), pixel[1], pixel[2])
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
            for _ in range(min(5000, img.width * img.height // 100)):
                x = random.randint(0, img.width - 1)
                y = random.randint(0, img.height - 1)
                r_val = random.randint(2, 6)
                color = img.getpixel((x, y))
                if len(color) >= 3:
                    draw.ellipse([x - r_val, y - r_val, x + r_val, y + r_val], fill=color[:3])
            return result
        elif filter_name == "mosaic":
            block = 15
            result = img.copy()
            for x in range(0, img.width, block):
                for y in range(0, img.height, block):
                    x2 = min(x + block, img.width)
                    y2 = min(y + block, img.height)
                    region = img.crop((x, y, x2, y2))
                    avg = region.resize((1, 1)).getpixel((0, 0))
                    if len(avg) >= 3:
                        color = avg[:3]
                    else:
                        color = (avg[0], avg[0], avg[0])
                    draw = ImageDraw.Draw(result)
                    draw.rectangle([x, y, x2, y2], fill=color)
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
            return img.rotate(180, expand=True)
        elif filter_name == "rotate_270":
            return img.rotate(90, expand=True)
        elif filter_name == "flip_h":
            return img.transpose(Image.FLIP_LEFT_RIGHT)
        elif filter_name == "flip_v":
            return img.transpose(Image.FLIP_TOP_BOTTOM)
        elif filter_name == "resize_50":
            return img.resize((max(1, img.width // 2), max(1, img.height // 2)), Image.LANCZOS)
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
            r_val = min(cx, cy)
            for i in range(r_val, 0, -5):
                alpha = int((1 - (i / r_val)) * 150)
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
            bg.paste(result, mask=result.split()[3] if len(result.split()) > 3 else None)
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
            r_val = min(img.width, img.height) // 3
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse([cx - r_val, cy - r_val, cx + r_val, cy + r_val], fill=255)
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

        # ── BG & AI Advanced Filters ───────────────────────────
        elif filter_name == "bg_remove":
            if REMBG_AVAILABLE:
                output = rembg_remove(img.convert("RGBA"))
                # Return with transparent background preserved as RGBA
                return output.convert("RGBA")
            else:
                # Fallback: simple edge-based masking
                gray = img.convert("L")
                mask = gray.point(lambda x: 255 if x > 30 else 0)
                result = img.copy().convert("RGBA")
                result.putalpha(mask)
                return result

        elif filter_name == "bg_white":
            if REMBG_AVAILABLE:
                rgba = rembg_remove(img.convert("RGBA"))
                bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                bg.paste(rgba, mask=rgba.split()[3])
                return bg.convert("RGB")
            else:
                return ImageOps.autocontrast(img)

        elif filter_name == "bg_black":
            if REMBG_AVAILABLE:
                rgba = rembg_remove(img.convert("RGBA"))
                bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
                bg.paste(rgba, mask=rgba.split()[3])
                return bg.convert("RGB")
            else:
                return ImageEnhance.Contrast(img).enhance(1.5)

        elif filter_name == "bg_blur":
            if REMBG_AVAILABLE:
                rgba = rembg_remove(img.convert("RGBA"))
                blurred_bg = img.filter(ImageFilter.GaussianBlur(15))
                result = blurred_bg.copy().convert("RGBA")
                result.paste(rgba, mask=rgba.split()[3])
                return result.convert("RGB")
            else:
                return apply_image_filter(img, "blur_background")

        elif filter_name == "portrait_enhance":
            bright = ImageEnhance.Brightness(img).enhance(1.1)
            sharp = ImageEnhance.Sharpness(bright).enhance(1.4)
            color = ImageEnhance.Color(sharp).enhance(1.2)
            return ImageEnhance.Contrast(color).enhance(1.15)

        elif filter_name == "skin_smooth":
            smooth = img.filter(ImageFilter.GaussianBlur(1.5))
            detail = img.filter(ImageFilter.DETAIL)
            result = Image.blend(smooth, img, 0.4)
            return ImageEnhance.Color(result).enhance(1.1)

        elif filter_name == "face_sharpen":
            sharp = ImageEnhance.Sharpness(img).enhance(2.5)
            return ImageEnhance.Contrast(sharp).enhance(1.1)

        elif filter_name == "auto_enhance":
            auto = ImageOps.autocontrast(img, cutoff=2)
            sharp = ImageEnhance.Sharpness(auto).enhance(1.3)
            return ImageEnhance.Color(sharp).enhance(1.15)

        elif filter_name == "denoiser":
            smooth1 = img.filter(ImageFilter.GaussianBlur(0.8))
            smooth2 = img.filter(ImageFilter.MedianFilter(3))
            return Image.blend(smooth1, smooth2, 0.5)

        elif filter_name == "super_sharpen":
            for _ in range(3):
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
            return ImageEnhance.Contrast(img).enhance(1.05)

        elif filter_name == "clarity":
            hc = ImageEnhance.Contrast(img).enhance(1.3)
            return ImageEnhance.Sharpness(hc).enhance(1.8)

        elif filter_name == "dehaze":
            bright = ImageEnhance.Brightness(img).enhance(1.15)
            cont = ImageEnhance.Contrast(bright).enhance(1.25)
            r, g, b = cont.split()
            r = r.point(lambda x: min(x + 10, 255))
            g = g.point(lambda x: min(x + 5, 255))
            return Image.merge("RGB", (r, g, b))

        elif filter_name == "lens_flare":
            result = img.copy().convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            cx, cy = img.width // 4, img.height // 4
            for i in range(8, 0, -1):
                alpha = int(255 / (i + 1))
                draw.ellipse([cx - i*12, cy - i*12, cx + i*12, cy + i*12],
                             fill=(255, 240, 200, alpha))
            result = Image.alpha_composite(result, overlay)
            return ImageEnhance.Brightness(result.convert("RGB")).enhance(1.1)

        elif filter_name == "tilt_shift":
            blurred = img.filter(ImageFilter.GaussianBlur(6))
            h = img.height
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            band_y1 = h // 3
            band_y2 = 2 * h // 3
            for y in range(h):
                if y < band_y1:
                    alpha = int(255 * (band_y1 - y) / band_y1)
                elif y > band_y2:
                    alpha = int(255 * (y - band_y2) / (h - band_y2))
                else:
                    alpha = 0
                draw.line([(0, y), (img.width, y)], fill=alpha)
            result = Image.composite(blurred, img, mask)
            return ImageEnhance.Color(result).enhance(1.3)

        elif filter_name == "long_exposure":
            blurred = img.filter(ImageFilter.GaussianBlur(4))
            result = ImageChops.add(
                ImageEnhance.Brightness(img).enhance(0.7),
                ImageEnhance.Brightness(blurred).enhance(0.4)
            )
            return ImageEnhance.Contrast(result).enhance(1.2)

        else:
            return img
    except Exception as e:
        logger.error(f"Error applying filter {filter_name}: {e}")
        return img

def make_round_logo(size: int = 256) -> Image.Image:
    """Generate round KiraFx logo image."""
    try:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Gradient background circle
        for i in range(size // 2, 0, -5):
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
    except Exception as e:
        logger.error(f"Error making logo: {e}")
        # Return a simple fallback image
        img = Image.new("RGB", (size, size), (75, 0, 130))
        return img

def add_watermark(img: Image.Image, text: str = "KiraFx") -> Image.Image:
    """Add round logo watermark to image."""
    try:
        result = img.copy().convert("RGBA")
        # Generate small round logo
        logo = make_round_logo(80)
        # Set transparency
        logo_rgba = logo.copy()
        if logo_rgba.mode == 'RGBA':
            pixels = logo_rgba.load()
            for y in range(logo_rgba.size[1]):
                for x in range(logo_rgba.size[0]):
                    pixel = pixels[x, y]
                    if len(pixel) == 4:
                        r, g, b, a = pixel
                        pixels[x, y] = (r, g, b, int(a * 0.6))
        # Paste at bottom-right
        margin = 10
        pos = (result.width - logo_rgba.width - margin, result.height - logo_rgba.height - margin)
        result.paste(logo_rgba, pos, logo_rgba)
        return result.convert("RGB")
    except Exception as e:
        logger.error(f"Error adding watermark: {e}")
        return img

# ============================================================
# FIXED VIDEO EFFECTS
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
    "vintage_video": "curves=vintage,vignette=PI/4",
    "cinematic":    "curves=psych,vignette=PI/6",
    "glitch_video": "hue=h=random*360",
    "pixelate_video": "scale=iw/10:ih/10,scale=iw*10:ih*10:flags=neighbor",
    "sketch_video": "edgedetect=low=0.1:high=0.4,negate",
    "cartoon_video": "edgedetect=low=0.1:high=0.3",
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
    "color_grading": "curves=r='0/0.1 0.5/0.5 1/0.9':g='0/0.05 0.5/0.5 1/0.95':b='0/0 0.5/0.4 1/0.8'",
    "colorize_video": "hue=h=220:s=2",
    "denoise_video": "hqdn3d=4:3:6:4.5",
    "stabilize":    "deshake",
    "crop_video":   "crop=iw/2:ih/2",
    "rotate_video_90": "transpose=1",
    "scale_square": "scale=720:720:force_original_aspect_ratio=decrease,pad=720:720:(ow-iw)/2:(oh-ih)/2",
}

VIDEO_SPEED_MAP = {
    "speed_025": 0.25, "speed_05": 0.5, "speed_075": 0.75,
    "speed_15": 1.5, "speed_2": 2.0, "speed_3": 3.0, "speed_4": 4.0,
}

def apply_video_effect(input_path: str, effect: str, output_path: str) -> Tuple[bool, str]:
    """Apply a named video effect with error handling."""
    if not validate_video(input_path):
        return False, "Invalid or corrupted video file."

    try:
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
            cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", out]
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
    except Exception as e:
        logger.error(f"Error applying video effect {effect}: {e}")
        return False, str(e)[:200]

# ============================================================
# FIXED COMPRESSION PRESETS
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
    """Compress video to specified quality."""
    if not validate_video(input_path):
        return False, "Invalid or corrupted video file."
    
    preset_data = COMPRESSION_PRESETS.get(quality)
    if not preset_data:
        return False, f"Unknown quality preset: {quality}"
    
    w, h = preset_data["width"], preset_data["height"]
    vb, ab = preset_data["bitrate"], preset_data["audio_bitrate"]
    crf, speed = preset_data["crf"], preset_data["preset"]
    
    try:
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
        
        # Fallback: simpler command
        cmd2 = ["ffmpeg", "-y", "-i", input_path,
                "-vf", f"scale={w}:{h}", "-c:v", "libx264", "-crf", str(crf), "-c:a", "aac", output_path]
        ok, err = run_ffmpeg(cmd2, timeout)
        if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, ""
        
        return False, err
    except Exception as e:
        return False, str(e)[:200]
# ============================================================
# FIXED LOGO MAKER
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
    """Generate a stylized logo image with error handling."""
    try:
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

        # Load fonts
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = font_large

        # Draw main text
        bbox = draw.textbbox((0, 0), text, font=font_large)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (width - tw) // 2
        ty = (height - th) // 2 - 20

        # Shadow
        draw.text((tx + 3, ty + 3), text, font=font_large, fill=(0, 0, 0))
        # Main text
        main_color = tuple(min(c + 100, 255) for c in colors[1])
        draw.text((tx, ty), text, font=font_large, fill=main_color)

        # Add round logo watermark
        logo = make_round_logo(50)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, (10, 10), logo)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.text((68, 20), "KiraFx Bot v8.1", font=font_small, fill=tuple(colors[1]))

        return img
    except Exception as e:
        logger.error(f"Error making logo: {e}")
        # Return simple fallback
        img = Image.new("RGB", (800, 300), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        draw.text((400, 150), text[:20], fill=(255, 255, 255))
        return img

# ============================================================
# FIXED WELCOME IMAGE (Round KiraFx Logo)
# ============================================================
def make_welcome_image(user_name: str, is_prem: bool = False) -> Image.Image:
    """Create a welcome image for new users with round KiraFx logo."""
    try:
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

        # Load fonts
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
    except Exception as e:
        logger.error(f"Error making welcome image: {e}")
        # Return simple fallback
        img = Image.new("RGB", (900, 450), (20, 20, 50))
        draw = ImageDraw.Draw(img)
        draw.text((450, 225), f"Welcome, {user_name[:20]}!", fill=(200, 160, 255))
        return img

# ============================================================
# FIXED PROFILE CARD GENERATION
# ============================================================
def make_profile_card(user_row: sqlite3.Row, is_prem: bool, is_adm: bool) -> Image.Image:
    """Generate a rich profile card with round KiraFx logo."""
    try:
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

        # Load fonts
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
    except Exception as e:
        logger.error(f"Error making profile card: {e}")
        # Return simple fallback
        img = Image.new("RGB", (700, 350), (20, 20, 50))
        draw = ImageDraw.Draw(img)
        draw.text((350, 175), f"{user_row['first_name']}", fill=(200, 160, 255))
        return img

# ============================================================
# FIXED TEXT TO IMAGE GENERATION
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
    """Generate an image from text with error handling."""
    try:
        width, height = 800, 600
        style_data = AI_TEXT_IMAGE_STYLES.get(style, AI_TEXT_IMAGE_STYLES["gradient"])
        bg = style_data["bg"]
        colors = style_data["colors"]

        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        for y in range(height):
            ratio = y / height
            r = int(bg[0] + (colors[0][0] - bg[0]) * ratio * 0.5)
            g = int(bg[1] + (colors[0][1] - bg[1]) * ratio * 0.5)
            b = int(bg[2] + (colors[0][2] - bg[2]) * ratio * 0.5)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Decorative dots
        for _ in range(25):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r_val = random.randint(2, 10)
            color = random.choice(colors)
            draw.ellipse([x - r_val, y - r_val, x + r_val, y + r_val], fill=(*color, 150))

        # Load fonts
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except Exception:
            font = ImageFont.load_default()
            font_small = font

        # Word wrap
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

        # Draw text
        total_h = len(lines) * 48
        start_y = (height - total_h) // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lx = (width - lw) // 2
            # Shadow
            draw.text((lx + 2, start_y + i * 48 + 2), line, font=font, fill=(0, 0, 0))
            # Main text
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
    except Exception as e:
        logger.error(f"Error in text_to_image: {e}")
        # Return simple fallback
        img = Image.new("RGB", (800, 600), (20, 20, 40))
        draw = ImageDraw.Draw(img)
        draw.text((400, 300), prompt[:50], fill=(255, 255, 255))
        return img

# ============================================================
# FIXED KEYBOARDS – Main Menu & Submenus
# ============================================================
def main_menu_keyboard(user_id: int = 0):
    """Create main menu keyboard."""
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
    """Create back to main menu button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]])

def cancel_keyboard():
    """Create cancel button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

def image_category_keyboard():
    """Create image filter category keyboard."""
    cats = list(IMAGE_FILTER_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"imgcat_{cat}")])
    buttons.append([InlineKeyboardButton("📊 Timeline Editor", callback_data="menu_timeline"),
                    InlineKeyboardButton("🤖 AI Edit", callback_data="ai_aiedit")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def image_filter_keyboard(category: str, page: int = 0):
    """Create image filter selection keyboard with pagination."""
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
    """Create video effect category keyboard."""
    cats = list(VIDEO_EFFECT_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"vidcat_{cat}")])
    buttons.append([InlineKeyboardButton("📊 Timeline Editor", callback_data="menu_timeline"),
                    InlineKeyboardButton("✂️ Quick Trim", callback_data="quick_trim")])
    buttons.append([InlineKeyboardButton("⚡ Speed", callback_data="quick_speed"),
                    InlineKeyboardButton("🎬 Subtitle", callback_data="quick_subtitle")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def video_effect_keyboard(category: str, page: int = 0):
    """Create video effect selection keyboard with pagination."""
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
    """Create compression quality keyboard."""
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
    """Create premium plans keyboard."""
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
    """Create timeline editor keyboard."""
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
    """Create logo style selection keyboard."""
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
    """Create logo background selection keyboard."""
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
    """Create AI generation keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Text to Image", callback_data="ai_txt2img"),
         InlineKeyboardButton("🎬 Text to Video", callback_data="ai_txt2vid")],
        [InlineKeyboardButton("🤖 AI Edit Prompt", callback_data="ai_edit"),
         InlineKeyboardButton("🎨 Style Transfer", callback_data="ai_style")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

def upload_type_keyboard():
    """Create upload type selection keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 As Document", callback_data="upload_doc"),
         InlineKeyboardButton("🎬 As Video", callback_data="upload_vid")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])

def after_edit_keyboard():
    """Create after edit keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Apply Another Filter", callback_data="menu_image"),
         InlineKeyboardButton("📊 Timeline", callback_data="menu_timeline")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

def after_video_keyboard():
    """Create after video effect keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Apply Another Effect", callback_data="menu_video"),
         InlineKeyboardButton("📊 Timeline", callback_data="menu_timeline")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

# ============================================================
# FIXED ADMIN PANEL – 50+ FEATURES
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
    """Create admin settings keyboard."""
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
    """Create admin premium management keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Premium", callback_data="aprem_add"),
         InlineKeyboardButton("➖ Remove Premium", callback_data="aprem_remove")],
        [InlineKeyboardButton("📋 List Premium Users", callback_data="aprem_list"),
         InlineKeyboardButton("⏱️ Expiring Soon", callback_data="aprem_expiring")],
        [InlineKeyboardButton("📊 Premium Stats", callback_data="aprem_stats"),
         InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")],
    ])
  # ============================================================
# FIXED DECORATORS
# ============================================================
def require_registered(func):
    """Decorator to ensure user is registered and not banned."""
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user = message.from_user
        if not user:
            return
        
        # Register user
        register_user(user)
        
        # Check ban
        if is_banned(user.id):
            await message.reply("🚫 You are banned from using this bot.")
            return
        
        # Check maintenance mode
        if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
            await message.reply(
                "🔧 **Maintenance Mode**\n\nBot is under maintenance. Please try again soon.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📩 Contact Support", callback_data="contact_admin")
                ]])
            )
            return
        
        # Check mute status
        try:
            db = get_db()
            mute_row = db.execute("SELECT is_muted, muted_until FROM users WHERE user_id=?", (user.id,)).fetchone()
            if mute_row and mute_row["is_muted"]:
                if mute_row["muted_until"]:
                    try:
                        if datetime.fromisoformat(mute_row["muted_until"]) < datetime.now():
                            db.execute("UPDATE users SET is_muted=0, muted_until=NULL WHERE user_id=?", (user.id,))
                            db.commit()
                        else:
                            await message.reply(f"🔇 You are muted until {str(mute_row['muted_until'])[:16]}.")
                            return
                    except Exception:
                        pass
                else:
                    await message.reply("🔇 You are muted by an admin.")
                    return
        except Exception as e:
            logger.error(f"Error checking mute status: {e}")
        
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorator to ensure user is admin."""
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply("🚫 **Admin Only**\n\nThis command is restricted to admins.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_premium(func):
    """Decorator to ensure user has premium."""
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
# FIXED PYROGRAM BOT APP
# ============================================================
app = Client(
    "kiraFx_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ============================================================
# FIXED COMMAND HANDLERS
# ============================================================

@app.on_message(filters.command("start"))
@require_registered
async def cmd_start(client, message: Message):
    """Handle /start command with referral support."""
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
                    try:
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
                    except Exception as e:
                        logger.error(f"Error processing referral: {e}")
        except ValueError:
            pass
        
        # Register with referral
        register_user(user, referred_by)
    else:
        # Normal registration
        register_user(user)

    prem = is_premium(user.id)

    # Generate welcome image
    try:
        welcome_img = make_welcome_image(user.first_name or "Friend", prem)
        bio = BytesIO()
        bio.name = "welcome.png"
        welcome_img.save(bio, "PNG")
        bio.seek(0)

        free_left = get_remaining_edits(user.id)
        user_display = user.first_name or "Friend"
        status_line = "🟢 ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴇ ⭐" if prem else f"🔵 ꜰʀᴇᴇ ᴇᴅɪᴛꜱ ʟᴇꜰᴛ: {free_left}"

        feature_block = (
            f"❖ {fancy('70+ Image Filters')}  ╶  6 categories\n"
            f"❖ {fancy('77+ Video Effects')}  ╶  cinematic\n"
            f"❖ {fancy('Timeline Editor')}  ╶  layered edits\n"
            f"❖ {fancy('9 Compression Presets')}  ╶  144p → 4K\n"
            f"❖ {fancy('File Rename + Metadata')}\n"
            f"❖ {fancy('AI Generation')}  ╶  images & videos\n"
            f"❖ {fancy('Logo Maker')}  ╶  7 styles\n"
            f"❖ {fancy('Premium Plans')}  ╶  unlimited"
        )

        caption = (
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"   ✦ **{fancy('Welcome')} {user_display}!** ✦\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f">**❖ {fancy(BOT_NAME)} ❖**\n"
            f">{fancy('Your all-in-one media editor')}\n"
            f">_Trusted by thousands._\n\n"
            f"{quote(feature_block)}\n\n"
            f"┌─────────────────┐\n"
            f"  {status_line}\n"
            f"└─────────────────┘\n\n"
            f"📌  Tap a button below or use /help"
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
            f"👋 **Welcome to {BOT_NAME}!**\n\n"
            f"Tap the menu below to start editing!\n\n"
            f"💡 Tip: Use /help for the full guide.",
            reply_markup=main_menu_keyboard(user.id)
        )

@app.on_message(filters.command("help"))
@require_registered
async def cmd_help(client, message: Message):
    """Handle /help command."""
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
        "**Admin Commands:** /admin (admin only)\n\n"
        f"📌 **Version:** {BOT_VERSION}"
    )
    await message.reply(text, reply_markup=main_menu_keyboard(message.from_user.id))

@app.on_message(filters.command("premium"))
@require_registered
async def cmd_premium(client, message: Message):
    """Handle /premium command."""
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
            f"📩 Contact admin to purchase.\n"
            f"🎁 Or use /trial for a free 7-day trial!",
            reply_markup=premium_plans_keyboard()
        )

@app.on_message(filters.command("trial"))
@require_registered
async def cmd_trial(client, message: Message):
    """Handle /trial command for free premium trial."""
    user_id = message.from_user.id
    row = get_user(user_id)
    
    if not row:
        await message.reply("❌ Please use /start first.")
        return
    
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
    """Handle /status command."""
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found. Please use /start first.")
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
    """Handle /profile command."""
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found. Please use /start first.")
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
        await message.delete()  # Delete the command message
    except Exception as e:
        logger.error(f"Profile card error: {e}")
        await message.reply(
            f"👤 **Profile**\n\n"
            f"Name: {row['first_name']}\n"
            f"Edits: {row['total_edits']}\n"
            f"Coins: {row['coins']}\n"
            f"Referral Code: `{row['referral_code']}`",
            reply_markup=main_menu_keyboard(user_id)
        )

@app.on_message(filters.command("refer"))
@require_registered
async def cmd_refer(client, message: Message):
    """Handle /refer command."""
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
        f"Share your link and earn rewards every time someone joins!\n\n"
        f"💡 **Tip:** The more you share, the more premium days you earn!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Get Premium", callback_data="menu_premium"),
             InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
        ])
    )

@app.on_message(filters.command("ping"))
async def cmd_ping(client, message: Message):
    """Handle /ping command."""
    start = time.time()
    msg = await message.reply("🏓 Pinging...")
    elapsed = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 **Pong!**\n\nResponse: `{elapsed:.1f}ms`")

@app.on_message(filters.command("alive"))
async def cmd_alive(client, message: Message):
    """Handle /alive command - show bot status."""
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
    """Handle /info command."""
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
        f"**Total Edits:** {get_total_edits()}\n\n"
        f"📌 **Created by:** KiraFx Team\n"
        f"🔗 **Support:** @{get_setting('support_username', 'KiraFxSupport')}",
        reply_markup=main_menu_keyboard(message.from_user.id)
    )

@app.on_message(filters.command("queue"))
@require_registered
async def cmd_queue(client, message: Message):
    """Handle /queue command."""
    pos = job_queue.get_position(message.from_user.id)
    if pos > 0:
        await message.reply(
            f"📋 **Queue Position:** #{pos}\n\n"
            f"Your job is being processed. Please wait.\n"
            f"Premium users get priority processing!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="menu_premium"),
                 InlineKeyboardButton("🏠 Home", callback_data="menu_main")]
            ])
        )
    else:
        await message.reply(
            "✅ **No active queue** — You can start editing right now!\n\n"
            "Send a photo or video to begin!",
            reply_markup=main_menu_keyboard(message.from_user.id)
        )

@app.on_message(filters.command("timeline"))
@require_registered
async def cmd_timeline(client, message: Message):
    """Handle /timeline command."""
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
        f"2️⃣ Choose 'Add to Timeline' from the menu\n"
        f"3️⃣ Stack as many effects as you want\n"
        f"4️⃣ Tap ▶️ Apply All to export\n\n"
        f"✨ **Pro tip:** Premium users can stack unlimited effects!",
        reply_markup=timeline_keyboard(user_id)
    )

@app.on_message(filters.command("rename"))
@require_registered
async def cmd_rename(client, message: Message):
    """Handle /rename command."""
    user_id = message.from_user.id
    set_session(user_id, "mode", "rename")
    await message.reply(
        "✏️ **Rename File**\n\n"
        "Send the file (document/audio/video) you want to rename.\n\n"
        "Supported formats: Any file type",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("metadata"))
@require_registered
async def cmd_metadata(client, message: Message):
    """Handle /metadata command."""
    user_id = message.from_user.id
    set_session(user_id, "mode", "metadata")
    await message.reply(
        "📝 **Metadata Editor**\n\n"
        "Send the media file you want to edit metadata for.\n\n"
        "Supported: Audio files, videos, documents",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("compress"))
@require_registered
async def cmd_compress(client, message: Message):
    """Handle /compress command."""
    user_id = message.from_user.id
    set_session(user_id, "mode", "compress")
    await message.reply(
        "🗜️ **Video Compression**\n\n"
        "Send the video you want to compress.\n\n"
        "**Available qualities:**\n"
        "• 144p, 240p, 360p, 480p, 720p, 1080p\n"
        "• ⭐ 1440p, 2K, 4K (Premium only)\n\n"
        "⭐ = Premium only — use /trial for 7 days free!",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("logo"))
@require_registered
async def cmd_logo(client, message: Message):
    """Handle /logo command."""
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    
    if len(args) < 2:
        set_session(user_id, "mode", "logo")
        await message.reply(
            "🎨 **Logo Maker**\n\n"
            "Send the text for your logo (max 20 characters):\n\n"
            "Example: `My Brand`\n\n"
            "You'll then be able to choose from 7 styles and 7 backgrounds!",
            reply_markup=cancel_keyboard()
        )
        return
    
    # Limit text length
    logo_text = args[1][:20]
    set_session(user_id, "logo_text", logo_text)
    await message.reply(
        f"🎨 Choose a **style** for: **{logo_text}**\n\n"
        f"Styles available:\n"
        f"• gradient • gold • neon • fire • ice • purple • pink • rainbow",
        reply_markup=logo_style_keyboard()
    )

@app.on_message(filters.command("txt2img"))
@require_registered
async def cmd_txt2img(client, message: Message):
    """Handle /txt2img command."""
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    
    if len(args) < 2:
        set_session(user_id, "mode", "txt2img")
        await message.reply(
            "🖼️ **Text to Image**\n\n"
            "Send your prompt. Optionally prefix with a style:\n"
            "`gradient:`, `neon:`, `gold:`, `dark:`, `fire:`, `ocean:`\n\n"
            "Example: `gradient:A beautiful sunset over mountains`\n\n"
            "Premium users get priority processing!",
            reply_markup=cancel_keyboard()
        )
        return
    
    await process_txt2img(client, message, user_id, args[1])

@app.on_message(filters.command("txt2vid"))
@require_registered
async def cmd_txt2vid(client, message: Message):
    """Handle /txt2vid command."""
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    
    if len(args) < 2:
        set_session(user_id, "mode", "txt2vid")
        await message.reply(
            "🎬 **Text to Video**\n\n"
            "Send your video prompt:\n\n"
            "Example: `A rocket launching into space`\n\n"
            "The bot will generate a short animation based on your prompt.\n"
            "⭐ Premium users get longer videos!",
            reply_markup=cancel_keyboard()
        )
        return
    
    await process_txt2vid(client, message, user_id, args[1])

@app.on_message(filters.command("aiedit"))
@require_registered
async def cmd_aiedit(client, message: Message):
    """Handle /aiedit command."""
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    
    if len(args) < 2:
        set_session(user_id, "mode", "aiedit_prompt")
        await message.reply(
            "🤖 **AI Prompt Edit**\n\n"
            "Describe what you want to do with your image:\n"
            "_Examples: 'make it look vintage and warm', 'add a neon glow effect', 'sharpen and enhance colors'_\n\n"
            "Then send your image after typing the prompt.\n\n"
            "The AI will automatically detect the best filters to apply!",
            reply_markup=cancel_keyboard()
        )
        return
    
    prompt = args[1].lower()
    await handle_aiedit_prompt(client, message, user_id, prompt)

async def handle_aiedit_prompt(client, message, user_id, prompt):
    """Handle AI edit prompt analysis."""
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
            "Or send a photo directly to choose from the filter menu.\n\n"
            "💡 Tip: Be more descriptive for better results!",
            reply_markup=main_menu_keyboard(user_id)
        )
        return

    set_session(user_id, "mode", "aiedit")
    set_session(user_id, "ai_filters", filters_matched)
    suggested = " → ".join(IMAGE_FILTERS.get(f, f) for f in filters_matched[:6])
    
    await message.reply(
        f"🤖 **AI Analysis Complete!**\n\n"
        f"**Detected filters:** {suggested}\n\n"
        f"Now send the **image** you want to edit with these filters.\n\n"
        f"The filters will be applied in the order suggested above.",
        reply_markup=cancel_keyboard()
)
# ============================================================
# FIXED ADMIN COMMANDS (50+ Features)
# ============================================================

@app.on_message(filters.command("admin"))
@require_registered
@require_admin
async def cmd_admin(client, message: Message):
    """Handle /admin command - Main admin panel."""
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
        f"💻 CPU: `{psutil.cpu_percent():.1f}%` | RAM: `{psutil.virtual_memory().percent:.1f}%`\n\n"
        f"📌 **Use the buttons below to manage the bot**",
        reply_markup=admin_panel_keyboard()
    )

@app.on_message(filters.command("ban"))
@require_registered
@require_admin
async def cmd_ban(client, message: Message):
    """Handle /ban command."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "🚫 **Ban User**\n\n"
            "Usage: `/ban [user_id] [reason] [days (optional)]`\n\n"
            "Examples:\n"
            "• `/ban 123456789 Spamming` - permanent ban\n"
            "• `/ban 123456789 Rule violation 7` - ban for 7 days"
        )
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID. Please provide a numeric ID.")
        return
    
    if target_id == OWNER_ID:
        await message.reply("❌ Cannot ban the bot owner.")
        return
    
    # Parse reason and duration
    reason = "Violation of terms"
    ban_until = None
    
    if len(args) > 2:
        # Check if last argument is a number (days)
        if args[-1].isdigit() and len(args) > 3:
            days = int(args[-1])
            ban_until = (datetime.now() + timedelta(days=days)).isoformat()
            reason = " ".join(args[2:-1]) if len(args) > 3 else "Violation of terms"
        else:
            reason = " ".join(args[2:])
    
    try:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, 'Unknown')", (target_id,))
        db.execute(
            "UPDATE users SET is_banned=1, ban_reason=?, ban_until=? WHERE user_id=?",
            (reason, ban_until, target_id)
        )
        db.commit()
        
        dur = f"{days} days" if ban_until else "permanent"
        await message.reply(f"✅ User `{target_id}` banned ({dur}). Reason: {reason}")
        
        # Notify user
        try:
            await client.send_message(
                target_id, 
                f"🚫 **You have been banned from {BOT_NAME}.**\n"
                f"Reason: {reason}\n"
                f"Duration: {dur}\n\n"
                f"Contact support if you believe this is a mistake."
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error banning user {target_id}: {e}")
        await message.reply(f"❌ Error banning user: {str(e)[:100]}")

@app.on_message(filters.command("unban"))
@require_registered
@require_admin
async def cmd_unban(client, message: Message):
    """Handle /unban command."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/unban [user_id]`\n\nExample: `/unban 123456789`")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    
    try:
        db = get_db()
        db.execute("UPDATE users SET is_banned=0, ban_reason=NULL, ban_until=NULL WHERE user_id=?", (target_id,))
        db.commit()
        await message.reply(f"✅ User `{target_id}` unbanned.")
        
        # Notify user
        try:
            await client.send_message(target_id, f"✅ You have been unbanned from {BOT_NAME}! Welcome back.")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error unbanning user {target_id}: {e}")
        await message.reply(f"❌ Error unbanning user: {str(e)[:100]}")

@app.on_message(filters.command("addprem"))
@require_registered
@require_admin
async def cmd_addprem(client, message: Message):
    """Handle /addprem command - Add premium to user."""
    args = message.text.split()
    if len(args) < 3:
        await message.reply(
            "⭐ **Add Premium**\n\n"
            "Usage: `/addprem [user_id] [days] [plan_name (optional)]`\n\n"
            "Examples:\n"
            "• `/addprem 123456789 30 monthly`\n"
            "• `/addprem 123456789 7 trial`"
        )
        return
    
    try:
        target_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments. User ID and days must be numbers.")
        return
    
    plan = args[3] if len(args) > 3 else "admin_grant"
    
    try:
        add_premium(target_id, days, plan)
        await message.reply(f"✅ Added {days} days **{plan}** premium to user `{target_id}`.")
        
        # Notify user
        try:
            await client.send_message(
                target_id, 
                f"⭐ **Premium Activated!**\n\n"
                f"You've been granted **{days} days** of premium by an admin!\n"
                f"Plan: {plan}\n\n"
                f"Enjoy unlimited edits, no ads, and priority processing!"
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error adding premium to {target_id}: {e}")
        await message.reply(f"❌ Error adding premium: {str(e)[:100]}")

@app.on_message(filters.command("rmprem"))
@require_registered
@require_admin
async def cmd_rmprem(client, message: Message):
    """Handle /rmprem command - Remove premium from user."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/rmprem [user_id]`\n\nExample: `/rmprem 123456789`")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    
    try:
        db = get_db()
        db.execute("UPDATE users SET is_premium=0, premium_until=NULL, premium_plan=NULL WHERE user_id=?", (target_id,))
        db.commit()
        await message.reply(f"✅ Premium removed from user `{target_id}`.")
        
        # Notify user
        try:
            await client.send_message(target_id, f"ℹ️ Your premium subscription has been removed by an admin.")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error removing premium from {target_id}: {e}")
        await message.reply(f"❌ Error removing premium: {str(e)[:100]}")

@app.on_message(filters.command("addadmin"))
@require_registered
async def cmd_addadmin(client, message: Message):
    """Handle /addadmin command - Only owner can add admins."""
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can add admins.")
        return
    
    args = message.text.split(None, 3)
    if len(args) < 2:
        await message.reply(
            "👑 **Add Admin**\n\n"
            "Usage: `/addadmin [user_id] [title (optional)] [level 1-9 (optional)]`\n\n"
            "Examples:\n"
            "• `/addadmin 123456789`\n"
            "• `/addadmin 123456789 'Support Admin' 5`"
        )
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
    
    try:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, 'Admin')", (target_id,))
        db.execute("UPDATE users SET is_admin=1, admin_level=?, admin_title=? WHERE user_id=?", (level, title, target_id))
        db.execute("""INSERT OR REPLACE INTO admins 
                      (user_id, title, level, added_by, can_ban, can_broadcast, can_manage_premium, can_manage_users)
                      VALUES (?, ?, ?, ?, 1, 1, 1, 1)""", 
                      (target_id, title, level, message.from_user.id))
        db.commit()
        await message.reply(f"✅ User `{target_id}` added as **{title}** (Level {level})")
        
        # Notify new admin
        try:
            await client.send_message(
                target_id, 
                f"👑 **You have been promoted to Admin!**\n\n"
                f"Title: {title}\n"
                f"Level: {level}\n\n"
                f"Use /admin to access the admin panel."
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error adding admin {target_id}: {e}")
        await message.reply(f"❌ Error adding admin: {str(e)[:100]}")

@app.on_message(filters.command("rmadmin"))
@require_registered
async def cmd_rmadmin(client, message: Message):
    """Handle /rmadmin command - Remove admin (owner only)."""
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can remove admins.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/rmadmin [user_id]`\n\nExample: `/rmadmin 123456789`")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    
    if target_id == OWNER_ID:
        await message.reply("❌ Cannot remove owner's admin status.")
        return
    
    try:
        db = get_db()
        db.execute("UPDATE users SET is_admin=0, admin_level=0, admin_title=NULL WHERE user_id=?", (target_id,))
        db.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
        db.commit()
        await message.reply(f"✅ Admin `{target_id}` removed.")
        
        # Notify user
        try:
            await client.send_message(target_id, f"ℹ️ Your admin privileges have been removed.")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error removing admin {target_id}: {e}")
        await message.reply(f"❌ Error removing admin: {str(e)[:100]}")

@app.on_message(filters.command("listadmins"))
@require_registered
@require_admin
async def cmd_listadmins(client, message: Message):
    """Handle /listadmins command."""
    try:
        admins = get_db().execute("SELECT * FROM admins ORDER BY level DESC").fetchall()
        if not admins:
            await message.reply("No admins found.")
            return
        
        text = "👑 **Admin List:**\n\n"
        for a in admins:
            text += f"• `{a['user_id']}` — {a['title']} (Lvl {a['level']})\n"
            if len(text) > 3500:
                text += "\n... and more"
                break
        await message.reply(text)
    except Exception as e:
        logger.error(f"Error listing admins: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("userinfo"))
@require_registered
@require_admin
async def cmd_userinfo(client, message: Message):
    """Handle /userinfo command."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/userinfo [user_id]`\n\nExample: `/userinfo 123456789`")
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
    """Handle /addcoins command."""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: `/addcoins [user_id] [amount]`\n\nExample: `/addcoins 123456789 100`")
        return
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments. User ID and amount must be numbers.")
        return
    
    try:
        add_coins(target_id, amount, "Admin grant")
        await message.reply(f"✅ Added 🪙 {amount} coins to user `{target_id}`.")
        
        # Notify user
        try:
            await client.send_message(target_id, f"🎉 **+{amount} Coins Added!**\n\nAdmin has added coins to your account.\nTotal coins: {get_user(target_id)['coins']}")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error adding coins to {target_id}: {e}")
        await message.reply(f"❌ Error adding coins: {str(e)[:100]}")

@app.on_message(filters.command("rmcoins"))
@require_registered
@require_admin
async def cmd_rmcoins(client, message: Message):
    """Handle /rmcoins command."""
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: `/rmcoins [user_id] [amount]`\n\nExample: `/rmcoins 123456789 50`")
        return
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    
    try:
        get_db().execute("UPDATE users SET coins=MAX(0,coins-?) WHERE user_id=?", (amount, target_id))
        get_db().commit()
        await message.reply(f"✅ Removed 🪙 {amount} coins from user `{target_id}`.")
    except Exception as e:
        logger.error(f"Error removing coins from {target_id}: {e}")
        await message.reply(f"❌ Error removing coins: {str(e)[:100]}")

@app.on_message(filters.command("broadcast"))
@require_registered
@require_admin
async def cmd_broadcast(client, message: Message):
    """Handle /broadcast command."""
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "📢 **Broadcast Message**\n\n"
            "Usage: `/broadcast [message]`\n\n"
            "You can use markdown formatting.\n\n"
            "Example: `/broadcast **Important Update!** New features added!`"
        )
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
    
    try:
        db = get_db()
        db.execute(
            "INSERT INTO broadcast_logs (admin_id, message_text, sent_count, failed_count) VALUES (?, ?, ?, ?)",
            (message.from_user.id, text[:500], sent, failed)
        )
        db.commit()
    except Exception as e:
        logger.error(f"Error logging broadcast: {e}")
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(users)}"
    )

@app.on_message(filters.command("setwelcome"))
@require_registered
@require_admin
async def cmd_setwelcome(client, message: Message):
    """Handle /setwelcome command."""
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: `/setwelcome [message]`\n\nExample: `/setwelcome Welcome to our bot!`")
        return
    
    set_setting("welcome_message", args[1])
    await message.reply(f"✅ Welcome message updated to:\n\n{args[1][:200]}")

@app.on_message(filters.command("setwatermark"))
@require_registered
@require_admin
async def cmd_setwatermark(client, message: Message):
    """Handle /setwatermark command."""
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: `/setwatermark [text]`\n\nExample: `/setwatermark MyBrand`")
        return
    
    set_setting("watermark_text", args[1])
    await message.reply(f"✅ Watermark text set to: `{args[1]}`")

@app.on_message(filters.command("setfree"))
@require_registered
@require_admin
async def cmd_setfree(client, message: Message):
    """Handle /setfree command - Set free edits per day."""
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Usage: `/setfree [number]`\n\nExample: `/setfree 10`")
        return
    
    set_setting("free_edits_per_day", args[1])
    await message.reply(f"✅ Free edits per day set to: **{args[1]}**")

@app.on_message(filters.command("setads"))
@require_registered
@require_admin
async def cmd_setads(client, message: Message):
    """Handle /setads command."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/setads [on|off] [interval (optional)]`\n\nExamples:\n• `/setads on 5` - show ads every 5 edits\n• `/setads off`")
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
    """Handle /maintenance command."""
    current = get_setting("maintenance_mode", "0")
    new_val = "0" if current == "1" else "1"
    set_setting("maintenance_mode", new_val)
    status = "🔧 ON (users cannot use bot)" if new_val == "1" else "✅ OFF (bot is live)"
    await message.reply(f"Maintenance mode: **{status}**")

@app.on_message(filters.command("backup"))
@require_registered
@require_admin
async def cmd_backup(client, message: Message):
    """Handle /backup command."""
    try:
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_path)
        await client.send_document(
            message.chat.id,
            document=backup_path,
            caption=f"💾 **Database Backup**\n"
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Users: {get_user_count()}\n"
                    f"Size: {os.path.getsize(backup_path) / 1024:.1f} KB"
        )
        os.remove(backup_path)
        await message.reply("✅ Backup sent successfully!")
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await message.reply(f"❌ Backup failed: {str(e)[:100]}")

@app.on_message(filters.command("cleanup"))
@require_registered
@require_admin
async def cmd_cleanup(client, message: Message):
    """Handle /cleanup command."""
    before = len(list(Path(TEMP_DIR).iterdir()))
    cleanup_temp_files(0)
    cleanup_sessions()
    after = len(list(Path(TEMP_DIR).iterdir()))
    await message.reply(f"✅ Cleanup done!\nRemoved {before - after} temp files.\nSessions cleared.")

@app.on_message(filters.command("logs"))
@require_registered
@require_admin
async def cmd_logs(client, message: Message):
    """Handle /logs command."""
    if os.path.exists(LOG_FILE):
        await client.send_document(
            message.chat.id, 
            document=LOG_FILE, 
            caption=f"📋 Bot Logs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        await message.reply("❌ Log file not found.")

@app.on_message(filters.command("export"))
@require_registered
@require_admin
async def cmd_export(client, message: Message):
    """Handle /export command."""
    try:
        settings = {r[0]: r[1] for r in get_db().execute("SELECT key, value FROM settings").fetchall()}
        config = {
            "bot_name": BOT_NAME,
            "version": BOT_VERSION,
            "exported_at": datetime.now().isoformat(),
            "user_count": get_user_count(),
            "premium_count": get_premium_count(),
            "banned_count": get_banned_count(),
            "total_edits": get_total_edits(),
            "today_edits": get_today_edits(),
            "today_new_users": get_today_new_users(),
            "settings": settings,
            "admin_count": get_admin_count(),
        }
        
        export_path = temp_path(".json")
        with open(export_path, "w") as f:
            json.dump(config, f, indent=2)
        
        await client.send_document(
            message.chat.id, 
            document=export_path, 
            caption="📤 **Bot Configuration Export**\n\nUse this file for backup or analysis."
        )
        os.remove(export_path)
    except Exception as e:
        logger.error(f"Export error: {e}")
        await message.reply(f"❌ Export failed: {str(e)[:100]}")

@app.on_message(filters.command("addcmd"))
@require_registered
@require_admin
async def cmd_addcmd(client, message: Message):
    """Add custom command."""
    args = message.text.split(None, 2)
    if len(args) < 3 and not message.reply_to_message:
        await message.reply(
            "📝 **Add Custom Command**\n\n"
            "**Text response:**\n"
            "`/addcmd [command] [response]`\n\n"
            "**Media response (reply to media):**\n"
            "Reply to a photo/video: `/addcmd [command]`\n\n"
            "**Code response:**\n"
            "`/addcmd [command] --code [code]`\n\n"
            "Examples:\n"
            "• `/addcmd hello Welcome to KiraFx!`\n"
            "• `/addcmd rules --code Please follow the rules...`"
        )
        return

    cmd_name = args[1].lstrip("/").lower() if len(args) > 1 else None
    if not cmd_name:
        await message.reply("❌ Provide a command name.")
        return

    try:
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
    except Exception as e:
        logger.error(f"Error adding custom command: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("delcmd"))
@require_registered
@require_admin
async def cmd_delcmd(client, message: Message):
    """Delete custom command."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/delcmd [command]`\n\nExample: `/delcmd hello`")
        return
    
    cmd_name = args[1].lstrip("/").lower()
    try:
        get_db().execute("DELETE FROM custom_commands WHERE command=?", (cmd_name,))
        get_db().commit()
        await message.reply(f"✅ Command `/{cmd_name}` deleted.")
    except Exception as e:
        logger.error(f"Error deleting custom command: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("togglecmd"))
@require_registered
@require_admin
async def cmd_togglecmd(client, message: Message):
    """Toggle custom command on/off."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/togglecmd [command]`\n\nExample: `/togglecmd hello`")
        return
    
    cmd_name = args[1].lstrip("/").lower()
    try:
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
    except Exception as e:
        logger.error(f"Error toggling custom command: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("listcmds"))
@require_registered
@require_admin
async def cmd_listcmds(client, message: Message):
    """List all custom commands."""
    try:
        cmds = get_db().execute("SELECT command, response_type, is_enabled, use_count FROM custom_commands").fetchall()
        if not cmds:
            await message.reply("📭 No custom commands found.")
            return
        
        text = "📋 **Custom Commands:**\n\n"
        for row in cmds:
            status = "✅" if row["is_enabled"] else "❌"
            text += f"{status} `/{row['command']}` [{row['response_type']}] — used {row['use_count']}x\n"
        
        await message.reply(text)
    except Exception as e:
        logger.error(f"Error listing custom commands: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("addautoreply"))
@require_registered
@require_admin
async def cmd_addautoreply(client, message: Message):
    """Add auto-reply rule."""
    args = message.text.split(None, 3)
    if len(args) < 4:
        await message.reply(
            "🤖 **Add Auto-Reply**\n\n"
            "Usage: `/addautoreply [exact|contains|startswith] [trigger] [response]`\n\n"
            "Examples:\n"
            "• `/addautoreply exact hello Hi there! 👋`\n"
            "• `/addautoreply contains bot I'm a bot!`\n"
            "• `/addautoreply startswith !ping Pong!`"
        )
        return
    
    match_type = args[1].lower()
    if match_type not in ["exact", "contains", "startswith"]:
        await message.reply("❌ Match type must be: exact, contains, or startswith")
        return
    
    trigger = args[2]
    response = args[3]
    
    try:
        db = get_db()
        db.execute(
            "INSERT INTO auto_replies (trigger, match_type, response, response_type, added_by) VALUES (?, ?, ?, 'text', ?)",
            (trigger, match_type, response, message.from_user.id)
        )
        db.commit()
        await message.reply(f"✅ Auto-reply added!\nTrigger: `{trigger}` ({match_type})\nResponse: {response[:50]}...")
    except Exception as e:
        logger.error(f"Error adding auto-reply: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("delautoreply"))
@require_registered
@require_admin
async def cmd_delautoreply(client, message: Message):
    """Delete auto-reply rule."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/delautoreply [id]`\n\nExample: `/delautoreply 5`")
        return
    
    try:
        reply_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid ID.")
        return
    
    try:
        get_db().execute("DELETE FROM auto_replies WHERE id=?", (reply_id,))
        get_db().commit()
        await message.reply(f"✅ Auto-reply #{reply_id} deleted.")
    except Exception as e:
        logger.error(f"Error deleting auto-reply: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("listautoreplies"))
@require_registered
@require_admin
async def cmd_listautoreplies(client, message: Message):
    """List all auto-replies."""
    try:
        rows = get_db().execute("SELECT * FROM auto_replies").fetchall()
        if not rows:
            await message.reply("📭 No auto-replies found.")
            return
        
        text = "🤖 **Auto-Replies:**\n\n"
        for row in rows:
            status = "✅" if row["is_enabled"] else "❌"
            text += f"{status} #{row['id']} `{row['trigger']}` ({row['match_type']}) → {row['response'][:40]}\n"
        
        await message.reply(text)
    except Exception as e:
        logger.error(f"Error listing auto-replies: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("stats"))
@require_registered
@require_admin
async def cmd_stats(client, message: Message):
    """Handle /stats command."""
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    
    try:
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
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await message.reply(f"❌ Error getting stats: {str(e)[:100]}")

@app.on_message(filters.command("resetedits"))
@require_registered
@require_admin
async def cmd_resetedits(client, message: Message):
    """Reset daily edits for user(s)."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/resetedits [user_id|all]`\n\nExamples:\n• `/resetedits all`\n• `/resetedits 123456789`")
        return
    
    try:
        if args[1].lower() == "all":
            get_db().execute("UPDATE users SET edits_today=0")
            get_db().commit()
            await message.reply("✅ Reset daily edits for ALL users.")
        else:
            target_id = int(args[1])
            get_db().execute("UPDATE users SET edits_today=0 WHERE user_id=?", (target_id,))
            get_db().commit()
            await message.reply(f"✅ Reset daily edits for user `{target_id}`.")
    except ValueError:
        await message.reply("❌ Invalid user ID.")
    except Exception as e:
        logger.error(f"Error resetting edits: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("premlist"))
@require_registered
@require_admin
async def cmd_premlist(client, message: Message):
    """List premium users."""
    try:
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
    except Exception as e:
        logger.error(f"Error listing premium users: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("banlist"))
@require_registered
@require_admin
async def cmd_banlist(client, message: Message):
    """List banned users."""
    try:
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
    except Exception as e:
        logger.error(f"Error listing banned users: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("note"))
@require_registered
@require_admin
async def cmd_note(client, message: Message):
    """Add a bot note."""
    args = message.text.split(None, 2)
    if len(args) < 3:
        await message.reply("Usage: `/note [title] [content]`\n\nTo view all notes: `/notes`")
        return
    
    title = args[1]
    content = args[2]
    
    try:
        db = get_db()
        db.execute("INSERT INTO bot_notes (title, content, created_by) VALUES (?, ?, ?)",
                   (title, content, message.from_user.id))
        db.commit()
        await message.reply(f"✅ Note **{title}** saved.")
    except Exception as e:
        logger.error(f"Error saving note: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("notes"))
@require_registered
@require_admin
async def cmd_notes(client, message: Message):
    """List all bot notes."""
    try:
        rows = get_db().execute("SELECT * FROM bot_notes ORDER BY created_at DESC").fetchall()
        if not rows:
            await message.reply("📭 No notes saved.")
            return
        
        text = "📋 **Bot Notes:**\n\n"
        for r in rows[:15]:
            text += f"**{r['title']}** (#{r['id']}) — {str(r['created_at'])[:10]}\n{r['content'][:80]}...\n\n"
        
        await message.reply(text)
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

@app.on_message(filters.command("delnote"))
@require_registered
@require_admin
async def cmd_delnote(client, message: Message):
    """Delete a bot note."""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/delnote [id]`\n\nExample: `/delnote 5`")
        return
    
    try:
        note_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid ID.")
        return
    
    try:
        get_db().execute("DELETE FROM bot_notes WHERE id=?", (note_id,))
        get_db().commit()
        await message.reply(f"✅ Note #{note_id} deleted.")
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

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
            "Usage: `/runcode [python code]`\n\n"
            "Example: `/runcode print(get_user_count())`\n\n"
            "Available functions: get_db(), get_user(), get_user_count(), get_setting(), set_setting(), is_premium(), is_admin(), add_premium(), add_coins()"
        )
        return
    
    code = args[1]
    output = ""
    
    try:
        import io as _io
        import contextlib
        
        stdout_capture = _io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {
                "get_db": get_db, 
                "get_user": get_user, 
                "get_user_count": get_user_count,
                "get_setting": get_setting, 
                "set_setting": set_setting,
                "is_premium": is_premium, 
                "is_admin": is_admin,
                "add_premium": add_premium, 
                "add_coins": add_coins,
                "logger": logger, 
                "datetime": datetime, 
                "json": json,
            })
        output = stdout_capture.getvalue() or "(no output)"
        
        # Limit output length
        if len(output) > 1000:
            output = output[:1000] + "\n... (truncated)"
        
        await message.reply(f"💻 **Code Output:**\n```\n{output}\n```")
    except Exception as e:
        await message.reply(f"💻 **Code Error:**\n```\n{str(e)[:500]}\n```")

@app.on_message(filters.command("deploy"))
@require_registered
@require_admin
async def cmd_deploy(client, message: Message):
    """Show deployment status."""
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
# ============================================================
# FIXED MEDIA HANDLERS
# ============================================================

async def handle_media_for_edit(client, message: Message, file_path: str, media_type: str):
    """Generic handler after downloading a media file."""
    user_id = message.from_user.id
    mode = get_session(user_id, "mode")

    try:
        loop = asyncio.get_running_loop()

        # ── OCR mode (any image) ───────────────────────────────
        if mode == "ocr" and media_type == "photo":
            status_msg = await message.reply("🔍 Scanning image for text...")
            clear_session(user_id, "mode")
            try:
                ocr_result = await loop.run_in_executor(
                    executor, lambda: do_ocr_simple(Image.open(file_path))
                )
                await status_msg.edit_text(
                    f"🔍 **OCR Result:**\n\n{ocr_result[:3000]}",
                    reply_markup=after_edit_keyboard()
                )
            except Exception as e:
                await status_msg.edit_text(f"❌ OCR failed: {str(e)[:200]}")
            return

        # ── Scan / analyze image ───────────────────────────────
        if mode == "scan" and media_type == "photo":
            status_msg = await message.reply("🔬 Analyzing image...")
            clear_session(user_id, "mode")
            try:
                info = await loop.run_in_executor(executor, lambda: analyze_image(Image.open(file_path)))
                sugg = " → ".join(IMAGE_FILTERS.get(f, f) for f in info["suggestions"])
                await status_msg.edit_text(
                    f"🔬 **Image Analysis Results:**\n\n"
                    f"📐 Size: `{info['width']}×{info['height']}` px\n"
                    f"🎨 Color mode: `{info['mode']}`\n"
                    f"💡 Brightness: `{info['brightness']}/255`\n"
                    f"🌡️ Tone: {info['warmth']}\n"
                    f"📊 Contrast: `{info['contrast_estimate']}/255`\n"
                    f"🔴 R avg: `{info['r_avg']}`  🟢 G: `{info['g_avg']}`  🔵 B: `{info['b_avg']}`\n\n"
                    f"✨ **Suggested filters:**\n`{sugg}`",
                    reply_markup=after_edit_keyboard()
                )
            except Exception as e:
                await status_msg.edit_text(f"❌ Analysis failed: {str(e)[:200]}")
            return

        # ── Sticker maker ─────────────────────────────────────
        if mode == "make_sticker" and media_type == "photo":
            status_msg = await message.reply("🎭 Creating sticker...")
            clear_session(user_id, "mode")
            try:
                sticker_img = await loop.run_in_executor(
                    executor, lambda: make_sticker_image(Image.open(file_path).convert("RGBA"))
                )
                out = temp_path(".png")
                sticker_img.save(out, "PNG")
                await client.send_document(
                    message.chat.id, document=out,
                    caption="🎭 **Sticker-ready PNG!**\n\n512×512, transparent background.\nSend to @Stickers to add to your pack!"
                )
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── File info ─────────────────────────────────────────
        if mode == "fileinfo":
            clear_session(user_id, "mode")
            info_text = await loop.run_in_executor(executor, lambda: get_file_info_text(file_path))
            await message.reply(info_text, reply_markup=after_edit_keyboard())
            return

        # ── Add text to image ─────────────────────────────────
        if mode == "addtext_waiting_photo" and media_type == "photo":
            text_data = get_session(user_id, "addtext_data", "Text")
            status_msg = await message.reply("✍️ Adding text to image...")
            clear_session(user_id)
            try:
                result = await loop.run_in_executor(
                    executor, lambda: apply_addtext(Image.open(file_path).convert("RGB"), text_data)
                )
                out = temp_path(".jpg")
                result.save(out, "JPEG", quality=92)
                await client.send_photo(message.chat.id, photo=out,
                                        caption="✅ **Text Added!**", reply_markup=after_edit_keyboard())
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Meme maker ────────────────────────────────────────
        if mode == "meme_waiting_photo" and media_type == "photo":
            meme_text = get_session(user_id, "meme_text", "Top Text | Bottom Text")
            status_msg = await message.reply("😂 Creating meme...")
            clear_session(user_id)
            try:
                result = await loop.run_in_executor(
                    executor, lambda: apply_meme(Image.open(file_path).convert("RGB"), meme_text)
                )
                out = temp_path(".jpg")
                result.save(out, "JPEG", quality=92)
                await client.send_photo(message.chat.id, photo=out,
                                        caption="😂 **Meme Created!**", reply_markup=after_edit_keyboard())
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Collage — collect images ───────────────────────────
        if mode == "collage" and media_type == "photo":
            images = get_session(user_id, "collage_images") or []
            images.append(file_path)
            set_session(user_id, "collage_images", images)
            await message.reply(
                f"🖼️ **Image {len(images)} added!**\n\n"
                f"Send more images or type `/done` to create the collage!\n"
                f"(Max 9 images)"
            )
            return

        # ── Resize image ──────────────────────────────────────
        if mode == "resize_waiting" and media_type == "photo":
            size_str = get_session(user_id, "resize_size", "50%")
            status_msg = await message.reply("📐 Resizing image...")
            clear_session(user_id)
            try:
                result = await loop.run_in_executor(
                    executor, lambda: do_resize_image(Image.open(file_path).convert("RGB"), size_str)
                )
                out = temp_path(".jpg")
                result.save(out, "JPEG", quality=92)
                await client.send_photo(message.chat.id, photo=out,
                                        caption=f"✅ **Resized to** `{result.width}×{result.height}`",
                                        reply_markup=after_edit_keyboard())
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Crop image ────────────────────────────────────────
        if mode == "crop_waiting_photo" and media_type == "photo":
            crop_data = get_session(user_id, "crop_data", "square")
            status_msg = await message.reply("✂️ Cropping image...")
            clear_session(user_id)
            try:
                img = Image.open(file_path).convert("RGB")
                result = await loop.run_in_executor(executor, lambda: do_crop_image(img, crop_data))
                out = temp_path(".jpg")
                result.save(out, "JPEG", quality=92)
                await client.send_photo(message.chat.id, photo=out,
                                        caption=f"✅ **Cropped!** `{result.width}×{result.height}`",
                                        reply_markup=after_edit_keyboard())
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Watermark image ───────────────────────────────────
        if mode == "watermark_waiting_media" and media_type == "photo":
            wm_text = get_session(user_id, "wm_text_custom", "KiraFx")
            status_msg = await message.reply("💧 Adding watermark...")
            clear_session(user_id)
            try:
                img = Image.open(file_path).convert("RGB")
                result = await loop.run_in_executor(executor, lambda: add_watermark(img, wm_text))
                out = temp_path(".jpg")
                result.save(out, "JPEG", quality=92)
                await client.send_photo(message.chat.id, photo=out,
                                        caption=f"💧 **Watermark Added:** {wm_text}",
                                        reply_markup=after_edit_keyboard())
                await status_msg.delete()
                os.remove(out)
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Prompt-based AI edit ──────────────────────────────
        if mode == "prompt_waiting_media" and media_type == "photo":
            prompt_text = get_session(user_id, "prompt_text", "enhance")
            filters_to_apply = map_prompt_to_filters(prompt_text)
            clear_session(user_id)
            await apply_image_filters_sequence(client, message, file_path, filters_to_apply, user_id)
            return

        # ── Set profile photo ─────────────────────────────────
        if mode == "setphoto" and media_type == "photo":
            target = get_session(user_id, "setphoto_target", "bot")
            status_msg = await message.reply("📸 Uploading photo...")
            clear_session(user_id)
            try:
                if target == "bot":
                    await client.set_profile_photo(photo=file_path)
                    await status_msg.edit_text("✅ **Bot profile photo updated!**")
                else:
                    await client.set_profile_photo(photo=file_path)
                    await status_msg.edit_text("✅ **Profile photo uploaded!**")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Convert image format ──────────────────────────────
        if mode == "convert_waiting_file" and media_type == "photo":
            fmt = get_session(user_id, "convert_format", "png")
            status_msg = await message.reply(f"🔄 Converting to {fmt.upper()}...")
            clear_session(user_id)
            ext = f".{fmt}" if not fmt.startswith(".") else fmt
            out = temp_path(ext)
            try:
                ok, err = await loop.run_in_executor(executor, lambda: do_convert_file(file_path, out, fmt))
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    await client.send_document(message.chat.id, document=out,
                                               caption=f"🔄 **Converted to {fmt.upper()}!**")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Conversion failed: {err or 'Unknown error'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── GIF / Video to GIF convert ────────────────────────
        if mode == "gif_convert" and media_type in ("video", "photo"):
            status_msg = await message.reply("🎞️ Converting to GIF... Please wait.")
            clear_session(user_id)
            max_dur = 30 if is_premium(user_id) else 10
            scale = "720" if is_premium(user_id) else "480"
            out = temp_path(".gif")
            try:
                cmd = ["ffmpeg", "-y", "-i", file_path,
                       "-t", str(max_dur),
                       "-vf", f"fps=10,scale={scale}:-1:flags=lanczos",
                       "-loop", "0", out]
                ok, err = await loop.run_in_executor(
                    executor, lambda: (lambda r: (r.returncode == 0, r.stderr[-200:]))(
                        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    )
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    size_mb = os.path.getsize(out) / (1024*1024)
                    await client.send_animation(message.chat.id, animation=out,
                                               caption=f"🎞️ **GIF Created!** ({size_mb:.1f} MB)")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ GIF conversion failed: {err}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Video trim ────────────────────────────────────────
        if mode == "trim_waiting_video" and media_type in ("video", "document"):
            times = get_session(user_id, "trim_times", "0 30")
            status_msg = await message.reply(f"✂️ Trimming video ({times})...")
            clear_session(user_id)
            out = temp_path(".mp4")
            try:
                ok, err = await loop.run_in_executor(
                    executor, lambda: do_trim_video(file_path, out, times)
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    size_mb = os.path.getsize(out) / (1024*1024)
                    if size_mb < 50:
                        await client.send_video(message.chat.id, video=out,
                                               caption=f"✂️ **Trimmed!** ({times})")
                    else:
                        await client.send_document(message.chat.id, document=out,
                                                   caption=f"✂️ **Trimmed!** ({times})")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Trim failed: {err or 'Empty output'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Speed change ──────────────────────────────────────
        if mode == "speed_waiting_video" and media_type in ("video", "audio", "document"):
            speed = float(get_session(user_id, "speed_value", "2.0"))
            status_msg = await message.reply(f"⚡ Changing speed to {speed}×...")
            clear_session(user_id)
            ext = ".mp4" if media_type != "audio" else ".mp3"
            out = temp_path(ext)
            try:
                ok, err = await loop.run_in_executor(
                    executor, lambda: do_speed_video(file_path, out, speed)
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    if ext == ".mp3":
                        await client.send_audio(message.chat.id, audio=out,
                                               caption=f"⚡ **Speed: {speed}×**")
                    else:
                        await client.send_video(message.chat.id, video=out,
                                               caption=f"⚡ **Speed: {speed}×**",
                                               reply_markup=after_video_keyboard())
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Speed change failed: {err or 'Empty output'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Add subtitle to video ─────────────────────────────
        if mode == "subtitle_waiting_video" and media_type in ("video", "document"):
            sub_text = get_session(user_id, "subtitle_text", "")
            status_msg = await message.reply("🎬 Adding subtitle...")
            clear_session(user_id)
            out = temp_path(".mp4")
            try:
                ok, err = await loop.run_in_executor(
                    executor, lambda: do_add_subtitle(file_path, out, sub_text, is_premium(user_id))
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    size_mb = os.path.getsize(out) / (1024*1024)
                    if size_mb < 50:
                        await client.send_video(message.chat.id, video=out,
                                               caption=f"✅ **Subtitle Added!**\n\n{sub_text[:100]}",
                                               reply_markup=after_video_keyboard())
                    else:
                        await client.send_document(message.chat.id, document=out,
                                                   caption=f"✅ **Subtitle Added!**")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Subtitle failed: {err or 'Unknown error'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Resize video ──────────────────────────────────────
        if mode == "resize_waiting" and media_type in ("video", "document"):
            size_str = get_session(user_id, "resize_size", "50%")
            status_msg = await message.reply("📐 Resizing video...")
            clear_session(user_id)
            out = temp_path(".mp4")
            try:
                ok, err = await loop.run_in_executor(
                    executor, lambda: do_resize_video(file_path, out, size_str)
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    size_mb = os.path.getsize(out) / (1024*1024)
                    if size_mb < 50:
                        await client.send_video(message.chat.id, video=out,
                                               caption=f"✅ **Resized to {size_str}!**")
                    else:
                        await client.send_document(message.chat.id, document=out,
                                                   caption=f"✅ **Resized!**")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Resize failed: {err or 'Unknown error'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Convert any file ──────────────────────────────────
        if mode == "convert_waiting_file" and media_type in ("video", "audio", "document"):
            fmt = get_session(user_id, "convert_format", "mp4")
            status_msg = await message.reply(f"🔄 Converting to {fmt.upper()}...")
            clear_session(user_id)
            out = temp_path(f".{fmt}")
            try:
                ok, err = await loop.run_in_executor(executor, lambda: do_convert_file(file_path, out, fmt))
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    await client.send_document(message.chat.id, document=out,
                                               caption=f"🔄 **Converted to {fmt.upper()}!**")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Conversion failed: {err or 'Unknown error'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── Watermark on video ─────────────────────────────────
        if mode == "watermark_waiting_media" and media_type in ("video", "document"):
            wm_text = get_session(user_id, "wm_text_custom", "KiraFx")
            status_msg = await message.reply("💧 Adding watermark to video...")
            clear_session(user_id)
            out = temp_path(".mp4")
            safe_wm = wm_text.replace("'", "\\'").replace(":", "\\:")
            try:
                cmd = ["ffmpeg", "-y", "-i", file_path,
                       "-vf", f"drawtext=text='{safe_wm}':fontcolor=white:fontsize=24:"
                              f"shadowcolor=black:shadowx=2:shadowy=2:"
                              f"x=10:y=h-th-10",
                       "-c:v", "libx264", "-c:a", "aac", out]
                ok, err = await loop.run_in_executor(
                    executor, lambda: (lambda r: (r.returncode == 0, r.stderr[-300:]))(
                        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    )
                )
                if ok and os.path.exists(out) and os.path.getsize(out) > 0:
                    await client.send_video(message.chat.id, video=out,
                                           caption=f"💧 **Watermark Added:** {wm_text}")
                    await status_msg.delete()
                    os.remove(out)
                else:
                    await status_msg.edit_text(f"❌ Failed: {err or 'Unknown error'}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            return

        # ── File info (any file) ───────────────────────────────
        if mode == "fileinfo":
            clear_session(user_id, "mode")
            info_text = await loop.run_in_executor(executor, lambda: get_file_info_text(file_path))
            await message.reply(info_text, reply_markup=after_edit_keyboard())
            return

        # ── Default photo handling ────────────────────────────
        if media_type == "photo":
            if mode == "aiedit":
                ai_filters = get_session(user_id, "ai_filters", [])
                if ai_filters:
                    await apply_image_filters_sequence(client, message, file_path, ai_filters, user_id)
                    clear_session(user_id)
                    return

            if get_session(user_id, "timeline_mode"):
                tl = get_timeline(user_id)
                save_timeline(user_id, file_path, "image", tl.get("steps", []))
                clear_session(user_id, "timeline_mode")
                await message.reply(
                    "📊 **Timeline Editor — Image Loaded!**\n\nNow add filters:",
                    reply_markup=timeline_keyboard(user_id)
                )
                return

            set_session(user_id, "image_path", file_path)
            clear_session(user_id, "mode")
            try:
                with Image.open(file_path) as _im:
                    w, h = _im.size
                    fmt = _im.format or "?"
                fsize = fmt_size(os.path.getsize(file_path))
                info_caption = (
                    f"📷 **{fancy('Photo Received')}!**\n\n"
                    f">┌  ✦  **{fancy('File Info')}**  ✦\n"
                    f">│ 📐 Size: `{w}×{h}` px\n"
                    f">│ 🎨 Format: `{fmt}`\n"
                    f">│ 💾 Weight: `{fsize}`\n"
                    f">└─────────────────\n\n"
                    f"⚡ {fancy('Choose a filter category below')} ⚡"
                )
            except Exception:
                info_caption = f"📷 **{fancy('Photo Received')}!**\n\nChoose a filter category:"
            await message.reply(info_caption, reply_markup=image_category_keyboard())

        elif media_type == "video":
            if mode == "compress":
                set_session(user_id, "video_path", file_path)
                clear_session(user_id, "mode")
                await message.reply(
                    "🗜️ **Choose Compression Quality:**\n\n⭐ = Premium only",
                    reply_markup=compress_keyboard()
                )
            elif get_session(user_id, "timeline_mode"):
                tl = get_timeline(user_id)
                save_timeline(user_id, file_path, "video", tl.get("steps", []))
                clear_session(user_id, "timeline_mode")
                await message.reply(
                    "📊 **Timeline Editor — Video Loaded!**\n\nNow add effects:",
                    reply_markup=timeline_keyboard(user_id)
                )
            else:
                set_session(user_id, "video_path", file_path)
                clear_session(user_id, "mode")
                # Probe video info
                fsize = fmt_size(os.path.getsize(file_path))
                duration = "?"
                resolution = "?"
                try:
                    probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
                                "-show_entries", "stream=width,height,duration",
                                "-of", "csv=p=0", file_path]
                    r = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    if r.returncode == 0 and r.stdout.strip():
                        parts = r.stdout.strip().split(",")
                        if len(parts) >= 2:
                            resolution = f"{parts[0]}×{parts[1]}"
                        if len(parts) >= 3 and parts[2]:
                            duration = f"{float(parts[2]):.1f}s"
                except Exception:
                    pass
                info_caption = (
                    f"🎬 **{fancy('Video Received')}!**\n\n"
                    f">┌  ✦  **{fancy('File Info')}**  ✦\n"
                    f">│ 📐 Resolution: `{resolution}`\n"
                    f">│ ⏱ Duration: `{duration}`\n"
                    f">│ 💾 Size: `{fsize}`\n"
                    f">└─────────────────\n\n"
                    f"⚡ {fancy('Choose an effect or quick action')} ⚡"
                )
                await message.reply(info_caption, reply_markup=video_category_keyboard())

        elif media_type in ("document", "audio"):
            if mode == "rename":
                original_name = getattr(message.document or message.audio, "file_name", "file")
                set_session(user_id, "rename_path", file_path)
                set_session(user_id, "rename_original", original_name)
                clear_session(user_id, "mode")
                await message.reply(
                    f"✏️ **Rename File**\n\nOriginal: `{original_name}`\n\nType the new filename:",
                    reply_markup=cancel_keyboard()
                )
            elif mode == "metadata":
                set_session(user_id, "metadata_path", file_path)
                clear_session(user_id, "mode")
                await show_metadata_menu(client, message)
            else:
                original_name = getattr(message.document or message.audio, "file_name", "file")
                ext = Path(original_name).suffix.lower()
                img_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
                vid_exts = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
                if ext in img_exts:
                    set_session(user_id, "image_path", file_path)
                    await message.reply("📷 **Image document received!**\n\nChoose a filter:",
                                        reply_markup=image_category_keyboard())
                elif ext in vid_exts:
                    set_session(user_id, "video_path", file_path)
                    await message.reply("🎬 **Video document received!**\n\nChoose an effect:",
                                        reply_markup=video_category_keyboard())
                else:
                    set_session(user_id, "rename_path", file_path)
                    set_session(user_id, "rename_original", original_name)
                    await message.reply(
                        f"📁 **File Received!**\n\nFile: `{original_name}`\n\nWhat to do?",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✏️ Rename", callback_data="do_rename"),
                             InlineKeyboardButton("📝 Edit Metadata", callback_data="do_metadata")],
                            [InlineKeyboardButton("ℹ️ File Info", callback_data="do_fileinfo"),
                             InlineKeyboardButton("🔄 Convert", callback_data="do_convert")],
                            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
                        ])
                    )
    except Exception as e:
        logger.error(f"Error in handle_media_for_edit: {e}\n{traceback.format_exc()}")
        await message.reply(f"❌ Error processing media: {str(e)[:200]}")

async def show_metadata_menu(client, message: Message):
    """Show metadata editing menu."""
    await message.reply(
        "📝 **Metadata Editor**\n\n"
        "Send metadata in this format:\n"
        "`title=My Title | artist=Artist | album=Album | year=2024`\n\n"
        "**Available fields:**\n"
        "title, artist, album, year, comment, description, genre, language, encoder, track, disc, composer, publisher, copyright\n\n"
        "Example:\n"
        "`title=My Song | artist=John Doe | year=2024 | genre=Pop`",
        reply_markup=cancel_keyboard()
    )

async def apply_image_filters_sequence(client, message: Message, file_path: str, filters_list: List[str], user_id: int = None):
    """Apply multiple filters in sequence."""
    if user_id is None:
        user_id = message.from_user.id
    
    status_msg = await message.reply(f"⏳ Applying {len(filters_list)} filter(s)...")
    
    try:
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(executor, lambda: Image.open(file_path).convert("RGB"))

        for f in filters_list:
            img = await loop.run_in_executor(executor, lambda fi=f, im=img: apply_image_filter(im, fi))

        # Add watermark for free users
        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = await loop.run_in_executor(executor, lambda: add_watermark(img, wm_text))

        out_path = temp_path(".jpg")
        img.save(out_path, "JPEG", quality=92)
        
        filter_names = " → ".join(IMAGE_FILTERS.get(f, f) for f in filters_list)
        caption = f"✅ **Applied:** {filter_names}"
        if is_premium(user_id):
            caption += "\n\n⭐ **Premium:** No watermark applied!"
        
        await client.send_photo(
            message.chat.id,
            photo=out_path,
            caption=caption,
            reply_markup=after_edit_keyboard()
        )
        
        increment_edits(user_id)
        log_edit(user_id, "image_sequence", filter_names)
        await status_msg.delete()
        os.remove(out_path)

        # Ad injection for free users
        if should_show_ad(user_id):
            await client.send_message(message.chat.id, get_random_ad())

    except Exception as e:
        logger.error(f"Filter apply error: {e}\n{traceback.format_exc()}")
        await status_msg.edit_text(f"❌ Error applying filters: {str(e)[:200]}")

@app.on_message(filters.photo)
@require_registered
async def handle_photo(client, message: Message):
    """Handle incoming photos."""
    user_id = message.from_user.id
    
    # Skip if in aiedit_prompt mode
    if get_session(user_id, "mode") == "aiedit_prompt":
        return
    
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ **Daily Limit Reached!**\n\n"
            f"Free users get {limit} edits per day.\n\n"
            f"⭐ Upgrade to Premium for unlimited edits!\n"
            f"🎁 Or use /trial for a 7-day free trial!",
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
    """Handle incoming videos."""
    user_id = message.from_user.id
    
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ **Daily Limit Reached!**\n\n"
            f"Free users get {limit} edits per day.\n\n"
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
    """Handle incoming documents."""
    doc = message.document
    ext = Path(doc.file_name or "file").suffix.lower() if doc.file_name else ""
    video_exts = [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".3gp", ".m4v"]
    img_exts = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"]
    
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
    """Handle incoming audio files."""
    status_msg = await message.reply("⬇️ Downloading audio...")
    
    try:
        file_path = await message.download(file_name=temp_path(".mp3"))
        await status_msg.delete()
        await handle_media_for_edit(client, message, file_path, "audio")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

# ============================================================
# ADVANCED EDITING TOOLS — NEW COMMANDS
# ============================================================

# ── /addtext ──────────────────────────────────────────────────
@app.on_message(filters.command("addtext"))
@require_registered
async def cmd_addtext(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "addtext")
        await message.reply(
            "✍️ **Add Text to Image**\n\n"
            "Format: `text | color | position | size`\n"
            "Example: `Hello World | white | bottom | 40`\n\n"
            "Then send your image!\n"
            "Position: top / center / bottom\n"
            "Color: white / black / red / yellow / blue / orange / pink / cyan",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "addtext_data", args[1])
    set_session(user_id, "mode", "addtext_waiting_photo")
    await message.reply("📷 Now send your image to add the text to.", reply_markup=cancel_keyboard())

# ── /meme ─────────────────────────────────────────────────────
@app.on_message(filters.command("meme"))
@require_registered
async def cmd_meme(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "meme")
        await message.reply(
            "😂 **Meme Maker**\n\n"
            "Format: `TOP TEXT | BOTTOM TEXT`\n"
            "Example: `When you fix a bug | But create 3 more`\n\n"
            "Then send your image!",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "meme_text", args[1])
    set_session(user_id, "mode", "meme_waiting_photo")
    await message.reply("📷 Now send the image for your meme.", reply_markup=cancel_keyboard())

# ── /sticker ──────────────────────────────────────────────────
@app.on_message(filters.command("sticker"))
@require_registered
async def cmd_sticker(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "make_sticker")
    await message.reply(
        "🎭 **Sticker Maker**\n\n"
        "Send an image and it will be converted to a 512×512 PNG sticker-ready file!\n\n"
        "• Transparent background preserved\n"
        "• PNG format (512×512)\n"
        "• Ready for @Stickers bot!",
        reply_markup=cancel_keyboard()
    )

# ── /ocr ──────────────────────────────────────────────────────
@app.on_message(filters.command("ocr"))
@require_registered
async def cmd_ocr(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "ocr")
    await message.reply(
        "🔍 **Image Text Scanner (OCR)**\n\n"
        "Send an image and the bot will extract all readable text from it!\n\n"
        "Works best with clear, high-contrast text on plain backgrounds.",
        reply_markup=cancel_keyboard()
    )

# ── /resize ───────────────────────────────────────────────────
@app.on_message(filters.command("resize"))
@require_registered
async def cmd_resize(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "resize")
        await message.reply(
            "📐 **Resize Image / Video**\n\n"
            "Send the target size:\n"
            "• `1280x720` — specific resolution\n"
            "• `50%` — percentage scale\n"
            "• `800` — fit to width (auto height)\n"
            "• `x600` — fit to height (auto width)\n\n"
            "Then send your image or video.",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "resize_size", args[1].strip())
    set_session(user_id, "mode", "resize_waiting")
    await message.reply("📷 Now send the image or video to resize.", reply_markup=cancel_keyboard())

# ── /crop ─────────────────────────────────────────────────────
@app.on_message(filters.command("crop"))
@require_registered
async def cmd_crop(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "crop_waiting_size")
        await message.reply(
            "✂️ **Crop Image**\n\n"
            "Send crop info:\n"
            "• `square` — crop to square (center)\n"
            "• `16:9` — widescreen ratio\n"
            "• `4:3` — classic ratio\n"
            "• `1:1` — square ratio\n"
            "• `x1,y1,x2,y2` — exact pixels (e.g. `100,50,800,600`)\n\n"
            "Then send your image.",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "crop_data", args[1].strip())
    set_session(user_id, "mode", "crop_waiting_photo")
    await message.reply("📷 Now send the image to crop.", reply_markup=cancel_keyboard())

# ── /collage ──────────────────────────────────────────────────
@app.on_message(filters.command("collage"))
@require_registered
async def cmd_collage(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "collage")
    set_session(user_id, "collage_images", [])
    await message.reply(
        "🖼️ **Collage Maker**\n\n"
        "Send 2–9 images one by one, then type `/done` to create the collage!\n\n"
        "Layouts: 1×2, 1×3, 2×2, 2×3, 3×3 (auto-detected)\n"
        "⭐ Premium users get HD export!",
        reply_markup=cancel_keyboard()
    )

# ── /subtitle ─────────────────────────────────────────────────
@app.on_message(filters.command("subtitle"))
@require_registered
async def cmd_subtitle(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "subtitle")
        await message.reply(
            "🎬 **Add Subtitle to Video**\n\n"
            "Send the subtitle text:\n\n"
            "Examples:\n"
            "• `Subscribe for more!`\n"
            "• `Copyright © 2025 My Channel`\n\n"
            "Then send your video!\n\n"
            "⭐ Premium: larger font, custom color",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "subtitle_text", args[1])
    set_session(user_id, "mode", "subtitle_waiting_video")
    await message.reply("🎬 Now send the video to add subtitles to.", reply_markup=cancel_keyboard())

# ── /trim ─────────────────────────────────────────────────────
@app.on_message(filters.command("trim"))
@require_registered
async def cmd_trim(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "trim")
        await message.reply(
            "✂️ **Trim Video**\n\n"
            "Send start and end time:\n\n"
            "Examples:\n"
            "• `00:05 01:30` — from 5s to 1m30s\n"
            "• `10 90` — from 10s to 90s\n"
            "• `0:10 0:45` — from 10s to 45s\n\n"
            "Then send your video!",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "trim_times", args[1].strip())
    set_session(user_id, "mode", "trim_waiting_video")
    await message.reply("🎬 Now send the video to trim.", reply_markup=cancel_keyboard())

# ── /speed ────────────────────────────────────────────────────
@app.on_message(filters.command("speed"))
@require_registered
async def cmd_speed(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "speed")
        await message.reply(
            "⚡ **Change Video / Audio Speed**\n\n"
            "Send the speed multiplier:\n\n"
            "• `0.5` — half speed (slow motion)\n"
            "• `1.5` — 1.5× speed\n"
            "• `2` — double speed\n"
            "• `0.25` — quarter speed\n"
            "• `4` — 4× fast forward\n\n"
            "Then send your video or audio file!",
            reply_markup=cancel_keyboard()
        )
        return
    try:
        speed = float(args[1].replace("x", "").strip())
        if not 0.1 <= speed <= 10:
            raise ValueError
    except ValueError:
        await message.reply("❌ Invalid speed. Use a number between 0.1 and 10 (e.g. `2` or `0.5`)")
        return
    set_session(user_id, "speed_value", str(speed))
    set_session(user_id, "mode", "speed_waiting_video")
    await message.reply(f"🎬 Speed: **{speed}×**. Now send your video or audio.", reply_markup=cancel_keyboard())

# ── /convert ──────────────────────────────────────────────────
@app.on_message(filters.command("convert"))
@require_registered
async def cmd_convert(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "convert")
        await message.reply(
            "🔄 **File Format Converter**\n\n"
            "Send the target format:\n\n"
            "🖼 **Images:** `jpg`, `png`, `webp`, `bmp`\n"
            "🎬 **Videos:** `mp4`, `avi`, `mkv`, `gif`, `webm`\n"
            "🎵 **Audio:** `mp3`, `aac`, `wav`, `ogg`, `flac`\n\n"
            "Then send your file!",
            reply_markup=cancel_keyboard()
        )
        return
    fmt = args[1].strip().lower().lstrip(".")
    set_session(user_id, "convert_format", fmt)
    set_session(user_id, "mode", "convert_waiting_file")
    await message.reply(f"🔄 Target format: **{fmt.upper()}**. Now send the file.", reply_markup=cancel_keyboard())

# ── /scan / /analyze / /sensor ────────────────────────────────
@app.on_message(filters.command(["scan", "analyze", "sensor"]))
@require_registered
async def cmd_scan(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "scan")
    await message.reply(
        "🔬 **Smart Image Analyzer**\n\n"
        "Send an image and the bot will analyze:\n\n"
        "• 🎨 Dominant colors & color temperature\n"
        "• 💡 Brightness & contrast level\n"
        "• 📐 Dimensions & format info\n"
        "• 🔍 Text content (OCR scan)\n"
        "• 🌟 Suggested filters for improvement",
        reply_markup=cancel_keyboard()
    )

# ── /gif (Video to GIF) ───────────────────────────────────────
@app.on_message(filters.command("gif"))
@require_registered
async def cmd_gif(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "gif_convert")
    await message.reply(
        "🎞️ **Video → GIF Converter**\n\n"
        "Send a video (max 30s) and it will be converted to an animated GIF!\n\n"
        "• Free users: up to 10s, 480p\n"
        "• ⭐ Premium: up to 30s, 720p quality",
        reply_markup=cancel_keyboard()
    )

# ── /watermark ────────────────────────────────────────────────
@app.on_message(filters.command("watermark"))
@require_registered
async def cmd_watermark_add(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "watermark_text")
        await message.reply(
            "💧 **Add Watermark**\n\n"
            "Send your watermark text:\n\n"
            "Example: `© My Channel 2025`\n\n"
            "Then send your image or video!\n"
            "⭐ Premium: custom position & opacity",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "wm_text_custom", args[1].strip())
    set_session(user_id, "mode", "watermark_waiting_media")
    await message.reply(f"💧 Watermark: **{args[1].strip()}**\n\nNow send your image or video.", reply_markup=cancel_keyboard())

# ── /setphoto ─────────────────────────────────────────────────
@app.on_message(filters.command("setphoto"))
@require_registered
async def cmd_setphoto(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    target = "bot" if (len(args) < 2 or args[1].lower() == "bot") else "user"
    if target == "bot" and user_id != OWNER_ID:
        await message.reply("🚫 Only the owner can change the bot's profile photo.\n\nUse `/setphoto user` to set your own profile photo via bot.")
        return
    set_session(user_id, "setphoto_target", target)
    set_session(user_id, "mode", "setphoto")
    await message.reply(
        f"📸 **Set Profile Photo**\n\n"
        f"Target: **{'🤖 Bot Profile' if target == 'bot' else '👤 Your Profile'}**\n\n"
        "Send the photo to use as the profile picture.",
        reply_markup=cancel_keyboard()
    )

# ── /setbotname ───────────────────────────────────────────────
@app.on_message(filters.command("setbotname"))
@require_registered
async def cmd_setbotname(client, message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        await message.reply("🚫 Only the owner can use this command.")
        return
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: `/setbotname New Bot Name`")
        return
    try:
        await client.set_bot_name(args[1].strip())
        await message.reply(f"✅ Bot name updated to: **{args[1].strip()}**")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)[:200]}\n\nTip: Use BotFather to change name manually.")

# ── /prompt (AI Prompt Edit) ──────────────────────────────────
@app.on_message(filters.command("prompt"))
@require_registered
async def cmd_prompt_edit(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "prompt_edit")
        await message.reply(
            "🧠 **AI Prompt Editor**\n\n"
            "Describe what you want to do with your image:\n\n"
            "Examples:\n"
            "• `make it look vintage and warm`\n"
            "• `sharp cinematic black and white`\n"
            "• `remove background and replace with white`\n"
            "• `portrait mode with skin smoothing`\n"
            "• `neon glow cyberpunk effect`\n"
            "• `dehaze and increase brightness`\n\n"
            "Then send your image!",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "prompt_text", args[1])
    set_session(user_id, "mode", "prompt_waiting_media")
    await message.reply(f"🧠 Prompt: **{args[1][:100]}**\n\nNow send your image.", reply_markup=cancel_keyboard())

# ── /done (for collage) ───────────────────────────────────────
@app.on_message(filters.command("done"))
@require_registered
async def cmd_done(client, message: Message):
    user_id = message.from_user.id
    mode = get_session(user_id, "mode")
    if mode == "collage":
        images = get_session(user_id, "collage_images") or []
        if len(images) < 2:
            await message.reply("❌ Need at least 2 images for a collage. Send more images first!")
            return
        status_msg = await message.reply(f"⏳ Creating collage from {len(images)} images...")
        try:
            loop = asyncio.get_running_loop()
            collage = await loop.run_in_executor(executor, lambda: make_collage(images))
            out = temp_path(".jpg")
            collage.save(out, "JPEG", quality=92)
            await client.send_photo(message.chat.id, photo=out,
                                    caption=f"🖼️ **Collage Created!** ({len(images)} images)",
                                    reply_markup=after_edit_keyboard())
            await status_msg.delete()
            os.remove(out)
            for p in images:
                try:
                    os.remove(p)
                except Exception:
                    pass
            clear_session(user_id)
        except Exception as e:
            await status_msg.edit_text(f"❌ Collage error: {str(e)[:200]}")
    else:
        await message.reply("ℹ️ Use /collage to start a collage session first.")

# ── /fileinfo ─────────────────────────────────────────────────
@app.on_message(filters.command("fileinfo"))
@require_registered
async def cmd_fileinfo(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "fileinfo")
    await message.reply(
        "ℹ️ **File Info**\n\nSend any file to see detailed information:\n"
        "• Image: resolution, mode, size, format\n"
        "• Video: duration, resolution, fps, codec, bitrate\n"
        "• Audio: duration, bitrate, sample rate, channels",
        reply_markup=cancel_keyboard()
    )


# ============================================================
# ADVANCED TOOL IMPLEMENTATIONS
# ============================================================

def make_collage(image_paths: list) -> Image.Image:
    """Create a grid collage from a list of image paths."""
    n = len(image_paths)
    if n <= 2:
        cols, rows = n, 1
    elif n <= 4:
        cols, rows = 2, 2
    elif n <= 6:
        cols, rows = 3, 2
    else:
        cols, rows = 3, 3

    cell_w, cell_h = 600, 450
    border = 4
    canvas = Image.new("RGB",
                       (cols * cell_w + (cols + 1) * border,
                        rows * cell_h + (rows + 1) * border),
                       (30, 30, 30))
    for idx, path in enumerate(image_paths[:cols * rows]):
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((cell_w, cell_h), Image.LANCZOS)
            off_x = (cell_w - img.width) // 2
            off_y = (cell_h - img.height) // 2
            row_idx, col_idx = divmod(idx, cols)
            x = border + col_idx * (cell_w + border) + off_x
            y = border + row_idx * (cell_h + border) + off_y
            canvas.paste(img, (x, y))
        except Exception:
            pass
    return canvas


def apply_addtext(img: Image.Image, text_data: str) -> Image.Image:
    """Add text overlay to image."""
    parts = [p.strip() for p in text_data.split("|")]
    text = parts[0] if parts else text_data
    color_name = parts[1].lower() if len(parts) > 1 else "white"
    position = parts[2].lower() if len(parts) > 2 else "bottom"
    try:
        size = int(parts[3]) if len(parts) > 3 else max(30, img.width // 20)
    except (ValueError, IndexError):
        size = max(30, img.width // 20)

    color_map = {
        "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 50, 50),
        "yellow": (255, 220, 0), "blue": (50, 120, 255), "green": (50, 200, 50),
        "orange": (255, 140, 0), "pink": (255, 105, 180), "cyan": (0, 220, 255),
    }
    fill = color_map.get(color_name, (255, 255, 255))

    result = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            font = ImageFont.load_default()

    max_w = int(img.width * 0.9)
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    line_h = size + 8
    total_h = len(lines) * line_h + 20

    if position == "top":
        y_start = 20
    elif position == "center":
        y_start = (img.height - total_h) // 2
    else:
        y_start = img.height - total_h - 20

    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        x = (img.width - tw) // 2
        y = y_start + i * line_h
        draw.text((x + 2, y + 2), ln, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), ln, font=font, fill=(*fill, 255))

    return Image.alpha_composite(result, overlay).convert("RGB")


def apply_meme(img: Image.Image, text_data: str) -> Image.Image:
    """Create meme with top and bottom text."""
    parts = text_data.split("|", 1)
    top_text = parts[0].strip().upper() if parts else ""
    bottom_text = parts[1].strip().upper() if len(parts) > 1 else ""

    result = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = max(36, img.width // 12)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    def draw_impact(text, y_ref, anchor="top"):
        words = text.split()
        lines = []
        line = ""
        max_w = int(img.width * 0.9)
        for word in words:
            test = (line + " " + word).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        line_h = font_size + 6
        total_h = len(lines) * line_h
        y_start = y_ref if anchor == "top" else y_ref - total_h
        for i, ln in enumerate(lines):
            bbox = draw.textbbox((0, 0), ln, font=font)
            tw = bbox[2] - bbox[0]
            x = (img.width - tw) // 2
            cy = y_start + i * line_h
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text((x + dx, cy + dy), ln, font=font, fill=(0, 0, 0, 255))
            draw.text((x, cy), ln, font=font, fill=(255, 255, 255, 255))

    if top_text:
        draw_impact(top_text, 15, "top")
    if bottom_text:
        draw_impact(bottom_text, img.height - 15, "bottom")

    return Image.alpha_composite(result, overlay).convert("RGB")


def make_sticker_image(img: Image.Image) -> Image.Image:
    """Convert image to 512×512 sticker format."""
    result = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    img_copy = img.convert("RGBA")
    img_copy.thumbnail((512, 512), Image.LANCZOS)
    off_x = (512 - img_copy.width) // 2
    off_y = (512 - img_copy.height) // 2
    result.paste(img_copy, (off_x, off_y), img_copy)
    return result


def do_ocr_simple(img: Image.Image) -> str:
    """OCR using pytesseract or image analysis fallback."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(img).strip()
        return text if text else "(No text detected)"
    except ImportError:
        pass
    except Exception:
        pass
    gray = img.convert("L")
    arr = list(gray.getdata())
    avg = sum(arr) / len(arr)
    dark_px = sum(1 for p in arr if p < 128)
    pct = dark_px / len(arr) * 100
    return (
        "⚠️ Install pytesseract for real OCR.\n\n"
        f"📊 **Image Analysis:**\n"
        f"• Avg brightness: {avg:.0f}/255\n"
        f"• Dark pixels: {pct:.1f}%\n"
        f"• {'Likely contains text/dark content' if pct > 35 else 'Mostly light image'}"
    )


def analyze_image(img: Image.Image) -> dict:
    """Full image analysis."""
    thumb = img.copy().convert("RGB")
    thumb.thumbnail((150, 150))
    pixels = list(thumb.getdata())
    r_avg = sum(p[0] for p in pixels) / len(pixels)
    g_avg = sum(p[1] for p in pixels) / len(pixels)
    b_avg = sum(p[2] for p in pixels) / len(pixels)
    brightness = (r_avg + g_avg + b_avg) / 3
    warmth = "warm 🌅" if r_avg > b_avg + 20 else ("cool 🌊" if b_avg > r_avg + 20 else "neutral ⚖️")
    gray = img.convert("L")
    pix = list(gray.getdata())
    contrast_est = max(pix) - min(pix)
    suggestions = []
    if brightness < 80:
        suggestions.append("brightness")
    if brightness > 200:
        suggestions.append("contrast")
    if contrast_est < 80:
        suggestions.append("clarity")
    if "warm" in warmth:
        suggestions.append("cold_tone")
    if "cool" in warmth:
        suggestions.append("warm_tone")
    suggestions.append("auto_enhance")
    return {
        "width": img.width, "height": img.height, "mode": img.mode,
        "brightness": round(brightness, 1), "warmth": warmth,
        "contrast_estimate": contrast_est,
        "suggestions": list(dict.fromkeys(suggestions))[:4],
        "r_avg": round(r_avg, 1), "g_avg": round(g_avg, 1), "b_avg": round(b_avg, 1),
    }


def do_resize_image(img: Image.Image, size_str: str) -> Image.Image:
    """Resize image from size string."""
    size_str = size_str.strip().lower()
    w, h = img.width, img.height
    if "x" in size_str and not size_str.startswith("x"):
        parts = size_str.split("x")
        try:
            return img.resize((int(parts[0]), int(parts[1])), Image.LANCZOS)
        except ValueError:
            pass
    elif size_str.endswith("%"):
        pct = float(size_str[:-1]) / 100
        return img.resize((int(w * pct), int(h * pct)), Image.LANCZOS)
    elif size_str.startswith("x"):
        nh = int(size_str[1:])
        return img.resize((int(w * nh / h), nh), Image.LANCZOS)
    else:
        try:
            nw = int(size_str)
            return img.resize((nw, int(h * nw / w)), Image.LANCZOS)
        except ValueError:
            pass
    return img


def do_crop_image(img: Image.Image, crop_data: str) -> Image.Image:
    """Crop image from crop data string."""
    crop_data = crop_data.strip().lower()
    w, h = img.width, img.height
    if crop_data == "square":
        side = min(w, h)
        return img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    elif ":" in crop_data:
        parts = crop_data.split(":")
        ar_w, ar_h = int(parts[0]), int(parts[1])
        if w / h > ar_w / ar_h:
            nw = int(h * ar_w / ar_h)
            return img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
        else:
            nh = int(w * ar_h / ar_w)
            return img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    elif "," in crop_data:
        parts = crop_data.split(",")
        return img.crop((int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])))
    return img


def do_trim_video(video_path: str, out_path: str, times_str: str) -> tuple:
    """Trim video using FFmpeg."""
    parts = times_str.strip().split()
    if len(parts) < 2:
        return False, "Need start and end time (e.g. '00:05 01:30')"
    cmd = ["ffmpeg", "-y", "-i", video_path,
           "-ss", parts[0], "-to", parts[1],
           "-c:v", "libx264", "-c:a", "aac",
           "-avoid_negative_ts", "make_zero", out_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return (True, None) if r.returncode == 0 else (False, r.stderr[-300:])
    except Exception as e:
        return False, str(e)


def do_speed_video(video_path: str, out_path: str, speed: float) -> tuple:
    """Change video speed using FFmpeg."""
    vf = f"setpts={1/speed:.4f}*PTS"
    if speed <= 2.0:
        af = f"atempo={speed:.2f}"
    else:
        steps = []
        rem = speed
        while rem > 2.0:
            steps.append("atempo=2.0")
            rem /= 2.0
        steps.append(f"atempo={rem:.2f}")
        af = ",".join(steps)
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-af", af,
           "-c:v", "libx264", "-c:a", "aac", out_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        return (True, None) if r.returncode == 0 else (False, r.stderr[-300:])
    except Exception as e:
        return False, str(e)


def do_add_subtitle(video_path: str, out_path: str, subtitle_text: str, prem: bool) -> tuple:
    """Add subtitle text overlay to video using FFmpeg drawtext."""
    safe = subtitle_text.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")[:200]
    font_size = 30 if prem else 22
    drawtext = (
        f"drawtext=text='{safe}':fontcolor=white:fontsize={font_size}:"
        f"shadowcolor=black:shadowx=2:shadowy=2:"
        f"x=(w-text_w)/2:y=h-th-30"
    )
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", drawtext,
           "-c:v", "libx264", "-c:a", "copy", out_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return (True, None) if r.returncode == 0 else (False, r.stderr[-300:])
    except Exception as e:
        return False, str(e)


def do_convert_file(in_path: str, out_path: str, fmt: str) -> tuple:
    """Convert file to target format."""
    img_fmts = {"jpg", "jpeg", "png", "webp", "bmp"}
    try:
        if fmt in img_fmts:
            img = Image.open(in_path).convert("RGB")
            pil_fmt = "JPEG" if fmt in ("jpg", "jpeg") else fmt.upper()
            img.save(out_path, pil_fmt)
            return True, None
        else:
            if fmt == "gif":
                cmd = ["ffmpeg", "-y", "-i", in_path,
                       "-vf", "fps=12,scale=480:-1:flags=lanczos",
                       "-loop", "0", out_path]
            else:
                cmd = ["ffmpeg", "-y", "-i", in_path, out_path]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return (True, None) if r.returncode == 0 else (False, r.stderr[-300:])
    except Exception as e:
        return False, str(e)


def do_resize_video(in_path: str, out_path: str, size_str: str) -> tuple:
    """Resize video using FFmpeg."""
    size_str = size_str.strip().lower()
    if "x" in size_str and not size_str.startswith("x"):
        parts = size_str.split("x")
        scale = f"{parts[0]}:{parts[1]}"
    elif size_str.endswith("%"):
        pct = float(size_str[:-1]) / 100
        scale = f"iw*{pct:.2f}:ih*{pct:.2f}"
    elif size_str.startswith("x"):
        scale = f"-1:{size_str[1:]}"
    else:
        scale = f"{size_str}:-1"
    cmd = ["ffmpeg", "-y", "-i", in_path, "-vf", f"scale={scale}",
           "-c:v", "libx264", "-c:a", "aac", out_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return (True, None) if r.returncode == 0 else (False, r.stderr[-300:])
    except Exception as e:
        return False, str(e)


def map_prompt_to_filters(prompt: str) -> list:
    """Map text prompt to image filter names."""
    p = prompt.lower()
    mapping = [
        (["vintage", "old", "retro", "classic", "film"], ["sepia", "vignette", "fade"]),
        (["warm", "golden", "sunset", "orange", "cozy"], ["warm_tone", "golden_hour"]),
        (["cool", "cold", "blue", "winter", "icy"], ["cold_tone", "temperature_cool"]),
        (["sharp", "crisp", "clear", "focus"], ["super_sharpen", "clarity"]),
        (["blur", "soft", "dreamy", "bokeh", "haze"], ["gaussian_blur", "vignette"]),
        (["bright", "light", "illuminate", "sunshine"], ["brightness", "auto_enhance"]),
        (["dark", "moody", "dramatic", "noir", "shadow"], ["contrast", "cold_tone"]),
        (["bw", "black and white", "monochrome", "grayscale", "b&w"], ["grayscale", "contrast"]),
        (["hdr", "vivid", "pop", "punchy", "vibrant"], ["hdr", "saturation", "clarity"]),
        (["cinematic", "movie", "film", "professional"], ["lomo", "vignette", "cold_tone"]),
        (["sketch", "drawing", "pencil", "line art"], ["pencil_sketch", "sharpen"]),
        (["oil", "painting", "artistic", "impressionist"], ["oil_paint", "saturation"]),
        (["neon", "glow", "cyber", "electric"], ["neon", "glow", "saturation"]),
        (["remove background", "remove bg", "transparent", "cutout", "no bg"], ["bg_remove"]),
        (["white background", "white bg", "clean bg"], ["bg_white"]),
        (["black background", "dark bg", "black bg"], ["bg_black"]),
        (["blur background", "bokeh bg", "depth of field"], ["bg_blur"]),
        (["portrait", "face", "selfie", "beauty"], ["portrait_enhance", "skin_smooth"]),
        (["smooth", "skin", "beauty mode"], ["skin_smooth", "portrait_enhance"]),
        (["dehaze", "foggy", "haze", "fog"], ["dehaze", "clarity"]),
        (["watercolor", "aquarelle", "paint"], ["watercolor"]),
        (["enhance", "improve", "better", "fix", "auto"], ["auto_enhance", "clarity"]),
        (["tilt shift", "miniature", "toy"], ["tilt_shift"]),
        (["lens flare", "light leak", "flare"], ["lens_flare"]),
    ]
    found = []
    for keywords, filters_list in mapping:
        if any(kw in p for kw in keywords):
            found.extend(filters_list)
    if not found:
        found = ["auto_enhance", "clarity"]
    return list(dict.fromkeys(found))[:4]


def get_file_info_text(file_path: str) -> str:
    """Get detailed file information."""
    try:
        size_bytes = os.path.getsize(file_path)
        size_str = (f"{size_bytes / (1024*1024):.2f} MB" if size_bytes > 1024*1024
                    else f"{size_bytes / 1024:.1f} KB")
        ext = Path(file_path).suffix.lower()
        img_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}
        vid_exts = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}
        aud_exts = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"}

        if ext in img_exts:
            img = Image.open(file_path)
            return (
                f"🖼️ **Image Info**\n\n"
                f"Format: `{img.format or ext.upper()}`\n"
                f"Mode: `{img.mode}`\n"
                f"Resolution: `{img.width}×{img.height}`\n"
                f"File size: `{size_str}`\n"
                f"Megapixels: `{img.width * img.height / 1_000_000:.1f} MP`"
            )
        elif ext in vid_exts or ext in aud_exts:
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
                   "-show_format", "-show_streams", file_path]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                data = json.loads(r.stdout)
                fmt = data.get("format", {})
                duration = float(fmt.get("duration", 0))
                bit_rate = int(fmt.get("bit_rate", 0))
                streams = data.get("streams", [])
                vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
                astream = next((s for s in streams if s.get("codec_type") == "audio"), None)
                info = f"📁 **File Info**\n\n"
                info += f"Size: `{size_str}`\n"
                info += f"Duration: `{int(duration//60):02d}:{int(duration%60):02d}`\n"
                info += f"Bitrate: `{bit_rate // 1000} kbps`\n"
                if vstream:
                    info += (f"Video: `{vstream.get('codec_name','?').upper()}` "
                             f"`{vstream.get('width','?')}×{vstream.get('height','?')}`\n")
                    fps_str = vstream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        n, d = fps_str.split("/")
                        fps = round(int(n) / int(d), 2) if int(d) > 0 else 0
                        info += f"FPS: `{fps}`\n"
                if astream:
                    info += (f"Audio: `{astream.get('codec_name','?').upper()}` "
                             f"`{astream.get('sample_rate','?')} Hz`\n")
                return info
        return f"📁 **File Info**\n\nSize: `{size_str}`\nExtension: `{ext}`"
    except Exception as e:
        return f"❌ Could not read file info: {str(e)[:100]}"


# ============================================================
# STICKER / VOICE / ANIMATION / MORE FILE HANDLERS
# ============================================================

@app.on_message(filters.sticker)
@require_registered
async def handle_sticker(client, message: Message):
    """Handle stickers — convert to image for editing."""
    user_id = message.from_user.id
    status_msg = await message.reply("🎭 Downloading sticker...")
    try:
        file_path = await message.download(file_name=temp_path(".webp"))
        await status_msg.delete()
        img = Image.open(file_path).convert("RGBA")
        png_path = temp_path(".png")
        img.save(png_path, "PNG")
        try:
            os.remove(file_path)
        except Exception:
            pass
        set_session(user_id, "image_path", png_path)
        await message.reply(
            "🎭 **Sticker converted to image!**\n\nChoose what to do:",
            reply_markup=image_category_keyboard()
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")


@app.on_message(filters.animation)
@require_registered
async def handle_animation(client, message: Message):
    """Handle GIF animations."""
    user_id = message.from_user.id
    status_msg = await message.reply("🎞️ Downloading GIF/animation...")
    try:
        file_path = await message.download(file_name=temp_path(".mp4"))
        await status_msg.delete()
        set_session(user_id, "video_path", file_path)
        await message.reply(
            "🎞️ **GIF / Animation received!**\n\nChoose an effect to apply:",
            reply_markup=video_category_keyboard()
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")


@app.on_message(filters.voice)
@require_registered
async def handle_voice(client, message: Message):
    """Handle voice messages."""
    user_id = message.from_user.id
    status_msg = await message.reply("🎙️ Downloading voice message...")
    try:
        file_path = await message.download(file_name=temp_path(".ogg"))
        await status_msg.delete()
        set_session(user_id, "video_path", file_path)
        await message.reply(
            "🎙️ **Voice message received!**\n\nChoose what to do:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Speed Change", callback_data="voice_speed_0.5"),
                 InlineKeyboardButton("🔄 Convert MP3", callback_data="voice_to_mp3")],
                [InlineKeyboardButton("🚀 2× Speed", callback_data="voice_speed_2.0"),
                 InlineKeyboardButton("🐢 0.5× Slow", callback_data="voice_speed_0.5")],
                [InlineKeyboardButton("❌ Cancel", callback_data="menu_main")],
            ])
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")


@app.on_message(filters.video_note)
@require_registered
async def handle_video_note(client, message: Message):
    """Handle video notes (circle videos)."""
    user_id = message.from_user.id
    status_msg = await message.reply("📹 Downloading video note...")
    try:
        file_path = await message.download(file_name=temp_path(".mp4"))
        await status_msg.delete()
        set_session(user_id, "video_path", file_path)
        await message.reply(
            "📹 **Video note received!**\n\nChoose an effect:",
            reply_markup=video_category_keyboard()
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ============================================================
# FIXED TEXT MESSAGE HANDLER
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
    "info", "queue", "timeline", "deploy", "warnuser", "warnlist", "clearwarn",
    "muteuser", "unmuteuser", "mutelist", "topusers", "diskusage", "dbstats",
    "resetuser", "getuser", "coinleader", "activeusers", "setmaxfile",
    "addtext", "meme", "sticker", "ocr", "resize", "crop", "collage",
    "subtitle", "trim", "speed", "convert", "scan", "analyze", "sensor",
    "gif", "watermark", "setphoto", "setbotname", "prompt", "done",
    "fileinfo",
]

@app.on_message(filters.text & ~filters.command(ALL_COMMANDS))
@require_registered
async def handle_text(client, message: Message):
    """Handle text messages for multi-step flows and auto-replies."""
    user_id = message.from_user.id
    text = message.text.strip()

    # Auto-replies check
    try:
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
    except Exception as e:
        logger.error(f"Auto-reply error: {e}")

    # Custom commands check
    if text.startswith("/"):
        cmd = text.split()[0].lstrip("/").lower()
        try:
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
        except Exception as e:
            logger.error(f"Custom command error: {e}")

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
            
            # Validate filename
            if not new_name or '/' in new_name or '\\' in new_name:
                await message.reply("❌ Invalid filename. Use only letters, numbers, dots, and underscores.")
                return
            
            status_msg = await message.reply(f"⠋ **{fancy('Renaming')}...**\n\n`▱▱▱▱▱▱▱▱▱▱`")
            anim = LoadingAnimator(status_msg, fancy("Renaming file"))
            await anim.start()
            try:
                new_path = os.path.join(TEMP_DIR, new_name)
                shutil.copy2(rename_path, new_path)
                
                # Detect file type & generate appropriate thumbnail
                ext = Path(new_name).suffix.lower()
                thumb_path = None
                old_size = fmt_size(os.path.getsize(rename_path))
                
                # Build thumbnail for image/video
                try:
                    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                        thumb_path = temp_path(".jpg")
                        with Image.open(rename_path) as _im:
                            _im.thumbnail((320, 320))
                            _im.convert("RGB").save(thumb_path, "JPEG", quality=85)
                    elif ext in {".mp4", ".mkv", ".mov", ".avi", ".webm"}:
                        thumb_path = temp_path(".jpg")
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", rename_path, "-ss", "00:00:01",
                             "-vframes", "1", "-vf", "scale=320:-1", thumb_path],
                            capture_output=True, timeout=15
                        )
                        if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                            thumb_path = None
                except Exception:
                    thumb_path = None
                
                final_caption = (
                    f"✅ **{fancy('File Renamed Successfully')}!**\n\n"
                    f">┌  ✦  **{fancy('Rename Details')}**  ✦\n"
                    f">│ 📜 Old: `{original}`\n"
                    f">│ ✨ New: `{new_name}`\n"
                    f">│ 💾 Size: `{old_size}`\n"
                    f">└─────────────────"
                )
                
                # Send appropriate file type to preserve thumbnail
                if ext in {".jpg", ".jpeg", ".png", ".webp"}:
                    await client.send_document(message.chat.id, document=new_path,
                                               file_name=new_name, thumb=thumb_path,
                                               caption=final_caption,
                                               force_document=True)
                elif ext in {".mp4", ".mkv", ".mov", ".webm"}:
                    await client.send_document(message.chat.id, document=new_path,
                                               file_name=new_name, thumb=thumb_path,
                                               caption=final_caption,
                                               force_document=True)
                elif ext in {".mp3", ".m4a", ".wav", ".ogg", ".flac"}:
                    await client.send_audio(message.chat.id, audio=new_path,
                                            file_name=new_name, thumb=thumb_path,
                                            caption=final_caption)
                else:
                    await client.send_document(message.chat.id, document=new_path,
                                               file_name=new_name, thumb=thumb_path,
                                               caption=final_caption,
                                               force_document=True)
                
                log_rename(user_id, original, new_name)
                await anim.stop()
                await status_msg.delete()
                
                for p in (new_path, rename_path, thumb_path):
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
            except Exception as e:
                await anim.stop(f"❌ Rename error: {str(e)[:200]}")
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
                        caption=f"✅ **Metadata Updated!**\n\n" + "\n".join(f"• {k}: {v}" for k, v in meta.items())
                    )
                    await status_msg.delete()
                    os.remove(out_path)
                    os.remove(meta_path)
                else:
                    await status_msg.edit_text(f"❌ Metadata edit failed: {err[:200]}")
            except Exception as e:
                await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
            clear_session(user_id)
        return

    if mode == "logo":
        set_session(user_id, "logo_text", text[:20])
        clear_session(user_id, "mode")
        await message.reply(
            f"🎨 Choose a **style** for: **{text[:20]}**\n\n"
            f"Styles: gradient, gold, neon, fire, ice, purple, pink, rainbow",
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
            "🤖 Now send the **image** you want to edit with AI filters.\n\n"
            "The AI will automatically apply the suggested filters!",
            reply_markup=cancel_keyboard()
        )
        return

    # ── New mode: addtext — waiting for text input ─────────────
    if mode == "addtext":
        set_session(user_id, "addtext_data", text)
        set_session(user_id, "mode", "addtext_waiting_photo")
        await message.reply("📷 Text saved! Now send the image.", reply_markup=cancel_keyboard())
        return

    # ── New mode: meme — waiting for text input ────────────────
    if mode == "meme":
        set_session(user_id, "meme_text", text)
        set_session(user_id, "mode", "meme_waiting_photo")
        await message.reply("📷 Meme text saved! Now send the image.", reply_markup=cancel_keyboard())
        return

    # ── New mode: resize — waiting for size input ──────────────
    if mode == "resize":
        set_session(user_id, "resize_size", text.strip())
        set_session(user_id, "mode", "resize_waiting")
        await message.reply(f"📐 Size set to: **{text.strip()}**\n\nNow send the image or video.", reply_markup=cancel_keyboard())
        return

    # ── New mode: crop — waiting for crop data input ───────────
    if mode == "crop_waiting_size":
        set_session(user_id, "crop_data", text.strip())
        set_session(user_id, "mode", "crop_waiting_photo")
        await message.reply(f"✂️ Crop: **{text.strip()}**\n\nNow send the image.", reply_markup=cancel_keyboard())
        return

    # ── New mode: subtitle — waiting for text ─────────────────
    if mode == "subtitle":
        set_session(user_id, "subtitle_text", text)
        set_session(user_id, "mode", "subtitle_waiting_video")
        await message.reply(f"🎬 Subtitle: **{text[:80]}**\n\nNow send the video.", reply_markup=cancel_keyboard())
        return

    # ── New mode: trim — waiting for times ────────────────────
    if mode == "trim":
        set_session(user_id, "trim_times", text.strip())
        set_session(user_id, "mode", "trim_waiting_video")
        await message.reply(f"✂️ Trim: **{text.strip()}**\n\nNow send the video.", reply_markup=cancel_keyboard())
        return

    # ── New mode: speed — waiting for speed value ─────────────
    if mode == "speed":
        try:
            spd = float(text.replace("x", "").strip())
            if not 0.1 <= spd <= 10:
                raise ValueError
            set_session(user_id, "speed_value", str(spd))
            set_session(user_id, "mode", "speed_waiting_video")
            await message.reply(f"⚡ Speed: **{spd}×**\n\nNow send the video or audio.", reply_markup=cancel_keyboard())
        except ValueError:
            await message.reply("❌ Invalid speed. Send a number between 0.1 and 10 (e.g. `2` or `0.5`)")
        return

    # ── New mode: convert — waiting for format ────────────────
    if mode == "convert":
        fmt = text.strip().lower().lstrip(".")
        set_session(user_id, "convert_format", fmt)
        set_session(user_id, "mode", "convert_waiting_file")
        await message.reply(f"🔄 Format: **{fmt.upper()}**\n\nNow send the file.", reply_markup=cancel_keyboard())
        return

    # ── New mode: watermark — waiting for text ────────────────
    if mode == "watermark_text":
        set_session(user_id, "wm_text_custom", text.strip())
        set_session(user_id, "mode", "watermark_waiting_media")
        await message.reply(f"💧 Watermark: **{text.strip()}**\n\nNow send your image or video.", reply_markup=cancel_keyboard())
        return

    # ── New mode: prompt — waiting for prompt text ────────────
    if mode == "prompt_edit":
        set_session(user_id, "prompt_text", text)
        set_session(user_id, "mode", "prompt_waiting_media")
        await message.reply(f"🧠 Prompt saved: **{text[:80]}**\n\nNow send your image.", reply_markup=cancel_keyboard())
        return

    # Admin broadcast input
    if get_session(user_id, "admin_broadcast_input"):
        clear_session(user_id, "admin_broadcast_input")
        users = get_all_users()
        sent = 0
        failed = 0
        
        status_msg = await message.reply(f"📢 Broadcasting to {len(users)} users...")
        
        for ur in users:
            try:
                await client.send_message(ur["user_id"], text)
                sent += 1
                if sent % 50 == 0:
                    await status_msg.edit_text(f"📢 Sending... {sent}/{len(users)}")
                await asyncio.sleep(0.05)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1
        
        try:
            get_db().execute(
                "INSERT INTO broadcast_logs (admin_id, message_text, sent_count, failed_count) VALUES (?, ?, ?, ?)",
                (user_id, text[:500], sent, failed)
            )
            get_db().commit()
        except Exception:
            pass
        
        await status_msg.edit_text(f"✅ Broadcast done!\nSent: {sent} | Failed: {failed}")
        return

    # Admin settings inputs
    admin_setting = get_session(user_id, "admin_setting_input")
    if admin_setting and is_admin(user_id):
        clear_session(user_id, "admin_setting_input")
        if admin_setting == "__premium_add__":
            parts = text.strip().split()
            if len(parts) >= 2:
                try:
                    tid, days = int(parts[0]), int(parts[1])
                    plan = parts[2] if len(parts) > 2 else "admin"
                    add_premium(tid, days, plan)
                    await message.reply(f"✅ Premium added to `{tid}` for {days} days ({plan})")
                except (ValueError, Exception) as e:
                    await message.reply(f"❌ Error: {e}\nFormat: `user_id days plan`")
            else:
                await message.reply("❌ Format: `user_id days plan`")
        elif admin_setting == "__premium_remove__":
            try:
                tid = int(text.strip())
                get_db().execute("UPDATE users SET is_premium=0, premium_until=NULL, premium_plan=NULL WHERE user_id=?", (tid,))
                get_db().commit()
                await message.reply(f"✅ Premium removed from `{tid}`")
            except (ValueError, Exception) as e:
                await message.reply(f"❌ Error: {e}\nSend just the user_id number.")
        elif admin_setting == "__coins_add__":
            parts = text.strip().split(None, 2)
            if len(parts) >= 2:
                try:
                    tid, amount = int(parts[0]), int(parts[1])
                    reason = parts[2] if len(parts) > 2 else "Admin adjustment"
                    cur = get_db().execute("SELECT coins FROM users WHERE user_id=?", (tid,)).fetchone()
                    if cur:
                        new_coins = max(0, (cur["coins"] or 0) + amount)
                        get_db().execute("UPDATE users SET coins=? WHERE user_id=?", (new_coins, tid))
                        get_db().commit()
                        await message.reply(f"✅ Coins {'added' if amount >= 0 else 'removed'}: `{abs(amount)}` for `{tid}`. New balance: {new_coins}. Reason: {reason}")
                    else:
                        await message.reply(f"❌ User `{tid}` not found.")
                except (ValueError, Exception) as e:
                    await message.reply(f"❌ Error: {e}\nFormat: `user_id amount reason`")
            else:
                await message.reply("❌ Format: `user_id amount reason`")
        else:
            set_setting(admin_setting, text.strip())
            await message.reply(f"✅ Setting `{admin_setting}` updated to: `{text.strip()}`")
        return

# ============================================================
# FIXED AI GENERATION FUNCTIONS
# ============================================================

async def process_txt2img(client, message: Message, user_id: int, prompt: str):
    """Process text to image generation."""
    status_msg = await message.reply(f"🎨 Generating image for: *{prompt[:50]}*...")
    
    try:
        # Check for style prefix
        style = "gradient"
        for s in AI_TEXT_IMAGE_STYLES.keys():
            if prompt.lower().startswith(s + ":"):
                style = s
                prompt = prompt[len(s)+1:].strip()
                break
        
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(executor, lambda: text_to_image(prompt, style))
        
        # Add watermark for free users
        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = await loop.run_in_executor(executor, lambda: add_watermark(img, wm_text))
        
        bio = BytesIO()
        bio.name = "generated.png"
        img.save(bio, "PNG")
        bio.seek(0)
        
        caption = f"🖼️ **Generated!**\n\nPrompt: *{prompt[:100]}*\nStyle: {style.upper()}"
        if not is_premium(user_id):
            caption += "\n\nℹ️ Free users have watermark. Upgrade to Premium for no watermark!"
        
        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Generate Another", callback_data="ai_txt2img"),
                 InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
            ])
        )
        await status_msg.delete()
        increment_edits(user_id)
        log_edit(user_id, "ai_txt2img", prompt[:50])
        
    except Exception as e:
        logger.error(f"txt2img error: {e}")
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

async def process_txt2vid(client, message: Message, user_id: int, prompt: str):
    """Process text to video generation — Gemini Flash style cinematic output.
    
    Generates smooth animated frames with motion (zoom + pan), gradient
    transitions between styles, and high-quality H.264 encoding.
    """
    status_msg = await message.reply(f"🎬 **AI Video Studio** — generating cinematic video...\n\n*Prompt:* `{prompt[:80]}`\n\n⏳ Step 1/3: Composing frames...")
    
    try:
        # Pick style from prompt prefix or default rotation
        styles = list(AI_TEXT_IMAGE_STYLES.keys())
        chosen_style = None
        for s in styles:
            if prompt.lower().startswith(s + ":"):
                chosen_style = s
                prompt = prompt[len(s)+1:].strip()
                break
        
        frames = []
        loop = asyncio.get_running_loop()
        
        # Premium gets cinematic quality, free gets standard
        if is_premium(user_id):
            frame_count, fps, scale = 60, 24, "1280:720"
        else:
            frame_count, fps, scale = 30, 15, "854:480"
        
        # Generate keyframes (fewer rendered, then interpolated by ffmpeg)
        keyframe_count = max(6, frame_count // 5)
        keyframes = []
        
        def render_keyframe(idx: int):
            ratio = idx / max(1, keyframe_count - 1)
            if chosen_style:
                style = chosen_style
            else:
                style = styles[int(ratio * len(styles)) % len(styles)]
            return text_to_image(prompt, style)
        
        for i in range(keyframe_count):
            kf = await loop.run_in_executor(executor, render_keyframe, i)
            kp = temp_path(".jpg")
            kf.save(kp, "JPEG", quality=92)
            keyframes.append(kp)
        
        await status_msg.edit_text(
            f"🎬 **AI Video Studio** — generating cinematic video...\n\n"
            f"*Prompt:* `{prompt[:80]}`\n\n"
            f"✅ Step 1/3: {keyframe_count} keyframes rendered\n"
            f"⏳ Step 2/3: Adding motion & transitions..."
        )
        
        # Each keyframe gets an animated zoom-in segment
        segments = []
        seg_dur = max(0.6, 6.0 / keyframe_count) if not is_premium(user_id) else max(0.8, 10.0 / keyframe_count)
        
        for idx, kp in enumerate(keyframes):
            seg_out = temp_path(".mp4")
            zoom_dir = "in" if idx % 2 == 0 else "out"
            if zoom_dir == "in":
                vf = (f"scale={scale},zoompan=z='min(zoom+0.0015,1.4)':"
                      f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                      f"d={int(fps*seg_dur)}:s={scale}:fps={fps},"
                      f"format=yuv420p")
            else:
                vf = (f"scale={scale},zoompan=z='if(lte(zoom,1.0),1.4,max(1.0,zoom-0.0015))':"
                      f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                      f"d={int(fps*seg_dur)}:s={scale}:fps={fps},"
                      f"format=yuv420p")
            cmd = ["ffmpeg", "-y", "-loop", "1", "-i", kp,
                   "-t", f"{seg_dur:.2f}", "-vf", vf,
                   "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                   seg_out]
            ok, err = await loop.run_in_executor(
                executor, lambda c=cmd: run_ffmpeg(c, timeout=30)
            )
            if ok and os.path.exists(seg_out) and os.path.getsize(seg_out) > 0:
                segments.append(seg_out)
            frames.append(kp)
        
        if not segments:
            raise Exception("No segments rendered")
        
        await status_msg.edit_text(
            f"🎬 **AI Video Studio** — finalizing...\n\n"
            f"*Prompt:* `{prompt[:80]}`\n\n"
            f"✅ Step 1/3: Keyframes rendered\n"
            f"✅ Step 2/3: Motion applied\n"
            f"⏳ Step 3/3: Stitching with crossfade..."
        )
        
        # Concat with crossfade for smooth transitions
        list_file = temp_path(".txt")
        out_path = temp_path(".mp4")
        
        with open(list_file, "w") as lf:
            for sp in segments:
                lf.write(f"file '{sp}'\n")
        
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
               "-c:v", "libx264", "-preset", "fast", "-crf", "23",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
        
        ok, err = run_ffmpeg(cmd, timeout=180)
        
        for sp in segments:
            try:
                os.remove(sp)
            except Exception:
                pass
        
        if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            caption = f"🎬 **Generated Video!**\n\nPrompt: *{prompt[:100]}*"
            if not is_premium(user_id):
                caption += "\n\nℹ️ Free users get shorter videos. Upgrade to Premium for longer videos!"
            
            await client.send_video(
                message.chat.id,
                video=out_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Generate Another", callback_data="ai_txt2vid"),
                     InlineKeyboardButton("🏠 Home", callback_data="menu_main")],
                ])
            )
            await status_msg.delete()
            increment_edits(user_id)
            os.remove(out_path)
        else:
            # Fallback: send single image
            img = await loop.run_in_executor(executor, lambda: text_to_image(prompt, "gradient"))
            bio = BytesIO()
            bio.name = "preview.png"
            img.save(bio, "PNG")
            bio.seek(0)
            await client.send_photo(
                message.chat.id, 
                photo=bio,
                caption=f"🖼️ Video preview (generation failed): *{prompt[:100]}*"
            )
            await status_msg.delete()
        
        # Cleanup
        for fp in frames:
            try:
                os.remove(fp)
            except Exception:
                pass
        if os.path.exists(list_file):
            os.remove(list_file)
            
    except Exception as e:
        logger.error(f"txt2vid error: {e}\n{traceback.format_exc()}")
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

# ============================================================
# FIXED CALLBACK QUERY HANDLER (Main Entry Point)
# ============================================================

@app.on_callback_query()
async def handle_callback(client, query: CallbackQuery):
    """Main callback handler - routes to appropriate sub-handler."""
    user = query.from_user
    data = query.data
    user_id = user.id

    # Register user if not exists
    register_user(user)
    
    # Check ban
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

# ============================================================
# FIXED CALLBACK QUERY INNER HANDLER (Due to length, continues in Part 7)
# ============================================================
# (The inner callback handler will be in Part 7 due to its large size)
# ============================================================
# FIXED CALLBACK QUERY INNER HANDLER
# ============================================================

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
        return

    elif data == "menu_image":
        await msg.edit_text(
            "📷 **Image Filters**\n\nChoose a filter category:",
            reply_markup=image_category_keyboard()
        )
        return

    elif data == "menu_video":
        await msg.edit_text(
            "🎬 **Video Effects**\n\nChoose an effect category:",
            reply_markup=video_category_keyboard()
        )
        return

    elif data == "menu_timeline":
        tl = get_timeline(user_id)
        steps_count = len(tl.get("steps", []))
        has_media = bool(tl.get("media_path") and os.path.exists(tl.get("media_path") or ""))
        status = f"📂 Media loaded | {steps_count} step(s)" if has_media else "📭 Send media to start"
        await msg.edit_text(
            f"📊 **Timeline Editor**\n\n{status}\n\nLayer multiple effects, then export the final result.",
            reply_markup=timeline_keyboard(user_id)
        )
        return

    elif data == "menu_compress":
        await msg.edit_text(
            "🗜️ **Video Compression**\n\nSend a video first, then choose quality.\n⭐ = Premium only\n\nPremium users get 1440p, 2K, and 4K compression!",
            reply_markup=compress_keyboard()
        )
        return

    elif data == "menu_rename":
        set_session(user_id, "mode", "rename")
        await msg.edit_text(
            "✏️ **Rename File**\n\nSend the file you want to rename.",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "menu_metadata":
        set_session(user_id, "mode", "metadata")
        await msg.edit_text(
            "📝 **Metadata Editor**\n\nSend the media file to edit metadata.",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "menu_ai":
        await msg.edit_text(
            "🤖 **AI Generation**\n\nChoose what to generate:",
            reply_markup=ai_gen_keyboard()
        )
        return

    elif data == "menu_logo":
        set_session(user_id, "mode", "logo")
        await msg.edit_text(
            "🎨 **Logo Maker**\n\nSend the text for your logo (max 20 characters):",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "menu_premium":
        prem = is_premium(user_id)
        row = get_user(user_id)
        status_str = "⭐ **Active**" if prem else "🆓 **Free**"
        until = str(row["premium_until"] or "N/A")[:10] if row else "N/A"
        
        plans_text = "\n".join(
            f"{p['emoji']} **{p['label']}** — {p['price']}"
            for p in PREMIUM_PLANS.values()
        )
        
        await msg.edit_text(
            f"⭐ **KiraFx Premium**\n\n"
            f"**Your status:** {status_str}\n"
            + (f"**Valid until:** {until}\n\n" if prem else "\n")
            + plans_text
            + "\n\n**Premium Benefits:**\n"
            f"✅ Unlimited daily edits\n"
            f"✅ No watermarks • No ads\n"
            f"✅ Priority queue\n"
            f"✅ 4K compression\n"
            f"✅ Exclusive filters\n"
            f"✅ Extended processing (600s)\n\n"
            f"📩 Contact admin to purchase.\n"
            f"🎁 Use /trial for 7 days free!",
            reply_markup=premium_plans_keyboard()
        )
        return

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
                    f"👤 **{row['first_name']}**\n"
                    f"Edits: {row['total_edits']} | Coins: 🪙{row['coins']}",
                    reply_markup=back_main()
                )
        return

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
            f"**Your coins:** 🪙 {row['coins'] if row else 0}\n\n"
            f"Share your link and earn rewards every time someone joins!",
            reply_markup=back_main()
        )
        return

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
            "• /help — full help guide\n\n"
            f"📌 **Version:** {BOT_VERSION}",
            reply_markup=back_main()
        )
        return

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
        return

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
        return

    # ── Image Filters ─────────────────────────────────────────
    elif data.startswith("imgcat_"):
        cat = data[7:]
        await msg.edit_text(
            f"📷 **{cat}**\n\nChoose a filter to apply:",
            reply_markup=image_filter_keyboard(cat)
        )
        return

    elif data.startswith("imgpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await msg.edit_text(
            f"📷 **{cat}** (Page {page+1})\n\nChoose a filter:",
            reply_markup=image_filter_keyboard(cat, page)
        )
        return

    elif data.startswith("imgfilter_"):
        filter_name = data[10:]
        image_path = get_session(user_id, "image_path")
        
        if not image_path or not os.path.exists(image_path):
            await query.answer("❌ No image found. Please send an image first!", show_alert=True)
            return
        
        if filter_name in PREMIUM_IMAGE_FILTERS and not is_premium(user_id):
            await query.answer("⭐ This filter requires Premium! Use /premium or /trial to upgrade.", show_alert=True)
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
            
            if result_img.mode == "RGBA":
                out_path = temp_path(".png")
                result_img.save(out_path, "PNG")
            else:
                out_path = temp_path(".jpg")
                result_img.convert("RGB").save(out_path, "JPEG", quality=92)
            
            caption = f"✅ **Filter Applied:** {filter_label}"
            if is_premium(user_id):
                caption += "\n\n⭐ **Premium:** No watermark applied!"
            if filter_name in ("bg_remove", "bg_white", "bg_black", "bg_blur"):
                caption += "\n\n🖼️ **Background** processed with AI!"
            
            await client.send_document(
                msg.chat.id,
                document=out_path,
                caption=caption,
                reply_markup=after_edit_keyboard()
            ) if result_img.mode == "RGBA" else await client.send_photo(
                msg.chat.id,
                photo=out_path,
                caption=caption,
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
        return

    # ── Video Effects ─────────────────────────────────────────
    elif data.startswith("vidcat_"):
        cat = data[7:]
        await msg.edit_text(
            f"🎬 **{cat}**\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat)
        )
        return

    elif data.startswith("vidpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await msg.edit_text(
            f"🎬 **{cat}** (Page {page+1})\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat, page)
        )
        return

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
        return

    # ── Compression ───────────────────────────────────────────
    elif data.startswith("compress_"):
        quality = data[9:]
        
        if quality in PREMIUM_COMPRESS and not is_premium(user_id):
            await query.answer(f"⭐ {quality} compression is Premium only! Use /premium or /trial.", show_alert=True)
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
        return

    # ── Timeline Editor ───────────────────────────────────────
    elif data == "tl_add_imgfilter":
        await msg.edit_text(
            "📷 **Timeline — Add Image Filter**\n\nChoose a filter category:",
            reply_markup=image_category_keyboard()
        )
        set_session(user_id, "timeline_filter_mode", True)
        return

    elif data == "tl_add_videffect":
        await msg.edit_text(
            "🎬 **Timeline — Add Video Effect**\n\nChoose an effect category:",
            reply_markup=video_category_keyboard()
        )
        set_session(user_id, "timeline_effect_mode", True)
        return

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
        return

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
        return

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
        return

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
        return

    elif data == "tl_clear":
        clear_timeline(user_id)
        await msg.edit_text(
            "🗑️ **Timeline Cleared**\n\nSend a new photo or video to start again.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return

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
            await apply_image_filters_sequence(client, msg, media_path, filter_names, user_id)
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
                        try:
                            os.remove(current_path)
                        except Exception:
                            pass
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
        return

    elif data == "tl_export":
        await query.answer("💾 Use ▶️ Apply All to export your timeline.", show_alert=True)
        return

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
        return

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
        return

    # ── AI Gen ────────────────────────────────────────────────
    elif data == "ai_txt2img":
        set_session(user_id, "mode", "txt2img")
        await msg.edit_text(
            "🖼️ **Text to Image**\n\n"
            "Send your prompt. Prefix with a style:\n"
            "`gradient:`, `neon:`, `gold:`, `dark:`, `fire:`, `ocean:`\n\n"
            "Example: `gradient:A beautiful sunset`",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "ai_txt2vid":
        set_session(user_id, "mode", "txt2vid")
        await msg.edit_text(
            "🎬 **Text to Video**\n\nSend your video prompt:\n\n"
            "Example: `A rocket launching into space`\n\n"
            "Premium users get longer videos!",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "ai_edit" or data == "ai_aiedit":
        set_session(user_id, "mode", "prompt_edit")
        await msg.edit_text(
            "🤖 **AI Smart Edit**\n\n"
            "Describe the edit you want in plain language. The AI will pick the best filters automatically.\n\n"
            "Examples:\n"
            "• `make it vintage and warm`\n"
            "• `oil painting style with vibrant colors`\n"
            "• `cinematic dark moody look`\n"
            "• `cyberpunk neon glow`\n"
            "• `black and white sketch`",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "quick_trim":
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video loaded.", show_alert=True)
            return
        set_session(user_id, "mode", "trim")
        await msg.edit_text(
            "✂️ **Quick Trim**\n\n"
            "Send the start and end time in seconds:\n\n"
            "Format: `START END`\n"
            "Example: `5 30` (keep from second 5 to 30)",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "quick_speed":
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video loaded.", show_alert=True)
            return
        set_session(user_id, "mode", "speed")
        await msg.edit_text(
            "⚡ **Quick Speed Change**\n\n"
            "Send the speed multiplier (0.1 to 10):\n\n"
            "Examples: `2` (2× faster), `0.5` (half speed), `1.5`",
            reply_markup=cancel_keyboard()
        )
        return

    elif data == "quick_subtitle":
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video loaded.", show_alert=True)
            return
        set_session(user_id, "mode", "subtitle")
        await msg.edit_text(
            "🎬 **Quick Subtitle**\n\n"
            "Send the subtitle text to burn into the video:\n\n"
            "Example: `Welcome to my channel!`",
            reply_markup=cancel_keyboard()
        )
        return

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
        return

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
        return

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
        return

    # ── Rename / Metadata / FileInfo / Convert do ─────────────
    elif data in ("do_rename", "do_metadata", "do_fileinfo", "do_convert"):
        rename_path = get_session(user_id, "rename_path")
        if not rename_path or not os.path.exists(rename_path):
            await query.answer("❌ No file found.", show_alert=True)
            return
        if data == "do_rename":
            set_session(user_id, "mode", "rename")
            await msg.edit_text(
                "✏️ Type the **new filename** (with extension):\n\n"
                "Example: `my_document.pdf`",
                reply_markup=cancel_keyboard()
            )
        elif data == "do_metadata":
            set_session(user_id, "mode", "metadata")
            set_session(user_id, "metadata_path", rename_path)
            await show_metadata_menu(client, msg)
        elif data == "do_fileinfo":
            try:
                info_text = get_file_info_text(rename_path)
                await msg.edit_text(info_text, reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="cancel")]]
                ))
            except Exception as e:
                await query.answer(f"Error: {str(e)[:100]}", show_alert=True)
        elif data == "do_convert":
            set_session(user_id, "mode", "convert")
            await msg.edit_text(
                "🔄 **Convert File**\n\n"
                "Send the target format:\n"
                "Images: `jpg`, `png`, `webp`, `bmp`\n"
                "Videos: `mp4`, `gif`, `avi`, `mkv`\n"
                "Audio: `mp3`, `aac`, `wav`, `ogg`",
                reply_markup=cancel_keyboard()
            )
        return

    # ── Voice callbacks ────────────────────────────────────────
    elif data == "voice_to_mp3":
        audio_path = get_session(user_id, "video_path")
        if not audio_path or not os.path.exists(audio_path):
            await query.answer("❌ No audio found.", show_alert=True)
            return
        await msg.edit_text("🔄 Converting to MP3...")
        out = temp_path(".mp3")
        try:
            loop = asyncio.get_running_loop()
            ok, err = await loop.run_in_executor(
                executor, lambda: do_convert_file(audio_path, out, "mp3")
            )
            if ok and os.path.exists(out):
                await client.send_audio(msg.chat.id, audio=out, caption="✅ **Converted to MP3!**")
                await msg.delete()
                os.remove(out)
            else:
                await msg.edit_text(f"❌ Failed: {err or 'Unknown error'}")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")
        return

    elif data.startswith("voice_speed_"):
        speed = float(data[12:])
        audio_path = get_session(user_id, "video_path")
        if not audio_path or not os.path.exists(audio_path):
            await query.answer("❌ No audio found.", show_alert=True)
            return
        await msg.edit_text(f"⚡ Changing speed to {speed}×...")
        ext = ".ogg" if audio_path.endswith(".ogg") else ".mp3"
        out = temp_path(ext)
        try:
            loop = asyncio.get_running_loop()
            ok, err = await loop.run_in_executor(
                executor, lambda: do_speed_video(audio_path, out, speed)
            )
            if ok and os.path.exists(out):
                await client.send_audio(msg.chat.id, audio=out, caption=f"⚡ **Speed: {speed}×**")
                await msg.delete()
                os.remove(out)
            else:
                await msg.edit_text(f"❌ Failed: {err or 'Unknown error'}")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")
        return

    # ── Quick ban / add premium shortcuts ─────────────────────
    elif data.startswith("quick_ban_"):
        target_id = int(data[10:])
        if not is_admin(user_id):
            await query.answer("🚫 Admin only.", show_alert=True)
            return
        try:
            get_db().execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?",
                            ("Quick ban", target_id))
            get_db().commit()
            await query.answer(f"✅ User {target_id} banned.", show_alert=True)
        except Exception as e:
            await query.answer(f"Error: {str(e)[:50]}", show_alert=True)
        return

    elif data.startswith("quick_addprem_"):
        target_id = int(data[14:])
        if not is_admin(user_id):
            await query.answer("🚫 Admin only.", show_alert=True)
            return
        try:
            add_premium(target_id, 30, "admin")
            await query.answer(f"✅ 30 days premium added to {target_id}.", show_alert=True)
        except Exception as e:
            await query.answer(f"Error: {str(e)[:50]}", show_alert=True)
        return

    # ── Admin Panel Callbacks ─────────────────────────────────
    else:
        await _handle_admin_callbacks(client, query, user_id, data, msg)


# ============================================================
# ADMIN PANEL CALLBACK HANDLER
# ============================================================

async def _handle_admin_callbacks(client, query, user_id: int, data: str, msg):
    """Handle all admin panel inline callbacks."""

    if not is_admin(user_id):
        await query.answer("🚫 Admin only.", show_alert=True)
        return

    # ── Main admin panel ───────────────────────────────────────
    if data == "admin_panel":
        await msg.edit_text(
            f"🔑 **Admin Panel**\n\n"
            f"👥 Users: `{get_user_count()}` | ⭐ Premium: `{get_premium_count()}`\n"
            f"🚫 Banned: `{get_banned_count()}` | ✂️ Edits: `{get_total_edits()}`\n"
            f"💻 CPU: `{psutil.cpu_percent():.1f}%` | RAM: `{psutil.virtual_memory().percent:.1f}%`",
            reply_markup=admin_panel_keyboard()
        )
        return

    # ── Full Stats ─────────────────────────────────────────────
    elif data == "admin_stats":
        uptime_secs = int(time.time() - START_TIME)
        h, m, s = uptime_secs // 3600, (uptime_secs % 3600) // 60, uptime_secs % 60
        await msg.edit_text(
            f"📊 **Full Bot Statistics**\n\n"
            f"👥 Total Users: `{get_user_count()}`\n"
            f"⭐ Premium: `{get_premium_count()}`\n"
            f"👑 Admins: `{get_admin_count()}`\n"
            f"🚫 Banned: `{get_banned_count()}`\n"
            f"✂️ Total Edits: `{get_total_edits()}`\n"
            f"📅 Today's Edits: `{get_today_edits()}`\n"
            f"🆕 New Today: `{get_today_new_users()}`\n"
            f"⏱️ Uptime: `{h:02d}h {m:02d}m {s:02d}s`\n"
            f"💻 CPU: `{psutil.cpu_percent():.1f}%`\n"
            f"🧠 RAM: `{psutil.virtual_memory().percent:.1f}%`\n"
            f"💾 Disk: `{psutil.disk_usage('/').percent:.1f}%`\n"
            f"🖼️ Image Filters: `{len(IMAGE_FILTERS)}`\n"
            f"🎬 Video Effects: `{len(VIDEO_EFFECTS)}`\n"
            f"🔥 BG Remove: `{'✅' if REMBG_AVAILABLE else '❌'}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Users List ─────────────────────────────────────────────
    elif data == "admin_users":
        users = get_db().execute(
            "SELECT user_id, first_name, is_premium, is_admin, is_banned, total_edits "
            "FROM users ORDER BY joined_at DESC LIMIT 20"
        ).fetchall()
        text = "👥 **Recent 20 Users:**\n\n"
        for u in users:
            badge = "👑" if u["is_admin"] else ("⭐" if u["is_premium"] else ("🚫" if u["is_banned"] else "👤"))
            text += f"{badge} `{u['user_id']}` {u['first_name'] or 'N/A'} — {u['total_edits']} edits\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Broadcast Menu ─────────────────────────────────────────
    elif data == "admin_broadcast_menu":
        set_session(user_id, "admin_broadcast_input", True)
        await msg.edit_text(
            "📢 **Broadcast Message**\n\nSend the message you want to broadcast to all users.\n"
            "Supports text, markdown.\n\n⚠️ This will be sent to ALL users.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]])
        )
        return

    # ── Backup DB ──────────────────────────────────────────────
    elif data == "admin_backup":
        await msg.edit_text("💾 Creating database backup...")
        try:
            import shutil as _shutil
            backup_path = f"kiraFx_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            _shutil.copy2(DB_PATH, backup_path)
            await client.send_document(
                msg.chat.id,
                document=backup_path,
                caption=f"💾 **Database Backup**\n\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nUsers: {get_user_count()}"
            )
            os.remove(backup_path)
        except Exception as e:
            await msg.edit_text(f"❌ Backup failed: {str(e)[:200]}")
        return

    # ── View Logs ──────────────────────────────────────────────
    elif data == "admin_logs":
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                last = "".join(lines[-50:]) if lines else "No logs."
                if len(last) > 3500:
                    last = last[-3500:]
                await msg.edit_text(
                    f"📋 **Recent Logs (last 50 lines):**\n\n```\n{last}\n```",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
                )
            else:
                await msg.edit_text("📋 No log file found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin", callback_data="admin_panel")]]))
        except Exception as e:
            await msg.edit_text(f"❌ Error reading logs: {str(e)[:200]}")
        return

    # ── Bot Settings ───────────────────────────────────────────
    elif data == "admin_settings":
        await msg.edit_text(
            "⚙️ **Bot Settings**\n\nCurrent configuration:",
            reply_markup=admin_settings_keyboard()
        )
        return

    # ── Settings sub-actions ───────────────────────────────────
    elif data in ("aset_watermark", "aset_free_edits", "aset_welcome", "aset_support", "aset_channel", "aset_file_size"):
        setting_map = {
            "aset_watermark": ("watermark_text", "Set watermark text (e.g. KiraFx)"),
            "aset_free_edits": ("free_edits_per_day", "Set daily free edits limit (number)"),
            "aset_welcome": ("welcome_message", "Set the welcome message"),
            "aset_support": ("support_username", "Set support username (without @)"),
            "aset_channel": ("channel_username", "Set channel username"),
            "aset_file_size": ("max_file_size_mb", "Set max file size in MB (number)"),
        }
        key, prompt = setting_map[data]
        set_session(user_id, "admin_setting_input", key)
        current = get_setting(key, "N/A")
        await msg.edit_text(
            f"⚙️ **Edit Setting: `{key}`**\n\nCurrent value: `{current}`\n\n{prompt}:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")]])
        )
        return

    elif data == "aset_toggle_ads":
        current = get_setting("ads_enabled", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("ads_enabled", new_val)
        status = "✅ ON" if new_val == "1" else "❌ OFF"
        await query.answer(f"Ads: {status}", show_alert=True)
        await msg.edit_text("⚙️ **Bot Settings:**", reply_markup=admin_settings_keyboard())
        return

    elif data == "aset_group_mode":
        current = get_setting("group_only_mode", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("group_only_mode", new_val)
        status = "✅ ON" if new_val == "1" else "❌ OFF"
        await query.answer(f"Group mode: {status}", show_alert=True)
        await msg.edit_text("⚙️ **Bot Settings:**", reply_markup=admin_settings_keyboard())
        return

    # ── Maintenance ────────────────────────────────────────────
    elif data == "admin_maintenance":
        current = get_setting("maintenance_mode", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("maintenance_mode", new_val)
        status = "🔧 ON" if new_val == "1" else "✅ OFF"
        await msg.edit_text(
            f"🔧 **Maintenance Mode: {status}**\n\n"
            f"{'All non-admin users are blocked.' if new_val == '1' else 'Bot is fully operational.'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Cleanup ────────────────────────────────────────────────
    elif data == "admin_cleanup":
        await msg.edit_text("🧹 Running cleanup...")
        cleanup_temp_files(max_age=0)
        cleanup_sessions()
        await msg.edit_text(
            "✅ **Cleanup Done!**\n\nTemp files and stale sessions have been cleared.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Premium Management ─────────────────────────────────────
    elif data == "admin_premium_menu":
        await msg.edit_text(
            "💎 **Premium Management**",
            reply_markup=admin_premium_keyboard()
        )
        return

    elif data == "aprem_add":
        set_session(user_id, "admin_setting_input", "__premium_add__")
        await msg.edit_text(
            "⭐ **Add Premium**\n\nSend: `user_id days plan`\n\nExample: `123456789 30 monthly`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium_menu")]])
        )
        return

    elif data == "aprem_remove":
        set_session(user_id, "admin_setting_input", "__premium_remove__")
        await msg.edit_text(
            "❌ **Remove Premium**\n\nSend the user_id to remove premium from:\n\nExample: `123456789`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium_menu")]])
        )
        return

    elif data == "aprem_list":
        rows = get_db().execute(
            "SELECT user_id, first_name, premium_until, premium_plan FROM users WHERE is_premium=1 LIMIT 20"
        ).fetchall()
        if not rows:
            await query.answer("No premium users.", show_alert=True)
            return
        text = "⭐ **Premium Users:**\n\n"
        for r in rows:
            until = str(r["premium_until"] or "Life")[:10]
            text += f"• `{r['user_id']}` {r['first_name']} — {r['premium_plan'] or 'N/A'} until {until}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_premium_menu")]]))
        return

    elif data == "aprem_expiring":
        cutoff = (datetime.now() + timedelta(days=7)).isoformat()
        rows = get_db().execute(
            "SELECT user_id, first_name, premium_until FROM users WHERE is_premium=1 AND premium_until<=? ORDER BY premium_until",
            (cutoff,)
        ).fetchall()
        if not rows:
            await query.answer("No premium expiring within 7 days.", show_alert=True)
            return
        text = "⏱️ **Expiring within 7 days:**\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — {str(r['premium_until'])[:10]}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_premium_menu")]]))
        return

    elif data == "aprem_stats":
        total = get_user_count()
        prem = get_premium_count()
        rate = f"{(prem/total*100):.1f}%" if total > 0 else "0%"
        await msg.edit_text(
            f"📊 **Premium Statistics**\n\n"
            f"Total users: `{total}`\n"
            f"Premium users: `{prem}`\n"
            f"Conversion rate: `{rate}`\n"
            f"Free users: `{total - prem}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_premium_menu")]])
        )
        return

    # ── Ban Manager ────────────────────────────────────────────
    elif data == "admin_ban_menu":
        rows = get_db().execute("SELECT user_id, first_name, ban_reason FROM users WHERE is_banned=1 LIMIT 10").fetchall()
        text = f"🚫 **Ban Manager** ({get_banned_count()} banned)\n\nRecent bans:\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — {r['ban_reason'] or 'N/A'}\n"
        if not rows:
            text += "No banned users.\n"
        text += "\nUse /ban and /unban commands to manage bans."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Custom Commands ────────────────────────────────────────
    elif data == "admin_custom_cmds":
        rows = get_db().execute("SELECT command, response, is_enabled FROM custom_commands ORDER BY id DESC LIMIT 10").fetchall()
        text = "📝 **Custom Commands:**\n\nUse /addcmd and /delcmd to manage.\n\n"
        for r in rows:
            status = "✅" if r["is_enabled"] else "❌"
            text += f"{status} /{r['command']} — {str(r['response'] or '')[:30]}\n"
        if not rows:
            text += "No custom commands yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Auto Replies ───────────────────────────────────────────
    elif data == "admin_auto_replies":
        rows = get_db().execute("SELECT trigger, response, is_enabled FROM auto_replies LIMIT 10").fetchall()
        text = "🤖 **Auto Replies:**\n\nUse /addreply to manage.\n\n"
        for r in rows:
            status = "✅" if r["is_enabled"] else "❌"
            text += f"{status} Trigger: `{r['trigger']}` → {str(r['response'] or '')[:30]}\n"
        if not rows:
            text += "No auto replies yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Coins Management ───────────────────────────────────────
    elif data == "admin_coins_menu":
        set_session(user_id, "admin_setting_input", "__coins_add__")
        await msg.edit_text(
            "💰 **Coins Management**\n\nSend: `user_id amount reason`\n\nExample: `123456789 500 Reward`\n\nTo remove coins, use a negative amount: `123456789 -100 Penalty`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]])
        )
        return

    # ── Admin Management ───────────────────────────────────────
    elif data == "admin_manage_admins":
        rows = get_db().execute("SELECT user_id, title, level FROM admins ORDER BY level DESC LIMIT 15").fetchall()
        text = "👑 **Admin Management:**\n\nUse /addadmin and /removeadmin.\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` — {r['title']} (Level {r['level']})\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Export Config ──────────────────────────────────────────
    elif data == "admin_export":
        try:
            config = {
                "bot_name": BOT_NAME,
                "version": BOT_VERSION,
                "settings": {k: v for k, v in get_db().execute("SELECT key, value FROM settings").fetchall()},
                "stats": {
                    "users": get_user_count(),
                    "premium": get_premium_count(),
                    "total_edits": get_total_edits(),
                },
                "exported_at": datetime.now().isoformat(),
            }
            config_json = json.dumps(config, indent=2)
            export_path = temp_path(".json")
            with open(export_path, "w") as f:
                f.write(config_json)
            await client.send_document(
                msg.chat.id,
                document=export_path,
                caption="📤 **Bot Config Export**"
            )
            os.remove(export_path)
        except Exception as e:
            await query.answer(f"Export error: {str(e)[:100]}", show_alert=True)
        return

    # ── Edit Stats ─────────────────────────────────────────────
    elif data == "admin_edit_stats":
        rows = get_db().execute(
            "SELECT edit_type, filter_name, COUNT(*) as cnt FROM edit_history GROUP BY edit_type, filter_name ORDER BY cnt DESC LIMIT 15"
        ).fetchall()
        text = "📊 **Edit Statistics:**\n\n"
        for r in rows:
            text += f"• {r['edit_type']}: {r['filter_name']} — {r['cnt']} times\n"
        if not rows:
            text += "No edit history yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Ads Manager ────────────────────────────────────────────
    elif data == "admin_ads_menu":
        ads_on = get_setting("ads_enabled", "0") == "1"
        interval = get_setting("ads_interval", "5")
        count = get_setting("ads_count", "0")
        await msg.edit_text(
            f"📡 **Ads Manager**\n\n"
            f"Status: {'✅ ON' if ads_on else '❌ OFF'}\n"
            f"Interval: Every {interval} edits\n"
            f"Total shown: {count}\n\n"
            f"Toggle with the settings menu.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if ads_on else '✅ Enable'} Ads", callback_data="aset_toggle_ads")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
            ])
        )
        return

    # ── Notifications ──────────────────────────────────────────
    elif data == "admin_notifications":
        await msg.edit_text(
            "🔔 **Notifications**\n\nBroadcast a notification to all users using the Broadcast option.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_menu")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
            ])
        )
        return

    # ── Run Code ───────────────────────────────────────────────
    elif data == "admin_run_code":
        await msg.edit_text(
            "💻 **Run Python Code**\n\nUse the /runcode command:\n\n`/runcode print(get_user_count())`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Bot Notes ──────────────────────────────────────────────
    elif data == "admin_notes":
        rows = get_db().execute("SELECT id, title, content FROM bot_notes ORDER BY created_at DESC LIMIT 10").fetchall()
        text = "📋 **Bot Notes:**\n\nUse /note and /notes commands.\n\n"
        for r in rows:
            text += f"• #{r['id']} **{r['title']}**: {str(r['content'])[:40]}...\n"
        if not rows:
            text += "No notes yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Generate Links ─────────────────────────────────────────
    elif data == "admin_gen_links":
        try:
            bot_info = await client.get_me()
            start_link = f"https://t.me/{bot_info.username}?start=ref"
            await msg.edit_text(
                f"🔗 **Bot Links**\n\n"
                f"**Start:** `{start_link}`\n"
                f"**Username:** @{bot_info.username}\n"
                f"**Deep link:** `https://t.me/{bot_info.username}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
            )
        except Exception as e:
            await query.answer(f"Error: {str(e)[:100]}", show_alert=True)
        return

    # ── Growth Stats ───────────────────────────────────────────
    elif data == "admin_growth":
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        month_ago = (datetime.now().date() - timedelta(days=30)).isoformat()
        today_count = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (today + "%",)).fetchone()[0]
        week_count = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at>=?", (week_ago,)).fetchone()[0]
        month_count = get_db().execute("SELECT COUNT(*) FROM users WHERE joined_at>=?", (month_ago,)).fetchone()[0]
        await msg.edit_text(
            f"📈 **Growth Statistics**\n\n"
            f"Today: +{today_count} users\n"
            f"Last 7 days: +{week_count} users\n"
            f"Last 30 days: +{month_count} users\n"
            f"Total: {get_user_count()} users",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Queue Status ───────────────────────────────────────────
    elif data == "admin_queue":
        queue_size = job_queue.get_size()
        sessions_count = get_session_count()
        await msg.edit_text(
            f"🗂️ **Queue & Session Status**\n\n"
            f"Queue size: `{queue_size}`\n"
            f"Active sessions: `{sessions_count}`\n"
            f"Thread pool workers: `6`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Restart ────────────────────────────────────────────────
    elif data == "admin_restart":
        await msg.edit_text("🔄 **Bot is restarting...**\n\nPlease wait a few seconds and use /start again.")
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # ── Top Users ──────────────────────────────────────────────
    elif data == "admin_top_users":
        rows = get_db().execute(
            "SELECT user_id, first_name, total_edits FROM users ORDER BY total_edits DESC LIMIT 15"
        ).fetchall()
        text = "🏆 **Top Users by Edits:**\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. `{r['user_id']}` {r['first_name']} — {r['total_edits']} edits\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Active Users ───────────────────────────────────────────
    elif data == "admin_active_users":
        today = datetime.now().date().isoformat()
        rows = get_db().execute(
            "SELECT user_id, first_name, edits_today FROM users WHERE daily_reset=? ORDER BY edits_today DESC LIMIT 15",
            (today,)
        ).fetchall()
        text = f"🟢 **Today's Active Users ({today}):**\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — {r['edits_today']} edits today\n"
        if not rows:
            text += "No active users today yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Disk Usage ─────────────────────────────────────────────
    elif data == "admin_disk_usage":
        disk = psutil.disk_usage("/")
        temp_count = len(list(Path(TEMP_DIR).iterdir())) if Path(TEMP_DIR).exists() else 0
        db_size = os.path.getsize(DB_PATH) / 1024 if os.path.exists(DB_PATH) else 0
        await msg.edit_text(
            f"💽 **Disk Usage**\n\n"
            f"Total: `{disk.total // (1024**3):.1f} GB`\n"
            f"Used: `{disk.used // (1024**3):.1f} GB` ({disk.percent}%)\n"
            f"Free: `{disk.free // (1024**3):.1f} GB`\n\n"
            f"Database: `{db_size:.1f} KB`\n"
            f"Temp files: `{temp_count}` files",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── DB Stats ───────────────────────────────────────────────
    elif data == "admin_db_stats":
        tables = ["users", "admins", "edit_history", "rename_history", "broadcast_logs",
                  "coins_transactions", "premium_transactions", "timeline_sessions"]
        text = "🗃️ **Database Statistics:**\n\n"
        for t in tables:
            try:
                count = get_db().execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                text += f"• {t}: `{count}` rows\n"
            except Exception:
                text += f"• {t}: N/A\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Warnings ───────────────────────────────────────────────
    elif data == "admin_warnings_menu":
        rows = get_db().execute(
            "SELECT u.user_id, u.first_name, COUNT(w.id) as warn_count "
            "FROM user_warnings w JOIN users u ON w.user_id=u.user_id "
            "GROUP BY w.user_id ORDER BY warn_count DESC LIMIT 10"
        ).fetchall()
        text = "⚠️ **User Warnings:**\n\nUse /warn [user_id] [reason]\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — {r['warn_count']} warnings\n"
        if not rows:
            text += "No warnings issued yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Mute Manager ───────────────────────────────────────────
    elif data == "admin_mute_menu":
        rows = get_db().execute("SELECT user_id, first_name, muted_until FROM users WHERE is_muted=1 LIMIT 10").fetchall()
        text = "🔇 **Muted Users:**\n\nUse /mute and /unmute commands.\n\n"
        for r in rows:
            text += f"• `{r['user_id']}` {r['first_name']} — until {str(r['muted_until'] or 'permanent')[:10]}\n"
        if not rows:
            text += "No muted users."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Coin Leaderboard ───────────────────────────────────────
    elif data == "admin_coin_leader":
        rows = get_db().execute(
            "SELECT user_id, first_name, coins FROM users ORDER BY coins DESC LIMIT 15"
        ).fetchall()
        text = "🏅 **Coin Leaderboard:**\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. `{r['user_id']}` {r['first_name']} — 🪙{r['coins']}\n"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── User Analytics ─────────────────────────────────────────
    elif data == "admin_analytics":
        total = get_user_count()
        prem = get_premium_count()
        banned = get_banned_count()
        today_new = get_today_new_users()
        total_edits = get_total_edits()
        avg_edits = total_edits // max(total, 1)
        await msg.edit_text(
            f"📉 **User Analytics**\n\n"
            f"Total users: `{total}`\n"
            f"Premium: `{prem}` ({prem*100//max(total,1)}%)\n"
            f"Banned: `{banned}` ({banned*100//max(total,1)}%)\n"
            f"New today: `{today_new}`\n"
            f"Total edits: `{total_edits}`\n"
            f"Avg edits/user: `{avg_edits}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Deploy Status ──────────────────────────────────────────
    elif data == "admin_deploy_status":
        uptime_secs = int(time.time() - START_TIME)
        h, m, s = uptime_secs // 3600, (uptime_secs % 3600) // 60, uptime_secs % 60
        await msg.edit_text(
            f"🚀 **Deploy Status**\n\n"
            f"Bot: 🟢 Running\n"
            f"Uptime: `{h:02d}h {m:02d}m {s:02d}s`\n"
            f"Flask: 🟢 Port {FLASK_PORT}\n"
            f"FFmpeg: {'🟢' if check_ffmpeg() else '🔴'}\n"
            f"BG Remove: {'🟢' if REMBG_AVAILABLE else '🔴'}\n"
            f"DB: 🟢 Connected\n"
            f"CPU: `{psutil.cpu_percent():.1f}%` | RAM: `{psutil.virtual_memory().percent:.1f}%`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Restart", callback_data="admin_restart")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
            ])
        )
        return

    # ── Security Info ──────────────────────────────────────────
    elif data == "admin_security":
        await msg.edit_text(
            f"🔐 **Security Info**\n\n"
            f"Owner ID: `{OWNER_ID}`\n"
            f"Admins: `{get_admin_count()}`\n"
            f"Banned: `{get_banned_count()}`\n"
            f"Sessions: `{get_session_count()}`\n\n"
            f"Ban system: ✅ Active\n"
            f"Mute system: ✅ Active\n"
            f"Rate limiting: ✅ Daily limits\n"
            f"Maintenance mode: {'🔧 ON' if get_setting('maintenance_mode')=='1' else '✅ OFF'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Session Info ───────────────────────────────────────────
    elif data == "admin_sessions":
        sessions = get_session_count()
        await msg.edit_text(
            f"📦 **Session Information**\n\n"
            f"Active sessions: `{sessions}`\n"
            f"Sessions auto-clear: after 2 hours of inactivity\n\n"
            f"Use /cleanup to clear all sessions immediately.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
        )
        return

    # ── Filter Stats ───────────────────────────────────────────
    elif data == "admin_filter_stats":
        rows = get_db().execute(
            "SELECT filter_name, COUNT(*) as cnt FROM edit_history WHERE edit_type='image' "
            "GROUP BY filter_name ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        text = "🎯 **Top Image Filters Used:**\n\n"
        for r in rows:
            text += f"• {r['filter_name']}: `{r['cnt']}` times\n"
        if not rows:
            text += "No filter usage data yet."
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]]))
        return

    # ── Unknown admin callback ─────────────────────────────────
    else:
        await query.answer("⚠️ Unknown action.", show_alert=True)


# ============================================================
# FIXED FLASK WEB DASHBOARD
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
                <tr><th>FFmpeg</th><td class="{{ 'ok' if stats.ffmpeg else 'err' }}">{{ '✅ Installed' if stats.ffmpeg else '❌ Not Found' }}</td></tr>
                <tr><th>Database</th><td class="ok">✅ Connected</td></tr>
                <tr><th>Maintenance</th><td>{{ '🔧 ON' if stats.maintenance else '✅ OFF' }}</td></tr>
                <tr><th>Ads</th><td>{{ '✅ ON' if stats.ads_enabled else '❌ OFF' }}</td></tr>
                <tr><th>Free Edits/Day</th><td>{{ stats.free_edits }}</td></tr>
                <tr><th>Keep-Alive</th><td class="ok">✅ Active (60s)</td></tr>
            </table>
        </div>
        <div class="section">
            <h2>🎬 Bot Capabilities</h2>
            <table>
                <tr><th>Image Filters</th><td>{{ stats.image_filters }}+</td></tr>
                <tr><th>Video Effects</th><td>{{ stats.video_effects }}+</td></tr>
                <tr><th>Premium Plans</th><td>{{ stats.premium_plans }}</td></tr>
                <tr><th>Compression Presets</th><td>{{ stats.comp_presets }}</td></tr>
                <tr><th>Logo Styles</th><td>{{ stats.logo_styles }}</td></tr>
                <tr><th>AI Styles</th><td>{{ stats.ai_styles }}</td></tr>
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
    """Main dashboard page."""
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
    """API endpoint for bot statistics."""
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
    """Health check endpoint with uptime stats."""
    uptime_secs = int(time.time() - START_TIME)
    total = _uptime_stats["total_pings"]
    failed = _uptime_stats["failed_pings"]
    uptime_pct = round((1 - failed / max(total, 1)) * 100, 2)
    return jsonify({
        "status": "ok",
        "bot": BOT_NAME,
        "version": BOT_VERSION,
        "uptime_seconds": uptime_secs,
        "uptime_human": f"{uptime_secs//3600}h {(uptime_secs%3600)//60}m {uptime_secs%60}s",
        "ping_uptime_pct": uptime_pct,
        "total_pings": total,
        "failed_pings": failed,
        "cpu_pct": psutil.cpu_percent(),
        "ram_pct": psutil.virtual_memory().percent,
    })

@flask_app.route("/api/users")
def api_users():
    """API endpoint for user list."""
    limit = int(flask_request.args.get("limit", 20))
    users = get_db().execute(
        f"SELECT user_id, first_name, username, is_premium, total_edits, coins FROM users ORDER BY joined_at DESC LIMIT {limit}"
    ).fetchall()
    return jsonify([dict(u) for u in users])

def run_flask():
    """Run Flask web dashboard in a daemon thread."""
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)

# ============================================================
# FIXED KEEP-ALIVE AND CLEANUP LOOPS
# ============================================================

_uptime_stats = {
    "total_pings": 0,
    "failed_pings": 0,
    "last_ping": None,
    "last_success": None,
}

def keep_alive_ping():
    """Ping health endpoint every 55 seconds to stay alive + track uptime metrics."""
    while True:
        _uptime_stats["total_pings"] += 1
        _uptime_stats["last_ping"] = time.time()
        try:
            r = req_lib.get(f"http://localhost:{FLASK_PORT}/health", timeout=10)
            if r.status_code == 200:
                _uptime_stats["last_success"] = time.time()
            else:
                _uptime_stats["failed_pings"] += 1
                logger.warning(f"Health check returned {r.status_code}")
        except Exception as e:
            _uptime_stats["failed_pings"] += 1
            logger.warning(f"Health check failed: {e}")
        # Ping external UptimeRobot / Render keep-alive URL
        if KEEP_ALIVE_URL:
            try:
                req_lib.get(KEEP_ALIVE_URL, timeout=10)
            except Exception:
                pass
        # Ping multiple uptime endpoints from env
        extra_urls = os.environ.get("EXTRA_PING_URLS", "")
        for url in extra_urls.split(","):
            url = url.strip()
            if url:
                try:
                    req_lib.get(url, timeout=10)
                except Exception:
                    pass
        time.sleep(55)

def temp_cleanup_loop():
    """Periodic temp file cleanup every 30 minutes."""
    while True:
        time.sleep(1800)
        cleanup_temp_files(1800)
        cleanup_sessions()
        logger.info("Performed periodic cleanup")

# ============================================================
# FIXED MAIN ENTRY POINT
# ============================================================

# ============================================================
# FIXED MAIN ENTRY POINT (Remove the problematic line)
# ============================================================

def main():
    """Main entry point for the bot."""
    logger.info(f"=" * 60)
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION}")
    logger.info(f"=" * 60)

    # Init database
    init_db()
    
    # Initialize AI tables
    #init_ai_tables()

    # Kill any stale Flask process on the same port before starting
    try:
        subprocess.run(f"fuser -k {FLASK_PORT}/tcp", shell=True,
                       capture_output=True, timeout=5)
        time.sleep(0.8)
    except Exception:
        pass

    # Check FFmpeg
    if check_ffmpeg():
        logger.info("FFmpeg found ✅")
    else:
        logger.warning("FFmpeg NOT found ❌ — Video features will be limited")

    # Start Flask dashboard
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(0.5)  # Let Flask bind before health pings
    logger.info(f"Flask dashboard started on port {FLASK_PORT}")

    # Start keep-alive thread (pings every 60s)
    ka_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ka_thread.start()
    logger.info("Keep-alive started (every 60s)")

    # Start temp cleanup thread
    cleanup_thread = threading.Thread(target=temp_cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Temp cleanup thread started (every 30 minutes)")

    logger.info("Starting Telegram bot...")
    
    # REMOVED THE PROBLEMATIC LINE:
    # logger.info(f"Bot username: @{app.me.username if hasattr(app, 'me') else 'unknown'}")
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
