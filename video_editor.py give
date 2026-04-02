# ============================================
# VIDEO_EDITOR.PY - COMPLETE VIDEO EDITING TOOLS
# KINVA MASTER PRO - 40+ VIDEO EDITING FEATURES
# ============================================

import os
import cv2
import numpy as np
from PIL import Image
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import logging
import random
import math

# Video processing imports
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
        concatenate_videoclips, ImageClip, ColorClip, CompositeAudioClip,
        vfx, afx
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("Warning: MoviePy not available. Some features disabled.")

from config import Config

logger = logging.getLogger(__name__)


class VideoEditor:
    """Complete Video Editing Class with 40+ Tools"""
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm', '.m4v']
        self.temp_dir = Config.TEMP_DIR
        self.output_dir = Config.OUTPUT_DIR
        
    def generate_filename(self, extension: str = ".mp4") -> str:
        """Generate unique filename for output"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_num = random.randint(1000, 9999)
        return os.path.join(self.output_dir, f"video_{timestamp}_{random_num}{extension}")
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information"""
        if not MOVIEPY_AVAILABLE:
            return self._get_video_info_ffmpeg(video_path)
        
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': (clip.w, clip.h),
                'resolution': f"{clip.w}x{clip.h}",
                'audio': clip.audio is not None,
                'size_mb': os.path.getsize(video_path) / (1024 * 1024)
            }
            clip.close()
            return info
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return self._get_video_info_ffmpeg(video_path)
    
    def _get_video_info_ffmpeg(self, video_path: str) -> Dict[str, Any]:
        """Get video info using ffmpeg"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            import json
            data = json.loads(result.stdout)
            
            duration = float(data.get('format', {}).get('duration', 0))
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
            if video_stream:
                width = int(video_stream.get('width', 0))
                height = int(video_stream.get('height', 0))
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 0
                else:
                    fps = float(fps_str)
            else:
                width = height = fps = 0
            
            return {
                'duration': duration,
                'fps': fps,
                'size': (width, height),
                'resolution': f"{width}x{height}",
                'audio': any(s.get('codec_type') == 'audio' for s in data.get('streams', [])),
                'size_mb': round(size_mb, 2)
            }
        except Exception as e:
            logger.error(f"FFprobe error: {e}")
            return {'duration': 0, 'fps': 0, 'size': (0, 0), 'resolution': 'Unknown', 'audio': False, 'size_mb': 0}
    
    # ============================================
    # BASIC EDITING TOOLS (1-10)
    # ============================================
    
    def trim(self, video_path: str, start_time: float, end_time: float = None) -> str:
        """Tool 1: Trim video"""
        if not MOVIEPY_AVAILABLE:
            return self._trim_ffmpeg(video_path, start_time, end_time)
        
        try:
            clip = VideoFileClip(video_path)
            if end_time:
                trimmed = clip.subclip(start_time, end_time)
            else:
                trimmed = clip.subclip(start_time)
            
            output_path = self.generate_filename()
            trimmed.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            trimmed.close()
            return output_path
        except Exception as e:
            logger.error(f"Trim error: {e}")
            raise
    
    def _trim_ffmpeg(self, video_path: str, start_time: float, end_time: float = None) -> str:
        """Trim using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-ss', str(start_time)]
        if end_time:
            duration = end_time - start_time
            cmd += ['-t', str(duration)]
        cmd += ['-c', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def crop(self, video_path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        """Tool 2: Crop video"""
        if not MOVIEPY_AVAILABLE:
            return self._crop_ffmpeg(video_path, x1, y1, x2, y2)
        
        try:
            clip = VideoFileClip(video_path)
            cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
            output_path = self.generate_filename()
            cropped.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            cropped.close()
            return output_path
        except Exception as e:
            logger.error(f"Crop error: {e}")
            raise
    
    def _crop_ffmpeg(self, video_path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        """Crop using ffmpeg"""
        output_path = self.generate_filename()
        width = x2 - x1
        height = y2 - y1
        cmd = ['ffmpeg', '-i', video_path, '-filter:v', f'crop={width}:{height}:{x1}:{y1}', '-c:a', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def resize(self, video_path: str, width: int, height: int) -> str:
        """Tool 3: Resize video"""
        if not MOVIEPY_AVAILABLE:
            return self._resize_ffmpeg(video_path, width, height)
        
        try:
            clip = VideoFileClip(video_path)
            resized = clip.resize(newsize=(width, height))
            output_path = self.generate_filename()
            resized.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            resized.close()
            return output_path
        except Exception as e:
            logger.error(f"Resize error: {e}")
            raise
    
    def _resize_ffmpeg(self, video_path: str, width: int, height: int) -> str:
        """Resize using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'scale={width}:{height}', '-c:a', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def rotate(self, video_path: str, angle: int) -> str:
        """Tool 4: Rotate video (90, 180, 270 degrees)"""
        if not MOVIEPY_AVAILABLE:
            return self._rotate_ffmpeg(video_path, angle)
        
        try:
            clip = VideoFileClip(video_path)
            rotated = clip.rotate(angle)
            output_path = self.generate_filename()
            rotated.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            rotated.close()
            return output_path
        except Exception as e:
            logger.error(f"Rotate error: {e}")
            raise
    
    def _rotate_ffmpeg(self, video_path: str, angle: int) -> str:
        """Rotate using ffmpeg"""
        output_path = self.generate_filename()
        rotate_filter = {90: 'transpose=1', 180: 'transpose=2,transpose=2', 270: 'transpose=2'}.get(angle, 'transpose=1')
        cmd = ['ffmpeg', '-i', video_path, '-vf', rotate_filter, '-c:a', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def flip_horizontal(self, video_path: str) -> str:
        """Tool 5: Flip video horizontally"""
        if not MOVIEPY_AVAILABLE:
            return self._flip_ffmpeg(video_path, 'hflip')
        
        try:
            clip = VideoFileClip(video_path)
            flipped = clip.fx(vfx.mirror_x)
            output_path = self.generate_filename()
            flipped.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            flipped.close()
            return output_path
        except Exception as e:
            logger.error(f"Flip horizontal error: {e}")
            raise
    
    def flip_vertical(self, video_path: str) -> str:
        """Tool 6: Flip video vertically"""
        if not MOVIEPY_AVAILABLE:
            return self._flip_ffmpeg(video_path, 'vflip')
        
        try:
            clip = VideoFileClip(video_path)
            flipped = clip.fx(vfx.mirror_y)
            output_path = self.generate_filename()
            flipped.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            flipped.close()
            return output_path
        except Exception as e:
            logger.error(f"Flip vertical error: {e}")
            raise
    
    def _flip_ffmpeg(self, video_path: str, flip_type: str) -> str:
        """Flip using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', flip_type, '-c:a', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def speed(self, video_path: str, factor: float) -> str:
        """Tool 7: Change video speed (0.1x to 8x)"""
        if not MOVIEPY_AVAILABLE:
            return self._speed_ffmpeg(video_path, factor)
        
        try:
            clip = VideoFileClip(video_path)
            sped = clip.fx(vfx.speedx, factor)
            output_path = self.generate_filename()
            sped.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            sped.close()
            return output_path
        except Exception as e:
            logger.error(f"Speed error: {e}")
            raise
    
    def _speed_ffmpeg(self, video_path: str, factor: float) -> str:
        """Speed change using ffmpeg"""
        output_path = self.generate_filename()
        video_filter = f'setpts={1/factor}*PTS'
        audio_filter = f'atempo={factor}' if factor <= 2 else f'atempo=2.0,atempo={factor/2}'
        cmd = ['ffmpeg', '-i', video_path, '-filter:v', video_filter, '-filter:a', audio_filter, '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def reverse(self, video_path: str) -> str:
        """Tool 8: Reverse video"""
        if not MOVIEPY_AVAILABLE:
            return self._reverse_ffmpeg(video_path)
        
        try:
            clip = VideoFileClip(video_path)
            reversed_clip = clip.fx(vfx.time_mirror)
            output_path = self.generate_filename()
            reversed_clip.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            reversed_clip.close()
            return output_path
        except Exception as e:
            logger.error(f"Reverse error: {e}")
            raise
    
    def _reverse_ffmpeg(self, video_path: str) -> str:
        """Reverse using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', 'reverse', '-af', 'areverse', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def loop(self, video_path: str, times: int) -> str:
        """Tool 9: Loop video multiple times"""
        if not MOVIEPY_AVAILABLE:
            return self._loop_ffmpeg(video_path, times)
        
        try:
            clip = VideoFileClip(video_path)
            clips = [clip] * times
            looped = concatenate_videoclips(clips)
            output_path = self.generate_filename()
            looped.write_videofile(output_path, logger=None, verbose=False)
            clip.close()
            looped.close()
            return output_path
        except Exception as e:
            logger.error(f"Loop error: {e}")
            raise
    
    def _loop_ffmpeg(self, video_path: str, times: int) -> str:
        """Loop using ffmpeg"""
        output_path = self.generate_filename()
        # Create filter complex for looping
        filter_complex = f"loop=loop={times}:size=1,setpts=PTS/{times}"
        cmd = ['ffmpeg', '-i', video_path, '-filter:v', filter_complex, '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def merge(self, video_paths: List[str]) -> str:
        """Tool 10: Merge multiple videos"""
        if not MOVIEPY_AVAILABLE:
            return self._merge_ffmpeg(video_paths)
        
        try:
            clips = [VideoFileClip(path) for path in video_paths]
            merged = concatenate_videoclips(clips)
            output_path = self.generate_filename()
            merged.write_videofile(output_path, logger=None, verbose=False)
            for clip in clips:
                clip.close()
            merged.close()
            return output_path
        except Exception as e:
            logger.error(f"Merge error: {e}")
            raise
    
    def _merge_ffmpeg(self, video_paths: List[str]) -> str:
        """Merge using ffmpeg"""
        output_path = self.generate_filename()
        
        # Create file list for ffmpeg
        list_file = os.path.join(self.temp_dir, "merge_list.txt")
        with open(list_file, 'w') as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")
        
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        os.remove(list_file)
        return output_path
    
    # ============================================
    # AUDIO TOOLS (11-20)
    # ============================================
    
    def extract_audio(self, video_path: str, format: str = "mp3") -> str:
        """Tool 11: Extract audio from video"""
        output_path = os.path.join(self.output_dir, f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}")
        
        cmd = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def remove_audio(self, video_path: str) -> str:
        """Tool 12: Remove audio track"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-an', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_audio(self, video_path: str, audio_path: str, volume: float = 1.0) -> str:
        """Tool 13: Add audio track to video"""
        if not MOVIEPY_AVAILABLE:
            return self._add_audio_ffmpeg(video_path, audio_path, volume)
        
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # Loop audio if needed
            if audio.duration < video.duration:
                audio = audio.loop(duration=video.duration)
            else:
                audio = audio.subclip(0, video.duration)
            
            audio = audio.volumex(volume)
            
            # Mix with original audio if exists
            if video.audio:
                final_audio = CompositeAudioClip([video.audio, audio])
            else:
                final_audio = audio
            
            final = video.set_audio(final_audio)
            output_path = self.generate_filename()
            final.write_videofile(output_path, logger=None, verbose=False)
            
            video.close()
            audio.close()
            final.close()
            return output_path
        except Exception as e:
            logger.error(f"Add audio error: {e}")
            raise
    
    def _add_audio_ffmpeg(self, video_path: str, audio_path: str, volume: float) -> str:
        """Add audio using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-i', audio_path, '-filter_complex', 
               f'[1:a]volume={volume}[a];[0:a][a]amix=inputs=2:duration=first', 
               '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def adjust_volume(self, video_path: str, factor: float) -> str:
        """Tool 14: Adjust video volume"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-filter:a', f'volume={factor}', '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def audio_fade(self, video_path: str, fade_in: float = 1.0, fade_out: float = 1.0) -> str:
        """Tool 15: Audio fade in/out"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-filter:a', f'afade=t=in:ss=0:d={fade_in},afade=t=out:st={fade_out}:d={fade_in}', 
               '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_background_music(self, video_path: str, music_path: str, music_volume: float = 0.3) -> str:
        """Tool 16: Add background music"""
        return self.add_audio(video_path, music_path, music_volume)
    
    def voiceover(self, video_path: str, voice_path: str, reduce_original: float = 0.3) -> str:
        """Tool 17: Add voiceover"""
        return self.add_audio(video_path, voice_path, reduce_original)
    
    def normalize_audio(self, video_path: str) -> str:
        """Tool 18: Normalize audio volume"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-filter:a', 'loudnorm', '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def noise_reduction(self, video_path: str) -> str:
        """Tool 19: Reduce background noise"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-filter:a', 'afftdn=nf=-25', '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def equalizer(self, video_path: str, frequencies: List[float]) -> str:
        """Tool 20: Audio equalizer"""
        output_path = self.generate_filename()
        # Simple 3-band equalizer
        filter_str = f'equalizer=f={frequencies[0]}:width=100:g=5,equalizer=f={frequencies[1]}:width=100:g=0,equalizer=f={frequencies[2]}:width=100:g=-5'
        cmd = ['ffmpeg', '-i', video_path, '-filter:a', filter_str, '-c:v', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    # ============================================
    # VIDEO EFFECTS (21-35)
    # ============================================
    
    def fade_in(self, video_path: str, duration: float = 1.0) -> str:
        """Tool 21: Fade in effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'fade=t=in:st=0:d={duration}', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def fade_out(self, video_path: str, duration: float = 1.0) -> str:
        """Tool 22: Fade out effect"""
        output_path = self.generate_filename()
        clip = VideoFileClip(video_path)
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'fade=t=out:st={clip.duration - duration}:d={duration}', '-y', output_path]
        clip.close()
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def glitch_effect(self, video_path: str, intensity: int = 5) -> str:
        """Tool 23: Glitch effect"""
        output_path = self.generate_filename()
        
        # Apply glitch effect using ffmpeg with multiple filters
        cmd = ['ffmpeg', '-i', video_path, 
               '-vf', f'noise=alls={intensity}:allf=t,chromashift=crh={intensity}:crv={intensity}',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def pixelate_effect(self, video_path: str, block_size: int = 10) -> str:
        """Tool 24: Pixelate effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'pixelize=block={block_size}', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def grayscale(self, video_path: str) -> str:
        """Tool 25: Grayscale/Black & White effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', 'colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def sepia(self, video_path: str) -> str:
        """Tool 26: Sepia effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def blur(self, video_path: str, radius: int = 5) -> str:
        """Tool 27: Blur effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'gblur=sigma={radius}', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def sharpen(self, video_path: str) -> str:
        """Tool 28: Sharpen effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-vf', 'unsharp=5:5:1.0:5:5:0.0', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def vintage(self, video_path: str) -> str:
        """Tool 29: Vintage effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, 
               '-vf', 'colorbalance=rs=.1:gs=.1:bs=.1,curves=vintage,colorchannelmixer=.8:.2:.1:0:.1:.8:.1:0:.1:.2:.8',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def vhs_effect(self, video_path: str) -> str:
        """Tool 30: VHS effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', 'noise=alls=20:allf=t,chromashift=cr=5,cb=5,eq=saturation=1.5',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def cinematic(self, video_path: str) -> str:
        """Tool 31: Cinematic effect (add black bars)"""
        output_path = self.generate_filename()
        
        clip = VideoFileClip(video_path)
        target_ratio = 2.35  # Cinematic aspect ratio
        current_ratio = clip.w / clip.h
        
        if current_ratio > target_ratio:
            new_height = int(clip.w / target_ratio)
            bar_height = (new_height - clip.h) // 2
            cmd = ['ffmpeg', '-i', video_path, '-vf', f'pad=width={clip.w}:height={new_height}:x=0:y={bar_height}:color=black', '-y', output_path]
        else:
            new_width = int(clip.h * target_ratio)
            bar_width = (new_width - clip.w) // 2
            cmd = ['ffmpeg', '-i', video_path, '-vf', f'pad=width={new_width}:height={clip.h}:x={bar_width}:y=0:color=black', '-y', output_path]
        
        clip.close()
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def neon_effect(self, video_path: str) -> str:
        """Tool 32: Neon effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', 'edgedetect=low=0.1:high=0.3,colorbalance=rs=1:gs=0:bs=1',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def cartoon_effect(self, video_path: str) -> str:
        """Tool 33: Cartoon effect"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', 'edgedetect,colorbalance=rs=1.2:gs=1.2:bs=1.2',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def slow_motion(self, video_path: str, factor: float = 0.5) -> str:
        """Tool 34: Slow motion effect"""
        return self.speed(video_path, factor)
    
    def fast_motion(self, video_path: str, factor: float = 2.0) -> str:
        """Tool 35: Fast motion effect"""
        return self.speed(video_path, factor)
    
    # ============================================
    # TRANSITIONS (36-40)
    # ============================================
    
    def crossfade_transition(self, video1_path: str, video2_path: str, duration: float = 1.0) -> str:
        """Tool 36: Crossfade transition between videos"""
        if not MOVIEPY_AVAILABLE:
            return self._crossfade_ffmpeg(video1_path, video2_path, duration)
        
        try:
            v1 = VideoFileClip(video1_path)
            v2 = VideoFileClip(video2_path)
            
            # Crossfade effect
            v2 = v2.crossfadein(duration)
            merged = concatenate_videoclips([v1, v2])
            
            output_path = self.generate_filename()
            merged.write_videofile(output_path, logger=None, verbose=False)
            
            v1.close()
            v2.close()
            merged.close()
            return output_path
        except Exception as e:
            logger.error(f"Crossfade error: {e}")
            raise
    
    def _crossfade_ffmpeg(self, video1_path: str, video2_path: str, duration: float) -> str:
        """Crossfade using ffmpeg"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video1_path, '-i', video2_path,
               '-filter_complex', f'[0:v][1:v]xfade=transition=fade:duration={duration}:offset=({duration})',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def slide_transition(self, video1_path: str, video2_path: str, direction: str = "right") -> str:
        """Tool 37: Slide transition"""
        output_path = self.generate_filename()
        transition_map = {
            'right': 'slide',
            'left': 'slideleft',
            'up': 'slideup',
            'down': 'slidedown'
        }
        transition = transition_map.get(direction, 'slide')
        
        cmd = ['ffmpeg', '-i', video1_path, '-i', video2_path,
               '-filter_complex', f'[0:v][1:v]xfade=transition={transition}:duration=1:offset=4',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def wipe_transition(self, video1_path: str, video2_path: str) -> str:
        """Tool 38: Wipe transition"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video1_path, '-i', video2_path,
               '-filter_complex', '[0:v][1:v]xfade=transition=wipe:duration=1:offset=4',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def zoom_transition(self, video1_path: str, video2_path: str) -> str:
        """Tool 39: Zoom transition"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video1_path, '-i', video2_path,
               '-filter_complex', '[0:v]zoompan=z=2:d=25[f];[f][1:v]xfade=transition=fade:duration=1:offset=24',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    # ============================================
    # ADVANCED FEATURES (41-50)
    # ============================================
    
    def picture_in_picture(self, background: str, overlay: str, position: str = "bottom-right", size: float = 0.3) -> str:
        """Tool 40: Picture in Picture effect"""
        if not MOVIEPY_AVAILABLE:
            return self._pip_ffmpeg(background, overlay, position, size)
        
        try:
            bg = VideoFileClip(background)
            ov = VideoFileClip(overlay).resize(size)
            
            positions = {
                "top-left": (10, 10),
                "top-right": (bg.w - ov.w - 10, 10),
                "bottom-left": (10, bg.h - ov.h - 10),
                "bottom-right": (bg.w - ov.w - 10, bg.h - ov.h - 10),
                "center": ((bg.w - ov.w) // 2, (bg.h - ov.h) // 2)
            }
            
            pos = positions.get(position, positions["bottom-right"])
            combined = CompositeVideoClip([bg, ov.set_position(pos)])
            
            output_path = self.generate_filename()
            combined.write_videofile(output_path, logger=None, verbose=False)
            
            bg.close()
            ov.close()
            combined.close()
            return output_path
        except Exception as e:
            logger.error(f"PIP error: {e}")
            raise
    
    def _pip_ffmpeg(self, background: str, overlay: str, position: str, size: float) -> str:
        """Picture in Picture using ffmpeg"""
        output_path = self.generate_filename()
        
        position_map = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2"
        }
        
        pos = position_map.get(position, position_map["bottom-right"])
        
        cmd = ['ffmpeg', '-i', background, '-i', overlay,
               '-filter_complex', f'[1:v]scale=iw*{size}:ih*{size}[ov];[0:v][ov]overlay={pos}',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def split_screen(self, video_paths: List[str], layout: str = "2x2") -> str:
        """Tool 41: Split screen effect"""
        output_path = self.generate_filename()
        
        if layout == "2x2" and len(video_paths) >= 4:
            cmd = ['ffmpeg', '-i', video_paths[0], '-i', video_paths[1], '-i', video_paths[2], '-i', video_paths[3],
                   '-filter_complex', 
                   '[0:v]scale=iw/2:ih/2[v0];[1:v]scale=iw/2:ih/2[v1];[2:v]scale=iw/2:ih/2[v2];[3:v]scale=iw/2:ih/2[v3];'
                   '[v0][v1]hstack[top];[v2][v3]hstack[bottom];[top][bottom]vstack',
                   '-y', output_path]
        else:
            # Horizontal split
            cmd = ['ffmpeg'] + sum([['-i', p] for p in video_paths[:2]], [])
            cmd += ['-filter_complex', f'[0:v][1:v]hstack=inputs={len(video_paths[:2])}', '-y', output_path]
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def chroma_key(self, video_path: str, color: str = "green", similarity: float = 0.3) -> str:
        """Tool 42: Chroma key / Green screen effect"""
        output_path = self.generate_filename()
        
        color_map = {
            "green": "0x00FF00",
            "blue": "0x0000FF",
            "red": "0xFF0000"
        }
        chroma_color = color_map.get(color, "0x00FF00")
        
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', f'chromakey={chroma_color}:{similarity}:0.1',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_watermark(self, video_path: str, text: str, position: str = "bottom-right", opacity: float = 0.7) -> str:
        """Tool 43: Add text watermark"""
        output_path = self.generate_filename()
        
        position_map = {
            "top-left": "10:10",
            "top-right": "W-tw-10:10",
            "bottom-left": "10:H-th-10",
            "bottom-right": "W-tw-10:H-th-10"
        }
        
        pos = position_map.get(position, position_map["bottom-right"])
        
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize=24:alpha={opacity}:x={pos.split(':')[0]}:y={pos.split(':')[1]}",
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_text_overlay(self, video_path: str, text: str, duration: float = 3.0, font_size: int = 30) -> str:
        """Tool 44: Add text overlay"""
        output_path = self.generate_filename()
        
        cmd = ['ffmpeg', '-i', video_path,
               '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize={font_size}:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,{duration})'",
               '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def compress(self, video_path: str, target_size_mb: int = 20) -> str:
        """Tool 45: Compress video to target size"""
        output_path = self.generate_filename()
        
        # Calculate bitrate based on target size
        clip = VideoFileClip(video_path)
        duration = clip.duration
        target_bitrate = (target_size_mb * 8) / duration
        clip.close()
        
        cmd = ['ffmpeg', '-i', video_path, '-b:v', f'{int(target_bitrate)}k', '-b:a', '128k', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def to_4k(self, video_path: str) -> str:
        """Tool 46: Convert to 4K resolution"""
        return self.resize(video_path, 3840, 2160)
    
    def to_1080p(self, video_path: str) -> str:
        """Tool 47: Convert to 1080p resolution"""
        return self.resize(video_path, 1920, 1080)
    
    def to_720p(self, video_path: str) -> str:
        """Tool 48: Convert to 720p resolution"""
        return self.resize(video_path, 1280, 720)
    
    def optimize(self, video_path: str) -> str:
        """Tool 49: Optimize for web streaming"""
        output_path = self.generate_filename()
        cmd = ['ffmpeg', '-i', video_path, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', 
               '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def extract_frames(self, video_path: str, interval: int = 1) -> List[str]:
        """Tool 50: Extract frames from video"""
        output_dir = os.path.join(self.output_dir, f"frames_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = ['ffmpeg', '-i', video_path, '-vf', f'fps=1/{interval}', f'{output_dir}/frame_%04d.jpg']
        subprocess.run(cmd, capture_output=True)
        
        frames = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.jpg')])
        return frames
    
    def create_gif(self, video_path: str, start_time: float, duration: float, width: int = 480) -> str:
        """Tool 51: Create GIF from video"""
        output_path = os.path.join(self.output_dir, f"gif_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif")
        
        cmd = ['ffmpeg', '-ss', str(start_time), '-t', str(duration), '-i', video_path,
               '-vf', f'fps=10,scale={width}:-1:flags=lanczos', '-y', output_path]
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def stabilize(self, video_path: str) -> str:
        """Tool 52: Video stabilization"""
        output_path = self.generate_filename()
        
        # First pass: detect motion
        transforms_file = os.path.join(self.temp_dir, "transforms.trf")
        cmd1 = ['ffmpeg', '-i', video_path, '-vf', 'vidstabdetect=shakiness=5:accuracy=15:result=' + transforms_file, '-f', 'null', '-']
        subprocess.run(cmd1, capture_output=True)
        
        # Second pass: apply stabilization
        cmd2 = ['ffmpeg', '-i', video_path, '-vf', f'vidstabtransform=input={transforms_file}:zoom=0:optzoom=1', '-y', output_path]
        subprocess.run(cmd2, capture_output=True)
        
        os.remove(transforms_file)
        return output_path
    
    def apply_filter(self, video_path: str, filter_name: str) -> str:
        """Apply filter to video"""
        filters = {
            'grayscale': self.grayscale,
            'sepia': self.sepia,
            'blur': lambda p: self.blur(p, 5),
            'sharpen': self.sharpen,
            'vintage': self.vintage,
            'vhs': self.vhs_effect,
            'cinematic': self.cinematic,
            'neon': self.neon_effect,
            'cartoon': self.cartoon_effect,
            'glitch': lambda p: self.glitch_effect(p, 5),
            'pixelate': lambda p: self.pixelate_effect(p, 10)
        }
        
        if filter_name in filters:
            return filters[filter_name](video_path)
        else:
            raise ValueError(f"Filter {filter_name} not found")


# ============================================
# INITIALIZE VIDEO EDITOR
# ============================================

video_editor = VideoEditor()
