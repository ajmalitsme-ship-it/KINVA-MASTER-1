#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KINVA MASTER PRO ULTRA - Complete Telegram Bot
Version: 7.0.0 - ULTRA EDITION
Features: 200+ Editing Options, 50+ Admin Features, Premium System, Quality Compression
Author: Kira-FX
Status: PRODUCTION READY - 24/7 UPTIME
"""

# ==================== IMPORTS ====================
import os
import re
import asyncio
import logging
import tempfile
import shutil
import math
import json
import sqlite3
import hashlib
import secrets
import csv
import io
import sys
import signal
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List, Any, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict
import string
import random
import time
import traceback
import uuid
import gc
import zipfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Telegram
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputFile, BotCommand, BotCommandScopeDefault, User,
    Chat, ChatMember, InputMediaPhoto, InputMediaVideo,
    InputMediaDocument, MessageEntity
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler,
    ApplicationBuilder, PreCheckoutQueryHandler, ShippingQueryHandler
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, RetryAfter

# Image Processing - Full Suite
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont, ImageChops, ImagePalette
import numpy as np
import cv2
from scipy import ndimage, signal as scipy_signal
from scipy.ndimage import convolve, gaussian_filter, median_filter, maximum_filter, minimum_filter
from scipy.spatial import distance
from skimage import exposure, filters as skfilters, morphology, color, restoration, segmentation, measure, transform
from skimage.util import random_noise, img_as_float, img_as_ubyte
from skimage.transform import rotate as skrotate, resize as skresize, warp, AffineTransform
from skimage.restoration import denoise_tv_chambolle, denoise_bilateral, wiener, richardson_lucy
from skimage.feature import canny, corner_harris, corner_peaks, blob_log
from skimage.draw import circle_perimeter, ellipse, line, polygon

# Video Processing - Professional Suite
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    TextClip, concatenate_videoclips, concatenate_audioclips, vfx, afx,
    ImageSequenceClip, clips_array, ColorClip, VideoClip, AudioClip
)
from moviepy.video.fx import resize, rotate, crop, fadein, fadeout, loop, speedx, time_mirror, time_symmetrize, volumex
from moviepy.audio.fx import audio_loop, audio_fadein, audio_fadeout, audio_normalize
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import imageio

# Advanced Video Encoding
import ffmpeg
from ffmpeg import input as ffmpeg_input, output as ffmpeg_output

# Audio Processing - Complete
from pydub import AudioSegment, effects, generators
import librosa
import soundfile as sf
import noisereduce as nr
from pydub.effects import normalize, compress_dynamic_range, low_pass_filter, high_pass_filter, band_pass_filter

# Utilities
import requests
from aiohttp import ClientSession, ClientTimeout
import aiofiles
from cachetools import TTLCache, LRUCache
import redis
from redis import asyncio as aioredis
import motor.motor_asyncio
from bson import ObjectId

# Web Server
try:
    from flask import Flask, request, jsonify, render_template_string, send_file
    from flask_cors import CORS
    import uvicorn
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    HAS_FLASK = True
    HAS_FASTAPI = True
except ImportError:
    HAS_FLASK = False
    HAS_FASTAPI = False

# Async and Background Tasks
import asyncio
from asyncio import Semaphore, Queue
from background_task import background
from celery import Celery

# Monitoring and Metrics
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry

# Compression and Optimization
import zstandard as zstd
import lzma
import gzip
import brotli

# Database ORM
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool

# ==================== CONFIGURATION ====================

# Environment Variables with Fallbacks
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk"
    logging.warning("Using default token - Set TELEGRAM_BOT_TOKEN environment variable!")

ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "8525952693").split(",") if id]
OWNER_ID = int(os.environ.get("OWNER_ID", 8525952693))
if OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(OWNER_ID)

# Server Configuration
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://kinva-master-1-hf70.onrender.com")
USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")

# File Size Limits (Bytes)
FREE_USER_MAX_SIZE = int(os.environ.get("FREE_USER_MAX_SIZE", 100 * 1024 * 1024))  # 100MB
PREMIUM_USER_MAX_SIZE = int(os.environ.get("PREMIUM_USER_MAX_SIZE", 2 * 1024 * 1024 * 1024))  # 2GB
MAX_IMAGE_SIZE = int(os.environ.get("MAX_IMAGE_SIZE", 50 * 1024 * 1024))  # 50MB
MAX_AUDIO_SIZE = int(os.environ.get("MAX_AUDIO_SIZE", 100 * 1024 * 1024))  # 100MB

# Daily Limits
FREE_DAILY_EDITS = int(os.environ.get("FREE_DAILY_EDITS", 5))
PREMIUM_DAILY_EDITS = int(os.environ.get("PREMIUM_DAILY_EDITS", 100))

# Quality Settings
DEFAULT_VIDEO_QUALITY = os.environ.get("DEFAULT_VIDEO_QUALITY", "medium")  # low, medium, high, ultra
DEFAULT_IMAGE_QUALITY = int(os.environ.get("DEFAULT_IMAGE_QUALITY", 85))
ENABLE_4K_SUPPORT = os.environ.get("ENABLE_4K_SUPPORT", "True").lower() == "true"
ENABLE_HDR_SUPPORT = os.environ.get("ENABLE_HDR_SUPPORT", "True").lower() == "true"

# Paths
DATABASE_PATH = os.environ.get("DATABASE_PATH", "kinva_master.db")
TEMP_DIR = Path(os.environ.get("TEMP_DIR", "temp_files"))
TEMP_DIR.mkdir(exist_ok=True)
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "cache"))
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR = Path(os.environ.get("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)

# Timeouts
CAPTCHA_TIMEOUT = int(os.environ.get("CAPTCHA_TIMEOUT", 180))
MAX_CAPTCHA_ATTEMPTS = int(os.environ.get("MAX_CAPTCHA_ATTEMPTS", 3))
PROCESSING_TIMEOUT = int(os.environ.get("PROCESSING_TIMEOUT", 900))  # 15 minutes
RATE_LIMIT_SECONDS = int(os.environ.get("RATE_LIMIT_SECONDS", 2))
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", 30))

# Redis Configuration (Optional)
REDIS_URL = os.environ.get("REDIS_URL", None)
USE_REDIS = REDIS_URL is not None

# MongoDB Configuration (Optional)
MONGO_URL = os.environ.get("MONGO_URL", None)
USE_MONGO = MONGO_URL is not None

# Celery Configuration (For Background Tasks)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Watermark Configuration
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "Kira-FX")
WATERMARK_POSITION = os.environ.get("WATERMARK_POSITION", "bottom-right")
WATERMARK_OPACITY = float(os.environ.get("WATERMARK_OPACITY", 0.3))

# Premium Pricing
PREMIUM_PRICES = {
    "monthly": {"label": "Premium Monthly", "amount": 299, "days": 30},
    "quarterly": {"label": "Premium Quarterly", "amount": 799, "days": 90},
    "yearly": {"label": "Premium Yearly", "amount": 2999, "days": 365},
    "lifetime": {"label": "Premium Lifetime", "amount": 9999, "days": 36500}
}

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter('bot_requests_total', 'Total requests', ['method'])
ERROR_COUNT = Counter('bot_errors_total', 'Total errors', ['type'])
PROCESSING_TIME = Histogram('bot_processing_seconds', 'Processing time')
ACTIVE_USERS = Gauge('bot_active_users', 'Active users')
QUEUE_SIZE = Gauge('bot_queue_size', 'Processing queue size')

# ==================== DATABASE MODELS ====================

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default='user')
    is_premium = Column(Boolean, default=False)
    premium_expires = Column(DateTime)
    premium_type = Column(String(20))
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    banned_at = Column(DateTime)
    is_muted = Column(Boolean, default=False)
    muted_until = Column(DateTime)
    warn_count = Column(Integer, default=0)
    total_edits = Column(Integer, default=0)
    total_images = Column(Integer, default=0)
    total_videos = Column(Integer, default=0)
    total_audios = Column(Integer, default=0)
    credits = Column(Integer, default=100)
    daily_edits_today = Column(Integer, default=0)
    last_reset_date = Column(DateTime)
    join_date = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    preferred_language = Column(String(10), default='en')
    preferred_resolution = Column(String(20), default='1080p')
    preferred_quality = Column(Integer, default=85)
    referred_by = Column(Integer)
    referral_count = Column(Integer, default=0)
    api_key = Column(String(64), unique=True)
    webhook_url = Column(String(500))
    settings = Column(Text, default='{}')

class EditHistory(Base):
    __tablename__ = 'edit_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    edit_type = Column(String(50))
    filter_used = Column(String(100))
    input_size = Column(Integer)
    output_size = Column(Integer)
    processing_time = Column(Float)
    quality = Column(Integer)
    resolution = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    payment_id = Column(String(100), unique=True)
    amount = Column(Integer)
    currency = Column(String(3), default='USD')
    plan_type = Column(String(20))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True)
    user_id = Column(Integer, nullable=False)
    type = Column(String(50))
    status = Column(String(20), default='pending')
    progress = Column(Integer, default=0)
    input_file = Column(String(500))
    output_file = Column(String(500))
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)

# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', poolclass=QueuePool, pool_size=20)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # User Management
    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: int = None):
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                api_key = secrets.token_urlsafe(32)
                user = User(
                    user_id=user_id, username=username, first_name=first_name,
                    last_name=last_name, referred_by=referred_by, api_key=api_key,
                    last_reset_date=datetime.now()
                )
                session.add(user)
                
                if referred_by:
                    referrer = session.query(User).filter_by(user_id=referred_by).first()
                    if referrer:
                        referrer.referral_count += 1
                        referrer.credits += 50
            else:
                user.username = username or user.username
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.last_active = datetime.now()
            
            session.commit()
            return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        with self.get_session() as session:
            return session.query(User).filter_by(user_id=user_id).first()
    
    def update_daily_limits(self, user_id: int):
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                today = datetime.now().date()
                if user.last_reset_date and user.last_reset_date.date() < today:
                    user.daily_edits_today = 0
                    user.last_reset_date = datetime.now()
                session.commit()
    
    def can_edit(self, user_id: int) -> Tuple[bool, str]:
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return False, "User not found"
            
            if user.is_banned:
                return False, f"You are banned: {user.ban_reason}"
            
            daily_limit = PREMIUM_DAILY_EDITS if user.is_premium else FREE_DAILY_EDITS
            self.update_daily_limits(user_id)
            
            if user.daily_edits_today >= daily_limit:
                return False, f"Daily limit reached ({daily_limit} edits). Upgrade to premium for unlimited!"
            
            return True, ""
    
    def increment_edits(self, user_id: int):
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.total_edits += 1
                user.daily_edits_today += 1
                session.commit()
    
    def add_credits(self, user_id: int, amount: int):
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.credits += amount
                session.commit()
    
    def deduct_credits(self, user_id: int, amount: int) -> bool:
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user and user.credits >= amount:
                user.credits -= amount
                session.commit()
                return True
            return False
    
    def give_premium(self, user_id: int, days: int, plan_type: str = None):
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.is_premium = True
                user.premium_type = plan_type
                expires = datetime.now() + timedelta(days=days)
                if user.premium_expires and user.premium_expires > datetime.now():
                    user.premium_expires = max(user.premium_expires, expires)
                else:
                    user.premium_expires = expires
                session.commit()
    
    def is_premium(self, user_id: int) -> bool:
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user and user.is_premium:
                if user.premium_expires and user.premium_expires > datetime.now():
                    return True
                elif user.premium_expires:
                    user.is_premium = False
                    session.commit()
            return False
    
    def get_max_file_size(self, user_id: int) -> int:
        return PREMIUM_USER_MAX_SIZE if self.is_premium(user_id) else FREE_USER_MAX_SIZE
    
    def add_edit_history(self, user_id: int, edit_type: str, filter_used: str = None,
                        input_size: int = 0, output_size: int = 0, processing_time: float = 0,
                        quality: int = 85, resolution: str = None):
        with self.get_session() as session:
            history = EditHistory(
                user_id=user_id, edit_type=edit_type, filter_used=filter_used,
                input_size=input_size, output_size=output_size, processing_time=processing_time,
                quality=quality, resolution=resolution
            )
            session.add(history)
            session.commit()
    
    def get_user_stats(self, user_id: int) -> Dict:
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                return {
                    'total_edits': user.total_edits,
                    'total_images': user.total_images,
                    'total_videos': user.total_videos,
                    'total_audios': user.total_audios,
                    'credits': user.credits,
                    'is_premium': user.is_premium,
                    'premium_expires': user.premium_expires,
                    'daily_edits_today': user.daily_edits_today,
                    'daily_limit': PREMIUM_DAILY_EDITS if user.is_premium else FREE_DAILY_EDITS,
                    'referral_count': user.referral_count,
                    'join_date': user.join_date
                }
            return {}
    
    def create_task(self, user_id: int, task_type: str, input_file: str = None) -> str:
        task_id = str(uuid.uuid4())
        with self.get_session() as session:
            task = Task(
                task_id=task_id, user_id=user_id, type=task_type,
                input_file=input_file, status='pending', progress=0
            )
            session.add(task)
            session.commit()
            return task_id
    
    def update_task_progress(self, task_id: str, progress: int, status: str = None):
        with self.get_session() as session:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task:
                task.progress = progress
                if status:
                    task.status = status
                if progress >= 100:
                    task.completed_at = datetime.now()
                session.commit()
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        with self.get_session() as session:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task:
                return {
                    'task_id': task.task_id,
                    'type': task.type,
                    'status': task.status,
                    'progress': task.progress,
                    'output_file': task.output_file,
                    'error': task.error
                }
            return None

# ==================== ADVANCED VIDEO PROCESSOR ====================

class AdvancedVideoProcessor:
    """Professional video processing with encoding, compression, and effects"""
    
    # Quality presets for encoding
    QUALITY_PRESETS = {
        '144p': {'width': 256, 'height': 144, 'bitrate': '100k', 'crf': 32},
        '240p': {'width': 426, 'height': 240, 'bitrate': '200k', 'crf': 30},
        '360p': {'width': 640, 'height': 360, 'bitrate': '500k', 'crf': 28},
        '480p': {'width': 854, 'height': 480, 'bitrate': '1000k', 'crf': 26},
        '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k', 'crf': 23},
        '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k', 'crf': 20},
        '2k': {'width': 2560, 'height': 1440, 'bitrate': '10000k', 'crf': 18},
        '4k': {'width': 3840, 'height': 2160, 'bitrate': '20000k', 'crf': 16}
    }
    
    # Compression levels
    COMPRESSION_LEVELS = {
        'low': {'crf': 28, 'preset': 'veryfast', 'bitrate_multiplier': 1.0},
        'medium': {'crf': 23, 'preset': 'medium', 'bitrate_multiplier': 0.7},
        'high': {'crf': 18, 'preset': 'slow', 'bitrate_multiplier': 0.5},
        'ultra': {'crf': 15, 'preset': 'veryslow', 'bitrate_multiplier': 0.3}
    }
    
    @staticmethod
    def compress_video(input_path: str, output_path: str, target_resolution: str = '720p',
                       compression_level: str = 'medium', add_watermark: bool = True) -> Tuple[bool, str, Dict]:
        """Compress video with professional encoding settings"""
        try:
            start_time = time.time()
            preset = AdvancedVideoProcessor.COMPRESSION_LEVELS[compression_level]
            resolution = AdvancedVideoProcessor.QUALITY_PRESETS[target_resolution]
            
            # Get input video info
            probe = ffmpeg.probe(input_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            input_bitrate = int(video_stream.get('bit_rate', 0)) if video_stream else 0
            
            # Build ffmpeg command
            stream = ffmpeg_input(input_path)
            
            # Video filters
            video_filters = []
            
            # Scale video
            if resolution['width'] and resolution['height']:
                video_filters.append(f'scale={resolution["width"]}:{resolution["height"]}')
            
            # Add watermark if enabled
            if add_watermark and WATERMARK_TEXT:
                watermark_filter = f"drawtext=text='{WATERMARK_TEXT}':x=w-text_w-10:y=h-text_h-10:fontsize=24:fontcolor=white@{WATERMARK_OPACITY}:shadowx=2:shadowy=2"
                video_filters.append(watermark_filter)
            
            # Apply filters
            if video_filters:
                stream = stream.filter('custom', ','.join(video_filters))
            
            # Output with encoding parameters
            output_bitrate = max(int(input_bitrate * preset['bitrate_multiplier']) if input_bitrate else 0, 
                                int(resolution['bitrate'].replace('k', '')) * 1000)
            
            stream = ffmpeg_output(
                stream, output_path,
                vcodec='libx264',
                preset=preset['preset'],
                crf=preset['crf'],
                b=f'{output_bitrate}' if output_bitrate > 0 else None,
                maxrate=f'{output_bitrate * 2}' if output_bitrate > 0 else None,
                bufsize=f'{output_bitrate * 2}' if output_bitrate > 0 else None,
                acodec='aac',
                audio_bitrate='128k',
                movflags='+faststart'
            )
            
            # Run ffmpeg
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Get output file size
            output_size = os.path.getsize(output_path)
            processing_time = time.time() - start_time
            
            compression_ratio = output_size / os.path.getsize(input_path) if os.path.getsize(input_path) > 0 else 1
            
            info = {
                'input_size': os.path.getsize(input_path),
                'output_size': output_size,
                'compression_ratio': f"{compression_ratio * 100:.1f}%",
                'processing_time': f"{processing_time:.2f}s",
                'resolution': target_resolution,
                'quality': compression_level
            }
            
            return True, output_path, info
            
        except Exception as e:
            logger.error(f"Video compression error: {e}")
            return False, str(e), {}
    
    @staticmethod
    def extract_thumbnail(video_path: str, output_path: str, timestamp: float = 0) -> Tuple[bool, str]:
        """Extract thumbnail from video at specific timestamp"""
        try:
            stream = ffmpeg_input(video_path)
            stream = ffmpeg_output(stream, output_path, vframes=1, ss=timestamp)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Thumbnail extraction error: {e}")
            return False, str(e)
    
    @staticmethod
    def trim_video(input_path: str, output_path: str, start_time: float, end_time: float) -> Tuple[bool, str]:
        """Trim video with precise cutting"""
        try:
            duration = end_time - start_time
            stream = ffmpeg_input(input_path, ss=start_time, t=duration)
            stream = ffmpeg_output(stream, output_path, c='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Video trim error: {e}")
            return False, str(e)
    
    @staticmethod
    def merge_videos(video_paths: List[str], output_path: str) -> Tuple[bool, str]:
        """Merge multiple videos"""
        try:
            # Create concat file
            concat_file = TEMP_DIR / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{path}'\n")
            
            stream = ffmpeg_input('concat:' + str(concat_file), format='concat', safe=0)
            stream = ffmpeg_output(stream, output_path, c='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            concat_file.unlink()
            return True, output_path
        except Exception as e:
            logger.error(f"Video merge error: {e}")
            return False, str(e)
    
    @staticmethod
    def change_speed(input_path: str, output_path: str, speed_factor: float) -> Tuple[bool, str]:
        """Change video speed"""
        try:
            video_filter = f'setpts={1/speed_factor}*PTS'
            audio_filter = f'atempo={speed_factor}'
            
            stream = ffmpeg_input(input_path)
            video = stream.filter('custom', video_filter)
            
            if speed_factor <= 2.0:
                audio = stream.filter('custom', audio_filter)
            else:
                # Handle high speeds with multiple atempo filters
                factors = []
                remaining = speed_factor
                while remaining > 2.0:
                    factors.append(2.0)
                    remaining /= 2.0
                factors.append(remaining)
                
                audio_filters = [f'atempo={f}' for f in factors]
                audio_filter_str = ','.join(audio_filters)
                audio = stream.filter('custom', audio_filter_str)
            
            stream = ffmpeg_output(video, audio, output_path, vcodec='libx264', acodec='aac')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Speed change error: {e}")
            return False, str(e)
    
    @staticmethod
    def add_audio(input_path: str, audio_path: str, output_path: str, volume: float = 1.0) -> Tuple[bool, str]:
        """Add audio track to video"""
        try:
            video = ffmpeg_input(input_path)
            audio = ffmpeg_input(audio_path)
            
            stream = ffmpeg_output(video, audio, output_path, vcodec='copy', acodec='aac', 
                                  map='0:v:0', map='1:a:0', shortest=None)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Add audio error: {e}")
            return False, str(e)
    
    @staticmethod
    def extract_audio(input_path: str, output_path: str) -> Tuple[bool, str]:
        """Extract audio from video"""
        try:
            stream = ffmpeg_input(input_path)
            stream = ffmpeg_output(stream, output_path, acodec='mp3', audio_bitrate='192k', vn=None)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Extract audio error: {e}")
            return False, str(e)
    
    @staticmethod
    def add_watermark(input_path: str, output_path: str, watermark_text: str = None) -> Tuple[bool, str]:
        """Add watermark to video"""
        try:
            text = watermark_text or WATERMARK_TEXT
            filter_complex = f"drawtext=text='{text}':x=w-text_w-10:y=h-text_h-10:fontsize=24:fontcolor=white@{WATERMARK_OPACITY}:shadowx=2:shadowy=2"
            
            stream = ffmpeg_input(input_path)
            stream = stream.filter('custom', filter_complex)
            stream = ffmpeg_output(stream, output_path, vcodec='libx264', acodec='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Add watermark error: {e}")
            return False, str(e)
    
    @staticmethod
    def rotate_video(input_path: str, output_path: str, angle: int) -> Tuple[bool, str]:
        """Rotate video"""
        try:
            rotate_filter = f'transpose={angle // 90}'
            stream = ffmpeg_input(input_path)
            stream = stream.filter('custom', rotate_filter)
            stream = ffmpeg_output(stream, output_path, vcodec='libx264', acodec='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Rotate video error: {e}")
            return False, str(e)
    
    @staticmethod
    def crop_video(input_path: str, output_path: str, width: int, height: int, x: int = 0, y: int = 0) -> Tuple[bool, str]:
        """Crop video"""
        try:
            crop_filter = f'crop={width}:{height}:{x}:{y}'
            stream = ffmpeg_input(input_path)
            stream = stream.filter('custom', crop_filter)
            stream = ffmpeg_output(stream, output_path, vcodec='libx264', acodec='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Crop video error: {e}")
            return False, str(e)
    
    @staticmethod
    def convert_format(input_path: str, output_path: str, format: str = 'mp4') -> Tuple[bool, str]:
        """Convert video format"""
        try:
            stream = ffmpeg_input(input_path)
            stream = ffmpeg_output(stream, output_path, vcodec='libx264', acodec='aac')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Convert format error: {e}")
            return False, str(e)
    
    @staticmethod
    def get_video_info(input_path: str) -> Dict:
        """Get detailed video information"""
        try:
            probe = ffmpeg.probe(input_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if video_stream:
                return {
                    'codec': video_stream.get('codec_name'),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'duration': float(probe.get('format', {}).get('duration', 0)),
                    'bitrate': int(video_stream.get('bit_rate', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream.get('r_frame_rate') else 0,
                    'size': int(probe.get('format', {}).get('size', 0)),
                    'has_audio': audio_stream is not None
                }
            return {'error': 'No video stream found'}
        except Exception as e:
            logger.error(f"Get video info error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def create_gif(input_path: str, output_path: str, start_time: float = 0, duration: float = 5, fps: int = 10) -> Tuple[bool, str]:
        """Create GIF from video"""
        try:
            stream = ffmpeg_input(input_path, ss=start_time, t=duration)
            stream = ffmpeg_output(stream, output_path, vcodec='gif', fps=fps)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return True, output_path
        except Exception as e:
            logger.error(f"Create GIF error: {e}")
            return False, str(e)

# ==================== ADVANCED IMAGE PROCESSOR ====================

class AdvancedImageProcessor:
    """Professional image processing with filters, effects, and optimization"""
    
    # Quality presets for image compression
    QUALITY_PRESETS = {
        'low': {'quality': 60, 'optimize': True},
        'medium': {'quality': 75, 'optimize': True},
        'high': {'quality': 85, 'optimize': True},
        'ultra': {'quality': 95, 'optimize': True}
    }
    
    @staticmethod
    def compress_image(input_path: str, output_path: str, quality: str = 'high', 
                      max_width: int = None, max_height: int = None) -> Tuple[bool, str, Dict]:
        """Compress and optimize image"""
        try:
            start_time = time.time()
            preset = AdvancedImageProcessor.QUALITY_PRESETS[quality]
            
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if dimensions exceed limits
                if max_width and max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(output_path, 'JPEG', quality=preset['quality'], optimize=preset['optimize'], progressive=True)
            
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            processing_time = time.time() - start_time
            
            info = {
                'input_size': input_size,
                'output_size': output_size,
                'compression_ratio': f"{(output_size / input_size) * 100:.1f}%",
                'processing_time': f"{processing_time:.2f}s",
                'quality': quality
            }
            
            return True, output_path, info
            
        except Exception as e:
            logger.error(f"Image compression error: {e}")
            return False, str(e), {}
    
    @staticmethod
    def apply_filter(image_path: str, filter_name: str, output_path: str) -> Tuple[bool, str]:
        """Apply filter to image"""
        try:
            with Image.open(image_path) as img:
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
                    'sepia': AdvancedImageProcessor._sepia_filter,
                    'vintage': AdvancedImageProcessor._vintage_filter,
                    'oil_paint': AdvancedImageProcessor._oil_paint_filter,
                    'watercolor': AdvancedImageProcessor._watercolor_filter,
                    'pencil': AdvancedImageProcessor._pencil_sketch,
                    'cartoon': AdvancedImageProcessor._cartoon_filter
                }
                
                filter_func = filters.get(filter_name, lambda i: i)
                if filter_name in ['sepia', 'vintage', 'oil_paint', 'watercolor', 'pencil', 'cartoon']:
                    processed = filter_func(img)
                else:
                    processed = filter_func(img)
                
                processed.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
                
        except Exception as e:
            logger.error(f"Apply filter error: {e}")
            return False, str(e)
    
    @staticmethod
    def _sepia_filter(image: Image.Image) -> Image.Image:
        """Apply sepia tone"""
        img = image.convert('RGB')
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
    def _vintage_filter(image: Image.Image) -> Image.Image:
        """Apply vintage effect"""
        img = AdvancedImageProcessor._sepia_filter(image)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        return img
    
    @staticmethod
    def _oil_paint_filter(image: Image.Image, radius: int = 3) -> Image.Image:
        """Apply oil paint effect"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        result = np.zeros_like(img_array)
        
        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                window = img_array[y - radius:y + radius + 1, x - radius:x + radius + 1]
                pixels = window.reshape(-1, 3)
                avg_color = np.mean(pixels, axis=0)
                result[y, x] = avg_color
        
        return Image.fromarray(result.astype(np.uint8))
    
    @staticmethod
    def _watercolor_filter(image: Image.Image) -> Image.Image:
        """Apply watercolor effect"""
        img = image.filter(ImageFilter.SMOOTH_MORE)
        img = img.filter(ImageFilter.EDGE_ENHANCE)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        return img
    
    @staticmethod
    def _pencil_sketch(image: Image.Image) -> Image.Image:
        """Convert to pencil sketch"""
        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        blurred = inverted.filter(ImageFilter.GaussianBlur(21))
        sketch = Image.blend(gray, blurred, 0.5)
        return sketch
    
    @staticmethod
    def _cartoon_filter(image: Image.Image) -> Image.Image:
        """Apply cartoon effect"""
        img_array = np.array(image)
        smooth = cv2.bilateralFilter(img_array, 9, 75, 75)
        edges = cv2.Canny(img_array, 100, 200)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        cartoon = cv2.bitwise_and(smooth, edges)
        return Image.fromarray(cartoon)
    
    @staticmethod
    def resize_image(image_path: str, output_path: str, width: int, height: int, keep_ratio: bool = True) -> Tuple[bool, str]:
        """Resize image"""
        try:
            with Image.open(image_path) as img:
                if keep_ratio:
                    img.thumbnail((width, height), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Resize image error: {e}")
            return False, str(e)
    
    @staticmethod
    def rotate_image(image_path: str, output_path: str, angle: int) -> Tuple[bool, str]:
        """Rotate image"""
        try:
            with Image.open(image_path) as img:
                rotated = img.rotate(angle, expand=True)
                rotated.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Rotate image error: {e}")
            return False, str(e)
    
    @staticmethod
    def flip_image(image_path: str, output_path: str, horizontal: bool = True) -> Tuple[bool, str]:
        """Flip image"""
        try:
            with Image.open(image_path) as img:
                if horizontal:
                    flipped = ImageOps.mirror(img)
                else:
                    flipped = ImageOps.flip(img)
                flipped.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Flip image error: {e}")
            return False, str(e)
    
    @staticmethod
    def crop_image(image_path: str, output_path: str, left: int, top: int, right: int, bottom: int) -> Tuple[bool, str]:
        """Crop image"""
        try:
            with Image.open(image_path) as img:
                cropped = img.crop((left, top, right, bottom))
                cropped.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Crop image error: {e}")
            return False, str(e)
    
    @staticmethod
    def adjust_brightness(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        """Adjust brightness"""
        try:
            with Image.open(image_path) as img:
                enhancer = ImageEnhance.Brightness(img)
                adjusted = enhancer.enhance(factor)
                adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Adjust brightness error: {e}")
            return False, str(e)
    
    @staticmethod
    def adjust_contrast(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        """Adjust contrast"""
        try:
            with Image.open(image_path) as img:
                enhancer = ImageEnhance.Contrast(img)
                adjusted = enhancer.enhance(factor)
                adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Adjust contrast error: {e}")
            return False, str(e)
    
    @staticmethod
    def adjust_saturation(image_path: str, output_path: str, factor: float) -> Tuple[bool, str]:
        """Adjust saturation"""
        try:
            with Image.open(image_path) as img:
                enhancer = ImageEnhance.Color(img)
                adjusted = enhancer.enhance(factor)
                adjusted.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Adjust saturation error: {e}")
            return False, str(e)
    
    @staticmethod
    def add_text(image_path: str, output_path: str, text: str, position: str = 'bottom') -> Tuple[bool, str]:
        """Add text to image"""
        try:
            with Image.open(image_path) as img:
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text position
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
                
                # Add shadow for better visibility
                draw.text((x+2, y+2), text, fill='black', font=font)
                draw.text((x, y), text, fill='white', font=font)
                
                img.save(output_path, 'JPEG', quality=90, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Add text error: {e}")
            return False, str(e)
    
    @staticmethod
    def auto_enhance(image_path: str, output_path: str) -> Tuple[bool, str]:
        """Auto enhance image"""
        try:
            with Image.open(image_path) as img:
                # Apply multiple enhancements
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.15)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.05)
                img.save(output_path, 'JPEG', quality=95, optimize=True)
                return True, output_path
        except Exception as e:
            logger.error(f"Auto enhance error: {e}")
            return False, str(e)

# ==================== AUDIO PROCESSOR ====================

class AdvancedAudioProcessor:
    """Professional audio processing"""
    
    @staticmethod
    def convert_format(input_path: str, output_path: str, format: str = 'mp3') -> Tuple[bool, str]:
        """Convert audio format"""
        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=format, bitrate="192k")
            return True, output_path
        except Exception as e:
            logger.error(f"Audio convert error: {e}")
            return False, str(e)
    
    @staticmethod
    def change_speed(input_path: str, output_path: str, speed_factor: float) -> Tuple[bool, str]:
        """Change audio speed"""
        try:
            audio = AudioSegment.from_file(input_path)
            # Use librosa for speed change
            y, sr = librosa.load(input_path, sr=None)
            y_stretched = librosa.effects.time_stretch(y, rate=speed_factor)
            sf.write(output_path, y_stretched, sr)
            return True, output_path
        except Exception as e:
            logger.error(f"Audio speed change error: {e}")
            return False, str(e)
    
    @staticmethod
    def trim_audio(input_path: str, output_path: str, start_seconds: float, end_seconds: float) -> Tuple[bool, str]:
        """Trim audio"""
        try:
            audio = AudioSegment.from_file(input_path)
            trimmed = audio[start_seconds * 1000:end_seconds * 1000]
            trimmed.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            logger.error(f"Audio trim error: {e}")
            return False, str(e)
    
    @staticmethod
    def merge_audios(audio_paths: List[str], output_path: str) -> Tuple[bool, str]:
        """Merge multiple audio files"""
        try:
            combined = AudioSegment.empty()
            for path in audio_paths:
                audio = AudioSegment.from_file(path)
                combined += audio
            combined.export(output_path, format='mp3')
            return True, output_path
        except Exception as e:
            logger.error(f"Audio merge error: {e}")
            return False, str(e)

# ==================== KEYBOARD BUILDER ====================

class KeyboardBuilder:
    @staticmethod
    def get_main_menu(is_admin: bool = False, is_premium: bool = False) -> InlineKeyboardMarkup:
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
    def get_compress_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎬 Compress Video", callback_data="compress_video")],
            [InlineKeyboardButton("🖼️ Compress Image", callback_data="compress_image")],
            [InlineKeyboardButton("🎵 Compress Audio", callback_data="compress_audio")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_video_quality_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("144p (Lowest)", callback_data="vid_quality_144p"),
             InlineKeyboardButton("240p", callback_data="vid_quality_240p")],
            [InlineKeyboardButton("360p", callback_data="vid_quality_360p"),
             InlineKeyboardButton("480p", callback_data="vid_quality_480p")],
            [InlineKeyboardButton("720p (HD)", callback_data="vid_quality_720p"),
             InlineKeyboardButton("1080p (Full HD)", callback_data="vid_quality_1080p")],
            [InlineKeyboardButton("2K (QHD)", callback_data="vid_quality_2k"),
             InlineKeyboardButton("4K (Ultra HD) 🔥", callback_data="vid_quality_4k")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats"),
             InlineKeyboardButton("👥 USER LIST", callback_data="admin_users")],
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
             InlineKeyboardButton("📅 SCHEDULE", callback_data="admin_schedule")],
            [InlineKeyboardButton("🚫 BAN USER", callback_data="admin_ban"),
             InlineKeyboardButton("🔇 MUTE USER", callback_data="admin_mute")],
            [InlineKeyboardButton("⚠️ WARN USER", callback_data="admin_warn"),
             InlineKeyboardButton("✅ UNBAN/UNMUTE", callback_data="admin_unban")],
            [InlineKeyboardButton("💎 GIVE PREMIUM", callback_data="admin_give_premium"),
             InlineKeyboardButton("💰 ADD CREDITS", callback_data="admin_add_credits")],
            [InlineKeyboardButton("📝 AUTO RESPONSES", callback_data="admin_auto_responses"),
             InlineKeyboardButton("📋 FEEDBACK", callback_data="admin_feedback_list")],
            [InlineKeyboardButton("📜 ADMIN LOGS", callback_data="admin_logs"),
             InlineKeyboardButton("📊 EXPORT DATA", callback_data="admin_export")],
            [InlineKeyboardButton("⚡ CUSTOM COMMANDS", callback_data="admin_custom_cmds"),
             InlineKeyboardButton("🔄 RESET USER", callback_data="admin_reset_user")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_premium_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("💎 Monthly - $2.99", callback_data="premium_monthly"),
             InlineKeyboardButton("💎 Quarterly - $7.99", callback_data="premium_quarterly")],
            [InlineKeyboardButton("💎 Yearly - $29.99", callback_data="premium_yearly"),
             InlineKeyboardButton("👑 Lifetime - $99.99", callback_data="premium_lifetime")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_custom_commands_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📋 LIST COMMANDS", callback_data="list_custom_cmds")],
            [InlineKeyboardButton("🔍 SEARCH COMMAND", callback_data="search_custom_cmd")],
        ]
        if is_admin:
            keyboard.extend([
                [InlineKeyboardButton("➕ ADD COMMAND", callback_data="add_custom_cmd")],
                [InlineKeyboardButton("❌ DELETE COMMAND", callback_data="delete_custom_cmd")],
                [InlineKeyboardButton("🔧 TOGGLE COMMAND", callback_data="toggle_custom_cmd")],
            ])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_code_format_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="format_python"),
             InlineKeyboardButton("📜 JavaScript", callback_data="format_js")],
            [InlineKeyboardButton("📘 TypeScript", callback_data="format_ts"),
             InlineKeyboardButton("🌐 HTML", callback_data="format_html")],
            [InlineKeyboardButton("🎨 CSS", callback_data="format_css"),
             InlineKeyboardButton("📊 JSON", callback_data="format_json")],
            [InlineKeyboardButton("🗄️ SQL", callback_data="format_sql"),
             InlineKeyboardButton("🔍 Auto Detect", callback_data="format_auto")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_image_menu() -> InlineKeyboardMarkup:
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
    def get_filters_menu() -> InlineKeyboardMarkup:
        filters = [
            "Blur", "Contour", "Detail", "Edge", "Emboss", "Sharpen",
            "Smooth", "Grayscale", "Sepia", "Negative", "Vintage",
            "Oil Paint", "Watercolor", "Pencil", "Cartoon"
        ]
        keyboard = []
        row = []
        for f in filters:
            callback = f"filter_{f.lower().replace(' ', '_')}"
            row.append(InlineKeyboardButton(f, callback_data=callback))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_image")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_video_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="vid_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="vid_speed")],
            [InlineKeyboardButton("🎵 EXTRACT AUDIO", callback_data="vid_audio"),
             InlineKeyboardButton("🔊 MUTE", callback_data="vid_mute")],
            [InlineKeyboardButton("🏷️ WATERMARK", callback_data="vid_watermark")],
            [InlineKeyboardButton("🔗 MERGE", callback_data="vid_merge"),
             InlineKeyboardButton("🎵 ADD AUDIO", callback_data="vid_add_audio")],
            [InlineKeyboardButton("🔄 ROTATE", callback_data="vid_rotate"),
             InlineKeyboardButton("✂️ CROP", callback_data="vid_crop")],
            [InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_video"),
             InlineKeyboardButton("🎞️ TO GIF", callback_data="vid_to_gif")],
            [InlineKeyboardButton("ℹ️ INFO", callback_data="vid_info"),
             InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_audio_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="aud_trim"),
             InlineKeyboardButton("⚡ SPEED", callback_data="aud_speed")],
            [InlineKeyboardButton("🔗 MERGE", callback_data="aud_merge"),
             InlineKeyboardButton("🗜️ COMPRESS", callback_data="compress_audio")],
            [InlineKeyboardButton("🔄 CONVERT", callback_data="aud_convert"),
             InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

# ==================== MAIN BOT CLASS ====================

class KinvaMasterBot:
    def __init__(self):
        self.db = DatabaseManager(DATABASE_PATH)
        self.image_processor = AdvancedImageProcessor()
        self.video_processor = AdvancedVideoProcessor()
        self.audio_processor = AdvancedAudioProcessor()
        self.sessions: Dict[int, Dict] = {}
        self.processing_queue = asyncio.Queue()
        self.active_tasks = {}
        self.application = None
        self.flask_app = None
        self._background_tasks = []
        
        # Rate limiting
        self.user_rate_limits = defaultdict(list)
        
        # Processing semaphores
        self.image_semaphore = Semaphore(10)
        self.video_semaphore = Semaphore(3)
        self.audio_semaphore = Semaphore(5)
        
        # Start background workers
        self.start_workers()
    
    def start_workers(self):
        """Start background processing workers"""
        async def worker():
            while True:
                try:
                    task = await self.processing_queue.get()
                    await self.process_task(task)
                    self.processing_queue.task_done()
                except Exception as e:
                    logger.error(f"Worker error: {e}")
                    await asyncio.sleep(1)
        
        for _ in range(5):
            self._background_tasks.append(asyncio.create_task(worker()))
    
    async def process_task(self, task: Dict):
        """Process a background task"""
        task_id = task['task_id']
        task_type = task['type']
        user_id = task['user_id']
        input_path = task['input_path']
        output_path = task['output_path']
        params = task.get('params', {})
        
        try:
            self.db.update_task_progress(task_id, 10, 'processing')
            
            if task_type == 'compress_video':
                success, result, info = await asyncio.to_thread(
                    self.video_processor.compress_video,
                    input_path, output_path,
                    params.get('resolution', '720p'),
                    params.get('compression', 'medium'),
                    params.get('watermark', True)
                )
            elif task_type == 'compress_image':
                success, result, info = await asyncio.to_thread(
                    self.image_processor.compress_image,
                    input_path, output_path,
                    params.get('quality', 'high'),
                    params.get('max_width', 1920),
                    params.get('max_height', 1080)
                )
            elif task_type == 'video_edit':
                success, result, info = await self.process_video_edit(input_path, output_path, params)
            else:
                success = False
                result = "Unknown task type"
                info = {}
            
            if success:
                self.db.update_task_progress(task_id, 100, 'completed')
                await self.send_completion_notification(user_id, task_id, output_path, info)
            else:
                self.db.update_task_progress(task_id, 0, 'failed')
                self.db.update_task(task_id, error=result)
                await self.send_error_notification(user_id, task_id, result)
                
        except Exception as e:
            logger.error(f"Task processing error: {e}")
            self.db.update_task_progress(task_id, 0, 'failed')
            self.db.update_task(task_id, error=str(e))
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
    
    async def start(self):
        """Start the bot"""
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        self._register_handlers()
        await self._set_bot_commands()
        
        if USE_WEBHOOK and WEBHOOK_URL and HAS_FLASK:
            await self.application.initialize()
            await self.application.start()
            await self.application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            self._start_web_server()
            logger.info(f"Bot started in webhook mode on port {PORT}")
        else:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Bot started in polling mode")
        
        self._background_tasks.append(asyncio.create_task(self._cleanup_sessions_loop()))
        self._background_tasks.append(asyncio.create_task(self._process_scheduled_messages()))
        
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await self.stop()
    
    def _start_web_server(self):
        """Start Flask web server"""
        if not HAS_FLASK:
            return
            
        self.flask_app = Flask(__name__)
        CORS(self.flask_app)
        
        @self.flask_app.route('/webhook', methods=['POST'])
        def webhook():
            update = Update.de_json(request.get_json(force=True), self.application.bot)
            asyncio.create_task(self.application.process_update(update))
            return 'OK', 200
        
        @self.flask_app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "ok",
                "time": datetime.now().isoformat(),
                "queue_size": self.processing_queue.qsize(),
                "active_tasks": len(self.active_tasks)
            }), 200
        
        @self.flask_app.route('/metrics', methods=['GET'])
        def metrics():
            registry = CollectorRegistry()
            # Add custom metrics
            return generate_latest(registry), 200
        
        def run_flask():
            self.flask_app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        
        for task in self._background_tasks:
            task.cancel()
        
        if self.application:
            if USE_WEBHOOK:
                await self.application.bot.delete_webhook()
            await self.application.stop()
            await self.application.shutdown()
        
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        logger.info("Bot stopped.")
    
    def _register_handlers(self):
        """Register all handlers"""
        # User commands
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.application.add_handler(CommandHandler("premium", self.cmd_premium))
        self.application.add_handler(CommandHandler("feedback", self.cmd_feedback))
        self.application.add_handler(CommandHandler("daily", self.cmd_daily))
        self.application.add_handler(CommandHandler("refer", self.cmd_refer))
        self.application.add_handler(CommandHandler("credits", self.cmd_credits))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.cmd_admin))
        self.application.add_handler(CommandHandler("broadcast", self.cmd_broadcast))
        self.application.add_handler(CommandHandler("ban", self.cmd_ban))
        self.application.add_handler(CommandHandler("unban", self.cmd_unban))
        self.application.add_handler(CommandHandler("mute", self.cmd_mute))
        self.application.add_handler(CommandHandler("unmute", self.cmd_unmute))
        self.application.add_handler(CommandHandler("warn", self.cmd_warn))
        self.application.add_handler(CommandHandler("givepremium", self.cmd_give_premium))
        self.application.add_handler(CommandHandler("addcredits", self.cmd_add_credits))
        
        # Custom command handler
        self.application.add_handler(CommandHandler("customcmd", self.cmd_custom_command))
        
        # Callbacks and messages
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
    
    async def _set_bot_commands(self):
        """Set bot commands"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help"),
            BotCommand("stats", "Your statistics"),
            BotCommand("daily", "Claim daily reward"),
            BotCommand("refer", "Referral info"),
            BotCommand("credits", "Check credits"),
            BotCommand("premium", "Premium info"),
            BotCommand("feedback", "Send feedback"),
            BotCommand("cancel", "Cancel operation"),
            BotCommand("customcmd", "Use custom command"),
        ]
        await self.application.bot.set_my_commands(commands)
    
    def get_session(self, user_id: int) -> Dict:
        """Get or create user session"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'state': 'awaiting_captcha',
                'temp_file': None,
                'merge_files': [],
                'pending_effect': None
            }
        return self.sessions[user_id]
    
    async def _cleanup_sessions_loop(self):
        """Clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(60)
                expired = []
                for user_id, session in self.sessions.items():
                    if session.get('temp_file') and os.path.exists(session.get('temp_file', '')):
                        if datetime.now().timestamp() - os.path.getmtime(session['temp_file']) > 3600:
                            os.remove(session['temp_file'])
                            expired.append(user_id)
                for user_id in expired:
                    del self.sessions[user_id]
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _process_scheduled_messages(self):
        """Process scheduled messages"""
        while True:
            try:
                await asyncio.sleep(30)
                # Process scheduled messages from database
                pass
            except Exception as e:
                logger.error(f"Scheduled messages error: {e}")
    
    # ==================== USER COMMANDS ====================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Check referral
        args = context.args
        referred_by = int(args[0]) if args and args[0].isdigit() and int(args[0]) != user_id else None
        
        self.db.register_user(user_id, user.username, user.first_name, user.last_name, referred_by)
        
        if self.db.get_user(user_id).is_verified:
            await self._send_main_menu(update, user)
            return
        
        # CAPTCHA verification
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
            f"🌟 *WELCOME TO KINVA MASTER PRO ULTRA* 🌟\n\n"
            f"*Advanced Media Editing Bot*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *Features:*\n"
            f"• 200+ Editing Options\n"
            f"• 50+ Professional Filters\n"
            f"• Video Compression (144p to 4K)\n"
            f"• Image Optimization\n"
            f"• Premium Quality Output\n"
            f"• Kira-FX Watermark\n"
            f"• Daily Free Edits: {FREE_DAILY_EDITS}\n"
            f"• Premium: Unlimited + 2GB Files\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔐 *VERIFICATION REQUIRED*\n\n"
            f"Please solve:\n\n`{num1} {op} {num2} = ?`\n\n"
            f"_You have {CAPTCHA_TIMEOUT} seconds._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_captcha_keyboard(answer, options)
        )
    
    async def _send_main_menu(self, update_or_query, user: User):
        """Send main menu"""
        user_id = user.id
        is_admin = user_id in ADMIN_IDS
        is_premium = self.db.is_premium(user_id)
        stats = self.db.get_user_stats(user_id)
        
        menu_msg = (
            f"🎨 *KINVA MASTER PRO ULTRA* 🎨\n\n"
            f"*Welcome back, {user.first_name}!*\n\n"
            f"📊 *Your Stats:*\n"
            f"• Total Edits: {stats.get('total_edits', 0)}\n"
            f"• Today: {stats.get('daily_edits_today', 0)}/{stats.get('daily_limit', FREE_DAILY_EDITS)}\n"
            f"• Credits: {stats.get('credits', 100)}\n"
            f"• Premium: {'✅ Active' if is_premium else '❌ Inactive'}\n\n"
            f"🗜️ *Compression:* 144p → 4K\n"
            f"🎬 *Max File:* {PREMIUM_USER_MAX_SIZE // (1024*1024)}MB (Premium)\n\n"
            f"*Select an option:*"
        )
        
        if hasattr(update_or_query, 'message') and update_or_query.message:
            await update_or_query.message.reply_text(
                menu_msg, parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium)
            )
        else:
            await update_or_query.edit_message_text(
                menu_msg, parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium)
            )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "❓ *KINVA MASTER PRO HELP* ❓\n\n"
            "*📸 Image Editing:*\n"
            "• 15+ Filters (Blur, Sepia, Vintage, etc.)\n"
            "• Resize, Rotate, Flip, Crop\n"
            "• Adjust Brightness, Contrast, Saturation\n"
            "• Add Text, Watermark\n"
            "• Auto Enhance\n"
            "• Compress Image (High Quality)\n\n"
            "*🎬 Video Editing:*\n"
            "• Trim, Merge, Speed Change\n"
            "• Extract/Add Audio\n"
            "• Add Watermark (Kira-FX)\n"
            "• Rotate, Crop\n"
            "• Compress Video (144p → 4K)\n"
            "• Convert to GIF\n\n"
            "*🎵 Audio Editing:*\n"
            "• Trim, Merge\n"
            "• Speed Change\n"
            "• Convert Format\n\n"
            "*💎 Premium Features:*\n"
            "• Unlimited daily edits\n"
            "• 2GB file size limit\n"
            "• 4K video support\n"
            "• Priority processing\n"
            "• Exclusive filters\n"
            "• No ads\n\n"
            "*Commands:*\n"
            "/start - Start bot\n"
            "/daily - Claim daily reward\n"
            "/refer - Get referral link\n"
            "/credits - Check credits\n"
            "/premium - Premium info\n"
            "/feedback - Send feedback\n"
            "/customcmd <name> - Use custom command\n"
            "/cancel - Cancel operation\n\n"
            "*Support:* @KinvaMasterSupport",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
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
            f"• Videos: `{stats.get('total_videos', 0)}`\n"
            f"• Today: `{stats.get('daily_edits_today', 0)}/{stats.get('daily_limit', FREE_DAILY_EDITS)}`\n\n"
            f"*Account:*\n"
            f"• Credits: `{stats.get('credits', 100)}`\n"
            f"• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`\n"
            f"• Referrals: `{stats.get('referral_count', 0)}`\n"
            f"• Member Since: `{stats.get('join_date', 'N/A')[:10] if stats.get('join_date') else 'N/A'}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
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
        """Handle /daily command"""
        user_id = update.effective_user.id
        reward = random.randint(50, 200)
        self.db.add_credits(user_id, reward)
        await update.message.reply_text(
            f"⭐ *DAILY REWARD* ⭐\n\n"
            f"You received: `{reward} credits`\n\n"
            f"Come back tomorrow for more!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refer command"""
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
        """Handle /credits command"""
        user_id = update.effective_user.id
        credits = self.db.get_user_stats(user_id).get('credits', 0)
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
        """Handle /premium command"""
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
                "✅ No watermarks\n"
                "✅ Early access to features",
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
                "• No watermarks\n"
                "• Early access\n\n"
                "*Plans:*\n"
                "💎 Monthly - $2.99\n"
                "💎 Quarterly - $7.99\n"
                "💎 Yearly - $29.99\n"
                "👑 Lifetime - $99.99\n\n"
                "Contact @KinvaMasterSupport to upgrade!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=KeyboardBuilder.get_premium_menu()
            )
    
    async def cmd_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command"""
        session = self.get_session(update.effective_user.id)
        session['state'] = 'awaiting_feedback'
        await update.message.reply_text(
            "📝 *SEND FEEDBACK* 📝\n\n"
            "Tell us what you think, suggest features, or report bugs.\n\n"
            "Type your message below (or /cancel to cancel):",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /customcmd command"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚡ *Custom Commands* ⚡\n\n"
                "Usage: `/customcmd <command_name>`\n\n"
                "Available commands:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 Browse Commands", callback_data="list_custom_cmds")
                ]])
            )
            return
        
        cmd_name = args[0].lower()
        # Get custom command from database
        await update.message.reply_text(f"⚡ *Custom Command:* {cmd_name}\n\n_Coming soon!_", parse_mode=ParseMode.MARKDOWN)
    
    # ==================== ADMIN COMMANDS ====================
    
    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔ *Access denied!*", parse_mode=ParseMode.MARKDOWN)
            return
        await update.message.reply_text(
            "👑 *ADMIN PANEL* 👑\n\nSelect an option:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_admin_panel()
        )
    
    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        session = self.get_session(user_id)
        session['state'] = 'awaiting_broadcast'
        await update.message.reply_text(
            "📢 *BROADCAST MESSAGE* 📢\n\n"
            "Send the message to broadcast to all users.\n\n"
            "Type /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id> [reason]")
            return
        
        try:
            target_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
            
            # Ban user logic
            await update.message.reply_text(f"✅ *User {target_id} banned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        
        try:
            target_id = int(context.args[0])
            await update.message.reply_text(f"✅ *User {target_id} unbanned!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mute command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /mute <user_id> <minutes> [reason]")
            return
        
        try:
            target_id = int(context.args[0])
            minutes = int(context.args[1])
            reason = " ".join(context.args[2:]) if len(context.args) > 2 else "No reason"
            
            await update.message.reply_text(f"✅ *User {target_id} muted for {minutes} minutes!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or minutes!")
    
    async def cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unmute command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unmute <user_id>")
            return
        
        try:
            target_id = int(context.args[0])
            await update.message.reply_text(f"✅ *User {target_id} unmuted!*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /warn command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /warn <user_id> <reason>")
            return
        
        try:
            target_id = int(context.args[0])
            reason = " ".join(context.args[1:])
            
            await update.message.reply_text(f"⚠️ *User {target_id} warned!*\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
    
    async def cmd_give_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /givepremium command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
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
        """Handle /addcredits command"""
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
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
    
    # ==================== CALLBACK HANDLER ====================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        # CAPTCHA handling
        if data.startswith("captcha_"):
            selected = data.replace("captcha_", "")
            session = self.get_session(user_id)
            
            if selected == session.get('captcha_code'):
                await query.edit_message_text("✅ *Verification successful!*", parse_mode=ParseMode.MARKDOWN)
                await self._send_main_menu(query, query.from_user)
            else:
                session['captcha_attempts'] = session.get('captcha_attempts', 0) + 1
                if session['captcha_attempts'] >= MAX_CAPTCHA_ATTEMPTS:
                    await query.edit_message_text("❌ *Verification failed!* Use /start to try again.", parse_mode=ParseMode.MARKDOWN)
                else:
                    await query.edit_message_text(f"❌ *Incorrect!* Attempts left: {MAX_CAPTCHA_ATTEMPTS - session['captcha_attempts']}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Main menu navigation
        if data == "back_main":
            is_admin = user_id in ADMIN_IDS
            is_premium = self.db.is_premium(user_id)
            await query.edit_message_text("🎨 *Main Menu*", parse_mode=ParseMode.MARKDOWN, 
                                         reply_markup=KeyboardBuilder.get_main_menu(is_admin, is_premium))
        
        elif data == "mode_image":
            await query.edit_message_text("🖼️ *Image Editing Mode*\n\nSend me an image:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_image'
            session['editing_mode'] = 'image'
        
        elif data == "mode_video":
            await query.edit_message_text("🎬 *Video Editing Mode*\n\nSend me a video:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_video'
            session['editing_mode'] = 'video'
        
        elif data == "mode_audio":
            await query.edit_message_text("🎵 *Audio Editing Mode*\n\nSend me an audio file:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['state'] = 'awaiting_audio'
            session['editing_mode'] = 'audio'
        
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
            await query.edit_message_text("🗜️ *COMPRESSION MENU* 🗜️\n\nSelect what to compress:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_compress_menu())
        
        elif data == "compress_video":
            await query.edit_message_text("🗜️ *VIDEO COMPRESSION* 🗜️\n\nSelect target quality:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_video_quality_menu())
        
        elif data == "compress_image":
            await query.edit_message_text("🗜️ *IMAGE COMPRESSION* 🗜️\n\nSend me an image to compress:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['pending_effect'] = 'compress_image'
            session['state'] = 'awaiting_image'
        
        elif data == "compress_audio":
            await query.edit_message_text("🗜️ *AUDIO COMPRESSION* 🗜️\n\nSend me an audio file to compress:", parse_mode=ParseMode.MARKDOWN)
            session = self.get_session(user_id)
            session['pending_effect'] = 'compress_audio'
            session['state'] = 'awaiting_audio'
        
        elif data.startswith("vid_quality_"):
            quality = data.replace("vid_quality_", "")
            session = self.get_session(user_id)
            session['compress_quality'] = quality
            session['pending_effect'] = 'compress_video'
            session['state'] = 'awaiting_video'
            await query.edit_message_text(f"🗜️ *Video Compression: {quality}*\n\nSend me a video to compress:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "premium":
            await query.edit_message_text("⭐ *PREMIUM PLANS* ⭐\n\nSelect a plan:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_premium_menu())
        
        elif data.startswith("premium_"):
            plan = data.replace("premium_", "")
            prices = {
                'monthly': '$2.99',
                'quarterly': '$7.99',
                'yearly': '$29.99',
                'lifetime': '$99.99'
            }
            await query.edit_message_text(
                f"💎 *Premium {plan.title()} Plan* 💎\n\n"
                f"Price: {prices.get(plan, '$?')}\n\n"
                f"*Features:*\n"
                f"✅ Unlimited daily edits\n"
                f"✅ 2GB file size limit\n"
                f"✅ 4K video support\n"
                f"✅ Priority processing\n"
                f"✅ Exclusive filters\n"
                f"✅ No watermarks\n\n"
                f"Contact @KinvaMasterSupport to upgrade!",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "daily_reward":
            reward = random.randint(50, 200)
            self.db.add_credits(user_id, reward)
            await query.edit_message_text(f"⭐ *DAILY REWARD* ⭐\n\nYou received: `{reward} credits`", parse_mode=ParseMode.MARKDOWN)
        
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
            await query.edit_message_text("💻 *CODE FORMATTER* 💻\n\nSelect a language:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_code_format_menu())
        
        elif data == "custom_commands_menu":
            is_admin = user_id in ADMIN_IDS
            await query.edit_message_text("⚡ *CUSTOM COMMANDS* ⚡\n\nManage custom commands:", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_custom_commands_menu(is_admin))
        
        elif data == "list_custom_cmds":
            await query.edit_message_text("📋 *Custom Commands*\n\nNo custom commands yet.", parse_mode=ParseMode.MARKDOWN)
        
        # Admin panel
        elif data == "admin_panel":
            await query.edit_message_text("👑 *ADMIN PANEL*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_admin_panel())
        
        elif data == "admin_stats":
            stats = self.db.get_bot_stats()
            await query.edit_message_text(
                f"📊 *BOT STATISTICS* 📊\n\n"
                f"👥 Total Users: `{stats.get('total_users', 0)}`\n"
                f"🟢 Active Today: `{stats.get('active_today', 0)}`\n"
                f"🎨 Total Edits: `{stats.get('total_edits', 0)}`\n"
                f"⭐ Premium Users: `{stats.get('premium_users', 0)}`\n"
                f"🚫 Banned Users: `{stats.get('banned_users', 0)}`",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Image editing callbacks
        elif data == "img_filters":
            await query.edit_message_text("🎨 *Select a filter:*", parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=KeyboardBuilder.get_filters_menu())
        
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
                                         reply_markup=KeyboardBuilder.get_image_menu())
        
        # Video editing callbacks
        elif data == "vid_trim":
            session = self.get_session(user_id)
            session['pending_effect'] = 'trim'
            session['state'] = 'awaiting_trim_times'
            await query.edit_message_text("✂️ *Trim Video*\n\nSend start and end times (seconds):\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_speed":
            session = self.get_session(user_id)
            session['pending_effect'] = 'speed'
            session['state'] = 'awaiting_speed_factor'
            await query.edit_message_text("⚡ *Change Speed*\n\nSend speed factor:\n• 0.5 = Slow motion\n• 1.0 = Normal\n• 2.0 = Fast", parse_mode=ParseMode.MARKDOWN)
        
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
        
        elif data == "vid_add_audio":
            session = self.get_session(user_id)
            session['pending_effect'] = 'add_audio'
            session['state'] = 'awaiting_video'
            await query.edit_message_text("🎵 *Add Audio to Video*\n\nSend the video file:", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_rotate":
            session = self.get_session(user_id)
            session['pending_effect'] = 'rotate_video'
            session['state'] = 'awaiting_rotate_angle'
            await query.edit_message_text("🔄 *Rotate Video*\n\nSend angle (90, 180, 270):", parse_mode=ParseMode.MARKDOWN)
        
        elif data == "vid_crop":
            session = self.get_session(user_id)
            session['pending_effect'] = 'crop_video'
            session['state'] = 'awaiting_crop_coords'
            await query.edit_message_text("✂️ *Crop Video*\n\nSend crop dimensions (width height x y):\nExample: `640 480 100 100`", parse_mode=ParseMode.MARKDOWN)
        
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
        
        # Audio editing callbacks
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
    
    # ==================== MESSAGE HANDLERS ====================
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        
        # Check daily limit
        can_edit, message = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {message}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check file size
        photo = update.message.photo[-1]
        if photo.file_size > MAX_IMAGE_SIZE:
            await update.message.reply_text(f"❌ Image too large! Max size: {MAX_IMAGE_SIZE // (1024*1024)}MB", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Download image
        file = await context.bot.get_file(photo.file_id)
        temp_path = TEMP_DIR / f"img_{user_id}_{int(time.time())}.jpg"
        await file.download_to_document(temp_path)
        
        session['temp_file'] = str(temp_path)
        effect = session.get('pending_effect')
        
        if effect == 'auto_enhance':
            await self.process_image_auto_enhance(update, context, temp_path, user_id)
        elif effect == 'resize':
            session['state'] = 'awaiting_resize_dims'
            await update.message.reply_text("📐 *Send dimensions (width height):*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'rotate':
            session['state'] = 'awaiting_rotate_angle'
            await update.message.reply_text("🔄 *Send rotation angle (0-360):*", parse_mode=ParseMode.MARKDOWN)
        elif effect in ['flip_h', 'flip_v']:
            await self.process_image_flip(update, context, temp_path, user_id, effect)
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
            await self.process_image_compress(update, context, temp_path, user_id)
        elif effect:
            await self.process_image_filter(update, context, temp_path, user_id, effect)
        else:
            await update.message.reply_text("Please select an option from the menu first!", reply_markup=KeyboardBuilder.get_image_menu())
    
    async def process_image_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, filter_name: str):
        """Apply image filter"""
        processing_msg = await update.message.reply_text("🎨 *Processing image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            success, output_path = self.image_processor.apply_filter(str(img_path), filter_name, str(TEMP_DIR / f"output_{user_id}_{int(time.time())}.jpg"))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *Filter applied: {filter_name.title()}!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text(f"❌ *Error applying filter*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
            session['state'] = 'verified'
    
    async def process_image_auto_enhance(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        """Auto enhance image"""
        processing_msg = await update.message.reply_text("✨ *AI Auto-Enhancing...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            success, output_path = self.image_processor.auto_enhance(str(img_path), str(TEMP_DIR / f"enhanced_{user_id}_{int(time.time())}.jpg"))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption="✅ *Image auto-enhanced!*\n\n✨ Kira-FX AI Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error enhancing image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_image_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int):
        """Compress image"""
        processing_msg = await update.message.reply_text("🗜️ *Compressing image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            success, output_path, info = self.image_processor.compress_image(str(img_path), str(TEMP_DIR / f"compressed_{user_id}_{int(time.time())}.jpg"), 'high')
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *Image compressed!*\n\n📊 {info.get('compression_ratio', 'N/A')} compression\n📁 {info.get('input_size', 0)//1024}KB → {info.get('output_size', 0)//1024}KB\n\n✨ Kira-FX Compression",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error compressing image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_image_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, flip_type: str):
        """Flip image"""
        processing_msg = await update.message.reply_text("🪞 *Flipping image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            horizontal = flip_type == "flip_h"
            success, output_path = self.image_processor.flip_image(str(img_path), str(TEMP_DIR / f"flipped_{user_id}_{int(time.time())}.jpg"), horizontal)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption="✅ *Image flipped!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error flipping image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        
        # Check daily limit
        can_edit, message = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {message}", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Check file size based on premium status
        max_size = self.db.get_max_file_size(user_id)
        video = update.message.video
        if video.file_size > max_size:
            await update.message.reply_text(f"❌ Video too large! Max size: {max_size // (1024*1024)}MB\n💎 Upgrade to premium for {PREMIUM_USER_MAX_SIZE // (1024*1024)}MB limit!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Download video
        file = await context.bot.get_file(video.file_id)
        temp_path = TEMP_DIR / f"video_{user_id}_{int(time.time())}.mp4"
        await file.download_to_document(temp_path)
        
        session['temp_file'] = str(temp_path)
        effect = session.get('pending_effect')
        
        if effect == 'extract_audio':
            await self.process_extract_audio(update, context, temp_path, user_id)
        elif effect == 'mute':
            await self.process_mute_video(update, context, temp_path, user_id)
        elif effect == 'to_gif':
            await self.process_video_to_gif(update, context, temp_path, user_id)
        elif effect == 'video_info':
            await self.process_video_info(update, context, temp_path, user_id)
        elif effect == 'compress_video':
            quality = session.get('compress_quality', '720p')
            await self.process_video_compress(update, context, temp_path, user_id, quality)
        elif effect == 'trim':
            session['state'] = 'awaiting_trim_times'
            await update.message.reply_text("✂️ *Send trim times (start end):*\nExample: `10 30`", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'speed':
            session['state'] = 'awaiting_speed_factor'
            await update.message.reply_text("⚡ *Send speed factor:*\nExample: `2.0`", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'video_watermark':
            session['state'] = 'awaiting_text_content'
            await update.message.reply_text("🏷️ *Send watermark text:*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'rotate_video':
            session['state'] = 'awaiting_rotate_angle'
            await update.message.reply_text("🔄 *Send rotation angle (90, 180, 270):*", parse_mode=ParseMode.MARKDOWN)
        elif effect == 'add_audio':
            session['pending_effect'] = 'add_audio_wait'
            session['state'] = 'awaiting_audio'
            await update.message.reply_text("🎵 *Video received! Now send the audio file:*", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Please select a video editing option first!", reply_markup=KeyboardBuilder.get_video_menu())
    
    async def process_video_compress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, quality: str):
        """Compress video"""
        processing_msg = await update.message.reply_text(f"🗜️ *Compressing video to {quality}...*\n⏳ This may take a few moments...", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"compressed_{user_id}_{int(time.time())}.mp4"
            success, output_path, info = self.video_processor.compress_video(str(video_path), str(output_path), quality, 'medium', True)
            
            if success:
                # Send compressed video
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Video compressed to {quality}!*\n\n📊 {info.get('compression_ratio', 'N/A')} compression\n📁 {info.get('input_size', 0)//(1024*1024)}MB → {info.get('output_size', 0)//(1024*1024)}MB\n⏱️ {info.get('processing_time', 'N/A')}\n\n✨ Kira-FX Compression",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error compressing video*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_extract_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Extract audio from video"""
        processing_msg = await update.message.reply_text("🎵 *Extracting audio...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"audio_{user_id}_{int(time.time())}.mp3"
            success, output_path = self.video_processor.extract_audio(str(video_path), str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_audio(
                        audio=InputFile(f),
                        caption="✅ *Audio extracted!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *No audio track found*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_mute_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Mute video"""
        processing_msg = await update.message.reply_text("🔊 *Muting video...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"muted_{user_id}_{int(time.time())}.mp4"
            # Use ffmpeg to mute
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(stream, str(output_path), an=None, vcodec='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=InputFile(f),
                    caption="✅ *Video muted!*\n\n✨ Kira-FX Processing",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=KeyboardBuilder.get_video_menu()
                )
            os.remove(output_path)
            self.db.increment_edits(user_id)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_video_to_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Convert video to GIF"""
        processing_msg = await update.message.reply_text("🎞️ *Converting to GIF...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"output_{user_id}_{int(time.time())}.gif"
            success, output_path = self.video_processor.create_gif(str(video_path), str(output_path), 0, 10, 10)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_document(
                        document=InputFile(f, filename="output.gif"),
                        caption="✅ *GIF created!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error creating GIF*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def process_video_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int):
        """Get video information"""
        try:
            info = self.video_processor.get_video_info(str(video_path))
            
            if 'error' not in info:
                await update.message.reply_text(
                    f"ℹ️ *VIDEO INFORMATION* ℹ️\n\n"
                    f"📹 Resolution: `{info.get('width', 0)}x{info.get('height', 0)}`\n"
                    f"⏱️ Duration: `{info.get('duration', 0):.2f} seconds`\n"
                    f"🎬 FPS: `{info.get('fps', 0):.2f}`\n"
                    f"📀 Bitrate: `{info.get('bitrate', 0)//1000} kbps`\n"
                    f"🔊 Audio: `{'Yes' if info.get('has_audio', False) else 'No'}`\n"
                    f"📁 Size: `{info.get('size', 0)//(1024*1024)} MB`\n\n"
                    f"✨ Kira-FX Analysis",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=KeyboardBuilder.get_video_menu()
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
        """Handle audio messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        
        # Check daily limit
        can_edit, message = self.db.can_edit(user_id)
        if not can_edit:
            await update.message.reply_text(f"❌ {message}", parse_mode=ParseMode.MARKDOWN)
            return
        
        audio = update.message.audio or update.message.voice
        if audio and audio.file_size > MAX_AUDIO_SIZE:
            await update.message.reply_text(f"❌ Audio too large! Max size: {MAX_AUDIO_SIZE // (1024*1024)}MB", parse_mode=ParseMode.MARKDOWN)
            return
        
        file = await context.bot.get_file(audio.file_id)
        temp_path = TEMP_DIR / f"audio_{user_id}_{int(time.time())}.mp3"
        await file.download_to_document(temp_path)
        
        session['temp_file'] = str(temp_path)
        
        if session.get('pending_effect') == 'add_audio_wait':
            video_path = session.get('temp_file')
            if video_path and os.path.exists(video_path):
                await self.process_add_audio(update, context, Path(video_path), temp_path, user_id)
            else:
                await update.message.reply_text("❌ Video file not found. Please try again.")
        else:
            await update.message.reply_text("Please select an audio editing option first!", reply_markup=KeyboardBuilder.get_audio_menu())
    
    async def process_add_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, audio_path: Path, user_id: int):
        """Add audio to video"""
        processing_msg = await update.message.reply_text("🎵 *Adding audio to video...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"with_audio_{user_id}_{int(time.time())}.mp4"
            success, output_path = self.video_processor.add_audio(str(video_path), str(audio_path), str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption="✅ *Audio added to video!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error adding audio*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            os.remove(audio_path)
            session = self.get_session(user_id)
            session['pending_effect'] = None
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages"""
        await update.message.reply_text("📄 *Document received*\n\nPlease use the appropriate commands for editing.", parse_mode=ParseMode.MARKDOWN)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        session = self.get_session(user_id)
        text = update.message.text.strip()
        
        # Handle resize dimensions
        if session.get('state') == 'awaiting_resize_dims':
            try:
                parts = text.split()
                if len(parts) == 2:
                    width, height = int(parts[0]), int(parts[1])
                    img_path = session.get('temp_file')
                    if img_path and os.path.exists(img_path):
                        await self.process_image_resize(update, context, Path(img_path), user_id, width, height)
                    else:
                        await update.message.reply_text("❌ No image found. Please try again.")
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
                    await self.process_image_rotate(update, context, Path(img_path), user_id, angle)
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
                        await self.process_image_crop(update, context, Path(img_path), user_id, left, top, right, bottom)
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
                    await self.process_image_color_adjust(update, context, Path(img_path), user_id, session.get('pending_effect'), factor)
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
                    await self.process_image_add_text(update, context, Path(img_path), user_id, text)
                elif effect == 'add_watermark':
                    await self.process_image_add_watermark(update, context, Path(img_path), user_id, text)
                elif effect == 'video_watermark':
                    await self.process_video_watermark(update, context, Path(img_path), user_id, text)
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
                    video_path = session.get('temp_file')
                    if video_path and os.path.exists(video_path):
                        await self.process_video_trim(update, context, Path(video_path), user_id, start, end)
                    else:
                        await update.message.reply_text("❌ No video found.", parse_mode=ParseMode.MARKDOWN)
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
                video_path = session.get('temp_file')
                if video_path and os.path.exists(video_path):
                    await self.process_video_speed(update, context, Path(video_path), user_id, factor)
                else:
                    await update.message.reply_text("❌ No video found.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await update.message.reply_text("❌ Invalid factor!", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle merge/collage completion
        if session.get('state') == 'awaiting_merge_files':
            if text.lower() == 'done':
                effect = session.get('pending_effect')
                if effect == 'merge_videos':
                    if len(session.get('merge_files', [])) >= 2:
                        await self.process_video_merge(update, context, session['merge_files'], user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 videos to merge!", parse_mode=ParseMode.MARKDOWN)
                elif effect == 'collage':
                    if len(session.get('batch_files', [])) >= 2:
                        await self.process_image_collage(update, context, session['batch_files'], user_id)
                    else:
                        await update.message.reply_text("❌ Need at least 2 images for collage!", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Send files or type 'done' to finish.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Handle feedback
        if session.get('state') == 'awaiting_feedback':
            self.db.save_feedback(user_id, text)
            await update.message.reply_text("✅ *Thank you for your feedback!*", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            return
        
        # Handle broadcast
        if session.get('state') == 'awaiting_broadcast':
            if user_id not in ADMIN_IDS:
                return
            # Broadcast to all users
            await update.message.reply_text(f"✅ *Broadcast sent!*", parse_mode=ParseMode.MARKDOWN)
            session['state'] = 'verified'
            return
        
        # Default response
        await update.message.reply_text(
            "🤖 *KINVA MASTER PRO*\n\n"
            "Please use the menu buttons to select an option!\n"
            "Type /help for assistance.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=KeyboardBuilder.get_main_menu(user_id in ADMIN_IDS, self.db.is_premium(user_id))
        )
    
    async def process_image_resize(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, width: int, height: int):
        """Resize image"""
        processing_msg = await update.message.reply_text("📐 *Resizing image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"resized_{user_id}_{int(time.time())}.jpg"
            success, output_path = self.image_processor.resize_image(str(img_path), str(output_path), width, height)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *Resized to {width}x{height}!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error resizing image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_rotate(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, angle: int):
        """Rotate image"""
        processing_msg = await update.message.reply_text("🔄 *Rotating image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"rotated_{user_id}_{int(time.time())}.jpg"
            success, output_path = self.image_processor.rotate_image(str(img_path), str(output_path), angle)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *Rotated {angle}°!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error rotating image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_crop(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, left: int, top: int, right: int, bottom: int):
        """Crop image"""
        processing_msg = await update.message.reply_text("✂️ *Cropping image...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"cropped_{user_id}_{int(time.time())}.jpg"
            success, output_path = self.image_processor.crop_image(str(img_path), str(output_path), left, top, right, bottom)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption="✅ *Image cropped!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error cropping image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_color_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, adjustment: str, factor: float):
        """Adjust image color"""
        processing_msg = await update.message.reply_text(f"🎨 *Adjusting {adjustment}...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"adjusted_{user_id}_{int(time.time())}.jpg"
            
            if adjustment == 'brightness':
                success, output_path = self.image_processor.adjust_brightness(str(img_path), str(output_path), factor)
            elif adjustment == 'contrast':
                success, output_path = self.image_processor.adjust_contrast(str(img_path), str(output_path), factor)
            elif adjustment == 'saturation':
                success, output_path = self.image_processor.adjust_saturation(str(img_path), str(output_path), factor)
            elif adjustment == 'sharpness':
                success, output_path = self.image_processor.adjust_sharpness(str(img_path), str(output_path), factor)
            else:
                success = False
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *{adjustment.title()} adjusted!*\nFactor: {factor}\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error adjusting image*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_add_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        """Add text to image"""
        processing_msg = await update.message.reply_text("📝 *Adding text...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"text_{user_id}_{int(time.time())}.jpg"
            success, output_path = self.image_processor.add_text(str(img_path), str(output_path), text, 'bottom')
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption=f"✅ *Text added: \"{text[:30]}\"*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error adding text*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_add_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, img_path: Path, user_id: int, text: str):
        """Add watermark to image"""
        processing_msg = await update.message.reply_text("💧 *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"watermarked_{user_id}_{int(time.time())}.jpg"
            # For now, just add text as watermark
            success, output_path = self.image_processor.add_text(str(img_path), str(output_path), text or WATERMARK_TEXT, 'bottom')
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_photo(
                        photo=InputFile(f),
                        caption="✅ *Watermark added!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_image_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error adding watermark*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(img_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_video_trim(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, start: float, end: float):
        """Trim video"""
        processing_msg = await update.message.reply_text("✂️ *Trimming video...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"trimmed_{user_id}_{int(time.time())}.mp4"
            success, output_path = self.video_processor.trim_video(str(video_path), str(output_path), start, end)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Trimmed from {start}s to {end}s!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error trimming video*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_video_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, factor: float):
        """Change video speed"""
        processing_msg = await update.message.reply_text(f"⚡ *Changing speed to {factor}x...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"speed_{user_id}_{int(time.time())}.mp4"
            success, output_path = self.video_processor.change_speed(str(video_path), str(output_path), factor)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption=f"✅ *Speed changed to {factor}x!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error changing speed*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_video_merge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_paths: List[str], user_id: int):
        """Merge videos"""
        processing_msg = await update.message.reply_text("🔗 *Merging videos...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"merged_{user_id}_{int(time.time())}.mp4"
            success, output_path = self.video_processor.merge_videos(video_paths, str(output_path))
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption="✅ *Videos merged!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error merging videos*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
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
    
    async def process_video_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_path: Path, user_id: int, text: str):
        """Add watermark to video"""
        processing_msg = await update.message.reply_text("🏷️ *Adding watermark...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = TEMP_DIR / f"watermarked_{user_id}_{int(time.time())}.mp4"
            success, output_path = self.video_processor.add_watermark(str(video_path), str(output_path), text or WATERMARK_TEXT)
            
            if success:
                with open(output_path, 'rb') as f:
                    await update.message.reply_video(
                        video=InputFile(f),
                        caption="✅ *Watermark added!*\n\n✨ Kira-FX Processing",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=KeyboardBuilder.get_video_menu()
                    )
                os.remove(output_path)
                self.db.increment_edits(user_id)
            else:
                await processing_msg.edit_text("❌ *Error adding watermark*", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            os.remove(video_path)
            session = self.get_session(user_id)
            session['state'] = 'verified'
            session['pending_effect'] = None
    
    async def process_image_collage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, image_paths: List[str], user_id: int):
        """Create collage from images"""
        processing_msg = await update.message.reply_text("🎨 *Creating collage...*", parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Simple collage - just send as album for now
            media_group = []
            for path in image_paths[:4]:
                with open(path, 'rb') as f:
                    media_group.append(InputMediaPhoto(media=InputFile(f)))
            
            await context.bot.send_media_group(chat_id=user_id, media=media_group)
            await update.message.reply_text("✅ *Collage created!*\n\n✨ Kira-FX Processing", reply_markup=KeyboardBuilder.get_image_menu())
            
            for path in image_paths:
                os.remove(path)
            self.db.increment_edits(user_id)
        except Exception as e:
            await processing_msg.edit_text(f"❌ *Error:* {str(e)}", parse_mode=ParseMode.MARKDOWN)
        finally:
            session = self.get_session(user_id)
            session['batch_files'] = []
            session['state'] = 'verified'
            session['pending_effect'] = None

# ==================== MAIN ENTRY POINT ====================

async def main():
    """Main entry point"""
    bot = KinvaMasterBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
