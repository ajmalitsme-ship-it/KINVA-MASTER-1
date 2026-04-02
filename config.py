# ============================================
# CONFIGURATION FILE - WITH 4GB SUPPORT
# ============================================

import os
from datetime import datetime
from pathlib import Path

class Config:
    """Master Configuration Class - ALL SETTINGS HERE"""
    
    # ============================================
    # BOT CONFIGURATION
    # ============================================
    
    # Telegram Bot Token - REPLACE WITH YOUR TOKEN
    BOT_TOKEN = "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk"
    
    # Admin User IDs (Add multiple admins)
    ADMIN_IDS = [8525952693]  # Your Telegram ID
    
    # Webhook URL for deployment (Render/Heroku)
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://KinvaMaster-1.onrender.com")
    
    # Server Port
    PORT = int(os.environ.get("PORT", 8080))
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    
    DATABASE_FILE = "kinva_master.db"
    
    # ============================================
    # STORAGE CONFIGURATION
    # ============================================
    
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    CACHE_DIR = "cache"
    
    # ============================================
    # FILE SIZE LIMITS (4GB SUPPORT)
    # ============================================
    
    # FREE USER LIMITS
    FREE_MAX_FILE_SIZE_MB = 700  # 700MB for free users
    FREE_MAX_VIDEO_DURATION = 300  # 5 minutes
    
    # PREMIUM USER LIMITS  
    PREMIUM_MAX_FILE_SIZE_MB = 4096  # 4GB for premium users
    PREMIUM_MAX_VIDEO_DURATION = 3600  # 60 minutes
    
    # Convert to bytes
    FREE_MAX_FILE_SIZE_BYTES = FREE_MAX_FILE_SIZE_MB * 1024 * 1024
    PREMIUM_MAX_FILE_SIZE_BYTES = PREMIUM_MAX_FILE_SIZE_MB * 1024 * 1024
    
    # ============================================
    # EDITING LIMITS
    # ============================================
    
    MAX_EDITS_PER_DAY_FREE = 10
    MAX_EDITS_PER_DAY_PREMIUM = 999999
    
    # ============================================
    # PREMIUM FEATURES
    # ============================================
    
    PREMIUM_FEATURES = {
        "file_size_limit": "4GB",
        "video_duration": "60 minutes",
        "no_watermark": True,
        "4k_export": True,
        "priority_processing": True,
        "all_filters": True,
        "all_tools": True,
        "batch_processing": True,
        "cloud_storage": True,
        "advanced_effects": True,
        "motion_tracking": True,
        "chroma_key": True,
        "auto_captions": True,
        "voiceover": True,
        "background_removal": True
    }
    
    # ============================================
    # PREMIUM PRICING
    # ============================================
    
    # USD Prices
    PREMIUM_PRICE_MONTHLY_USD = 9.99
    PREMIUM_PRICE_YEARLY_USD = 49.99
    PREMIUM_PRICE_LIFETIME_USD = 99.99
    
    # INR Prices
    PREMIUM_PRICE_MONTHLY_INR = 499
    PREMIUM_PRICE_YEARLY_INR = 2499
    PREMIUM_PRICE_LIFETIME_INR = 4999
    
    # Telegram Stars
    PREMIUM_PRICE_MONTHLY_STARS = 100
    PREMIUM_PRICE_YEARLY_STARS = 500
    PREMIUM_PRICE_LIFETIME_STARS = 1000
    
    # ============================================
    # PAYMENT CONFIGURATION
    # ============================================
    
    # UPI Payment
    UPI_ID = "kinvamaster@okhdfcbank"
    UPI_NAME = "Kinva Master Pro"
    
    # Stripe (Optional)
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    
    # PayPal (Optional)
    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    
    # ============================================
    # WATERMARK CONFIGURATION
    # ============================================
    
    DEFAULT_WATERMARK = "Kinva Master Pro"
    WATERMARK_POSITIONS = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    
    # ============================================
    # CAPCUT, KINEMASTER, CANVA FEATURES
    # ============================================
    
    # CapCut Style Features
    CAPCUT_FEATURES = {
        "transitions": ["fade", "slide", "zoom", "blur", "glitch", "flash"],
        "text_templates": ["modern", "neon", "typewriter", "bounce", "fade_in"],
        "stickers": True,
        "filters": True,
        "effects": True
    }
    
    # Kinemaster Style Features
    KINEMASTER_FEATURES = {
        "layers": 10,
        "chroma_key": True,
        "animation": True,
        "voiceover": True,
        "speed_control": True,
        "reverse_video": True
    }
    
    # Canva Style Features
    CANVA_FEATURES = {
        "templates": True,
        "elements": True,
        "backgrounds": True,
        "fonts": True,
        "brand_kits": True
    }
    
    # ============================================
    # SUPPORT
    # ============================================
    
    SUPPORT_CHAT = "https://t.me/kinvasupport"
    SUPPORT_EMAIL = "support@kinvamaster.com"
    
    # ============================================
    # SYSTEM SETUP
    # ============================================
    
    @classmethod
    def setup_directories(cls):
        """Create all required directories"""
        dirs = [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            # Set permissions for large files
            os.chmod(dir_path, 0o777)
    
    @classmethod
    def get_file_limit_mb(cls, is_premium: bool = False) -> int:
        """Get file size limit for user type"""
        return cls.PREMIUM_MAX_FILE_SIZE_MB if is_premium else cls.FREE_MAX_FILE_SIZE_MB
    
    @classmethod
    def get_file_limit_bytes(cls, is_premium: bool = False) -> int:
        """Get file size limit in bytes"""
        return cls.PREMIUM_MAX_FILE_SIZE_BYTES if is_premium else cls.FREE_MAX_FILE_SIZE_BYTES
    
    @classmethod
    def get_duration_limit(cls, is_premium: bool = False) -> int:
        """Get video duration limit"""
        return cls.PREMIUM_MAX_VIDEO_DURATION if is_premium else cls.FREE_MAX_VIDEO_DURATION
    
    @classmethod
    def can_upload_file(cls, file_size_bytes: int, is_premium: bool = False) -> tuple:
        """Check if file can be uploaded"""
        limit = cls.get_file_limit_bytes(is_premium)
        if file_size_bytes > limit:
            return False, f"File too large! {'Premium' if not is_premium else 'Free'} limit: {limit // (1024*1024)}MB"
        return True, "OK"
    
    @classmethod
    def get_version(cls):
        return "4.0.0"
    
    @classmethod
    def get_features_list(cls, is_premium: bool = False) -> dict:
        """Get features based on user type"""
        if is_premium:
            return {
                "file_size": f"{cls.PREMIUM_MAX_FILE_SIZE_MB}MB (4GB)",
                "video_duration": f"{cls.PREMIUM_MAX_VIDEO_DURATION} seconds",
                "daily_edits": "Unlimited",
                "watermark": "No watermark",
                "export_quality": "4K",
                "filters": "All 50+ filters",
                "tools": "All 40+ tools",
                "effects": "All effects",
                "priority": "Priority processing"
            }
        else:
            return {
                "file_size": f"{cls.FREE_MAX_FILE_SIZE_MB}MB",
                "video_duration": f"{cls.FREE_MAX_VIDEO_DURATION} seconds",
                "daily_edits": f"{cls.MAX_EDITS_PER_DAY_FREE} edits/day",
                "watermark": "Has watermark",
                "export_quality": "720p",
                "filters": "10 basic filters",
                "tools": "20 basic tools",
                "effects": "Basic effects",
                "priority": "Normal queue"
            }

# Initialize directories
Config.setup_directories()
