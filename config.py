# ============================================
# CONFIGURATION FILE - KINVA MASTER PRO
# FULL CAPCUT-STYLE EDITING SYSTEM
# ============================================

import os
from pathlib import Path
from datetime import datetime

class Config:
    """Master Configuration Class - Complete Editing System"""
    
    # ============================================
    # BOT CONFIGURATION
    # ============================================
    
    # Telegram Bot Token
    BOT_TOKEN = "8791110410:AAFq6WbsiI9zhpWFalxDk3ZRdoFvHU3xcVk"
    
    # Admin User IDs
    ADMIN_IDS = [8525952693]
    
    # Bot Name
    BOT_NAME = "Kinva Master Pro"
    BOT_VERSION = "5.0.0"
    
    # ============================================
    # SERVER CONFIGURATION
    # ============================================
    
    PORT = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://KinvaMaster-1.onrender.com")
    HOST = "0.0.0.0"
    
    # ============================================
    # FILE SIZE LIMITS
    # ============================================
    
    # Free User Limits
    FREE_MAX_FILE_SIZE_MB = 700      # 700MB maximum
    FREE_MAX_FILE_SIZE_BYTES = FREE_MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Premium User Limits  
    PREMIUM_MAX_FILE_SIZE_MB = 4096   # 4GB maximum
    PREMIUM_MAX_FILE_SIZE_BYTES = PREMIUM_MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Supported File Types
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg']
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico']
    SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg', '.wma']
    
    # ============================================
    # VIDEO DURATION LIMITS
    # ============================================
    
    FREE_MAX_VIDEO_DURATION = 300     # 5 minutes
    PREMIUM_MAX_VIDEO_DURATION = 3600  # 60 minutes
    
    # ============================================
    # DAILY EDIT LIMITS
    # ============================================
    
    FREE_DAILY_EDITS = 10
    PREMIUM_DAILY_EDITS = 999999
    
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
    UPI_MERCHANT = "KINVAMASTER"
    
    # Stripe
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    
    # PayPal
    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_MODE = "live"
    
    # ============================================
    # CAPCUT-STYLE EDITING SYSTEM
    # ============================================
    
    # Video Effects (50+)
    VIDEO_EFFECTS = {
        "basic": ["fade_in", "fade_out", "slide_in", "slide_out", "zoom_in", "zoom_out"],
        "glitch": ["glitch_1", "glitch_2", "glitch_3", "static", "scan_lines"],
        "vintage": ["vhs", "retro", "old_film", "grain", "sepia"],
        "cinematic": ["cinematic_bars", "film_grain", "lens_flare", "bokeh"],
        "artistic": ["oil_paint", "watercolor", "sketch", "cartoon", "mosaic"],
        "lighting": ["neon", "glow", "sparkle", "rainbow", "prism"],
        "transition": ["fade", "dissolve", "wipe", "slide", "zoom", "blur", "shutter"]
    }
    
    # Audio Effects (30+)
    AUDIO_EFFECTS = {
        "basic": ["volume_up", "volume_down", "mute", "normalize"],
        "filters": ["low_pass", "high_pass", "band_pass", "equalizer"],
        "effects": ["echo", "reverb", "chorus", "flanger", "phaser"],
        "speed": ["slow_motion", "fast_motion", "reverse", "pitch_shift"],
        "noise": ["noise_reduction", "click_removal", "hum_removal"]
    }
    
    # Text Effects (30+)
    TEXT_EFFECTS = {
        "animations": ["fade", "bounce", "slide", "typewriter", "zoom", "rotate", "shake"],
        "styles": ["neon", "shadow", "outline", "gradient", "glow", "3d", "retro"],
        "fonts": ["Arial", "Helvetica", "Times", "Courier", "Impact", "Comic", "Monospace"],
        "positions": ["top", "center", "bottom", "custom"]
    }
    
    # Stickers & Elements (100+)
    STICKERS = {
        "emojis": ["😀", "😂", "❤️", "🔥", "✨", "⭐", "🎬", "🎥", "📸", "🎨"],
        "shapes": ["circle", "square", "triangle", "star", "heart", "arrow"],
        "arrows": ["→", "←", "↑", "↓", "↔", "↕", "➡️", "⬅️"],
        "badges": ["NEW", "HOT", "TRENDING", "EXCLUSIVE", "PREMIUM", "LIMITED"]
    }
    
    # Transitions (50+)
    TRANSITIONS = {
        "basic": ["cut", "fade", "dissolve", "wipe_left", "wipe_right", "wipe_up", "wipe_down"],
        "slide": ["slide_left", "slide_right", "slide_up", "slide_down", "slide_together"],
        "zoom": ["zoom_in", "zoom_out", "zoom_blur", "zoom_rotate"],
        "3d": ["cube", "flip", "spin", "rotate_3d"],
        "creative": ["glitch", "pixelate", "mosaic", "blur", "shutter", "flash"],
        "advanced": ["page_curl", "ripple", "wave", "explode", "implode"]
    }
    
    # Filters (100+)
    FILTERS = {
        "basic": ["normal", "auto", "brightness", "contrast", "saturation", "sharpness"],
        "color": ["grayscale", "sepia", "invert", "vintage", "noir", "pastel", "sunset"],
        "cinematic": ["cinema", "hollywood", "bollywood", "horror", "romance", "action"],
        "social": ["instagram", "snapchat", "tiktok", "youtube", "facebook"],
        "artistic": ["oil", "watercolor", "sketch", "cartoon", "mosaic", "pixelate"],
        "lighting": ["bokeh", "lens_flare", "vignette", "hdr", "dramatic", "dreamy"],
        "special": ["neon", "glow", "sparkle", "rainbow", "prism", "mirror"]
    }
    
    # ============================================
    # KINEMASTER-STYLE FEATURES
    # ============================================
    
    KINEMASTER_FEATURES = {
        "layers": 10,
        "chroma_key": True,
        "green_screen": True,
        "blue_screen": True,
        "animation_presets": True,
        "voiceover": True,
        "speed_control": [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 4, 8],
        "reverse_video": True,
        "transitions_50_plus": True,
        "picture_in_picture": True,
        "split_screen": True,
        "audio_mixing": True,
        "volume_control": True,
        "fade_in_out": True,
        "keyframe_animation": True,
        "motion_tracking": True,
        "color_grading": True,
        "audio_visualization": True,
        "3d_effects": True,
        "particle_effects": True
    }
    
    # ============================================
    # CAPCUT-STYLE FEATURES
    # ============================================
    
    CAPCUT_FEATURES = {
        "auto_captions": True,
        "text_to_speech": True,
        "speech_to_text": True,
        "background_music": True,
        "sound_effects": True,
        "voice_changer": True,
        "beauty_filter": True,
        "body_effects": True,
        "stabilization": True,
        "slow_motion": True,
        "hyperlapse": True,
        "reverse": True,
        "trim": True,
        "crop": True,
        "rotate": True,
        "flip": True,
        "speed_ramping": True,
        "keyframes": True,
        "masking": True,
        "blending_modes": True,
        "color_match": True,
        "scene_detection": True,
        "object_removal": True,
        "background_removal": True
    }
    
    # ============================================
    # CANVA-STYLE FEATURES
    # ============================================
    
    CANVA_FEATURES = {
        "templates_500_plus": True,
        "elements_1000_plus": True,
        "backgrounds_200_plus": True,
        "fonts_100_plus": True,
        "brand_kits": True,
        "social_media_templates": True,
        "presentation_templates": True,
        "video_templates": True,
        "logo_maker": True,
        "poster_maker": True,
        "flyer_maker": True,
        "business_card": True,
        "resume_maker": True,
        "invitation_maker": True,
        "thumbnail_maker": True,
        "banner_maker": True,
        "story_maker": True,
        "reel_maker": True,
        "youtube_intro": True,
        "outro_maker": True
    }
    
    # ============================================
    # EXPORT SETTINGS
    # ============================================
    
    # Free Export
    FREE_EXPORT_QUALITY = "720p"
    FREE_VIDEO_BITRATE = "2000k"
    FREE_VIDEO_CODEC = "libx264"
    FREE_AUDIO_BITRATE = "128k"
    FREE_FPS = 30
    
    # Premium Export
    PREMIUM_EXPORT_QUALITY = "4K"
    PREMIUM_VIDEO_BITRATE = "20000k"
    PREMIUM_VIDEO_CODEC = "libx264"
    PREMIUM_AUDIO_BITRATE = "320k"
    PREMIUM_FPS = 60
    
    # Export Formats
    EXPORT_FORMATS = {
        "video": ["mp4", "mov", "avi", "mkv", "webm"],
        "image": ["png", "jpg", "webp", "gif"],
        "audio": ["mp3", "wav", "aac", "flac"]
    }
    
    # ============================================
    # WATERMARK SETTINGS
    # ============================================
    
    DEFAULT_WATERMARK = "Kinva Master Pro"
    WATERMARK_POSITIONS = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    WATERMARK_OPACITY = 0.7
    WATERMARK_FONT_SIZE = 20
    WATERMARK_FONT_COLOR = "#FFFFFF"
    WATERMARK_BACKGROUND = "transparent"
    
    # ============================================
    # STORAGE CONFIGURATION
    # ============================================
    
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    CACHE_DIR = "cache"
    DATABASE_FILE = "kinva_master.db"
    LOGS_DIR = "logs"
    THUMBNAILS_DIR = "thumbnails"
    
    # File cleanup (hours)
    FILE_RETENTION_HOURS = 24
    TEMP_CLEANUP_INTERVAL = 3600  # 1 hour
    
    # ============================================
    # SOCIAL MEDIA DOWNLOADER
    # ============================================
    
    SUPPORTED_PLATFORMS = {
        "youtube": ["youtube.com", "youtu.be"],
        "instagram": ["instagram.com", "instagr.am"],
        "tiktok": ["tiktok.com", "vm.tiktok.com"],
        "twitter": ["twitter.com", "x.com"],
        "facebook": ["facebook.com", "fb.com"],
        "pinterest": ["pinterest.com"],
        "reddit": ["reddit.com"],
        "linkedin": ["linkedin.com"],
        "telegram": ["t.me"],
        "whatsapp": ["whatsapp.com"]
    }
    
    # Download Quality Options
    DOWNLOAD_QUALITIES = {
        "video": ["144p", "240p", "360p", "480p", "720p", "1080p", "2K", "4K"],
        "audio": ["64kbps", "128kbps", "192kbps", "320kbps"]
    }
    
    # ============================================
    # AI FEATURES
    # ============================================
    
    AI_FEATURES = {
        "auto_caption": True,
        "auto_highlight": True,
        "scene_detection": True,
        "face_detection": True,
        "object_detection": True,
        "background_removal": True,
        "image_enhancement": True,
        "video_stabilization": True,
        "noise_reduction": True,
        "color_correction": True
    }
    
    # ============================================
    # SUPPORT & CONTACT
    # ============================================
    
    SUPPORT_CHAT = "https://t.me/kinvasupport"
    SUPPORT_EMAIL = "support@kinvamaster.com"
    WEBSITE = "https://kinvamaster.com"
    TELEGRAM_CHANNEL = "https://t.me/kinvamaster"
    YOUTUBE_CHANNEL = "https://youtube.com/@kinvamaster"
    INSTAGRAM = "https://instagram.com/kinvamaster"
    
    # ============================================
    # MESSAGES
    # ============================================
    
    WELCOME_MESSAGE = """
🎬 **KINVA MASTER PRO** 🎬

Welcome {first_name}! 

✨ **Your Plan:** {plan}
📁 **File Limit:** {file_limit}
🎥 **Duration:** {duration}
📊 **Daily Edits:** {daily_edits}

🔥 **CAPCUT-STYLE FEATURES:**
• 50+ Video Effects
• 30+ Audio Effects
• 100+ Filters
• 50+ Transitions
• Auto Captions
• Voice Changer
• Green Screen
• Motion Tracking

💡 **Send me a photo/video to start editing!**
    """
    
    PREMIUM_MESSAGE = """
⭐ **PREMIUM FEATURES** ⭐

🚀 **Upgrade to Unlock Everything:**

**📁 FILE LIMITS:**
• FREE: 700MB / 5min
• PREMIUM: 4GB / 60min

**🎬 CAPCUT FEATURES:**
• Auto Captions
• Voice Changer
• Text to Speech
• Beauty Filter
• Body Effects
• Stabilization

**🎨 EDITING TOOLS:**
• 100+ Filters
• 50+ Transitions
• 50+ Video Effects
• 30+ Audio Effects
• Chroma Key (Green Screen)
• Motion Tracking

**📤 EXPORT:**
• FREE: 720p with Watermark
• PREMIUM: 4K No Watermark

**💎 PRICE:**
• Monthly: ${monthly} / {inr} INR
• Yearly: ${yearly} / {yearly_inr} INR
• Lifetime: ${lifetime} / {lifetime_inr} INR

**💳 UPI:** {upi}
⭐ **Stars:** {stars} stars/month
    """
    
    # ============================================
    # FEATURE FLAGS
    # ============================================
    
    # Free Features
    FREE_FEATURES = {
        "max_file_size_mb": FREE_MAX_FILE_SIZE_MB,
        "max_duration_seconds": FREE_MAX_VIDEO_DURATION,
        "daily_edits": FREE_DAILY_EDITS,
        "watermark": True,
        "export_4k": False,
        "export_quality": "720p",
        "basic_filters": True,
        "basic_effects": True,
        "basic_transitions": True,
        "trim": True,
        "crop": True,
        "rotate": True,
        "speed_control": True,
        "audio_extract": True,
        "text_overlay": True,
        "stickers": True,
        "advanced_filters": False,
        "chroma_key": False,
        "motion_tracking": False,
        "auto_captions": False,
        "voiceover": False,
        "background_removal": False,
        "keyframe_animation": False,
        "3d_effects": False,
        "particle_effects": False
    }
    
    # Premium Features
    PREMIUM_FEATURES = {
        "max_file_size_mb": PREMIUM_MAX_FILE_SIZE_MB,
        "max_duration_seconds": PREMIUM_MAX_VIDEO_DURATION,
        "daily_edits": PREMIUM_DAILY_EDITS,
        "watermark": False,
        "export_4k": True,
        "export_quality": "4K",
        "basic_filters": True,
        "basic_effects": True,
        "basic_transitions": True,
        "trim": True,
        "crop": True,
        "rotate": True,
        "speed_control": True,
        "audio_extract": True,
        "text_overlay": True,
        "stickers": True,
        "advanced_filters": True,
        "chroma_key": True,
        "motion_tracking": True,
        "auto_captions": True,
        "voiceover": True,
        "background_removal": True,
        "keyframe_animation": True,
        "3d_effects": True,
        "particle_effects": True,
        "all_effects": True,
        "all_transitions": True,
        "all_filters": True,
        "priority_queue": True,
        "batch_processing": True
    }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    @classmethod
    def setup_directories(cls):
        """Create all required directories"""
        dirs = [
            cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, 
            cls.CACHE_DIR, cls.LOGS_DIR, cls.THUMBNAILS_DIR
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_max_file_size_mb(cls, is_premium: bool = False) -> int:
        """Get max file size in MB"""
        return cls.PREMIUM_MAX_FILE_SIZE_MB if is_premium else cls.FREE_MAX_FILE_SIZE_MB
    
    @classmethod
    def get_max_file_size_bytes(cls, is_premium: bool = False) -> int:
        """Get max file size in bytes"""
        return cls.PREMIUM_MAX_FILE_SIZE_BYTES if is_premium else cls.FREE_MAX_FILE_SIZE_BYTES
    
    @classmethod
    def get_max_duration(cls, is_premium: bool = False) -> int:
        """Get max video duration in seconds"""
        return cls.PREMIUM_MAX_VIDEO_DURATION if is_premium else cls.FREE_MAX_VIDEO_DURATION
    
    @classmethod
    def get_daily_edits(cls, is_premium: bool = False) -> int:
        """Get daily edit limit"""
        return cls.PREMIUM_DAILY_EDITS if is_premium else cls.FREE_DAILY_EDITS
    
    @classmethod
    def get_export_quality(cls, is_premium: bool = False) -> str:
        """Get export quality"""
        return cls.PREMIUM_EXPORT_QUALITY if is_premium else cls.FREE_EXPORT_QUALITY
    
    @classmethod
    def get_video_bitrate(cls, is_premium: bool = False) -> str:
        """Get video bitrate"""
        return cls.PREMIUM_VIDEO_BITRATE if is_premium else cls.FREE_VIDEO_BITRATE
    
    @classmethod
    def check_file_size(cls, file_size_bytes: int, is_premium: bool = False) -> tuple:
        """Check if file size is within limit"""
        limit = cls.get_max_file_size_bytes(is_premium)
        if file_size_bytes > limit:
            limit_mb = limit // (1024 * 1024)
            return False, f"❌ File too large! Maximum {limit_mb}MB for {'premium' if is_premium else 'free'} users. Upgrade to premium for 4GB support!"
        return True, "OK"
    
    @classmethod
    def check_duration(cls, duration_seconds: int, is_premium: bool = False) -> tuple:
        """Check if video duration is within limit"""
        limit = cls.get_max_duration(is_premium)
        if duration_seconds > limit:
            minutes = limit // 60
            return False, f"❌ Video too long! Maximum {minutes} minutes for {'premium' if is_premium else 'free'} users. Upgrade to premium for 60 minutes!"
        return True, "OK"
    
    @classmethod
    def get_features_for_user(cls, is_premium: bool = False) -> dict:
        """Get features for user type"""
        return cls.PREMIUM_FEATURES if is_premium else cls.FREE_FEATURES
    
    @classmethod
    def is_feature_allowed(cls, feature_name: str, is_premium: bool = False) -> bool:
        """Check if feature is allowed"""
        features = cls.get_features_for_user(is_premium)
        return features.get(feature_name, False)
    
    @classmethod
    def get_all_effects(cls) -> dict:
        """Get all available effects"""
        return {
            "video": cls.VIDEO_EFFECTS,
            "audio": cls.AUDIO_EFFECTS,
            "text": cls.TEXT_EFFECTS,
            "transitions": cls.TRANSITIONS,
            "filters": cls.FILTERS
        }
    
    @classmethod
    def get_capcut_features(cls) -> dict:
        """Get CapCut style features"""
        return cls.CAPCUT_FEATURES
    
    @classmethod
    def get_kinemaster_features(cls) -> dict:
        """Get Kinemaster style features"""
        return cls.KINEMASTER_FEATURES
    
    @classmethod
    def get_canva_features(cls) -> dict:
        """Get Canva style features"""
        return cls.CANVA_FEATURES
    
    @classmethod
    def get_version(cls) -> str:
        """Get bot version"""
        return cls.BOT_VERSION

# Initialize directories
Config.setup_directories()

# Print configuration
print(f"""
╔══════════════════════════════════════════════════════════════╗
║              KINVA MASTER PRO CONFIGURATION                   ║
╠══════════════════════════════════════════════════════════════╣
║ Version: {Config.BOT_VERSION}                                                    
╠══════════════════════════════════════════════════════════════╣
║ FILE LIMITS:                                                 ║
║   • Free User:  {Config.FREE_MAX_FILE_SIZE_MB}MB / {Config.FREE_MAX_VIDEO_DURATION//60}min         ║
║   • Premium:    {Config.PREMIUM_MAX_FILE_SIZE_MB}MB / {Config.PREMIUM_MAX_VIDEO_DURATION//60}min        ║
╠══════════════════════════════════════════════════════════════╣
║ DAILY EDITS:                                                 ║
║   • Free:       {Config.FREE_DAILY_EDITS} edits/day                           ║
║   • Premium:    Unlimited                                     ║
╠══════════════════════════════════════════════════════════════╣
║ CAPCUT-STYLE FEATURES:                                       ║
║   • Video Effects:  {len(Config.VIDEO_EFFECTS)} categories                         ║
║   • Audio Effects:  {len(Config.AUDIO_EFFECTS)} categories                         ║
║   • Filters:        {len(Config.FILTERS)} categories                            ║
║   • Transitions:    {len(Config.TRANSITIONS)} categories                         ║
╠══════════════════════════════════════════════════════════════╣
║ PREMIUM PRICING:                                             ║
║   • Monthly:  ${Config.PREMIUM_PRICE_MONTHLY_USD} / {Config.PREMIUM_PRICE_MONTHLY_INR} INR     ║
║   • Yearly:   ${Config.PREMIUM_PRICE_YEARLY_USD} / {Config.PREMIUM_PRICE_YEARLY_INR} INR     ║
║   • Lifetime: ${Config.PREMIUM_PRICE_LIFETIME_USD} / {Config.PREMIUM_PRICE_LIFETIME_INR} INR   ║
╠══════════════════════════════════════════════════════════════╣
║ PAYMENT:                                                     ║
║   • UPI: {Config.UPI_ID}                    ║
║   • Telegram Stars: {Config.PREMIUM_PRICE_MONTHLY_STARS} stars/month                 ║
╚══════════════════════════════════════════════════════════════╝
""")
