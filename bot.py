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
                "📷 **Photo Received!**\n\n"
                "Choose a filter category to apply:",
                reply_markup=image_category_keyboard()
            )

        elif media_type == "video":
            if mode == "compress":
                set_session(user_id, "video_path", file_path)
                clear_session(user_id, "mode")
                await message.reply(
                    "🗜️ **Choose Compression Quality:**\n\n"
                    "⭐ = Premium only\n"
                    "Premium users get 1440p, 2K, and 4K compression!",
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
                    "🎬 **Video Received!**\n\n"
                    "Choose an effect category to apply:",
                    reply_markup=video_category_keyboard()
                )

        elif media_type in ("document", "audio"):
            if mode == "rename":
                original_name = getattr(message.document or message.audio, "file_name", "file")
                set_session(user_id, "rename_path", file_path)
                set_session(user_id, "rename_original", original_name)
                clear_session(user_id, "mode")
                await message.reply(
                    f"✏️ **Rename File**\n\n"
                    f"Original name: `{original_name}`\n\n"
                    f"Type the **new filename** (with extension):\n"
                    f"Example: `my_document.pdf`",
                    reply_markup=cancel_keyboard()
                )
            elif mode == "metadata":
                set_session(user_id, "metadata_path", file_path)
                clear_session(user_id, "mode")
                await show_metadata_menu(client, message)
            else:
                original_name = getattr(message.document or message.audio, "file_name", "file")
                set_session(user_id, "rename_path", file_path)
                set_session(user_id, "rename_original", original_name)
                await message.reply(
                    f"📁 **File Received!**\n\n"
                    f"File: `{original_name}`\n\n"
                    f"What would you like to do?",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ Rename", callback_data="do_rename"),
                         InlineKeyboardButton("📝 Edit Metadata", callback_data="do_metadata")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
                    ])
                )
    except Exception as e:
        logger.error(f"Error in handle_media_for_edit: {e}")
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
            
            status_msg = await message.reply(f"✏️ Renaming to `{new_name}`...")
            try:
                new_path = os.path.join(TEMP_DIR, new_name)
                shutil.copy2(rename_path, new_path)
                
                await client.send_document(
                    message.chat.id,
                    document=new_path,
                    file_name=new_name,
                    caption=f"✅ **Renamed!**\n\nOriginal: `{original}`\nNew name: `{new_name}`",
                )
                log_rename(user_id, original, new_name)
                await status_msg.delete()
                os.remove(new_path)
                os.remove(rename_path)
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
    """Process text to video generation."""
    status_msg = await message.reply(f"🎬 Generating video for: *{prompt[:50]}*...")
    
    try:
        styles = list(AI_TEXT_IMAGE_STYLES.keys())
        frames = []
        loop = asyncio.get_running_loop()
        
        # Generate frames (fewer for free users)
        frame_count = 24 if is_premium(user_id) else 12
        
        for i in range(frame_count):
            ratio = i / frame_count
            style = styles[int(ratio * len(styles)) % len(styles)]
            frame = await loop.run_in_executor(executor, lambda s=style: text_to_image(f"{prompt}", s))
            frame_path = temp_path(".jpg")
            frame.save(frame_path, "JPEG", quality=85)
            frames.append(frame_path)
        
        # Create video from frames
        list_file = temp_path(".txt")
        out_path = temp_path(".mp4")
        
        with open(list_file, "w") as lf:
            for fp in frames:
                lf.write(f"file '{fp}'\n")
                lf.write("duration 0.125\n")
        
        fps = 8 if is_premium(user_id) else 4
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", list_file, "-vf", f"fps={fps},scale=800:600", "-pix_fmt", "yuv420p", out_path]
        
        ok, err = run_ffmpeg(cmd, timeout=120)
        
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
        until = str(row.get("premium_until", "N/A") or "N/A")[:10] if row else "N/A"
        
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
            
            out_path = temp_path(".jpg")
            result_img.save(out_path, "JPEG", quality=92)
            
            caption = f"✅ **Filter Applied:** {filter_label}"
            if is_premium(user_id):
                caption += "\n\n⭐ **Premium:** No watermark applied!"
            
            await client.send_photo(
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

    elif data == "ai_edit":
        set_session(user_id, "mode", "aiedit_prompt")
        await msg.edit_text(
            "🤖 **AI Edit Prompt**\n\n"
            "Describe the edit you want (e.g., 'make it vintage and warm').\n"
            "Then I'll suggest filters based on your description.\n\n"
            "Example: `make it look like an oil painting with warm colors`",
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

    # ── Rename / Metadata do ──────────────────────────────────
    elif data in ("do_rename", "do_metadata"):
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
        else:
            set_session(user_id, "mode", "metadata")
            set_session(user_id, "metadata_path", rename_path)
            await show_metadata_menu(client, msg)
        return

    # ── Admin Panel Callbacks (Due to length, these will continue in Part 8) ──
    else:
        # Admin panel callbacks are handled in Part 8
        await _handle_admin_callbacks(client, query, user_id, data, msg)


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
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "bot": BOT_NAME,
        "version": BOT_VERSION,
        "uptime": int(time.time() - START_TIME)
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
