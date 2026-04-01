# ============================================
# KINVA MASTER PRO - COMPLETE EDITING BOT
# ============================================
# PART 1: IMPORTS AND CONFIGURATION
# ============================================

import os
import sys
import logging
import asyncio
import tempfile
import shutil
import json
import hashlib
import secrets
import string
import random
import time
import threading
import sqlite3
import hmac
import base64
import uuid
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
from functools import wraps
from collections import defaultdict
import traceback
import re
import glob

# Image Processing
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps, ImageChops
import numpy as np
import cv2
from scipy import ndimage
from skimage import exposure, filters, restoration

# Video Processing - MOVIEPY 2.2.1 (CORRECTED)
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
    concatenate_videoclips, ImageClip, ColorClip, clips_array,
    CompositeAudioClip, concatenate_audioclips
)
# Note: All effects are now METHODS on clip objects (e.g., clip.fadein(), clip.rotate())
# No separate effect imports needed!

# Audio Processing
from pydub import AudioSegment, effects, generators
from pydub.effects import normalize, low_pass_filter, high_pass_filter
import librosa
import soundfile as sf

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler, PreCheckoutQueryHandler
)
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder


# Web Framework
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Downloaders
import yt_dlp
import instaloader
import requests
from bs4 import BeautifulSoup

# Payment
import stripe
import qrcode
from io import BytesIO

# ============================================
# CONFIGURATION
# ============================================
class Config:
    """Master Configuration Class"""
    
    # Bot Configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8791110410:AAGDvRjSJ4OvMgcYG8pOL7aCZXhkkHopEig")
    ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "8525952693").split(",")]
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://KinvaMaster-1.onrender.com")
    PORT = int(os.environ.get("PORT", 8080))
    
    # Admin Panel
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    
    # Payment Configuration
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    UPI_ID = os.environ.get("UPI_ID", "kinvamaster@okhdfcbank")
    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    
    # Star Payment (Telegram Stars)
    STAR_PRICE_MONTHLY = 100  # Telegram Stars
    STAR_PRICE_YEARLY = 1000
    
    # Premium Pricing
    PREMIUM_PRICE_USD = 9.99
    PREMIUM_PRICE_INR = 499
    PREMIUM_PRICE_STARS = 100
    
    # Watermark Configuration
    DEFAULT_WATERMARK = "Kinva Master Pro"
    WATERMARK_POSITIONS = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    
    # Storage
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    CACHE_DIR = "cache"
    DATABASE_FILE = "kinva_master.db"
    
    # Limits
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_VIDEO_DURATION = 600  # 10 minutes
    MAX_EDIT_PER_DAY_FREE = 10
    MAX_EDIT_PER_DAY_PREMIUM = 1000
    
    # Features
    ENABLE_WATERMARK = True
    ENABLE_PREMIUM = True
    ENABLE_PAYMENTS = True
    ENABLE_WEB_APP = True
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        for dir_path in [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    
    @classmethod
    def get_version(cls):
        return "3.0.0"

Config.setup_directories()

# ============================================
# DATABASE MANAGEMENT
# ============================================

class Database:
    """Advanced Database Management with SQLite"""
    
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
    
    def init_tables(self):
        """Initialize all database tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                is_premium INTEGER DEFAULT 0,
                premium_expiry TEXT,
                premium_type TEXT DEFAULT 'monthly',
                edits_count INTEGER DEFAULT 0,
                daily_edits INTEGER DEFAULT 0,
                last_edit_date TEXT,
                balance REAL DEFAULT 0,
                stars_balance INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Edit history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                edit_type TEXT,
                tool_used TEXT,
                input_size INTEGER,
                output_size INTEGER,
                processing_time REAL,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                stars_amount INTEGER,
                payment_method TEXT,
                transaction_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                payment_data TEXT,
                created_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                data TEXT,
                preview_url TEXT,
                created_by INTEGER,
                is_public INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                data TEXT,
                thumbnail TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback TEXT,
                rating INTEGER,
                category TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                user_id INTEGER,
                data TEXT,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
        
        # Initialize default settings
        self.init_default_settings()
    
    def init_default_settings(self):
        """Initialize default settings"""
        defaults = {
            'bot_name': 'Kinva Master Pro',
            'bot_version': Config.get_version(),
            'welcome_message': 'Welcome to Kinva Master Pro!',
            'maintenance_mode': 'false',
            'referral_bonus': '10',
            'daily_free_edits': '10',
            'min_withdrawal': '10',
            'support_chat': 'https://t.me/kinvasupport'
        }
        
        for key, value in defaults.items():
            self.set_setting(key, value)
    
    def get_user(self, user_id: int) -> dict:
        """Get or create user"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return None
        return dict(user)
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referrer_id: int = 0):
        """Create new user"""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (id, username, first_name, last_name, created_at, updated_at, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, now, now, referrer_id))
        
        # Add referral bonus if applicable
        if referrer_id > 0:
            cursor.execute('''
                UPDATE users SET referral_count = referral_count + 1, balance = balance + 5
                WHERE id = ?
            ''', (referrer_id,))
        
        self.conn.commit()
        return self.get_user(user_id)
    
    def update_user(self, user_id: int, **kwargs):
        """Update user data"""
        cursor = self.conn.cursor()
        fields = []
        values = []
        
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        if fields:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
            cursor.execute(query, values + [datetime.now().isoformat()])
            self.conn.commit()
    
    def is_premium(self, user_id: int) -> bool:
        """Check if user has premium access"""
        user = self.get_user(user_id)
        if user and user['is_premium']:
            if user['premium_expiry']:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                if datetime.now() > expiry:
                    self.update_user(user_id, is_premium=0, premium_expiry=None)
                    return False
            return True
        return False
    
    def add_premium(self, user_id: int, days: int = 30, premium_type: str = "monthly"):
        """Add premium subscription"""
        user = self.get_user(user_id)
        if user['premium_expiry']:
            expiry = datetime.fromisoformat(user['premium_expiry'])
            new_expiry = expiry + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        self.update_user(user_id, is_premium=1, premium_expiry=new_expiry.isoformat(), premium_type=premium_type)
    
    def increment_edits(self, user_id: int):
        """Increment edit count"""
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        
        if user['last_edit_date'] != today:
            self.update_user(user_id, daily_edits=1, last_edit_date=today)
        else:
            self.update_user(user_id, daily_edits=user['daily_edits'] + 1)
        
        self.update_user(user_id, edits_count=user['edits_count'] + 1)
    
    def can_edit(self, user_id: int) -> bool:
        """Check if user can perform edit"""
        if self.is_premium(user_id):
            return True
        
        user = self.get_user(user_id)
        today = datetime.now().date().isoformat()
        
        if user['last_edit_date'] != today:
            return True
        
        return user['daily_edits'] < Config.MAX_EDIT_PER_DAY_FREE
    
    def add_transaction(self, user_id: int, amount: float, payment_method: str, transaction_id: str, stars_amount: int = None):
        """Add transaction record"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, stars_amount, payment_method, transaction_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, stars_amount, payment_method, transaction_id, 'pending', now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_transaction(self, transaction_id: str):
        """Complete transaction and activate premium"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE transactions SET status = 'completed', completed_at = ?
            WHERE transaction_id = ?
        ''', (datetime.now().isoformat(), transaction_id))
        
        # Get transaction details
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        tx = cursor.fetchone()
        
        if tx:
            # Add premium for 30 days
            self.add_premium(tx['user_id'], 30)
            
            # Add stars if applicable
            if tx['stars_amount']:
                self.update_user(tx['user_id'], stars_balance=tx['stars_amount'])
        
        self.conn.commit()
    
    def add_feedback(self, user_id: int, feedback: str, rating: int, category: str = "general"):
        """Add user feedback"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feedback (user_id, feedback, rating, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, feedback, rating, category, now))
        
        self.conn.commit()
    
    def get_stats(self) -> dict:
        """Get overall statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(edits_count) FROM users")
        total_edits = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM edit_history WHERE date(created_at) = date('now')")
        today_edits = cursor.fetchone()[0]
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "total_edits": total_edits,
            "today_edits": today_edits,
            "premium_percent": round((premium_users / total_users * 100), 1) if total_users > 0 else 0
        }
    
    def save_project(self, project_id: str, user_id: int, name: str, data: dict):
        """Save user project"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO projects (id, user_id, name, data, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM projects WHERE id = ?), ?))
        ''', (project_id, user_id, name, json.dumps(data), now, project_id, now))
        
        self.conn.commit()
    
    def get_project(self, project_id: str, user_id: int) -> dict:
        """Get user project"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        project = cursor.fetchone()
        return dict(project) if project else None
    
    def set_setting(self, key: str, value: str):
        """Set system setting"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Get system setting"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else default
    
    def add_analytics(self, event_type: str, user_id: int, data: dict):
        """Add analytics event"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO analytics (event_type, user_id, data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (event_type, user_id, json.dumps(data), now))
        
        self.conn.commit()

db = Database()

# ============================================
# PART 2: 50+ FILTERS AND EFFECTS
# ============================================

class Filters50:
    """50+ Professional Filters and Effects"""
    
    def __init__(self):
        self.filter_list = []
        self.init_filters()
    
    def init_filters(self):
        """Initialize all filters"""
        self.filters = {
            # Basic Filters (1-10)
            "grayscale": self.grayscale,
            "sepia": self.sepia,
            "invert": self.invert,
            "emboss": self.emboss,
            "sharpen": self.sharpen,
            "blur": self.blur,
            "smooth": self.smooth,
            "edge_enhance": self.edge_enhance,
            "contour": self.contour,
            "detail": self.detail,
            
            # Color Filters (11-20)
            "vintage": self.vintage,
            "cool": self.cool,
            "warm": self.warm,
            "noir": self.noir,
            "pastel": self.pastel,
            "sunset": self.sunset,
            "ocean": self.ocean,
            "forest": self.forest,
            "autumn": self.autumn,
            "spring": self.spring,
            
            # Artistic Filters (21-30)
            "oil_paint": self.oil_paint,
            "watercolor": self.watercolor,
            "pencil_sketch": self.pencil_sketch,
            "cartoon": self.cartoon,
            "pixelate": self.pixelate,
            "glitch": self.glitch,
            "vhs": self.vhs,
            "halftone": self.halftone,
            "mosaic": self.mosaic,
            "stained_glass": self.stained_glass,
            
            # Lighting Effects (31-40)
            "bokeh": self.bokeh,
            "lens_flare": self.lens_flare,
            "vignette": self.vignette,
            "gradient_map": self.gradient_map,
            "dual_tone": self.dual_tone,
            "cross_process": self.cross_process,
            "hdr": self.hdr,
            "dramatic": self.dramatic,
            "dreamy": self.dreamy,
            "cinematic": self.cinematic,
            
            # Special Effects (41-50)
            "neon": self.neon,
            "glow": self.glow,
            "sparkle": self.sparkle,
            "rainbow": self.rainbow,
            "prism": self.prism,
            "mirror": self.mirror,
            "kaleidoscope": self.kaleidoscope,
            "fisheye": self.fisheye,
            "tilt_shift": self.tilt_shift,
            "miniature": self.miniature
        }
    
    def apply_filter(self, image_path: str, filter_name: str) -> str:
        """Apply filter to image"""
        if filter_name not in self.filters:
            raise ValueError(f"Filter {filter_name} not found")
        
        img = Image.open(image_path)
        img = self.filters[filter_name](img)
        
        output_path = os.path.join(Config.OUTPUT_DIR, f"filter_{filter_name}_{datetime.now().timestamp()}.png")
        img.save(output_path)
        return output_path
    
    # ========== BASIC FILTERS ==========
    
    def grayscale(self, img):
        return img.convert("L").convert("RGB")
    
    def sepia(self, img):
        img = img.convert("RGB")
        width, height = img.size
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return img
    
    def invert(self, img):
        return ImageOps.invert(img.convert("RGB"))
    
    def emboss(self, img):
        return img.filter(ImageFilter.EMBOSS)
    
    def sharpen(self, img):
        return img.filter(ImageFilter.SHARPEN)
    
    def blur(self, img):
        return img.filter(ImageFilter.GaussianBlur(radius=2))
    
    def smooth(self, img):
        return img.filter(ImageFilter.SMOOTH)
    
    def edge_enhance(self, img):
        return img.filter(ImageFilter.EDGE_ENHANCE)
    
    def contour(self, img):
        return img.filter(ImageFilter.CONTOUR)
    
    def detail(self, img):
        return img.filter(ImageFilter.DETAIL)
    
    # ========== COLOR FILTERS ==========
    
    def vintage(self, img):
        img = ImageEnhance.Color(img).enhance(0.8)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        return img
    
    def cool(self, img):
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.1)
        return img
    
    def warm(self, img):
        img = ImageEnhance.Color(img).enhance(0.8)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        return img
    
    def noir(self, img):
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.5)
        return img.convert("RGB")
    
    def pastel(self, img):
        img = ImageEnhance.Color(img).enhance(0.6)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        return img
    
    def sunset(self, img):
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.2)
        img = Image.merge("RGB", (r, g, b))
        return img
    
    def ocean(self, img):
        img = ImageEnhance.Color(img).enhance(1.4)
        r, g, b = img.split()
        b = b.point(lambda i: i * 1.3)
        img = Image.merge("RGB", (r, g, b))
        return img
    
    def forest(self, img):
        img = ImageEnhance.Color(img).enhance(1.2)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.3)
        img = Image.merge("RGB", (r, g, b))
        return img
    
    def autumn(self, img):
        img = ImageEnhance.Color(img).enhance(1.1)
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.3)
        g = g.point(lambda i: i * 0.8)
        img = Image.merge("RGB", (r, g, b))
        return img
    
    def spring(self, img):
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.2)
        img = Image.merge("RGB", (r, g, b))
        return img
    
    # ========== ARTISTIC FILTERS ==========
    
    def oil_paint(self, img):
        img_array = np.array(img)
        radius = 5
        intensity = 30
        
        # Apply oil painting effect using OpenCV
        output = cv2.xphoto.oilPainting(img_array, radius, intensity)
        return Image.fromarray(output)
    
    def watercolor(self, img):
        img_array = np.array(img)
        # Apply bilateral filter for watercolor effect
        output = cv2.stylization(img_array, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(output)
    
    def pencil_sketch(self, img):
        img_array = np.array(img.convert("L"))
        # Apply pencil sketch effect
        _, sketch = cv2.pencilSketch(img_array, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        return Image.fromarray(sketch).convert("RGB")
    
    def cartoon(self, img):
        img_array = np.array(img)
        # Apply cartoon effect
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        
        color = cv2.bilateralFilter(img_array, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)
    
    def pixelate(self, img, pixel_size=10):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Downsample
        small = cv2.resize(img_array, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
        # Upsample
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return Image.fromarray(pixelated)
    
    def glitch(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Random color shifts
        shift = np.random.randint(-15, 15)
        img_array = np.roll(img_array, shift, axis=1)
        
        # Add noise
        noise = np.random.randint(0, 40, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        return Image.fromarray(img_array.astype('uint8'))
    
    def vhs(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Add scanlines
        scanlines = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(0, h, 2):
            scanlines[i:i+1, :] = [20, 20, 20]
        
        img_array = np.clip(img_array + scanlines, 0, 255)
        
        # Add color bleed
        img_array[:, :, 0] = np.roll(img_array[:, :, 0], 2, axis=1)
        img_array[:, :, 2] = np.roll(img_array[:, :, 2], -2, axis=1)
        
        return Image.fromarray(img_array)
    
    def halftone(self, img):
        img_array = np.array(img.convert("L"))
        h, w = img_array.shape
        
        # Create halftone pattern
        pattern = np.zeros((h, w), dtype=np.uint8)
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                block = img_array[y:y+4, x:x+4]
                intensity = np.mean(block) / 255
                size = int(4 * intensity)
                if size > 0:
                    cv2.circle(pattern, (x+2, y+2), size//2, 255, -1)
        
        return Image.fromarray(pattern).convert("RGB")
    
    def mosaic(self, img, block_size=20):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = img_array[y:y+block_size, x:x+block_size]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img_array[y:y+block_size, x:x+block_size] = avg_color
        
        return Image.fromarray(img_array)
    
    def stained_glass(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create grid
        grid_size = 30
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                block = img_array[y:y+grid_size, x:x+grid_size]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img_array[y:y+grid_size, x:x+grid_size] = avg_color
        
        # Add black borders
        img_array[::grid_size, :] = [0, 0, 0]
        img_array[:, ::grid_size] = [0, 0, 0]
        
        return Image.fromarray(img_array)
    
    # ========== LIGHTING EFFECTS ==========
    
    def bokeh(self, img):
        img = img.filter(ImageFilter.GaussianBlur(radius=5))
        return img
    
    def lens_flare(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create lens flare effect
        flare = np.zeros((h, w, 3), dtype=np.uint8)
        center_x, center_y = w // 2, h // 2
        
        for y in range(h):
            for x in range(w):
                dx = x - center_x
                dy = y - center_y
                dist = np.sqrt(dx*dx + dy*dy)
                intensity = max(0, 1 - dist / (min(w, h) / 3))
                flare[y, x] = [255 * intensity, 200 * intensity, 150 * intensity]
        
        img_array = np.clip(img_array + flare, 0, 255)
        return Image.fromarray(img_array)
    
    def vignette(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create vignette mask
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        center_x, center_y = w // 2, h // 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        radius = min(w, h) / 2
        mask = 1 - (dist / radius)
        mask = np.clip(mask, 0, 1)
        
        # Apply mask
        for i in range(3):
            img_array[:, :, i] = img_array[:, :, i] * mask
        
        return Image.fromarray(img_array.astype('uint8'))
    
    def gradient_map(self, img):
        img_array = np.array(img.convert("L"))
        
        # Create gradient colors
        gradient = np.linspace(0, 255, 256)
        gradient = np.stack([gradient, gradient * 0.5, gradient * 0.2], axis=1)
        
        # Apply gradient map
        mapped = gradient[img_array.flatten()].reshape(img_array.shape + (3,))
        
        return Image.fromarray(mapped.astype('uint8'))
    
    def dual_tone(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Split into shadows and highlights
        shadows = np.clip(img_array * 0.5, 0, 255).astype('uint8')
        highlights = np.clip(img_array * 1.5, 0, 255).astype('uint8')
        
        # Combine
        result = np.where(img_array < 128, shadows, highlights)
        
        return Image.fromarray(result)
    
    def cross_process(self, img):
        img = ImageEnhance.Color(img).enhance(1.3)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        r, g, b = img.split()
        r = r.point(lambda i: i * 0.9)
        b = b.point(lambda i: i * 1.1)
        return Image.merge("RGB", (r, g, b))
    
    def hdr(self, img):
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        return img
    
    def dramatic(self, img):
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(0.9)
        return img
    
    def dreamy(self, img):
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img = ImageEnhance.Brightness(img).enhance(1.2)
        return img
    
    def cinematic(self, img):
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Color(img).enhance(0.8)
        
        # Add black bars
        width, height = img.size
        bar_height = height // 6
        result = Image.new('RGB', (width, height), 'black')
        result.paste(img, (0, bar_height))
        
        return result
    
    # ========== SPECIAL EFFECTS ==========
    
    def neon(self, img):
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Create neon effect
        neon = np.zeros_like(img_array)
        neon[edges > 0] = [0, 255, 255]
        
        # Blend with original
        result = cv2.addWeighted(img_array, 0.7, neon, 0.3, 0)
        
        return Image.fromarray(result)
    
    def glow(self, img):
        blur = img.filter(ImageFilter.GaussianBlur(radius=10))
        return Image.blend(img, blur, 0.5)
    
    def sparkle(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Add random sparkles
        num_sparkles = 100
        for _ in range(num_sparkles):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            cv2.circle(img_array, (x, y), 2, (255, 255, 255), -1)
        
        return Image.fromarray(img_array)
    
    def rainbow(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create rainbow gradient
        rainbow = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            for j in range(w):
                angle = (j / w) * 2 * np.pi
                rainbow[i, j] = [int(127.5 + 127.5 * np.sin(angle)),
                                 int(127.5 + 127.5 * np.sin(angle + 2*np.pi/3)),
                                 int(127.5 + 127.5 * np.sin(angle + 4*np.pi/3))]
        
        # Blend with original
        result = cv2.addWeighted(img_array, 0.7, rainbow, 0.3, 0)
        
        return Image.fromarray(result)
    
    def prism(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Shift color channels
        r = np.roll(img_array[:, :, 0], 5, axis=1)
        g = img_array[:, :, 1]
        b = np.roll(img_array[:, :, 2], -5, axis=1)
        
        result = np.stack([r, g, b], axis=2)
        
        return Image.fromarray(result)
    
    def mirror(self, img):
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    
    def kaleidoscope(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create kaleidoscope effect
        result = np.zeros((h, w, 3), dtype=np.uint8)
        
        for y in range(h):
            for x in range(w):
                # Map to polar coordinates
                cx, cy = w // 2, h // 2
                dx = x - cx
                dy = y - cy
                
                angle = np.arctan2(dy, dx)
                radius = np.sqrt(dx*dx + dy*dy)
                
                # Mirror sections
                sections = 8
                angle = angle % (2 * np.pi / sections)
                
                # Map back to cartesian
                x2 = int(cx + radius * np.cos(angle))
                y2 = int(cy + radius * np.sin(angle))
                
                if 0 <= x2 < w and 0 <= y2 < h:
                    result[y, x] = img_array[y2, x2]
        
        return Image.fromarray(result)
    
    def fisheye(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create fisheye distortion
        result = np.zeros((h, w, 3), dtype=np.uint8)
        cx, cy = w // 2, h // 2
        radius = min(w, h) / 2
        
        for y in range(h):
            for x in range(w):
                dx = (x - cx) / radius
                dy = (y - cy) / radius
                r = np.sqrt(dx*dx + dy*dy)
                
                if r <= 1:
                    theta = np.arctan2(dy, dx)
                    r2 = r * r
                    x2 = int(cx + radius * r2 * np.cos(theta))
                    y2 = int(cy + radius * r2 * np.sin(theta))
                    
                    if 0 <= x2 < w and 0 <= y2 < h:
                        result[y, x] = img_array[y2, x2]
        
        return Image.fromarray(result)
    
    def tilt_shift(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        
        # Create tilt-shift effect
        center = h // 2
        blur_radius = 10
        
        for y in range(h):
            distance = abs(y - center)
            blur = blur_radius * (distance / center)
            if blur > 0:
                kernel_size = int(blur) * 2 + 1
                if kernel_size > 1:
                    img_array[y:y+1] = cv2.GaussianBlur(img_array[y:y+1], (kernel_size, kernel_size), 0)
        
        return Image.fromarray(img_array)
    
    def miniature(self, img):
        # Similar to tilt-shift but with saturation boost
        img = self.tilt_shift(img)
        img = ImageEnhance.Color(img).enhance(1.5)
        return img

# ============================================
# PART 3: 40+ VIDEO EDITING TOOLS
# ============================================

class VideoTools40:
    """40+ Professional Video Editing Tools"""
    
    def __init__(self):
        self.tools_count = 0
    
    def generate_filename(self, ext=".mp4"):
        return os.path.join(Config.OUTPUT_DIR, f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}{ext}")
    
    # ========== BASIC EDITING (1-10) ==========
    
    def trim(self, path: str, start: float, end: float) -> str:
        """Tool 1: Trim video"""
        clip = VideoFileClip(path)
        trimmed = clip.subclip(start, end)
        out = self.generate_filename()
        trimmed.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def crop(self, path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        """Tool 2: Crop video"""
        clip = VideoFileClip(path)
        cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
        out = self.generate_filename()
        cropped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def resize(self, path: str, width: int, height: int) -> str:
        """Tool 3: Resize video"""
        clip = VideoFileClip(path)
        resized = clip.resize(newsize=(width, height))
        out = self.generate_filename()
        resized.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def rotate(self, path: str, angle: int) -> str:
        """Tool 4: Rotate video"""
        clip = VideoFileClip(path)
        rotated = clip.rotate(angle)
        out = self.generate_filename()
        rotated.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def flip_horizontal(self, path: str) -> str:
        """Tool 5: Flip horizontally"""
        clip = VideoFileClip(path)
        flipped = clip.fx(vfx.mirror_x)
        out = self.generate_filename()
        flipped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def flip_vertical(self, path: str) -> str:
        """Tool 6: Flip vertically"""
        clip = VideoFileClip(path)
        flipped = clip.fx(vfx.mirror_y)
        out = self.generate_filename()
        flipped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def speed(self, path: str, factor: float) -> str:
        """Tool 7: Change speed"""
        clip = VideoFileClip(path)
        sped = clip.fx(vfx.speedx, factor)
        out = self.generate_filename()
        sped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def reverse(self, path: str) -> str:
        """Tool 8: Reverse video"""
        clip = VideoFileClip(path)
        reversed_clip = clip.fx(vfx.time_mirror)
        out = self.generate_filename()
        reversed_clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def loop(self, path: str, times: int) -> str:
        """Tool 9: Loop video"""
        clip = VideoFileClip(path)
        looped = concatenate_videoclips([clip] * times)
        out = self.generate_filename()
        looped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def merge(self, paths: list) -> str:
        """Tool 10: Merge videos"""
        clips = [VideoFileClip(p) for p in paths]
        merged = concatenate_videoclips(clips)
        out = self.generate_filename()
        merged.write_videofile(out, logger=None, verbose=False)
        for c in clips:
            c.close()
        return out
    
    # ========== AUDIO TOOLS (11-15) ==========
    
    def extract_audio(self, path: str) -> str:
        """Tool 11: Extract audio"""
        clip = VideoFileClip(path)
        out = self.generate_filename(".mp3")
        clip.audio.write_audiofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def remove_audio(self, path: str) -> str:
        """Tool 12: Remove audio"""
        clip = VideoFileClip(path)
        no_audio = clip.without_audio()
        out = self.generate_filename()
        no_audio.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def add_audio(self, video_path: str, audio_path: str, volume: float = 1.0) -> str:
        """Tool 13: Add audio"""
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        audio = audio.volumex(volume)
        final = video.set_audio(audio)
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        video.close()
        audio.close()
        return out
    
    def volume(self, path: str, factor: float) -> str:
        """Tool 14: Adjust volume"""
        clip = VideoFileClip(path)
        if clip.audio:
            audio = clip.audio.volumex(factor)
            clip = clip.set_audio(audio)
        out = self.generate_filename()
        clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def audio_fade(self, path: str, fade_in: float = 1, fade_out: float = 1) -> str:
        """Tool 15: Audio fade"""
        clip = VideoFileClip(path)
        if clip.audio:
            audio = clip.audio.audio_fadein(fade_in).audio_fadeout(fade_out)
            clip = clip.set_audio(audio)
        out = self.generate_filename()
        clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    # ========== EFFECTS & TRANSITIONS (16-25) ==========
    
    def fade_in(self, path: str, duration: float = 1) -> str:
        """Tool 16: Fade in"""
        clip = VideoFileClip(path)
        faded = clip.fx(vfx.fadein, duration)
        out = self.generate_filename()
        faded.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def fade_out(self, path: str, duration: float = 1) -> str:
        """Tool 17: Fade out"""
        clip = VideoFileClip(path)
        faded = clip.fx(vfx.fadeout, duration)
        out = self.generate_filename()
        faded.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def crossfade(self, path1: str, path2: str, duration: float = 1) -> str:
        """Tool 18: Crossfade transition"""
        v1 = VideoFileClip(path1)
        v2 = VideoFileClip(path2)
        v2 = v2.crossfadein(duration)
        merged = concatenate_videoclips([v1, v2])
        out = self.generate_filename()
        merged.write_videofile(out, logger=None, verbose=False)
        v1.close()
        v2.close()
        return out
    
    def slide_transition(self, path1: str, path2: str, direction: str = "right") -> str:
        """Tool 19: Slide transition"""
        v1 = VideoFileClip(path1)
        v2 = VideoFileClip(path2)
        
        # Create sliding effect
        duration = 1
        slide = v2.set_position(lambda t: (v1.w * (t / duration), 0)).set_start(v1.duration - duration)
        
        final = CompositeVideoClip([v1, slide])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        v1.close()
        v2.close()
        return out
    
    def glitch_effect(self, path: str) -> str:
        """Tool 20: Glitch effect"""
        clip = VideoFileClip(path)
        
        def glitch_frame(frame):
            frame_array = np.array(frame)
            h, w = frame_array.shape[:2]
            
            # Add glitch
            shift = np.random.randint(-20, 20)
            frame_array = np.roll(frame_array, shift, axis=1)
            
            # Add noise
            noise = np.random.randint(0, 30, frame_array.shape)
            frame_array = np.clip(frame_array + noise, 0, 255)
            
            return frame_array.astype('uint8')
        
        glitched = clip.fl_image(glitch_frame)
        out = self.generate_filename()
        glitched.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def pixelate_effect(self, path: str, pixel_size: int = 10) -> str:
        """Tool 21: Pixelate effect"""
        clip = VideoFileClip(path)
        
        def pixelate_frame(frame):
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            return pixelated
        
        pixelated = clip.fl_image(pixelate_frame)
        out = self.generate_filename()
        pixelated.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def grayscale_video(self, path: str) -> str:
        """Tool 22: Grayscale effect"""
        clip = VideoFileClip(path)
        bw = clip.fx(vfx.blackwhite)
        out = self.generate_filename()
        bw.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def sepia_video(self, path: str) -> str:
        """Tool 23: Sepia effect"""
        clip = VideoFileClip(path)
        
        def sepia_frame(frame):
            frame_array = np.array(frame)
            sepia_filter = np.array([[0.393, 0.769, 0.189],
                                     [0.349, 0.686, 0.168],
                                     [0.272, 0.534, 0.131]])
            sepia = frame_array @ sepia_filter.T
            return np.clip(sepia, 0, 255).astype('uint8')
        
        sepia = clip.fl_image(sepia_frame)
        out = self.generate_filename()
        sepia.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def blur_video(self, path: str, radius: int = 5) -> str:
        """Tool 24: Blur effect"""
        clip = VideoFileClip(path)
        
        def blur_frame(frame):
            return cv2.GaussianBlur(frame, (radius*2+1, radius*2+1), 0)
        
        blurred = clip.fl_image(blur_frame)
        out = self.generate_filename()
        blurred.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def sharpen_video(self, path: str) -> str:
        """Tool 25: Sharpen effect"""
        clip = VideoFileClip(path)
        
        def sharpen_frame(frame):
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            return cv2.filter2D(frame, -1, kernel)
        
        sharpened = clip.fl_image(sharpen_frame)
        out = self.generate_filename()
        sharpened.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    # ========== COMPRESSION & QUALITY (26-30) ==========
    
    def compress(self, path: str, target_size_mb: int = 20) -> str:
        """Tool 26: Compress video"""
        clip = VideoFileClip(path)
        duration = clip.duration
        target_bitrate = (target_size_mb * 8) / duration
        out = self.generate_filename()
        clip.write_videofile(out, bitrate=f"{target_bitrate}k", logger=None, verbose=False)
        clip.close()
        return out
    
    def quality_4k(self, path: str) -> str:
        """Tool 27: Convert to 4K"""
        clip = VideoFileClip(path)
        resized = clip.resize(newsize=(3840, 2160))
        out = self.generate_filename()
        resized.write_videofile(out, bitrate="20000k", logger=None, verbose=False)
        clip.close()
        return out
    
    def quality_1080p(self, path: str) -> str:
        """Tool 28: Convert to 1080p"""
        clip = VideoFileClip(path)
        resized = clip.resize(newsize=(1920, 1080))
        out = self.generate_filename()
        resized.write_videofile(out, bitrate="5000k", logger=None, verbose=False)
        clip.close()
        return out
    
    def quality_720p(self, path: str) -> str:
        """Tool 29: Convert to 720p"""
        clip = VideoFileClip(path)
        resized = clip.resize(newsize=(1280, 720))
        out = self.generate_filename()
        resized.write_videofile(out, bitrate="2500k", logger=None, verbose=False)
        clip.close()
        return out
    
    def optimize(self, path: str) -> str:
        """Tool 30: Optimize for web"""
        clip = VideoFileClip(path)
        out = self.generate_filename()
        clip.write_videofile(out, codec='libx264', audio_codec='aac', 
                            preset='fast', logger=None, verbose=False)
        clip.close()
        return out
    
    # ========== ADVANCED EFFECTS (31-35) ==========
    
    def slow_motion(self, path: str, factor: float = 0.5) -> str:
        """Tool 31: Slow motion"""
        return self.speed(path, factor)
    
    def fast_motion(self, path: str, factor: float = 2.0) -> str:
        """Tool 32: Fast motion"""
        return self.speed(path, factor)
    
    def pip(self, background: str, overlay: str, position: str = "bottom-right") -> str:
        """Tool 33: Picture-in-picture"""
        bg = VideoFileClip(background)
        ov = VideoFileClip(overlay).resize(0.3)
        
        positions = {
            "top-left": (10, 10),
            "top-right": (bg.w - ov.w - 10, 10),
            "bottom-left": (10, bg.h - ov.h - 10),
            "bottom-right": (bg.w - ov.w - 10, bg.h - ov.h - 10),
            "center": ((bg.w - ov.w) // 2, (bg.h - ov.h) // 2)
        }
        
        pos = positions.get(position, positions["bottom-right"])
        combined = CompositeVideoClip([bg, ov.set_position(pos)])
        out = self.generate_filename()
        combined.write_videofile(out, logger=None, verbose=False)
        
        bg.close()
        ov.close()
        return out
    
    def split_screen(self, paths: list, layout: str = "2x2") -> str:
        """Tool 34: Split screen effect"""
        clips = [VideoFileClip(p) for p in paths[:4]]
        
        if layout == "2x2" and len(clips) >= 4:
            # Create 2x2 grid
            w = clips[0].w
            h = clips[0].h
            
            top_row = clips_array([[clips[0].resize((w//2, h//2)), 
                                   clips[1].resize((w//2, h//2))]])
            bottom_row = clips_array([[clips[2].resize((w//2, h//2)), 
                                      clips[3].resize((w//2, h//2))]])
            final = clips_array([[top_row], [bottom_row]])
        else:
            # Horizontal split
            final = clips_array([clips])
        
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        for c in clips:
            c.close()
        return out
    
    def add_text(self, path: str, text: str, font_size: int = 30, color: str = "white") -> str:
        """Tool 35: Add text overlay"""
        clip = VideoFileClip(path)
        txt = TextClip(text, fontsize=font_size, color=color, font='Arial', 
                       stroke_color='black', stroke_width=1)
        txt = txt.set_position(('center', 'bottom')).set_duration(clip.duration)
        final = CompositeVideoClip([clip, txt])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    # ========== WATERMARK & OVERLAY (36-40) ==========
    
    def add_watermark(self, path: str, text: str, position: str = "bottom-right") -> str:
        """Tool 36: Add watermark"""
        clip = VideoFileClip(path)
        
        positions = {
            "top-left": (10, 10),
            "top-right": (clip.w - 100, 10),
            "bottom-left": (10, clip.h - 30),
            "bottom-right": (clip.w - 100, clip.h - 30)
        }
        
        pos = positions.get(position, positions["bottom-right"])
        watermark = TextClip(text, fontsize=20, color='white', font='Arial')
        watermark = watermark.set_position(pos).set_duration(clip.duration).set_opacity(0.5)
        final = CompositeVideoClip([clip, watermark])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def add_logo(self, path: str, logo_path: str, position: str = "bottom-right") -> str:
        """Tool 37: Add logo overlay"""
        clip = VideoFileClip(path)
        logo = ImageClip(logo_path).set_duration(clip.duration).resize(height=100)
        
        positions = {
            "top-left": (10, 10),
            "top-right": (clip.w - logo.w - 10, 10),
            "bottom-left": (10, clip.h - logo.h - 10),
            "bottom-right": (clip.w - logo.w - 10, clip.h - logo.h - 10)
        }
        
        pos = positions.get(position, positions["bottom-right"])
        final = CompositeVideoClip([clip, logo.set_position(pos)])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        clip.close()
        return out
    
    def add_music(self, video_path: str, music_path: str, volume: float = 0.3) -> str:
        """Tool 38: Add background music"""
        video = VideoFileClip(video_path)
        music = AudioFileClip(music_path)
        
        # Loop music if needed
        if music.duration < video.duration:
            music = music.loop(duration=video.duration)
        else:
            music = music.subclip(0, video.duration)
        
        music = music.volumex(volume)
        
        # Mix with original audio
        if video.audio:
            final_audio = CompositeAudioClip([video.audio, music])
        else:
            final_audio = music
        
        final = video.set_audio(final_audio)
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        video.close()
        music.close()
        return out
    
    def voiceover(self, video_path: str, audio_path: str) -> str:
        """Tool 39: Add voiceover"""
        video = VideoFileClip(video_path)
        voice = AudioFileClip(audio_path)
        
        # Reduce original volume
        if video.audio:
            original = video.audio.volumex(0.3)
            final_audio = CompositeAudioClip([original, voice])
        else:
            final_audio = voice
        
        final = video.set_audio(final_audio)
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        
        video.close()
        voice.close()
        return out
    
    def extract_frames(self, path: str, interval: int = 1) -> list:
        """Tool 40: Extract frames"""
        clip = VideoFileClip(path)
        frames = []
        
        for t in range(0, int(clip.duration), interval):
            frame = clip.get_frame(t)
            frame_path = os.path.join(Config.OUTPUT_DIR, f"frame_{t}.jpg")
            cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            frames.append(frame_path)
        
        clip.close()
        return frames

# ============================================
# PART 4: TELEGRAM BOT WITH FULL MENU
# ============================================

class KinvaMasterBot:
    """Complete Telegram Bot with 30+ Command Menu"""
    
    def __init__(self):
        self.video_tools = VideoTools40()
        self.filters = Filters50()
        self.user_sessions = {}
        self.processing_tasks = {}
    
    # ========== COMMAND HANDLERS ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message with animation"""
        user = update.effective_user
        
        # Check if user exists
        if not db.get_user(user.id):
            db.create_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_animation = """
🎬 **KINVA MASTER PRO** 🎬

━━━━━━━━━━━━━━━━━━━━━━
✨ **WELCOME TO THE ULTIMATE EDITING BOT** ✨
━━━━━━━━━━━━━━━━━━━━━━

👋 Hello **{first_name}**!

🚀 **What I Can Do:**
• 🎥 **40+ Video Editing Tools**
• 🖼️ **30+ Image Editing Tools**  
• 🎨 **50+ Professional Filters**
• 🎵 **Audio Processing Tools**
• 📥 **Social Media Downloader**
• ⭐ **Premium Features**
• 💎 **Kinemaster/CapCut/VN Style Tools**

📊 **Your Stats:**
• Edits Today: {daily_edits}/{max_edits}
• Total Edits: {total_edits}
• Premium: {premium_status}

💡 **Quick Start:**
Send me a photo or video to start editing!

━━━━━━━━━━━━━━━━━━━━━━
🌟 **Type /menu to see all tools** 🌟
━━━━━━━━━━━━━━━━━━━━━━
        """
        
        user_data = db.get_user(user.id)
        is_premium = db.is_premium(user.id)
        max_edits = Config.MAX_EDIT_PER_DAY_PREMIUM if is_premium else Config.MAX_EDIT_PER_DAY_FREE
        
        welcome_text = welcome_animation.format(
            first_name=user.first_name,
            daily_edits=user_data['daily_edits'],
            max_edits=max_edits,
            total_edits=user_data['edits_count'],
            premium_status="✅ ACTIVE" if is_premium else "❌ INACTIVE"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
             InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium")],
            [InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download"),
             InlineKeyboardButton("💎 TEMPLATES", callback_data="menu_templates")],
            [InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats"),
             InlineKeyboardButton("❓ HELP", callback_data="menu_help")]
        ]
        
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full command menu"""
        menu_text = """
📋 **COMPLETE COMMAND MENU**

━━━━━━━━━━━━━━━━━━━━━━
**🎬 VIDEO EDITING (40+ TOOLS)**
━━━━━━━━━━━━━━━━━━━━━━
/trim - Trim video
/crop_video - Crop video
/resize_video - Resize video
/rotate_video - Rotate video
/flip_h - Flip horizontal
/flip_v - Flip vertical
/speed - Change speed
/slow_mo - Slow motion
/fast_mo - Fast motion
/reverse - Reverse video
/loop - Loop video
/merge - Merge videos

**🎵 AUDIO TOOLS**
/extract_audio - Extract audio
/remove_audio - Remove audio
/add_audio - Add audio track
/volume - Adjust volume
/audio_fade - Audio fade effect

**✨ VIDEO EFFECTS**
/fade_in - Fade in effect
/fade_out - Fade out effect
/glitch - Glitch effect
/pixelate - Pixelate effect
/grayscale_vid - Black & white
/sepia_vid - Sepia effect
/blur_vid - Blur effect
/sharpen_vid - Sharpen effect

**📦 COMPRESSION**
/compress - Compress video
/to_4k - Convert to 4K
/to_1080p - Convert to 1080p
/to_720p - Convert to 720p
/optimize - Optimize for web

**🖼️ IMAGE EDITING (30+ TOOLS)**
/resize_img - Resize image
/crop_img - Crop image
/rotate_img - Rotate image
/flip_h_img - Flip horizontal
/flip_v_img - Flip vertical
/brightness - Adjust brightness
/contrast - Adjust contrast
/saturation - Adjust saturation
/sharpness - Adjust sharpness
/blur_img - Blur image

**🎨 FILTERS (50+)**
/filters - Show all filters
/grayscale - Grayscale filter
/sepia - Sepia filter
/vintage - Vintage filter
/cool - Cool filter
/warm - Warm filter
/noir - Noir filter
/pastel - Pastel filter
/glow - Glow effect
/neon - Neon effect

**⭐ PREMIUM FEATURES**
/premium - Get premium
/kinemaster - Kinemaster tools
/capcut - CapCut tools
/vn - VN Editor tools
/canva - Canva templates

**📥 DOWNLOAD TOOLS**
/youtube - Download YouTube
/instagram - Download Instagram
/tiktok - Download TikTok
/pinterest - Download Pinterest

**ℹ️ INFO**
/stats - Your statistics
/feedback - Send feedback
/support - Contact support
/about - About bot

━━━━━━━━━━━━━━━━━━━━━━
💡 **Just send me a photo/video to start!**
        """
        
        await update.message.reply_text(menu_text, parse_mode=ParseMode.MARKDOWN)
    
    async def video_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show video tools menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("🎵 AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("🔊 COMPRESS", callback_data="tool_compress")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="tool_effects"),
             InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🎬 **VIDEO EDITING TOOLS**\n\nChoose a tool:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def image_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show image tools menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_img"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img"),
             InlineKeyboardButton("🪞 FLIP", callback_data="tool_flip_img")],
            [InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust"),
             InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark_img"),
             InlineKeyboardButton("📝 TEXT", callback_data="tool_text_img")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🖼️ **IMAGE EDITING TOOLS**\n\nChoose a tool:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all 50+ filters menu"""
        query = update.callback_query
        await query.answer()
        
        filter_categories = [
            ("🎨 BASIC", "filters_basic"),
            ("🌈 COLOR", "filters_color"),
            ("🎭 ARTISTIC", "filters_artistic"),
            ("✨ LIGHTING", "filters_lighting"),
            ("⚡ SPECIAL", "filters_special")
        ]
        
        keyboard = [[InlineKeyboardButton(name, callback_data=cb)] for name, cb in filter_categories]
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        
        await query.edit_message_text("🎨 **50+ PROFESSIONAL FILTERS**\n\nChoose category:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_basic_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show basic filters"""
        query = update.callback_query
        await query.answer()
        
        filters_list = [
            "grayscale", "sepia", "invert", "emboss", "sharpen", 
            "blur", "smooth", "edge_enhance", "contour", "detail"
        ]
        
        keyboard = []
        for i in range(0, len(filters_list), 2):
            row = []
            row.append(InlineKeyboardButton(filters_list[i].title(), callback_data=f"filter_{filters_list[i]}"))
            if i+1 < len(filters_list):
                row.append(InlineKeyboardButton(filters_list[i+1].title(), callback_data=f"filter_{filters_list[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text("🎨 **BASIC FILTERS**\n\nChoose a filter:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def premium_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium subscription menu"""
        query = update.callback_query
        await query.answer()
        
        is_premium = db.is_premium(query.from_user.id)
        
        if is_premium:
            user = db.get_user(query.from_user.id)
            text = f"""
⭐ **YOU ARE A PREMIUM MEMBER!** ⭐

✨ **Premium Features Active:**
• 🚫 No Watermark
• 📤 4K Export
• ⚡ Priority Processing
• 🎯 Motion Tracking
• 🟢 Chroma Key
• 📝 Auto Captions
• 🎙️ Voiceover
• 💎 All Filters

📅 **Expires:** {user['premium_expiry'][:10]}

💎 **Thank you for supporting Kinva Master!**
            """
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            text = """
⭐ **KINVA MASTER PREMIUM** ⭐

🚀 **Unlock Unlimited Power!**

**Premium Features:**
✨ **Video Tools:**
• 🎯 Motion Tracking
• 🟢 Chroma Key (Green Screen)
• 📝 Auto Captions
• 🔑 Keyframe Animation
• 🎙️ Voiceover Recording

✨ **Image Tools:**
• 🌈 Advanced Color Grading
• 🎭 AI Face Detection
• 🖌️ Custom Brushes
• 📊 Batch Processing

✨ **Benefits:**
• 🚫 No Watermark
• 📤 4K Export
• ⚡ Priority Queue
• 📞 Priority Support
• 💎 Exclusive Templates

**Pricing:**
💎 Monthly: ${Config.PREMIUM_PRICE_USD} / {Config.PREMIUM_PRICE_STARS} Stars
💎 Yearly: ${Config.PREMIUM_PRICE_USD * 10} (Save 20%)

**Payment Methods:**
💳 UPI: `{Config.UPI_ID}`
💸 PayPal: PayPal Link
⭐ Telegram Stars
₿ Crypto: USDT

━━━━━━━━━━━━━━━━━━━━━━
🔥 **UPGRADE NOW AND GET 7 DAYS FREE!** 🔥
            """
            
            keyboard = [
                [InlineKeyboardButton("💎 BUY PREMIUM", callback_data="buy_premium")],
                [InlineKeyboardButton("⭐ PAY WITH STARS", callback_data="pay_stars")],
                [InlineKeyboardButton("💳 UPI PAYMENT", callback_data="pay_upi")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo upload"""
        user_id = update.effective_user.id
        
        if not db.can_edit(user_id):
            await update.message.reply_text("❌ You've reached your daily free edit limit! Upgrade to premium for unlimited edits.")
            return
        
        photo = await update.message.photo[-1].get_file()
        path = os.path.join(Config.UPLOAD_DIR, f"photo_{user_id}_{datetime.now().timestamp()}.jpg")
        await photo.download_to_drive(path)
        
        context.user_data['current_image'] = path
        context.user_data['original_image'] = path
        db.increment_edits(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🎨 APPLY FILTER", callback_data="apply_filter_menu"),
             InlineKeyboardButton("🛠️ EDIT TOOLS", callback_data="image_tools_menu")],
            [InlineKeyboardButton("💧 ADD WATERMARK", callback_data="add_watermark_img"),
             InlineKeyboardButton("📝 ADD TEXT", callback_data="add_text_img")],
            [InlineKeyboardButton("🔄 RESET", callback_data="reset_image"),
             InlineKeyboardButton("✅ DONE", callback_data="done_edit")]
        ]
        
        await update.message.reply_photo(photo=open(path, 'rb'), 
                                         caption="✅ **Photo received!** Choose an option:", 
                                         reply_markup=InlineKeyboardMarkup(keyboard), 
                                         parse_mode=ParseMode.MARKDOWN)
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video upload"""
        user_id = update.effective_user.id
        
        if not db.can_edit(user_id):
            await update.message.reply_text("❌ You've reached your daily free edit limit! Upgrade to premium for unlimited edits.")
            return
        
        video = await update.message.video.get_file()
        path = os.path.join(Config.UPLOAD_DIR, f"video_{user_id}_{datetime.now().timestamp()}.mp4")
        await video.download_to_drive(path)
        
        context.user_data['current_video'] = path
        db.increment_edits(user_id)
        
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed")],
            [InlineKeyboardButton("🎵 ADD AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("🔊 COMPRESS", callback_data="tool_compress")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="tool_effects"),
             InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark")],
            [InlineKeyboardButton("✅ DONE", callback_data="done_edit")]
        ]
        
        await update.message.reply_video(video=open(path, 'rb'), 
                                         caption="✅ **Video received!** Choose an option:", 
                                         reply_markup=InlineKeyboardMarkup(keyboard), 
                                         parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        # Main menu navigation
        if data == "back_main":
            await self.start(update, context)
        elif data == "menu_video":
            await self.video_menu(update, context)
        elif data == "menu_image":
            await self.image_menu(update, context)
        elif data == "menu_filters":
            await self.filters_menu(update, context)
        elif data == "menu_premium":
            await self.premium_menu(update, context)
        elif data == "menu_stats":
            await self.stats_command(update, context)
        elif data == "menu_help":
            await self.help_command(update, context)
        
        # Filter categories
        elif data == "filters_basic":
            await self.show_basic_filters(update, context)
        
        # Apply filter
        elif data.startswith("filter_"):
            filter_name = data.replace("filter_", "")
            if 'current_image' in context.user_data:
                await query.answer(f"Applying {filter_name}...")
                
                try:
                    path = context.user_data['current_image']
                    output_path = self.filters.apply_filter(path, filter_name)
                    
                    with open(output_path, 'rb') as f:
                        await query.message.reply_photo(f, caption=f"✅ Applied **{filter_name}** filter!", parse_mode=ParseMode.MARKDOWN)
                    
                    context.user_data['current_image'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
        
        # Video tools
        elif data == "tool_trim":
            await query.edit_message_text("✂️ **Trim Video**\n\nSend start and end time in seconds.\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'trim_params'
        
        elif data == "tool_speed":
            await query.edit_message_text("⚡ **Change Speed**\n\nSend speed factor:\n• 0.5 = Slow motion\n• 1.0 = Normal\n• 2.0 = Fast motion\n\nExample: `1.5`", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'speed_params'
        
        elif data == "tool_compress":
            await query.edit_message_text("🔊 **Compress Video**\n\nSend target size in MB (max 50MB).\nExample: `20`", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'compress_params'
        
        elif data == "done_edit":
            await query.edit_message_text("✅ **Editing complete!** Send me another file to continue!", parse_mode=ParseMode.MARKDOWN)
        
        # Payment
        elif data == "pay_stars":
            await self.pay_with_stars(update, context)
        elif data == "pay_upi":
            await self.show_upi_payment(update, context)
        elif data == "buy_premium":
            await self.premium_purchase(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for tool parameters"""
        text = update.message.text
        
        if 'waiting_for' in context.user_data:
            action = context.user_data['waiting_for']
            
            if action == 'trim_params':
                try:
                    start, end = map(float, text.split())
                    video_path = context.user_data['current_video']
                    
                    await update.message.reply_text("✂️ Trimming video... Please wait.")
                    
                    output_path = self.video_tools.trim(video_path, start, end)
                    
                    with open(output_path, 'rb') as f:
                        await update.message.reply_video(f, caption=f"✅ Trimmed from {start}s to {end}s")
                    
                    context.user_data['current_video'] = output_path
                    del context.user_data['waiting_for']
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {str(e)}")
            
            elif action == 'speed_params':
                try:
                    speed = float(text)
                    video_path = context.user_data['current_video']
                    
                    await update.message.reply_text("⚡ Changing speed... Please wait.")
                    
                    output_path = self.video_tools.speed(video_path, speed)
                    
                    with open(output_path, 'rb') as f:
                        await update.message.reply_video(f, caption=f"✅ Speed changed to {speed}x")
                    
                    context.user_data['current_video'] = output_path
                    del context.user_data['waiting_for']
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {str(e)}")
            
            elif action == 'compress_params':
                try:
                    target_size = int(text)
                    video_path = context.user_data['current_video']
                    
                    await update.message.reply_text("🔊 Compressing video... This may take a while.")
                    
                    output_path = self.video_tools.compress(video_path, target_size)
                    
                    with open(output_path, 'rb') as f:
                        await update.message.reply_video(f, caption=f"✅ Compressed to {target_size}MB")
                    
                    context.user_data['current_video'] = output_path
                    del context.user_data['waiting_for']
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user = db.get_user(update.effective_user.id)
        is_premium = db.is_premium(update.effective_user.id)
        stats = db.get_stats()
        
        text = f"""
📊 **YOUR STATISTICS**

👤 **User:** {update.effective_user.first_name}
🆔 **ID:** `{update.effective_user.id}`

📈 **Activity:**
• Total Edits: `{user['edits_count']}`
• Today's Edits: `{user['daily_edits']}`
• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`

{'📅 Expires: ' + user['premium_expiry'][:10] if is_premium else ''}

🏆 **Global Stats:**
• Total Users: `{stats['total_users']}`
• Premium Users: `{stats['premium_users']}`
• Total Edits: `{stats['total_edits']}`
• Today's Edits: `{stats['today_edits']}`

💎 **Referral Bonus:**
• Referrals: `{user['referral_count']}`
• Balance: `${user['balance']}`

━━━━━━━━━━━━━━━━━━━━━━
💡 **Share your referral link to earn rewards!**
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help menu"""
        await self.menu_command(update, context)
    
    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process Telegram Stars payment"""
        query = update.callback_query
        
        text = """
⭐ **PAY WITH TELEGRAM STARS** ⭐

**Premium Price:** `{Config.PREMIUM_PRICE_STARS} Stars`

**How to Pay:**
1. Click the button below
2. Confirm payment in Telegram
3. Premium activated instantly!

**Benefits:**
• No Watermark
• 4K Export
• Priority Processing
• All Filters Access
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐ PAY 100 STARS", callback_data="confirm_stars_payment")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_upi_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show UPI payment details"""
        query = update.callback_query
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"upi://pay?pa={Config.UPI_ID}&pn=KinvaMaster&am={Config.PREMIUM_PRICE_INR}&cu=INR")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(Config.TEMP_DIR, f"qr_{query.from_user.id}.png")
        img.save(qr_path)
        
        text = f"""
💳 **UPI PAYMENT**

**UPI ID:** `{Config.UPI_ID}`
**Amount:** ₹{Config.PREMIUM_PRICE_INR}

**Scan QR Code or Pay to UPI ID**

**Steps:**
1. Pay to the UPI ID above
2. Send screenshot to @admin
3. Premium activated within 24 hours

**Transaction ID Format:**
Send: `/confirm [transaction_id]` after payment
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]]
        
        with open(qr_path, 'rb') as f:
            await query.message.reply_photo(f, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def premium_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium purchase options"""
        query = update.callback_query
        
        text = """
💎 **CHOOSE YOUR PLAN**

**Monthly Plan:**
• ${Config.PREMIUM_PRICE_USD} / month
• 100 Telegram Stars
• All Premium Features

**Yearly Plan:**
• ${Config.PREMIUM_PRICE_USD * 10} / year
• Save 20%
• All Premium Features + Bonus

**Lifetime Plan:**
• ${Config.PREMIUM_PRICE_USD * 30}
• One-time payment
• Lifetime access + Future updates
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 MONTHLY", callback_data="buy_monthly"),
             InlineKeyboardButton("💎 YEARLY", callback_data="buy_yearly")],
            [InlineKeyboardButton("👑 LIFETIME", callback_data="buy_lifetime")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel command"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ You are not authorized to use this command!")
            return
        
        stats = db.get_stats()
        
        text = f"""
🔧 **ADMIN PANEL**

📊 **Statistics:**
• Total Users: {stats['total_users']}
• Premium Users: {stats['premium_users']}
• Total Edits: {stats['total_edits']}
• Today's Edits: {stats['today_edits']}

🛠️ **Admin Commands:**
/broadcast [message] - Broadcast to all users
/add_premium [user_id] - Add premium
/remove_premium [user_id] - Remove premium
/stats_all - View detailed stats
/announce [message] - Make announcement
/ban [user_id] - Ban user
/unban [user_id] - Unban user

📊 **Web Admin Panel:**
{Config.WEBHOOK_URL}/admin

🔐 **Admin Password:** {Config.ADMIN_PASSWORD}
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

  # ============================================
# PART 5: FLASK WEB APP WITH TIMELINE EDITOR
# ============================================
# Complete Web Application with Professional UI, Timeline Editor,
# Real-time Processing, and Advanced Animation Effects
flask_app = Flask(__name__)
flask_app.sercet_key = os.environ.get("FLASK_SECRET",  "")
# Correct - with proper closing
socketio = SocketIO(flask_app, cors_allowed_origins="*")
# ============================================
# COMPLETE WEB APP HTML TEMPLATE
# ============================================

WEB_APP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#667eea">
    <title>Kinva Master Pro - Professional Video & Image Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.12/cropper.min.css">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.12/cropper.min.js"></script>
    <style>
        /* ============================================
           GLOBAL STYLES & ANIMATIONS
        ============================================ */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #fff;
            overflow-x: hidden;
            min-height: 100vh;
        }
        
        /* Animated Background */
        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        
        .animated-bg::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
            animation: rotate 60s linear infinite;
        }
        
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Loading Animation */
        .loader-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            transition: all 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        .loader {
            text-align: center;
            animation: fadeInUp 1s ease;
        }
        
        .loader-circle {
            width: 100px;
            height: 100px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid #fff;
            border-right: 4px solid #fff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }
        
        .loader-text {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 4px;
            background: linear-gradient(135deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        .loader-sub {
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.8;
        }
        
        .loader-progress {
            width: 300px;
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            margin: 30px auto 0;
            overflow: hidden;
        }
        
        .loader-progress-bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #fff, #f0f0f0);
            border-radius: 2px;
            animation: progress 2.5s ease-in-out infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        /* Container */
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Header with Animation */
        .header {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px 30px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            animation: slideInLeft 0.6s ease;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-icon {
            width: 55px;
            height: 55px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            animation: pulse 2s ease-in-out infinite;
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        }
        
        .logo h1 {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #a8c0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .logo p {
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            margin-top: 5px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .premium-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.3s;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .premium-badge:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(245,87,108,0.4);
        }
        
        /* Main Editor Layout */
        .editor-layout {
            display: grid;
            grid-template-columns: 320px 1fr 320px;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 1200px) {
            .editor-layout {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }
        
        /* Tools Panel with Animation */
        .tools-panel {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px;
            height: fit-content;
            animation: slideInLeft 0.6s ease 0.1s both;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        
        .tools-panel:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .tools-panel h3 {
            margin-bottom: 20px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(102,126,234,0.5);
        }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .tools-grid::-webkit-scrollbar {
            width: 5px;
        }
        
        .tools-grid::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        
        .tools-grid::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        
        .tool-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 14px;
            color: #fff;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-content: center;
            font-weight: 500;
        }
        
        .tool-btn i {
            font-size: 16px;
        }
        
        .tool-btn:hover {
            background: linear-gradient(135deg, #667eea, #764ba2);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        
        /* Preview Area */
        .preview-area {
            background: rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            overflow: hidden;
            animation: scaleIn 0.6s ease 0.2s both;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .preview-header {
            background: rgba(255,255,255,0.1);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .preview-header span {
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .preview-container {
            position: relative;
            background: #000;
            min-height: 450px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        #preview-canvas, #preview-video {
            max-width: 100%;
            max-height: 500px;
            object-fit: contain;
            transition: all 0.3s;
        }
        
        .controls {
            padding: 20px;
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.3);
        }
        
        .control-btn {
            background: rgba(255,255,255,0.15);
            border: none;
            padding: 10px 24px;
            border-radius: 30px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .control-btn:hover {
            background: linear-gradient(135deg, #667eea, #764ba2);
            transform: translateY(-2px);
        }
        
        .control-btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        
        /* Filters Panel */
        .filters-panel {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px;
            height: fit-content;
            animation: slideInRight 0.6s ease 0.1s both;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .filters-panel h3 {
            margin-bottom: 20px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(102,126,234,0.5);
        }
        
        .filters-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .filter-item {
            background: rgba(255,255,255,0.1);
            border-radius: 14px;
            padding: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .filter-item:hover {
            background: linear-gradient(135deg, #667eea, #764ba2);
            transform: scale(1.05);
        }
        
        .filter-preview {
            width: 100%;
            height: 70px;
            border-radius: 10px;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            transition: all 0.3s;
        }
        
        .filter-name {
            font-size: 11px;
            font-weight: 500;
        }
        
        /* Timeline Area */
        .timeline-area {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px;
            margin-top: 20px;
            animation: fadeInUp 0.6s ease 0.3s both;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .timeline-header {
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .timeline-header h3 {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .timeline-container {
            position: relative;
            overflow-x: auto;
            background: rgba(0,0,0,0.3);
            border-radius: 16px;
            padding: 15px;
        }
        
        .timeline-track {
            display: flex;
            gap: 8px;
            min-height: 100px;
        }
        
        .timeline-clip {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 12px;
            padding: 12px;
            min-width: 120px;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
            text-align: center;
        }
        
        .timeline-clip:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(102,126,234,0.4);
        }
        
        .timeline-clip.selected {
            border: 2px solid #fff;
            box-shadow: 0 0 20px rgba(102,126,234,0.6);
        }
        
        .timeline-clip i {
            font-size: 24px;
            margin-bottom: 8px;
            display: block;
        }
        
        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(10px);
            padding: 14px 24px;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            font-size: 14px;
            border-left: 4px solid #667eea;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(15px);
            z-index: 20000;
            justify-content: center;
            align-items: center;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .modal-content {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 28px;
            padding: 35px;
            max-width: 500px;
            width: 90%;
            animation: scaleIn 0.3s ease;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header {
                flex-direction: column;
                text-align: center;
            }
            
            .tools-grid, .filters-grid {
                grid-template-columns: repeat(3, 1fr);
            }
            
            .control-btn {
                padding: 8px 16px;
                font-size: 12px;
            }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        
        /* Floating Animation */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .float-animation {
            animation: float 3s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <!-- Animated Background -->
    <div class="animated-bg"></div>
    
    <!-- Loading Animation -->
    <div class="loader-wrapper" id="loader">
        <div class="loader">
            <div class="loader-circle"></div>
            <div class="loader-text">KINVA MASTER</div>
            <div class="loader-sub">Professional Video & Image Editor</div>
            <div class="loader-progress">
                <div class="loader-progress-bar"></div>
            </div>
            <div class="loader-sub" id="loading-status">Loading advanced features...</div>
        </div>
    </div>
    
    <!-- Main Content -->
    <div class="container" id="main-content" style="display: none;">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <div class="logo-icon float-animation">
                    <i class="fas fa-film"></i>
                </div>
                <div>
                    <h1>Kinva Master Pro</h1>
                    <p><i class="fas fa-crown"></i> Professional Video & Image Editor | 50+ Filters | 40+ Tools</p>
                </div>
            </div>
            <div class="user-info">
                <div class="premium-badge" id="premium-status" onclick="showPremiumModal()">
                    <i class="fas fa-crown"></i> <span id="premium-text">FREE</span>
                </div>
                <button class="tool-btn" onclick="connectTelegram()" style="background: #0088cc;">
                    <i class="fab fa-telegram"></i> Connect
                </button>
                <button class="tool-btn" onclick="showSettings()">
                    <i class="fas fa-cog"></i>
                </button>
            </div>
        </div>
        
        <!-- Editor Layout -->
        <div class="editor-layout">
            <!-- Left Tools Panel -->
            <div class="tools-panel">
                <h3><i class="fas fa-magic"></i> Editing Tools <span style="font-size: 12px;">(40+)</span></h3>
                <div class="tools-grid" id="tools-grid">
                    <!-- Tools will be populated by JS -->
                </div>
            </div>
            
            <!-- Center Preview Area -->
            <div class="preview-area">
                <div class="preview-header">
                    <span><i class="fas fa-eye"></i> Live Preview</span>
                    <span id="file-info"><i class="fas fa-info-circle"></i> No file selected</span>
                    <span id="processing-status" style="color: #667eea;"><i class="fas fa-spinner fa-spin"></i> Ready</span>
                </div>
                <div class="preview-container">
                    <canvas id="preview-canvas" style="display: none;"></canvas>
                    <video id="preview-video" style="display: none;" controls></video>
                    <div id="no-file-message" style="text-align: center; padding: 60px;">
                        <i class="fas fa-upload" style="font-size: 48px; opacity: 0.5; margin-bottom: 20px; display: block;"></i>
                        <p>Upload an image or video to start editing</p>
                        <button class="control-btn control-btn-primary" onclick="uploadFile()" style="margin-top: 20px;">
                            <i class="fas fa-cloud-upload-alt"></i> Choose File
                        </button>
                    </div>
                </div>
                <div class="controls">
                    <button class="control-btn" onclick="uploadFile()">
                        <i class="fas fa-upload"></i> Upload
                    </button>
                    <button class="control-btn control-btn-primary" onclick="applyCurrentEffect()">
                        <i class="fas fa-magic"></i> Apply
                    </button>
                    <button class="control-btn" onclick="exportFile()">
                        <i class="fas fa-download"></i> Export
                    </button>
                    <button class="control-btn" onclick="resetEdit()">
                        <i class="fas fa-undo"></i> Reset
                    </button>
                    <button class="control-btn" onclick="addToTimeline()">
                        <i class="fas fa-plus-circle"></i> Add to Timeline
                    </button>
                </div>
                <div class="progress-bar" id="progress-bar" style="display: none;">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
            </div>
            
            <!-- Right Filters Panel -->
            <div class="filters-panel">
                <h3><i class="fas fa-palette"></i> Professional Filters <span style="font-size: 12px;">(50+)</span></h3>
                <div class="filters-grid" id="filters-grid">
                    <!-- Filters will be populated by JS -->
                </div>
            </div>
        </div>
        
        <!-- Timeline Area -->
        <div class="timeline-area">
            <div class="timeline-header">
                <h3><i class="fas fa-chart-line"></i> Timeline Editor</h3>
                <div>
                    <button class="tool-btn" onclick="exportTimeline()">
                        <i class="fas fa-film"></i> Export Timeline
                    </button>
                    <button class="tool-btn" onclick="clearTimeline()">
                        <i class="fas fa-trash"></i> Clear All
                    </button>
                </div>
            </div>
            <div class="timeline-container">
                <div class="timeline-track" id="timeline-track">
                    <div style="text-align: center; padding: 30px; color: rgba(255,255,255,0.5);">
                        <i class="fas fa-clock"></i> Timeline empty - Add clips to start editing
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Toast Notification -->
    <div id="toast" class="toast" style="display: none;">
        <i class="fas fa-check-circle"></i>
        <span id="toast-message"></span>
    </div>
    
    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <h3 id="modal-title" style="margin-bottom: 15px;"></h3>
            <p id="modal-message" style="line-height: 1.6;"></p>
            <div style="margin-top: 25px; text-align: center;">
                <button class="control-btn" onclick="closeModal()" style="background: #667eea;">Close</button>
            </div>
        </div>
    </div>
    
    <script>
        // ============================================
        // GLOBAL VARIABLES
        // ============================================
        let currentFile = null;
        let currentFileType = null;
        let originalImageData = null;
        let currentImageData = null;
        let timelineClips = [];
        let selectedClip = null;
        let telegramConnected = false;
        let userData = null;
        let currentFilter = null;
        let currentTool = null;
        let socket = null;
        let isProcessing = false;
        
        // ============================================
        // TOOLS LIST (40+)
        // ============================================
        const tools = [
            { name: "Trim", icon: "fa-cut", category: "video" },
            { name: "Crop", icon: "fa-crop", category: "both" },
            { name: "Resize", icon: "fa-expand", category: "both" },
            { name: "Rotate", icon: "fa-rotate-right", category: "both" },
            { name: "Flip Horizontal", icon: "fa-arrows-left-right", category: "both" },
            { name: "Flip Vertical", icon: "fa-arrows-up-down", category: "both" },
            { name: "Speed", icon: "fa-gauge-high", category: "video" },
            { name: "Reverse", icon: "fa-arrow-rotate-left", category: "video" },
            { name: "Brightness", icon: "fa-sun", category: "image" },
            { name: "Contrast", icon: "fa-circle-half-stroke", category: "image" },
            { name: "Saturation", icon: "fa-droplet", category: "image" },
            { name: "Blur", icon: "fa-blur", category: "both" },
            { name: "Sharpen", icon: "fa-eye", category: "both" },
            { name: "Glitch", icon: "fa-bolt", category: "both" },
            { name: "Vintage", icon: "fa-clock", category: "image" },
            { name: "Watermark", icon: "fa-water", category: "both" },
            { name: "Text Overlay", icon: "fa-font", category: "both" },
            { name: "Noise Reduction", icon: "fa-volume-down", category: "video" },
            { name: "Color Balance", icon: "fa-palette", category: "image" },
            { name: "Exposure", icon: "fa-camera", category: "image" },
            { name: "Gamma", icon: "fa-chart-line", category: "image" },
            { name: "HDR", icon: "fa-sun", category: "image" },
            { name: "Fade In", icon: "fa-fade", category: "video" },
            { name: "Fade Out", icon: "fa-fade", category: "video" },
            { name: "Transition", icon: "fa-arrow-right-arrow-left", category: "video" },
            { name: "Picture in Picture", icon: "fa-window-maximize", category: "video" },
            { name: "Split Screen", icon: "fa-table-cells", category: "video" },
            { name: "Slow Motion", icon: "fa-snail", category: "video" },
            { name: "Fast Motion", icon: "fa-rabbit", category: "video" },
            { name: "Zoom", icon: "fa-magnifying-glass-plus", category: "both" },
            { name: "Pan", icon: "fa-arrows-up-down-left-right", category: "both" },
            { name: "Ken Burns", icon: "fa-film", category: "both" },
            { name: "Chroma Key", icon: "fa-chrome", category: "video", premium: true },
            { name: "Motion Tracking", icon: "fa-location-dot", category: "video", premium: true },
            { name: "Auto Captions", icon: "fa-closed-captioning", category: "video", premium: true },
            { name: "Voiceover", icon: "fa-microphone", category: "video", premium: true },
            { name: "Background Removal", icon: "fa-eraser", category: "image", premium: true }
        ];
        
        // ============================================
        // FILTERS LIST (50+)
        // ============================================
        const filters = [
            "Grayscale", "Sepia", "Invert", "Emboss", "Sharpen", "Blur", "Smooth",
            "Edge Enhance", "Contour", "Detail", "Vintage", "Cool", "Warm", "Noir",
            "Pastel", "Sunset", "Ocean", "Forest", "Autumn", "Spring", "Oil Paint",
            "Watercolor", "Pencil Sketch", "Cartoon", "Pixelate", "Glitch", "VHS",
            "Halftone", "Mosaic", "Stained Glass", "Bokeh", "Lens Flare", "Vignette",
            "Gradient Map", "Dual Tone", "Cross Process", "HDR", "Dramatic", "Dreamy",
            "Cinematic", "Neon", "Glow", "Sparkle", "Rainbow", "Prism", "Mirror",
            "Kaleidoscope", "Fisheye", "Tilt Shift", "Miniature"
        ];
        
        // ============================================
        // INITIALIZATION
        // ============================================
        window.onload = function() {
            // Simulate loading progress
            let progress = 0;
            const loadingStatus = document.getElementById('loading-status');
            const statusMessages = [
                "Loading editing engine...",
                "Initializing 50+ filters...",
                "Loading 40+ tools...",
                "Setting up timeline editor...",
                "Connecting to server...",
                "Almost ready..."
            ];
            
            let msgIndex = 0;
            const interval = setInterval(() => {
                progress += 5;
                if (progress <= 100) {
                    if (msgIndex < statusMessages.length && progress % 15 === 0) {
                        loadingStatus.textContent = statusMessages[msgIndex];
                        msgIndex++;
                    }
                } else {
                    clearInterval(interval);
                    setTimeout(() => {
                        document.getElementById('loader').style.opacity = '0';
                        setTimeout(() => {
                            document.getElementById('loader').style.display = 'none';
                            document.getElementById('main-content').style.display = 'block';
                            showToast('Welcome to Kinva Master Pro!', 'success');
                        }, 500);
                    }, 500);
                }
            }, 80);
            
            // Load tools and filters
            loadTools();
            loadFilters();
            
            // Initialize Socket.IO
            initSocket();
            
            // Check Telegram connection
            checkTelegramConnection();
        };
        
        function initSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('Connected to server');
                showToast('Real-time connection established', 'success');
            });
            
            socket.on('processing_update', (data) => {
                document.getElementById('processing-status').innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${data.message}`;
                if (data.progress) {
                    document.getElementById('progress-bar').style.display = 'block';
                    document.getElementById('progress-fill').style.width = data.progress + '%';
                }
            });
            
            socket.on('processing_complete', (data) => {
                document.getElementById('processing-status').innerHTML = '<i class="fas fa-check-circle"></i> Complete';
                document.getElementById('progress-bar').style.display = 'none';
                showToast('Processing complete!', 'success');
                
                if (data.url) {
                    window.open(data.url, '_blank');
                }
            });
            
            socket.on('processing_error', (data) => {
                document.getElementById('processing-status').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                document.getElementById('progress-bar').style.display = 'none';
                showToast('Error: ' + data.message, 'error');
            });
        }
        
        function loadTools() {
            const container = document.getElementById('tools-grid');
            container.innerHTML = '';
            
            tools.forEach(tool => {
                const btn = document.createElement('button');
                btn.className = 'tool-btn';
                let premiumBadge = tool.premium ? '<span style="font-size: 10px; background: #f5576c; padding: 2px 6px; border-radius: 10px; margin-left: 5px;">⭐</span>' : '';
                btn.innerHTML = `<i class="fas ${tool.icon}"></i> ${tool.name}${premiumBadge}`;
                btn.onclick = () => applyTool(tool.name.toLowerCase().replace(/ /g, '_'));
                container.appendChild(btn);
            });
        }
        
        function loadFilters() {
            const container = document.getElementById('filters-grid');
            container.innerHTML = '';
            
            filters.forEach((filter, index) => {
                const filterDiv = document.createElement('div');
                filterDiv.className = 'filter-item';
                // Generate gradient preview
                const hue = (index * 7) % 360;
                filterDiv.innerHTML = `
                    <div class="filter-preview" style="background: linear-gradient(135deg, hsl(${hue}, 70%, 60%), hsl(${hue + 40}, 70%, 50%));"></div>
                    <div class="filter-name">${filter}</div>
                `;
                filterDiv.onclick = () => applyFilter(filter.toLowerCase().replace(/ /g, '_'));
                container.appendChild(filterDiv);
            });
        }
        
        // ============================================
        // FILE HANDLING
        // ============================================
        function uploadFile() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*,video/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    currentFile = file;
                    currentFileType = file.type.startsWith('image/') ? 'image' : 'video';
                    showToast(`Loaded: ${file.name}`, 'success');
                    
                    // Hide no file message
                    document.getElementById('no-file-message').style.display = 'none';
                    
                    if (currentFileType === 'image') {
                        document.getElementById('preview-canvas').style.display = 'block';
                        document.getElementById('preview-video').style.display = 'none';
                        
                        const reader = new FileReader();
                        reader.onload = (event) => {
                            const img = new Image();
                            img.onload = () => {
                                const canvas = document.getElementById('preview-canvas');
                                canvas.width = img.width;
                                canvas.height = img.height;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                                currentImageData = originalImageData;
                                
                                document.getElementById('file-info').innerHTML = 
                                    `<i class="fas fa-image"></i> ${file.name} (${img.width}x${img.height})`;
                            };
                            img.src = event.target.result;
                        };
                        reader.readAsDataURL(file);
                    } else {
                        document.getElementById('preview-canvas').style.display = 'none';
                        document.getElementById('preview-video').style.display = 'block';
                        
                        const url = URL.createObjectURL(file);
                        const video = document.getElementById('preview-video');
                        video.src = url;
                        video.style.display = 'block';
                        
                        document.getElementById('file-info').innerHTML = 
                            `<i class="fas fa-video"></i> ${file.name}`;
                    }
                }
            };
            input.click();
        }
        
        // ============================================
        // TOOL ACTIONS
        // ============================================
        function applyTool(toolName) {
            if (!currentFile) {
                showToast('Please upload a file first!', 'error');
                return;
            }
            
            if (currentFileType === 'image' && !currentImageData) {
                showToast('No image data available!', 'error');
                return;
            }
            
            showToast(`Applying: ${toolName}...`, 'info');
            currentTool = toolName;
            
            const canvas = document.getElementById('preview-canvas');
            const ctx = canvas.getContext('2d');
            
            switch(toolName) {
                case 'grayscale':
                    applyGrayscale(ctx, canvas);
                    break;
                case 'sepia':
                    applySepia(ctx, canvas);
                    break;
                case 'invert':
                    applyInvert(ctx, canvas);
                    break;
                case 'blur':
                    applyBlur(ctx, canvas);
                    break;
                case 'sharpen':
                    applySharpen(ctx, canvas);
                    break;
                case 'brightness':
                    adjustBrightness(ctx, canvas, 1.2);
                    break;
                case 'contrast':
                    adjustContrast(ctx, canvas, 1.2);
                    break;
                case 'saturation':
                    adjustSaturation(ctx, canvas, 1.3);
                    break;
                case 'rotate':
                    rotateImage(ctx, canvas, 90);
                    break;
                case 'flip_horizontal':
                    flipImage(ctx, canvas, 'horizontal');
                    break;
                case 'flip_vertical':
                    flipImage(ctx, canvas, 'vertical');
                    break;
                case 'resize':
                    showModal('Resize', 'Enter new dimensions:');
                    break;
                case 'crop':
                    showModal('Crop', 'Click and drag to select crop area');
                    break;
                default:
                    showToast(`Tool: ${toolName}`, 'info');
            }
            
            showToast(`Applied: ${toolName}`, 'success');
        }
        
        function applyGrayscale(ctx, canvas) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                const gray = (data[i] + data[i+1] + data[i+2]) / 3;
                data[i] = gray;
                data[i+1] = gray;
                data[i+2] = gray;
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function applySepia(ctx, canvas) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i];
                const g = data[i+1];
                const b = data[i+2];
                data[i] = Math.min(255, r * 0.393 + g * 0.769 + b * 0.189);
                data[i+1] = Math.min(255, r * 0.349 + g * 0.686 + b * 0.168);
                data[i+2] = Math.min(255, r * 0.272 + g * 0.534 + b * 0.131);
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function applyInvert(ctx, canvas) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                data[i] = 255 - data[i];
                data[i+1] = 255 - data[i+1];
                data[i+2] = 255 - data[i+2];
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function applyBlur(ctx, canvas) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            const width = canvas.width;
            const height = canvas.height;
            const temp = new Uint8ClampedArray(data);
            
            for (let y = 1; y < height - 1; y++) {
                for (let x = 1; x < width - 1; x++) {
                    let r = 0, g = 0, b = 0;
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4;
                            r += temp[idx];
                            g += temp[idx + 1];
                            b += temp[idx + 2];
                        }
                    }
                    const idx = (y * width + x) * 4;
                    data[idx] = r / 9;
                    data[idx + 1] = g / 9;
                    data[idx + 2] = b / 9;
                }
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function applySharpen(ctx, canvas) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            const width = canvas.width;
            const height = canvas.height;
            const temp = new Uint8ClampedArray(data);
            
            const kernel = [
                [-1, -1, -1],
                [-1,  9, -1],
                [-1, -1, -1]
            ];
            
            for (let y = 1; y < height - 1; y++) {
                for (let x = 1; x < width - 1; x++) {
                    let r = 0, g = 0, b = 0;
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * width + (x + kx)) * 4;
                            const weight = kernel[ky + 1][kx + 1];
                            r += temp[idx] * weight;
                            g += temp[idx + 1] * weight;
                            b += temp[idx + 2] * weight;
                        }
                    }
                    const idx = (y * width + x) * 4;
                    data[idx] = Math.min(255, Math.max(0, r));
                    data[idx + 1] = Math.min(255, Math.max(0, g));
                    data[idx + 2] = Math.min(255, Math.max(0, b));
                }
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function adjustBrightness(ctx, canvas, factor) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                data[i] = Math.min(255, data[i] * factor);
                data[i+1] = Math.min(255, data[i+1] * factor);
                data[i+2] = Math.min(255, data[i+2] * factor);
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function adjustContrast(ctx, canvas, factor) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                data[i] = Math.min(255, Math.max(0, (data[i] - 128) * factor + 128));
                data[i+1] = Math.min(255, Math.max(0, (data[i+1] - 128) * factor + 128));
                data[i+2] = Math.min(255, Math.max(0, (data[i+2] - 128) * factor + 128));
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function adjustSaturation(ctx, canvas, factor) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                const gray = (data[i] + data[i+1] + data[i+2]) / 3;
                data[i] = Math.min(255, gray + (data[i] - gray) * factor);
                data[i+1] = Math.min(255, gray + (data[i+1] - gray) * factor);
                data[i+2] = Math.min(255, gray + (data[i+2] - gray) * factor);
            }
            
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
        }
        
        function rotateImage(ctx, canvas, angle) {
            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            
            if (angle === 90 || angle === 270) {
                tempCanvas.width = canvas.height;
                tempCanvas.height = canvas.width;
            } else {
                tempCanvas.width = canvas.width;
                tempCanvas.height = canvas.height;
            }
            
            tempCtx.translate(tempCanvas.width / 2, tempCanvas.height / 2);
            tempCtx.rotate(angle * Math.PI / 180);
            tempCtx.drawImage(canvas, -canvas.width / 2, -canvas.height / 2);
            
            canvas.width = tempCanvas.width;
            canvas.height = tempCanvas.height;
            ctx.drawImage(tempCanvas, 0, 0);
            
            currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        }
        
        function flipImage(ctx, canvas, direction) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            if (direction === 'horizontal') {
                ctx.translate(canvas.width, 0);
                ctx.scale(-1, 1);
            } else {
                ctx.translate(0, canvas.height);
                ctx.scale(1, -1);
            }
            
            ctx.putImageData(imageData, 0, 0);
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            
            currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        }
        
        function applyFilter(filterName) {
            if (!currentFile || currentFileType !== 'image') {
                showToast('Please upload an image first!', 'error');
                return;
            }
            
            showToast(`Applying filter: ${filterName}...`, 'info');
            
            const canvas = document.getElementById('preview-canvas');
            const ctx = canvas.getContext('2d');
            
            switch(filterName) {
                case 'grayscale':
                    applyGrayscale(ctx, canvas);
                    break;
                case 'sepia':
                    applySepia(ctx, canvas);
                    break;
                case 'invert':
                    applyInvert(ctx, canvas);
                    break;
                case 'blur':
                    applyBlur(ctx, canvas);
                    break;
                case 'sharpen':
                    applySharpen(ctx, canvas);
                    break;
                case 'vintage':
                    applyVintage(ctx, canvas);
                    break;
                case 'cool':
                    adjustSaturation(ctx, canvas, 1.2);
                    adjustContrast(ctx, canvas, 1.1);
                    break;
                case 'warm':
                    adjustSaturation(ctx, canvas, 0.8);
                    adjustContrast(ctx, canvas, 1.2);
                    break;
                case 'noir':
                    applyGrayscale(ctx, canvas);
                    adjustContrast(ctx, canvas, 1.5);
                    break;
                default:
                    showToast(`Filter: ${filterName}`, 'info');
            }
            
            showToast(`Applied: ${filterName} filter!`, 'success');
        }
        
        function applyVintage(ctx, canvas) {
            adjustSaturation(ctx, canvas, 0.8);
            adjustContrast(ctx, canvas, 1.2);
            applyBlur(ctx, canvas);
        }
        
        function applyCurrentEffect() {
            if (currentTool) {
                applyTool(currentTool);
            } else if (currentFilter) {
                applyFilter(currentFilter);
            } else {
                showToast('Select a tool or filter first!', 'info');
            }
        }
        
        // ============================================
        // TIMELINE FUNCTIONS
        // ============================================
        function addToTimeline() {
            if (!currentImageData && !currentFile) {
                showToast('No file to add to timeline!', 'error');
                return;
            }
            
            const clip = {
                id: Date.now(),
                type: currentFileType,
                data: currentFileType === 'image' ? currentImageData : currentFile,
                timestamp: new Date().toLocaleTimeString(),
                name: currentFile ? currentFile.name : 'Untitled'
            };
            
            timelineClips.push(clip);
            updateTimeline();
            showToast('Added to timeline!', 'success');
            
            // Send to server for processing
            if (socket) {
                socket.emit('add_to_timeline', {
                    clip_id: clip.id,
                    type: clip.type
                });
            }
        }
        
        function updateTimeline() {
            const container = document.getElementById('timeline-track');
            if (timelineClips.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 30px; color: rgba(255,255,255,0.5);"><i class="fas fa-clock"></i> Timeline empty - Add clips to start editing</div>';
                return;
            }
            
            container.innerHTML = '';
            
            timelineClips.forEach((clip, index) => {
                const clipDiv = document.createElement('div');
                clipDiv.className = `timeline-clip ${selectedClip === index ? 'selected' : ''}`;
                clipDiv.innerHTML = `
                    <i class="fas ${clip.type === 'image' ? 'fa-image' : 'fa-video'}"></i>
                    <div style="font-size: 11px; margin-top: 5px; overflow: hidden; text-overflow: ellipsis;">${clip.name.substring(0, 15)}</div>
                    <div style="font-size: 9px; opacity: 0.7;">${clip.timestamp}</div>
                    <button onclick="removeFromTimeline(${index})" style="position: absolute; top: -8px; right: -8px; background: #f5576c; border: none; border-radius: 50%; width: 20px; height: 20px; color: white; cursor: pointer; font-size: 12px;">×</button>
                `;
                clipDiv.onclick = (e) => {
                    e.stopPropagation();
                    selectClip(index);
                };
                container.appendChild(clipDiv);
            });
        }
        
        function selectClip(index) {
            selectedClip = index;
            updateTimeline();
            
            const clip = timelineClips[index];
            if (clip) {
                showToast(`Selected: ${clip.name}`, 'success');
                
                // Load clip into preview
                if (clip.type === 'image' && clip.data) {
                    const canvas = document.getElementById('preview-canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = clip.data.width;
                    canvas.height = clip.data.height;
                    ctx.putImageData(clip.data, 0, 0);
                    currentImageData = clip.data;
                    document.getElementById('preview-canvas').style.display = 'block';
                    document.getElementById('preview-video').style.display = 'none';
                }
            }
        }
        
        function removeFromTimeline(index) {
            timelineClips.splice(index, 1);
            if (selectedClip === index) {
                selectedClip = null;
            } else if (selectedClip > index) {
                selectedClip--;
            }
            updateTimeline();
            showToast('Clip removed from timeline', 'info');
        }
        
        function clearTimeline() {
            if (confirm('Clear entire timeline? This cannot be undone.')) {
                timelineClips = [];
                selectedClip = null;
                updateTimeline();
                showToast('Timeline cleared', 'info');
            }
        }
        
        function exportTimeline() {
            if (timelineClips.length === 0) {
                showToast('Timeline is empty!', 'error');
                return;
            }
            
            showToast('Exporting timeline...', 'info');
            
            // Send timeline to server for processing
            if (socket) {
                socket.emit('export_timeline', {
                    clips: timelineClips.map(clip => ({
                        id: clip.id,
                        type: clip.type
                    }))
                });
            }
        }
        
        // ============================================
        // EXPORT FUNCTIONS
        // ============================================
        function exportFile() {
            if (!currentImageData && !currentFile) {
                showToast('No file to export!', 'error');
                return;
            }
            
            if (currentFileType === 'image') {
                const canvas = document.getElementById('preview-canvas');
                const link = document.createElement('a');
                link.download = `kinva_edit_${Date.now()}.png`;
                link.href = canvas.toDataURL();
                link.click();
                showToast('Image exported successfully!', 'success');
            } else {
                showToast('Video export feature coming soon!', 'info');
            }
        }
        
        function resetEdit() {
            if (originalImageData) {
                const canvas = document.getElementById('preview-canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = originalImageData.width;
                canvas.height = originalImageData.height;
                ctx.putImageData(originalImageData, 0, 0);
                currentImageData = originalImageData;
                showToast('Reset to original!', 'success');
            } else {
                showToast('No changes to reset', 'info');
            }
        }
        
        // ============================================
        // TELEGRAM CONNECTION
        // ============================================
        function connectTelegram() {
            const botId = '{{ BOT_ID }}';
            const redirectUrl = encodeURIComponent(window.location.href);
            const telegramAuthUrl = `https://oauth.telegram.org/auth?bot_id=${botId}&origin=${encodeURIComponent(window.location.origin)}&return_to=${redirectUrl}`;
            window.open(telegramAuthUrl, '_blank', 'width=600,height=600');
            showToast('Connecting to Telegram...', 'info');
        }
        
        function checkTelegramConnection() {
            const params = new URLSearchParams(window.location.search);
            const authData = params.get('tg_auth');
            
            if (authData) {
                telegramConnected = true;
                document.getElementById('premium-text').textContent = 'PREMIUM';
                document.getElementById('premium-status').style.background = 'linear-gradient(135deg, #4caf50, #45a049)';
                showToast('Connected to Telegram! Premium activated!', 'success');
                
                // Remove auth param from URL
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        }
        
        function showPremiumModal() {
            const isPremium = telegramConnected;
            if (isPremium) {
                showModal('Premium Member', 'Thank you for being a premium member! You have access to all features including:\n• 4K Export\n• No Watermark\n• Priority Processing\n• All Filters & Tools');
            } else {
                showModal('Upgrade to Premium', 'Get access to exclusive features:\n⭐ 4K Export\n⭐ No Watermark\n⭐ Priority Queue\n⭐ All Filters\n⭐ Motion Tracking\n⭐ Chroma Key\n\nPrice: $9.99/month or 100 Stars\n\nConnect Telegram to activate!');
            }
        }
        
        function showSettings() {
            showModal('Settings', '⚙️ Editor Settings:\n• Quality: High\n• Export Format: PNG/MP4\n• Default Filters: On\n• Auto-save: Off\n\nMore features coming soon!');
        }
        
        // ============================================
        // UI HELPER FUNCTIONS
        // ============================================
        function showToast(message, type = 'info') {
            const toast = document.getElementById('toast');
            const toastMessage = document.getElementById('toast-message');
            const icon = toast.querySelector('i');
            
            toastMessage.textContent = message;
            
            if (type === 'success') {
                icon.className = 'fas fa-check-circle';
                toast.style.borderLeftColor = '#4caf50';
            } else if (type === 'error') {
                icon.className = 'fas fa-times-circle';
                toast.style.borderLeftColor = '#f44336';
            } else {
                icon.className = 'fas fa-info-circle';
                toast.style.borderLeftColor = '#667eea';
            }
            
            toast.style.display = 'flex';
            
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => {
                    toast.style.display = 'none';
                    toast.style.opacity = '1';
                }, 300);
            }, 3000);
        }
        
        function showModal(title, message) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;
            document.getElementById('modal').style.display = 'flex';
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        // ============================================
        // KEYBOARD SHORTCUTS
        // ============================================
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                resetEdit();
            } else if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                exportFile();
            } else if (e.key === 'Delete' && selectedClip !== null) {
                removeFromTimeline(selectedClip);
            }
        });
        
        // ============================================
        // DRAG AND DROP
        // ============================================
        const dropZone = document.querySelector('.preview-container');
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.border = '2px dashed #667eea';
        });
        
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.border = 'none';
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.border = 'none';
            const file = e.dataTransfer.files[0];
            if (file && (file.type.startsWith('image/') || file.type.startsWith('video/'))) {
                const inputEvent = { target: { files: [file] } };
                uploadFileFromEvent(inputEvent);
            } else {
                showToast('Please drop an image or video file', 'error');
            }
        });
        
        function uploadFileFromEvent(event) {
            const file = event.target.files[0];
            if (file) {
                currentFile = file;
                currentFileType = file.type.startsWith('image/') ? 'image' : 'video';
                showToast(`Loaded: ${file.name}`, 'success');
                
                document.getElementById('no-file-message').style.display = 'none';
                
                if (currentFileType === 'image') {
                    document.getElementById('preview-canvas').style.display = 'block';
                    document.getElementById('preview-video').style.display = 'none';
                    
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const img = new Image();
                        img.onload = () => {
                            const canvas = document.getElementById('preview-canvas');
                            canvas.width = img.width;
                            canvas.height = img.height;
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(img, 0, 0);
                            originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                            currentImageData = originalImageData;
                            
                            document.getElementById('file-info').innerHTML = 
                                `<i class="fas fa-image"></i> ${file.name} (${img.width}x${img.height})`;
                        };
                        img.src = event.target.result;
                    };
                    reader.readAsDataURL(file);
                } else {
                    document.getElementById('preview-canvas').style.display = 'none';
                    document.getElementById('preview-video').style.display = 'block';
                    
                    const url = URL.createObjectURL(file);
                    const video = document.getElementById('preview-video');
                    video.src = url;
                    video.style.display = 'block';
                    
                    document.getElementById('file-info').innerHTML = 
                        `<i class="fas fa-video"></i> ${file.name}`;
                }
            }
        }
    </script>
</body>
</html>
"""

# ============================================
# FLASK ROUTES
# ============================================

@flask_app.route('/')
def index():
    """Render main web app"""
    bot_id = os.environ.get("BOT_TOKEN", "").split(':')[0] if os.environ.get("BOT_TOKEN") else "YOUR_BOT_ID"
    return render_template_string(WEB_APP_HTML.replace('{{ BOT_ID }}', bot_id))

@flask_app.route('/admin')
def admin_panel():
    """Admin panel with login"""
    password = request.args.get('password', '')
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if password != admin_password:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Login - Kinva Master</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .login-container {
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(20px);
                    border-radius: 30px;
                    padding: 40px;
                    width: 350px;
                    text-align: center;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                h2 {
                    margin-bottom: 30px;
                    color: #fff;
                }
                input {
                    width: 100%;
                    padding: 15px;
                    margin: 10px 0;
                    border: none;
                    border-radius: 15px;
                    background: rgba(255,255,255,0.2);
                    color: #fff;
                    font-size: 16px;
                }
                input::placeholder {
                    color: rgba(255,255,255,0.7);
                }
                button {
                    width: 100%;
                    padding: 15px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 15px;
                    color: #fff;
                    font-size: 16px;
                    cursor: pointer;
                    margin-top: 20px;
                    transition: all 0.3s;
                }
                button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 20px rgba(102,126,234,0.4);
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>🔐 Admin Login</h2>
                <form method="GET">
                    <input type="password" name="password" placeholder="Enter admin password" required>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        '''
    
    # Get database stats
    import sqlite3
    conn = sqlite3.connect('kinva_bot.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    premium_users = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(edits_count) FROM users")
    total_edits = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM edit_history WHERE date(created_at) = date('now')")
    today_edits = c.fetchone()[0] or 0
    
    c.execute("SELECT * FROM users ORDER BY joined_date DESC LIMIT 20")
    users = c.fetchall()
    
    conn.close()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel - Kinva Master</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #fff;
                padding: 20px;
            }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                padding: 25px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .stat-number {{
                font-size: 42px;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .stat-label {{
                margin-top: 10px;
                color: rgba(255,255,255,0.7);
            }}
            .section {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                padding: 25px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            .section h2 {{
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            th {{
                color: #667eea;
                font-weight: 600;
            }}
            .badge {{
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .badge-premium {{ background: #4caf50; }}
            .badge-free {{ background: #ff9800; }}
            .btn {{
                padding: 6px 12px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
            }}
            .btn-primary {{
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }}
            .btn-danger {{
                background: #f44336;
                color: white;
            }}
            .btn:hover {{
                transform: translateY(-2px);
            }}
            @media (max-width: 768px) {{
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                table {{
                    font-size: 12px;
                }}
                th, td {{
                    padding: 8px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Kinva Master Admin Panel</h1>
                <p style="margin-top: 10px; opacity: 0.8;">Welcome back, Administrator! Monitor and manage your editing bot.</p>
                <div style="margin-top: 15px;">
                    <a href="/" style="color: #667eea; text-decoration: none; margin-right: 20px;">← Back to Editor</a>
                    <a href="/logout" style="color: #f44336; text-decoration: none;">Logout</a>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_users}</div>
                    <div class="stat-label">Total Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{premium_users}</div>
                    <div class="stat-label">Premium Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_edits}</div>
                    <div class="stat-label">Total Edits</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{today_edits}</div>
                    <div class="stat-label">Today's Edits</div>
                </div>
            </div>
            
            <div class="section">
                <h2><i class="fas fa-users"></i> Recent Users</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Name</th>
                                <th>Edits</th>
                                <th>Status</th>
                                <th>Joined</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                 # Clean, readable solution
items_html = []
for item in some_list:  # whatever you're iterating over
    items_html.append(f'<div class="{some_function(param1, param2)}">')
result = ''.join(items_html)
                          <tr>
                                <td>{user[0]}</td>
                                <td>@{user[1] or 'N/A'}</td>
                                <td>{user[2] or ''} {user[3] or ''}</td>
                                <td>{user[7] or 0}</td>
                                <td><span class="badge {'badge-premium' if user[5] else 'badge-free'}">{'Premium' if user[5] else 'Free'}</span></td>
                                <td>{user[4][:10] if user[4] else 'N/A'}</td>
                                <td>
                                    <button class="btn btn-primary" onclick="addPremium({user[0]})">Add Premium</button>
                                </td>
                            </tr>
# Replace the incorrect line with this:
'''.join([f'''...''' for user in users])
# ✅ FIRST create app
app = Flask(__name__)

# ✅ THEN define routes
@app.route('/some-page')
def some_function():
    return "OK"
    return """
        </tbody>
    </table>
                </div>
            </div>
        </div>
        
        <script>
            function addPremium(userId) {{
                if(confirm('Add premium to user ' + userId + '?')) {{
                    fetch('/api/add_premium', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{user_id: userId}})
                    }}).then(r => r.json()).then(data => {{
                        if(data.success) location.reload();
                        else alert('Error: ' + data.error);
                    }});
                }}
            }}
        </script>
    </body>
    </html>
    """

@flask_app.route('/logout')
def logout():
    """Logout from admin panel"""
    return redirect('/admin')

@flask_app.route('/api/add_premium', methods=['POST'])
def api_add_premium():
    """API endpoint to add premium to user"""
    data = request.json
    user_id = data.get('user_id')
    
    if user_id:
        try:
            import sqlite3
            conn = sqlite3.connect('kinva_bot.db')
            c = conn.cursor()
            from datetime import datetime, timedelta
            expiry = (datetime.now() + timedelta(days=30)).isoformat()
            c.execute("UPDATE users SET is_premium = 1, premium_expiry = ? WHERE id = ?", (expiry, user_id))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid user ID"}), 400

@flask_app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    import sqlite3
    conn = sqlite3.connect('kinva_bot.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    premium_users = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(edits_count) FROM users")
    total_edits = c.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        "total_users": total_users,
        "premium_users": premium_users,
        "total_edits": total_edits
    })

@flask_app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "features": {
            "video_tools": 40,
            "image_tools": 30,
            "filters": 50
        }
    })

# ============================================
# SOCKET.IO EVENT HANDLERS
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Kinva Master Server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('add_to_timeline')
def handle_add_to_timeline(data):
    """Handle adding clip to timeline"""
    print(f"Adding to timeline: {data}")
    emit('processing_update', {'message': 'Clip added to timeline', 'progress': 30})

@socketio.on('export_timeline')
def handle_export_timeline(data):
    """Handle timeline export"""
    print(f"Exporting timeline: {data}")
    
    # Simulate processing
    for i in range(0, 101, 10):
        time.sleep(0.5)
        emit('processing_update', {'message': f'Processing timeline... {i}%', 'progress': i})
    
    emit('processing_complete', {'message': 'Timeline exported successfully!'})

# ============================================
# PART 6: MAIN EXECUTION & ROUTING
# ============================================

# 1. Define Flask Routes
@app.route('/dashboard')
def dashboard(): # <--- Changed from 'index' to 'dashboard'
    return "Dashboard"
# 2. Function to run Flask in a separate thread
def run_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR) # Hide standard Flask logs to keep console clean
    
    print(f"🌐 Web App running on port {Config.PORT}")
    # allow_unsafe_werkzeug is needed for dev environments when using threading
    socketio.run(flask_app, host="0.0.0.0", port=Config.PORT, allow_unsafe_werkzeug=True)

# 3. Main Function
def main():
    print("🚀 Starting Kinva Master Pro...")
    
    # Start Flask/SocketIO in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True # Daemon thread exits when main program exits
    flask_thread.start()
    
    # Initialize Telegram Bot
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    bot_instance = KinvaMasterBot()
    
    # Register Command Handlers
    application.add_handler(CommandHandler("start", bot_instance.start))
    application.add_handler(CommandHandler("menu", bot_instance.menu_command))
    application.add_handler(CommandHandler("stats", bot_instance.stats_command))
    application.add_handler(CommandHandler("help", bot_instance.help_command))
    application.add_handler(CommandHandler("admin", bot_instance.admin_command))
    
    # Register Message & Callback Handlers
    application.add_handler(CallbackQueryHandler(bot_instance.handle_callback))
    application.add_handler(MessageHandler(filters.PHOTO, bot_instance.handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, bot_instance.handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.handle_text))
    
    # Start Telegram Bot (This blocks the main thread and keeps the script running)
    print("🤖 Telegram Bot is polling for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Ensure directories exist
    Config.setup_directories()
    
    # Run the main function
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        traceback.print_exc()
        updater.start_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 10000)),
    url_path=TOKEN
)

updater.bot.set_webhook(
    url=f"https://Kinva-Master-1.onrender.com/{TOKEN}"
)
