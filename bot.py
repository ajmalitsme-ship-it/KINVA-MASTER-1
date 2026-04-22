import os
import json
import uuid
import base64
import logging
import asyncio
import threading
import time
from io import BytesIO
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import requests

# Telegram Bot imports
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Configuration
BOT_TOKEN = "8623600399:AAGNn_d6Lq5DRrwelD_rvOUfgsM-jyk8Kf8"
# Replace with your actual bot token from @BotFather
WEBAPP_URL = "https://your-domain.com"  # Replace with your actual domain when deploying
PORT = int(os.environ.get("PORT", 5000))

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "animation_fire_master_key_2024")
CORS(app)

# In-memory storage (use Redis/DB in production)
animation_sessions = {}
user_sessions = {}

# AI Drawing Enhancer API (using Hugging Face or local model)
# You can replace with actual AI service API key
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")

class AnimationSession:
    """Advanced animation session with full features"""
    def __init__(self, session_id, user_id=None):
        self.session_id = session_id
        self.user_id = user_id
        self.frames = []
        self.current_frame_index = 0
        self.canvas_width = 512
        self.canvas_height = 512
        self.fps = 12
        self.animation_name = "Untitled Animation"
        self.created_at = datetime.now()
        self.undo_stack = []
        self.redo_stack = []
        self.layers = [{"name": "Layer 1", "visible": True, "opacity": 1.0}]
        self.current_layer = 0
        self.brush_size = 5
        self.brush_color = "#000000"
        self.brush_type = "pencil"  # pencil, marker, airbrush, eraser
        self.create_initial_frame()
    
    def create_initial_frame(self):
        """Create a blank white frame"""
        img = Image.new('RGBA', (self.canvas_width, self.canvas_height), (255, 255, 255, 255))
        self.frames.append(img)
        self.save_to_undo()
    
    def save_to_undo(self):
        """Save current state to undo stack"""
        if self.frames:
            frame_copy = self.frames[self.current_frame_index].copy()
            self.undo_stack.append(frame_copy)
            self.redo_stack.clear()
            # Limit stack size
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
    
    def undo(self):
        """Undo last action"""
        if len(self.undo_stack) > 0:
            current = self.frames[self.current_frame_index].copy()
            self.redo_stack.append(current)
            restored = self.undo_stack.pop()
            self.frames[self.current_frame_index] = restored
            return True
        return False
    
    def redo(self):
        """Redo last undone action"""
        if len(self.redo_stack) > 0:
            current = self.frames[self.current_frame_index].copy()
            self.undo_stack.append(current)
            restored = self.redo_stack.pop()
            self.frames[self.current_frame_index] = restored
            return True
        return False
    
    def add_blank_frame(self):
        """Add a new blank frame"""
        new_frame = Image.new('RGBA', (self.canvas_width, self.canvas_height), (255, 255, 255, 255))
        self.frames.append(new_frame)
        return len(self.frames) - 1
    
    def duplicate_frame(self, index):
        """Duplicate existing frame"""
        if 0 <= index < len(self.frames):
            copied = self.frames[index].copy()
            self.frames.insert(index + 1, copied)
            return index + 1
        return None
    
    def delete_frame(self, index):
        """Delete a frame"""
        if len(self.frames) > 1 and 0 <= index < len(self.frames):
            del self.frames[index]
            if self.current_frame_index >= len(self.frames):
                self.current_frame_index = len(self.frames) - 1
            return True
        return False
    
    def update_frame_image(self, index, image_data):
        """Update frame with new image data"""
        if 0 <= index < len(self.frames):
            self.save_to_undo()
            if ',' in image_data:
                img_data = base64.b64decode(image_data.split(',')[1])
            else:
                img_data = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            if img.size != (self.canvas_width, self.canvas_height):
                img = img.resize((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
            self.frames[index] = img
            return True
        return False
    
    def get_frame_as_base64(self, index):
        """Get frame as base64 string"""
        if 0 <= index < len(self.frames):
            buffered = BytesIO()
            # Convert RGBA to RGB for PNG
            if self.frames[index].mode == 'RGBA':
                rgb_img = Image.new('RGB', self.frames[index].size, (255, 255, 255))
                rgb_img.paste(self.frames[index], mask=self.frames[index].split()[3] if self.frames[index].mode == 'RGBA' else None)
                rgb_img.save(buffered, format='PNG')
            else:
                self.frames[index].save(buffered, format='PNG')
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        return None
    
    def get_all_frames_base64(self):
        """Get all frames as base64 strings"""
        return [self.get_frame_as_base64(i) for i in range(len(self.frames))]
    
    def export_as_gif(self):
        """Export animation as GIF"""
        if len(self.frames) < 1:
            return None
        duration = int(1000 / self.fps)
        gif_buffer = BytesIO()
        # Convert frames to RGB for GIF
        rgb_frames = []
        for frame in self.frames:
            if frame.mode == 'RGBA':
                rgb = Image.new('RGB', frame.size, (255, 255, 255))
                rgb.paste(frame, mask=frame.split()[3] if frame.mode == 'RGBA' else None)
                rgb_frames.append(rgb)
            else:
                rgb_frames.append(frame.convert('RGB'))
        
        rgb_frames[0].save(
            gif_buffer,
            format='GIF',
            save_all=True,
            append_images=rgb_frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        gif_buffer.seek(0)
        return gif_buffer
    
    def export_as_mp4(self):
        """Export as MP4 (simplified - would need ffmpeg in production)"""
        # This is a placeholder - full MP4 export would require ffmpeg
        return self.export_as_gif()
    
    def apply_ai_enhance(self, image_data, enhancement_type="smooth"):
        """Apply AI-based image enhancement"""
        try:
            # Decode image
            if ',' in image_data:
                img_data = base64.b64decode(image_data.split(',')[1])
            else:
                img_data = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_data)).convert('RGBA')
            
            # Apply different enhancements
            if enhancement_type == "smooth":
                img = img.filter(ImageFilter.SMOOTH_MORE)
            elif enhancement_type == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            elif enhancement_type == "edge_enhance":
                img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            elif enhancement_type == "contour":
                img = img.filter(ImageFilter.CONTOUR)
            elif enhancement_type == "detail":
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
            elif enhancement_type == "brighten":
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.3)
            elif enhancement_type == "ai_fix_lineart":
                # Line art enhancement - threshold and cleanup
                img = img.convert('L')
                threshold = 128
                img = img.point(lambda p: 255 if p > threshold else 0)
                img = img.convert('RGBA')
            
            # Convert back to base64
            buffered = BytesIO()
            img.save(buffered, format='PNG')
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"AI enhancement error: {e}")
            return None
    
    def generate_ai_frame(self, prompt):
        """Generate frame using AI based on text prompt"""
        if not HF_API_TOKEN:
            return None
        try:
            # Using Hugging Face Stable Diffusion API
            API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {"inputs": f"animation style, frame for animation, {prompt}"}
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.resize((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
                buffered = BytesIO()
                img.save(buffered, format='PNG')
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"AI generation error: {e}")
        return None
    
    def apply_color_filter(self, image_data, filter_type):
        """Apply color filter to frame"""
        try:
            if ',' in image_data:
                img_data = base64.b64decode(image_data.split(',')[1])
            else:
                img_data = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_data)).convert('RGBA')
            
            if filter_type == "grayscale":
                img = img.convert('L').convert('RGBA')
            elif filter_type == "sepia":
                sepia_filter = (0.393, 0.769, 0.189, 0.349, 0.686, 0.168, 0.272, 0.534, 0.131)
                img = img.convert('RGB')
                width, height = img.size
                pixels = img.load()
                for x in range(width):
                    for y in range(height):
                        r, g, b = pixels[x, y]
                        tr = int(r * 0.393 + g * 0.769 + b * 0.189)
                        tg = int(r * 0.349 + g * 0.686 + b * 0.168)
                        tb = int(r * 0.272 + g * 0.534 + b * 0.131)
                        pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
                img = img.convert('RGBA')
            elif filter_type == "invert":
                img = Image.eval(img.convert('RGB'), lambda x: 255 - x).convert('RGBA')
            elif filter_type == "vibrant":
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.5)
            
            buffered = BytesIO()
            img.save(buffered, format='PNG')
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Color filter error: {e}")
            return None
    
    def onion_skin(self, current_index, opacity=0.3):
        """Create onion skin overlay of previous and next frames"""
        if len(self.frames) < 2:
            return None
        
        current = self.frames[current_index].copy()
        overlay = Image.new('RGBA', current.size, (0, 0, 0, 0))
        
        # Show previous frame
        if current_index > 0:
            prev = self.frames[current_index - 1].copy()
            prev.putalpha(int(255 * opacity))
            overlay = Image.alpha_composite(overlay, prev)
        
        # Show next frame
        if current_index < len(self.frames) - 1:
            nxt = self.frames[current_index + 1].copy()
            nxt.putalpha(int(255 * opacity))
            overlay = Image.alpha_composite(overlay, nxt)
        
        # Composite with current
        result = Image.alpha_composite(overlay.convert('RGBA'), current)
        buffered = BytesIO()
        result.save(buffered, format='PNG')
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def get_session(session_id, user_id=None):
    """Get or create animation session"""
    if session_id not in animation_sessions:
        animation_sessions[session_id] = AnimationSession(session_id, user_id)
    return animation_sessions[session_id]

# Flask Routes
@app.route('/')
def index():
    """Main web app entry point"""
    session_id = request.cookies.get('animation_session_id', str(uuid.uuid4()))
    user_id = request.args.get('user_id')
    resp = make_response(render_template('animation_maker.html', session_id=session_id, bot_username="@ANIFiremationBot"))
    resp.set_cookie('animation_session_id', session_id, max_age=30*24*3600)
    return resp

@app.route('/api/get_frames', methods=['POST'])
def get_frames():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    frames_base64 = session.get_all_frames_base64()
    return jsonify({
        'frames': frames_base64,
        'current_index': session.current_frame_index,
        'frame_count': len(session.frames),
        'canvas_width': session.canvas_width,
        'canvas_height': session.canvas_height,
        'fps': session.fps,
        'animation_name': session.animation_name
    })

@app.route('/api/save_frame', methods=['POST'])
def save_frame():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    image_data = data.get('image_data')
    if not session_id or frame_index is None or not image_data:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    if session.update_frame_image(frame_index, image_data):
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid frame index'}), 400

@app.route('/api/add_frame', methods=['POST'])
def add_frame():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    new_index = session.add_blank_frame()
    return jsonify({'success': True, 'frame_index': new_index, 'frame_count': len(session.frames)})

@app.route('/api/duplicate_frame', methods=['POST'])
def duplicate_frame():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    if not session_id or frame_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    new_index = session.duplicate_frame(frame_index)
    if new_index is not None:
        frames_base64 = session.get_all_frames_base64()
        return jsonify({'success': True, 'new_index': new_index, 'frames': frames_base64, 'frame_count': len(session.frames)})
    return jsonify({'error': 'Invalid frame index'}), 400

@app.route('/api/delete_frame', methods=['POST'])
def delete_frame():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    if not session_id or frame_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    if session.delete_frame(frame_index):
        frames_base64 = session.get_all_frames_base64()
        return jsonify({'success': True, 'frames': frames_base64, 'frame_count': len(session.frames), 'current_index': min(session.current_frame_index, len(session.frames)-1)})
    return jsonify({'error': 'Cannot delete last frame'}), 400

@app.route('/api/undo', methods=['POST'])
def undo():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    if session.undo():
        frame_b64 = session.get_frame_as_base64(session.current_frame_index)
        return jsonify({'success': True, 'frame_data': frame_b64})
    return jsonify({'error': 'Nothing to undo'}), 400

@app.route('/api/redo', methods=['POST'])
def redo():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    if session.redo():
        frame_b64 = session.get_frame_as_base64(session.current_frame_index)
        return jsonify({'success': True, 'frame_data': frame_b64})
    return jsonify({'error': 'Nothing to redo'}), 400

@app.route('/api/clear_all', methods=['POST'])
def clear_all():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    session.frames = []
    session.add_blank_frame()
    session.current_frame_index = 0
    frames_base64 = session.get_all_frames_base64()
    return jsonify({'success': True, 'frames': frames_base64, 'frame_count': 1, 'current_index': 0})

@app.route('/api/export_gif', methods=['POST'])
def export_gif():
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'No session_id'}), 400
    session = get_session(session_id)
    gif_buffer = session.export_as_gif()
    if gif_buffer:
        return send_file(gif_buffer, mimetype='image/gif', as_attachment=True, download_name=f'{session.animation_name}.gif')
    return jsonify({'error': 'Failed to export GIF'}), 500

@app.route('/api/set_fps', methods=['POST'])
def set_fps():
    data = request.get_json()
    session_id = data.get('session_id')
    fps = data.get('fps')
    if not session_id or not fps:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    session.fps = max(1, min(60, int(fps)))
    return jsonify({'success': True, 'fps': session.fps})

@app.route('/api/ai_enhance', methods=['POST'])
def ai_enhance():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    enhancement_type = data.get('enhancement_type', 'smooth')
    if not session_id or frame_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    frame_data = session.get_frame_as_base64(frame_index)
    if frame_data:
        enhanced = session.apply_ai_enhance(f"data:image/png;base64,{frame_data}", enhancement_type)
        if enhanced:
            session.update_frame_image(frame_index, f"data:image/png;base64,{enhanced}")
            return jsonify({'success': True, 'frame_data': enhanced})
    return jsonify({'error': 'AI enhancement failed'}), 500

@app.route('/api/ai_generate', methods=['POST'])
def ai_generate():
    data = request.get_json()
    session_id = data.get('session_id')
    prompt = data.get('prompt', '')
    if not session_id or not prompt:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    generated = session.generate_ai_frame(prompt)
    if generated:
        session.add_blank_frame()
        new_index = len(session.frames) - 1
        session.update_frame_image(new_index, f"data:image/png;base64,{generated}")
        frames_base64 = session.get_all_frames_base64()
        return jsonify({'success': True, 'frames': frames_base64, 'frame_count': len(session.frames), 'new_index': new_index})
    return jsonify({'error': 'AI generation failed. Please check API token.'}), 500

@app.route('/api/apply_filter', methods=['POST'])
def apply_filter():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    filter_type = data.get('filter_type', 'grayscale')
    if not session_id or frame_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    frame_data = session.get_frame_as_base64(frame_index)
    if frame_data:
        filtered = session.apply_color_filter(f"data:image/png;base64,{frame_data}", filter_type)
        if filtered:
            session.update_frame_image(frame_index, f"data:image/png;base64,{filtered}")
            return jsonify({'success': True, 'frame_data': filtered})
    return jsonify({'error': 'Filter application failed'}), 500

@app.route('/api/onion_skin', methods=['POST'])
def onion_skin():
    data = request.get_json()
    session_id = data.get('session_id')
    frame_index = data.get('frame_index')
    if not session_id or frame_index is None:
        return jsonify({'error': 'Missing parameters'}), 400
    session = get_session(session_id)
    onion_data = session.onion_skin(frame_index)
    if onion_data:
        return jsonify({'success': True, 'overlay_data': onion_data})
    return jsonify({'error': 'Onion skin failed'}), 400

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_text = f"""🔥 *Welcome to ANIFiremation!* 🔥

Hello {user.first_name}! I'm your AI-powered animation creation assistant.

✨ *Features:*
• 🎨 Full animation studio with drawing tools
• 🤖 AI drawing enhancer and fixer
• 🎬 Frame-by-frame animation maker
• 🌈 Color filters and effects
• 📱 Export as GIF or MP4
• 💫 Onion skinning for smooth animation

Click the button below to launch the Animation Studio!"""

    keyboard = [[InlineKeyboardButton("🎬 Launch Animation Studio", web_app=WebAppInfo(url=WEBAPP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """📚 *ANIFiremation Help*

*Drawing Tools:*
• Pencil, Marker, Airbrush, Eraser
• Adjustable brush size and color
• Undo/Redo functionality

*AI Features:*
• Smart line art fixer
• Image enhancement (smooth, sharpen, detail)
• AI frame generation from text prompts

*Animation Tools:*
• Add/duplicate/delete frames
• Onion skinning for better timing
• Adjust FPS (1-60)
• Export as GIF

*Filters:*
• Grayscale, Sepia, Invert, Vibrant
• Edge enhancement, contour effects

Need more help? Visit our documentation!"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data from web app"""
    data = update.effective_message.web_app_data
    if data:
        await update.message.reply_text(f"✨ Animation saved! Your masterpiece has been processed.")

# Setup bot application
def setup_bot():
    """Initialize and run Telegram bot in separate thread"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("No bot token provided. Bot will not run. Please set BOT_TOKEN.")
        return None
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
    
    def run_bot():
        logger.info("Starting Telegram bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    return application

# Create templates directory and HTML
os.makedirs('templates', exist_ok=True)

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>ANIFiremation — AI Animation Studio</title>
    <style>
        :root {
            --primary: #ff4757;
            --primary-dark: #ff3838;
            --secondary: #2ed573;
            --dark: #2f3542;
            --light: #f1f2f6;
            --accent: #5352ed;
            --gradient: linear-gradient(135deg, #ff4757, #ff6b81, #ffa502);
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e1e2f, #2d2d44);
            min-height: 100vh;
            color: #fff;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        /* Header */
        .header {
            text-align: center;
            margin-bottom: 30px;
            position: relative;
        }
        .logo {
            font-size: 3rem;
            font-weight: 800;
            background: var(--gradient);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 0 30px rgba(255,71,87,0.3);
            letter-spacing: -1px;
        }
        .logo span {
            font-size: 2rem;
        }
        .subtitle {
            color: rgba(255,255,255,0.7);
            margin-top: 5px;
        }
        /* Main Layout */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 20px;
        }
        @media (max-width: 900px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        /* Canvas Area */
        .canvas-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 28px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .canvas-wrapper {
            display: flex;
            justify-content: center;
            background: #fff;
            border-radius: 20px;
            padding: 10px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        canvas {
            display: block;
            width: 100%;
            height: auto;
            cursor: crosshair;
            border-radius: 12px;
        }
        #mainCanvas {
            width: 100%;
            max-width: 512px;
            aspect-ratio: 1/1;
        }
        /* Tools */
        .tools-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 20px;
            justify-content: center;
        }
        .tool-btn {
            background: rgba(255,255,255,0.15);
            border: none;
            color: white;
            padding: 10px 18px;
            border-radius: 40px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            backdrop-filter: blur(5px);
        }
        .tool-btn:hover, .tool-btn.active {
            background: var(--primary);
            transform: translateY(-2px);
        }
        .tool-btn.secondary { background: rgba(45, 213, 115, 0.8); }
        .tool-btn.danger { background: rgba(255, 71, 87, 0.8); }
        .tool-btn.warning { background: rgba(255, 165, 2, 0.8); }
        
        /* Sidebar */
        .sidebar {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border-radius: 28px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.15);
        }
        .section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: var(--secondary);
            border-left: 3px solid var(--primary);
            padding-left: 10px;
        }
        /* Frames Strip */
        .frames-strip {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 10px 0;
        }
        .frame-card {
            flex-shrink: 0;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 8px;
            border: 2px solid transparent;
        }
        .frame-card.active {
            border-color: var(--primary);
            background: rgba(255,71,87,0.2);
            transform: scale(1.02);
        }
        .frame-card canvas {
            width: 80px;
            height: 80px;
            border-radius: 8px;
        }
        .frame-number {
            font-size: 11px;
            margin-top: 5px;
        }
        /* AI Panel */
        .ai-panel {
            background: linear-gradient(135deg, rgba(83,82,237,0.2), rgba(255,71,87,0.2));
            border-radius: 20px;
            padding: 15px;
            margin-top: 15px;
        }
        .ai-input {
            width: 100%;
            padding: 10px;
            border-radius: 12px;
            border: none;
            margin: 10px 0;
            background: rgba(255,255,255,0.9);
        }
        .filter-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .filter-chip {
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-chip:hover {
            background: var(--primary);
        }
        .status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 12px;
            text-align: center;
            font-size: 13px;
        }
        input[type="color"] {
            width: 50px;
            height: 50px;
            border-radius: 25px;
            border: 2px solid white;
            cursor: pointer;
        }
        input[type="range"] {
            width: 140px;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">🔥 ANIFiremation <span>Studio</span></div>
        <div class="subtitle">AI-Powered Frame Animation • Draw • Enhance • Export</div>
    </div>
    
    <div class="main-grid">
        <div class="canvas-card">
            <div class="canvas-wrapper">
                <canvas id="mainCanvas" width="512" height="512"></canvas>
            </div>
            
            <div class="tools-grid">
                <button class="tool-btn" id="pencilBtn">✏️ Pencil</button>
                <button class="tool-btn" id="markerBtn">🖌️ Marker</button>
                <button class="tool-btn" id="airbrushBtn">💨 Airbrush</button>
                <button class="tool-btn" id="eraserBtn">🧽 Eraser</button>
                <input type="color" id="penColor" value="#000000">
                <input type="range" id="brushSize" min="1" max="40" value="5">
                <span id="sizeValue" style="font-size:12px">5px</span>
                <button class="tool-btn secondary" id="undoBtn">↩️ Undo</button>
                <button class="tool-btn secondary" id="redoBtn">↪️ Redo</button>
                <button class="tool-btn warning" id="clearCanvasBtn">🗑️ Clear</button>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="section">
                <div class="section-title">🎬 Frame Control</div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px">
                    <button class="tool-btn" id="addFrameBtn">+ New Frame</button>
                    <button class="tool-btn secondary" id="duplicateBtn">📋 Duplicate</button>
                    <button class="tool-btn danger" id="deleteBtn">❌ Delete</button>
                    <button class="tool-btn" id="onionSkinBtn">🧅 Onion Skin</button>
                </div>
                <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px">
                    <span>FPS:</span>
                    <input type="number" id="fpsInput" min="1" max="60" value="12" style="width:70px">
                    <button class="tool-btn secondary" id="setFpsBtn">Set</button>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📽️ Frames (<span id="frameCount">0</span>)</div>
                <div id="framesContainer" class="frames-strip"></div>
            </div>
            
            <div class="ai-panel">
                <div class="section-title">🤖 AI Tools</div>
                <div class="filter-buttons">
                    <div class="filter-chip" data-ai="smooth">✨ Smooth</div>
                    <div class="filter-chip" data-ai="sharpen">🔪 Sharpen</div>
                    <div class="filter-chip" data-ai="detail">💎 Detail</div>
                    <div class="filter-chip" data-ai="ai_fix_lineart">✍️ Fix Lineart</div>
                    <div class="filter-chip" data-ai="brighten">☀️ Brighten</div>
                </div>
                <input type="text" id="aiPrompt" class="ai-input" placeholder="Describe a frame... e.g., 'fire dragon'">
                <button class="tool-btn" id="aiGenerateBtn" style="width:100%; margin-top:8px">🎨 AI Generate Frame</button>
                
                <div class="section-title" style="margin-top: 15px">🌈 Filters</div>
                <div class="filter-buttons">
                    <div class="filter-chip" data-filter="grayscale">⚫ Grayscale</div>
                    <div class="filter-chip" data-filter="sepia">🟤 Sepia</div>
                    <div class="filter-chip" data-filter="invert">🎭 Invert</div>
                    <div class="filter-chip" data-filter="vibrant">💜 Vibrant</div>
                    <div class="filter-chip" data-filter="edge_enhance">📐 Edge</div>
                </div>
            </div>
            
            <div class="section" style="margin-top: 15px">
                <button class="tool-btn secondary" id="previewBtn" style="width:48%; margin:1%">▶️ Preview</button>
                <button class="tool-btn" id="exportGifBtn" style="width:48%; margin:1%; background:#2ed573">💾 Export GIF</button>
                <button class="tool-btn danger" id="clearAllBtn" style="width:100%; margin-top:8px">⚠️ Clear All Frames</button>
            </div>
            <div id="status" class="status"></div>
        </div>
    </div>
</div>

<script>
    const sessionId = '{{ session_id }}';
    let frames = [];
    let currentFrameIndex = 0;
    let canvasWidth = 512, canvasHeight = 512;
    let fps = 12;
    let isDrawing = false;
    let lastX = 0, lastY = 0;
    let currentTool = 'pencil';
    let brushColor = '#000000';
    let brushSize = 5;
    
    const canvas = document.getElementById('mainCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    
    // Tool selection
    document.getElementById('pencilBtn').onclick = () => { currentTool = 'pencil'; brushColor = document.getElementById('penColor').value; };
    document.getElementById('markerBtn').onclick = () => { currentTool = 'marker'; };
    document.getElementById('airbrushBtn').onclick = () => { currentTool = 'airbrush'; };
    document.getElementById('eraserBtn').onclick = () => { currentTool = 'eraser'; };
    document.getElementById('penColor').onchange = (e) => { brushColor = e.target.value; };
    document.getElementById('brushSize').oninput = (e) => { brushSize = e.target.value; document.getElementById('sizeValue').innerText = brushSize + 'px'; };
    
    function getCanvasCoords(e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        let clientX, clientY;
        if (e.touches) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        let x = (clientX - rect.left) * scaleX;
        let y = (clientY - rect.top) * scaleY;
        x = Math.min(Math.max(0, x), canvas.width);
        y = Math.min(Math.max(0, y), canvas.height);
        return { x, y };
    }
    
    function draw(e) {
        if (!isDrawing) return;
        e.preventDefault();
        const pos = getCanvasCoords(e);
        const currentX = pos.x, currentY = pos.y;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(currentX, currentY);
        ctx.strokeStyle = currentTool === 'eraser' ? 'white' : brushColor;
        ctx.lineWidth = brushSize;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        if (currentTool === 'airbrush') {
            ctx.globalAlpha = 0.3;
        } else {
            ctx.globalAlpha = 1;
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
        lastX = currentX;
        lastY = currentY;
    }
    
    function startDraw(e) {
        isDrawing = true;
        const pos = getCanvasCoords(e);
        lastX = pos.x;
        lastY = pos.y;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(lastX, lastY);
        ctx.stroke();
    }
    
    function stopDraw() {
        isDrawing = false;
        saveCurrentFrame();
    }
    
    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('mouseleave', stopDraw);
    canvas.addEventListener('touchstart', startDraw);
    canvas.addEventListener('touchmove', draw);
    canvas.addEventListener('touchend', stopDraw);
    
    function saveCurrentFrame() {
        const imageData = canvas.toDataURL('image/png');
        fetch('/api/save_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, frame_index: currentFrameIndex, image_data: imageData })
        }).then(res => res.json()).then(data => {
            if (data.success) frames[currentFrameIndex] = imageData;
            updateThumbnail(currentFrameIndex);
        });
    }
    
    function loadFrame(index) {
        if (frames[index]) {
            const img = new Image();
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                currentFrameIndex = index;
                highlightActive();
            };
            img.src = frames[index];
        }
    }
    
    function updateThumbnail(index) {
        const thumbCanvas = document.getElementById(`thumb_${index}`);
        if (thumbCanvas && frames[index]) {
            const img = new Image();
            img.onload = () => {
                const tCtx = thumbCanvas.getContext('2d');
                thumbCanvas.width = 80;
                thumbCanvas.height = 80;
                tCtx.drawImage(img, 0, 0, 80, 80);
            };
            img.src = frames[index];
        }
    }
    
    function highlightActive() {
        document.querySelectorAll('.frame-card').forEach(el => el.classList.remove('active'));
        const active = document.querySelector(`.frame-card[data-index="${currentFrameIndex}"]`);
        if (active) active.classList.add('active');
    }
    
    function renderFrames() {
        const container = document.getElementById('framesContainer');
        container.innerHTML = '';
        frames.forEach((frame, idx) => {
            const div = document.createElement('div');
            div.className = 'frame-card';
            div.setAttribute('data-index', idx);
            div.onclick = () => loadFrame(idx);
            const thumbCanvas = document.createElement('canvas');
            thumbCanvas.id = `thumb_${idx}`;
            thumbCanvas.width = 80;
            thumbCanvas.height = 80;
            const img = new Image();
            img.onload = () => {
                const tCtx = thumbCanvas.getContext('2d');
                tCtx.drawImage(img, 0, 0, 80, 80);
            };
            img.src = frame;
            const numSpan = document.createElement('div');
            numSpan.className = 'frame-number';
            numSpan.innerText = `Frame ${idx+1}`;
            div.appendChild(thumbCanvas);
            div.appendChild(numSpan);
            container.appendChild(div);
            setTimeout(() => {
                if (frames[idx]) {
                    const tCtx = thumbCanvas.getContext('2d');
                    const tempImg = new Image();
                    tempImg.onload = () => tCtx.drawImage(tempImg, 0, 0, 80, 80);
                    tempImg.src = frames[idx];
                }
            }, 10);
        });
        document.getElementById('frameCount').innerText = frames.length;
        highlightActive();
    }
    
    function fetchFrames() {
        fetch('/api/get_frames', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        }).then(res => res.json()).then(data => {
            frames = data.frames.map(b64 => 'data:image/png;base64,' + b64);
            currentFrameIndex = data.current_index;
            fps = data.fps;
            document.getElementById('fpsInput').value = fps;
            if (frames.length) loadFrame(currentFrameIndex);
            renderFrames();
        });
    }
    
    async function apiCall(endpoint, body) {
        const res = await fetch(endpoint, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, ...body })
        });
        return res.json();
    }
    
    document.getElementById('addFrameBtn').onclick = async () => {
        await apiCall('/api/add_frame', {});
        fetchFrames();
        showStatus('New frame added', 'success');
    };
    document.getElementById('duplicateBtn').onclick = async () => {
        await apiCall('/api/duplicate_frame', { frame_index: currentFrameIndex });
        fetchFrames();
        showStatus('Frame duplicated', 'success');
    };
    document.getElementById('deleteBtn').onclick = async () => {
        const res = await apiCall('/api/delete_frame', { frame_index: currentFrameIndex });
        if (res.success) {
            frames = res.frames.map(b64 => 'data:image/png;base64,' + b64);
            renderFrames();
            loadFrame(res.current_index);
            showStatus('Frame deleted', 'info');
        } else showStatus('Cannot delete last frame', 'error');
    };
    document.getElementById('clearCanvasBtn').onclick = () => {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        saveCurrentFrame();
    };
    document.getElementById('clearAllBtn').onclick = async () => {
        if (confirm('Delete ALL frames?')) {
            await apiCall('/api/clear_all', {});
            fetchFrames();
            showStatus('All cleared', 'warning');
        }
    };
    document.getElementById('undoBtn').onclick = async () => {
        const res = await apiCall('/api/undo', {});
        if (res.success && res.frame_data) {
            loadCurrentFromBase64(res.frame_data);
        }
    };
    document.getElementById('redoBtn').onclick = async () => {
        const res = await apiCall('/api/redo', {});
        if (res.success && res.frame_data) loadCurrentFromBase64(res.frame_data);
    };
    function loadCurrentFromBase64(b64) {
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            frames[currentFrameIndex] = canvas.toDataURL();
            updateThumbnail(currentFrameIndex);
        };
        img.src = 'data:image/png;base64,' + b64;
    }
    document.getElementById('setFpsBtn').onclick = async () => {
        const newFps = parseInt(document.getElementById('fpsInput').value);
        await apiCall('/api/set_fps', { fps: newFps });
        fps = newFps;
        showStatus(`FPS set to ${fps}`, 'success');
    };
    document.getElementById('exportGifBtn').onclick = () => {
        fetch('/api/export_gif', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        }).then(res => res.blob()).then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'animation.gif';
            a.click();
            URL.revokeObjectURL(url);
        });
    };
    document.getElementById('previewBtn').onclick = () => {
        if (!frames.length) return;
        let idx = 0;
        const win = window.open();
        win.document.write(`<body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh"><img id="previewImg" src="${frames[0]}" style="max-width:90vw"></body><script>const frames=${JSON.stringify(frames)};let i=0;setInterval(()=>{i=(i+1)%frames.length;document.getElementById('previewImg').src=frames[i]},${1000/fps})<\\/script>`);
    };
    document.getElementById('aiGenerateBtn').onclick = async () => {
        const prompt = document.getElementById('aiPrompt').value;
        if (!prompt) { showStatus('Enter a prompt', 'error'); return; }
        showStatus('Generating...', 'info');
        const res = await apiCall('/api/ai_generate', { prompt });
        if (res.success) {
            frames = res.frames.map(b64 => 'data:image/png;base64,' + b64);
            renderFrames();
            loadFrame(res.new_index);
            showStatus('AI frame generated!', 'success');
        } else showStatus('AI failed: check token', 'error');
    };
    document.querySelectorAll('[data-ai]').forEach(el => {
        el.onclick = async () => {
            const type = el.getAttribute('data-ai');
            const res = await apiCall('/api/ai_enhance', { frame_index: currentFrameIndex, enhancement_type: type });
            if (res.success && res.frame_data) loadCurrentFromBase64(res.frame_data);
        };
    });
    document.querySelectorAll('[data-filter]').forEach(el => {
        el.onclick = async () => {
            const type = el.getAttribute('data-filter');
            const res = await apiCall('/api/apply_filter', { frame_index: currentFrameIndex, filter_type: type });
            if (res.success && res.frame_data) loadCurrentFromBase64(res.frame_data);
        };
    });
    document.getElementById('onionSkinBtn').onclick = async () => {
        const res = await apiCall('/api/onion_skin', { frame_index: currentFrameIndex });
        if (res.success && res.overlay_data) {
            const img = new Image();
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
            };
            img.src = 'data:image/png;base64,' + res.overlay_data;
        }
    };
    function showStatus(msg, type) {
        const statusDiv = document.getElementById('status');
        statusDiv.innerText = msg;
        statusDiv.style.background = type === 'error' ? '#ff4757' : type === 'success' ? '#2ed573' : '#ffa502';
        statusDiv.style.color = 'white';
        setTimeout(() => statusDiv.innerText = '', 2000);
    }
    fetchFrames();
</script>
</body>
</html>
'''

with open('templates/animation_maker.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

from flask import make_response

# Run Flask and Bot
if __name__ == '__main__':
    print("=" * 60)
    print("🔥 ANIFiremation Animation Studio 🔥")
    print("=" * 60)
    print("✨ Web App running at: http://localhost:5000")
    print("🤖 Telegram Bot will start if BOT_TOKEN is configured")
    print("📌 Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token from @BotFather")
    print("📌 For AI features, set HF_API_TOKEN environment variable")
    print("=" * 60)
    
    # Start bot in background
    setup_bot()
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=PORT)

