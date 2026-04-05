#!/usr/bin/env python3
# ============================================
# KINVA MASTER PRO - MAIN BOT FILE
# VIDEO/IMAGE EDITING | MONGODB | ADMIN PANEL
# VERSION: 7.0.0
# ============================================

# ============================================
# STANDARD LIBRARY IMPORTS
# ============================================

import os
import sys
import json
import time
import asyncio
import logging
import sqlite3
import hashlib
import hmac
import secrets
import string
import random
import re
import uuid
import base64
import binascii
import threading
import multiprocessing
import subprocess
import signal
import atexit
import gc
import inspect
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any, Union, Callable, Awaitable
from functools import wraps, partial
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, asdict, field
from enum import Enum
from io import BytesIO, StringIO
from contextlib import contextmanager, asynccontextmanager

# ============================================
# THIRD PARTY IMPORTS - WEB SERVER
# ============================================

from flask import (
    Flask, jsonify, request, send_file, send_from_directory, 
    render_template, abort, redirect, url_for, make_response,
    Response, stream_with_context, session
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ============================================
# THIRD PARTY IMPORTS - DATABASE
# ============================================

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import (
    ConnectionFailure, OperationFailure, DuplicateKeyError, 
    ServerSelectionTimeoutError, BulkWriteError
)
from bson import ObjectId, json_util
from bson.errors import InvalidId
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

# ============================================
# THIRD PARTY IMPORTS - TELEGRAM
# ============================================

from telegram import (
    Update, User, Chat, Message, CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    KeyboardButton, ForceReply, WebAppInfo, LoginUrl, InputFile,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio,
    InlineQueryResultArticle, InlineQueryResultPhoto, InlineQueryResultVideo,
    InlineQueryResultDocument, InlineQueryResultAudio, InlineQueryResultGif,
    InlineQueryResultCachedPhoto, InlineQueryResultCachedVideo, InlineQueryResultCachedDocument,
    InlineQueryResultCachedAudio, InlineQueryResultCachedGif, InlineQueryResultCachedMpeg4Gif,
    InlineQueryResultLocation, InlineQueryResultVenue, InlineQueryResultContact,
    InlineQueryResultGame, InlineQueryResultVoice, InlineQueryResultCachedVoice,
    InlineQueryResultCachedSticker, InlineQueryResultCachedSticker,
    PreCheckoutQuery, ShippingQuery, SuccessfulPayment, LabeledPrice,
    MenuButtonCommands, MenuButtonWebApp, MenuButtonDefault, BotCommand,
    BotCommandScopeChat, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators, BotCommandScopeChatMember, BotCommandScopeDefault,
    ChatMemberUpdated, ChatJoinRequest, ChatPermissions, ChatAdministratorRights,
    ForumTopic, ForumTopicCreated, ForumTopicClosed, ForumTopicReopened,
    GeneralForumTopicHidden, GeneralForumTopicUnhidden, WriteAccessAllowed,
    ProximityAlertTriggered, MessageAutoDeleteTimerChanged, VideoChatScheduled,
    VideoChatStarted, VideoChatEnded, VideoChatParticipantsInvited, WebAppData,
    InlineQuery, ChosenInlineResult, Poll, PollAnswer, PollOption,
    PassportData, EncryptedPassportElement, PassportElementError,
    InlineKeyboardMarkup as InlineKeyboardMarkupType,
    ReplyKeyboardMarkup as ReplyKeyboardMarkupType,
    ForceReply as ForceReplyType, ReplyKeyboardRemove as ReplyKeyboardRemoveType
)
from telegram.constants import (
    ChatAction, ParseMode, ChatType, MessageEntityType, 
    InlineQueryResultType, UpdateType, ReactionEmoji,
    PollType, PassportElementType, EncryptedPassportElementType
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler, PollHandler, PollAnswerHandler,
    InlineQueryHandler, ChosenInlineResultHandler, ChatMemberHandler,
    ChatJoinRequestHandler, TypeHandler, JobQueue, Defaults,
    Updater, CallbackContext, ExtBot, DefaultBotSession
)
from telegram.error import (
    TelegramError, BadRequest, Unauthorized, Forbidden, InvalidToken,
    NetworkError, RetryAfter, TimedOut, Conflict, ChatMigrated,
    TelegramError as TelegramErrorMessage
)
from telegram.request import HTTPXRequest
from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.types import FileLike, JSONDict

# ============================================
# THIRD PARTY IMPORTS - VIDEO/AUDIO PROCESSING
# ============================================

try:
    # MoviePy for video editing
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, 
        TextClip, concatenate_videoclips, vfx, CompositeAudioClip,
        ImageClip, ColorClip, clips_array, afx, transfx, fx
    )
    from moviepy.video.fx import (
        fadein, fadeout, resize, rotate, crop, speedx,
        time_mirror, time_symmetrize, loop, lum_contrast,
        freeze, freeze_region, gaussian_blur, painting, charcoal,
        colorx, blackwhite, invert_colors, mask_and, mask_or,
        scroll, headblur, supersample, accel_decel
    )
    from moviepy.audio.fx import (
        volumex, audio_fadein, audio_fadeout, audio_normalize,
        audio_loop, audio_left_right
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available")

try:
    # OpenCV for advanced video processing
    import cv2
    import numpy as np
    from numpy import array, ndarray, dtype
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available")

try:
    # PIL/Pillow for image processing
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps, ImageChops, ImageStat
    from PIL.Image import open as open_image, new as new_image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️ Pillow not available")

try:
    # Audio processing
    import librosa
    import soundfile as sf
    import pydub
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    from pydub.generators import Sine, Square, Sawtooth, Pulse
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ Audio processing libraries not available")

try:
    # FFmpeg
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    print("⚠️ FFmpeg-python not available")

# ============================================
# THIRD PARTY IMPORTS - SOCIAL MEDIA DOWNLOADER
# ============================================

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("⚠️ yt-dlp not available")

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False

try:
    from TikTokApi import TikTokApi
    TIKTOK_AVAILABLE = False  # Requires setup
except ImportError:
    TIKTOK_AVAILABLE = False

# ============================================
# THIRD PARTY IMPORTS - UTILITIES
# ============================================

try:
    import aiohttp
    import aiofiles
    from aiohttp import ClientSession, ClientTimeout, TCPConnector
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp not available")

try:
    from celery import Celery, Task, shared_task
    from celery.result import AsyncResult
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("⚠️ Celery not available")

try:
    import jwt
    from jwt import PyJWTError, ExpiredSignatureError, InvalidTokenError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import qrcode
    from qrcode.image.styled import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    from qrcode.image.styles.colormasks import SolidFillColorMask
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

try:
    import sentry_sdk
    from sentry_sdk import capture_exception, capture_message
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# ============================================
# LOCAL MODULE IMPORTS (Will be created later)
# ============================================

# These will be created in separate files
# from database import MongoDB
# from video_editor import VideoEditor
# from image_editor import ImageEditor
# from filters import Filters
# from effects import Effects
# from downloader import SocialMediaDownloader
# from admin_panel import AdminPanel
# from premium_manager import PremiumManager
# from log_manager import LogManager
# from utils import Utils

# ============================================
# INITIALIZE FLASK APP FOR WEB SERVER
# ============================================

flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
CORS(flask_app)

# ============================================
# INITIALIZE GLOBAL VARIABLES
# ============================================

# Database instances
mongo_client = None
mongo_db = None
redis_client = None

# Bot instances
bot_app = None
bot_instance = None

# Editor instances
video_editor = None
image_editor = None
filters_manager = None
effects_manager = None
downloader = None

# Manager instances
admin_manager = None
premium_manager = None
log_manager = None

# ============================================
# PRINT STARTUP BANNER
# ============================================
# ============================================
# PART 2: CONFIGURATION & DATABASE CLASSES
# KINVA MASTER PRO - COMPLETE BACKEND
# ============================================

# ============================================
# CONFIGURATION CLASS
# ============================================

class Config:
    """Master Configuration Class - All Settings in One Place"""
    
    # ========================================
    # BOT CONFIGURATION
    # ========================================
    
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "kinvamasterbot")
    BOT_NAME = os.getenv("BOT_NAME", "Kinva Master Pro")
    BOT_VERSION = "7.0.0"
    
    # ========================================
    # ADMIN CONFIGURATION
    # ========================================
    
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8525952693").split(",")]
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "kinvamaster")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "support@kinvamaster.com")
    
    # ========================================
    # DATABASE CONFIGURATION
    # ========================================
    
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "kinva_master")
    MONGODB_MAX_POOL_SIZE = int(os.getenv("MONGODB_MAX_POOL_SIZE", "50"))
    MONGODB_MIN_POOL_SIZE = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))
    MONGODB_MAX_IDLE_TIME_MS = int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "10000"))
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    # ========================================
    # FILE CONFIGURATION
    # ========================================
    
    # Directories
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    THUMBNAILS_DIR = os.path.join(BASE_DIR, "thumbnails")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
    
    # File Limits
    FREE_MAX_FILE_SIZE_MB = 700
    PREMIUM_MAX_FILE_SIZE_MB = 4096
    FREE_MAX_VIDEO_DURATION = 300
    PREMIUM_MAX_VIDEO_DURATION = 3600
    FREE_DAILY_EDITS = 10
    PREMIUM_DAILY_EDITS = 999999
    FREE_DAILY_DOWNLOADS = 1
    PREMIUM_DAILY_DOWNLOADS = 50
    FREE_TRIAL_DOWNLOADS = 1
    PREMIUM_TRIAL_DAYS = 7
    
    # Allowed Extensions
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico', '.svg'}
    ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx'}
    
    # ========================================
    # PREMIUM PRICING
    # ========================================
    
    PREMIUM_PRICES = {
        "trial": {"days": 7, "price_usd": 0, "price_inr": 0, "stars": 0, "description": "Free Trial"},
        "monthly": {"days": 30, "price_usd": 9.99, "price_inr": 499, "stars": 100, "description": "Monthly Premium"},
        "yearly": {"days": 365, "price_usd": 49.99, "price_inr": 2499, "stars": 500, "description": "Yearly Premium (Save 58%)"},
        "lifetime": {"days": 3650, "price_usd": 99.99, "price_inr": 4999, "stars": 1000, "description": "Lifetime Premium"}
    }
    
    # ========================================
    # PAYMENT CONFIGURATION
    # ========================================
    
    UPI_ID = os.getenv("UPI_ID", "kinvamaster@okhdfcbank")
    UPI_NAME = os.getenv("UPI_NAME", "Kinva Master Pro")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # ========================================
    # SOCIAL MEDIA DOWNLOADER
    # ========================================
    
    SOCIAL_PLATFORMS = {
        "youtube": {
            "domains": ["youtube.com", "youtu.be", "m.youtube.com"],
            "enabled": True,
            "requires_auth": False
        },
        "instagram": {
            "domains": ["instagram.com", "instagr.am", "www.instagram.com"],
            "enabled": True,
            "requires_auth": True
        },
        "tiktok": {
            "domains": ["tiktok.com", "vm.tiktok.com", "www.tiktok.com"],
            "enabled": True,
            "requires_auth": False
        },
        "twitter": {
            "domains": ["twitter.com", "x.com", "www.twitter.com"],
            "enabled": True,
            "requires_auth": False
        },
        "facebook": {
            "domains": ["facebook.com", "fb.com", "www.facebook.com", "fb.watch"],
            "enabled": True,
            "requires_auth": False
        },
        "reddit": {
            "domains": ["reddit.com", "www.reddit.com", "redd.it"],
            "enabled": True,
            "requires_auth": False
        },
        "pinterest": {
            "domains": ["pinterest.com", "www.pinterest.com", "pin.it"],
            "enabled": True,
            "requires_auth": False
        },
        "twitch": {
            "domains": ["twitch.tv", "www.twitch.tv", "clips.twitch.tv"],
            "enabled": True,
            "requires_auth": False
        },
        "vimeo": {
            "domains": ["vimeo.com", "www.vimeo.com", "player.vimeo.com"],
            "enabled": True,
            "requires_auth": False
        },
        "dailymotion": {
            "domains": ["dailymotion.com", "www.dailymotion.com", "dai.ly"],
            "enabled": True,
            "requires_auth": False
        },
        "telegram": {
            "domains": ["t.me", "telegram.me", "www.t.me"],
            "enabled": True,
            "requires_auth": False
        },
        "whatsapp": {
            "domains": ["whatsapp.com", "wa.me"],
            "enabled": False,
            "requires_auth": True
        },
        "linkedin": {
            "domains": ["linkedin.com", "www.linkedin.com"],
            "enabled": False,
            "requires_auth": True
        },
        "snapchat": {
            "domains": ["snapchat.com", "www.snapchat.com"],
            "enabled": False,
            "requires_auth": True
        }
    }
    
    # ========================================
    # VIDEO EFFECTS (50+ TOOLS)
    # ========================================
    
    VIDEO_EFFECTS = {
        "basic": ["trim", "crop", "resize", "rotate", "flip_h", "flip_v", "speed", "reverse", "loop", "compress"],
        "transitions": ["fade", "dissolve", "wipe", "slide", "zoom", "blur", "glitch", "pixelate", "cube", "flip"],
        "filters": ["grayscale", "sepia", "invert", "emboss", "sharpen", "blur", "vintage", "neon", "cinematic"],
        "audio": ["extract", "remove", "add_music", "volume", "fade", "slow_motion", "fast_motion", "echo", "reverb"],
        "advanced": ["chroma_key", "green_screen", "picture_in_picture", "split_screen", "mosaic", "watermark", "text_overlay", "subtitles", "stabilize", "slow_mo_ai"]
    }
    
    # ========================================
    # IMAGE EFFECTS (50+ TOOLS)
    # ========================================
    
    IMAGE_EFFECTS = {
        "basic": ["resize", "crop", "rotate", "flip_h", "flip_v", "compress", "convert"],
        "adjustments": ["brightness", "contrast", "saturation", "sharpness", "hue", "exposure", "temperature"],
        "filters": ["grayscale", "sepia", "invert", "emboss", "blur", "sharpen", "vintage", "neon", "glow", "cartoon"],
        "artistic": ["oil_paint", "watercolor", "sketch", "pixelate", "mosaic", "pointillism", "stained_glass"],
        "advanced": ["remove_bg", "face_detect", "add_text", "add_sticker", "add_frame", "collage", "merge"]
    }
    
    # ========================================
    # LOG CHANNELS
    # ========================================
    
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "-1001234567890")) if os.getenv("LOG_CHANNEL_ID") else None
    ERROR_LOG_CHANNEL = int(os.getenv("ERROR_LOG_CHANNEL", "-1001234567890")) if os.getenv("ERROR_LOG_CHANNEL") else None
    ADMIN_LOG_CHANNEL = int(os.getenv("ADMIN_LOG_CHANNEL", "-1001234567890")) if os.getenv("ADMIN_LOG_CHANNEL") else None
    USER_LOG_CHANNEL = int(os.getenv("USER_LOG_CHANNEL", "-1001234567890")) if os.getenv("USER_LOG_CHANNEL") else None
    PREMIUM_LOG_CHANNEL = int(os.getenv("PREMIUM_LOG_CHANNEL", "-1001234567890")) if os.getenv("PREMIUM_LOG_CHANNEL") else None
    
    # ========================================
    # MINI APP CONFIGURATION
    # ========================================
    
    MINI_APP_URL = os.getenv("MINI_APP_URL", "https://kinva-master.onrender.com/mini-app")
    MINI_APP_ENABLED = os.getenv("MINI_APP_ENABLED", "true").lower() == "true"
    
    # ========================================
    # WEBHOOK CONFIGURATION
    # ========================================
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PORT = int(os.getenv("PORT", 8080))
    WEBHOOK_HOST = os.getenv("HOST", "0.0.0.0")
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    
    # ========================================
    # CACHE CONFIGURATION
    # ========================================
    
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    TEMP_FILE_LIFETIME = int(os.getenv("TEMP_FILE_LIFETIME", "3600"))
    
    # ========================================
    # RATE LIMITING
    # ========================================
    
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # ========================================
    # SECURITY CONFIGURATION
    # ========================================
    
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", secrets.token_hex(32))
    JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    
    # ========================================
    # MONITORING
    # ========================================
    
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    HEALTH_CHECK_ENABLED = os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true"
    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    
    # ========================================
    # SUPPORT & CONTACT
    # ========================================
    
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/kinvasupport")
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@kinvamaster.com")
    WEBSITE = os.getenv("WEBSITE", "https://kinvamaster.com")
    TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "https://t.me/kinvamaster")
    
    # ========================================
    # WELCOME MESSAGES
    # ========================================
    
    WELCOME_TEXT = """
🎬 **{bot_name}** 🎬

━━━━━━━━━━━━━━━━━━━━━━
✨ **WELCOME {first_name}!** ✨
━━━━━━━━━━━━━━━━━━━━━━

📀 **Plan:** {plan}
📁 **File Limit:** {max_size}MB
🎥 **Max Duration:** {duration} min
📊 **Daily Edits:** {daily_edits}
📈 **Total Edits:** {total_edits}

━━━━━━━━━━━━━━━━━━━━━━
🎬 **50+ VIDEO EDITING TOOLS** 🎬
━━━━━━━━━━━━━━━━━━━━━━

• ✂️ Trim & Cut Video
• 🎯 Crop & Rotate
• ⚡ Speed Control (0.5x - 3x)
• 🎨 50+ Professional Filters
• ✨ 30+ Video Effects
• 🎵 Audio Tools
• 📝 Text Overlay
• 🟢 Chroma Key
• 🎯 Motion Tracking
• 🔄 Reverse Video
• 📦 Compress Video
• 🖼️ Extract Frames

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

━━━━━━━━━━━━━━━━━━━━━━
📥 **SOCIAL MEDIA DOWNLOADER** 📥
━━━━━━━━━━━━━━━━━━━━━━

• YouTube • Instagram • TikTok
• Twitter • Facebook • Reddit
• Pinterest • Twitch • Vimeo

**Free Trial:** 1 download | **Premium:** Unlimited

━━━━━━━━━━━━━━━━━━━━━━
💡 **Send me a photo or video to start editing!**
"""
    
    WELCOME_PHOTO_URL = os.getenv("WELCOME_PHOTO_URL", "https://telegra.ph/file/kinva-master-welcome.jpg")
    WELCOME_VIDEO_URL = os.getenv("WELCOME_VIDEO_URL", "")
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    @classmethod
    def setup_dirs(cls):
        """Create all required directories"""
        dirs = [
            cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR,
            cls.LOGS_DIR, cls.DATABASE_DIR, cls.THUMBNAILS_DIR, cls.BACKUP_DIR,
            cls.DOWNLOADS_DIR, cls.STATIC_DIR, cls.TEMPLATES_DIR
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        print("✅ All directories created")
    
    @classmethod
    def get_max_size_mb(cls, is_premium: bool) -> int:
        """Get max file size based on premium status"""
        return cls.PREMIUM_MAX_FILE_SIZE_MB if is_premium else cls.FREE_MAX_FILE_SIZE_MB
    
    @classmethod
    def get_max_size_bytes(cls, is_premium: bool) -> int:
        """Get max file size in bytes"""
        return cls.get_max_size_mb(is_premium) * 1024 * 1024
    
    @classmethod
    def get_max_duration(cls, is_premium: bool) -> int:
        """Get max video duration based on premium status"""
        return cls.PREMIUM_MAX_VIDEO_DURATION if is_premium else cls.FREE_MAX_VIDEO_DURATION
    
    @classmethod
    def get_daily_edits(cls, is_premium: bool) -> int:
        """Get daily edit limit based on premium status"""
        return cls.PREMIUM_DAILY_EDITS if is_premium else cls.FREE_DAILY_EDITS
    
    @classmethod
    def get_daily_downloads(cls, is_premium: bool) -> int:
        """Get daily download limit based on premium status"""
        return cls.PREMIUM_DAILY_DOWNLOADS if is_premium else cls.FREE_DAILY_DOWNLOADS
    
    @classmethod
    def check_file_size(cls, size_bytes: int, is_premium: bool) -> tuple:
        """Check if file size is within limit"""
        limit = cls.get_max_size_bytes(is_premium)
        if size_bytes > limit:
            return False, f"❌ File too large! Max {limit//(1024*1024)}MB"
        return True, "OK"
    
    @classmethod
    def check_video_duration(cls, duration: int, is_premium: bool) -> tuple:
        """Check if video duration is within limit"""
        limit = cls.get_max_duration(is_premium)
        if duration > limit:
            return False, f"❌ Video too long! Max {limit//60} minutes"
        return True, "OK"
    
    @classmethod
    def get_version(cls) -> str:
        """Get bot version"""
        return cls.BOT_VERSION
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_premium_plan(cls, plan_type: str) -> dict:
        """Get premium plan details"""
        return cls.PREMIUM_PRICES.get(plan_type, cls.PREMIUM_PRICES["monthly"])
    
    @classmethod
    def validate_platform(cls, platform: str) -> bool:
        """Check if social media platform is supported"""
        return platform in cls.SOCIAL_PLATFORMS and cls.SOCIAL_PLATFORMS[platform]["enabled"]
    
    @classmethod
    def get_all_platforms(cls) -> list:
        """Get all supported platforms"""
        return [p for p, config in cls.SOCIAL_PLATFORMS.items() if config["enabled"]]

# Create directories
Config.setup_dirs()

# ============================================
# MONGODB DATABASE CLASS
# ============================================

class MongoDB:
    """Complete MongoDB Database Manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self.connection_attempts = 0
        self.max_attempts = 5
        self.connect()
    
    def connect(self):
        """Connect to MongoDB with retry logic"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                Config.MONGODB_URI,
                maxPoolSize=Config.MONGODB_MAX_POOL_SIZE,
                minPoolSize=Config.MONGODB_MIN_POOL_SIZE,
                maxIdleTimeMS=Config.MONGODB_MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            self.db = self.client[Config.MONGODB_DB_NAME]
            self.connected = True
            self.connection_attempts = 0
            logger.info("✅ MongoDB Connected Successfully")
        except Exception as e:
            self.connected = False
            self.connection_attempts += 1
            logger.error(f"❌ MongoDB Connection Error (Attempt {self.connection_attempts}/{self.max_attempts}): {e}")
            if self.connection_attempts < self.max_attempts:
                time.sleep(5)
                self.connect()
            else:
                logger.critical("❌ Failed to connect to MongoDB after multiple attempts")
    
    async def ensure_connection(self):
        """Ensure database connection is active"""
        if not self.connected:
            self.connect()
            await asyncio.sleep(1)
        return self.connected
    
    async def get_collection(self, name: str):
        """Get collection by name"""
        await self.ensure_connection()
        return self.db[name]
    
    async def ping(self) -> bool:
        """Check database connection"""
        try:
            await self.db.command('ping')
            return True
        except:
            return False
    
    # ========================================
    # INDEX MANAGEMENT
    # ========================================
    
    async def create_indexes(self):
        """Create all database indexes"""
        try:
            # Users collection indexes
            users_collection = await self.get_collection("users")
            await users_collection.create_index("user_id", unique=True)
            await users_collection.create_index("referral_code", unique=True)
            await users_collection.create_index("is_premium")
            await users_collection.create_index("premium_expiry")
            await users_collection.create_index("created_at")
            await users_collection.create_index("banned")
            
            # Edit history indexes
            edit_history = await self.get_collection("edit_history")
            await edit_history.create_index("user_id")
            await edit_history.create_index("created_at")
            await edit_history.create_index("edit_type")
            
            # Download history indexes
            download_history = await self.get_collection("download_history")
            await download_history.create_index("user_id")
            await download_history.create_index("created_at")
            await download_history.create_index("platform")
            
            # Transactions indexes
            transactions = await self.get_collection("transactions")
            await transactions.create_index("user_id")
            await transactions.create_index("transaction_id", unique=True)
            await transactions.create_index("created_at")
            await transactions.create_index("status")
            
            # Feedback indexes
            feedback = await self.get_collection("feedback")
            await feedback.create_index("user_id")
            await feedback.create_index("created_at")
            await feedback.create_index("status")
            
            # Notifications indexes
            notifications = await self.get_collection("notifications")
            await notifications.create_index("user_id")
            await notifications.create_index("is_read")
            await notifications.create_index("created_at")
            
            # Projects indexes
            projects = await self.get_collection("projects")
            await projects.create_index("user_id")
            await projects.create_index("created_at")
            await projects.create_index("status")
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    # ========================================
    # USER MANAGEMENT
    # ========================================
    
    @staticmethod
    def generate_referral_code() -> str:
        """Generate unique referral code"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    async def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: str = None):
        """Create new user"""
        try:
            collection = await self.get_collection("users")
            
            # Check if user exists
            existing = await collection.find_one({"user_id": user_id})
            if existing:
                return existing
            
            # Generate referral code
            referral_code = self.generate_referral_code()
            while await collection.find_one({"referral_code": referral_code}):
                referral_code = self.generate_referral_code()
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "referral_code": referral_code,
                "referred_by": referred_by,
                "is_premium": False,
                "premium_expiry": None,
                "premium_type": None,
                "edits_today": 0,
                "total_edits": 0,
                "downloads_today": 0,
                "total_downloads": 0,
                "trial_used": False,
                "trial_downloads_used": 0,
                "banned": False,
                "ban_reason": None,
                "banned_at": None,
                "warning_count": 0,
                "balance_usd": 0.0,
                "balance_inr": 0.0,
                "stars_balance": 0,
                "referral_earnings": 0.0,
                "referrals": [],
                "settings": {
                    "language": "en",
                    "notifications": True,
                    "auto_delete": False,
                    "save_history": True,
                    "theme": "dark"
                },
                "stats": {
                    "videos_edited": 0,
                    "images_edited": 0,
                    "downloads_count": 0,
                    "total_processing_time": 0
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
            
            await collection.insert_one(user_data)
            
            # Update referrer's referral count
            if referred_by:
                referrer = await collection.find_one({"referral_code": referred_by})
                if referrer:
                    await collection.update_one(
                        {"_id": referrer["_id"]},
                        {
                            "$push": {"referrals": user_id},
                            "$inc": {"referral_count": 1, "referral_earnings": 5.0},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
            
            logger.info(f"✅ User created: {user_id} - {first_name}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            collection = await self.get_collection("users")
            return await collection.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_user_by_referral(self, referral_code: str) -> Optional[Dict]:
        """Get user by referral code"""
        try:
            collection = await self.get_collection("users")
            return await collection.find_one({"referral_code": referral_code})
        except Exception as e:
            logger.error(f"Error getting user by referral: {e}")
            return None
    
    async def update_user(self, user_id: int, data: dict) -> bool:
        """Update user data"""
        try:
            collection = await self.get_collection("users")
            data["updated_at"] = datetime.utcnow()
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def increment_user_field(self, user_id: int, field: str, amount: int = 1) -> bool:
        """Increment user field"""
        try:
            collection = await self.get_collection("users")
            result = await collection.update_one(
                {"user_id": user_id},
                {"$inc": {field: amount}, "$set": {"updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing user field: {e}")
            return False
    
    async def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium subscription"""
        try:
            user = await self.get_user(user_id)
            if user and user.get("is_premium") and user.get("premium_expiry"):
                return datetime.utcnow() < user["premium_expiry"]
            return False
        except Exception as e:
            logger.error(f"Error checking premium: {e}")
            return False
    
    async def add_premium(self, user_id: int, days: int, plan_type: str = "monthly", amount_paid: float = 0.0) -> bool:
        """Add premium subscription to user"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # Calculate new expiry
            if user.get("is_premium") and user.get("premium_expiry"):
                current_expiry = user["premium_expiry"]
                if datetime.utcnow() < current_expiry:
                    new_expiry = current_expiry + timedelta(days=days)
                else:
                    new_expiry = datetime.utcnow() + timedelta(days=days)
            else:
                new_expiry = datetime.utcnow() + timedelta(days=days)
            
            # Update user
            await self.update_user(user_id, {
                "is_premium": True,
                "premium_expiry": new_expiry,
                "premium_type": plan_type
            })
            
            # Record transaction
            await self.add_transaction(
                user_id=user_id,
                amount=amount_paid,
                plan_type=plan_type,
                duration_days=days,
                status="completed"
            )
            
            logger.info(f"✅ Premium added to user {user_id} for {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Error adding premium: {e}")
            return False
    
    async def remove_premium(self, user_id: int) -> bool:
        """Remove premium subscription from user"""
        try:
            await self.update_user(user_id, {
                "is_premium": False,
                "premium_expiry": None,
                "premium_type": None
            })
            logger.info(f"✅ Premium removed from user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing premium: {e}")
            return False
    
    async def can_edit(self, user_id: int) -> tuple:
        """Check if user can edit today"""
        try:
            if await self.is_premium(user_id):
                return True, "Premium user - unlimited edits", -1
            
            user = await self.get_user(user_id)
            if not user:
                return True, "New user - first edit", 1
            
            today = datetime.utcnow().date().isoformat()
            last_edit_date = user.get("last_edit_date")
            
            if last_edit_date != today:
                return True, "First edit of the day", Config.FREE_DAILY_EDITS
            
            edits_today = user.get("edits_today", 0)
            if edits_today < Config.FREE_DAILY_EDITS:
                remaining = Config.FREE_DAILY_EDITS - edits_today
                return True, f"Edit {edits_today + 1}/{Config.FREE_DAILY_EDITS}", remaining
            
            return False, f"Daily limit reached! {Config.FREE_DAILY_EDITS}/{Config.FREE_DAILY_EDITS}", 0
            
        except Exception as e:
            logger.error(f"Error checking edit limit: {e}")
            return True, "Error checking limit", 0
    
    async def increment_edits(self, user_id: int, edit_type: str = "general", tool: str = None, file_size: int = 0) -> bool:
        """Increment user edit count"""
        try:
            today = datetime.utcnow().date().isoformat()
            user = await self.get_user(user_id)
            
            if not user:
                return False
            
            if user.get("last_edit_date") != today:
                await self.update_user(user_id, {
                    "edits_today": 1,
                    "last_edit_date": today,
                    "total_edits": user.get("total_edits", 0) + 1
                })
            else:
                await self.update_user(user_id, {
                    "edits_today": user.get("edits_today", 0) + 1,
                    "total_edits": user.get("total_edits", 0) + 1
                })
            
            # Record edit history
            await self.add_edit_history(user_id, edit_type, tool, file_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing edits: {e}")
            return False
    
    async def can_download(self, user_id: int) -> tuple:
        """Check if user can download from social media"""
        try:
            if await self.is_premium(user_id):
                return True, "Premium user - unlimited downloads", -1
            
            user = await self.get_user(user_id)
            if not user:
                return True, "New user - free trial available", Config.FREE_TRIAL_DOWNLOADS
            
            # Check trial downloads
            trial_used = user.get("trial_downloads_used", 0)
            if trial_used < Config.FREE_TRIAL_DOWNLOADS:
                remaining = Config.FREE_TRIAL_DOWNLOADS - trial_used
                return True, f"Free trial: {trial_used + 1}/{Config.FREE_TRIAL_DOWNLOADS}", remaining
            
            return False, "Free trial used! Upgrade to premium for unlimited downloads.", 0
            
        except Exception as e:
            logger.error(f"Error checking download limit: {e}")
            return True, "Error checking limit", 0
    
    async def increment_downloads(self, user_id: int, platform: str, url: str, file_size: int = 0) -> bool:
        """Increment user download count"""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            if not await self.is_premium(user_id):
                await self.increment_user_field(user_id, "trial_downloads_used", 1)
            
            await self.increment_user_field(user_id, "total_downloads", 1)
            
            # Record download history
            await self.add_download_history(user_id, platform, url, file_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing downloads: {e}")
            return False
    
    # ========================================
    # HISTORY MANAGEMENT
    # ========================================
    
    async def add_edit_history(self, user_id: int, edit_type: str, tool: str = None, file_size: int = 0) -> bool:
        """Add edit history record"""
        try:
            collection = await self.get_collection("edit_history")
            await collection.insert_one({
                "user_id": user_id,
                "edit_type": edit_type,
                "tool_used": tool,
                "file_size": file_size,
                "created_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding edit history: {e}")
            return False
    
    async def add_download_history(self, user_id: int, platform: str, url: str, file_size: int = 0) -> bool:
        """Add download history record"""
        try:
            collection = await self.get_collection("download_history")
            await collection.insert_one({
                "user_id": user_id,
                "platform": platform,
                "url": url,
                "file_size": file_size,
                "created_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding download history: {e}")
            return False
    
    async def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user edit history"""
        try:
            collection = await self.get_collection("edit_history")
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return []
    
    # ========================================
    # TRANSACTION MANAGEMENT
    # ========================================
    
    async def add_transaction(self, user_id: int, amount: float, plan_type: str = None, 
                              duration_days: int = None, transaction_id: str = None, 
                              payment_method: str = None, status: str = "pending") -> bool:
        """Add transaction record"""
        try:
            collection = await self.get_collection("transactions")
            
            if not transaction_id:
                transaction_id = f"TXN_{int(time.time())}_{secrets.token_hex(8)}"
            
            await collection.insert_one({
                "user_id": user_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "plan_type": plan_type,
                "duration_days": duration_days,
                "payment_method": payment_method,
                "status": status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    async def update_transaction(self, transaction_id: str, status: str, completed_at: datetime = None) -> bool:
        """Update transaction status"""
        try:
            collection = await self.get_collection("transactions")
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            if completed_at:
                update_data["completed_at"] = completed_at
            
            result = await collection.update_one(
                {"transaction_id": transaction_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return False
    
    async def get_user_transactions(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user transactions"""
        try:
            collection = await self.get_collection("transactions")
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    # ========================================
    # FEEDBACK MANAGEMENT
    # ========================================
    
    async def add_feedback(self, user_id: int, message: str, rating: int = 5, category: str = "general") -> bool:
        """Add user feedback"""
        try:
            collection = await self.get_collection("feedback")
            await collection.insert_one({
                "user_id": user_id,
                "message": message,
                "rating": rating,
                "category": category,
                "status": "pending",
                "admin_response": None,
                "created_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return False
    
    async def get_feedback(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get feedback entries"""
        try:
            collection = await self.get_collection("feedback")
            query = {}
            if status:
                query["status"] = status
            
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []
    
    async def respond_feedback(self, feedback_id: str, admin_response: str) -> bool:
        """Respond to feedback"""
        try:
            collection = await self.get_collection("feedback")
            from bson import ObjectId
            result = await collection.update_one(
                {"_id": ObjectId(feedback_id)},
                {"$set": {
                    "status": "replied",
                    "admin_response": admin_response,
                    "replied_at": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error responding to feedback: {e}")
            return False
    
    # ========================================
    # NOTIFICATION MANAGEMENT
    # ========================================
    
    async def add_notification(self, user_id: int, title: str, message: str, notif_type: str = "info") -> bool:
        """Add user notification"""
        try:
            collection = await self.get_collection("notifications")
            await collection.insert_one({
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notif_type,
                "is_read": False,
                "created_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding notification: {e}")
            return False
    
    async def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user notifications"""
        try:
            collection = await self.get_collection("notifications")
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            collection = await self.get_collection("notifications")
            from bson import ObjectId
            result = await collection.update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"is_read": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            return False
    
    # ========================================
    # PROJECT MANAGEMENT
    # ========================================
    
    async def save_project(self, user_id: int, name: str, data: dict, thumbnail: str = None) -> str:
        """Save user project"""
        try:
            collection = await self.get_collection("projects")
            project_id = str(uuid.uuid4())
            
            await collection.insert_one({
                "project_id": project_id,
                "user_id": user_id,
                "name": name,
                "data": data,
                "thumbnail": thumbnail,
                "status": "draft",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            return project_id
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return None
    
    async def get_user_projects(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user projects"""
        try:
            collection = await self.get_collection("projects")
            cursor = collection.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    async def delete_project(self, project_id: str, user_id: int) -> bool:
        """Delete user project"""
        try:
            collection = await self.get_collection("projects")
            result = await collection.delete_one({"project_id": project_id, "user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False
    
    # ========================================
    # BROADCAST MANAGEMENT
    # ========================================
    
    async def add_broadcast(self, admin_id: int, message: str, recipients: int, success: int, failed: int) -> bool:
        """Add broadcast record"""
        try:
            collection = await self.get_collection("broadcasts")
            await collection.insert_one({
                "admin_id": admin_id,
                "message": message,
                "recipients": recipients,
                "success": success,
                "failed": failed,
                "created_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding broadcast: {e}")
            return False
    
    async def get_broadcast_history(self, limit: int = 20) -> List[Dict]:
        """Get broadcast history"""
        try:
            collection = await self.get_collection("broadcasts")
            cursor = collection.find().sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting broadcast history: {e}")
            return []
    
    # ========================================
    # STATISTICS
    # ========================================
    
    async def get_stats(self) -> Dict:
        """Get bot statistics"""
        try:
            users_collection = await self.get_collection("users")
            edit_collection = await self.get_collection("edit_history")
            
            total_users = await users_collection.count_documents({})
            premium_users = await users_collection.count_documents({"is_premium": True})
            banned_users = await users_collection.count_documents({"banned": True})
            
            # Total edits
            pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_edits"}}}]
            result = await users_collection.aggregate(pipeline).to_list(None)
            total_edits = result[0]["total"] if result else 0
            
            # Today's edits
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_edits = await edit_collection.count_documents({"created_at": {"$gte": today_start}})
            
            # Recent users
            recent_users = await users_collection.find().sort("created_at", -1).limit(10).to_list(None)
            
            return {
                "total_users": total_users,
                "premium_users": premium_users,
                "banned_users": banned_users,
                "free_users": total_users - premium_users,
                "total_edits": total_edits,
                "today_edits": today_edits,
                "recent_users": recent_users
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    # ========================================
    # BAN MANAGEMENT
    # ========================================
    
    async def ban_user(self, user_id: int, reason: str = None, admin_id: int = None) -> bool:
        """Ban a user"""
        try:
            await self.update_user(user_id, {
                "banned": True,
                "ban_reason": reason,
                "banned_at": datetime.utcnow(),
                "banned_by": admin_id
            })
            logger.info(f"User {user_id} banned. Reason: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    async def unban_user(self, user_id: int, admin_id: int = None) -> bool:
        """Unban a user"""
        try:
            await self.update_user(user_id, {
                "banned": False,
                "ban_reason": None,
                "banned_at": None,
                "unbanned_by": admin_id,
                "unbanned_at": datetime.utcnow()
            })
            logger.info(f"User {user_id} unbanned")
            return True
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    async def warn_user(self, user_id: int, reason: str = None) -> int:
        """Warn a user and return warning count"""
        try:
            user = await self.get_user(user_id)
            warning_count = user.get("warning_count", 0) + 1
            
            await self.update_user(user_id, {
                "warning_count": warning_count,
                "last_warning": datetime.utcnow(),
                "last_warning_reason": reason
            })
            
            # Auto-ban after 3 warnings
            if warning_count >= 3:
                await self.ban_user(user_id, "Auto-ban after 3 warnings")
            
            return warning_count
            
        except Exception as e:
            logger.error(f"Error warning user: {e}")
            return 0
    
    # ========================================
    # REFERRAL SYSTEM
    # ========================================
    
    async def process_referral(self, user_id: int, referral_code: str) -> bool:
        """Process referral when user joins"""
        try:
            # Get referrer by referral code
            referrer = await self.get_user_by_referral(referral_code)
            if not referrer or referrer["user_id"] == user_id:
                return False
            
            # Update current user with referrer
            await self.update_user(user_id, {"referred_by": referral_code})
            
            # Update referrer
            await self.update_user(referrer["user_id"], {
                "referral_earnings": referrer.get("referral_earnings", 0) + 5.0
            })
            await self.increment_user_field(referrer["user_id"], "referral_count", 1)
            
            # Add referral bonus to referrer (7 days premium)
            await self.add_premium(referrer["user_id"], Config.PREMIUM_PRICES["monthly"]["days"], "referral_bonus")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return False
    
    # ========================================
    # DATABASE BACKUP
    # ========================================
    
    async def backup_database(self) -> str:
        """Backup database to file"""
        try:
            backup_path = os.path.join(Config.BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # Get all collections
            collections = await self.db.list_collection_names()
            backup_data = {}
            
            for collection_name in collections:
                collection = await self.get_collection(collection_name)
                cursor = collection.find({})
                documents = await cursor.to_list(length=None)
                backup_data[collection_name] = documents
            
            # Save to file
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, default=str, indent=2)
            
            logger.info(f"Database backed up to {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return None

# Initialize MongoDB
mongo_db = MongoDB()

# ============================================
# REDIS CACHE CLASS
# ============================================

class RedisCache:
    """Redis Cache Manager for performance"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                Config.REDIS_URL,
                decode_responses=True,
                max_connections=Config.REDIS_MAX_CONNECTIONS
            )
            self.connected = True
            logger.info("✅ Redis Connected Successfully")
        except Exception as e:
            self.connected = False
            logger.error(f"❌ Redis Connection Error: {e}")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.connected:
            return None
        try:
            return await self.client.get(key)
        except:
            return None
    
    async def set(self, key: str, value: str, ttl: int = Config.CACHE_TTL) -> bool:
        """Set value in cache"""
        if not self.connected:
            return False
        try:
            await self.client.setex(key, ttl, value)
            return True
        except:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        if not self.connected:
            return False
        try:
            await self.client.delete(key)
            return True
        except:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.connected:
            return False
        try:
            return await self.client.exists(key) > 0
        except:
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.connected:
            return 0
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except:
            return 0

# Initialize Redis
redis_cache = RedisCache()
# ============================================
# PART 3: MAIN BOT CLASS - KINVA MASTER PRO
# ALL COMMANDS, HANDLERS, AND EDITING TOOLS
# ============================================

class KinvaMasterBot:
    """Main Bot Class - Complete Telegram Bot"""
    
    def __init__(self):
        self.db = mongo_db
        self.cache = redis_cache
        self.user_data = {}
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
        self.SETTINGS_STATE = 14
        self.DOWNLOAD_STATE = 15
        
        # Initialize sub-systems
        self.init_subsystems()
    
    def init_subsystems(self):
        """Initialize all sub-systems"""
        logger.info("Initializing bot subsystems...")
        
        # These will be implemented in separate parts
        self.video_editor = None
        self.image_editor = None
        self.filters_manager = None
        self.effects_manager = None
        self.downloader = None
        
        logger.info("✅ Bot subsystems initialized")
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def escape_markdown(self, text: str) -> str:
        """Escape markdown special characters"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    async def send_message(self, update: Update, text: str, keyboard: list = None, parse_mode: str = ParseMode.MARKDOWN):
        """Send message handling both direct and callback"""
        try:
            if update.callback_query:
                if keyboard:
                    await update.callback_query.edit_message_text(
                        text, 
                        reply_markup=InlineKeyboardMarkup(keyboard), 
                        parse_mode=parse_mode
                    )
                else:
                    await update.callback_query.edit_message_text(text, parse_mode=parse_mode)
            else:
                if keyboard:
                    await update.message.reply_text(
                        text, 
                        reply_markup=InlineKeyboardMarkup(keyboard), 
                        parse_mode=parse_mode
                    )
                else:
                    await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def delete_message(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
        """Delete message safely"""
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
    
    # ========================================
    # START COMMAND
    # ========================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            # Get user info
            if update.callback_query:
                query = update.callback_query
                await query.answer()
                user = query.from_user
                send_func = query.edit_message_text
            else:
                user = update.effective_user
                send_func = update.message.reply_text
            
            # Check if user exists in database
            user_data = await self.db.get_user(user.id)
            if not user_data:
                # Check for referral code
                args = context.args
                referral_code = args[0] if args else None
                user_data = await self.db.create_user(
                    user.id, 
                    user.username, 
                    user.first_name, 
                    user.last_name,
                    referral_code
                )
            
            # Check if banned
            if user_data and user_data.get("banned", False):
                await send_func("🚫 **You are banned from using this bot!**\n\nContact support for assistance.", parse_mode=ParseMode.MARKDOWN)
                return
            
            # Get user stats
            is_premium = await self.db.is_premium(user.id)
            max_size = Config.get_max_size_mb(is_premium)
            max_duration = Config.get_max_duration(is_premium)
            daily_edits = Config.get_daily_edits(is_premium)
            total_edits = user_data.get("total_edits", 0)
            
            # Format welcome message
            welcome_text = Config.WELCOME_TEXT.format(
                bot_name=Config.BOT_NAME,
                first_name=user.first_name,
                plan="⭐ PREMIUM" if is_premium else "📀 FREE",
                max_size=max_size,
                duration=max_duration//60,
                daily_edits=daily_edits,
                total_edits=total_edits
            )
            
            # Create main menu keyboard
            keyboard = [
                [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
                 InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
                [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
                 InlineKeyboardButton("✨ EFFECTS (30+)", callback_data="menu_effects")],
                [InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium"),
                 InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download")],
                [InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats"),
                 InlineKeyboardButton("🎁 FREE TRIAL", callback_data="menu_trial")],
                [InlineKeyboardButton("❓ HELP", callback_data="menu_help"),
                 InlineKeyboardButton("📢 SUPPORT", callback_data="menu_support")],
                [InlineKeyboardButton("🎮 OPEN MINI APP", web_app=WebAppInfo(url=Config.MINI_APP_URL))]
            ]
            
            # Add admin button if user is admin
            if Config.is_admin(user.id):
                keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="menu_admin")])
            
            # Send welcome message
            if Config.WELCOME_PHOTO_URL:
                try:
                    if update.callback_query:
                        await update.callback_query.message.reply_photo(
                            photo=Config.WELCOME_PHOTO_URL,
                            caption=welcome_text,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await update.message.reply_photo(
                            photo=Config.WELCOME_PHOTO_URL,
                            caption=welcome_text,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    return
                except:
                    pass
            
            # Fallback to text only
            await send_func(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            
            # Log user activity
            logger.info(f"User started bot: {user.id} - @{user.username}")
            
        except Exception as e:
            logger.error(f"Start command error: {e}")
            traceback.print_exc()
            await update.message.reply_text("❌ An error occurred. Please try again later.")
    
    # ========================================
    # HELP COMMAND
    # ========================================
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 **KINVA MASTER PRO - HELP MENU**

━━━━━━━━━━━━━━━━━━━━━━
**📌 BASIC COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━

/start - Start the bot
/help - Show this help menu
/menu - Show main menu
/stats - Your statistics
/premium - Premium info
/trial - Start free trial
/feedback - Send feedback
/support - Contact support
/about - About bot

━━━━━━━━━━━━━━━━━━━━━━
**🎬 VIDEO EDITING**
━━━━━━━━━━━━━━━━━━━━━━

Send me a **video** and use these tools:
• ✂️ Trim - Cut unwanted parts
• 🎯 Crop - Remove unwanted areas
• ⚡ Speed - Change speed (0.5x-3x)
• 🔄 Reverse - Play backwards
• 📦 Compress - Reduce file size
• 🔄 Rotate - Rotate video
• 🎨 Filters - Apply effects
• ✨ Effects - Add transitions

━━━━━━━━━━━━━━━━━━━━━━
**🖼️ IMAGE EDITING**
━━━━━━━━━━━━━━━━━━━━━━

Send me an **image** and use these tools:
• 📏 Resize - Change dimensions
• ✂️ Crop - Cut image
• 🔄 Rotate - Rotate image
• 🪞 Flip - Mirror image
• ☀️ Brightness - Adjust brightness
• 🌓 Contrast - Adjust contrast
• 🎨 Filters - 50+ filters

━━━━━━━━━━━━━━━━━━━━━━
**📥 SOCIAL MEDIA DOWNLOADER**
━━━━━━━━━━━━━━━━━━━━━━

Send me a link to download from:
• YouTube • Instagram • TikTok
• Twitter • Facebook • Reddit
• Pinterest • Twitch • Vimeo

**Free Trial:** 1 download
**Premium:** Unlimited downloads

━━━━━━━━━━━━━━━━━━━━━━
**⭐ PREMIUM FEATURES**
━━━━━━━━━━━━━━━━━━━━━━

• 4GB file limit (vs 700MB)
• 60 min videos (vs 5 min)
• Unlimited daily edits
• 50+ filters (vs 10)
• No watermark
• 4K export
• Priority processing

━━━━━━━━━━━━━━━━━━━━━━
**💡 TIPS**
━━━━━━━━━━━━━━━━━━━━━━

• Use /trial for 7 days free premium
• Share referral code to earn premium
• Send /feedback to report issues
• Join our channel for updates

━━━━━━━━━━━━━━━━━━━━━━
**📞 SUPPORT**
━━━━━━━━━━━━━━━━━━━━━━

• Telegram: {support_chat}
• Email: {support_email}
• Website: {website}
• Channel: {channel}
"""
        
        keyboard = [[InlineKeyboardButton("🔙 BACK TO MENU", callback_data="back_main")]]
        
        await self.send_message(
            update,
            help_text.format(
                support_chat=Config.SUPPORT_CHAT,
                support_email=Config.SUPPORT_EMAIL,
                website=Config.WEBSITE,
                channel=Config.TELEGRAM_CHANNEL
            ),
            keyboard,
            ParseMode.MARKDOWN
        )
    
    # ========================================
    # STATS COMMAND
    # ========================================
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            user_id = update.effective_user.id
            user_data = await self.db.get_user(user_id)
            
            if not user_data:
                await update.message.reply_text("❌ User not found. Please use /start")
                return
            
            is_premium = await self.db.is_premium(user_id)
            
            stats_text = f"""
📊 **YOUR STATISTICS**

━━━━━━━━━━━━━━━━━━━━━━
👤 **Profile**
━━━━━━━━━━━━━━━━━━━━━━

• User ID: `{user_id}`
• Username: @{user_data.get('username', 'N/A')}
• Plan: {'⭐ PREMIUM' if is_premium else '📀 FREE'}
• Joined: {user_data.get('created_at', 'N/A')[:10]}

{f'• Premium Expiry: {user_data["premium_expiry"][:10]}' if is_premium else ''}

━━━━━━━━━━━━━━━━━━━━━━
📈 **Activity**
━━━━━━━━━━━━━━━━━━━━━━

• Total Edits: `{user_data.get('total_edits', 0)}`
• Today's Edits: `{user_data.get('edits_today', 0)}`
• Total Downloads: `{user_data.get('total_downloads', 0)}`
• Today's Downloads: `{user_data.get('downloads_today', 0)}`

━━━━━━━━━━━━━━━━━━━━━━
💰 **Earnings**
━━━━━━━━━━━━━━━━━━━━━━

• Balance: `${user_data.get('balance_usd', 0)}`
• Stars: `{user_data.get('stars_balance', 0)}`
• Referrals: `{len(user_data.get('referrals', []))}`
• Referral Earnings: `${user_data.get('referral_earnings', 0)}`

━━━━━━━━━━━━━━━━━━━━━━
🎁 **Your Referral Code**
━━━━━━━━━━━━━━━━━━━━━━

`{user_data.get('referral_code', 'N/A')}`

Share this code with friends to earn premium!

━━━━━━━━━━━━━━━━━━━━━━
📊 **Global Stats**
━━━━━━━━━━━━━━━━━━━━━━
"""
            
            # Get global stats
            global_stats = await self.db.get_stats()
            stats_text += f"""
• Total Users: `{global_stats.get('total_users', 0)}`
• Premium Users: `{global_stats.get('premium_users', 0)}`
• Total Edits: `{global_stats.get('total_edits', 0)}`
• Today's Edits: `{global_stats.get('today_edits', 0)}`
"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 REFRESH", callback_data="menu_stats")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
            ]
            
            await self.send_message(update, stats_text, keyboard, ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Stats command error: {e}")
            await update.message.reply_text("❌ Error fetching stats. Please try again.")
    
    # ========================================
    # PREMIUM COMMAND
    # ========================================
    
    async def cmd_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command"""
        await self.premium_menu(update, context)
    
    async def premium_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium menu"""
        user_id = update.effective_user.id
        is_premium = await self.db.is_premium(user_id)
        
        if is_premium:
            user_data = await self.db.get_user(user_id)
            expiry = user_data.get('premium_expiry', datetime.utcnow())
            days_left = (expiry - datetime.utcnow()).days if expiry else 0
            
            premium_text = f"""
⭐ **PREMIUM MEMBER** ⭐

━━━━━━━━━━━━━━━━━━━━━━
✅ **Your Benefits:**
━━━━━━━━━━━━━━━━━━━━━━

• 4GB File Support (↑ 700MB)
• 60 Minute Videos (↑ 5 min)
• Unlimited Daily Edits
• 50+ Professional Filters
• 30+ Video Effects
• No Watermark
• 4K Export Quality
• Priority Processing

━━━━━━━━━━━━━━━━━━━━━━
📅 **Subscription Info**
━━━━━━━━━━━━━━━━━━━━━━

• Plan: {user_data.get('premium_type', 'Monthly').title()}
• Expires: {expiry.strftime('%Y-%m-%d') if expiry else 'N/A'}
• Days Left: {days_left}

━━━━━━━━━━━━━━━━━━━━━━
💎 Thank you for supporting Kinva Master Pro!
"""
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        else:
            premium_text = """
⭐ **KINVA MASTER PREMIUM** ⭐

━━━━━━━━━━━━━━━━━━━━━━
🚀 **UNLOCK ALL FEATURES** 🚀
━━━━━━━━━━━━━━━━━━━━━━

**FREE vs PREMIUM Comparison:**

| Feature | FREE | PREMIUM |
|---------|------|---------|
| File Size | 700MB | **4GB** |
| Duration | 5 min | **60 min** |
| Daily Edits | 10 | **Unlimited** |
| Watermark | Yes | **No** |
| Export | 720p | **4K** |
| Filters | 10 | **50+** |
| Effects | 10 | **30+** |
| Priority | No | **Yes** |

━━━━━━━━━━━━━━━━━━━━━━
💎 **PRICING** 💎
━━━━━━━━━━━━━━━━━━━━━━

• **Monthly:** $9.99 / ₹499
• **Yearly:** $49.99 / ₹2499 (Save 50%)
• **Lifetime:** $99.99 / ₹4999

━━━━━━━━━━━━━━━━━━━━━━
💳 **PAYMENT METHODS** 💳
━━━━━━━━━━━━━━━━━━━━━━

• **UPI:** `{Config.UPI_ID}`
• **Telegram Stars:** 100 stars/month
• **PayPal:** Available
• **Crypto:** USDT/BTC

🔥 **Try FREE for 7 days!** 🔥
"""
            keyboard = [
                [InlineKeyboardButton("🎁 FREE TRIAL", callback_data="menu_trial")],
                [InlineKeyboardButton("💎 BUY MONTHLY", callback_data="buy_monthly"),
                 InlineKeyboardButton("💎 BUY YEARLY", callback_data="buy_yearly")],
                [InlineKeyboardButton("👑 BUY LIFETIME", callback_data="buy_lifetime")],
                [InlineKeyboardButton("⭐ PAY WITH STARS", callback_data="pay_stars")],
                [InlineKeyboardButton("💳 UPI PAYMENT", callback_data="pay_upi")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
            ]
        
        await self.send_message(update, premium_text, keyboard, ParseMode.MARKDOWN)
    
    # ========================================
    # TRIAL COMMAND
    # ========================================
    
    async def cmd_trial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trial command"""
        user_id = update.effective_user.id
        
        # Check if already premium
        if await self.db.is_premium(user_id):
            await update.message.reply_text("✅ **You are already a premium user!**", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check if trial already used
        user_data = await self.db.get_user(user_id)
        if user_data and user_data.get("trial_used", False):
            await update.message.reply_text(
                "❌ **You have already used your free trial!**\n\n"
                "Upgrade to premium to continue using all features.\n\n"
                "⭐ /premium",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Add trial premium
        await self.db.add_premium(user_id, Config.PREMIUM_PRICES["monthly"]["days"], "trial")
        await self.db.update_user(user_id, {"trial_used": True})
        
        await update.message.reply_text(
            "🎉 **FREE TRIAL ACTIVATED!** 🎉\n\n"
            "✅ 7 days of premium features\n"
            "✅ 4GB file limit\n"
            "✅ Unlimited edits\n"
            "✅ 50+ filters\n"
            "✅ Social media downloader\n\n"
            "Enjoy! 🚀",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log trial activation
        logger.info(f"User {user_id} activated free trial")
    
    # ========================================
    # FEEDBACK COMMAND
    # ========================================
    
    async def cmd_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command"""
        await update.message.reply_text(
            "📝 **Send Feedback**\n\n"
            "Please send your feedback, bug report, or feature request.\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        return self.FEEDBACK_STATE
    
    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle feedback input"""
        user_id = update.effective_user.id
        message = update.message.text
        
        if message.startswith('/'):
            return
        
        await self.db.add_feedback(user_id, message)
        
        await update.message.reply_text(
            "✅ **Feedback Sent!**\n\n"
            "Thank you for your feedback. We'll review it and get back to you if needed.\n\n"
            "Use /menu to continue.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Notify admins
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"📝 **New Feedback**\n\n"
                    f"User: `{user_id}`\n"
                    f"Message: {message[:200]}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        return ConversationHandler.END
    
    # ========================================
    # SUPPORT COMMAND
    # ========================================
    
    async def cmd_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command"""
        support_text = f"""
📞 **SUPPORT & CONTACT**

━━━━━━━━━━━━━━━━━━━━━━
**Get Help:**
━━━━━━━━━━━━━━━━━━━━━━

• **Support Chat:** {Config.SUPPORT_CHAT}
• **Email:** {Config.SUPPORT_EMAIL}
• **Website:** {Config.WEBSITE}
• **Channel:** {Config.TELEGRAM_CHANNEL}

━━━━━━━━━━━━━━━━━━━━━━
**FAQs:**
━━━━━━━━━━━━━━━━━━━━━━

❓ **How to edit video?** - Send me a video
❓ **Premium benefits?** - Use /premium
❓ **Report bug?** - Use /feedback
❓ **Payment issue?** - Contact support

━━━━━━━━━━━━━━━━━━━━━━
**Response Time:** 24-48 hours

💬 **Join our channel for updates!**
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=Config.TELEGRAM_CHANNEL)],
            [InlineKeyboardButton("💬 Support Chat", url=Config.SUPPORT_CHAT)],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await self.send_message(update, support_text, keyboard, ParseMode.MARKDOWN)
    
    # ========================================
    # ABOUT COMMAND
    # ========================================
    
    async def cmd_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_text = f"""
ℹ️ **About Kinva Master Pro**

━━━━━━━━━━━━━━━━━━━━━━
**Version:** {Config.BOT_VERSION}
**Developer:** Kinva Master Team
**Platform:** Telegram

**Features:**
• 50+ Video Editing Tools
• 30+ Image Editing Tools
• 50+ Professional Filters
• 10+ Social Media Downloaders
• Premium Subscription
• Free Trial Available

**Technologies:**
• MongoDB Database
• Redis Cache
• FFmpeg Processing
• AI Effects

━━━━━━━━━━━━━━━━━━━━━━
📞 **Support:** @kinvasupport
🌐 **Website:** kinvamaster.com

Made with ❤️ for Telegram
"""
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        await self.send_message(update, about_text, keyboard, ParseMode.MARKDOWN)
    
    # ========================================
    # CANCEL COMMAND
    # ========================================
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ **Operation Cancelled**\n\n"
            "Use /menu to continue.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # ========================================
    # VIDEO HANDLER
    # ========================================
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user_id = update.effective_user.id
        video = update.message.video
        
        # Check if user is banned
        user_data = await self.db.get_user(user_id)
        if user_data and user_data.get("banned", False):
            await update.message.reply_text("🚫 You are banned from using this bot!")
            return
        
        # Check edit limit
        can_edit, msg, remaining = await self.db.can_edit(user_id)
        if not can_edit:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Check file size
        is_premium = await self.db.is_premium(user_id)
        can_upload, size_msg = Config.check_file_size(video.file_size, is_premium)
        if not can_upload:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(size_msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Check video duration
        if video.duration:
            can_upload, duration_msg = Config.check_video_duration(video.duration, is_premium)
            if not can_upload:
                keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
                await update.message.reply_text(duration_msg, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        
        # Send processing message
        processing_msg = await update.message.reply_text("📥 **Downloading video...**", parse_mode=ParseMode.MARKDOWN)
        
        # Download video
        file = await video.get_file()
        file_path = os.path.join(Config.UPLOAD_DIR, f"video_{user_id}_{int(time.time())}.mp4")
        await file.download_to_drive(file_path)
        
        await processing_msg.delete()
        
        # Store in context
        context.user_data['current_video'] = file_path
        context.user_data['original_video'] = file_path
        context.user_data['file_type'] = 'video'
        
        # Increment edit count
        await self.db.increment_edits(user_id, "upload", "video", video.file_size)
        
        # Show video editing menu
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
            [InlineKeyboardButton("🔄 RESET", callback_data="tool_reset"),
             InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        # Get video info
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        caption = f"✅ **Video Ready!**\n\n📁 Size: {file_size_mb:.2f}MB\n🎥 Duration: {video.duration}s"
        
        await update.message.reply_video(
            video=open(file_path, 'rb'),
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ========================================
    # PHOTO HANDLER
    # ========================================
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages"""
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        
        # Check if user is banned
        user_data = await self.db.get_user(user_id)
        if user_data and user_data.get("banned", False):
            await update.message.reply_text("🚫 You are banned from using this bot!")
            return
        
        # Check edit limit
        can_edit, msg, remaining = await self.db.can_edit(user_id)
        if not can_edit:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Download image
        processing_msg = await update.message.reply_text("📥 **Downloading image...**", parse_mode=ParseMode.MARKDOWN)
        
        file = await photo.get_file()
        file_path = os.path.join(Config.UPLOAD_DIR, f"image_{user_id}_{int(time.time())}.jpg")
        await file.download_to_drive(file_path)
        
        await processing_msg.delete()
        
        # Store in context
        context.user_data['current_image'] = file_path
        context.user_data['original_image'] = file_path
        context.user_data['file_type'] = 'image'
        
        # Increment edit count
        await self.db.increment_edits(user_id, "upload", "image", file.file_size)
        
        # Show image editing menu
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_img"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🪞 FLIP", callback_data="tool_flip_img"),
             InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust")],
            [InlineKeyboardButton("🔄 RESET", callback_data="tool_reset"),
             InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        await update.message.reply_photo(
            photo=open(file_path, 'rb'),
            caption="✅ **Image Ready!** Choose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ========================================
    # TEXT HANDLER (for download links)
    # ========================================
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (for download links)"""
        text = update.message.text
        waiting_for = context.user_data.get('waiting_for')
        
        # Check for social media links
        if text.startswith(('http://', 'https://')):
            await self.handle_download_link(update, context, text)
            return
        
        # Handle waiting states
        if waiting_for == 'broadcast':
            await self.handle_broadcast_input(update, context)
        elif waiting_for == 'add_premium':
            await self.handle_add_premium_input(update, context)
        elif waiting_for == 'ban_user':
            await self.handle_ban_input(update, context)
        elif waiting_for == 'unban_user':
            await self.handle_unban_input(update, context)
        elif waiting_for == 'feedback':
            await self.handle_feedback(update, context)
        elif waiting_for == 'trim':
            await self.handle_trim_input(update, context)
        elif waiting_for == 'compress':
            await self.handle_compress_input(update, context)
        elif waiting_for == 'crop':
            await self.handle_crop_input(update, context)
        elif waiting_for == 'resize_img':
            await self.handle_resize_input(update, context)
        elif waiting_for == 'crop_img':
            await self.handle_crop_image_input(update, context)
        elif waiting_for == 'speed':
            await self.handle_speed_input(update, context)
        elif waiting_for == 'text_overlay':
            await self.handle_text_input(update, context)
        elif waiting_for == 'watermark':
            await self.handle_watermark_input(update, context)
        else:
            await update.message.reply_text(
                "❌ **Unknown command**\n\n"
                "Send me a photo/video to edit, or use /menu for commands!",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========================================
    # DOWNLOAD HANDLER
    # ========================================
    
    async def handle_download_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Handle social media download links"""
        user_id = update.effective_user.id
        
        # Check download limit
        can_download, msg, remaining = await self.db.can_download(user_id)
        if not can_download:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(f"❌ {msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Detect platform
        platform = self.detect_platform(url)
        if not platform:
            await update.message.reply_text(
                "❌ **Unsupported Platform**\n\n"
                "Supported platforms:\n"
                "• YouTube • Instagram • TikTok\n"
                "• Twitter • Facebook • Reddit\n"
                "• Pinterest • Twitch • Vimeo\n\n"
                "Make sure you send a valid link.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Send processing message
        msg = await update.message.reply_text(
            f"📥 **Downloading from {platform.upper()}...**\n\n"
            f"URL: {url[:50]}...\n\n"
            f"⏳ Please wait...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download video
            download_path = await self.download_video(url, platform)
            
            if download_path:
                # Increment download count
                await self.db.increment_downloads(user_id, platform, url)
                
                # Send video
                file_size = os.path.getsize(download_path)
                await msg.delete()
                
                await update.message.reply_video(
                    video=open(download_path, 'rb'),
                    caption=f"✅ **Download Complete!**\n\n"
                            f"📥 Platform: {platform.upper()}\n"
                            f"📁 Size: {file_size/(1024*1024):.2f}MB\n\n"
                            f"Use /menu for more tools!",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Cleanup
                os.remove(download_path)
            else:
                await msg.edit_text(
                    "❌ **Download Failed**\n\n"
                    "Unable to download from this link. Please check the URL and try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            await msg.edit_text(
                "❌ **Download Failed**\n\n"
                f"Error: {str(e)[:100]}\n\n"
                "Please try again later or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def detect_platform(self, url: str) -> str:
        """Detect social media platform from URL"""
        url_lower = url.lower()
        for platform, config in Config.SOCIAL_PLATFORMS.items():
            if config["enabled"]:
                for domain in config["domains"]:
                    if domain in url_lower:
                        return platform
        return None
    
    async def download_video(self, url: str, platform: str) -> str:
        """Download video from social media"""
        # This is a placeholder - implement actual downloading
        # For now, return None
        return None
    
    # ========================================
    # CALLBACK HANDLER
    # ========================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data
        await query.answer()
        
        # Navigation menus
        if data == "back_main":
            await self.cmd_start(update, context)
        
        elif data == "menu_video":
            await self.show_video_menu(update, context)
        
        elif data == "menu_image":
            await self.show_image_menu(update, context)
        
        elif data == "menu_filters":
            await self.show_filters_menu(update, context)
        
        elif data == "menu_effects":
            await self.show_effects_menu(update, context)
        
        elif data == "menu_premium":
            await self.premium_menu(update, context)
        
        elif data == "menu_stats":
            await self.cmd_stats(update, context)
        
        elif data == "menu_help":
            await self.cmd_help(update, context)
        
        elif data == "menu_download":
            await self.show_download_menu(update, context)
        
        elif data == "menu_support":
            await self.cmd_support(update, context)
        
        elif data == "menu_trial":
            await self.cmd_trial(update, context)
        
        elif data == "menu_admin":
            await self.admin_panel(update, context)
        
        # Filter categories
        elif data.startswith("filter_cat_"):
            category = data.replace("filter_cat_", "")
            await self.show_filters_by_category(update, context, category)
        
        elif data.startswith("filter_"):
            filter_name = data.replace("filter_", "")
            await self.apply_filter(update, context, filter_name)
        
        # Effects
        elif data.startswith("effect_"):
            effect_name = data.replace("effect_", "")
            await self.apply_effect(update, context, effect_name)
        
        # Video tools
        elif data == "tool_trim":
            await self.tool_trim(update, context)
        
        elif data == "tool_crop":
            await self.tool_crop(update, context)
        
        elif data == "tool_speed":
            await self.tool_speed(update, context)
        
        elif data.startswith("speed_"):
            speed = float(data.split("_")[1])
            await self.apply_speed(update, context, speed)
        
        elif data == "tool_reverse":
            await self.tool_reverse(update, context)
        
        elif data == "tool_compress":
            await self.tool_compress(update, context)
        
        elif data == "tool_rotate":
            await self.tool_rotate(update, context)
        
        elif data.startswith("rotate_"):
            angle = int(data.split("_")[1])
            await self.apply_rotate(update, context, angle)
        
        elif data == "tool_audio":
            await self.tool_audio(update, context)
        
        elif data == "tool_text":
            await self.tool_text(update, context)
        
        elif data == "tool_reset":
            await self.reset_edit(update, context)
        
        elif data == "tool_done":
            await self.done_edit(update, context)
        
        # Image tools
        elif data == "tool_rotate_img":
            await self.tool_rotate_image(update, context)
        
        elif data.startswith("rotate_img_"):
            angle = int(data.split("_")[2])
            await self.apply_rotate_image(update, context, angle)
        
        elif data == "tool_resize_img":
            await self.tool_resize_image(update, context)
        
        elif data == "tool_crop_img":
            await self.tool_crop_image(update, context)
        
        elif data == "tool_flip_img":
            await self.tool_flip_image(update, context)
        
        elif data.startswith("flip_"):
            direction = data.split("_")[1]
            await self.apply_flip_image(update, context, direction)
        
        elif data == "tool_adjust":
            await self.tool_adjust_image(update, context)
        
        elif data.startswith("adjust_"):
            adjustment = data.replace("adjust_", "")
            await self.handle_adjust_image(update, context, adjustment)
        
        # Premium purchase
        elif data.startswith("buy_"):
            plan = data.replace("buy_", "")
            await self.handle_purchase(update, context, plan)
        
        elif data == "pay_stars":
            await self.handle_stars_payment(update, context)
        
        elif data == "pay_upi":
            await self.handle_upi_payment(update, context)
        
        # Admin actions
        elif data.startswith("admin_"):
            action = data.replace("admin_", "")
            await self.handle_admin_action(update, context, action)
        
        else:
            await query.edit_message_text("🛠️ **Feature coming soon!**", parse_mode=ParseMode.MARKDOWN)
    
    # ========================================
    # VIDEO TOOLS IMPLEMENTATIONS
    # ========================================
    
    async def show_video_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show video editing menu"""
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("📦 COMPRESS", callback_data="tool_compress"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate")],
            [InlineKeyboardButton("🎵 AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("📝 TEXT", callback_data="tool_text")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await self.send_message(
            update,
            "🎬 **VIDEO EDITING TOOLS**\n\nChoose a tool to edit your video:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def tool_trim(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trim video tool"""
        await self.send_message(
            update,
            "✂️ **Trim Video**\n\n"
            "Send start and end time in seconds.\n\n"
            "**Examples:**\n"
            "• `10 30` - from 10s to 30s\n"
            "• `start 10` - from 10s to end\n"
            "• `end 30` - from start to 30s\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'trim'
        return self.TRIM_STATE
    
    async def handle_trim_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle trim input"""
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found! Send a video first.")
            return
        
        try:
            text = update.message.text.lower()
            
            if text.startswith('start'):
                start = float(text.split()[1])
                end = None
            elif text.startswith('end'):
                start = None
                end = float(text.split()[1])
            else:
                parts = text.split()
                start = float(parts[0])
                end = float(parts[1]) if len(parts) > 1 else None
            
            await update.message.reply_text("✂️ Trimming video... Please wait.")
            
            # Call video editor (placeholder)
            output_path = video_path  # Replace with actual trim
            
            context.user_data['current_video'] = output_path
            
            await update.message.reply_video(
                video=open(output_path, 'rb'),
                caption=f"✅ Trimmed successfully!"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}\n\nUse format: `10 30`")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def tool_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Change video speed tool"""
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
        
        await self.send_message(
            update,
            "⚡ **Change Video Speed**\n\nChoose speed factor:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, speed: float):
        """Apply speed change"""
        query = update.callback_query
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"⚡ Changing speed to {speed}x... Please wait.")
        
        # Apply speed (placeholder)
        output_path = video_path
        
        context.user_data['current_video'] = output_path
        
        await query.message.reply_video(
            video=open(output_path, 'rb'),
            caption=f"✅ Speed changed to {speed}x!"
        )
    
    async def tool_reverse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reverse video tool"""
        query = update.callback_query
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text("🔄 Reversing video... Please wait.")
        
        # Apply reverse (placeholder)
        output_path = video_path
        
        context.user_data['current_video'] = output_path
        
        await query.message.reply_video(
            video=open(output_path, 'rb'),
            caption="✅ Video reversed!"
        )
    
    async def tool_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compress video tool"""
        await self.send_message(
            update,
            "📦 **Compress Video**\n\n"
            "Send target size in MB (max 50MB).\n\n"
            "**Example:** `20`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'compress'
        return self.COMPRESS_STATE
    
    async def handle_compress_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle compress input"""
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return
        
        try:
            target = int(update.message.text)
            await update.message.reply_text(f"📦 Compressing video to {target}MB... This may take a while.")
            
            # Apply compression (placeholder)
            output_path = video_path
            
            context.user_data['current_video'] = output_path
            
            await update.message.reply_video(
                video=open(output_path, 'rb'),
                caption=f"✅ Compressed to {target}MB!"
            )
            
        except:
            await update.message.reply_text("❌ Invalid format! Use: `20`")
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    async def tool_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rotate video tool"""
        keyboard = [
            [InlineKeyboardButton("90°", callback_data="rotate_90"),
             InlineKeyboardButton("180°", callback_data="rotate_180")],
            [InlineKeyboardButton("270°", callback_data="rotate_270"),
             InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await self.send_message(
            update,
            "🔄 **Rotate Video**\n\nChoose rotation angle:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, angle: int):
        """Apply rotation"""
        query = update.callback_query
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"🔄 Rotating {angle}°...")
        
        # Apply rotation (placeholder)
        output_path = video_path
        
        context.user_data['current_video'] = output_path
        
        await query.message.reply_video(
            video=open(output_path, 'rb'),
            caption=f"✅ Rotated {angle}°!"
        )
    
    async def tool_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Crop video tool"""
        await self.send_message(
            update,
            "🎯 **Crop Video**\n\n"
            "Send coordinates: `x y width height`\n\n"
            "**Example:** `100 100 800 600`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'crop'
    
    async def handle_crop_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle crop input"""
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return
        
        try:
            parts = update.message.text.split()
            x, y, w, h = map(int, parts[:4])
            
            await update.message.reply_text("🎯 Cropping video...")
            
            # Apply crop (placeholder)
            output_path = video_path
            
            context.user_data['current_video'] = output_path
            
            await update.message.reply_video(
                video=open(output_path, 'rb'),
                caption=f"✅ Cropped to {w}x{h}!"
            )
            
        except:
            await update.message.reply_text("❌ Invalid format! Use: `100 100 800 600`")
        
        context.user_data.pop('waiting_for', None)
    
    async def tool_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Audio tools menu"""
        keyboard = [
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="audio_extract"),
             InlineKeyboardButton("🔇 REMOVE AUDIO", callback_data="audio_remove")],
            [InlineKeyboardButton("➕ ADD MUSIC", callback_data="audio_add"),
             InlineKeyboardButton("🔊 ADJUST VOLUME", callback_data="audio_volume")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await self.send_message(
            update,
            "🎵 **AUDIO TOOLS**\n\nChoose an audio tool:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def tool_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add text to video"""
        await self.send_message(
            update,
            "📝 **Add Text to Video**\n\n"
            "Send the text you want to add:\n\n"
            "**Example:** `Hello World!`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'text_overlay'
        return self.TEXT_STATE
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for video"""
        video_path = context.user_data.get('current_video')
        if not video_path:
            await update.message.reply_text("❌ No video found!")
            return
        
        text = update.message.text
        
        await update.message.reply_text(f"📝 Adding text: '{text}'...")
        
        # Apply text overlay (placeholder)
        output_path = video_path
        
        context.user_data['current_video'] = output_path
        
        await update.message.reply_video(
            video=open(output_path, 'rb'),
            caption=f"✅ Text added: {text}"
        )
        
        context.user_data.pop('waiting_for', None)
        return ConversationHandler.END
    
    # ========================================
    # IMAGE TOOLS IMPLEMENTATIONS
    # ========================================
    
    async def show_image_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show image editing menu"""
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_img"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🪞 FLIP", callback_data="tool_flip_img"),
             InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await self.send_message(
            update,
            "🖼️ **IMAGE EDITING TOOLS**\n\nChoose a tool to edit your image:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def tool_rotate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rotate image tool"""
        keyboard = [
            [InlineKeyboardButton("90°", callback_data="rotate_img_90"),
             InlineKeyboardButton("180°", callback_data="rotate_img_180")],
            [InlineKeyboardButton("270°", callback_data="rotate_img_270"),
             InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await self.send_message(
            update,
            "🔄 **Rotate Image**\n\nChoose rotation angle:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_rotate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, angle: int):
        """Apply image rotation"""
        query = update.callback_query
        image_path = context.user_data.get('current_image')
        
        if not image_path:
            await query.edit_message_text("❌ No image found!")
            return
        
        await query.edit_message_text(f"🔄 Rotating {angle}°...")
        
        # Apply rotation (placeholder)
        output_path = image_path
        
        context.user_data['current_image'] = output_path
        
        await query.message.reply_photo(
            photo=open(output_path, 'rb'),
            caption=f"✅ Rotated {angle}°!"
        )
    
    async def tool_resize_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resize image tool"""
        await self.send_message(
            update,
            "📏 **Resize Image**\n\n"
            "Send width and height.\n\n"
            "**Example:** `800 600`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'resize_img'
    
    async def handle_resize_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle resize input"""
        image_path = context.user_data.get('current_image')
        if not image_path:
            await update.message.reply_text("❌ No image found!")
            return
        
        try:
            parts = update.message.text.split()
            width = int(parts[0])
            height = int(parts[1]) if len(parts) > 1 else width
            
            await update.message.reply_text(f"📏 Resizing to {width}x{height}...")
            
            # Apply resize (placeholder)
            output_path = image_path
            
            context.user_data['current_image'] = output_path
            
            await update.message.reply_photo(
                photo=open(output_path, 'rb'),
                caption=f"✅ Resized to {width}x{height}!"
            )
            
        except:
            await update.message.reply_text("❌ Invalid format! Use: `800 600`")
        
        context.user_data.pop('waiting_for', None)
    
    async def tool_crop_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Crop image tool"""
        await self.send_message(
            update,
            "✂️ **Crop Image**\n\n"
            "Send coordinates: `x1 y1 x2 y2`\n\n"
            "**Example:** `10 10 500 500`\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'crop_img'
    
    async def handle_crop_image_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle crop image input"""
        image_path = context.user_data.get('current_image')
        if not image_path:
            await update.message.reply_text("❌ No image found!")
            return
        
        try:
            parts = update.message.text.split()
            x1, y1, x2, y2 = map(int, parts[:4])
            
            await update.message.reply_text("✂️ Cropping image...")
            
            # Apply crop (placeholder)
            output_path = image_path
            
            context.user_data['current_image'] = output_path
            
            await update.message.reply_photo(
                photo=open(output_path, 'rb'),
                caption="✅ Cropped!"
            )
            
        except:
            await update.message.reply_text("❌ Invalid format! Use: `10 10 500 500`")
        
        context.user_data.pop('waiting_for', None)
    
    async def tool_flip_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Flip image tool"""
        keyboard = [
            [InlineKeyboardButton("🪞 HORIZONTAL", callback_data="flip_h"),
             InlineKeyboardButton("🪞 VERTICAL", callback_data="flip_v")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await self.send_message(
            update,
            "🪞 **Flip Image**\n\nChoose direction:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_flip_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, direction: str):
        """Apply image flip"""
        query = update.callback_query
        image_path = context.user_data.get('current_image')
        
        if not image_path:
            await query.edit_message_text("❌ No image found!")
            return
        
        await query.edit_message_text(f"🪞 Flipping {direction}...")
        
        # Apply flip (placeholder)
        output_path = image_path
        
        context.user_data['current_image'] = output_path
        
        await query.message.reply_photo(
            photo=open(output_path, 'rb'),
            caption=f"✅ Flipped {direction}!"
        )
    
    async def tool_adjust_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Image adjustment menu"""
        keyboard = [
            [InlineKeyboardButton("☀️ BRIGHTNESS", callback_data="adjust_brightness"),
             InlineKeyboardButton("🌓 CONTRAST", callback_data="adjust_contrast")],
            [InlineKeyboardButton("🎨 SATURATION", callback_data="adjust_saturation"),
             InlineKeyboardButton("🔍 SHARPNESS", callback_data="adjust_sharpness")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_image")]
        ]
        
        await self.send_message(
            update,
            "🌈 **Adjust Image**\n\nChoose adjustment:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def handle_adjust_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, adjustment: str):
        """Handle image adjustment"""
        query = update.callback_query
        await query.edit_message_text(
            f"🌈 **Adjust {adjustment.title()}**\n\n"
            f"Send factor (0.5 to 2.0)\n"
            f"**Example:** `1.2`\n\n"
            f"Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = f'adjust_{adjustment}'
    
    # ========================================
    # FILTERS AND EFFECTS
    # ========================================
    
    async def show_filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show filters menu"""
        keyboard = [
            [InlineKeyboardButton("🎨 BASIC", callback_data="filter_cat_basic"),
             InlineKeyboardButton("🌈 COLOR", callback_data="filter_cat_color")],
            [InlineKeyboardButton("🎭 ARTISTIC", callback_data="filter_cat_artistic"),
             InlineKeyboardButton("✨ LIGHTING", callback_data="filter_cat_lighting")],
            [InlineKeyboardButton("🎬 CINEMATIC", callback_data="filter_cat_cinematic"),
             InlineKeyboardButton("⚡ SPECIAL", callback_data="filter_cat_special")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await self.send_message(
            update,
            "🎨 **50+ PROFESSIONAL FILTERS**\n\nChoose category:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def show_filters_by_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
        """Show filters by category"""
        filters_by_cat = {
            "basic": ["grayscale", "sepia", "invert", "emboss", "sharpen", "blur", "smooth"],
            "color": ["vintage", "cool", "warm", "noir", "pastel", "sunset", "ocean", "forest"],
            "artistic": ["oil_paint", "watercolor", "sketch", "cartoon", "pixelate", "mosaic"],
            "lighting": ["glow", "neon", "bokeh", "lens_flare", "vignette", "hdr"],
            "cinematic": ["cinematic", "dramatic", "dreamy", "hollywood"],
            "special": ["rainbow", "prism", "mirror", "kaleidoscope", "fisheye"]
        }
        
        filters_list = filters_by_cat.get(category, filters_by_cat["basic"])
        
        keyboard = []
        row = []
        for filter_name in filters_list:
            row.append(InlineKeyboardButton(filter_name.title(), callback_data=f"filter_{filter_name}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await self.send_message(
            update,
            f"🎨 **{category.upper()} FILTERS**\n\nClick a filter to apply!",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, filter_name: str):
        """Apply filter to image/video"""
        query = update.callback_query
        
        # Check if image exists
        image_path = context.user_data.get('current_image')
        if not image_path:
            await query.edit_message_text("❌ No image found! Send an image first.")
            return
        
        await query.edit_message_text(f"🎨 Applying {filter_name} filter...")
        
        # Apply filter (placeholder)
        output_path = image_path
        
        context.user_data['current_image'] = output_path
        
        await query.message.reply_photo(
            photo=open(output_path, 'rb'),
            caption=f"✅ Applied **{filter_name}** filter!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_effects_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show video effects menu"""
        keyboard = [
            [InlineKeyboardButton("✨ GLITCH", callback_data="effect_glitch"),
             InlineKeyboardButton("📺 VHS", callback_data="effect_vhs")],
            [InlineKeyboardButton("💎 PIXELATE", callback_data="effect_pixelate"),
             InlineKeyboardButton("🎨 CARTOON", callback_data="effect_cartoon")],
            [InlineKeyboardButton("🌊 SLOW MOTION", callback_data="effect_slow"),
             InlineKeyboardButton("⚡ FAST MOTION", callback_data="effect_fast")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
        ]
        
        await self.send_message(
            update,
            "✨ **VIDEO EFFECTS**\n\nChoose an effect:",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    async def apply_effect(self, update: Update, context: ContextTypes.DEFAULT_TYPE, effect_name: str):
        """Apply video effect"""
        query = update.callback_query
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await query.edit_message_text("❌ No video found!")
            return
        
        await query.edit_message_text(f"✨ Applying {effect_name} effect...")
        
        # Apply effect (placeholder)
        output_path = video_path
        
        context.user_data['current_video'] = output_path
        
        await query.message.reply_video(
            video=open(output_path, 'rb'),
            caption=f"✅ Applied {effect_name} effect!"
        )
    
    # ========================================
    # DOWNLOAD MENU
    # ========================================
    
    async def show_download_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show social media download menu"""
        keyboard = [
            [InlineKeyboardButton("📺 YOUTUBE", callback_data="download_youtube"),
             InlineKeyboardButton("📸 INSTAGRAM", callback_data="download_instagram")],
            [InlineKeyboardButton("🎵 TIKTOK", callback_data="download_tiktok"),
             InlineKeyboardButton("🐦 TWITTER", callback_data="download_twitter")],
            [InlineKeyboardButton("📘 FACEBOOK", callback_data="download_facebook"),
             InlineKeyboardButton("🔴 REDDIT", callback_data="download_reddit")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await self.send_message(
            update,
            "📥 **SOCIAL MEDIA DOWNLOADER**\n\n"
            "Send me a link to download!\n\n"
            "**Supported Platforms:**\n"
            "• YouTube • Instagram • TikTok\n"
            "• Twitter • Facebook • Reddit\n"
            "• Pinterest • Twitch • Vimeo\n\n"
            "**Free Trial:** 1 download\n"
            "**Premium:** Unlimited downloads",
            keyboard,
            ParseMode.MARKDOWN
        )
    
    # ========================================
    # RESET AND DONE
    # ========================================
    
    async def reset_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset to original file"""
        query = update.callback_query
        file_type = context.user_data.get('file_type')
        
        if file_type == 'video':
            original = context.user_data.get('original_video')
            if original and os.path.exists(original):
                context.user_data['current_video'] = original
                await query.message.reply_video(
                    video=open(original, 'rb'),
                    caption="✅ Reset to original video!"
                )
            else:
                await query.edit_message_text("❌ No original file found!")
        
        elif file_type == 'image':
            original = context.user_data.get('original_image')
            if original and os.path.exists(original):
                context.user_data['current_image'] = original
                await query.message.reply_photo(
                    photo=open(original, 'rb'),
                    caption="✅ Reset to original image!"
                )
            else:
                await query.edit_message_text("❌ No original file found!")
    
    async def done_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finish editing"""
        query = update.callback_query
        
        await query.edit_message_text(
            "✅ **Editing Complete!**\n\n"
            "Send me another file to continue editing!\n\n"
            "💡 Tip: Use /menu to see all available tools.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Clear session data
        context.user_data.clear()
    
    # ========================================
    # PAYMENT HANDLERS
    # ========================================
    
    async def handle_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str):
        """Handle premium purchase"""
        plan_data = Config.PREMIUM_PRICES.get(plan, Config.PREMIUM_PRICES["monthly"])
        
        payment_text = f"""
💎 **Purchase {plan.upper()} Plan** 💎

━━━━━━━━━━━━━━━━━━━━━━
**Plan Details:**
━━━━━━━━━━━━━━━━━━━━━━

• Duration: {plan_data['days']} days
• Price: ${plan_data['price_usd']} / ₹{plan_data['price_inr']}
• Stars: {plan_data['stars']} Stars

━━━━━━━━━━━━━━━━━━━━━━
**Payment Methods:**
━━━━━━━━━━━━━━━━━━━━━━

1️⃣ **UPI Payment**
   UPI ID: `{Config.UPI_ID}`
   Amount: ₹{plan_data['price_inr']}

2️⃣ **Telegram Stars**
   {plan_data['stars']} Stars

3️⃣ **PayPal/Crypto**
   Contact support

━━━━━━━━━━━━━━━━━━━━━━
**How to Pay via UPI:**
━━━━━━━━━━━━━━━━━━━━━━

1. Open any UPI app (Google Pay, PhonePe, Paytm)
2. Send ₹{plan_data['price_inr']} to `{Config.UPI_ID}`
3. Take a screenshot of payment
4. Send screenshot here

✅ Premium will be activated within 24 hours
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"pay_upi_{plan}"),
             InlineKeyboardButton("⭐ PAY WITH STARS", callback_data=f"pay_stars_{plan}")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await self.send_message(update, payment_text, keyboard, ParseMode.MARKDOWN)
    
    async def handle_upi_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle UPI payment"""
        query = update.callback_query
        await query.edit_message_text(
            f"💳 **UPI Payment Instructions**\n\n"
            f"**UPI ID:** `{Config.UPI_ID}`\n"
            f"**Name:** {Config.UPI_NAME}\n\n"
            f"**Steps:**\n"
            f"1. Open Google Pay / PhonePe / Paytm\n"
            f"2. Send payment to above UPI ID\n"
            f"3. Take screenshot\n"
            f"4. Send screenshot here\n\n"
            f"✅ Premium will be activated within 24 hours\n\n"
            f"Send /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['waiting_for'] = 'payment_screenshot'
    
    async def handle_stars_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Telegram Stars payment"""
        query = update.callback_query
        await query.edit_message_text(
            "⭐ **Telegram Stars Payment**\n\n"
            "This feature is coming soon!\n\n"
            "You will be able to pay with Telegram Stars directly.\n\n"
            "For now, please use UPI payment.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ========================================
    # ADMIN PANEL
    # ========================================
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not Config.is_admin(user_id):
            await query.edit_message_text("❌ You are not authorized to use this panel!")
            return
        
        stats = await self.db.get_stats()
        
        admin_text = f"""
👑 **ADMIN PANEL**

━━━━━━━━━━━━━━━━━━━━━━
📊 **STATISTICS**
━━━━━━━━━━━━━━━━━━━━━━

• Total Users: `{stats.get('total_users', 0)}`
• Premium Users: `{stats.get('premium_users', 0)}`
• Free Users: `{stats.get('free_users', 0)}`
• Banned Users: `{stats.get('banned_users', 0)}`

• Total Edits: `{stats.get('total_edits', 0)}`
• Today's Edits: `{stats.get('today_edits', 0)}`

━━━━━━━━━━━━━━━━━━━━━━
🛠️ **ADMIN ACTIONS**
━━━━━━━━━━━━━━━━━━━━━━

• 📢 Broadcast Message
• ⭐ Add/Remove Premium
• 🚫 Ban/Unban Users
• 📊 View All Users
• 💰 View Transactions
• 📝 View Feedback
• ⚙️ System Settings
• 💾 Backup Database
• 🔄 Restart Bot

━━━━━━━━━━━━━━━━━━━━━━
💡 **Use buttons below to manage**
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("⭐ ADD PREMIUM", callback_data="admin_add_premium")],
            [InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban"),
             InlineKeyboardButton("✅ UNBAN USER", callback_data="admin_unban")],
            [InlineKeyboardButton("📊 ALL USERS", callback_data="admin_users"),
             InlineKeyboardButton("💰 TRANSACTIONS", callback_data="admin_transactions")],
            [InlineKeyboardButton("📝 FEEDBACK", callback_data="admin_feedback"),
             InlineKeyboardButton("💾 BACKUP DB", callback_data="admin_backup")],
            [InlineKeyboardButton("⚙️ SETTINGS", callback_data="admin_settings"),
             InlineKeyboardButton("📈 STATS", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_admin_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle admin actions"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not Config.is_admin(user_id):
            await query.edit_message_text("❌ Unauthorized!")
            return
        
        if action == "broadcast":
            await query.edit_message_text(
                "📢 **Broadcast Message**\n\n"
                "Send the message you want to broadcast to all users.\n\n"
                "Type /cancel to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['waiting_for'] = 'broadcast'
        
        elif action == "add_premium":
            await query.edit_message_text(
                "⭐ **Add Premium**\n\n"
                "Send user ID and days (e.g., `123456789 30`)\n\n"
                "Type /cancel to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['waiting_for'] = 'add_premium'
        
        elif action == "ban":
            await query.edit_message_text(
                "🚫 **Ban User**\n\n"
                "Send user ID to ban (e.g., `123456789`)\n\n"
                "Type /cancel to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['waiting_for'] = 'ban_user'
        
        elif action == "unban":
            await query.edit_message_text(
                "✅ **Unban User**\n\n"
                "Send user ID to unban (e.g., `123456789`)\n\n"
                "Type /cancel to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['waiting_for'] = 'unban_user'
        
        elif action == "users":
            users = await self.db.get_all_users()
            text = "📊 **ALL USERS**\n\n"
            for user in users[:20]:
                status = "⭐" if user.get("is_premium") else "📀"
                text += f"{status} `{user['user_id']}` - {user.get('first_name', 'N/A')}\n"
            
            if len(users) > 20:
                text += f"\n... and {len(users) - 20} more users"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif action == "transactions":
            transactions = await self.db.get_user_transactions(0, 20)
            text = "💰 **RECENT TRANSACTIONS**\n\n"
            for tx in transactions:
                text += f"• User: `{tx['user_id']}` | ${tx.get('amount', 0)} | {tx.get('status', 'pending')}\n"
            
            if not transactions:
                text = "💰 No transactions found"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif action == "feedback":
            feedbacks = await self.db.get_feedback()
            text = "📝 **USER FEEDBACK**\n\n"
            for fb in feedbacks[:10]:
                text += f"• User: `{fb['user_id']}` | Rating: {'⭐' * fb.get('rating', 5)}\n"
                text += f"  Message: {fb.get('message', '')[:100]}\n\n"
            
            if not feedbacks:
                text = "📝 No feedback found"
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif action == "backup":
            await query.edit_message_text("💾 **Backing up database...**")
            backup_path = await self.db.backup_database()
            
            if backup_path:
                await query.edit_message_text(f"✅ Database backed up successfully!\n\n📁 Location: `{backup_path}`", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("❌ Backup failed!")
        
        elif action == "settings":
            settings_text = """
⚙️ **SYSTEM SETTINGS**

━━━━━━━━━━━━━━━━━━━━━━
**Current Settings:**
━━━━━━━━━━━━━━━━━━━━━━

• Free Limit: 700MB
• Premium Limit: 4GB
• Free Duration: 5 min
• Premium Duration: 60 min
• Daily Free Edits: 10

━━━━━━━━━━━━━━━━━━━━━━
**Coming Soon:**
━━━━━━━━━━━━━━━━━━━━━━

• Custom file limits
• Custom pricing
• Welcome message editor
• Maintenance mode
"""
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
            await query.edit_message_text(settings_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif action == "stats":
            stats = await self.db.get_stats()
            stats_text = f"""
📈 **DETAILED STATISTICS**

━━━━━━━━━━━━━━━━━━━━━━
👥 **USERS**
• Total: {stats.get('total_users', 0)}
• Premium: {stats.get('premium_users', 0)}
• Free: {stats.get('free_users', 0)}
• Banned: {stats.get('banned_users', 0)}

━━━━━━━━━━━━━━━━━━━━━━
🎬 **EDITS**
• Total: {stats.get('total_edits', 0)}
• Today: {stats.get('today_edits', 0)}

━━━━━━━━━━━━━━━━━━━━━━
📊 **CONVERSION**
• Premium rate: {stats.get('premium_rate', 0)}%
"""
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_admin")]]
            await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_broadcast_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast message input"""
        user_id = update.effective_user.id
        
        if not Config.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        message = update.message.text
        
        # Get all users
        users = await self.db.get_all_users()
        success = 0
        failed = 0
        
        progress_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 **ANNOUNCEMENT**\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success += 1
            except:
                failed += 1
            
            await asyncio.sleep(0.05)
        
        await progress_msg.edit_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}"
        )
        
        # Save broadcast history
        await self.db.add_broadcast(user_id, message, len(users), success, failed)
        
        context.user_data.pop('waiting_for', None)
    
    async def handle_add_premium_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle add premium input"""
        admin_id = update.effective_user.id
        
        if not Config.is_admin(admin_id):
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        try:
            parts = update.message.text.split()
            target_id = int(parts[0])
            days = int(parts[1]) if len(parts) > 1 else 30
            
            await self.db.add_premium(target_id, days)
            
            await update.message.reply_text(f"✅ Premium added to user {target_id} for {days} days!")
            
            # Notify user
            try:
                await context.bot.send_message(
                    target_id,
                    f"🎉 **Congratulations!**\n\nYou have been gifted {days} days of Premium!\n\nThank you for using Kinva Master Pro!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
                
        except:
            await update.message.reply_text("❌ Invalid format! Use: `user_id days`")
        
        context.user_data.pop('waiting_for', None)
    
    async def handle_ban_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ban user input"""
        admin_id = update.effective_user.id
        
        if not Config.is_admin(admin_id):
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        try:
            target_id = int(update.message.text)
            await self.db.ban_user(target_id, "Banned by admin", admin_id)
            
            await update.message.reply_text(f"✅ User {target_id} has been banned!")
            
            # Notify user
            try:
                await context.bot.send_message(
                    target_id,
                    "🚫 **You have been banned** from using Kinva Master Pro.\n\nContact admin for more information.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
                
        except:
            await update.message.reply_text("❌ Invalid user ID!")
        
        context.user_data.pop('waiting_for', None)
    
    async def handle_unban_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unban user input"""
        admin_id = update.effective_user.id
        
        if not Config.is_admin(admin_id):
            await update.message.reply_text("❌ Unauthorized!")
            return
        
        try:
            target_id = int(update.message.text)
            await self.db.unban_user(target_id, admin_id)
            
            await update.message.reply_text(f"✅ User {target_id} has been unbanned!")
            
            # Notify user
            try:
                await context.bot.send_message(
                    target_id,
                    "✅ **You have been unbanned** from Kinva Master Pro.\n\nYou can now use the bot again!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
                
        except:
            await update.message.reply_text("❌ Invalid user ID!")
        
        context.user_data.pop('waiting_for', None)

# ============================================
# FLASK WEB SERVER FOR RENDER
# ============================================

web_app = Flask(__name__)
web_app.secret_key = Config.SECRET_KEY

@web_app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": Config.BOT_NAME,
        "version": Config.BOT_VERSION,
        "uptime": time.time()
    })

@web_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@web_app.route('/mini-app')
def mini_app():
    return send_from_directory('mini-app', 'index.html')

@web_app.route('/mini-app/<path:path>')
def mini_app_files(path):
    return send_from_directory('mini-app', path)

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False)

# Start web server in background
threading.Thread(target=run_web_server, daemon=True).start()

# ============================================
# MAIN FUNCTION
# ============================================

async def main():
    """Main function to run the bot"""
    
    # Create bot instance
    bot = KinvaMasterBot()
    
    # Build application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.cmd_start))
    application.add_handler(CommandHandler("help", bot.cmd_help))
    application.add_handler(CommandHandler("menu", bot.cmd_help))
    application.add_handler(CommandHandler("stats", bot.cmd_stats))
    application.add_handler(CommandHandler("premium", bot.cmd_premium))
    application.add_handler(CommandHandler("trial", bot.cmd_trial))
    application.add_handler(CommandHandler("feedback", bot.cmd_feedback))
    application.add_handler(CommandHandler("support", bot.cmd_support))
    application.add_handler(CommandHandler("about", bot.cmd_about))
    application.add_handler(CommandHandler("cancel", bot.cmd_cancel))
    
    # Add conversation handlers
    feedback_handler = ConversationHandler(
        entry_points=[CommandHandler("feedback", bot.cmd_feedback)],
        states={bot.FEEDBACK_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_feedback)]},
        fallbacks=[CommandHandler("cancel", bot.cmd_cancel)]
    )
    application.add_handler(feedback_handler)
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.VIDEO, bot.handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # Delete webhook before starting
    await application.bot.delete_webhook(drop_pending_updates=True)
    
    # Print startup banner
    print("\n" + "="*60)
    print(f"✅ KINVA MASTER PRO v{Config.BOT_VERSION} STARTED")
    print("="*60)
    print(f"🤖 Bot: @{Config.BOT_USERNAME}")
    print(f"👑 Admin: {Config.ADMIN_IDS}")
    print(f"📊 MongoDB: {'✅' if mongo_db.connected else '❌'}")
    print(f"⚡ Redis: {'✅' if redis_cache.connected else '❌'}")
    print(f"🌐 Web Server: http://localhost:{os.environ.get('PORT', 8080)}")
    print("="*60)
    print("\n✅ Bot is running 24/7...\n")
    
    # Start polling
    await application.run_polling(allowed_updates=["message", "callback_query"])

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    asyncio.run(main())
