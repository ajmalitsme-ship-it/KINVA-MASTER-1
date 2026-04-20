#!/usr/bin/env python3
"""
KiraFx Media Editor Bot v1.0
A comprehensive Telegram bot for image/video editing with premium features.
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
        InlineKeyboardButton, User
    )
    from pyrogram.errors import FloodWait, UserNotParticipant, RPCError
except ImportError:
    print("Installing pyrogram...")
    os.system("pip install pyrogram tgcrypto")
    from pyrogram import Client, filters, enums
    from pyrogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup,
        InlineKeyboardButton, User
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
    from flask import Flask, render_template_string, jsonify, request
except ImportError:
    os.system("pip install flask")
    from flask import Flask, render_template_string, jsonify, request

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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8623600399:AAGNn_d6Lq5DRrwelD_rvOUfgsM-jyk8Kf8")
API_ID = int(os.environ.get("API_ID", 27806628))
API_HASH = os.environ.get("API_HASH", "25d88301e886b82826a525b7cf52e090")
OWNER_ID = int(os.environ.get("OWNER_ID", "8525952693"))
DB_PATH = os.environ.get("DB_PATH", "kiraFx.db")
TEMP_DIR = os.environ.get("TEMP_DIR", "temp_files")
LOG_FILE = os.environ.get("LOG_FILE", "kiraFx.log")
FLASK_PORT = int(os.environ.get("PORT", "5000"))
FREE_EDITS_PER_DAY = int(os.environ.get("FREE_EDITS_PER_DAY", "6"))
KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "https://kinva-master-1-hf70.onrender.com/")
BOT_NAME = "KiraFx Media Editor Bot v7.0 Ultra Premium Edition"
BOT_VERSION = "1.0"
START_TIME = time.time()

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
executor = ThreadPoolExecutor(max_workers=4)

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
            is_admin INTEGER DEFAULT 0,
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
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            title TEXT DEFAULT 'Admin',
            added_by INTEGER,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        INSERT OR IGNORE INTO settings (key, value) VALUES
            ('watermark_text', 'KiraFx'),
            ('free_edits_per_day', '10'),
            ('ads_enabled', '0'),
            ('ads_interval', '5'),
            ('maintenance_mode', '0'),
            ('welcome_message', 'Welcome to KiraFx Bot!'),
            ('group_only_mode', '0');
    """)
    conn.commit()

    # Ensure owner is in users and admins table
    if OWNER_ID:
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, is_admin) VALUES (?, 'Owner', 1)",
            (OWNER_ID,)
        )
        c.execute(
            "INSERT OR IGNORE INTO admins (user_id, title, added_by) VALUES (?, 'Owner', ?)",
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
    ref_code = hashlib.md5(str(user.id).encode()).hexdigest()[:8]
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
            until = datetime.fromisoformat(row["premium_until"])
            if until > datetime.now():
                return True
            else:
                get_db().execute("UPDATE users SET is_premium=0 WHERE user_id=?", (user_id,))
                get_db().commit()
                return False
        return True
    return False

def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    row = get_user(user_id)
    return bool(row and row["is_admin"])

def is_banned(user_id: int) -> bool:
    row = get_user(user_id)
    if not row or not row["is_banned"]:
        return False
    if row["ban_until"]:
        until = datetime.fromisoformat(row["ban_until"])
        if until < datetime.now():
            get_db().execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
            get_db().commit()
            return False
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

def increment_edits(user_id: int):
    today = datetime.now().date().isoformat()
    get_db().execute(
        "UPDATE users SET edits_today=edits_today+1, total_edits=total_edits+1, daily_reset=? WHERE user_id=?",
        (today, user_id)
    )
    get_db().commit()

def add_premium(user_id: int, days: int):
    until = (datetime.now() + timedelta(days=days)).isoformat()
    get_db().execute(
        "UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?",
        (until, user_id)
    )
    get_db().commit()

def get_all_users() -> List[sqlite3.Row]:
    return get_db().execute("SELECT * FROM users").fetchall()

def get_user_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]

def get_premium_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]

def get_total_edits() -> int:
    row = get_db().execute("SELECT SUM(total_edits) FROM users").fetchone()
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
    """Remove sessions older than 1 hour."""
    cutoff = time.time() - 3600
    stale = [uid for uid, s in user_sessions.items() if s.get("created", 0) < cutoff]
    for uid in stale:
        del user_sessions[uid]

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
    """Check if FFmpeg is installed."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def validate_video(path: str) -> bool:
    """Validate a video file using FFprobe."""
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
    """Get video metadata."""
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
    """Run FFmpeg command with error handling."""
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

def ffmpeg_apply_video_filter(input_path: str, output_path: str, vf: str,
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

    # Strategy 2: Simple copy audio, just video filter
    cmd2 = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd2 += ["-vf", vf]
    cmd2 += ["-c:a", "copy", output_path]

    ok, err = run_ffmpeg(cmd2, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    # Strategy 3: Stream copy only
    cmd3 = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
    ok, err = run_ffmpeg(cmd3, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    return False, f"All strategies failed: {err}"

def temp_path(ext: str = "") -> str:
    """Generate a temporary file path."""
    name = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return os.path.join(TEMP_DIR, f"{name}{ext}")

def cleanup_temp_files(max_age: int = 3600):
    """Remove temp files older than max_age seconds."""
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
    # Special
    "vignette": "Vignette",
    "border": "Border",
    "rounded_corners": "Rounded Corners",
    "shadow": "Shadow",
    "glow": "Glow",
    "duotone": "Duotone",
    "sunset": "Sunset",
    "winter": "Winter",
    "autumn": "Autumn",
    "spring": "Spring",
    "night": "Night",
    "wave": "Wave",
    "hue_shift": "Hue Shift",
    "temperature_warm": "Warm Temperature",
    "temperature_cool": "Cool Temperature",
    "channel_mixer": "Channel Mixer",
    "skew": "Skew",
    "color_balance": "Color Balance",
    "firework": "Firework",
    "perspective": "Perspective",
    "blur_background": "Blur Background",
}

IMAGE_FILTER_CATEGORIES = {
    "🔧 Basic": ["blur", "sharpen", "grayscale", "sepia", "edge_enhance", "contour",
                  "emboss", "smooth", "detail", "gaussian_blur", "unsharp_mask", "median_filter"],
    "🎨 Artistic": ["oil_paint", "watercolor", "sketch", "pencil_sketch", "cartoon",
                    "pixelate", "glitch", "vintage", "neon", "pointillism", "mosaic",
                    "pastel", "comic", "stained_glass"],
    "🌈 Color": ["brightness", "contrast", "saturation", "auto_color", "equalize",
                  "posterize", "solarize", "invert", "golden_hour", "cold_tone",
                  "warm_tone", "hue_shift", "temperature_warm", "temperature_cool",
                  "channel_mixer", "color_balance"],
    "↔️ Transform": ["rotate_90", "rotate_180", "rotate_270", "flip_h", "flip_v",
                      "resize_50", "resize_200", "crop_center", "mirror", "skew", "perspective"],
    "✨ Special": ["vignette", "border", "rounded_corners", "shadow", "glow", "duotone",
                   "sunset", "winter", "autumn", "spring", "night", "wave", "firework",
                   "blur_background"],
}

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
        sepia_px = [(min(int(p * 1.07), 255), int(p * 0.74), int(p * 0.43)) for p in px]
        sepia.putdata(sepia_px)
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
    elif filter_name == "warm_tone":
        return apply_image_filter(img, "golden_hour")
    elif filter_name == "hue_shift":
        hsv = img.convert("HSV") if hasattr(img, "convert") else img
        return ImageEnhance.Color(img).enhance(1.3)
    elif filter_name == "temperature_warm":
        return apply_image_filter(img, "golden_hour")
    elif filter_name == "temperature_cool":
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
        left = (w - s) // 2
        top = (h - s) // 2
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
        for corner in [(0, 0), (img.width - 2 * radius, 0),
                       (0, img.height - 2 * radius), (img.width - 2 * radius, img.height - 2 * radius)]:
            draw.ellipse([corner[0], corner[1], corner[0] + 2 * radius, corner[1] + 2 * radius], fill=255)
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
        g = g.point(lambda x: min(x + 20, 255))
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
        colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (238, 130, 238)]
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
        result = Image.composite(img, blurred, mask)
        return result
    else:
        return img

def add_watermark(img: Image.Image, text: str = "KiraFx") -> Image.Image:
    """Add text watermark to image."""
    result = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = result.width - tw - 10
    y = result.height - th - 10
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 120))
    result = Image.alpha_composite(result, overlay)
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
    "change_resolution": "Change Resolution",
    "scale_square": "Scale to Square",
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
    "🎬 Basic": ["trim", "reverse", "loop", "extract_gif", "change_resolution", "scale_square"],
    "🎨 Filters": ["bw_video", "sepia_video", "vintage_video", "cinematic", "glitch_video",
                   "pixelate_video", "sketch_video", "cartoon_video", "neon_video",
                   "sunset_video", "winter_video", "vibrant", "haze", "vhs", "rgb_shift", "soft_glow"],
    "🔊 Audio": ["mute_video", "extract_audio", "volume_up", "volume_down",
                  "boost_bass", "echo", "reverb", "normalize_audio", "fade_audio"],
    "⚡ Speed": ["speed_025", "speed_05", "speed_075", "speed_15", "speed_2", "speed_3", "speed_4"],
    "🎭 Transitions": ["fade_in", "fade_out"],
    "🔧 Advanced": ["rotate_video_90", "crop_video", "stabilize", "denoise_video",
                    "text_overlay", "watermark_video", "color_grading",
                    "face_blur", "colorize_video", "chroma_key", "pip"],
}

VIDEO_FILTER_MAP = {
    "bw_video": "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
    "sepia_video": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "vintage_video": "curves=vintage,vignette=PI/4",
    "cinematic": "curves=psych,vignette=PI/6",
    "glitch_video": "hue=h=random*360",
    "pixelate_video": "scale=iw/10:ih/10,scale=iw*10:ih*10:flags=neighbor",
    "sketch_video": "edgedetect=low=0.1:high=0.4,negate",
    "cartoon_video": "edgedetect=low=0.1:high=0.3",
    "neon_video": "edgedetect,negate,colorchannelmixer=0:0:0:0:0:1:0:0:0:0:1:0",
    "sunset_video": "curves=r='0/0 0.5/0.8 1/1':g='0/0 0.5/0.6 1/0.8':b='0/0 0.5/0.3 1/0.6'",
    "winter_video": "curves=b='0/0 0.5/0.8 1/1':r='0/0 0.5/0.4 1/0.7'",
    "vibrant": "hue=s=2,eq=contrast=1.2:saturation=1.5",
    "haze": "curves=all='0/0 0.1/0.15 1/1'",
    "vhs": "noise=alls=10:allf=t,chromashift=crh=2:crv=2",
    "rgb_shift": "split[a][b],[a]chromashift=crh=5:crv=0[a1],[b]chromashift=crh=-5:crv=0[b1],[a1][b1]blend=all_mode=difference",
    "soft_glow": "gblur=sigma=10,blend=all_mode=screen:all_opacity=0.5",
    "fade_in": "fade=t=in:st=0:d=1",
    "fade_out": "fade=t=out:st=0:d=1",
    "color_grading": "curves=r='0/0.1 0.5/0.5 1/0.9':g='0/0.05 0.5/0.5 1/0.95':b='0/0 0.5/0.4 1/0.8'",
    "colorize_video": "hue=h=220:s=2",
    "denoise_video": "hqdn3d=4:3:6:4.5",
    "stabilize": "deshake",
    "crop_video": "crop=iw/2:ih/2",
    "rotate_video_90": "transpose=1",
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
        # FFmpeg atempo filter supports 0.5-2.0 range, chain for extremes
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
        cmd = ["ffmpeg", "-y", "-stream_loop", "1", "-i", input_path,
               "-c", "copy", output_path]
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
        return ffmpeg_apply_video_filter(input_path, output_path, None,
                                          "aecho=0.8:0.88:60:0.4")

    elif effect == "reverb":
        return ffmpeg_apply_video_filter(input_path, output_path, None,
                                          "aecho=0.8:0.9:1000:0.3")

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
        # Simple blur entire frame as fallback (real face detection needs DNN)
        vf = "boxblur=20:1"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "chroma_key":
        vf = "chromakey=green:0.1:0.2"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    elif effect == "pip":
        # Self PiP effect
        vf = f"split[a][b],[b]scale=iw/4:ih/4[small],[a][small]overlay=main_w-overlay_w-10:10"
        return ffmpeg_apply_video_filter(input_path, output_path, vf)

    else:
        return False, f"Unknown effect: {effect}"

# ============================================================
# COMPRESSION PRESETS
# ============================================================
COMPRESSION_PRESETS = {
    "144p":  {"width": 256,  "height": 144,  "bitrate": "100k",  "audio_bitrate": "64k",  "crf": 35, "preset": "ultrafast"},
    "240p":  {"width": 426,  "height": 240,  "bitrate": "300k",  "audio_bitrate": "64k",  "crf": 32, "preset": "ultrafast"},
    "360p":  {"width": 640,  "height": 360,  "bitrate": "500k",  "audio_bitrate": "96k",  "crf": 28, "preset": "fast"},
    "480p":  {"width": 854,  "height": 480,  "bitrate": "800k",  "audio_bitrate": "128k", "crf": 25, "preset": "fast"},
    "720p":  {"width": 1280, "height": 720,  "bitrate": "1500k", "audio_bitrate": "128k", "crf": 23, "preset": "medium"},
    "1080p": {"width": 1920, "height": 1080, "bitrate": "3000k", "audio_bitrate": "192k", "crf": 20, "preset": "medium"},
    "1440p": {"width": 2560, "height": 1440, "bitrate": "6000k", "audio_bitrate": "256k", "crf": 18, "preset": "slow"},
    "2K":    {"width": 2048, "height": 1080, "bitrate": "4000k", "audio_bitrate": "256k", "crf": 18, "preset": "slow"},
    "4K":    {"width": 3840, "height": 2160, "bitrate": "12000k","audio_bitrate": "320k", "crf": 15, "preset": "veryslow"},
}

def compress_video(input_path: str, output_path: str, quality: str, timeout: int = 300) -> Tuple[bool, str]:
    """Compress video to specified quality preset."""
    if not validate_video(input_path):
        return False, "Invalid or corrupted video file."

    preset_data = COMPRESSION_PRESETS.get(quality)
    if not preset_data:
        return False, f"Unknown quality preset: {quality}"

    w = preset_data["width"]
    h = preset_data["height"]
    vb = preset_data["bitrate"]
    ab = preset_data["audio_bitrate"]
    crf = preset_data["crf"]
    speed = preset_data["preset"]

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease",
        "-c:v", "libx264", "-crf", str(crf), "-preset", speed,
        "-b:v", vb, "-maxrate", vb, "-bufsize", str(int(vb[:-1]) * 2) + "k",
        "-c:a", "aac", "-b:a", ab,
        "-movflags", "+faststart",
        output_path
    ]

    ok, err = run_ffmpeg(cmd, timeout)
    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, ""

    # Fallback: simpler command
    cmd2 = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={w}:{h}",
        "-c:v", "libx264", "-crf", str(crf),
        "-c:a", "aac",
        output_path
    ]
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

    # Draw gradient background
    for x in range(width):
        ratio = x / width
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.line([(x, height - 40), (x, height - 5)], fill=(r, g, b))

    # Text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Main text with gradient effect
    bbox = draw.textbbox((0, 0), text, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = (height - th) // 2 - 20

    # Shadow
    draw.text((tx + 3, ty + 3), text, font=font_large, fill=(0, 0, 0))
    # Main text color from style
    main_color = tuple(min(c + 100, 255) for c in colors[1])
    draw.text((tx, ty), text, font=font_large, fill=main_color)

    # Branding
    draw.text((10, height - 35), "KiraFx Bot v7.0", font=font_small,
               fill=tuple(colors[1]))

    return img

# ============================================================
# TEXT TO IMAGE GENERATION
# ============================================================
AI_TEXT_IMAGE_STYLES = {
    "gradient": {"bg": (20, 20, 40), "colors": [(100, 50, 255), (255, 50, 200)]},
    "neon":     {"bg": (0, 5, 15),   "colors": [(0, 255, 200), (0, 150, 255)]},
    "gold":     {"bg": (10, 5, 0),   "colors": [(255, 200, 0), (200, 150, 0)]},
    "dark":     {"bg": (10, 10, 10), "colors": [(180, 180, 200), (100, 100, 150)]},
    "fire":     {"bg": (10, 0, 0),   "colors": [(255, 100, 0), (255, 200, 0)]},
}

def text_to_image(prompt: str, style: str = "gradient") -> Image.Image:
    """Generate a styled image from a text prompt."""
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

    # Decorative elements
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r_val = random.randint(2, 8)
        color = random.choice(colors)
        draw.ellipse([x - r_val, y - r_val, x + r_val, y + r_val],
                      fill=(*color, 150))

    # Text wrapping
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
        font_small = font

    # Wrap text
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

    total_h = len(lines) * 45
    start_y = (height - total_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lx = (width - lw) // 2
        draw.text((lx + 2, start_y + i * 45 + 2), line, font=font, fill=(0, 0, 0))
        draw.text((lx, start_y + i * 45), line, font=font, fill=colors[0])

    # Watermark
    draw.text((10, height - 30), "KiraFx AI • Generated", font=font_small,
               fill=(*colors[1], 180))

    return img

# ============================================================
# WELCOME IMAGE
# ============================================================
def make_welcome_image(user_name: str) -> Image.Image:
    """Create a welcome image for new users."""
    width, height = 800, 400
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(20 + 30 * ratio)
        g = int(20 + 10 * ratio)
        b = int(50 + 50 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative circles
    for i in range(5):
        cx = random.randint(100, 700)
        cy = random.randint(50, 350)
        r_val = random.randint(20, 80)
        draw.ellipse([cx - r_val, cy - r_val, cx + r_val, cy + r_val],
                      outline=(100, 100, 255, 80), width=2)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large

    # Welcome text
    welcome_text = f"Welcome, {user_name}!"
    bbox = draw.textbbox((0, 0), welcome_text, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2 + 2, 82), welcome_text, font=font_large, fill=(0, 0, 0))
    draw.text(((width - tw) // 2, 80), welcome_text, font=font_large, fill=(180, 150, 255))

    # Bot name
    bot_text = BOT_NAME
    bbox2 = draw.textbbox((0, 0), bot_text, font=font_med)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, 150), bot_text, font=font_med, fill=(255, 200, 100))

    # Feature badges
    features = ["📷 66+ Filters", "🎬 77+ Effects", "📁 File Rename", "🤖 AI Gen", "⭐ Premium"]
    badge_x = 30
    badge_y = 230
    for feat in features:
        bbox3 = draw.textbbox((0, 0), feat, font=font_small)
        fw = bbox3[2] - bbox3[0]
        draw.rounded_rectangle([badge_x - 5, badge_y - 5, badge_x + fw + 10, badge_y + 25],
                                 radius=8, fill=(50, 30, 100))
        draw.text((badge_x, badge_y), feat, font=font_small, fill=(200, 200, 255))
        badge_x += fw + 25
        if badge_x > width - 100:
            badge_x = 30
            badge_y += 45

    # KiraFx branding
    draw.text((10, height - 30), "KiraFx Bot v7.0 Ultra Premium Edition",
               font=font_small, fill=(100, 100, 200))

    return img

# ============================================================
# KEYBOARDS
# ============================================================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Image Filters", callback_data="menu_image"),
         InlineKeyboardButton("🎬 Video Effects", callback_data="menu_video")],
        [InlineKeyboardButton("🗜️ Compress", callback_data="menu_compress"),
         InlineKeyboardButton("✏️ Rename", callback_data="menu_rename")],
        [InlineKeyboardButton("📝 Metadata", callback_data="menu_metadata"),
         InlineKeyboardButton("🤖 AI Gen", callback_data="menu_ai")],
        [InlineKeyboardButton("🎨 Logo Maker", callback_data="menu_logo"),
         InlineKeyboardButton("⭐ Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📊 My Profile", callback_data="menu_profile"),
         InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")],
    ])

def image_category_keyboard(page: int = 0):
    cats = list(IMAGE_FILTER_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"imgcat_{cat}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
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
        row.append(InlineKeyboardButton(name, callback_data=f"imgfilter_{f}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"imgpage_{category}_{page-1}"))
    if end < len(filters_list):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"imgpage_{category}_{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_image")])
    return InlineKeyboardMarkup(buttons)

def video_category_keyboard():
    cats = list(VIDEO_EFFECT_CATEGORIES.keys())
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"vidcat_{cat}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
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
        nav.append(InlineKeyboardButton("◀️", callback_data=f"vidpage_{category}_{page-1}"))
    if end < len(effects_list):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"vidpage_{category}_{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_video")])
    return InlineKeyboardMarkup(buttons)

def compress_keyboard():
    buttons = []
    row = []
    for quality in COMPRESSION_PRESETS.keys():
        if quality == "4K":
            row.append(InlineKeyboardButton(f"⭐ {quality}", callback_data=f"compress_{quality}"))
        else:
            row.append(InlineKeyboardButton(quality, callback_data=f"compress_{quality}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
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
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
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
    buttons.append([InlineKeyboardButton("🔙 Styles", callback_data="menu_logo")])
    return InlineKeyboardMarkup(buttons)

def ai_gen_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Text to Image", callback_data="ai_txt2img"),
         InlineKeyboardButton("🎬 Text to Video", callback_data="ai_txt2vid")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
    ])

def upload_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 As Document", callback_data="upload_doc"),
         InlineKeyboardButton("🎬 As Video", callback_data="upload_vid")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users", callback_data="admin_users"),
         InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 Backup DB", callback_data="admin_backup"),
         InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup")],
        [InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
         InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
         InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")],
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
            await message.reply("🔧 Bot is in maintenance mode. Please try again later.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply("❌ This command is for admins only.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def require_premium(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not is_premium(message.from_user.id):
            await message.reply(
                "⭐ **Premium Required**\n\nThis feature is for premium users only.\n"
                "Use /premium to learn more or /trial for a free 7-day trial.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⭐ Get Premium", callback_data="menu_premium")],
                    [InlineKeyboardButton("🎁 Free Trial", callback_data="trial")],
                ])
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

    if len(args) > 1:
        ref_code_or_id = args[1]
        try:
            referrer_id = int(ref_code_or_id)
            if referrer_id != user.id:
                referred_by = referrer_id
                # Reward referrer
                referrer = get_user(referrer_id)
                if referrer:
                    db = get_db()
                    db.execute("UPDATE users SET referral_count=referral_count+1, coins=coins+100 WHERE user_id=?", (referrer_id,))
                    db.commit()
                    add_premium(referrer_id, 3)
                    try:
                        await client.send_message(
                            referrer_id,
                            f"🎉 Someone joined using your referral link! You got **3 days premium + 100 coins**!"
                        )
                    except Exception:
                        pass
        except ValueError:
            pass
        register_user(user, referred_by)

    # Generate welcome image
    try:
        welcome_img = make_welcome_image(user.first_name or "Runner")
        bio = BytesIO()
        bio.name = "welcome.png"
        welcome_img.save(bio, "PNG")
        bio.seek(0)

        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=(
                f"👋 **Welcome to {BOT_NAME}!**\n\n"
                f"Your all-in-one media editor bot.\n\n"
                f"📷 **66+ Image Filters**\n"
                f"🎬 **77+ Video Effects**\n"
                f"🗜️ **Video Compression**\n"
                f"✏️ **File Rename & Metadata**\n"
                f"🤖 **AI Generation**\n"
                f"⭐ **Premium Features**\n\n"
                f"Use /help for guide or tap the menu below!"
            ),
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Welcome image error: {e}")
        await message.reply(
            f"👋 **Welcome to {BOT_NAME}!**\n\nTap the menu below to get started!",
            reply_markup=main_menu_keyboard()
        )

@app.on_message(filters.command("help"))
@require_registered
async def cmd_help(client, message: Message):
    text = (
        "📖 **KiraFx Bot Help Guide**\n\n"
        "**Image Editing:**\n"
        "Send any photo → Choose filter category → Select filter\n\n"
        "**Video Editing:**\n"
        "Send any video → Choose effect category → Select effect\n\n"
        "**Rename Files:**\n"
        "Use /rename → Send file → Type new name\n\n"
        "**Metadata Edit:**\n"
        "Use /metadata → Send media file → Edit fields\n\n"
        "**Compress Video:**\n"
        "Use /compress → Send video → Choose quality\n\n"
        "**AI Features:**\n"
        "• /txt2img [prompt] - Generate image from text\n"
        "• /txt2vid [prompt] - Generate video from text\n"
        "• /aiedit [prompt] - AI-guided filter selection\n\n"
        "**Other Commands:**\n"
        "• /logo - Logo maker\n"
        "• /premium - Premium info\n"
        "• /trial - Free 7-day trial\n"
        "• /status - Your status\n"
        "• /profile - Your profile\n"
        "• /refer - Get referral link\n"
        "• /ping - Bot ping\n"
        "• /alive - Bot alive check\n"
        "• /queue - Queue status\n"
    )
    await message.reply(text, reply_markup=main_menu_keyboard())

@app.on_message(filters.command("premium"))
@require_registered
async def cmd_premium(client, message: Message):
    user_id = message.from_user.id
    if is_premium(user_id):
        row = get_user(user_id)
        until = row["premium_until"] or "Lifetime"
        await message.reply(
            f"⭐ **You are a Premium User!**\n\n"
            f"Premium until: `{until}`\n\n"
            f"**Premium Benefits:**\n"
            f"✅ Unlimited edits per day\n"
            f"✅ No watermarks\n"
            f"✅ No ads\n"
            f"✅ Priority queue\n"
            f"✅ 4K compression\n"
            f"✅ Longer timeout (600s)\n"
        )
    else:
        await message.reply(
            "⭐ **KiraFx Premium Plans**\n\n"
            "• 7-day free trial (/trial)\n"
            "• 1 Month: Contact admin\n"
            "• 3 Months: Contact admin\n"
            "• Lifetime: Contact admin\n\n"
            "**Premium Benefits:**\n"
            "✅ Unlimited edits per day\n"
            "✅ No watermarks\n"
            "✅ No ads\n"
            "✅ Priority queue\n"
            "✅ 4K compression\n"
            "✅ Longer timeout (600s)\n\n"
            "Contact the bot owner to purchase premium.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Free 7-Day Trial", callback_data="trial")],
            ])
        )

@app.on_message(filters.command("trial"))
@require_registered
async def cmd_trial(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if row["trial_used"]:
        await message.reply("❌ You have already used your free trial.")
        return
    if is_premium(user_id):
        await message.reply("✅ You already have premium access!")
        return
    add_premium(user_id, 7)
    get_db().execute("UPDATE users SET trial_used=1 WHERE user_id=?", (user_id,))
    get_db().commit()
    await message.reply(
        "🎉 **7-Day Free Trial Activated!**\n\n"
        "You now have premium access for 7 days. Enjoy!\n\n"
        "✅ Unlimited edits\n✅ No watermarks\n✅ No ads\n✅ Priority queue"
    )

@app.on_message(filters.command("status"))
@require_registered
async def cmd_status(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found.")
        return
    prem = "⭐ Premium" if is_premium(user_id) else "Free"
    admin_str = " | 🔑 Admin" if is_admin(user_id) else ""
    today_edits = row["edits_today"]
    limit = "∞" if is_premium(user_id) else get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
    await message.reply(
        f"📊 **Your Status**\n\n"
        f"**Tier:** {prem}{admin_str}\n"
        f"**Edits Today:** {today_edits} / {limit}\n"
        f"**Total Edits:** {row['total_edits']}\n"
        f"**Total Renames:** {row['total_renames']}\n"
        f"**Coins:** {row['coins']}\n"
        f"**Referrals:** {row['referral_count']}\n"
    )

@app.on_message(filters.command("profile"))
@require_registered
async def cmd_profile(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        await message.reply("❌ User not found.")
        return
    prem = "⭐ Premium" if is_premium(user_id) else "🆓 Free"
    await message.reply(
        f"👤 **Your Profile**\n\n"
        f"**Name:** {row['first_name']} {row['last_name'] or ''}\n"
        f"**Username:** @{row['username'] or 'N/A'}\n"
        f"**User ID:** `{user_id}`\n"
        f"**Status:** {prem}\n"
        f"**Total Edits:** {row['total_edits']}\n"
        f"**Total Renames:** {row['total_renames']}\n"
        f"**Coins:** 🪙 {row['coins']}\n"
        f"**Referrals:** {row['referral_count']}\n"
        f"**Referral Code:** `{row['referral_code']}`\n"
        f"**Joined:** {row['joined_at'][:10]}\n"
    )

@app.on_message(filters.command("refer"))
@require_registered
async def cmd_refer(client, message: Message):
    user_id = message.from_user.id
    row = get_user(user_id)
    bot_info = await client.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    await message.reply(
        f"🔗 **Your Referral Link**\n\n"
        f"`{link}`\n\n"
        f"**Rewards per referral:**\n"
        f"• 3 days premium\n"
        f"• 100 coins\n\n"
        f"**Your referrals:** {row['referral_count']}"
    )

@app.on_message(filters.command("ping"))
async def cmd_ping(client, message: Message):
    start = time.time()
    msg = await message.reply("🏓 Pong!")
    elapsed = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong! `{elapsed:.1f}ms`")

@app.on_message(filters.command("alive"))
async def cmd_alive(client, message: Message):
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    await message.reply(
        f"✅ **{BOT_NAME}** is alive!\n\n"
        f"⏱️ Uptime: `{h:02d}:{m:02d}:{s:02d}`\n"
        f"🔧 FFmpeg: `{'✅' if check_ffmpeg() else '❌'}`\n"
        f"👥 Users: `{get_user_count()}`\n"
    )

@app.on_message(filters.command("info"))
async def cmd_info(client, message: Message):
    await message.reply(
        f"ℹ️ **{BOT_NAME}**\n\n"
        f"**Version:** v{BOT_VERSION}\n"
        f"**Library:** Pyrogram\n"
        f"**Image Filters:** {len(IMAGE_FILTERS)}+\n"
        f"**Video Effects:** {len(VIDEO_EFFECTS)}+\n"
        f"**Compression Presets:** {len(COMPRESSION_PRESETS)}\n"
        f"**FFmpeg:** {'Installed ✅' if check_ffmpeg() else 'Not found ❌'}\n"
        f"**Total Users:** {get_user_count()}\n"
        f"**Total Edits:** {get_total_edits()}\n"
    )

@app.on_message(filters.command("queue"))
@require_registered
async def cmd_queue(client, message: Message):
    pos = job_queue.get_position(message.from_user.id)
    if pos > 0:
        await message.reply(f"📋 Your position in queue: **#{pos}**")
    else:
        await message.reply("✅ No active job in queue. You can start editing!")

@app.on_message(filters.command("rename"))
@require_registered
async def cmd_rename(client, message: Message):
    user_id = message.from_user.id
    set_session(user_id, "mode", "rename")
    await message.reply(
        "✏️ **Rename File**\n\n"
        "Send the file you want to rename.",
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
        "Send the video you want to compress.",
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
            "🎨 **Logo Maker**\n\nSend the text for your logo.",
            reply_markup=cancel_keyboard()
        )
        return
    set_session(user_id, "logo_text", args[1])
    await message.reply(
        f"🎨 Choose a style for: **{args[1]}**",
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
            "🖼️ **Text to Image**\n\nSend your image prompt.",
            reply_markup=cancel_keyboard()
        )
        return
    prompt = args[1]
    await process_txt2img(client, message, user_id, prompt)

@app.on_message(filters.command("txt2vid"))
@require_registered
async def cmd_txt2vid(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        set_session(user_id, "mode", "txt2vid")
        await message.reply(
            "🎬 **Text to Video**\n\nSend your video prompt.",
            reply_markup=cancel_keyboard()
        )
        return
    await message.reply("🎬 Generating video animation...")
    await process_txt2vid(client, message, user_id, args[1])

@app.on_message(filters.command("aiedit"))
@require_registered
async def cmd_aiedit(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply(
            "🤖 **AI Prompt Edit**\n\n"
            "Usage: /aiedit [prompt]\n"
            "Example: /aiedit make this look vintage and warm"
        )
        return
    prompt = args[1].lower()
    filters_matched = []
    keywords = {
        "blur": "blur", "sharp": "sharpen", "gray": "grayscale", "grey": "grayscale",
        "sepia": "sepia", "vintage": "vintage", "warm": "golden_hour", "cold": "cold_tone",
        "cool": "cold_tone", "sketch": "sketch", "cartoon": "cartoon", "neon": "neon",
        "bright": "brightness", "dark": "night", "contrast": "contrast", "color": "saturation",
        "invert": "invert", "flip": "flip_h", "rotate": "rotate_90", "glow": "glow",
        "watercolor": "watercolor", "oil": "oil_paint", "pixel": "pixelate", "glitch": "glitch",
        "sunset": "sunset", "winter": "winter", "autumn": "autumn", "spring": "spring",
        "emboss": "emboss", "edge": "edge_enhance", "border": "border",
    }
    for kw, f in keywords.items():
        if kw in prompt:
            filters_matched.append(f)

    if not filters_matched:
        await message.reply(
            "❓ Couldn't match any filters to your prompt. Try describing specific effects like: "
            "blur, sharp, vintage, warm, cool, cartoon, sketch, neon, etc.\n\n"
            "Or send a photo directly and choose from the filter menu."
        )
        return

    set_session(user_id, "mode", "aiedit")
    set_session(user_id, "ai_filters", filters_matched)
    suggested = ", ".join(IMAGE_FILTERS.get(f, f) for f in filters_matched[:5])
    await message.reply(
        f"🤖 **AI Analysis:** I'll apply these filters: **{suggested}**\n\n"
        f"Now send the image you want to edit.",
        reply_markup=cancel_keyboard()
    )

@app.on_message(filters.command("livestream"))
async def cmd_livestream(client, message: Message):
    await message.reply(
        "📡 **Group Livestream Mode**\n\n"
        "KiraFx Bot supports media processing in groups!\n"
        "• Send images/videos in the group to process them\n"
        "• Use commands directly in the group\n"
        "• Admins can enable/disable private editing\n\n"
        "**Admin Commands:**\n"
        "• /setgroup - Enable group-only mode\n"
        "• /admin - Open admin panel"
    )

# ============================================================
# ADMIN COMMANDS
# ============================================================

@app.on_message(filters.command("admin"))
@require_registered
@require_admin
async def cmd_admin(client, message: Message):
    await message.reply(
        f"🔑 **Admin Panel**\n\n"
        f"Total Users: `{get_user_count()}`\n"
        f"Premium Users: `{get_premium_count()}`\n"
        f"Total Edits: `{get_total_edits()}`\n",
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
    reason = " ".join(args[2:-1]) if len(args) > 3 else " ".join(args[2:]) if len(args) > 2 else "No reason"
    ban_until = None
    if len(args) > 3 and args[-1].isdigit():
        ban_until = (datetime.now() + timedelta(days=int(args[-1]))).isoformat()
    db = get_db()
    db.execute(
        "UPDATE users SET is_banned=1, ban_reason=?, ban_until=? WHERE user_id=?",
        (reason, ban_until, target_id)
    )
    db.commit()
    await message.reply(f"✅ User `{target_id}` banned. Reason: {reason}")
    try:
        await client.send_message(target_id, f"🚫 You have been banned from KiraFx Bot.\nReason: {reason}")
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
        await client.send_message(target_id, "✅ You have been unbanned from KiraFx Bot!")
    except Exception:
        pass

@app.on_message(filters.command("addprem"))
@require_registered
@require_admin
async def cmd_addprem(client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /addprem [user_id] [days]")
        return
    try:
        target_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    add_premium(target_id, days)
    await message.reply(f"✅ Added {days} days premium to user `{target_id}`.")
    try:
        await client.send_message(target_id, f"⭐ You have been granted {days} days of premium by an admin!")
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
    db.execute("UPDATE users SET is_premium=0, premium_until=NULL WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ Premium removed from user `{target_id}`.")

@app.on_message(filters.command("addadmin"))
@require_registered
async def cmd_addadmin(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Only the owner can add admins.")
        return
    args = message.text.split(None, 2)
    if len(args) < 2:
        await message.reply("Usage: /addadmin [user_id] [title (optional)]")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return
    title = args[2] if len(args) > 2 else "Admin"
    db = get_db()
    db.execute("UPDATE users SET is_admin=1, admin_title=? WHERE user_id=?", (title, target_id))
    db.execute("INSERT OR REPLACE INTO admins (user_id, title, added_by) VALUES (?, ?, ?)",
               (target_id, title, message.from_user.id))
    db.commit()
    await message.reply(f"✅ User `{target_id}` added as admin with title: {title}")

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
    db = get_db()
    db.execute("UPDATE users SET is_admin=0, admin_title=NULL WHERE user_id=?", (target_id,))
    db.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
    db.commit()
    await message.reply(f"✅ Admin `{target_id}` removed.")

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
    prem = "⭐ Yes" if row["is_premium"] else "No"
    admin_str = "✅ Yes" if row["is_admin"] else "No"
    banned_str = "🚫 Yes" if row["is_banned"] else "No"
    await message.reply(
        f"👤 **User Info: `{target_id}`**\n\n"
        f"Name: {row['first_name']} {row['last_name'] or ''}\n"
        f"Username: @{row['username'] or 'N/A'}\n"
        f"Premium: {prem}\n"
        f"Admin: {admin_str}\n"
        f"Banned: {banned_str}\n"
        f"Edits: {row['total_edits']}\n"
        f"Coins: {row['coins']}\n"
        f"Joined: {row['joined_at'][:10]}\n"
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
        target_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.reply("❌ Invalid arguments.")
        return
    db = get_db()
    db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, target_id))
    db.commit()
    await message.reply(f"✅ Added {amount} coins to user `{target_id}`.")

@app.on_message(filters.command("broadcast"))
@require_registered
@require_admin
async def cmd_broadcast(client, message: Message):
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("Usage: /broadcast [message]")
        return
    text = args[1]
    users = get_all_users()
    sent = 0
    failed = 0
    status_msg = await message.reply(f"📢 Broadcasting to {len(users)} users...")
    for user_row in users:
        try:
            await client.send_message(user_row["user_id"], text)
            sent += 1
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
    get_db().execute(
        "INSERT INTO broadcast_logs (admin_id, message_text, sent_count) VALUES (?, ?, ?)",
        (message.from_user.id, text[:500], sent)
    )
    get_db().commit()
    await status_msg.edit_text(f"✅ Broadcast complete!\nSent: {sent}\nFailed: {failed}")

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
    await message.reply(f"✅ Watermark text set to: {args[1]}")

@app.on_message(filters.command("setfree"))
@require_registered
@require_admin
async def cmd_setfree(client, message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Usage: /setfree [number]")
        return
    set_setting("free_edits_per_day", args[1])
    await message.reply(f"✅ Free edits per day set to: {args[1]}")

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
        await message.reply("✅ Ads enabled.")
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
    status = "🔧 ON" if new_val == "1" else "✅ OFF"
    await message.reply(f"Maintenance mode: {status}")

@app.on_message(filters.command("backup"))
@require_registered
@require_admin
async def cmd_backup(client, message: Message):
    backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    await client.send_document(
        message.chat.id,
        document=backup_path,
        caption=f"💾 Database backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    os.remove(backup_path)

@app.on_message(filters.command("cleanup"))
@require_registered
@require_admin
async def cmd_cleanup(client, message: Message):
    cleanup_temp_files(0)
    cleanup_sessions()
    await message.reply("✅ Temporary files and sessions cleaned up.")

@app.on_message(filters.command("logs"))
@require_registered
@require_admin
async def cmd_logs(client, message: Message):
    if os.path.exists(LOG_FILE):
        await client.send_document(
            message.chat.id,
            document=LOG_FILE,
            caption="📋 Bot Logs"
        )
    else:
        await message.reply("❌ Log file not found.")

@app.on_message(filters.command("export"))
@require_registered
@require_admin
async def cmd_export(client, message: Message):
    settings = dict(get_db().execute("SELECT key, value FROM settings").fetchall())
    config = {
        "settings": settings,
        "admin_count": get_db().execute("SELECT COUNT(*) FROM admins").fetchone()[0],
        "user_count": get_user_count(),
        "premium_count": get_premium_count(),
        "total_edits": get_total_edits(),
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
            "Usage: /addcmd [command] [response]\n"
            "Or: Reply to media with /addcmd [command]\n"
            "For code: /addcmd [command] --code [code block]"
        )
        return

    cmd_name = args[1].lstrip("/").lower() if len(args) > 1 else None
    if not cmd_name:
        await message.reply("❌ Please provide a command name.")
        return

    db = get_db()
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.photo:
            media_id = reply.photo.file_id
            response_type = "photo"
        elif reply.video:
            media_id = reply.video.file_id
            response_type = "video"
        elif reply.audio:
            media_id = reply.audio.file_id
            response_type = "audio"
        elif reply.document:
            media_id = reply.document.file_id
            response_type = "document"
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
    await message.reply(f"✅ Custom command `/{cmd_name}` added.")

@app.on_message(filters.command("delcmd"))
@require_registered
@require_admin
async def cmd_delcmd(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /delcmd [command]")
        return
    cmd_name = args[1].lstrip("/").lower()
    db = get_db()
    db.execute("DELETE FROM custom_commands WHERE command=?", (cmd_name,))
    db.commit()
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
    cmds = get_db().execute("SELECT command, response_type, is_enabled FROM custom_commands").fetchall()
    if not cmds:
        await message.reply("No custom commands found.")
        return
    text = "📋 **Custom Commands:**\n\n"
    for row in cmds:
        status = "✅" if row["is_enabled"] else "❌"
        text += f"{status} `/{row['command']}` [{row['response_type']}]\n"
    await message.reply(text)

@app.on_message(filters.command("addautoreply"))
@require_registered
@require_admin
async def cmd_addautoreply(client, message: Message):
    args = message.text.split(None, 3)
    if len(args) < 4:
        await message.reply(
            "Usage: /addautoreply [exact|contains|startswith] [trigger] [response]"
        )
        return
    match_type = args[1].lower()
    if match_type not in ["exact", "contains", "startswith"]:
        await message.reply("❌ Match type must be: exact, contains, or startswith")
        return
    trigger = args[2]
    response = args[3]
    db = get_db()
    db.execute(
        "INSERT INTO auto_replies (trigger, match_type, response, response_type, added_by) VALUES (?, ?, ?, 'text', ?)",
        (trigger, match_type, response, message.from_user.id)
    )
    db.commit()
    await message.reply(f"✅ Auto-reply added for trigger: `{trigger}`")

# ============================================================
# MEDIA HANDLERS
# ============================================================

async def handle_media_for_edit(client, message: Message, file_path: str, media_type: str):
    """Generic handler after downloading a media file."""
    user_id = message.from_user.id
    mode = get_session(user_id, "mode")

    if media_type in ("photo",):
        if mode in ("aiedit",):
            ai_filters = get_session(user_id, "ai_filters", [])
            if ai_filters:
                await apply_image_filters_sequence(client, message, file_path, ai_filters)
                clear_session(user_id)
                return
        # Show image filter menu
        set_session(user_id, "image_path", file_path)
        clear_session(user_id, "mode")
        await message.reply(
            "📷 **Choose Filter Category:**",
            reply_markup=image_category_keyboard()
        )

    elif media_type in ("video",):
        if mode == "compress":
            set_session(user_id, "video_path", file_path)
            clear_session(user_id, "mode")
            await message.reply(
                "🗜️ **Choose Compression Quality:**\n"
                "⭐ = Premium only",
                reply_markup=compress_keyboard()
            )
        else:
            set_session(user_id, "video_path", file_path)
            clear_session(user_id, "mode")
            await message.reply(
                "🎬 **Choose Effect Category:**",
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
            set_session(user_id, "media_type_meta", media_type)
            clear_session(user_id, "mode")
            await show_metadata_menu(client, message)
        else:
            # Default: rename
            set_session(user_id, "rename_path", file_path)
            set_session(user_id, "rename_original", getattr(message.document or message.audio, "file_name", "file"))
            await message.reply(
                "✏️ Send new filename or use /rename for the full rename menu:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Rename", callback_data="do_rename"),
                     InlineKeyboardButton("📝 Metadata", callback_data="do_metadata")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
                ])
            )

async def show_metadata_menu(client, message: Message):
    await message.reply(
        "📝 **Metadata Editor**\n\n"
        "Send the metadata in this format:\n"
        "`title=My Title | artist=Artist | album=Album`\n\n"
        "**Available fields:** title, artist, album, year, comment, description, genre, language, encoder, track, disc, composer, publisher, copyright",
        reply_markup=cancel_keyboard()
    )

async def apply_image_filters_sequence(client, message: Message, file_path: str, filters_list: List[str]):
    """Apply multiple filters in sequence."""
    status_msg = await message.reply(f"⏳ Applying {len(filters_list)} filter(s)...")
    user_id = message.from_user.id
    try:
        img = Image.open(file_path).convert("RGB")
        for f in filters_list:
            img = apply_image_filter(img, f)
        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = add_watermark(img, wm_text)
        out_path = temp_path(".jpg")
        img.save(out_path, "JPEG", quality=90)
        filter_names = ", ".join(IMAGE_FILTERS.get(f, f) for f in filters_list)
        await client.send_photo(
            message.chat.id,
            photo=out_path,
            caption=f"✅ Applied: {filter_names}",
        )
        increment_edits(user_id)
        log_edit(user_id, "image", filter_names)
        await status_msg.delete()
        os.remove(out_path)
    except Exception as e:
        logger.error(f"Filter apply error: {e}")
        await status_msg.edit_text(f"❌ Error applying filter: {str(e)[:200]}")

@app.on_message(filters.photo & ~filters.edited)
@require_registered
async def handle_photo(client, message: Message):
    user_id = message.from_user.id
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ Daily limit reached ({limit} edits/day).\n"
            f"Upgrade to premium for unlimited edits! /premium"
        )
        return
    status_msg = await message.reply("⬇️ Downloading photo...")
    try:
        file_path = await message.download(file_name=temp_path(".jpg"))
        await status_msg.delete()
        await handle_media_for_edit(client, message, file_path, "photo")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

@app.on_message(filters.video & ~filters.edited)
@require_registered
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    if not can_edit(user_id):
        limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
        await message.reply(
            f"❌ Daily limit reached ({limit} edits/day).\n"
            f"Upgrade to premium for unlimited edits! /premium"
        )
        return
    status_msg = await message.reply("⬇️ Downloading video... This may take a moment.")
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
        await message.reply("❌ Invalid video file. Please send a valid video.")
        return
    await handle_media_for_edit(client, message, file_path, "video")

@app.on_message(filters.document & ~filters.edited)
@require_registered
async def handle_document(client, message: Message):
    doc = message.document
    ext = Path(doc.file_name or "file").suffix.lower() if doc.file_name else ""
    video_exts = [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".3gp"]
    status_msg = await message.reply("⬇️ Downloading file...")
    try:
        file_path = await message.download(file_name=temp_path(ext or ".bin"))
        await status_msg.delete()
        if ext in video_exts:
            await handle_media_for_edit(client, message, file_path, "video")
        else:
            await handle_media_for_edit(client, message, file_path, "document")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {str(e)[:200]}")

@app.on_message(filters.audio & ~filters.edited)
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
# TEXT MESSAGE HANDLER (for multi-step flows)
# ============================================================
@app.on_message(filters.text & ~filters.command(["start", "help", "admin", "ban", "unban",
    "addprem", "rmprem", "addadmin", "rmadmin", "userinfo", "addcoins", "broadcast",
    "setwelcome", "setwatermark", "setfree", "setads", "maintenance", "backup", "cleanup",
    "logs", "export", "addcmd", "delcmd", "togglecmd", "listcmds", "addautoreply",
    "premium", "trial", "status", "profile", "refer", "rename", "metadata", "compress",
    "logo", "txt2img", "txt2vid", "aiedit", "ping", "alive", "info", "queue", "livestream"]))
@require_registered
async def handle_text(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Check auto-replies
    auto_replies = get_db().execute(
        "SELECT * FROM auto_replies WHERE is_enabled=1"
    ).fetchall()
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

    # Check custom commands
    if text.startswith("/"):
        cmd = text.split()[0].lstrip("/").lower()
        row = get_db().execute(
            "SELECT * FROM custom_commands WHERE command=? AND is_enabled=1", (cmd,)
        ).fetchone()
        if row:
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

    # Handle mode-based flows
    mode = get_session(user_id, "mode")

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
                    caption=f"✅ Renamed to: `{new_name}`",
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
            # Parse metadata from text
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
                # Build ffmpeg metadata command
                cmd = ["ffmpeg", "-y", "-i", meta_path]
                for k, v in meta.items():
                    cmd += ["-metadata", f"{k}={v}"]
                cmd += ["-c", "copy", out_path]
                ok, err = run_ffmpeg(cmd)
                if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    await client.send_document(
                        message.chat.id,
                        document=out_path,
                        caption=f"✅ Metadata updated!\n" + "\n".join(f"• {k}: {v}" for k, v in meta.items())
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
            f"🎨 Choose a style for: **{text}**",
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

# ============================================================
# AI GENERATION PROCESSING
# ============================================================
async def process_txt2img(client, message: Message, user_id: int, prompt: str):
    status_msg = await message.reply(f"🎨 Generating image for: *{prompt[:50]}*...")
    try:
        # Allow style in prompt: "gradient: my prompt"
        style = "gradient"
        for s in AI_TEXT_IMAGE_STYLES.keys():
            if prompt.lower().startswith(s + ":"):
                style = s
                prompt = prompt[len(s)+1:].strip()
                break
        img = text_to_image(prompt, style)
        wm_text = get_setting("watermark_text", "KiraFx")
        if wm_text and not is_premium(user_id):
            img = add_watermark(img, wm_text)
        bio = BytesIO()
        bio.name = "generated.png"
        img.save(bio, "PNG")
        bio.seek(0)
        await client.send_photo(
            message.chat.id,
            photo=bio,
            caption=f"🖼️ Generated: *{prompt[:100]}*\nStyle: {style}"
        )
        await status_msg.delete()
        increment_edits(user_id)
    except Exception as e:
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

async def process_txt2vid(client, message: Message, user_id: int, prompt: str):
    status_msg = await message.reply(f"🎬 Generating video for: *{prompt[:50]}*...")
    try:
        # Generate a sequence of frames and combine into video
        frames = []
        durations = [0, 5, 10]  # Different color phases
        styles = list(AI_TEXT_IMAGE_STYLES.keys())

        for i in range(30):  # 30 frames = ~3 seconds at 10fps
            ratio = i / 30
            style = styles[int(ratio * len(styles)) % len(styles)]
            frame = text_to_image(f"{prompt} (frame {i})", style)
            frame_path = temp_path(".jpg")
            frame.save(frame_path, "JPEG", quality=85)
            frames.append(frame_path)

        # Create video from frames
        list_file = temp_path(".txt")
        out_path = temp_path(".mp4")
        with open(list_file, "w") as lf:
            for fp in frames:
                lf.write(f"file '{fp}'\n")
                lf.write("duration 0.1\n")

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", list_file, "-vf", "fps=10", "-pix_fmt", "yuv420p", out_path]
        ok, err = run_ffmpeg(cmd, timeout=120)

        if ok and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            await client.send_video(
                message.chat.id,
                video=out_path,
                caption=f"🎬 Generated: *{prompt[:100]}*"
            )
            await status_msg.delete()
            increment_edits(user_id)
            os.remove(out_path)
        else:
            # Fallback: just send one frame
            img = text_to_image(prompt, "gradient")
            bio = BytesIO()
            bio.name = "preview.png"
            img.save(bio, "PNG")
            bio.seek(0)
            await client.send_photo(
                message.chat.id,
                photo=bio,
                caption=f"🖼️ Video generation preview: *{prompt[:100]}*\n(Full video gen requires FFmpeg)"
            )
            await status_msg.delete()

        # Cleanup frames
        for fp in frames:
            try:
                os.remove(fp)
            except Exception:
                pass
        if os.path.exists(list_file):
            os.remove(list_file)
    except Exception as e:
        logger.error(f"txt2vid error: {e}")
        await status_msg.edit_text(f"❌ Generation error: {str(e)[:200]}")

# ============================================================
# CALLBACK QUERY HANDLERS
# ============================================================
@app.on_callback_query()
async def handle_callback(client, query: CallbackQuery):
    user = query.from_user
    data = query.data
    user_id = user.id

    register_user(user)
    if is_banned(user_id):
        await query.answer("🚫 You are banned.", show_alert=True)
        return

    # Cancel
    if data == "cancel":
        clear_session(user_id)
        await query.message.edit_text(
            "❌ Operation cancelled.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Main menu navigation
    if data == "menu_main":
        await query.message.edit_text(
            f"🎬 **{BOT_NAME}**\n\nChoose what you want to do:",
            reply_markup=main_menu_keyboard()
        )
    elif data == "menu_image":
        await query.message.edit_text(
            "📷 **Image Filters**\n\nChoose a category:",
            reply_markup=image_category_keyboard()
        )
    elif data == "menu_video":
        await query.message.edit_text(
            "🎬 **Video Effects**\n\nChoose a category:",
            reply_markup=video_category_keyboard()
        )
    elif data == "menu_compress":
        await query.message.edit_text(
            "🗜️ **Video Compression**\n\nFirst send a video, then choose quality.",
            reply_markup=compress_keyboard()
        )
    elif data == "menu_rename":
        set_session(user_id, "mode", "rename")
        await query.message.edit_text(
            "✏️ **Rename File**\n\nSend the file you want to rename.",
            reply_markup=cancel_keyboard()
        )
    elif data == "menu_metadata":
        set_session(user_id, "mode", "metadata")
        await query.message.edit_text(
            "📝 **Metadata Editor**\n\nSend the media file to edit metadata.",
            reply_markup=cancel_keyboard()
        )
    elif data == "menu_ai":
        await query.message.edit_text(
            "🤖 **AI Generation**\n\nChoose what to generate:",
            reply_markup=ai_gen_keyboard()
        )
    elif data == "menu_logo":
        set_session(user_id, "mode", "logo")
        await query.message.edit_text(
            "🎨 **Logo Maker**\n\nSend the text for your logo:",
            reply_markup=cancel_keyboard()
        )
    elif data == "menu_premium":
        prem = "⭐ Premium" if is_premium(user_id) else "🆓 Free"
        await query.message.edit_text(
            f"⭐ **Premium Info**\n\nYour status: {prem}\n\n"
            "Use /premium for details or /trial for a free 7-day trial.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Free Trial", callback_data="trial")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
            ])
        )
    elif data == "menu_profile":
        row = get_user(user_id)
        if row:
            prem = "⭐ Premium" if is_premium(user_id) else "🆓 Free"
            await query.message.edit_text(
                f"👤 **Profile**\n\nName: {row['first_name']}\nStatus: {prem}\n"
                f"Total Edits: {row['total_edits']}\nCoins: 🪙 {row['coins']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]])
            )
    elif data == "menu_help":
        await query.message.edit_text(
            "📖 Send /help for the full guide.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]])
        )

    # Image category
    elif data.startswith("imgcat_"):
        cat = data[7:]
        await query.message.edit_text(
            f"📷 **{cat}**\n\nChoose a filter:",
            reply_markup=image_filter_keyboard(cat)
        )

    elif data.startswith("imgpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await query.message.edit_text(
            f"📷 **{cat}**\n\nChoose a filter:",
            reply_markup=image_filter_keyboard(cat, page)
        )

    elif data.startswith("imgfilter_"):
        filter_name = data[10:]
        image_path = get_session(user_id, "image_path")
        if not image_path or not os.path.exists(image_path):
            await query.answer("❌ No image found. Please send an image first.", show_alert=True)
            return
        if not can_edit(user_id):
            limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
            await query.answer(f"❌ Daily limit reached ({limit}/day). Upgrade to premium!", show_alert=True)
            return
        await query.message.edit_text(f"⏳ Applying {IMAGE_FILTERS.get(filter_name, filter_name)}...")
        try:
            loop = asyncio.get_event_loop()
            result_img = await loop.run_in_executor(
                executor,
                lambda: apply_image_filter(Image.open(image_path).convert("RGB"), filter_name)
            )
            wm_text = get_setting("watermark_text", "KiraFx")
            if wm_text and not is_premium(user_id):
                result_img = await loop.run_in_executor(
                    executor,
                    lambda: add_watermark(result_img, wm_text)
                )
            out_path = temp_path(".jpg")
            result_img.save(out_path, "JPEG", quality=90)
            await client.send_photo(
                query.message.chat.id,
                photo=out_path,
                caption=f"✅ Filter: **{IMAGE_FILTERS.get(filter_name, filter_name)}**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Apply Another", callback_data="menu_image")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
                ])
            )
            increment_edits(user_id)
            log_edit(user_id, "image", filter_name)
            await query.message.delete()
            os.remove(out_path)
        except Exception as e:
            logger.error(f"Image filter error: {e}\n{traceback.format_exc()}")
            await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

    # Video category
    elif data.startswith("vidcat_"):
        cat = data[7:]
        await query.message.edit_text(
            f"🎬 **{cat}**\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat)
        )

    elif data.startswith("vidpage_"):
        parts = data[8:].rsplit("_", 1)
        cat = parts[0]
        page = int(parts[1])
        await query.message.edit_text(
            f"🎬 **{cat}**\n\nChoose an effect:",
            reply_markup=video_effect_keyboard(cat, page)
        )

    elif data.startswith("videffect_"):
        effect = data[10:]
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video found. Please send a video first.", show_alert=True)
            return
        if not can_edit(user_id):
            limit = get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY))
            await query.answer(f"❌ Daily limit reached ({limit}/day). Upgrade to premium!", show_alert=True)
            return
        timeout = 600 if is_premium(user_id) else 300
        await query.message.edit_text(f"⏳ Applying {VIDEO_EFFECTS.get(effect, effect)}...")
        try:
            ext = ".mp3" if effect == "extract_audio" else ".gif" if effect == "extract_gif" else ".mp4"
            out_path = temp_path(ext)
            loop = asyncio.get_event_loop()
            ok, err = await loop.run_in_executor(
                executor,
                lambda: apply_video_effect(video_path, effect, out_path)
            )
            if not ok or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                await query.message.edit_text(
                    f"❌ Effect failed: {err[:200] if err else 'Output file is empty.'}\n\n"
                    "Please try another effect or check FFmpeg installation."
                )
                return
            caption = f"✅ Effect: **{VIDEO_EFFECTS.get(effect, effect)}**"
            if ext == ".mp3":
                await client.send_audio(query.message.chat.id, audio=out_path, caption=caption)
            elif ext == ".gif":
                await client.send_animation(query.message.chat.id, animation=out_path, caption=caption)
            else:
                if os.path.getsize(out_path) < 50 * 1024 * 1024:
                    await client.send_video(query.message.chat.id, video=out_path, caption=caption)
                else:
                    await client.send_document(query.message.chat.id, document=out_path, caption=caption)
            increment_edits(user_id)
            log_edit(user_id, "video", effect)
            await query.message.delete()
            os.remove(out_path)
        except Exception as e:
            logger.error(f"Video effect error: {e}\n{traceback.format_exc()}")
            await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

    # Compression
    elif data.startswith("compress_"):
        quality = data[9:]
        if quality == "4K" and not is_premium(user_id):
            await query.answer("⭐ 4K compression is for premium users only!", show_alert=True)
            return
        video_path = get_session(user_id, "video_path")
        if not video_path or not os.path.exists(video_path):
            await query.answer("❌ No video found. Please send a video first.", show_alert=True)
            return
        timeout = 600 if is_premium(user_id) else 300
        await query.message.edit_text(f"⏳ Compressing to **{quality}**... This may take a while.")
        try:
            out_path = temp_path(".mp4")
            loop = asyncio.get_event_loop()
            ok, err = await loop.run_in_executor(
                executor,
                lambda: compress_video(video_path, out_path, quality, timeout)
            )
            if not ok or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                await query.message.edit_text(
                    f"❌ Compression failed: {err[:200] if err else 'Empty output file.'}\n\n"
                    "This may happen with incompatible codecs. Try a different quality."
                )
                return
            orig_size = os.path.getsize(video_path) / (1024 * 1024)
            new_size = os.path.getsize(out_path) / (1024 * 1024)
            ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
            caption = (
                f"✅ Compressed to **{quality}**\n\n"
                f"Original: `{orig_size:.1f} MB`\n"
                f"Compressed: `{new_size:.1f} MB`\n"
                f"Saved: `{ratio:.1f}%`"
            )
            if new_size < 50:
                await client.send_video(query.message.chat.id, video=out_path, caption=caption)
            else:
                await client.send_document(query.message.chat.id, document=out_path, caption=caption)
            increment_edits(user_id)
            log_edit(user_id, "compress", quality)
            await query.message.delete()
            os.remove(out_path)
        except Exception as e:
            logger.error(f"Compress error: {e}\n{traceback.format_exc()}")
            await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

    # Logo
    elif data.startswith("logo_style_"):
        style = data[11:]
        logo_text = get_session(user_id, "logo_text")
        if not logo_text:
            await query.answer("❌ No logo text found. Use /logo first.", show_alert=True)
            return
        set_session(user_id, "logo_style", style)
        await query.message.edit_text(
            f"🎨 Choose background for **{logo_text}** ({style} style):",
            reply_markup=logo_bg_keyboard(style)
        )

    elif data.startswith("logo_bg_"):
        parts = data[8:].split("_", 1)
        style = parts[0]
        bg = parts[1] if len(parts) > 1 else "dark"
        logo_text = get_session(user_id, "logo_text")
        if not logo_text:
            await query.answer("❌ No logo text found.", show_alert=True)
            return
        await query.message.edit_text(f"⏳ Generating logo...")
        try:
            loop = asyncio.get_event_loop()
            img = await loop.run_in_executor(
                executor,
                lambda: make_logo(logo_text, style, bg)
            )
            bio = BytesIO()
            bio.name = "logo.png"
            img.save(bio, "PNG")
            bio.seek(0)
            await client.send_photo(
                query.message.chat.id,
                photo=bio,
                caption=f"🎨 **Logo Generated!**\nText: {logo_text}\nStyle: {style}\nBg: {bg}"
            )
            await query.message.delete()
            clear_session(user_id)
        except Exception as e:
            await query.message.edit_text(f"❌ Logo error: {str(e)[:200]}")

    # AI Gen
    elif data == "ai_txt2img":
        set_session(user_id, "mode", "txt2img")
        await query.message.edit_text(
            "🖼️ **Text to Image**\n\nSend your prompt. You can prefix with a style:\n"
            "`gradient:`, `neon:`, `gold:`, `dark:`, `fire:`",
            reply_markup=cancel_keyboard()
        )

    elif data == "ai_txt2vid":
        set_session(user_id, "mode", "txt2vid")
        await query.message.edit_text(
            "🎬 **Text to Video**\n\nSend your video prompt:",
            reply_markup=cancel_keyboard()
        )

    elif data == "trial":
        row = get_user(user_id)
        if not row:
            await query.answer("❌ Please start the bot first.", show_alert=True)
            return
        if row["trial_used"]:
            await query.answer("❌ You have already used your free trial.", show_alert=True)
            return
        if is_premium(user_id):
            await query.answer("✅ You already have premium access!", show_alert=True)
            return
        add_premium(user_id, 7)
        get_db().execute("UPDATE users SET trial_used=1 WHERE user_id=?", (user_id,))
        get_db().commit()
        await query.message.edit_text(
            "🎉 **7-Day Free Trial Activated!**\n\n"
            "✅ Unlimited edits\n✅ No watermarks\n✅ No ads\n✅ Priority queue"
        )

    # Admin callbacks
    elif data == "admin_stats":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        uptime_secs = int(time.time() - START_TIME)
        h = uptime_secs // 3600
        m = (uptime_secs % 3600) // 60
        s = uptime_secs % 60
        await query.message.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"Total Users: {get_user_count()}\n"
            f"Premium Users: {get_premium_count()}\n"
            f"Total Edits: {get_total_edits()}\n"
            f"Uptime: {h:02d}:{m:02d}:{s:02d}\n"
            f"FFmpeg: {'✅' if check_ffmpeg() else '❌'}\n"
            f"CPU: {psutil.cpu_percent():.1f}%\n"
            f"Memory: {psutil.virtual_memory().percent:.1f}%",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
        )

    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        await query.message.edit_text(
            "🔑 **Admin Panel**",
            reply_markup=admin_panel_keyboard()
        )

    elif data == "admin_maintenance":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        current = get_setting("maintenance_mode", "0")
        new_val = "0" if current == "1" else "1"
        set_setting("maintenance_mode", new_val)
        status = "🔧 ON" if new_val == "1" else "✅ OFF"
        await query.answer(f"Maintenance mode: {status}", show_alert=True)

    elif data == "admin_cleanup":
        if not is_admin(user_id):
            await query.answer("❌ Admin only.", show_alert=True)
            return
        cleanup_temp_files(0)
        cleanup_sessions()
        await query.answer("✅ Cleanup complete!", show_alert=True)

    elif data in ("do_rename", "do_metadata"):
        rename_path = get_session(user_id, "rename_path")
        if not rename_path or not os.path.exists(rename_path):
            await query.answer("❌ No file found.", show_alert=True)
            return
        if data == "do_rename":
            set_session(user_id, "mode", "rename")
            await query.message.edit_text(
                "✏️ Type the new filename (with extension):",
                reply_markup=cancel_keyboard()
            )
        else:
            set_session(user_id, "mode", "metadata")
            set_session(user_id, "metadata_path", rename_path)
            await show_metadata_menu(client, query.message)

    else:
        await query.answer("Unknown action.", show_alert=True)

    try:
        await query.answer()
    except Exception:
        pass

# ============================================================
# FLASK WEB DASHBOARD
# ============================================================
flask_app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KiraFx Bot Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0ff; }
        .header { background: linear-gradient(135deg, #1a1a3e, #2d1b69); padding: 20px 30px;
                  display: flex; align-items: center; justify-content: space-between;
                  border-bottom: 1px solid #333; }
        .header h1 { font-size: 1.5rem; color: #a78bfa; }
        .header .version { font-size: 0.85rem; color: #888; }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                      gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #1a1a2e; border: 1px solid #2d2d4e; border-radius: 12px;
                     padding: 20px; text-align: center; }
        .stat-card .value { font-size: 2rem; font-weight: bold; color: #a78bfa; }
        .stat-card .label { font-size: 0.85rem; color: #888; margin-top: 5px; }
        .section { background: #1a1a2e; border: 1px solid #2d2d4e; border-radius: 12px;
                   padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #a78bfa; margin-bottom: 15px; font-size: 1.1rem; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #2d2d4e; font-size: 0.9rem; }
        th { color: #a78bfa; font-weight: 600; }
        td { color: #ccc; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
        .badge-prem { background: #3d2070; color: #a78bfa; }
        .badge-free { background: #1e3a2e; color: #4ade80; }
        .badge-banned { background: #3b1a1a; color: #f87171; }
        .badge-admin { background: #3b2d00; color: #fbbf24; }
        .status-ok { color: #4ade80; }
        .status-err { color: #f87171; }
        .refresh-note { text-align: right; font-size: 0.75rem; color: #555; margin-bottom: 10px; }
        .bar { height: 8px; background: #2d2d4e; border-radius: 4px; overflow: hidden; margin-top: 8px; }
        .bar-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a78bfa); border-radius: 4px; }
        @media (max-width: 600px) { .stats-grid { grid-template-columns: 1fr 1fr; } }
    </style>
    <script>
        setTimeout(() => location.reload(), 30000);
        function updateTime() {
            const el = document.getElementById('last-refresh');
            if (el) el.textContent = 'Last refresh: ' + new Date().toLocaleTimeString();
        }
        window.onload = updateTime;
    </script>
</head>
<body>
    <div class="header">
        <div>
            <h1>🎬 KiraFx Bot Dashboard</h1>
            <div class="version">{{ bot_name }} | v{{ version }}</div>
        </div>
        <div class="version" id="last-refresh">Auto-refresh: 30s</div>
    </div>
    <div class="container">
        <div class="refresh-note">Auto-refreshes every 30 seconds</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{{ stats.total_users }}</div>
                <div class="label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ stats.premium_users }}</div>
                <div class="label">Premium Users</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ stats.total_edits }}</div>
                <div class="label">Total Edits</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ stats.uptime }}</div>
                <div class="label">Uptime</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ stats.cpu }}%</div>
                <div class="label">CPU Usage</div>
                <div class="bar"><div class="bar-fill" style="width:{{ stats.cpu }}%"></div></div>
            </div>
            <div class="stat-card">
                <div class="value">{{ stats.mem }}%</div>
                <div class="label">Memory Usage</div>
                <div class="bar"><div class="bar-fill" style="width:{{ stats.mem }}%"></div></div>
            </div>
        </div>

        <div class="section">
            <h2>🔧 System Status</h2>
            <table>
                <tr><td>FFmpeg</td><td class="{{ 'status-ok' if stats.ffmpeg else 'status-err' }}">{{ '✅ Installed' if stats.ffmpeg else '❌ Not Found' }}</td></tr>
                <tr><td>Database</td><td class="status-ok">✅ Connected</td></tr>
                <tr><td>Maintenance Mode</td><td>{{ '🔧 ON' if stats.maintenance else '✅ OFF' }}</td></tr>
                <tr><td>Free Edits/Day</td><td>{{ stats.free_edits }}</td></tr>
                <tr><td>Ads Enabled</td><td>{{ 'Yes' if stats.ads_enabled else 'No' }}</td></tr>
                <tr><td>Image Filters</td><td>{{ stats.image_filters }}</td></tr>
                <tr><td>Video Effects</td><td>{{ stats.video_effects }}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>👥 Recent Users</h2>
            <table>
                <thead>
                    <tr><th>ID</th><th>Name</th><th>Status</th><th>Edits</th><th>Joined</th></tr>
                </thead>
                <tbody>
                {% for u in users %}
                <tr>
                    <td><code>{{ u.user_id }}</code></td>
                    <td>{{ u.first_name }} @{{ u.username or '-' }}</td>
                    <td>
                        {% if u.is_banned %}<span class="badge badge-banned">Banned</span>
                        {% elif u.is_admin %}<span class="badge badge-admin">Admin</span>
                        {% elif u.is_premium %}<span class="badge badge-prem">Premium</span>
                        {% else %}<span class="badge badge-free">Free</span>{% endif %}
                    </td>
                    <td>{{ u.total_edits }}</td>
                    <td>{{ u.joined_at[:10] }}</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@flask_app.route("/")
def dashboard():
    uptime_secs = int(time.time() - START_TIME)
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    users = get_all_users()[-20:]
    stats = {
        "total_users": get_user_count(),
        "premium_users": get_premium_count(),
        "total_edits": get_total_edits(),
        "uptime": f"{h:02d}:{m:02d}:{s:02d}",
        "cpu": round(psutil.cpu_percent(), 1),
        "mem": round(psutil.virtual_memory().percent, 1),
        "ffmpeg": check_ffmpeg(),
        "maintenance": get_setting("maintenance_mode") == "1",
        "free_edits": get_setting("free_edits_per_day", str(FREE_EDITS_PER_DAY)),
        "ads_enabled": get_setting("ads_enabled") == "1",
        "image_filters": len(IMAGE_FILTERS),
        "video_effects": len(VIDEO_EFFECTS),
    }
    return render_template_string(
        DASHBOARD_HTML,
        stats=stats,
        users=users,
        bot_name=BOT_NAME,
        version=BOT_VERSION,
    )

@flask_app.route("/api/stats")
def api_stats():
    return jsonify({
        "total_users": get_user_count(),
        "premium_users": get_premium_count(),
        "total_edits": get_total_edits(),
        "uptime": int(time.time() - START_TIME),
        "ffmpeg": check_ffmpeg(),
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
    })

@flask_app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": BOT_NAME})

def run_flask():
    """Run Flask in a separate thread."""
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)

# ============================================================
# KEEP-ALIVE
# ============================================================
def keep_alive_ping():
    """Ping keep-alive URL periodically."""
    while True:
        try:
            if KEEP_ALIVE_URL:
                req_lib.get(KEEP_ALIVE_URL, timeout=10)
            else:
                req_lib.get(f"http://localhost:{FLASK_PORT}/health", timeout=10)
        except Exception:
            pass
        time.sleep(240)

def temp_cleanup_loop():
    """Periodic temp file cleanup."""
    while True:
        time.sleep(3600)
        cleanup_temp_files(3600)
        cleanup_sessions()

# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    logger.info(f"Starting {BOT_NAME}")

    # Init database
    init_db()

    # Check FFmpeg
    if check_ffmpeg():
        logger.info("FFmpeg found ✅")
    else:
        logger.warning("FFmpeg NOT found ❌ - Video features will be limited")

    # Start Flask dashboard in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask dashboard started on port {FLASK_PORT}")

    # Start keep-alive thread
    ka_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ka_thread.start()

    # Start temp cleanup thread
    cleanup_thread = threading.Thread(target=temp_cleanup_loop, daemon=True)
    cleanup_thread.start()

    logger.info("Bot starting...")
    app.run()

if __name__ == "__main__":
    main()
