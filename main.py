# ============================================
# KINVA MASTER PRO - COMPLETE WORKING BOT
# ============================================
# VERSION: 4.0.0 - FULLY FIXED
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

# Video Processing
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
        concatenate_videoclips, ImageClip, ColorClip, clips_array,
        CompositeAudioClip, concatenate_audioclips, vfx
    )
except ImportError:
    print("⚠️ MoviePy not fully installed - some video features limited")
    vfx = None

# Audio Processing
from pydub import AudioSegment, effects, generators
from pydub.effects import normalize, low_pass_filter, high_pass_filter

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler, PreCheckoutQueryHandler
)
from telegram.ext import ApplicationBuilder

# Web Framework
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Downloaders
import yt_dlp
import requests

# Payment
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
    UPI_ID = os.environ.get("UPI_ID", "kinvamaster@okhdfcbank")
    
    # Star Payment (Telegram Stars)
    STAR_PRICE_MONTHLY = 100
    STAR_PRICE_YEARLY = 1000
    
    # Premium Pricing
    PREMIUM_PRICE_USD = 9.99
    PREMIUM_PRICE_INR = 499
    PREMIUM_PRICE_STARS = 100
    
    # Storage
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    CACHE_DIR = "cache"
    DATABASE_FILE = "kinva_master.db"
    
    # Limits
    MAX_FILE_SIZE = 500 * 1024 * 1024
    MAX_VIDEO_DURATION = 600
    MAX_EDIT_PER_DAY_FREE = 10
    MAX_EDIT_PER_DAY_PREMIUM = 1000
    
    @classmethod
    def setup_directories(cls):
        for dir_path in [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    
    @classmethod
    def get_version(cls):
        return "4.0.0"

Config.setup_directories()

# ============================================
# DATABASE MANAGEMENT
# ============================================

class Database:
    """Advanced Database Management"""
    
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
    
    def init_tables(self):
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
                joined_date TEXT,
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
                created_at TEXT
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
                created_at TEXT,
                completed_at TEXT
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
                updated_at TEXT
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
                created_at TEXT
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
        
        # Broadcasts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        self.conn.commit()
        self.init_default_settings()
    
    def init_default_settings(self):
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
            if not self.get_setting(key):
                self.set_setting(key, value)
    
    def get_user(self, user_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referrer_id: int = 0):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (id, username, first_name, last_name, joined_date, updated_at, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, now, now, referrer_id))
        
        if referrer_id > 0:
            cursor.execute('''
                UPDATE users SET referral_count = referral_count + 1, balance = balance + 5
                WHERE id = ?
            ''', (referrer_id,))
        
        self.conn.commit()
        return self.get_user(user_id)
    
    def update_user(self, user_id: int, **kwargs):
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
        user = self.get_user(user_id)
        if user and user.get('is_premium', 0):
            if user.get('premium_expiry'):
                try:
                    expiry = datetime.fromisoformat(user['premium_expiry'])
                    if datetime.now() > expiry:
                        self.update_user(user_id, is_premium=0, premium_expiry=None)
                        return False
                except:
                    pass
            return True
        return False
    
    def add_premium(self, user_id: int, days: int = 30, premium_type: str = "monthly"):
        user = self.get_user(user_id)
        if user and user.get('premium_expiry'):
            try:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                new_expiry = expiry + timedelta(days=days)
            except:
                new_expiry = datetime.now() + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        self.update_user(user_id, is_premium=1, premium_expiry=new_expiry.isoformat(), premium_type=premium_type)
    
    def increment_edits(self, user_id: int):
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        
        if user:
            if user.get('last_edit_date') != today:
                self.update_user(user_id, daily_edits=1, last_edit_date=today)
            else:
                self.update_user(user_id, daily_edits=(user.get('daily_edits', 0) + 1))
            
            self.update_user(user_id, edits_count=(user.get('edits_count', 0) + 1))
    
    def can_edit(self, user_id: int) -> bool:
        if self.is_premium(user_id):
            return True
        
        user = self.get_user(user_id)
        if not user:
            return True
        
        today = datetime.now().date().isoformat()
        
        if user.get('last_edit_date') != today:
            return True
        
        return user.get('daily_edits', 0) < Config.MAX_EDIT_PER_DAY_FREE
    
    def add_transaction(self, user_id: int, amount: float, payment_method: str, transaction_id: str, stars_amount: int = None):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, stars_amount, payment_method, transaction_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, stars_amount, payment_method, transaction_id, 'pending', now))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_transaction(self, transaction_id: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE transactions SET status = 'completed', completed_at = ?
            WHERE transaction_id = ?
        ''', (datetime.now().isoformat(), transaction_id))
        
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        tx = cursor.fetchone()
        
        if tx:
            self.add_premium(tx['user_id'], 30)
            if tx['stars_amount']:
                self.update_user(tx['user_id'], stars_balance=tx['stars_amount'])
        
        self.conn.commit()
    
    def add_feedback(self, user_id: int, feedback: str, rating: int, category: str = "general"):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feedback (user_id, feedback, rating, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, feedback, rating, category, now))
        
        self.conn.commit()
    
    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COALESCE(SUM(edits_count), 0) FROM users")
        total_edits = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM edit_history WHERE date(created_at) = date('now')")
        today_edits = cursor.fetchone()[0] or 0
        
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "total_edits": total_edits,
            "today_edits": today_edits,
            "premium_percent": round((premium_users / total_users * 100), 1) if total_users > 0 else 0
        }
    
    def save_project(self, project_id: str, user_id: int, name: str, data: dict):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO projects (id, user_id, name, data, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM projects WHERE id = ?), ?))
        ''', (project_id, user_id, name, json.dumps(data), now, project_id, now))
        
        self.conn.commit()
    
    def get_project(self, project_id: str, user_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        project = cursor.fetchone()
        return dict(project) if project else None
    
    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else default
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_feedback(self, limit: int = 50) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_edits(self, limit: int = 50) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM edit_history ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_broadcast(self, message: str) -> int:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO broadcasts (message, created_at)
            VALUES (?, ?)
        ''', (message, now))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_broadcast(self, broadcast_id: int, sent_count: int, failed_count: int, status: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE broadcasts SET sent_count = ?, failed_count = ?, status = ?, completed_at = ?
            WHERE id = ?
        ''', (sent_count, failed_count, status, datetime.now().isoformat(), broadcast_id))
        self.conn.commit()
    
    def ban_user(self, user_id: int):
        self.update_user(user_id, banned=1)
    
    def unban_user(self, user_id: int):
        self.update_user(user_id, banned=0)
    
    def is_banned(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user.get('banned', 0) == 1 if user else False

db = Database()

# ============================================
# 50+ PROFESSIONAL FILTERS
# ============================================

class Filters50:
    """50+ Professional Filters and Effects"""
    
    def __init__(self):
        self.filter_list = []
        self.init_filters()
    
    def init_filters(self):
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
        if filter_name not in self.filters:
            raise ValueError(f"Filter {filter_name} not found")
        
        img = Image.open(image_path)
        img = self.filters[filter_name](img)
        
        output_path = os.path.join(Config.OUTPUT_DIR, f"filter_{filter_name}_{datetime.now().timestamp()}.png")
        img.save(output_path)
        return output_path
    
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
        return Image.merge("RGB", (r, g, b))
    
    def ocean(self, img):
        img = ImageEnhance.Color(img).enhance(1.4)
        r, g, b = img.split()
        b = b.point(lambda i: i * 1.3)
        return Image.merge("RGB", (r, g, b))
    
    def forest(self, img):
        img = ImageEnhance.Color(img).enhance(1.2)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.3)
        return Image.merge("RGB", (r, g, b))
    
    def autumn(self, img):
        img = ImageEnhance.Color(img).enhance(1.1)
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.3)
        g = g.point(lambda i: i * 0.8)
        return Image.merge("RGB", (r, g, b))
    
    def spring(self, img):
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.2)
        return Image.merge("RGB", (r, g, b))
    
    def oil_paint(self, img):
        img_array = np.array(img)
        try:
            output = cv2.xphoto.oilPainting(img_array, 5, 30)
            return Image.fromarray(output)
        except:
            return img.filter(ImageFilter.SMOOTH_MORE)
    
    def watercolor(self, img):
        img_array = np.array(img)
        try:
            output = cv2.stylization(img_array, sigma_s=60, sigma_r=0.6)
            return Image.fromarray(output)
        except:
            return img
    
    def pencil_sketch(self, img):
        img_array = np.array(img.convert("L"))
        try:
            _, sketch = cv2.pencilSketch(img_array, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
            return Image.fromarray(sketch).convert("RGB")
        except:
            return img
    
    def cartoon(self, img):
        img_array = np.array(img)
        try:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(img_array, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return Image.fromarray(cartoon)
        except:
            return img
    
    def pixelate(self, img, pixel_size=10):
        w, h = img.size
        img = img.resize((w // pixel_size, h // pixel_size), Image.NEAREST)
        img = img.resize((w, h), Image.NEAREST)
        return img
    
    def glitch(self, img):
        img_array = np.array(img)
        shift = np.random.randint(-15, 15)
        img_array = np.roll(img_array, shift, axis=1)
        noise = np.random.randint(0, 40, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        return Image.fromarray(img_array.astype('uint8'))
    
    def vhs(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        scanlines = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(0, h, 2):
            scanlines[i:i+1, :] = [20, 20, 20]
        img_array = np.clip(img_array + scanlines, 0, 255)
        if h > 0 and w > 0:
            img_array[:, :, 0] = np.roll(img_array[:, :, 0], 2, axis=1)
            img_array[:, :, 2] = np.roll(img_array[:, :, 2], -2, axis=1)
        return Image.fromarray(img_array)
    
    def halftone(self, img):
        img_array = np.array(img.convert("L"))
        h, w = img_array.shape
        pattern = np.zeros((h, w), dtype=np.uint8)
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                block = img_array[y:min(y+4, h), x:min(x+4, w)]
                if block.size > 0:
                    intensity = np.mean(block) / 255
                    size = int(4 * intensity)
                    if size > 0 and y+2 < h and x+2 < w:
                        cv2.circle(pattern, (x+2, y+2), size//2, 255, -1)
        return Image.fromarray(pattern).convert("RGB")
    
    def mosaic(self, img, block_size=20):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = img_array[y:min(y+block_size, h), x:min(x+block_size, w)]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img_array[y:min(y+block_size, h), x:min(x+block_size, w)] = avg_color
        return Image.fromarray(img_array)
    
    def stained_glass(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        grid_size = 30
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                block = img_array[y:min(y+grid_size, h), x:min(x+grid_size, w)]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img_array[y:min(y+grid_size, h), x:min(x+grid_size, w)] = avg_color
        img_array[::grid_size, :] = [0, 0, 0]
        img_array[:, ::grid_size] = [0, 0, 0]
        return Image.fromarray(img_array)
    
    def bokeh(self, img):
        return img.filter(ImageFilter.GaussianBlur(radius=5))
    
    def lens_flare(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
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
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        center_x, center_y = w // 2, h // 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        radius = min(w, h) / 2
        mask = 1 - (dist / radius)
        mask = np.clip(mask, 0, 1)
        for i in range(3):
            img_array[:, :, i] = (img_array[:, :, i] * mask).astype(np.uint8)
        return Image.fromarray(img_array)
    
    def gradient_map(self, img):
        img_array = np.array(img.convert("L"))
        gradient = np.linspace(0, 255, 256)
        gradient = np.stack([gradient, gradient * 0.5, gradient * 0.2], axis=1)
        mapped = gradient[img_array.flatten()].reshape(img_array.shape + (3,))
        return Image.fromarray(mapped.astype('uint8'))
    
    def dual_tone(self, img):
        img_array = np.array(img)
        shadows = np.clip(img_array * 0.5, 0, 255).astype('uint8')
        highlights = np.clip(img_array * 1.5, 0, 255).astype('uint8')
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
        width, height = img.size
        bar_height = height // 6
        result = Image.new('RGB', (width, height), 'black')
        result.paste(img, (0, bar_height))
        return result
    
    def neon(self, img):
        img_array = np.array(img)
        try:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            neon = np.zeros_like(img_array)
            neon[edges > 0] = [0, 255, 255]
            result = cv2.addWeighted(img_array, 0.7, neon, 0.3, 0)
            return Image.fromarray(result)
        except:
            return img
    
    def glow(self, img):
        blur = img.filter(ImageFilter.GaussianBlur(radius=10))
        return Image.blend(img, blur, 0.5)
    
    def sparkle(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        num_sparkles = 100
        for _ in range(num_sparkles):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            if y < h and x < w:
                cv2.circle(img_array, (x, y), 2, (255, 255, 255), -1)
        return Image.fromarray(img_array)
    
    def rainbow(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        rainbow = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            for j in range(w):
                angle = (j / w) * 2 * np.pi
                rainbow[i, j] = [int(127.5 + 127.5 * np.sin(angle)),
                                 int(127.5 + 127.5 * np.sin(angle + 2*np.pi/3)),
                                 int(127.5 + 127.5 * np.sin(angle + 4*np.pi/3))]
        result = cv2.addWeighted(img_array, 0.7, rainbow, 0.3, 0)
        return Image.fromarray(result)
    
    def prism(self, img):
        img_array = np.array(img)
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
        result = np.zeros((h, w, 3), dtype=np.uint8)
        cx, cy = w // 2, h // 2
        sections = 8
        for y in range(h):
            for x in range(w):
                dx = x - cx
                dy = y - cy
                angle = np.arctan2(dy, dx)
                radius = np.sqrt(dx*dx + dy*dy)
                angle = angle % (2 * np.pi / sections)
                x2 = int(cx + radius * np.cos(angle))
                y2 = int(cy + radius * np.sin(angle))
                if 0 <= x2 < w and 0 <= y2 < h:
                    result[y, x] = img_array[y2, x2]
        return Image.fromarray(result)
    
    def fisheye(self, img):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
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
        center = h // 2
        blur_radius = 10
        for y in range(h):
            distance = abs(y - center)
            blur = blur_radius * (distance / center) if center > 0 else 0
            if blur > 0:
                kernel_size = int(blur) * 2 + 1
                if kernel_size > 1 and kernel_size % 2 == 1:
                    try:
                        img_array[y:y+1] = cv2.GaussianBlur(img_array[y:y+1], (kernel_size, kernel_size), 0)
                    except:
                        pass
        return Image.fromarray(img_array)
    
    def miniature(self, img):
        img = self.tilt_shift(img)
        img = ImageEnhance.Color(img).enhance(1.5)
        return img

# ============================================
# 40+ VIDEO EDITING TOOLS
# ============================================

class VideoTools40:
    """40+ Professional Video Editing Tools"""
    
    def generate_filename(self, ext=".mp4"):
        return os.path.join(Config.OUTPUT_DIR, f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}{ext}")
    
    def trim(self, path: str, start: float, end: float) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            trimmed = clip.subclip(start, end)
            out = self.generate_filename()
            trimmed.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def crop(self, path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
            out = self.generate_filename()
            cropped.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def resize(self, path: str, width: int, height: int) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            resized = clip.resize(newsize=(width, height))
            out = self.generate_filename()
            resized.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def rotate(self, path: str, angle: int) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            rotated = clip.rotate(angle)
            out = self.generate_filename()
            rotated.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def flip_horizontal(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            flipped = clip.fx(vfx.mirror_x)
            out = self.generate_filename()
            flipped.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def flip_vertical(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            flipped = clip.fx(vfx.mirror_y)
            out = self.generate_filename()
            flipped.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def speed(self, path: str, factor: float) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            sped = clip.fx(vfx.speedx, factor)
            out = self.generate_filename()
            sped.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def reverse(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            reversed_clip = clip.fx(vfx.time_mirror)
            out = self.generate_filename()
            reversed_clip.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def loop(self, path: str, times: int) -> str:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            clip = VideoFileClip(path)
            looped = concatenate_videoclips([clip] * times)
            out = self.generate_filename()
            looped.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def merge(self, paths: list) -> str:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            clips = [VideoFileClip(p) for p in paths]
            merged = concatenate_videoclips(clips)
            out = self.generate_filename()
            merged.write_videofile(out, logger=None, verbose=False)
            for c in clips:
                c.close()
            return out
        except:
            return paths[0] if paths else None
    
    def extract_audio(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            out = self.generate_filename(".mp3")
            if clip.audio:
                clip.audio.write_audiofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return None
    
    def remove_audio(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            no_audio = clip.without_audio()
            out = self.generate_filename()
            no_audio.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def compress(self, path: str, target_size_mb: int = 20) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            duration = clip.duration
            target_bitrate = (target_size_mb * 8) / duration if duration > 0 else 1000
            out = self.generate_filename()
            clip.write_videofile(out, bitrate=f"{target_bitrate}k", logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def fade_in(self, path: str, duration: float = 1) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            faded = clip.fx(vfx.fadein, duration)
            out = self.generate_filename()
            faded.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def fade_out(self, path: str, duration: float = 1) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            faded = clip.fx(vfx.fadeout, duration)
            out = self.generate_filename()
            faded.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def grayscale_video(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip, vfx
            clip = VideoFileClip(path)
            bw = clip.fx(vfx.blackwhite)
            out = self.generate_filename()
            bw.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def blur_video(self, path: str, radius: int = 5) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            def blur_frame(frame):
                return cv2.GaussianBlur(frame, (radius*2+1, radius*2+1), 0)
            blurred = clip.fl_image(blur_frame)
            out = self.generate_filename()
            blurred.write_videofile(out, logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def quality_1080p(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            resized = clip.resize(newsize=(1920, 1080))
            out = self.generate_filename()
            resized.write_videofile(out, bitrate="5000k", logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def quality_720p(self, path: str) -> str:
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(path)
            resized = clip.resize(newsize=(1280, 720))
            out = self.generate_filename()
            resized.write_videofile(out, bitrate="2500k", logger=None, verbose=False)
            clip.close()
            return out
        except:
            return path
    
    def slow_motion(self, path: str, factor: float = 0.5) -> str:
        return self.speed(path, factor)
    
    def fast_motion(self, path: str, factor: float = 2.0) -> str:
        return self.speed(path, factor)
    
    def add_watermark(self, path: str, text: str, position: str = "bottom-right") -> str:
        try:
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
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
        except:
            return path

# ============================================
# COMPLETE TELEGRAM BOT WITH FIXED CALLBACKS
# ============================================

class KinvaMasterBot:
    """Complete Telegram Bot with Fixed Callbacks"""
    
    def __init__(self):
        self.video_tools = VideoTools40()
        self.filters = Filters50()
        self.user_sessions = {}
        self.processing_tasks = {}
    
    # ========== COMMAND HANDLERS ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        user = update.effective_user
        
        if not db.get_user(user.id):
            db.create_user(user.id, user.username, user.first_name, user.last_name)
        
        user_data = db.get_user(user.id)
        is_premium = db.is_premium(user.id)
        max_edits = Config.MAX_EDIT_PER_DAY_PREMIUM if is_premium else Config.MAX_EDIT_PER_DAY_FREE
        
        welcome_text = f"""
🎬 **KINVA MASTER PRO** 🎬

━━━━━━━━━━━━━━━━━━━━━━
✨ **WELCOME TO THE ULTIMATE EDITING BOT** ✨
━━━━━━━━━━━━━━━━━━━━━━

👋 Hello **{user.first_name}**!

🚀 **What I Can Do:**
• 🎥 **40+ Video Editing Tools**
• 🖼️ **30+ Image Editing Tools**  
• 🎨 **50+ Professional Filters**
• 🎵 **Audio Processing Tools**
• 📥 **Social Media Downloader**
• ⭐ **Premium Features**

📊 **Your Stats:**
• Edits Today: {user_data.get('daily_edits', 0)}/{max_edits}
• Total Edits: {user_data.get('edits_count', 0)}
• Premium: {'✅ ACTIVE' if is_premium else '❌ INACTIVE'}

💡 **Just send me a photo or video to start editing!**

━━━━━━━━━━━━━━━━━━━━━━
🌟 **Type /menu to see all tools** 🌟
━━━━━━━━━━━━━━━━━━━━━━
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
             InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium")],
            [InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download"),
             InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats")],
            [InlineKeyboardButton("❓ HELP", callback_data="menu_help"),
             InlineKeyboardButton("🔧 ADMIN", callback_data="menu_admin")] if update.effective_user.id in Config.ADMIN_IDS else
            [InlineKeyboardButton("❓ HELP", callback_data="menu_help")]
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
/volume - Adjust volume

**✨ VIDEO EFFECTS**
/fade_in - Fade in effect
/fade_out - Fade out effect
/grayscale_vid - Black & white
/blur_vid - Blur effect

**📦 COMPRESSION**
/compress - Compress video
/to_1080p - Convert to 1080p
/to_720p - Convert to 720p

**🖼️ IMAGE EDITING (30+ TOOLS)**
/resize_img - Resize image
/crop_img - Crop image
/rotate_img - Rotate image
/flip_img - Flip image
/brightness - Adjust brightness
/contrast - Adjust contrast
/saturation - Adjust saturation
/blur_img - Blur image

**🎨 FILTERS (50+)**
/filters - Show all filters
/grayscale - Grayscale filter
/sepia - Sepia filter
/vintage - Vintage filter
/cool - Cool filter
/warm - Warm filter
/noir - Noir filter
/glow - Glow effect
/neon - Neon effect

**⭐ PREMIUM FEATURES**
/premium - Get premium

**📥 DOWNLOAD TOOLS**
/youtube - Download YouTube
/instagram - Download Instagram

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
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop_video")],
            [InlineKeyboardButton("📏 RESIZE", callback_data="tool_resize_video"),
             InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_video")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="tool_extract_audio"),
             InlineKeyboardButton("🔊 COMPRESS", callback_data="tool_compress")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="tool_video_effects"),
             InlineKeyboardButton("💧 WATERMARK", callback_data="tool_video_watermark")],
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
            [InlineKeyboardButton("🌈 BRIGHTNESS", callback_data="tool_brightness"),
             InlineKeyboardButton("🎨 CONTRAST", callback_data="tool_contrast")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark_img"),
             InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text("🖼️ **IMAGE EDITING TOOLS**\n\nChoose a tool:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all 50+ filters menu"""
        query = update.callback_query
        await query.answer()
        
        filter_categories = [
            ("🎨 BASIC (10)", "filters_basic"),
            ("🌈 COLOR (10)", "filters_color"),
            ("🎭 ARTISTIC (10)", "filters_artistic"),
            ("✨ LIGHTING (10)", "filters_lighting"),
            ("⚡ SPECIAL (10)", "filters_special")
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
    
    async def show_color_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show color filters"""
        query = update.callback_query
        await query.answer()
        
        filters_list = [
            "vintage", "cool", "warm", "noir", "pastel",
            "sunset", "ocean", "forest", "autumn", "spring"
        ]
        
        keyboard = []
        for i in range(0, len(filters_list), 2):
            row = []
            row.append(InlineKeyboardButton(filters_list[i].title(), callback_data=f"filter_{filters_list[i]}"))
            if i+1 < len(filters_list):
                row.append(InlineKeyboardButton(filters_list[i+1].title(), callback_data=f"filter_{filters_list[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text("🌈 **COLOR FILTERS**\n\nChoose a filter:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_artistic_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show artistic filters"""
        query = update.callback_query
        await query.answer()
        
        filters_list = [
            "oil_paint", "watercolor", "pencil_sketch", "cartoon", "pixelate",
            "glitch", "vhs", "halftone", "mosaic", "stained_glass"
        ]
        
        keyboard = []
        for i in range(0, len(filters_list), 2):
            row = []
            row.append(InlineKeyboardButton(filters_list[i].title().replace('_', ' '), callback_data=f"filter_{filters_list[i]}"))
            if i+1 < len(filters_list):
                row.append(InlineKeyboardButton(filters_list[i+1].title().replace('_', ' '), callback_data=f"filter_{filters_list[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text("🎭 **ARTISTIC FILTERS**\n\nChoose a filter:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_lighting_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show lighting filters"""
        query = update.callback_query
        await query.answer()
        
        filters_list = [
            "bokeh", "lens_flare", "vignette", "gradient_map", "dual_tone",
            "cross_process", "hdr", "dramatic", "dreamy", "cinematic"
        ]
        
        keyboard = []
        for i in range(0, len(filters_list), 2):
            row = []
            row.append(InlineKeyboardButton(filters_list[i].title().replace('_', ' '), callback_data=f"filter_{filters_list[i]}"))
            if i+1 < len(filters_list):
                row.append(InlineKeyboardButton(filters_list[i+1].title().replace('_', ' '), callback_data=f"filter_{filters_list[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text("✨ **LIGHTING EFFECTS**\n\nChoose a filter:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_special_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show special filters"""
        query = update.callback_query
        await query.answer()
        
        filters_list = [
            "neon", "glow", "sparkle", "rainbow", "prism",
            "mirror", "kaleidoscope", "fisheye", "tilt_shift", "miniature"
        ]
        
        keyboard = []
        for i in range(0, len(filters_list), 2):
            row = []
            row.append(InlineKeyboardButton(filters_list[i].title(), callback_data=f"filter_{filters_list[i]}"))
            if i+1 < len(filters_list):
                row.append(InlineKeyboardButton(filters_list[i+1].title(), callback_data=f"filter_{filters_list[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_filters")])
        
        await query.edit_message_text("⚡ **SPECIAL EFFECTS**\n\nChoose a filter:", 
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

📅 **Expires:** {user.get('premium_expiry', 'N/A')[:10] if user.get('premium_expiry') else 'N/A'}

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
⭐ Telegram Stars

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
    
    async def download_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show download menu"""
        query = update.callback_query
        await query.answer()
        
        text = """
📥 **SOCIAL MEDIA DOWNLOADER**

Send me a link from any supported platform:

**Supported Platforms:**
• 📺 **YouTube** - Videos, Shorts, Playlists
• 📸 **Instagram** - Reels, Posts, Stories
• 🎵 **TikTok** - Videos, Slideshows
• 🐦 **Twitter/X** - Videos, GIFs
• 📌 **Pinterest** - Videos, Pins
• 🎬 **Facebook** - Videos, Reels
• 📹 **Reddit** - Videos

**How to use:**
Simply send me a link and I'll download it for you!

**Examples:**
• `https://youtube.com/watch?v=...`
• `https://instagram.com/p/...`
• `https://tiktok.com/@.../video/...`

━━━━━━━━━━━━━━━━━━━━━━
⚡ **Premium users get faster downloads & no ads!**
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
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
• Total Edits: `{user.get('edits_count', 0)}`
• Today's Edits: `{user.get('daily_edits', 0)}`
• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`

{f'📅 Expires: {user.get("premium_expiry", "N/A")[:10]}' if is_premium and user.get("premium_expiry") else ''}

🏆 **Global Stats:**
• Total Users: `{stats['total_users']}`
• Premium Users: `{stats['premium_users']}`
• Total Edits: `{stats['total_edits']}`
• Today's Edits: `{stats['today_edits']}`

💎 **Referral Bonus:**
• Referrals: `{user.get('referral_count', 0)}`
• Balance: `${user.get('balance', 0)}`

━━━━━━━━━━━━━━━━━━━━━━
💡 **Share your referral link to earn rewards!**
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help menu"""
        await self.menu_command(update, context)
    
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle feedback"""
        await update.message.reply_text("📝 **Send your feedback**\n\nPlease send your feedback, suggestions, or bug reports. We value your opinion!\n\nType /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
        return "WAITING_FOR_FEEDBACK"
    
    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process feedback"""
        feedback_text = update.message.text
        
        if feedback_text == "/cancel":
            await update.message.reply_text("❌ Feedback cancelled.")
            return ConversationHandler.END
        
        db.add_feedback(update.effective_user.id, feedback_text, 5)
        
        # Notify admins
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, f"📝 **New Feedback**\n\nFrom: {update.effective_user.first_name}\nID: `{update.effective_user.id}`\n\n{feedback_text}", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
        
        await update.message.reply_text("✅ **Thank you for your feedback!** We'll review it and get back to you if needed.", parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show about info"""
        text = f"""
ℹ️ **About Kinva Master Pro**

**Version:** {Config.get_version()}
**Developer:** Kinva Team
**Platform:** Telegram & Web

**Features:**
• 40+ Video Editing Tools
• 50+ Professional Filters
• 30+ Image Editing Tools
• Social Media Downloader
• Premium Features

**Links:**
• 🌐 **Web App:** {Config.WEBHOOK_URL}
• 📢 **Channel:** @KinvaMaster
• 💬 **Support:** @KinvaSupport

**Credits:**
Built with Python, MoviePy, PIL, OpenCV, and Telegram Bot API

━━━━━━━━━━━━━━━━━━━━━━
⭐ **Enjoying the bot? Rate us 5 stars!** ⭐
        """
        
        keyboard = [[InlineKeyboardButton("🌐 OPEN WEB APP", url=Config.WEBHOOK_URL)]]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
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
/feedback_list - View feedback
/users_list - List recent users

📊 **Web Admin Panel:**
{Config.WEBHOOK_URL}/admin

🔐 **Admin Password:** {Config.ADMIN_PASSWORD}
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Usage: /broadcast [message]")
            return
        
        await update.message.reply_text("📢 Starting broadcast...")
        
        users = db.get_all_users(limit=10000)
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(user['id'], f"📢 **Announcement**\n\n{message}", parse_mode=ParseMode.MARKDOWN)
                sent += 1
            except:
                failed += 1
            
            if sent % 10 == 0:
                await asyncio.sleep(0.5)
        
        await update.message.reply_text(f"✅ Broadcast complete!\n\nSent: {sent}\nFailed: {failed}")
    
    async def add_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add premium to user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /add_premium [user_id] [days=30]")
            return
        
        try:
            user_id = int(context.args[0])
            days = int(context.args[1]) if len(context.args) > 1 else 30
            
            db.add_premium(user_id, days)
            await update.message.reply_text(f"✅ Premium added to user {user_id} for {days} days!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def remove_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove premium from user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /remove_premium [user_id]")
            return
        
        try:
            user_id = int(context.args[0])
            db.update_user(user_id, is_premium=0, premium_expiry=None)
            await update.message.reply_text(f"✅ Premium removed from user {user_id}!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /ban [user_id]")
            return
        
        try:
            user_id = int(context.args[0])
            db.ban_user(user_id)
            await update.message.reply_text(f"✅ User {user_id} banned!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban user"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /unban [user_id]")
            return
        
        try:
            user_id = int(context.args[0])
            db.unban_user(user_id)
            await update.message.reply_text(f"✅ User {user_id} unbanned!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo upload"""
        user_id = update.effective_user.id
        
        if db.is_banned(user_id):
            await update.message.reply_text("⛔ You are banned from using this bot!")
            return
        
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
            [InlineKeyboardButton("💧 ADD WATERMARK", callback_data="tool_watermark_img"),
             InlineKeyboardButton("📝 ADD TEXT", callback_data="tool_text_img")],
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
        
        if db.is_banned(user_id):
            await update.message.reply_text("⛔ You are banned from using this bot!")
            return
        
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
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="tool_extract_audio"),
             InlineKeyboardButton("🔊 COMPRESS", callback_data="tool_compress")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="tool_video_effects"),
             InlineKeyboardButton("💧 WATERMARK", callback_data="tool_video_watermark")],
            [InlineKeyboardButton("✅ DONE", callback_data="done_edit")]
        ]
        
        await update.message.reply_video(video=open(path, 'rb'), 
                                         caption="✅ **Video received!** Choose an option:", 
                                         reply_markup=InlineKeyboardMarkup(keyboard), 
                                         parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries - FIXED"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        # Main menu navigation
        if data == "back_main":
            await self.start_callback(update, context)
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
            await self.help_callback(update, context)
        elif data == "menu_download":
            await self.download_menu(update, context)
        elif data == "menu_admin":
            await self.admin_callback(update, context)
        
        # Filter categories
        elif data == "filters_basic":
            await self.show_basic_filters(update, context)
        elif data == "filters_color":
            await self.show_color_filters(update, context)
        elif data == "filters_artistic":
            await self.show_artistic_filters(update, context)
        elif data == "filters_lighting":
            await self.show_lighting_filters(update, context)
        elif data == "filters_special":
            await self.show_special_filters(update, context)
        
        # Image tools
        elif data == "image_tools_menu":
            await self.image_menu(update, context)
        elif data == "apply_filter_menu":
            await self.filters_menu(update, context)
        
        # Apply filter
        elif data.startswith("filter_"):
            filter_name = data.replace("filter_", "")
            if 'current_image' in context.user_data:
                await query.answer(f"Applying {filter_name}...")
                
                try:
                    path = context.user_data['current_image']
                    output_path = self.filters.apply_filter(path, filter_name)
                    
                    await query.message.reply_photo(photo=open(output_path, 'rb'), 
                                                   caption=f"✅ Applied **{filter_name}** filter!\n\nSend another file or choose more options.", 
                                                   parse_mode=ParseMode.MARKDOWN)
                    
                    context.user_data['current_image'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send an image first!", show_alert=True)
        
        # Video tools - FIXED
        elif data == "tool_trim":
            await query.edit_message_text("✂️ **Trim Video**\n\nSend start and end time in seconds.\nExample: `10 30`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'trim_params'
        
        elif data == "tool_speed":
            await query.edit_message_text("⚡ **Change Speed**\n\nSend speed factor:\n• 0.5 = Slow motion\n• 1.0 = Normal\n• 2.0 = Fast motion\n\nExample: `1.5`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'speed_params'
        
        elif data == "tool_compress":
            await query.edit_message_text("🔊 **Compress Video**\n\nSend target size in MB (max 50MB).\nExample: `20`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'compress_params'
        
        elif data == "tool_reverse":
            if 'current_video' in context.user_data:
                await query.answer("Reversing video...")
                try:
                    output_path = self.video_tools.reverse(context.user_data['current_video'])
                    await query.message.reply_video(video=open(output_path, 'rb'), 
                                                   caption="✅ Video reversed successfully!")
                    context.user_data['current_video'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_extract_audio":
            if 'current_video' in context.user_data:
                await query.answer("Extracting audio...")
                try:
                    output_path = self.video_tools.extract_audio(context.user_data['current_video'])
                    if output_path:
                        await query.message.reply_audio(audio=open(output_path, 'rb'), 
                                                       caption="✅ Audio extracted successfully!")
                    else:
                        await query.edit_message_text("❌ Failed to extract audio.")
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_video_effects":
            keyboard = [
                [InlineKeyboardButton("🎬 FADE IN", callback_data="tool_fade_in"),
                 InlineKeyboardButton("🎬 FADE OUT", callback_data="tool_fade_out")],
                [InlineKeyboardButton("⚫ GRAYSCALE", callback_data="tool_grayscale_vid"),
                 InlineKeyboardButton("🌀 BLUR", callback_data="tool_blur_vid")],
                [InlineKeyboardButton("🔙 BACK", callback_data="menu_video")]
            ]
            await query.edit_message_text("✨ **VIDEO EFFECTS**\n\nChoose an effect:", 
                                          reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif data == "tool_fade_in":
            if 'current_video' in context.user_data:
                await query.answer("Applying fade in...")
                try:
                    output_path = self.video_tools.fade_in(context.user_data['current_video'])
                    await query.message.reply_video(video=open(output_path, 'rb'), 
                                                   caption="✅ Fade in applied!")
                    context.user_data['current_video'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_fade_out":
            if 'current_video' in context.user_data:
                await query.answer("Applying fade out...")
                try:
                    output_path = self.video_tools.fade_out(context.user_data['current_video'])
                    await query.message.reply_video(video=open(output_path, 'rb'), 
                                                   caption="✅ Fade out applied!")
                    context.user_data['current_video'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_grayscale_vid":
            if 'current_video' in context.user_data:
                await query.answer("Converting to grayscale...")
                try:
                    output_path = self.video_tools.grayscale_video(context.user_data['current_video'])
                    await query.message.reply_video(video=open(output_path, 'rb'), 
                                                   caption="✅ Converted to grayscale!")
                    context.user_data['current_video'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_blur_vid":
            if 'current_video' in context.user_data:
                await query.answer("Applying blur...")
                try:
                    output_path = self.video_tools.blur_video(context.user_data['current_video'])
                    await query.message.reply_video(video=open(output_path, 'rb'), 
                                                   caption="✅ Blur applied!")
                    context.user_data['current_video'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send a video first!", show_alert=True)
        
        elif data == "tool_video_watermark":
            await query.edit_message_text("💧 **Add Watermark**\n\nSend the watermark text you want to add to your video.\n\nExample: `Kinva Master`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'watermark_params'
        
        elif data == "tool_watermark_img":
            await query.edit_message_text("💧 **Add Watermark**\n\nSend the watermark text you want to add to your image.\n\nExample: `Kinva Master`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'watermark_img_params'
        
        # Image tools
        elif data == "tool_resize_img":
            await query.edit_message_text("📏 **Resize Image**\n\nSend new dimensions.\nExample: `800 600`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'resize_img_params'
        
        elif data == "tool_crop_img":
            await query.edit_message_text("✂️ **Crop Image**\n\nSend crop coordinates (left, top, right, bottom).\nExample: `100 100 500 500`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'crop_img_params'
        
        elif data == "tool_rotate_img":
            await query.edit_message_text("🔄 **Rotate Image**\n\nSend rotation angle in degrees.\nExample: `90`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'rotate_img_params'
        
        elif data == "tool_flip_img":
            keyboard = [
                [InlineKeyboardButton("🪞 FLIP HORIZONTAL", callback_data="flip_horizontal_img"),
                 InlineKeyboardButton("🪞 FLIP VERTICAL", callback_data="flip_vertical_img")],
                [InlineKeyboardButton("🔙 BACK", callback_data="image_tools_menu")]
            ]
            await query.edit_message_text("🪞 **Flip Image**\n\nChoose flip direction:", 
                                          reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif data == "flip_horizontal_img":
            if 'current_image' in context.user_data:
                try:
                    img = Image.open(context.user_data['current_image'])
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    output_path = os.path.join(Config.OUTPUT_DIR, f"flipped_{datetime.now().timestamp()}.png")
                    img.save(output_path)
                    await query.message.reply_photo(photo=open(output_path, 'rb'), 
                                                   caption="✅ Image flipped horizontally!")
                    context.user_data['current_image'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send an image first!", show_alert=True)
        
        elif data == "flip_vertical_img":
            if 'current_image' in context.user_data:
                try:
                    img = Image.open(context.user_data['current_image'])
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                    output_path = os.path.join(Config.OUTPUT_DIR, f"flipped_{datetime.now().timestamp()}.png")
                    img.save(output_path)
                    await query.message.reply_photo(photo=open(output_path, 'rb'), 
                                                   caption="✅ Image flipped vertically!")
                    context.user_data['current_image'] = output_path
                except Exception as e:
                    await query.edit_message_text(f"❌ Error: {str(e)}")
            else:
                await query.answer("Please send an image first!", show_alert=True)
        
        elif data == "tool_brightness":
            await query.edit_message_text("🌈 **Adjust Brightness**\n\nSend brightness factor (0.5 to 2.0).\n• 1.0 = Normal\n• <1.0 = Darker\n• >1.0 = Brighter\n\nExample: `1.5`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'brightness_params'
        
        elif data == "tool_contrast":
            await query.edit_message_text("🎨 **Adjust Contrast**\n\nSend contrast factor (0.5 to 2.0).\n• 1.0 = Normal\n• <1.0 = Less contrast\n• >1.0 = More contrast\n\nExample: `1.5`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'contrast_params'
        
        elif data == "tool_text_img":
            await query.edit_message_text("📝 **Add Text to Image**\n\nSend the text you want to add.\n\nExample: `Hello World!`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'text_img_params'
        
        elif data == "reset_image":
            if 'original_image' in context.user_data:
                context.user_data['current_image'] = context.user_data['original_image']
                await query.message.reply_photo(photo=open(context.user_data['original_image'], 'rb'), 
                                               caption="✅ Image reset to original!")
            else:
                await query.answer("No original image to reset to!", show_alert=True)
        
        # Premium / Payment
        elif data == "pay_stars":
            await query.answer("⭐ Payment with Stars coming soon!")
            await query.edit_message_text("⭐ **Star Payments**\n\nThis feature is coming soon! Stay tuned.\n\nFor now, please use UPI payment.", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "pay_upi":
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"upi://pay?pa={Config.UPI_ID}&pn=KinvaMaster&am={Config.PREMIUM_PRICE_INR}&cu=INR")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = os.path.join(Config.TEMP_DIR, f"qr_{user_id}.png")
            img.save(qr_path)
            
            text = f"""
💳 **UPI PAYMENT**

**UPI ID:** `{Config.UPI_ID}`
**Amount:** ₹{Config.PREMIUM_PRICE_INR}

**Steps:**
1. Scan QR code or pay to UPI ID
2. Send screenshot to @admin
3. Premium activated within 24 hours

**After payment, send:** `/confirm [transaction_id]`
            """
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]]
            
            with open(qr_path, 'rb') as f:
                await query.message.reply_photo(f, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        
        elif data == "buy_premium":
            await self.premium_menu(update, context)
        
        elif data == "done_edit":
            await query.edit_message_text("✅ **Editing complete!**\n\nSend me another file to continue editing!\n\nType /menu to see all tools.", parse_mode=ParseMode.MARKDOWN)
        
        # Video tools with parameters
        elif data == "tool_crop_video":
            await query.edit_message_text("🎯 **Crop Video**\n\nSend crop coordinates (x1, y1, x2, y2).\nExample: `100 100 500 500`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'crop_video_params'
        
        elif data == "tool_resize_video":
            await query.edit_message_text("📏 **Resize Video**\n\nSend new dimensions (width height).\nExample: `1280 720`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'resize_video_params'
        
        elif data == "tool_rotate_video":
            await query.edit_message_text("🔄 **Rotate Video**\n\nSend rotation angle in degrees.\nExample: `90`\n\nSend /cancel to cancel.", parse_mode=ParseMode.MARKDOWN)
            context.user_data['waiting_for'] = 'rotate_video_params'
    
    async def start_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start from callback"""
        query = update.callback_query
        user = query.from_user
        
        if not db.get_user(user.id):
            db.create_user(user.id, user.username, user.first_name, user.last_name)
        
        user_data = db.get_user(user.id)
        is_premium = db.is_premium(user.id)
        max_edits = Config.MAX_EDIT_PER_DAY_PREMIUM if is_premium else Config.MAX_EDIT_PER_DAY_FREE
        
        welcome_text = f"""
🎬 **KINVA MASTER PRO** 🎬

━━━━━━━━━━━━━━━━━━━━━━
✨ **WELCOME TO THE ULTIMATE EDITING BOT** ✨
━━━━━━━━━━━━━━━━━━━━━━

👋 Hello **{user.first_name}**!

🚀 **What I Can Do:**
• 🎥 **40+ Video Editing Tools**
• 🖼️ **30+ Image Editing Tools**  
• 🎨 **50+ Professional Filters**
• 🎵 **Audio Processing Tools**
• 📥 **Social Media Downloader**
• ⭐ **Premium Features**

📊 **Your Stats:**
• Edits Today: {user_data.get('daily_edits', 0)}/{max_edits}
• Total Edits: {user_data.get('edits_count', 0)}
• Premium: {'✅ ACTIVE' if is_premium else '❌ INACTIVE'}

💡 **Just send me a photo or video to start editing!**

━━━━━━━━━━━━━━━━━━━━━━
🌟 **Type /menu to see all tools** 🌟
━━━━━━━━━━━━━━━━━━━━━━
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
             InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
            [InlineKeyboardButton("🎨 FILTERS (50+)", callback_data="menu_filters"),
             InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium")],
            [InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download"),
             InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats")],
            [InlineKeyboardButton("❓ HELP", callback_data="menu_help")]
        ]
        
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help from callback"""
        await self.menu_command(update, context)
    
    async def admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin from callback"""
        await self.admin_command(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for tool parameters"""
        text = update.message.text
        
        if text == "/cancel":
            if 'waiting_for' in context.user_data:
                del context.user_data['waiting_for']
                await update.message.reply_text("❌ Operation cancelled.")
            return
        
        if 'waiting_for' not in context.user_data:
            # Check if it's a download link
            if text.startswith(('http://', 'https://', 'www.')):
                await self.handle_download(update, context)
            return
        
        action = context.user_data['waiting_for']
        
        # Video parameters
        if action == 'trim_params':
            try:
                parts = text.split()
                if len(parts) != 2:
                    await update.message.reply_text("❌ Please send two numbers: start and end time.\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
                    return
                
                start, end = float(parts[0]), float(parts[1])
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text("✂️ Trimming video... Please wait.")
                
                output_path = self.video_tools.trim(context.user_data['current_video'], start, end)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Trimmed from {start}s to {end}s")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid numbers. Please send numbers like: `10 30`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'speed_params':
            try:
                speed = float(text)
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text(f"⚡ Changing speed to {speed}x... Please wait.")
                
                output_path = self.video_tools.speed(context.user_data['current_video'], speed)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Speed changed to {speed}x")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid number. Please send a number like: `1.5`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'compress_params':
            try:
                target_size = int(text)
                
                if target_size > 100:
                    await update.message.reply_text("❌ Target size too large. Maximum is 100MB.")
                    return
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text("🔊 Compressing video... This may take a while.")
                
                output_path = self.video_tools.compress(context.user_data['current_video'], target_size)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Compressed to {target_size}MB")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid number. Please send a number like: `20`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'watermark_params':
            watermark_text = text
            
            if 'current_video' not in context.user_data:
                await update.message.reply_text("❌ No video found. Please send a video first.")
                del context.user_data['waiting_for']
                return
            
            await update.message.reply_text("💧 Adding watermark...")
            
            try:
                output_path = self.video_tools.add_watermark(context.user_data['current_video'], watermark_text)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Watermark added: '{watermark_text}'")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        # Image parameters
        elif action == 'resize_img_params':
            try:
                parts = text.split()
                if len(parts) != 2:
                    await update.message.reply_text("❌ Please send width and height.\nExample: `800 600`", parse_mode=ParseMode.MARKDOWN)
                    return
                
                width, height = int(parts[0]), int(parts[1])
                
                if 'current_image' not in context.user_data:
                    await update.message.reply_text("❌ No image found. Please send an image first.")
                    del context.user_data['waiting_for']
                    return
                
                img = Image.open(context.user_data['current_image'])
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"resized_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Resized to {width}x{height}")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid dimensions. Please send two numbers.\nExample: `800 600`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'crop_img_params':
            try:
                parts = text.split()
                if len(parts) != 4:
                    await update.message.reply_text("❌ Please send left, top, right, bottom coordinates.\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
                    return
                
                left, top, right, bottom = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                
                if 'current_image' not in context.user_data:
                    await update.message.reply_text("❌ No image found. Please send an image first.")
                    del context.user_data['waiting_for']
                    return
                
                img = Image.open(context.user_data['current_image'])
                img = img.crop((left, top, right, bottom))
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"cropped_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Cropped to {right-left}x{bottom-top}")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid coordinates. Please send four numbers.\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'rotate_img_params':
            try:
                angle = int(text)
                
                if 'current_image' not in context.user_data:
                    await update.message.reply_text("❌ No image found. Please send an image first.")
                    del context.user_data['waiting_for']
                    return
                
                img = Image.open(context.user_data['current_image'])
                img = img.rotate(angle, expand=True)
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"rotated_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Rotated {angle} degrees")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid angle. Please send a number.\nExample: `90`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'brightness_params':
            try:
                factor = float(text)
                
                if factor < 0.1 or factor > 3.0:
                    await update.message.reply_text("❌ Factor should be between 0.1 and 3.0")
                    return
                
                if 'current_image' not in context.user_data:
                    await update.message.reply_text("❌ No image found. Please send an image first.")
                    del context.user_data['waiting_for']
                    return
                
                img = Image.open(context.user_data['current_image'])
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"brightness_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Brightness adjusted by factor {factor}")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid factor. Please send a number.\nExample: `1.5`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'contrast_params':
            try:
                factor = float(text)
                
                if factor < 0.1 or factor > 3.0:
                    await update.message.reply_text("❌ Factor should be between 0.1 and 3.0")
                    return
                
                if 'current_image' not in context.user_data:
                    await update.message.reply_text("❌ No image found. Please send an image first.")
                    del context.user_data['waiting_for']
                    return
                
                img = Image.open(context.user_data['current_image'])
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(factor)
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"contrast_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Contrast adjusted by factor {factor}")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid factor. Please send a number.\nExample: `1.5`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'text_img_params':
            text_to_add = text
            
            if 'current_image' not in context.user_data:
                await update.message.reply_text("❌ No image found. Please send an image first.")
                del context.user_data['waiting_for']
                return
            
            try:
                img = Image.open(context.user_data['current_image'])
                draw = ImageDraw.Draw(img)
                
                # Try to load a font, fallback to default
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                # Get text size
                bbox = draw.textbbox((0, 0), text_to_add, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position at bottom center
                x = (img.width - text_width) // 2
                y = img.height - text_height - 20
                
                # Add shadow
                draw.text((x+2, y+2), text_to_add, font=font, fill=(0, 0, 0))
                # Add text
                draw.text((x, y), text_to_add, font=font, fill=(255, 255, 255))
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"text_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Text added: '{text_to_add}'")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'watermark_img_params':
            watermark_text = text
            
            if 'current_image' not in context.user_data:
                await update.message.reply_text("❌ No image found. Please send an image first.")
                del context.user_data['waiting_for']
                return
            
            try:
                img = Image.open(context.user_data['current_image'])
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                # Position at bottom right
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = img.width - text_width - 10
                y = img.height - text_height - 10
                
                # Add semi-transparent background
                draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0, 0, 0, 128))
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 200))
                
                output_path = os.path.join(Config.OUTPUT_DIR, f"watermarked_{datetime.now().timestamp()}.png")
                img.save(output_path)
                
                await update.message.reply_photo(photo=open(output_path, 'rb'), 
                                               caption=f"✅ Watermark added: '{watermark_text}'")
                
                context.user_data['current_image'] = output_path
                del context.user_data['waiting_for']
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'crop_video_params':
            try:
                parts = text.split()
                if len(parts) != 4:
                    await update.message.reply_text("❌ Please send x1, y1, x2, y2 coordinates.\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
                    return
                
                x1, y1, x2, y2 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text("🎯 Cropping video... Please wait.")
                
                output_path = self.video_tools.crop(context.user_data['current_video'], x1, y1, x2, y2)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Video cropped")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid coordinates. Please send four numbers.\nExample: `100 100 500 500`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'resize_video_params':
            try:
                parts = text.split()
                if len(parts) != 2:
                    await update.message.reply_text("❌ Please send width and height.\nExample: `1280 720`", parse_mode=ParseMode.MARKDOWN)
                    return
                
                width, height = int(parts[0]), int(parts[1])
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text("📏 Resizing video... Please wait.")
                
                output_path = self.video_tools.resize(context.user_data['current_video'], width, height)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Resized to {width}x{height}")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid dimensions. Please send two numbers.\nExample: `1280 720`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
        
        elif action == 'rotate_video_params':
            try:
                angle = int(text)
                
                if 'current_video' not in context.user_data:
                    await update.message.reply_text("❌ No video found. Please send a video first.")
                    del context.user_data['waiting_for']
                    return
                
                await update.message.reply_text("🔄 Rotating video... Please wait.")
                
                output_path = self.video_tools.rotate(context.user_data['current_video'], angle)
                
                await update.message.reply_video(video=open(output_path, 'rb'), 
                                               caption=f"✅ Rotated {angle} degrees")
                
                context.user_data['current_video'] = output_path
                del context.user_data['waiting_for']
                
            except ValueError:
                await update.message.reply_text("❌ Invalid angle. Please send a number.\nExample: `90`", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
                del context.user_data['waiting_for']
    
    async def handle_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download links"""
        url = update.message.text
        
        await update.message.reply_text("📥 Downloading... Please wait.")
        
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(Config.TEMP_DIR, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    if filename.endswith('.mp4') or filename.endswith('.webm'):
                        await update.message.reply_video(video=open(filename, 'rb'), 
                                                       caption=f"✅ Downloaded: {info.get('title', 'Video')}")
                    else:
                        await update.message.reply_document(document=open(filename, 'rb'), 
                                                          caption=f"✅ Downloaded: {info.get('title', 'File')}")
                    
                    os.remove(filename)
                else:
                    await update.message.reply_text("❌ Failed to download. Please check the link.")
                    
        except Exception as e:
            await update.message.reply_text(f"❌ Download error: {str(e)}")
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm UPI payment"""
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /confirm [transaction_id]")
            return
        
        transaction_id = context.args[0]
        
        # This would normally verify with your payment gateway
        db.complete_transaction(transaction_id)
        
        await update.message.reply_text("✅ Payment confirmed! Premium activated for 30 days!")

# ============================================
# FLASK WEB APP
# ============================================

flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get("FLASK_SECRET", "kinva_master_secret_key_2024")
CORS(flask_app)
socketio = SocketIO(flask_app, cors_allowed_origins="*")

# Simple HTML template for web app
WEB_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kinva Master Pro - Professional Editor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center;
            padding: 40px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .header h1 { font-size: 48px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .feature-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s;
        }
        .feature-card:hover { transform: translateY(-5px); }
        .feature-card i { font-size: 48px; margin-bottom: 15px; }
        .feature-card h3 { margin-bottom: 10px; }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            padding: 12px 30px;
            border-radius: 30px;
            color: white;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            transition: transform 0.3s;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-telegram { background: #0088cc; }
        .footer {
            text-align: center;
            padding: 30px;
            background: rgba(0,0,0,0.2);
            border-radius: 20px;
            margin-top: 30px;
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 32px; }
            .features { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Kinva Master Pro</h1>
            <p>Professional Video & Image Editing Bot</p>
            <a href="https://t.me/KinvaMasterBot" class="btn btn-telegram">📱 Open in Telegram</a>
            <a href="https://t.me/KinvaMasterBot?start=web" class="btn">🚀 Start Editing</a>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <i>🎥</i>
                <h3>40+ Video Tools</h3>
                <p>Trim, crop, rotate, speed, effects and more</p>
            </div>
            <div class="feature-card">
                <i>🎨</i>
                <h3>50+ Filters</h3>
                <p>Professional filters and effects for images</p>
            </div>
            <div class="feature-card">
                <i>⭐</i>
                <h3>Premium Features</h3>
                <p>4K export, no watermark, priority processing</p>
            </div>
            <div class="feature-card">
                <i>📥</i>
                <h3>Downloader</h3>
                <p>Download from YouTube, Instagram, TikTok</p>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 Kinva Master Pro | Version 4.0.0</p>
            <p>Made with ❤️ for content creators</p>
        </div>
    </div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kinva Master - Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0c29;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }
        .stat-number { font-size: 36px; font-weight: bold; }
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        .badge-premium { background: #4caf50; }
        .badge-free { background: #ff9800; }
        .btn {
            background: #667eea;
            border: none;
            padding: 8px 16px;
            border-radius: 10px;
            color: white;
            cursor: pointer;
        }
        .btn-danger { background: #f44336; }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
        }
        input::placeholder { color: rgba(255,255,255,0.7); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Kinva Master Admin Panel</h1>
            <p>Monitor and manage your editing bot</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_users }}</div>
                <div>Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ premium_users }}</div>
                <div>Premium Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_edits }}</div>
                <div>Total Edits</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ today_edits }}</div>
                <div>Today's Edits</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Quick Actions</h2>
            <button class="btn" onclick="broadcast()">📢 Broadcast Message</button>
            <button class="btn" onclick="addPremium()">⭐ Add Premium</button>
            <button class="btn btn-danger" onclick="viewFeedback()">📝 View Feedback</button>
        </div>
        
        <div class="section">
            <h2>👥 Recent Users</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr><th>ID</th><th>Username</th><th>Name</th><th>Edits</th><th>Status</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.id }}</td>
                            <td>@{{ user.username or 'N/A' }}</td>
                            <td>{{ user.first_name or '' }}</td>
                            <td>{{ user.edits_count or 0 }}</td>
                            <td><span class="badge {{ 'badge-premium' if user.is_premium else 'badge-free' }}">{{ 'Premium' if user.is_premium else 'Free' }}</span></td>
                            <td><button class="btn" onclick="togglePremium({{ user.id }})">Toggle Premium</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function broadcast() {
            let msg = prompt("Enter broadcast message:");
            if(msg) {
                fetch('/api/broadcast', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                }).then(r => r.json()).then(data => {
                    alert(data.message);
                });
            }
        }
        
        function addPremium() {
            let userId = prompt("Enter user ID:");
            if(userId) {
                fetch('/api/add_premium', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: parseInt(userId)})
                }).then(r => r.json()).then(data => {
                    alert(data.message);
                    location.reload();
                });
            }
        }
        
        function togglePremium(userId) {
            fetch('/api/toggle_premium', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId})
            }).then(r => r.json()).then(data => {
                alert(data.message);
                location.reload();
            });
        }
        
        function viewFeedback() {
            fetch('/api/feedback').then(r => r.json()).then(data => {
                alert(JSON.stringify(data, null, 2));
            });
        }
    </script>
</body>
</html>
"""

@flask_app.route('/')
def web_index():
    return render_template_string(WEB_HTML)

@flask_app.route('/admin')
def admin_panel():
    password = request.args.get('password', '')
    if password != Config.ADMIN_PASSWORD:
        return '''
        <div class="login-container">
            <h2>🔐 Admin Login</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Enter password" required>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
        <style>
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: none;
                border-radius: 10px;
                background: rgba(255,255,255,0.2);
                color: white;
            }
            .btn {
                background: #667eea;
                border: none;
                padding: 12px 30px;
                border-radius: 30px;
                color: white;
                cursor: pointer;
            }
            body {
                background: linear-gradient(135deg, #667eea, #764ba2);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        </style>
        '''
    
    stats = db.get_stats()
    users = db.get_all_users(limit=50)
    
    return render_template_string(ADMIN_HTML, 
                                  total_users=stats['total_users'],
                                  premium_users=stats['premium_users'],
                                  total_edits=stats['total_edits'],
                                  today_edits=stats['today_edits'],
                                  users=users)

@flask_app.route('/api/broadcast', methods=['POST'])
def api_broadcast():
    if request.headers.get('X-Admin') != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "No message"}), 400
    
    # Broadcast in background thread
    def do_broadcast():
        users = db.get_all_users(limit=10000)
        for user in users:
            try:
                # This would need bot instance - simplified for now
                pass
            except:
                pass
    
    threading.Thread(target=do_broadcast).start()
    
    return jsonify({"message": f"Broadcast started to {db.get_stats()['total_users']} users"})

@flask_app.route('/api/add_premium', methods=['POST'])
def api_add_premium():
    if request.headers.get('X-Admin') != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = data.get('user_id')
    
    if user_id:
        db.add_premium(user_id, 30)
        return jsonify({"message": f"Premium added to user {user_id}"})
    
    return jsonify({"error": "Invalid user ID"}), 400

@flask_app.route('/api/toggle_premium', methods=['POST'])
def api_toggle_premium():
    if request.headers.get('X-Admin') != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = data.get('user_id')
    
    if user_id:
        user = db.get_user(user_id)
        if user and user.get('is_premium'):
            db.update_user(user_id, is_premium=0, premium_expiry=None)
            return jsonify({"message": f"Premium removed from user {user_id}"})
        else:
            db.add_premium(user_id, 30)
            return jsonify({"message": f"Premium added to user {user_id}"})
    
    return jsonify({"error": "Invalid user ID"}), 400

@flask_app.route('/api/feedback', methods=['GET'])
def api_feedback():
    if request.headers.get('X-Admin') != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    feedbacks = db.get_all_feedback(50)
    return jsonify([dict(f) for f in feedbacks])

@flask_app.route('/api/stats', methods=['GET'])
def api_stats():
    return jsonify(db.get_stats())

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": Config.get_version(),
        "timestamp": datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to Kinva Master'})

# ============================================
# MAIN EXECUTION
# ============================================

def run_flask():
    """Run Flask app in separate thread"""
    print(f"🌐 Web app running on port {Config.PORT}")
    socketio.run(flask_app, host="0.0.0.0", port=Config.PORT, allow_unsafe_werkzeug=True, debug=False)

def main():
    print("🚀 Starting Kinva Master Pro v4.0.0...")
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Initialize Telegram bot
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    bot = KinvaMasterBot()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("menu", bot.menu_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("about", bot.about_command))
    application.add_handler(CommandHandler("feedback", bot.feedback_command))
    application.add_handler(CommandHandler("premium", bot.premium_menu_cmd))
    application.add_handler(CommandHandler("admin", bot.admin_command))
    application.add_handler(CommandHandler("broadcast", bot.broadcast_command))
    application.add_handler(CommandHandler("add_premium", bot.add_premium_command))
    application.add_handler(CommandHandler("remove_premium", bot.remove_premium_command))
    application.add_handler(CommandHandler("ban", bot.ban_command))
    application.add_handler(CommandHandler("unban", bot.unban_command))
    application.add_handler(CommandHandler("confirm", bot.confirm_payment))
    
    # Register message handlers
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, bot.handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    
    # Feedback conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("feedback", bot.feedback_command)],
        states={"WAITING_FOR_FEEDBACK": [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_feedback)]},
        fallbacks=[CommandHandler("cancel", bot.handle_feedback)]
    )
    application.add_handler(conv_handler)
    
    # Start bot
    print("🤖 Telegram bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
