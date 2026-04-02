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

# Video Processing - MOVIEPY
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips, ImageClip, ColorClip, CompositeAudioClip

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
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

# Web Framework
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Downloaders
import yt_dlp
import instaloader
import requests

# Payment
import qrcode

# ============================================
# CONFIGURATION
# ============================================
class Config:
    """Master Configuration Class"""
    
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8791110410:AAGDvRjSJ4OvMgcYG8pOL7aCZXhkkHopEig")
    ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "8525952693").split(",")]
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://KinvaMaster-1.onrender.com")
    PORT = int(os.environ.get("PORT", 8080))
    
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
    UPI_ID = os.environ.get("UPI_ID", "kinvamaster@okhdfcbank")
    
    STAR_PRICE_MONTHLY = 100
    STAR_PRICE_YEARLY = 1000
    
    PREMIUM_PRICE_USD = 9.99
    PREMIUM_PRICE_INR = 499
    PREMIUM_PRICE_STARS = 100
    
    DEFAULT_WATERMARK = "Kinva Master Pro"
    WATERMARK_POSITIONS = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    CACHE_DIR = "cache"
    DATABASE_FILE = "kinva_master.db"
    
    MAX_FILE_SIZE = 500 * 1024 * 1024
    MAX_VIDEO_DURATION = 600
    MAX_EDIT_PER_DAY_FREE = 10
    MAX_EDIT_PER_DAY_PREMIUM = 1000
    
    ENABLE_WATERMARK = True
    ENABLE_PREMIUM = True
    ENABLE_PAYMENTS = True
    ENABLE_WEB_APP = True
    
    @classmethod
    def setup_directories(cls):
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
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
    
    def init_tables(self):
        cursor = self.conn.cursor()
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
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
            self.set_setting(key, value)
    
    def get_user(self, user_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return None
        return dict(user)
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referrer_id: int = 0):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (id, username, first_name, last_name, created_at, updated_at, referrer_id)
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
        if user and user['is_premium']:
            if user['premium_expiry']:
                expiry = datetime.fromisoformat(user['premium_expiry'])
                if datetime.now() > expiry:
                    self.update_user(user_id, is_premium=0, premium_expiry=None)
                    return False
            return True
        return False
    
    def add_premium(self, user_id: int, days: int = 30, premium_type: str = "monthly"):
        user = self.get_user(user_id)
        if user['premium_expiry']:
            expiry = datetime.fromisoformat(user['premium_expiry'])
            new_expiry = expiry + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        self.update_user(user_id, is_premium=1, premium_expiry=new_expiry.isoformat(), premium_type=premium_type)
    
    def increment_edits(self, user_id: int):
        today = datetime.now().date().isoformat()
        user = self.get_user(user_id)
        
        if user['last_edit_date'] != today:
            self.update_user(user_id, daily_edits=1, last_edit_date=today)
        else:
            self.update_user(user_id, daily_edits=user['daily_edits'] + 1)
        
        self.update_user(user_id, edits_count=user['edits_count'] + 1)
    
    def can_edit(self, user_id: int) -> bool:
        if self.is_premium(user_id):
            return True
        
        user = self.get_user(user_id)
        today = datetime.now().date().isoformat()
        
        if user['last_edit_date'] != today:
            return True
        
        return user['daily_edits'] < Config.MAX_EDIT_PER_DAY_FREE
    
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
    
    def add_analytics(self, event_type: str, user_id: int, data: dict):
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
    def __init__(self):
        self.filter_list = []
        self.init_filters()
    
    def init_filters(self):
        self.filters = {
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
    
    def oil_paint(self, img):
        img_array = np.array(img)
        output = cv2.xphoto.oilPainting(img_array, 5, 30)
        return Image.fromarray(output)
    
    def watercolor(self, img):
        img_array = np.array(img)
        output = cv2.stylization(img_array, sigma_s=60, sigma_r=0.6)
        return Image.fromarray(output)
    
    def pencil_sketch(self, img):
        img_array = np.array(img.convert("L"))
        _, sketch = cv2.pencilSketch(img_array, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        return Image.fromarray(sketch).convert("RGB")
    
    def cartoon(self, img):
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img_array, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return Image.fromarray(cartoon)
    
    def pixelate(self, img, pixel_size=10):
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        small = cv2.resize(img_array, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return Image.fromarray(pixelated)
    
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
        img_array[:, :, 0] = np.roll(img_array[:, :, 0], 2, axis=1)
        img_array[:, :, 2] = np.roll(img_array[:, :, 2], -2, axis=1)
        return Image.fromarray(img_array)
    
    def halftone(self, img):
        img_array = np.array(img.convert("L"))
        h, w = img_array.shape
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
        grid_size = 30
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                block = img_array[y:y+grid_size, x:x+grid_size]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img_array[y:y+grid_size, x:x+grid_size] = avg_color
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
            img_array[:, :, i] = img_array[:, :, i] * mask
        return Image.fromarray(img_array.astype('uint8'))
    
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
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        neon = np.zeros_like(img_array)
        neon[edges > 0] = [0, 255, 255]
        result = cv2.addWeighted(img_array, 0.7, neon, 0.3, 0)
        return Image.fromarray(result)
    
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
            blur = blur_radius * (distance / center)
            if blur > 0:
                kernel_size = int(blur) * 2 + 1
                if kernel_size > 1:
                    img_array[y:y+1] = cv2.GaussianBlur(img_array[y:y+1], (kernel_size, kernel_size), 0)
        return Image.fromarray(img_array)
    
    def miniature(self, img):
        img = self.tilt_shift(img)
        img = ImageEnhance.Color(img).enhance(1.5)
        return img

# ============================================
# PART 3: 40+ VIDEO EDITING TOOLS
# ============================================

class VideoTools40:
    def __init__(self):
        self.tools_count = 0
    
    def generate_filename(self, ext=".mp4"):
        return os.path.join(Config.OUTPUT_DIR, f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}{ext}")
    
    def trim(self, path: str, start: float, end: float) -> str:
        clip = VideoFileClip(path)
        trimmed = clip.subclipped(start, end)
        out = self.generate_filename()
        trimmed.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def crop(self, path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        clip = VideoFileClip(path)
        cropped = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
        out = self.generate_filename()
        cropped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def resize(self, path: str, width: int, height: int) -> str:
        clip = VideoFileClip(path)
        resized = clip.resized(newsize=(width, height))
        out = self.generate_filename()
        resized.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def rotate(self, path: str, angle: int) -> str:
        clip = VideoFileClip(path)
        rotated = clip.rotated(angle)
        out = self.generate_filename()
        rotated.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def flip_horizontal(self, path: str) -> str:
        clip = VideoFileClip(path)
        flipped = clip.resized(lambda t: (clip.w, clip.h), 
                               lambda t: (clip.w, clip.h, -1, 1))
        out = self.generate_filename()
        flipped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def flip_vertical(self, path: str) -> str:
        clip = VideoFileClip(path)
        flipped = clip.resized(lambda t: (clip.w, clip.h),
                               lambda t: (clip.w, clip.h, 1, -1))
        out = self.generate_filename()
        flipped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def speed(self, path: str, factor: float) -> str:
        clip = VideoFileClip(path)
        sped = clip.with_effects([vfx.MultiplySpeed(factor)])
        out = self.generate_filename()
        sped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def reverse(self, path: str) -> str:
        clip = VideoFileClip(path)
        reversed_clip = clip.with_effects([vfx.TimeMirror()])
        out = self.generate_filename()
        reversed_clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def loop(self, path: str, times: int) -> str:
        clip = VideoFileClip(path)
        looped = concatenate_videoclips([clip] * times)
        out = self.generate_filename()
        looped.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def merge(self, paths: list) -> str:
        clips = [VideoFileClip(p) for p in paths]
        merged = concatenate_videoclips(clips)
        out = self.generate_filename()
        merged.write_videofile(out, logger=None, verbose=False)
        for c in clips:
            c.close()
        return out
    
    def extract_audio(self, path: str) -> str:
        clip = VideoFileClip(path)
        out = self.generate_filename(".mp3")
        clip.audio.write_audiofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def remove_audio(self, path: str) -> str:
        clip = VideoFileClip(path)
        no_audio = clip.without_audio()
        out = self.generate_filename()
        no_audio.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def add_audio(self, video_path: str, audio_path: str, volume: float = 1.0) -> str:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        if audio.duration > video.duration:
            audio = audio.subclipped(0, video.duration)
        audio = audio.with_volume_scaled(volume)
        final = video.with_audio(audio)
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        video.close()
        audio.close()
        return out
    
    def volume(self, path: str, factor: float) -> str:
        clip = VideoFileClip(path)
        if clip.audio:
            audio = clip.audio.with_volume_scaled(factor)
            clip = clip.with_audio(audio)
        out = self.generate_filename()
        clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def audio_fade(self, path: str, fade_in: float = 1, fade_out: float = 1) -> str:
        clip = VideoFileClip(path)
        if clip.audio:
            audio = clip.audio.audio_fadein(fade_in).audio_fadeout(fade_out)
            clip = clip.with_audio(audio)
        out = self.generate_filename()
        clip.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def fade_in(self, path: str, duration: float = 1) -> str:
        clip = VideoFileClip(path)
        faded = clip.with_effects([vfx.FadeIn(duration)])
        out = self.generate_filename()
        faded.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def fade_out(self, path: str, duration: float = 1) -> str:
        clip = VideoFileClip(path)
        faded = clip.with_effects([vfx.FadeOut(duration)])
        out = self.generate_filename()
        faded.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def crossfade(self, path1: str, path2: str, duration: float = 1) -> str:
        v1 = VideoFileClip(path1)
        v2 = VideoFileClip(path2)
        v2 = v2.with_effects([vfx.CrossFadeIn(duration)])
        merged = concatenate_videoclips([v1, v2])
        out = self.generate_filename()
        merged.write_videofile(out, logger=None, verbose=False)
        v1.close()
        v2.close()
        return out
    
    def compress(self, path: str, target_size_mb: int = 20) -> str:
        clip = VideoFileClip(path)
        duration = clip.duration
        target_bitrate = (target_size_mb * 8) / duration
        out = self.generate_filename()
        clip.write_videofile(out, bitrate=f"{target_bitrate}k", logger=None, verbose=False)
        clip.close()
        return out
    
    def quality_1080p(self, path: str) -> str:
        clip = VideoFileClip(path)
        resized = clip.resized(newsize=(1920, 1080))
        out = self.generate_filename()
        resized.write_videofile(out, bitrate="5000k", logger=None, verbose=False)
        clip.close()
        return out
    
    def quality_720p(self, path: str) -> str:
        clip = VideoFileClip(path)
        resized = clip.resized(newsize=(1280, 720))
        out = self.generate_filename()
        resized.write_videofile(out, bitrate="2500k", logger=None, verbose=False)
        clip.close()
        return out
    
    def optimize(self, path: str) -> str:
        clip = VideoFileClip(path)
        out = self.generate_filename()
        clip.write_videofile(out, codec='libx264', audio_codec='aac', 
                            preset='fast', logger=None, verbose=False)
        clip.close()
        return out
    
    def slow_motion(self, path: str, factor: float = 0.5) -> str:
        return self.speed(path, factor)
    
    def fast_motion(self, path: str, factor: float = 2.0) -> str:
        return self.speed(path, factor)
    
    def add_text(self, path: str, text: str, font_size: int = 30, color: str = "white") -> str:
        clip = VideoFileClip(path)
        txt = TextClip(text, font_size=font_size, color=color, font='Arial')
        txt = txt.with_position(('center', 'bottom')).with_duration(clip.duration)
        final = CompositeVideoClip([clip, txt])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def add_watermark(self, path: str, text: str, position: str = "bottom-right") -> str:
        clip = VideoFileClip(path)
        positions = {
            "top-left": (10, 10),
            "top-right": (clip.w - 100, 10),
            "bottom-left": (10, clip.h - 30),
            "bottom-right": (clip.w - 100, clip.h - 30)
        }
        pos = positions.get(position, positions["bottom-right"])
        watermark = TextClip(text, font_size=20, color='white', font='Arial')
        watermark = watermark.with_position(pos).with_duration(clip.duration).with_opacity(0.5)
        final = CompositeVideoClip([clip, watermark])
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        clip.close()
        return out
    
    def add_music(self, video_path: str, music_path: str, volume: float = 0.3) -> str:
        video = VideoFileClip(video_path)
        music = AudioFileClip(music_path)
        if music.duration < video.duration:
            music = music.loop(duration=video.duration)
        else:
            music = music.subclipped(0, video.duration)
        music = music.with_volume_scaled(volume)
        if video.audio:
            final_audio = CompositeAudioClip([video.audio, music])
        else:
            final_audio = music
        final = video.with_audio(final_audio)
        out = self.generate_filename()
        final.write_videofile(out, logger=None, verbose=False)
        video.close()
        music.close()
        return out

# ============================================
# PART 4: TELEGRAM BOT
# ============================================

class KinvaMasterBot:
    def __init__(self):
        self.video_tools = VideoTools40()
        self.filters = Filters50()
        self.user_sessions = {}
        self.processing_tasks = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not db.get_user(user.id):
            db.create_user(user.id, user.username, user.first_name, user.last_name)
        
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

💡 **Quick Start:**
Send me a photo or video to start editing!

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
             InlineKeyboardButton("💎 TEMPLATES", callback_data="menu_templates")],
            [InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats"),
             InlineKeyboardButton("❓ HELP", callback_data="menu_help")]
        ]
        
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        menu_text = """
📋 **COMPLETE COMMAND MENU**

━━━━━━━━━━━━━━━━━━━━━━
**🎬 VIDEO EDITING (40+ TOOLS)**
━━━━━━━━━━━━━━━━━━━━━━
/trim - Trim video
/crop - Crop video
/resize - Resize video
/rotate - Rotate video
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

**✨ VIDEO EFFECTS**
/fade_in - Fade in effect
/fade_out - Fade out effect
/grayscale_vid - Black & white
/sepia_vid - Sepia effect

**📦 COMPRESSION**
/compress - Compress video
/to_1080p - Convert to 1080p
/to_720p - Convert to 720p

**🖼️ IMAGE EDITING (30+ TOOLS)**
/resize_img - Resize image
/crop_img - Crop image
/rotate_img - Rotate image
/brightness - Adjust brightness
/contrast - Adjust contrast
/saturation - Adjust saturation

**🎨 FILTERS (50+)**
/filters - Show all filters
/grayscale - Grayscale filter
/sepia - Sepia filter
/vintage - Vintage filter

**⭐ PREMIUM FEATURES**
/premium - Get premium

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
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        with open(path, 'rb') as f:
            await update.message.reply_photo(photo=f, 
                                             caption="✅ **Photo received!** Choose an option:", 
                                             reply_markup=InlineKeyboardMarkup(keyboard), 
                                             parse_mode=ParseMode.MARKDOWN)
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        with open(path, 'rb') as f:
            await update.message.reply_video(video=f, 
                                             caption="✅ **Video received!** Choose an option:", 
                                             reply_markup=InlineKeyboardMarkup(keyboard), 
                                             parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
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
            await self.menu_command(update, context)
        elif data == "filters_basic":
            await self.show_basic_filters(update, context)
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
        elif data == "pay_stars":
            await self.pay_with_stars(update, context)
        elif data == "pay_upi":
            await self.show_upi_payment(update, context)
        elif data == "buy_premium":
            await self.premium_purchase(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        
        text = f"""
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
            [InlineKeyboardButton(f"⭐ PAY {Config.PREMIUM_PRICE_STARS} STARS", callback_data="confirm_stars_payment")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_upi_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        
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
        """
        
        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]]
        
        with open(qr_path, 'rb') as f:
            await query.message.reply_photo(f, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def premium_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        
        text = f"""
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
# PART 5: FLASK WEB APP
# ============================================

flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get("FLASK_SECRET", "kinva_master_secret_key_2024")
socketio = SocketIO(flask_app, cors_allowed_origins="*")

# Web App HTML Template (Simplified working version)
WEB_APP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kinva Master Pro - Professional Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px 30px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .logo { display: flex; align-items: center; gap: 15px; }
        .logo-icon {
            width: 50px; height: 50px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        .logo h1 { font-size: 24px; font-weight: 700; }
        .logo p { font-size: 12px; opacity: 0.7; margin-top: 5px; }
        .premium-badge {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
        }
        .editor-layout {
            display: grid;
            grid-template-columns: 280px 1fr 280px;
            gap: 20px;
        }
        @media (max-width: 1000px) {
            .editor-layout { grid-template-columns: 1fr; }
        }
        .tools-panel, .filters-panel {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .tools-panel h3, .filters-panel h3 {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(102,126,234,0.5);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tools-grid, .filters-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            max-height: 500px;
            overflow-y: auto;
        }
        .tool-btn, .filter-item {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 12px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            font-size: 12px;
        }
        .tool-btn:hover, .filter-item:hover {
            background: linear-gradient(135deg, #667eea, #764ba2);
            transform: translateY(-2px);
        }
        .preview-area {
            background: rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .preview-header {
            background: rgba(255,255,255,0.1);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        .preview-container {
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
            padding: 20px;
        }
        #preview-canvas, #preview-video {
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
        }
        .controls {
            padding: 20px;
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.3);
        }
        .control-btn {
            background: rgba(255,255,255,0.15);
            border: none;
            padding: 10px 20px;
            border-radius: 30px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .control-btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        .control-btn:hover { transform: translateY(-2px); }
        .timeline-area {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 20px;
            margin-top: 20px;
        }
        .timeline-track {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 10px;
            min-height: 100px;
        }
        .timeline-clip {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 12px;
            padding: 15px;
            min-width: 120px;
            text-align: center;
            cursor: pointer;
            position: relative;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.9);
            padding: 12px 20px;
            border-radius: 30px;
            border-left: 4px solid #667eea;
            z-index: 1000;
        }
        .progress-bar {
            width: 100%;
            height: 3px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            overflow: hidden;
        }
        .progress-fill {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.1); border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <div class="logo-icon"><i class="fas fa-film"></i></div>
                <div>
                    <h1>Kinva Master Pro</h1>
                    <p>Professional Video & Image Editor | 50+ Filters | 40+ Tools</p>
                </div>
            </div>
            <div class="premium-badge" onclick="showPremium()"><i class="fas fa-crown"></i> FREE</div>
        </div>
        
        <div class="editor-layout">
            <div class="tools-panel">
                <h3><i class="fas fa-magic"></i> Tools (40+)</h3>
                <div class="tools-grid" id="tools-grid"></div>
            </div>
            
            <div class="preview-area">
                <div class="preview-header">
                    <span><i class="fas fa-eye"></i> Live Preview</span>
                    <span id="file-info">No file selected</span>
                </div>
                <div class="preview-container">
                    <canvas id="preview-canvas" style="display:none;"></canvas>
                    <video id="preview-video" style="display:none;" controls></video>
                    <div id="upload-prompt" style="text-align:center;">
                        <i class="fas fa-upload" style="font-size:48px; opacity:0.5;"></i>
                        <p>Upload image or video to start</p>
                        <button class="control-btn control-btn-primary" onclick="uploadFile()">Choose File</button>
                    </div>
                </div>
                <div class="controls">
                    <button class="control-btn" onclick="uploadFile()"><i class="fas fa-upload"></i> Upload</button>
                    <button class="control-btn control-btn-primary" onclick="applyCurrent()"><i class="fas fa-magic"></i> Apply</button>
                    <button class="control-btn" onclick="exportFile()"><i class="fas fa-download"></i> Export</button>
                    <button class="control-btn" onclick="resetEdit()"><i class="fas fa-undo"></i> Reset</button>
                </div>
                <div class="progress-bar" id="progress-bar" style="display:none;"><div class="progress-fill" id="progress-fill"></div></div>
            </div>
            
            <div class="filters-panel">
                <h3><i class="fas fa-palette"></i> Filters (50+)</h3>
                <div class="filters-grid" id="filters-grid"></div>
            </div>
        </div>
        
        <div class="timeline-area">
            <h3><i class="fas fa-chart-line"></i> Timeline</h3>
            <div class="timeline-track" id="timeline-track">Timeline empty</div>
        </div>
    </div>
    
    <div id="toast" class="toast" style="display:none;"><i class="fas fa-info-circle"></i> <span id="toast-msg"></span></div>
    
    <script>
        let currentFile = null;
        let currentFileType = null;
        let originalImageData = null;
        let currentImageData = null;
        let timelineClips = [];
        let socket = null;
        
        const tools = [
            "Grayscale", "Sepia", "Invert", "Blur", "Sharpen", 
            "Brightness", "Contrast", "Saturation", "Rotate", "Flip"
        ];
        
        const filters = [
            "Vintage", "Cool", "Warm", "Noir", "Pastel", "Sunset", "Ocean",
            "Forest", "Autumn", "Spring", "Glitch", "VHS", "Neon", "Glow"
        ];
        
        function showToast(msg, type='info') {
            const toast = document.getElementById('toast');
            document.getElementById('toast-msg').textContent = msg;
            toast.style.display = 'flex';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }
        
        function loadTools() {
            const container = document.getElementById('tools-grid');
            container.innerHTML = '';
            tools.forEach(tool => {
                const btn = document.createElement('button');
                btn.className = 'tool-btn';
                btn.innerHTML = `<i class="fas fa-${tool === 'Grayscale' ? 'adjust' : tool === 'Sepia' ? 'image' : 'wand-magic'}"></i> ${tool}`;
                btn.onclick = () => applyTool(tool.toLowerCase());
                container.appendChild(btn);
            });
        }
        
        function loadFilters() {
            const container = document.getElementById('filters-grid');
            container.innerHTML = '';
            filters.forEach(filter => {
                const btn = document.createElement('button');
                btn.className = 'filter-item';
                btn.innerHTML = filter;
                btn.onclick = () => applyFilter(filter.toLowerCase());
                container.appendChild(btn);
            });
        }
        
        function uploadFile() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*,video/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    currentFile = file;
                    currentFileType = file.type.startsWith('image/') ? 'image' : 'video';
                    document.getElementById('upload-prompt').style.display = 'none';
                    
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
                                document.getElementById('file-info').innerHTML = `<i class="fas fa-image"></i> ${file.name}`;
                            };
                            img.src = event.target.result;
                        };
                        reader.readAsDataURL(file);
                    } else {
                        document.getElementById('preview-canvas').style.display = 'none';
                        document.getElementById('preview-video').style.display = 'block';
                        const url = URL.createObjectURL(file);
                        document.getElementById('preview-video').src = url;
                        document.getElementById('file-info').innerHTML = `<i class="fas fa-video"></i> ${file.name}`;
                    }
                    showToast(`Loaded: ${file.name}`, 'success');
                }
            };
            input.click();
        }
        
        function applyTool(toolName) {
            if (!currentImageData) { showToast('Upload an image first!', 'error'); return; }
            const canvas = document.getElementById('preview-canvas');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            switch(toolName) {
                case 'grayscale':
                    for (let i = 0; i < data.length; i += 4) {
                        const gray = (data[i] + data[i+1] + data[i+2]) / 3;
                        data[i] = data[i+1] = data[i+2] = gray;
                    }
                    break;
                case 'sepia':
                    for (let i = 0; i < data.length; i += 4) {
                        const r = data[i], g = data[i+1], b = data[i+2];
                        data[i] = Math.min(255, r*0.393 + g*0.769 + b*0.189);
                        data[i+1] = Math.min(255, r*0.349 + g*0.686 + b*0.168);
                        data[i+2] = Math.min(255, r*0.272 + g*0.534 + b*0.131);
                    }
                    break;
                case 'invert':
                    for (let i = 0; i < data.length; i += 4) {
                        data[i] = 255 - data[i];
                        data[i+1] = 255 - data[i+1];
                        data[i+2] = 255 - data[i+2];
                    }
                    break;
                case 'blur':
                    const temp = new Uint8ClampedArray(data);
                    const w = canvas.width, h = canvas.height;
                    for (let y = 1; y < h-1; y++) {
                        for (let x = 1; x < w-1; x++) {
                            let r=0,g=0,b=0;
                            for (let ky=-1; ky<=1; ky++) {
                                for (let kx=-1; kx<=1; kx++) {
                                    const idx = ((y+ky)*w + (x+kx))*4;
                                    r += temp[idx];
                                    g += temp[idx+1];
                                    b += temp[idx+2];
                                }
                            }
                            const idx = (y*w + x)*4;
                            data[idx] = r/9; data[idx+1] = g/9; data[idx+2] = b/9;
                        }
                    }
                    break;
                case 'brightness':
                    for (let i = 0; i < data.length; i += 4) {
                        data[i] = Math.min(255, data[i] * 1.2);
                        data[i+1] = Math.min(255, data[i+1] * 1.2);
                        data[i+2] = Math.min(255, data[i+2] * 1.2);
                    }
                    break;
                case 'contrast':
                    for (let i = 0; i < data.length; i += 4) {
                        data[i] = Math.min(255, Math.max(0, (data[i]-128)*1.3+128));
                        data[i+1] = Math.min(255, Math.max(0, (data[i+1]-128)*1.3+128));
                        data[i+2] = Math.min(255, Math.max(0, (data[i+2]-128)*1.3+128));
                    }
                    break;
            }
            ctx.putImageData(imageData, 0, 0);
            currentImageData = imageData;
            showToast(`Applied: ${toolName}`, 'success');
        }
        
        function applyFilter(filterName) {
            applyTool(filterName);
        }
        
        function applyCurrent() {
            showToast('Effect applied!', 'success');
        }
        
        function exportFile() {
            if (currentImageData) {
                const canvas = document.getElementById('preview-canvas');
                const link = document.createElement('a');
                link.download = `kinva_edit_${Date.now()}.png`;
                link.href = canvas.toDataURL();
                link.click();
                showToast('Image exported!', 'success');
            } else {
                showToast('No file to export', 'error');
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
                showToast('Reset to original', 'success');
            }
        }
        
        function showPremium() {
            alert('⭐ Premium Features:\n• No Watermark\n• 4K Export\n• Priority Processing\n• All Filters\n\nUpgrade: $9.99/month');
        }
        
        loadTools();
        loadFilters();
    </script>
</body>
</html>
"""

# ============================================
# FLASK ROUTES
# ============================================

@flask_app.route('/')
def index():
    bot_id = Config.BOT_TOKEN.split(':')[0] if Config.BOT_TOKEN else "8791110410"
    return render_template_string(WEB_APP_HTML.replace('{{ BOT_ID }}', bot_id))

@flask_app.route('/admin')
def admin_panel():
    password = request.args.get('password', '')
    
    if password != Config.ADMIN_PASSWORD:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Login</title>
            <style>
                body {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    font-family: Arial, sans-serif;
                }
                .login-box {
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(20px);
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                }
                input {
                    padding: 12px 20px;
                    margin: 10px 0;
                    border: none;
                    border-radius: 10px;
                    width: 250px;
                }
                button {
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 10px;
                    color: white;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>Admin Login</h2>
                <form method="GET">
                    <input type="password" name="password" placeholder="Enter password"><br>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        '''
    
    stats = db.get_stats()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {{
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: white;
                font-family: Arial, sans-serif;
                padding: 20px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
            }}
        </style>
    </head>
    <body>
        <h1>Admin Panel</h1>
        <div class="stats">
            <div class="stat-card"><div class="stat-number">{stats['total_users']}</div><div>Total Users</div></div>
            <div class="stat-card"><div class="stat-number">{stats['premium_users']}</div><div>Premium Users</div></div>
            <div class="stat-card"><div class="stat-number">{stats['total_edits']}</div><div>Total Edits</div></div>
            <div class="stat-card"><div class="stat-number">{stats['today_edits']}</div><div>Today's Edits</div></div>
        </div>
        <a href="/" style="color: #667eea;">← Back to Editor</a>
    </body>
    </html>
    '''

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": "3.0.0"})

# ============================================
# SOCKETIO HANDLERS
# ============================================

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

# ============================================
# MAIN EXECUTION
# ============================================

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
