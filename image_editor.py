# ============================================
# IMAGE_EDITOR.PY - COMPLETE IMAGE EDITING TOOLS
# KINVA MASTER PRO - 30+ IMAGE EDITING FEATURES
# ============================================

import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import logging
import random
import io
import requests

from config import Config

logger = logging.getLogger(__name__)


class ImageEditor:
    """Complete Image Editing Class with 30+ Tools"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        self.output_dir = Config.OUTPUT_DIR
        
    def generate_filename(self, extension: str = ".png") -> str:
        """Generate unique filename for output"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_num = random.randint(1000, 9999)
        return os.path.join(self.output_dir, f"image_{timestamp}_{random_num}{extension}")
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get image information"""
        try:
            img = Image.open(image_path)
            info = {
                'width': img.width,
                'height': img.height,
                'size': f"{img.width}x{img.height}",
                'format': img.format,
                'mode': img.mode,
                'size_mb': os.path.getsize(image_path) / (1024 * 1024),
                'aspect_ratio': round(img.width / img.height, 2)
            }
            img.close()
            return info
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {'width': 0, 'height': 0, 'size': '0x0', 'format': 'Unknown', 'mode': 'Unknown', 'size_mb': 0, 'aspect_ratio': 0}
    
    # ============================================
    # BASIC EDITING TOOLS (1-10)
    # ============================================
    
    def resize(self, image_path: str, width: int = None, height: int = None, maintain_ratio: bool = True) -> str:
        """Tool 1: Resize image"""
        try:
            img = Image.open(image_path)
            
            if maintain_ratio and width and height:
                # Calculate new dimensions maintaining aspect ratio
                ratio = min(width / img.width, height / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
            elif width:
                ratio = width / img.width
                new_width = width
                new_height = int(img.height * ratio)
            elif height:
                ratio = height / img.height
                new_height = height
                new_width = int(img.width * ratio)
            else:
                new_width, new_height = img.width, img.height
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            output_path = self.generate_filename()
            resized.save(output_path, quality=95)
            
            img.close()
            resized.close()
            return output_path
        except Exception as e:
            logger.error(f"Resize error: {e}")
            raise
    
    def crop(self, image_path: str, x1: int, y1: int, x2: int, y2: int) -> str:
        """Tool 2: Crop image"""
        try:
            img = Image.open(image_path)
            cropped = img.crop((x1, y1, x2, y2))
            output_path = self.generate_filename()
            cropped.save(output_path, quality=95)
            
            img.close()
            cropped.close()
            return output_path
        except Exception as e:
            logger.error(f"Crop error: {e}")
            raise
    
    def rotate(self, image_path: str, angle: float, expand: bool = True) -> str:
        """Tool 3: Rotate image"""
        try:
            img = Image.open(image_path)
            rotated = img.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)
            output_path = self.generate_filename()
            rotated.save(output_path, quality=95)
            
            img.close()
            rotated.close()
            return output_path
        except Exception as e:
            logger.error(f"Rotate error: {e}")
            raise
    
    def flip_horizontal(self, image_path: str) -> str:
        """Tool 4: Flip image horizontally"""
        try:
            img = Image.open(image_path)
            flipped = ImageOps.mirror(img)
            output_path = self.generate_filename()
            flipped.save(output_path, quality=95)
            
            img.close()
            flipped.close()
            return output_path
        except Exception as e:
            logger.error(f"Flip horizontal error: {e}")
            raise
    
    def flip_vertical(self, image_path: str) -> str:
        """Tool 5: Flip image vertically"""
        try:
            img = Image.open(image_path)
            flipped = ImageOps.flip(img)
            output_path = self.generate_filename()
            flipped.save(output_path, quality=95)
            
            img.close()
            flipped.close()
            return output_path
        except Exception as e:
            logger.error(f"Flip vertical error: {e}")
            raise
    
    def adjust_brightness(self, image_path: str, factor: float) -> str:
        """Tool 6: Adjust brightness (0.5 to 2.0)"""
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Brightness(img)
            adjusted = enhancer.enhance(factor)
            output_path = self.generate_filename()
            adjusted.save(output_path, quality=95)
            
            img.close()
            adjusted.close()
            return output_path
        except Exception as e:
            logger.error(f"Brightness adjustment error: {e}")
            raise
    
    def adjust_contrast(self, image_path: str, factor: float) -> str:
        """Tool 7: Adjust contrast (0.5 to 2.0)"""
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Contrast(img)
            adjusted = enhancer.enhance(factor)
            output_path = self.generate_filename()
            adjusted.save(output_path, quality=95)
            
            img.close()
            adjusted.close()
            return output_path
        except Exception as e:
            logger.error(f"Contrast adjustment error: {e}")
            raise
    
    def adjust_saturation(self, image_path: str, factor: float) -> str:
        """Tool 8: Adjust saturation (0.5 to 2.0)"""
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Color(img)
            adjusted = enhancer.enhance(factor)
            output_path = self.generate_filename()
            adjusted.save(output_path, quality=95)
            
            img.close()
            adjusted.close()
            return output_path
        except Exception as e:
            logger.error(f"Saturation adjustment error: {e}")
            raise
    
    def adjust_sharpness(self, image_path: str, factor: float) -> str:
        """Tool 9: Adjust sharpness (0.5 to 2.0)"""
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Sharpness(img)
            adjusted = enhancer.enhance(factor)
            output_path = self.generate_filename()
            adjusted.save(output_path, quality=95)
            
            img.close()
            adjusted.close()
            return output_path
        except Exception as e:
            logger.error(f"Sharpness adjustment error: {e}")
            raise
    
    def blur(self, image_path: str, radius: int = 2) -> str:
        """Tool 10: Apply blur effect"""
        try:
            img = Image.open(image_path)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
            output_path = self.generate_filename()
            blurred.save(output_path, quality=95)
            
            img.close()
            blurred.close()
            return output_path
        except Exception as e:
            logger.error(f"Blur error: {e}")
            raise
    
    # ============================================
    # ADVANCED EDITING TOOLS (11-20)
    # ============================================
    
    def add_text(self, image_path: str, text: str, position: Tuple[int, int] = (10, 10), 
                 font_size: int = 30, color: str = "white", outline: bool = True) -> str:
        """Tool 11: Add text overlay to image"""
        try:
            img = Image.open(image_path).convert('RGBA')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Add outline for better visibility
            if outline:
                draw.text((position[0]-1, position[1]-1), text, fill="black", font=font)
                draw.text((position[0]+1, position[1]-1), text, fill="black", font=font)
                draw.text((position[0]-1, position[1]+1), text, fill="black", font=font)
                draw.text((position[0]+1, position[1]+1), text, fill="black", font=font)
            
            draw.text(position, text, fill=color, font=font)
            
            output_path = self.generate_filename()
            img.save(output_path, quality=95)
            
            img.close()
            return output_path
        except Exception as e:
            logger.error(f"Add text error: {e}")
            raise
    
    def add_watermark(self, image_path: str, text: str, position: str = "bottom-right", 
                      opacity: float = 0.5, font_size: int = 20) -> str:
        """Tool 12: Add watermark to image"""
        try:
            img = Image.open(image_path).convert('RGBA')
            
            # Create watermark layer
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size and position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            position_map = {
                "top-left": (10, 10),
                "top-right": (img.width - text_width - 10, 10),
                "bottom-left": (10, img.height - text_height - 10),
                "bottom-right": (img.width - text_width - 10, img.height - text_height - 10),
                "center": ((img.width - text_width) // 2, (img.height - text_height) // 2)
            }
            
            pos = position_map.get(position, position_map["bottom-right"])
            
            # Draw watermark with opacity
            draw.text(pos, text, fill=(255, 255, 255, int(255 * opacity)), font=font)
            
            # Composite watermark with original
            watermarked = Image.alpha_composite(img, watermark)
            watermarked = watermarked.convert('RGB')
            
            output_path = self.generate_filename()
            watermarked.save(output_path, quality=95)
            
            img.close()
            watermarked.close()
            return output_path
        except Exception as e:
            logger.error(f"Watermark error: {e}")
            raise
    
    def remove_background(self, image_path: str) -> str:
        """Tool 13: Remove background using rembg (if available) or basic method"""
        try:
            # Try using rembg if available
            try:
                from rembg import remove
                img = Image.open(image_path)
                removed = remove(img)
                output_path = self.generate_filename()
                removed.save(output_path)
                return output_path
            except ImportError:
                # Fallback to basic background removal using OpenCV
                return self._basic_background_removal(image_path)
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            raise
    
    def _basic_background_removal(self, image_path: str) -> str:
        """Basic background removal using OpenCV (simple version)"""
        img = cv2.imread(image_path)
        
        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reshape to 1D array
        pixels = img_rgb.reshape((-1, 3))
        
        # Apply k-means clustering for segmentation
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pixels)
        
        # Create mask
        mask = labels.reshape(img.shape[:2])
        
        # Apply mask
        result = img_rgb.copy()
        result[mask == 0] = [0, 255, 0]  # Green background
        
        output_path = self.generate_filename()
        cv2.imwrite(output_path, cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        return output_path
    
    def compress(self, image_path: str, quality: int = 85) -> str:
        """Tool 14: Compress image"""
        try:
            img = Image.open(image_path)
            output_path = self.generate_filename()
            
            # Save with reduced quality
            img.save(output_path, quality=quality, optimize=True)
            
            img.close()
            return output_path
        except Exception as e:
            logger.error(f"Compress error: {e}")
            raise
    
    def convert_format(self, image_path: str, target_format: str) -> str:
        """Tool 15: Convert image format (jpg, png, webp, bmp)"""
        try:
            img = Image.open(image_path)
            
            # Convert RGBA to RGB for JPEG
            if target_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            output_path = self.generate_filename(f".{target_format.lower()}")
            img.save(output_path, quality=95)
            
            img.close()
            return output_path
        except Exception as e:
            logger.error(f"Convert format error: {e}")
            raise
    
    def auto_enhance(self, image_path: str) -> str:
        """Tool 16: Auto enhance image (brightness + contrast + color)"""
        try:
            img = Image.open(image_path)
            
            # Auto contrast
            img = ImageOps.autocontrast(img)
            
            # Enhance color
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            output_path = self.generate_filename()
            img.save(output_path, quality=95)
            
            img.close()
            return output_path
        except Exception as e:
            logger.error(f"Auto enhance error: {e}")
            raise
    
    def red_eye_removal(self, image_path: str) -> str:
        """Tool 17: Remove red eye effect"""
        try:
            img = Image.open(image_path)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Detect red pixels (simple method)
            red_channel = img_array[:, :, 0]
            green_channel = img_array[:, :, 1]
            blue_channel = img_array[:, :, 2]
            
            # Find red-eye pixels
            red_eye_mask = (red_channel > 150) & (green_channel < 100) & (blue_channel < 100)
            
            # Replace with dark color
            img_array[red_eye_mask] = [50, 50, 50]
            
            result = Image.fromarray(img_array)
            output_path = self.generate_filename()
            result.save(output_path, quality=95)
            
            img.close()
            result.close()
            return output_path
        except Exception as e:
            logger.error(f"Red eye removal error: {e}")
            raise
    
    def resize_canvas(self, image_path: str, width: int, height: int, 
                      background_color: str = "white", position: str = "center") -> str:
        """Tool 18: Resize canvas (add padding)"""
        try:
            img = Image.open(image_path)
            
            # Create new canvas
            canvas = Image.new(img.mode, (width, height), background_color)
            
            # Calculate paste position
            position_map = {
                "top-left": (0, 0),
                "top-right": (width - img.width, 0),
                "bottom-left": (0, height - img.height),
                "bottom-right": (width - img.width, height - img.height),
                "center": ((width - img.width) // 2, (height - img.height) // 2)
            }
            
            pos = position_map.get(position, position_map["center"])
            canvas.paste(img, pos)
            
            output_path = self.generate_filename()
            canvas.save(output_path, quality=95)
            
            img.close()
            canvas.close()
            return output_path
        except Exception as e:
            logger.error(f"Resize canvas error: {e}")
            raise
    
    def create_collage(self, image_paths: List[str], layout: str = "grid", 
                       cols: int = 2, spacing: int = 10) -> str:
        """Tool 19: Create collage from multiple images"""
        try:
            images = [Image.open(path) for path in image_paths]
            
            if layout == "grid":
                # Calculate grid dimensions
                rows = (len(images) + cols - 1) // cols
                
                # Resize all images to same size
                max_width = max(img.width for img in images)
                max_height = max(img.height for img in images)
                
                resized_images = []
                for img in images:
                    ratio = min(max_width / img.width, max_height / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Create square canvas
                    square = Image.new('RGB', (max_width, max_height), (255, 255, 255))
                    x = (max_width - new_width) // 2
                    y = (max_height - new_height) // 2
                    square.paste(resized, (x, y))
                    resized_images.append(square)
                
                # Create collage
                collage_width = cols * max_width + (cols - 1) * spacing
                collage_height = rows * max_height + (rows - 1) * spacing
                collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))
                
                for idx, img in enumerate(resized_images):
                    row = idx // cols
                    col = idx % cols
                    x = col * (max_width + spacing)
                    y = row * (max_height + spacing)
                    collage.paste(img, (x, y))
                
                output_path = self.generate_filename()
                collage.save(output_path, quality=95)
                
            else:
                # Horizontal layout
                total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
                max_height = max(img.height for img in images)
                collage = Image.new('RGB', (total_width, max_height), (255, 255, 255))
                
                x = 0
                for img in images:
                    collage.paste(img, (x, 0))
                    x += img.width + spacing
                
                output_path = self.generate_filename()
                collage.save(output_path, quality=95)
            
            for img in images:
                img.close()
            
            return output_path
        except Exception as e:
            logger.error(f"Collage error: {e}")
            raise
    
    def apply_filter(self, image_path: str, filter_name: str) -> str:
        """Tool 20: Apply filter to image"""
        filters = {
            'grayscale': self.grayscale,
            'sepia': self.sepia,
            'invert': self.invert,
            'emboss': self.emboss,
            'sharpen': self.sharpen,
            'blur': lambda p: self.blur(p, 2),
            'smooth': self.smooth,
            'edge_enhance': self.edge_enhance,
            'contour': self.contour,
            'detail': self.detail
        }
        
        if filter_name in filters:
            return filters[filter_name](image_path)
        else:
            raise ValueError(f"Filter {filter_name} not found")
    
    # ============================================
    # FILTER EFFECTS (21-30)
    # ============================================
    
    def grayscale(self, image_path: str) -> str:
        """Convert to grayscale"""
        try:
            img = Image.open(image_path)
            grayscale = img.convert('L').convert('RGB')
            output_path = self.generate_filename()
            grayscale.save(output_path, quality=95)
            
            img.close()
            grayscale.close()
            return output_path
        except Exception as e:
            logger.error(f"Grayscale error: {e}")
            raise
    
    def sepia(self, image_path: str) -> str:
        """Apply sepia filter"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Sepia transformation matrix
            sepia_matrix = np.array([[0.393, 0.769, 0.189],
                                      [0.349, 0.686, 0.168],
                                      [0.272, 0.534, 0.131]])
            
            sepia = img_array @ sepia_matrix.T
            sepia = np.clip(sepia, 0, 255).astype('uint8')
            
            result = Image.fromarray(sepia)
            output_path = self.generate_filename()
            result.save(output_path, quality=95)
            
            img.close()
            result.close()
            return output_path
        except Exception as e:
            logger.error(f"Sepia error: {e}")
            raise
    
    def invert(self, image_path: str) -> str:
        """Invert colors"""
        try:
            img = Image.open(image_path)
            inverted = ImageOps.invert(img.convert('RGB'))
            output_path = self.generate_filename()
            inverted.save(output_path, quality=95)
            
            img.close()
            inverted.close()
            return output_path
        except Exception as e:
            logger.error(f"Invert error: {e}")
            raise
    
    def emboss(self, image_path: str) -> str:
        """Apply emboss filter"""
        try:
            img = Image.open(image_path)
            embossed = img.filter(ImageFilter.EMBOSS)
            output_path = self.generate_filename()
            embossed.save(output_path, quality=95)
            
            img.close()
            embossed.close()
            return output_path
        except Exception as e:
            logger.error(f"Emboss error: {e}")
            raise
    
    def sharpen(self, image_path: str) -> str:
        """Apply sharpen filter"""
        try:
            img = Image.open(image_path)
            sharpened = img.filter(ImageFilter.SHARPEN)
            output_path = self.generate_filename()
            sharpened.save(output_path, quality=95)
            
            img.close()
            sharpened.close()
            return output_path
        except Exception as e:
            logger.error(f"Sharpen error: {e}")
            raise
    
    def smooth(self, image_path: str) -> str:
        """Apply smooth filter"""
        try:
            img = Image.open(image_path)
            smoothed = img.filter(ImageFilter.SMOOTH)
            output_path = self.generate_filename()
            smoothed.save(output_path, quality=95)
            
            img.close()
            smoothed.close()
            return output_path
        except Exception as e:
            logger.error(f"Smooth error: {e}")
            raise
    
    def edge_enhance(self, image_path: str) -> str:
        """Apply edge enhance filter"""
        try:
            img = Image.open(image_path)
            enhanced = img.filter(ImageFilter.EDGE_ENHANCE)
            output_path = self.generate_filename()
            enhanced.save(output_path, quality=95)
            
            img.close()
            enhanced.close()
            return output_path
        except Exception as e:
            logger.error(f"Edge enhance error: {e}")
            raise
    
    def contour(self, image_path: str) -> str:
        """Apply contour filter"""
        try:
            img = Image.open(image_path)
            contoured = img.filter(ImageFilter.CONTOUR)
            output_path = self.generate_filename()
            contoured.save(output_path, quality=95)
            
            img.close()
            contoured.close()
            return output_path
        except Exception as e:
            logger.error(f"Contour error: {e}")
            raise
    
    def detail(self, image_path: str) -> str:
        """Apply detail filter"""
        try:
            img = Image.open(image_path)
            detailed = img.filter(ImageFilter.DETAIL)
            output_path = self.generate_filename()
            detailed.save(output_path, quality=95)
            
            img.close()
            detailed.close()
            return output_path
        except Exception as e:
            logger.error(f"Detail error: {e}")
            raise
    
    def oil_paint(self, image_path: str, radius: int = 5, intensity: int = 30) -> str:
        """Apply oil painting effect"""
        try:
            img = cv2.imread(image_path)
            
            # Apply oil painting effect using OpenCV
            try:
                # OpenCV's xphoto module
                oil = cv2.xphoto.oilPainting(img, radius, intensity)
            except:
                # Alternative method: apply bilateral filter and median blur
                oil = cv2.bilateralFilter(img, radius * 2, intensity, intensity)
                oil = cv2.medianBlur(oil, radius)
            
            output_path = self.generate_filename()
            cv2.imwrite(output_path, oil)
            return output_path
        except Exception as e:
            logger.error(f"Oil paint error: {e}")
            raise
    
    # ============================================
    # SPECIAL EFFECTS (31-35)
    # ============================================
    
    def watercolor(self, image_path: str) -> str:
        """Apply watercolor effect"""
        try:
            img = cv2.imread(image_path)
            
            # Apply stylization for watercolor effect
            watercolor = cv2.stylization(img, sigma_s=60, sigma_r=0.6)
            
            output_path = self.generate_filename()
            cv2.imwrite(output_path, watercolor)
            return output_path
        except Exception as e:
            logger.error(f"Watercolor error: {e}")
            raise
    
    def pencil_sketch(self, image_path: str) -> str:
        """Apply pencil sketch effect"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply pencil sketch effect
            sketch_gray, sketch_color = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
            
            output_path = self.generate_filename()
            cv2.imwrite(output_path, sketch_color)
            return output_path
        except Exception as e:
            logger.error(f"Pencil sketch error: {e}")
            raise
    
    def cartoon(self, image_path: str) -> str:
        """Apply cartoon effect"""
        try:
            img = cv2.imread(image_path)
            
            # Apply cartoon effect
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            
            color = cv2.bilateralFilter(img, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            
            output_path = self.generate_filename()
            cv2.imwrite(output_path, cartoon)
            return output_path
        except Exception as e:
            logger.error(f"Cartoon error: {e}")
            raise
    
    def pixelate(self, image_path: str, pixel_size: int = 10) -> str:
        """Apply pixelation effect"""
        try:
            img = Image.open(image_path)
            
            # Downsample and upsample for pixelation
            small = img.resize((img.width // pixel_size, img.height // pixel_size), Image.Resampling.NEAREST)
            pixelated = small.resize(img.size, Image.Resampling.NEAREST)
            
            output_path = self.generate_filename()
            pixelated.save(output_path, quality=95)
            
            img.close()
            pixelated.close()
            return output_path
        except Exception as e:
            logger.error(f"Pixelate error: {e}")
            raise
    
    def mosaic(self, image_path: str, block_size: int = 20) -> str:
        """Apply mosaic effect"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            h, w = img_array.shape[:2]
            
            for y in range(0, h, block_size):
                for x in range(0, w, block_size):
                    block = img_array[y:y+block_size, x:x+block_size]
                    if block.size > 0:
                        avg_color = np.mean(block, axis=(0, 1))
                        img_array[y:y+block_size, x:x+block_size] = avg_color
            
            mosaic = Image.fromarray(img_array.astype('uint8'))
            output_path = self.generate_filename()
            mosaic.save(output_path, quality=95)
            
            img.close()
            mosaic.close()
            return output_path
        except Exception as e:
            logger.error(f"Mosaic error: {e}")
            raise
    
    def vignette(self, image_path: str) -> str:
        """Apply vignette effect"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            h, w = img_array.shape[:2]
            
            # Create vignette mask
            X, Y = np.meshgrid(np.arange(w), np.arange(h))
            center_x, center_y = w // 2, h // 2
            dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
            radius = min(w, h) / 2
            mask = 1 - (dist / radius)
            mask = np.clip(mask, 0.3, 1)  # Darken edges but keep center bright
            
            # Apply mask
            for i in range(3):
                img_array[:, :, i] = (img_array[:, :, i] * mask).astype('uint8')
            
            vignetted = Image.fromarray(img_array)
            output_path = self.generate_filename()
            vignetted.save(output_path, quality=95)
            
            img.close()
            vignetted.close()
            return output_path
        except Exception as e:
            logger.error(f"Vignette error: {e}")
            raise
    
    def glow(self, image_path: str) -> str:
        """Apply glow effect"""
        try:
            img = Image.open(image_path)
            
            # Create blurred copy
            blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
            
            # Blend original with blurred
            glow = Image.blend(img, blurred, 0.5)
            
            output_path = self.generate_filename()
            glow.save(output_path, quality=95)
            
            img.close()
            glow.close()
            return output_path
        except Exception as e:
            logger.error(f"Glow error: {e}")
            raise


# ============================================
# INITIALIZE IMAGE EDITOR
# ============================================

image_editor = ImageEditor()
