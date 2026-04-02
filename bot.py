# ============================================
# BOT.PY - MAIN TELEGRAM BOT FILE
# KINVA MASTER PRO - COMPLETE EDITING SYSTEM
# ============================================

import os
import logging
import asyncio
import tempfile
import shutil
import json
import random
import time
import sqlite3
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, ChatAction
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler
)
from telegram.constants import ParseMode

# Import config
from config import Config

# Import database
from database import Database

# Import editing tools
from video_editor import VideoEditor
from image_editor import ImageEditor
from filters import Filters
from premium import PremiumManager
from payments import PaymentManager

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# MAIN BOT CLASS
# ============================================

class KinvaMasterBot:
    """Main Bot Class with Complete Editing System"""
    
    def __init__(self):
        self.db = Database()
        self.video_editor = VideoEditor()
        self.image_editor = ImageEditor()
        self.filters = Filters()
        self.premium = PremiumManager(self.db)
        self.payment = PaymentManager()
        self.user_sessions = {}
        self.processing_tasks = {}
        
        # Conversation states
        self.TRIM, self.CROP, self.SPEED, self.TEXT, self.WATERMARK = range(5)
    
    # ============================================
    # COMMAND HANDLERS
    # ============================================
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        user_id = user.id
        
        # Get or create user
        user_data = self.db.get_user(user_id)
        if not user_data:
            user_data = self.db.create_user(user_id, user.username, user.first_name)
        
        is_premium = self.db.is_premium(user_id)
        
        # Get limits
        max_size_mb = Config.get_max_file_size_mb(is_premium)
        max_duration = Config.get_max_duration(is_premium)
        daily_edits = Config.get_daily_edits(is_premium)
        remaining_edits = daily_edits - (user_data.get('edits_today', 0) if user_data else 0)
        
        # Premium features list
        premium_features = """
⭐ **PREMIUM FEATURES:**
• 📁 4GB File Support
• 🎥 60 Min Videos
• 🚫 No Watermark
• 📤 4K Export
• 🎨 100+ Filters
• 🎬 50+ Effects
• 🎯 Motion Tracking
• 🟢 Chroma Key
• 📝 Auto Captions
        """ if not is_premium else ""
        
        welcome_text = f"""
🎬 **KINVA MASTER PRO** 🎬

Welcome {user.first_name}! 

━━━━━━━━━━━━━━━━━━━━━━
✨ **YOUR STATUS** ✨
━━━━━━━━━━━━━━━━━━━━━━

📀 **Plan:** {'⭐ PREMIUM' if is_premium else '📀 FREE'}
📁 **File Limit:** {max_size_mb}MB
🎥 **Duration:** {max_duration//60} minutes
📊 **Daily Edits:** {remaining_edits}/{daily_edits}
📈 **Total Edits:** {user_data.get('total_edits', 0) if user_data else 0}

━━━━━━━━━━━━━━━━━━━━━━
🎬 **CAPCUT-STYLE FEATURES** 🎬
━━━━━━━━━━━━━━━━━━━━━━

• ✂️ Trim & Cut Video
• 🎯 Crop & Rotate
• ⚡ Speed Control (0.1x - 8x)
• 🎨 100+ Professional Filters
• ✨ 50+ Video Effects
• 🎵 30+ Audio Effects
• 🔄 50+ Transitions
• 📝 Text Overlay & Stickers
• 🎙️ Voiceover & Auto Captions
• 🟢 Chroma Key (Green Screen)
• 🎯 Motion Tracking
• 🖼️ Picture in Picture
• 📊 Split Screen
• 🎚️ Audio Mixing
• 🌈 Color Grading
{premium_features}
━━━━━━━━━━━━━━━━━━━━━━

💡 **Send me a photo or video to start editing!**

🔹 Type /help for all commands
🔹 Type /menu for tools menu
🔹 Type /premium to upgrade
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 VIDEO TOOLS", callback_data="menu_video"),
             InlineKeyboardButton("🖼️ IMAGE TOOLS", callback_data="menu_image")],
            [InlineKeyboardButton("🎨 FILTERS (100+)", callback_data="menu_filters"),
             InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects")],
            [InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium"),
             InlineKeyboardButton("📥 DOWNLOADER", callback_data="menu_download")],
            [InlineKeyboardButton("📊 MY STATS", callback_data="menu_stats"),
             InlineKeyboardButton("❓ HELP", callback_data="menu_help")]
        ]
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.MARKDOWN
        )
    
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
/speed - Change speed (0.1x-8x)
/slow_mo - Slow motion
/fast_mo - Fast motion
/reverse - Reverse video
/loop - Loop video
/merge - Merge videos
/split_screen - Split screen effect
/pip - Picture in picture

**🎵 AUDIO TOOLS**
/extract_audio - Extract audio
/remove_audio - Remove audio
/add_audio - Add audio track
/volume - Adjust volume
/audio_fade - Audio fade effect
/voiceover - Add voiceover
/auto_captions - Auto generate captions

**✨ VIDEO EFFECTS (50+)**
/fade_in - Fade in effect
/fade_out - Fade out effect
/glitch - Glitch effect
/pixelate - Pixelate effect
/grayscale_vid - Black & white
/sepia_vid - Sepia effect
/blur_vid - Blur effect
/sharpen_vid - Sharpen effect
/vintage - Vintage effect
/neon - Neon effect
/chroma_key - Green screen effect
/motion_track - Motion tracking

**📦 COMPRESSION & EXPORT**
/compress - Compress video
/to_4k - Convert to 4K (Premium)
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
/remove_bg - Remove background (Premium)

**🎨 FILTERS (100+)**
/filters - Show all filters
/grayscale - Grayscale filter
/sepia - Sepia filter
/vintage - Vintage filter
/cool - Cool filter
/warm - Warm filter
/noir - Noir filter
/pastel - Pastel filter
/glow - Glow effect
/neon_img - Neon effect
/oil_paint - Oil painting
/watercolor - Watercolor effect
/cartoon - Cartoon effect

**⭐ PREMIUM FEATURES**
/premium - Get premium
/kinemaster - Kinemaster tools
/capcut - CapCut tools
/canva - Canva templates

**📥 DOWNLOAD TOOLS**
/youtube - Download YouTube
/instagram - Download Instagram
/tiktok - Download TikTok
/facebook - Download Facebook
/twitter - Download Twitter

**ℹ️ INFO**
/stats - Your statistics
/feedback - Send feedback
/support - Contact support
/about - About bot

━━━━━━━━━━━━━━━━━━━━━━
💡 **Just send me a photo/video to start!**
        """
        
        await update.message.reply_text(menu_text, parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # FILE HANDLERS
    # ============================================
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video upload"""
        user_id = update.effective_user.id
        video = update.message.video
        
        # Check if user can edit
        if not self.db.can_edit(user_id):
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(
                "❌ You've reached your daily free edit limit!\n\nUpgrade to premium for unlimited edits!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Check file size
        file_size_bytes = video.file_size
        is_premium = self.db.is_premium(user_id)
        can_upload, message = Config.check_file_size(file_size_bytes, is_premium)
        
        if not can_upload:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Check duration
        duration = video.duration
        can_upload, message = Config.check_duration(duration, is_premium)
        
        if not can_upload:
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            "📥 **Downloading video...**\nPlease wait while I process your file.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Download video
        file = await video.get_file()
        timestamp = int(time.time())
        input_path = os.path.join(Config.UPLOAD_DIR, f"video_{user_id}_{timestamp}.mp4")
        await file.download_to_drive(input_path)
        
        # Update session
        context.user_data['current_video'] = input_path
        context.user_data['original_video'] = input_path
        context.user_data['file_type'] = 'video'
        
        # Increment edit count
        self.db.increment_edits(user_id)
        
        # Get video info
        video_info = self.video_editor.get_video_info(input_path)
        
        await processing_msg.delete()
        
        # Create keyboard based on premium status
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("🎵 ADD AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("🔊 EXTRACT AUDIO", callback_data="tool_extract_audio")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="tool_effects"),
             InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark"),
             InlineKeyboardButton("📝 ADD TEXT", callback_data="tool_text")],
            [InlineKeyboardButton("🟢 CHROMA KEY", callback_data="tool_chroma"),
             InlineKeyboardButton("🎯 MOTION TRACK", callback_data="tool_motion")],
            [InlineKeyboardButton("📊 COMPRESS", callback_data="tool_compress"),
             InlineKeyboardButton("💎 EXPORT", callback_data="tool_export")],
            [InlineKeyboardButton("🔄 RESET", callback_data="tool_reset"),
             InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        # Add premium features if not premium
        if not is_premium:
            keyboard.insert(6, [InlineKeyboardButton("⭐ UNLOCK 4K & NO WATERMARK", callback_data="menu_premium")])
        
        caption = f"""
✅ **Video Ready!**

📁 **Info:**
• Size: {video_info.get('size_mb', 0)}MB / {Config.get_max_file_size_mb(is_premium)}MB max
• Duration: {video_info.get('duration', 0)}s / {Config.get_max_duration(is_premium)}s max
• Resolution: {video_info.get('resolution', 'Unknown')}
• FPS: {video_info.get('fps', 0)}

🎬 **Choose an editing option below:**
        """
        
        await update.message.reply_video(
            video=open(input_path, 'rb'),
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo upload"""
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        
        # Check if user can edit
        if not self.db.can_edit(user_id):
            keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
            await update.message.reply_text(
                "❌ You've reached your daily free edit limit!\n\nUpgrade to premium for unlimited edits!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            "📥 **Downloading image...**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Download image
        file = await photo.get_file()
        timestamp = int(time.time())
        input_path = os.path.join(Config.UPLOAD_DIR, f"image_{user_id}_{timestamp}.jpg")
        await file.download_to_drive(input_path)
        
        # Update session
        context.user_data['current_image'] = input_path
        context.user_data['original_image'] = input_path
        context.user_data['file_type'] = 'image'
        
        # Increment edit count
        self.db.increment_edits(user_id)
        
        await processing_msg.delete()
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🎨 FILTERS (100+)", callback_data="menu_filters"),
             InlineKeyboardButton("✂️ CROP", callback_data="tool_crop_img")],
            [InlineKeyboardButton("🔄 ROTATE", callback_data="tool_rotate_img"),
             InlineKeyboardButton("⚡ RESIZE", callback_data="tool_resize_img")],
            [InlineKeyboardButton("🌈 ADJUST", callback_data="tool_adjust"),
             InlineKeyboardButton("🖌️ EFFECTS", callback_data="tool_effects_img")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark_img"),
             InlineKeyboardButton("📝 ADD TEXT", callback_data="tool_text_img")],
            [InlineKeyboardButton("🗑️ REMOVE BG", callback_data="tool_remove_bg"),
             InlineKeyboardButton("🔄 RESET", callback_data="tool_reset")],
            [InlineKeyboardButton("✅ DONE", callback_data="tool_done")]
        ]
        
        await update.message.reply_photo(
            photo=open(input_path, 'rb'),
            caption="✅ **Image Ready!** Choose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ============================================
    # VIDEO EDITING TOOLS
    # ============================================
    
    async def trim_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trim video tool"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "✂️ **Trim Video**\n\n"
            "Send start and end time in seconds.\n"
            "Example: `10 30` (trim from 10s to 30s)\n\n"
            "Or send:\n"
            "• `start 10` - trim from 10s to end\n"
            "• `end 30` - trim from start to 30s\n"
            "• `10 30` - trim between 10s and 30s",
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.user_data['waiting_for'] = 'trim'
        return self.TRIM
    
    async def handle_trim_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle trim input"""
        text = update.message.text
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await update.message.reply_text("❌ No video found. Please send a video first.")
            return ConversationHandler.END
        
        try:
            parts = text.split()
            if len(parts) == 1:
                if parts[0].startswith('start'):
                    start = float(parts[0].split('_')[1])
                    end = None
                elif parts[0].startswith('end'):
                    start = None
                    end = float(parts[0].split('_')[1])
                else:
                    raise ValueError("Invalid format")
            else:
                start = float(parts[0])
                end = float(parts[1])
            
            await update.message.reply_text("✂️ **Trimming video...** Please wait.", parse_mode=ParseMode.MARKDOWN)
            
            output_path = self.video_editor.trim(video_path, start, end)
            context.user_data['current_video'] = output_path
            
            # Send result
            with open(output_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"✅ **Video trimmed successfully!**\n\nFrom {start}s to {end}s" if end else f"✅ **Video trimmed from {start}s!**",
                    parse_mode=ParseMode.MARKDOWN
                )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}\n\nPlease use format: `10 30`", parse_mode=ParseMode.MARKDOWN)
        
        return ConversationHandler.END
    
    async def speed_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Change video speed"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🐌 0.25x", callback_data="speed_0.25"),
             InlineKeyboardButton("🚶 0.5x", callback_data="speed_0.5"),
             InlineKeyboardButton("🚶 0.75x", callback_data="speed_0.75")],
            [InlineKeyboardButton("⚡ 1x (Normal)", callback_data="speed_1.0"),
             InlineKeyboardButton("🏃 1.25x", callback_data="speed_1.25"),
             InlineKeyboardButton("🏃 1.5x", callback_data="speed_1.5")],
            [InlineKeyboardButton("🚀 2x", callback_data="speed_2.0"),
             InlineKeyboardButton("🚀 3x", callback_data="speed_3.0"),
             InlineKeyboardButton("🚀 4x", callback_data="speed_4.0")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_video")]
        ]
        
        await query.edit_message_text(
            "⚡ **Change Video Speed**\n\nChoose speed factor:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def apply_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Apply speed change"""
        query = update.callback_query
        await query.answer()
        
        speed = float(query.data.split('_')[1])
        video_path = context.user_data.get('current_video')
        
        if not video_path:
            await query.edit_message_text("❌ No video found. Please send a video first.")
            return
        
        await query.edit_message_text(f"⚡ **Changing speed to {speed}x...** Please wait.", parse_mode=ParseMode.MARKDOWN)
        
        try:
            output_path = self.video_editor.speed(video_path, speed)
            context.user_data['current_video'] = output_path
            
            with open(output_path, 'rb') as f:
                await query.message.reply_video(
                    video=f,
                    caption=f"✅ **Speed changed to {speed}x!**",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")
    
    # ============================================
    # PREMIUM MENU
    # ============================================
    
    async def premium_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium subscription menu"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        is_premium = self.db.is_premium(user_id)
        
        if is_premium:
            user_data = self.db.get_user(user_id)
            expiry = user_data.get('premium_expiry', 'N/A')
            
            text = f"""
⭐ **YOU ARE A PREMIUM MEMBER!** ⭐

━━━━━━━━━━━━━━━━━━━━━━
✨ **Active Features:** ✨
━━━━━━━━━━━━━━━━━━━━━━

✅ **4GB File Support**
✅ **60 Minute Videos**
✅ **No Watermark**
✅ **4K Export**
✅ **100+ Filters**
✅ **50+ Effects**
✅ **Motion Tracking**
✅ **Chroma Key**
✅ **Auto Captions**
✅ **Priority Processing**

📅 **Expires:** {expiry[:10] if expiry else 'N/A'}

💎 **Thank you for supporting Kinva Master!**
            """
            
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            text = f"""
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
| Filters | 10 | **100+** |
| Effects | 10 | **50+** |
| Transitions | 10 | **50+** |
| Motion Track | ❌ | **✅** |
| Chroma Key | ❌ | **✅** |
| Auto Captions | ❌ | **✅** |
| Remove BG | ❌ | **✅** |
| Priority | ❌ | **✅** |

━━━━━━━━━━━━━━━━━━━━━━
💎 **PRICING** 💎
━━━━━━━━━━━━━━━━━━━━━━

• **Monthly:** ${Config.PREMIUM_PRICE_MONTHLY_USD} / {Config.PREMIUM_PRICE_MONTHLY_INR} INR
• **Yearly:** ${Config.PREMIUM_PRICE_YEARLY_USD} / {Config.PREMIUM_PRICE_YEARLY_INR} INR (Save 50%)
• **Lifetime:** ${Config.PREMIUM_PRICE_LIFETIME_USD} / {Config.PREMIUM_PRICE_LIFETIME_INR} INR

━━━━━━━━━━━━━━━━━━━━━━
💳 **PAYMENT METHODS** 💳
━━━━━━━━━━━━━━━━━━━━━━

• **UPI:** `{Config.UPI_ID}`
• **Telegram Stars:** {Config.PREMIUM_PRICE_MONTHLY_STARS} stars/month
• **PayPal:** Available
• **Crypto:** USDT/BTC

🔥 **UPGRADE NOW AND GET 7 DAYS FREE!** 🔥
            """
            
            keyboard = [
                [InlineKeyboardButton("💎 BUY MONTHLY", callback_data="buy_monthly"),
                 InlineKeyboardButton("💎 BUY YEARLY", callback_data="buy_yearly")],
                [InlineKeyboardButton("👑 BUY LIFETIME", callback_data="buy_lifetime")],
                [InlineKeyboardButton("⭐ PAY WITH STARS", callback_data="pay_stars")],
                [InlineKeyboardButton("💳 UPI PAYMENT", callback_data="pay_upi")],
                [InlineKeyboardButton("💸 PAYPAL", callback_data="pay_paypal")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
            ]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    # ============================================
    # CALLBACK HANDLER
    # ============================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        # Main navigation
        if data == "back_main":
            await self.start(update, context)
        elif data == "menu_video":
            await self.video_menu(update, context)
        elif data == "menu_image":
            await self.image_menu(update, context)
        elif data == "menu_filters":
            await self.filters_menu(update, context)
        elif data == "menu_effects":
            await self.effects_menu(update, context)
        elif data == "menu_premium":
            await self.premium_menu(update, context)
        elif data == "menu_stats":
            await self.stats_command(update, context)
        elif data == "menu_help":
            await self.help_command(update, context)
        elif data == "menu_download":
            await self.download_menu(update, context)
        
        # Video tools
        elif data == "tool_trim":
            await self.trim_video(update, context)
        elif data == "tool_speed":
            await self.speed_video(update, context)
        elif data.startswith("speed_"):
            await self.apply_speed(update, context)
        elif data == "tool_reverse":
            await self.reverse_video(update, context)
        elif data == "tool_compress":
            await self.compress_video(update, context)
        elif data == "tool_watermark":
            await self.add_watermark(update, context)
        elif data == "tool_export":
            await self.export_video(update, context)
        elif data == "tool_reset":
            await self.reset_edit(update, context)
        elif data == "tool_done":
            await self.done_edit(update, context)
        
        # Premium purchase
        elif data.startswith("buy_"):
            await self.initiate_purchase(update, context, data)
        elif data == "pay_stars":
            await self.pay_with_stars(update, context)
        elif data == "pay_upi":
            await self.show_upi_payment(update, context)
        elif data == "pay_paypal":
            await self.pay_with_paypal(update, context)
        
        # Filter application
        elif data.startswith("filter_"):
            await self.apply_filter(update, context, data)
        
        # Effect application
        elif data.startswith("effect_"):
            await self.apply_effect(update, context, data)
        
        else:
            await query.answer("🛠️ Feature coming soon!", show_alert=True)
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def video_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show video tools menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("✂️ TRIM", callback_data="tool_trim"),
             InlineKeyboardButton("🎯 CROP", callback_data="tool_crop")],
            [InlineKeyboardButton("⚡ SPEED", callback_data="tool_speed"),
             InlineKeyboardButton("🔄 REVERSE", callback_data="tool_reverse")],
            [InlineKeyboardButton("🎵 AUDIO", callback_data="tool_audio"),
             InlineKeyboardButton("🔊 COMPRESS", callback_data="tool_compress")],
            [InlineKeyboardButton("✨ EFFECTS", callback_data="menu_effects"),
             InlineKeyboardButton("🎨 FILTERS", callback_data="menu_filters")],
            [InlineKeyboardButton("💧 WATERMARK", callback_data="tool_watermark"),
             InlineKeyboardButton("📝 TEXT", callback_data="tool_text")],
            [InlineKeyboardButton("🟢 CHROMA KEY", callback_data="tool_chroma"),
             InlineKeyboardButton("🎯 MOTION TRACK", callback_data="tool_motion")],
            [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text(
            "🎬 **VIDEO EDITING TOOLS**\n\nChoose a tool:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show filters menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🎨 BASIC", callback_data="filters_basic"),
             InlineKeyboardButton("🌈 COLOR", callback_data="filters_color")],
            [InlineKeyboardButton("🎭 ARTISTIC", callback_data="filters_artistic"),
             InlineKeyboardButton("✨ LIGHTING", callback_data="filters_lighting")],
            [InlineKeyboardButton("🎬 CINEMATIC", callback_data="filters_cinematic"),
             InlineKeyboardButton("📱 SOCIAL", callback_data="filters_social")],
            [InlineKeyboardButton("⚡ SPECIAL", callback_data="filters_special"),
             InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
        ]
        
        await query.edit_message_text(
            "🎨 **100+ PROFESSIONAL FILTERS**\n\nChoose category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        is_premium = self.db.is_premium(user_id)
        stats = self.db.get_stats()
        
        if not user_data:
            user_data = self.db.create_user(user_id)
        
        text = f"""
📊 **YOUR STATISTICS**

👤 **User:** {update.effective_user.first_name}
🆔 **ID:** `{user_id}`

📈 **Activity:**
• Total Edits: `{user_data.get('total_edits', 0)}`
• Today's Edits: `{user_data.get('edits_today', 0)}`
• Premium: `{'✅ Active' if is_premium else '❌ Inactive'}`

{f"📅 Expires: {user_data.get('premium_expiry', 'N/A')[:10]}" if is_premium else ''}

🏆 **Global Stats:**
• Total Users: `{stats['total_users']}`
• Premium Users: `{stats['premium_users']}`
• Total Edits: `{stats['total_edits']}`
• Today's Edits: `{stats['today_edits']}`

💎 **Referral Bonus:**
• Referrals: `{user_data.get('referral_count', 0)}`
• Balance: `${user_data.get('balance', 0)}`

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
    
    async def reset_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset to original file"""
        query = update.callback_query
        await query.answer()
        
        file_type = context.user_data.get('file_type')
        
        if file_type == 'video':
            original = context.user_data.get('original_video')
            if original and os.path.exists(original):
                context.user_data['current_video'] = original
                with open(original, 'rb') as f:
                    await query.message.reply_video(video=f, caption="✅ **Reset to original video!**", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("❌ No original file found!")
        
        elif file_type == 'image':
            original = context.user_data.get('original_image')
            if original and os.path.exists(original):
                context.user_data['current_image'] = original
                with open(original, 'rb') as f:
                    await query.message.reply_photo(photo=f, caption="✅ **Reset to original image!**", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("❌ No original file found!")
    
    async def done_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finish editing"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "✅ **Editing complete!**\n\n"
            "Send me another file to continue editing!\n\n"
            "💡 Tip: Use /menu to see all available tools.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Cleanup
        context.user_data.clear()
    
    async def apply_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Apply filter to image/video"""
        query = update.callback_query
        await query.answer()
        
        filter_name = data.replace("filter_", "")
        file_type = context.user_data.get('file_type')
        
        if file_type == 'image':
            image_path = context.user_data.get('current_image')
            if not image_path:
                await query.edit_message_text("❌ No image found!")
                return
            
            await query.edit_message_text(f"🎨 **Applying {filter_name} filter...**", parse_mode=ParseMode.MARKDOWN)
            
            try:
                output_path = self.filters.apply_filter(image_path, filter_name)
                context.user_data['current_image'] = output_path
                
                with open(output_path, 'rb') as f:
                    await query.message.reply_photo(
                        photo=f,
                        caption=f"✅ **Applied {filter_name} filter!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as e:
                await query.message.reply_text(f"❌ Error: {str(e)}")
        
        elif file_type == 'video':
            video_path = context.user_data.get('current_video')
            if not video_path:
                await query.edit_message_text("❌ No video found!")
                return
            
            is_premium = self.db.is_premium(query.from_user.id)
            if not is_premium and filter_name not in ['grayscale', 'sepia', 'blur']:
                keyboard = [[InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="menu_premium")]]
                await query.edit_message_text(
                    "❌ This filter is only available for premium users!\n\nUpgrade to access all 100+ filters.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            await query.edit_message_text(f"🎨 **Applying {filter_name} filter to video...**\nThis may take a moment.", parse_mode=ParseMode.MARKDOWN)
            
            try:
                output_path = self.video_editor.apply_filter(video_path, filter_name)
                context.user_data['current_video'] = output_path
                
                with open(output_path, 'rb') as f:
                    await query.message.reply_video(
                        video=f,
                        caption=f"✅ **Applied {filter_name} filter to video!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as e:
                await query.message.reply_text(f"❌ Error: {str(e)}")
    
    async def initiate_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Initiate premium purchase"""
        query = update.callback_query
        await query.answer()
        
        plan = data.replace("buy_", "")
        
        if plan == "monthly":
            amount = Config.PREMIUM_PRICE_MONTHLY_USD
            days = 30
        elif plan == "yearly":
            amount = Config.PREMIUM_PRICE_YEARLY_USD
            days = 365
        else:  # lifetime
            amount = Config.PREMIUM_PRICE_LIFETIME_USD
            days = 365 * 10
        
        text = f"""
💎 **Purchase Confirmation**

Plan: {plan.upper()}
Amount: ${amount}
Days: {days}

Click below to complete payment:
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"pay_upi_{plan}")],
            [InlineKeyboardButton("⭐ PAY WITH STARS", callback_data=f"pay_stars_{plan}")],
            [InlineKeyboardButton("💸 PAY WITH PAYPAL", callback_data=f"pay_paypal_{plan}")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def show_upi_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show UPI payment details"""
        query = update.callback_query
        await query.answer()
        
        text = f"""
💳 **UPI PAYMENT DETAILS**

**UPI ID:** `{Config.UPI_ID}`
**Name:** Kinva Master Pro

**Steps to Pay:**
1. Open any UPI app (Google Pay, PhonePe, Paytm)
2. Pay to the UPI ID above
3. Amount: ₹{Config.PREMIUM_PRICE_MONTHLY_INR} (Monthly)
4. Send screenshot to @admin
5. Premium will be activated within 24 hours

**Send after payment:**
`/confirm [transaction_id]`

━━━━━━━━━━━━━━━━━━━━━━
⭐ **Or pay with Telegram Stars instantly!**
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐ PAY WITH STARS (Instant)", callback_data="pay_stars")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    
    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process Telegram Stars payment"""
        query = update.callback_query
        await query.answer()
        
        # This would integrate with Telegram Stars API
        await query.edit_message_text(
            "⭐ **Telegram Stars Payment**\n\n"
            "Click the button below to pay 100 Stars for Premium Monthly!\n\n"
            "✅ Instant activation after payment",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ PAY 100 STARS", callback_data="confirm_stars")],
                [InlineKeyboardButton("🔙 BACK", callback_data="menu_premium")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def pay_with_paypal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process PayPal payment"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "💸 **PayPal Payment**\n\n"
            "Pay to: `kinvamaster@paypal.com`\n\n"
            "Amount: $9.99 USD\n\n"
            "Send payment and email receipt to @admin\n\n"
            "Premium will be activated within 24 hours",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ============================================
    # PLACEHOLDER METHODS (to be implemented)
    # ============================================
    
    async def image_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show image tools menu"""
        pass
    
    async def effects_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show effects menu"""
        pass
    
    async def download_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show download menu"""
        pass
    
    async def reverse_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reverse video"""
        pass
    
    async def compress_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compress video"""
        pass
    
    async def add_watermark(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add watermark"""
        pass
    
    async def export_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export video"""
        pass
    
    async def apply_effect(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Apply effect"""
        pass

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    """Main function to run the bot"""
    # Create bot instance
    bot = KinvaMasterBot()
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("menu", bot.menu_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("premium", bot.premium_menu))
    
    # Add conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.trim_video, pattern="^tool_trim$")],
        states={
            bot.TRIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_trim_input)],
        },
        fallbacks=[CommandHandler("cancel", bot.help_command)]
    )
    application.add_handler(conv_handler)
    
    # Add callback and message handlers
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.add_handler(MessageHandler(filters.VIDEO, bot.handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    
    # Start bot
    print(f"""
╔════════════════════════════════════════╗
║     KINVA MASTER PRO BOT STARTED       ║
╠════════════════════════════════════════╣
║ Version: {Config.BOT_VERSION}                                 ║
║ Bot: @{Config.BOT_NAME}                   ║
║ Status: 🟢 RUNNING                      ║
╚════════════════════════════════════════╝
    """)
    
    # Start polling
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
