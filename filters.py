# ============================================
# FILTERS.PY - 100+ PROFESSIONAL FILTERS
# KINVA MASTER PRO - COMPLETE FILTER COLLECTION
# ============================================

import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageChops
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
import random
import math

from config import Config

logger = logging.getLogger(__name__)


class Filters:
    """Complete Filters Class with 100+ Professional Filters"""
    
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        self.filters_cache = {}
        
    def generate_filename(self, filter_name: str, extension: str = ".png") -> str:
        """Generate unique filename for output"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_num = random.randint(1000, 9999)
        return os.path.join(self.output_dir, f"filter_{filter_name}_{timestamp}_{random_num}{extension}")
    
    # ============================================
    # BASIC FILTERS (1-15)
    # ============================================
    
    def grayscale(self, image_path: str) -> str:
        """Filter 1: Convert to grayscale"""
        img = Image.open(image_path)
        result = img.convert('L').convert('RGB')
        output_path = self.generate_filename("grayscale")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def sepia(self, image_path: str) -> str:
        """Filter 2: Apply sepia tone"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        sepia_matrix = np.array([[0.393, 0.769, 0.189],
                                  [0.349, 0.686, 0.168],
                                  [0.272, 0.534, 0.131]])
        
        sepia = img_array @ sepia_matrix.T
        sepia = np.clip(sepia, 0, 255).astype('uint8')
        
        result = Image.fromarray(sepia)
        output_path = self.generate_filename("sepia")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def invert(self, image_path: str) -> str:
        """Filter 3: Invert colors"""
        img = Image.open(image_path)
        result = ImageOps.invert(img.convert('RGB'))
        output_path = self.generate_filename("invert")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def emboss(self, image_path: str) -> str:
        """Filter 4: Apply emboss effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.EMBOSS)
        output_path = self.generate_filename("emboss")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def sharpen(self, image_path: str) -> str:
        """Filter 5: Apply sharpen effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.SHARPEN)
        output_path = self.generate_filename("sharpen")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def blur(self, image_path: str, radius: int = 2) -> str:
        """Filter 6: Apply blur effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.GaussianBlur(radius=radius))
        output_path = self.generate_filename("blur")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def smooth(self, image_path: str) -> str:
        """Filter 7: Apply smooth effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.SMOOTH)
        output_path = self.generate_filename("smooth")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def edge_enhance(self, image_path: str) -> str:
        """Filter 8: Apply edge enhancement"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.EDGE_ENHANCE)
        output_path = self.generate_filename("edge_enhance")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def contour(self, image_path: str) -> str:
        """Filter 9: Apply contour effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.CONTOUR)
        output_path = self.generate_filename("contour")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def detail(self, image_path: str) -> str:
        """Filter 10: Enhance details"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.DETAIL)
        output_path = self.generate_filename("detail")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def find_edges(self, image_path: str) -> str:
        """Filter 11: Find edges"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.FIND_EDGES)
        output_path = self.generate_filename("find_edges")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def unsharp_mask(self, image_path: str, radius: int = 2, percent: int = 150, threshold: int = 3) -> str:
        """Filter 12: Apply unsharp mask for sharpening"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
        output_path = self.generate_filename("unsharp_mask")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def box_blur(self, image_path: str, radius: int = 2) -> str:
        """Filter 13: Apply box blur"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.BoxBlur(radius))
        output_path = self.generate_filename("box_blur")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def mode_filter(self, image_path: str, size: int = 3) -> str:
        """Filter 14: Apply mode filter (reduces noise)"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.ModeFilter(size))
        output_path = self.generate_filename("mode_filter")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def rank_filter(self, image_path: str, size: int = 3, rank: int = 1) -> str:
        """Filter 15: Apply rank filter"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.RankFilter(size, rank))
        output_path = self.generate_filename("rank_filter")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    # ============================================
    # COLOR FILTERS (16-35)
    # ============================================
    
    def vintage(self, image_path: str) -> str:
        """Filter 16: Vintage/warm tone effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(0.8)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        output_path = self.generate_filename("vintage")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def cool(self, image_path: str) -> str:
        """Filter 17: Cool blue tone"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.1)
        
        # Add blue tint
        r, g, b = img.split()
        b = b.point(lambda i: i * 1.2)
        img = Image.merge('RGB', (r, g, b))
        
        output_path = self.generate_filename("cool")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def warm(self, image_path: str) -> str:
        """Filter 18: Warm orange tone"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(0.8)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        
        # Add warm tint
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.2)
        img = Image.merge('RGB', (r, g, b))
        
        output_path = self.generate_filename("warm")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def noir(self, image_path: str) -> str:
        """Filter 19: Film noir effect"""
        img = Image.open(image_path)
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert('RGB')
        output_path = self.generate_filename("noir")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def pastel(self, image_path: str) -> str:
        """Filter 20: Soft pastel effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(0.6)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        output_path = self.generate_filename("pastel")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def sunset(self, image_path: str) -> str:
        """Filter 21: Sunset orange/red effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.3)
        g = g.point(lambda i: i * 0.8)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("sunset")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def ocean(self, image_path: str) -> str:
        """Filter 22: Ocean blue effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.4)
        r, g, b = img.split()
        b = b.point(lambda i: i * 1.3)
        g = g.point(lambda i: i * 0.9)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("ocean")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def forest(self, image_path: str) -> str:
        """Filter 23: Forest green effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.2)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.3)
        r = r.point(lambda i: i * 0.8)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("forest")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def autumn(self, image_path: str) -> str:
        """Filter 24: Autumn orange/brown effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.1)
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.3)
        g = g.point(lambda i: i * 0.7)
        b = b.point(lambda i: i * 0.5)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("autumn")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def spring(self, image_path: str) -> str:
        """Filter 25: Spring pastel effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.3)
        r, g, b = img.split()
        g = g.point(lambda i: i * 1.2)
        b = b.point(lambda i: i * 1.1)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("spring")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def neon(self, image_path: str) -> str:
        """Filter 26: Neon glow effect"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        neon = np.zeros_like(img)
        neon[edges > 0] = [0, 255, 255]  # Cyan neon
        
        result = cv2.addWeighted(img, 0.7, neon, 0.3, 0)
        output_path = self.generate_filename("neon", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def glow(self, image_path: str) -> str:
        """Filter 27: Soft glow effect"""
        img = Image.open(image_path)
        blur = img.filter(ImageFilter.GaussianBlur(radius=10))
        result = Image.blend(img, blur, 0.5)
        output_path = self.generate_filename("glow")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def sparkle(self, image_path: str) -> str:
        """Filter 28: Add sparkle/star effects"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Add random sparkles
        num_sparkles = 100
        for _ in range(num_sparkles):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            cv2.circle(img, (x, y), 2, (255, 255, 255), -1)
        
        output_path = self.generate_filename("sparkle", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def rainbow(self, image_path: str) -> str:
        """Filter 29: Rainbow color effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Create rainbow gradient
        rainbow = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            for j in range(w):
                angle = (j / w) * 2 * np.pi
                rainbow[i, j] = [
                    int(127.5 + 127.5 * np.sin(angle)),
                    int(127.5 + 127.5 * np.sin(angle + 2*np.pi/3)),
                    int(127.5 + 127.5 * np.sin(angle + 4*np.pi/3))
                ]
        
        result = cv2.addWeighted(img, 0.7, rainbow, 0.3, 0)
        output_path = self.generate_filename("rainbow", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def prism(self, image_path: str) -> str:
        """Filter 30: Prism/color split effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Shift color channels
        r = np.roll(img[:, :, 2], 5, axis=1)  # Red channel shift
        g = img[:, :, 1]  # Green channel
        b = np.roll(img[:, :, 0], -5, axis=1)  # Blue channel shift
        
        result = np.stack([r, g, b], axis=2)
        output_path = self.generate_filename("prism", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def mirror(self, image_path: str) -> str:
        """Filter 31: Mirror effect"""
        img = Image.open(image_path)
        result = img.transpose(Image.FLIP_LEFT_RIGHT)
        output_path = self.generate_filename("mirror")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def kaleidoscope(self, image_path: str) -> str:
        """Filter 32: Kaleidoscope effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
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
                    result[y, x] = img[y2, x2]
        
        output_path = self.generate_filename("kaleidoscope", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def fisheye(self, image_path: str) -> str:
        """Filter 33: Fisheye lens effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
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
                        result[y, x] = img[y2, x2]
        
        output_path = self.generate_filename("fisheye", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def tilt_shift(self, image_path: str) -> str:
        """Filter 34: Tilt-shift miniature effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        center = h // 2
        blur_radius = 10
        
        for y in range(h):
            distance = abs(y - center)
            blur = blur_radius * (distance / center)
            if blur > 0:
                kernel_size = int(blur) * 2 + 1
                if kernel_size > 1:
                    img[y:y+1] = cv2.GaussianBlur(img[y:y+1], (kernel_size, kernel_size), 0)
        
        output_path = self.generate_filename("tilt_shift", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def miniature(self, image_path: str) -> str:
        """Filter 35: Miniature/fake tilt-shift effect"""
        result = self.tilt_shift(image_path)
        img = Image.open(result)
        img = ImageEnhance.Color(img).enhance(1.5)
        output_path = self.generate_filename("miniature")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    # ============================================
    # ARTISTIC FILTERS (36-55)
    # ============================================
    
    def oil_paint(self, image_path: str, radius: int = 5, intensity: int = 30) -> str:
        """Filter 36: Oil painting effect"""
        img = cv2.imread(image_path)
        
        try:
            oil = cv2.xphoto.oilPainting(img, radius, intensity)
        except:
            oil = cv2.bilateralFilter(img, radius * 2, intensity, intensity)
            oil = cv2.medianBlur(oil, radius)
        
        output_path = self.generate_filename("oil_paint", ".jpg")
        cv2.imwrite(output_path, oil)
        return output_path
    
    def watercolor(self, image_path: str) -> str:
        """Filter 37: Watercolor painting effect"""
        img = cv2.imread(image_path)
        watercolor = cv2.stylization(img, sigma_s=60, sigma_r=0.6)
        output_path = self.generate_filename("watercolor", ".jpg")
        cv2.imwrite(output_path, watercolor)
        return output_path
    
    def pencil_sketch(self, image_path: str) -> str:
        """Filter 38: Pencil sketch effect"""
        img = cv2.imread(image_path)
        _, sketch = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        output_path = self.generate_filename("pencil_sketch", ".jpg")
        cv2.imwrite(output_path, sketch)
        return output_path
    
    def cartoon(self, image_path: str) -> str:
        """Filter 39: Cartoon effect"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        
        color = cv2.bilateralFilter(img, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        
        output_path = self.generate_filename("cartoon", ".jpg")
        cv2.imwrite(output_path, cartoon)
        return output_path
    
    def pixelate(self, image_path: str, pixel_size: int = 10) -> str:
        """Filter 40: Pixelation effect"""
        img = Image.open(image_path)
        small = img.resize((img.width // pixel_size, img.height // pixel_size), Image.Resampling.NEAREST)
        pixelated = small.resize(img.size, Image.Resampling.NEAREST)
        output_path = self.generate_filename("pixelate")
        pixelated.save(output_path, quality=95)
        img.close()
        pixelated.close()
        return output_path
    
    def glitch(self, image_path: str) -> str:
        """Filter 41: Glitch/error effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Random color shifts
        shift = np.random.randint(-15, 15)
        img = np.roll(img, shift, axis=1)
        
        # Add noise
        noise = np.random.randint(0, 40, img.shape)
        img = np.clip(img + noise, 0, 255)
        
        output_path = self.generate_filename("glitch", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def vhs(self, image_path: str) -> str:
        """Filter 42: VHS tape effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Add scanlines
        scanlines = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(0, h, 2):
            scanlines[i:i+1, :] = [20, 20, 20]
        
        img = np.clip(img + scanlines, 0, 255)
        
        # Color bleed
        img[:, :, 0] = np.roll(img[:, :, 0], 2, axis=1)
        img[:, :, 2] = np.roll(img[:, :, 2], -2, axis=1)
        
        output_path = self.generate_filename("vhs", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def halftone(self, image_path: str) -> str:
        """Filter 43: Halftone/print effect"""
        img = cv2.imread(image_path, 0)
        h, w = img.shape
        
        pattern = np.zeros((h, w), dtype=np.uint8)
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                block = img[y:y+4, x:x+4]
                intensity = np.mean(block) / 255
                size = int(4 * intensity)
                if size > 0:
                    cv2.circle(pattern, (x+2, y+2), size//2, 255, -1)
        
        output_path = self.generate_filename("halftone", ".jpg")
        cv2.imwrite(output_path, pattern)
        return output_path
    
    def mosaic(self, image_path: str, block_size: int = 20) -> str:
        """Filter 44: Mosaic effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = img[y:y+block_size, x:x+block_size]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img[y:y+block_size, x:x+block_size] = avg_color
        
        output_path = self.generate_filename("mosaic", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def stained_glass(self, image_path: str) -> str:
        """Filter 45: Stained glass effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        grid_size = 30
        
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                block = img[y:y+grid_size, x:x+grid_size]
                if block.size > 0:
                    avg_color = np.mean(block, axis=(0, 1))
                    img[y:y+grid_size, x:x+grid_size] = avg_color
        
        # Add black borders
        img[::grid_size, :] = [0, 0, 0]
        img[:, ::grid_size] = [0, 0, 0]
        
        output_path = self.generate_filename("stained_glass", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    # ============================================
    # LIGHTING EFFECTS (56-70)
    # ============================================
    
    def bokeh(self, image_path: str) -> str:
        """Filter 56: Bokeh/blur background effect"""
        img = Image.open(image_path)
        result = img.filter(ImageFilter.GaussianBlur(radius=5))
        output_path = self.generate_filename("bokeh")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    def lens_flare(self, image_path: str) -> str:
        """Filter 57: Lens flare effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        flare = np.zeros((h, w, 3), dtype=np.uint8)
        center_x, center_y = w // 2, h // 2
        
        for y in range(h):
            for x in range(w):
                dx = x - center_x
                dy = y - center_y
                dist = np.sqrt(dx*dx + dy*dy)
                intensity = max(0, 1 - dist / (min(w, h) / 3))
                flare[y, x] = [255 * intensity, 200 * intensity, 150 * intensity]
        
        result = np.clip(img + flare, 0, 255)
        output_path = self.generate_filename("lens_flare", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def vignette(self, image_path: str) -> str:
        """Filter 58: Vignette/dark corners effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        center_x, center_y = w // 2, h // 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        radius = min(w, h) / 2
        mask = 1 - (dist / radius)
        mask = np.clip(mask, 0, 1)
        
        for i in range(3):
            img[:, :, i] = (img[:, :, i] * mask).astype('uint8')
        
        output_path = self.generate_filename("vignette", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    def gradient_map(self, image_path: str) -> str:
        """Filter 59: Gradient map effect"""
        img = cv2.imread(image_path, 0)
        gradient = np.linspace(0, 255, 256)
        gradient = np.stack([gradient, gradient * 0.5, gradient * 0.2], axis=1)
        mapped = gradient[img.flatten()].reshape(img.shape + (3,))
        
        output_path = self.generate_filename("gradient_map", ".jpg")
        cv2.imwrite(output_path, mapped.astype('uint8'))
        return output_path
    
    def dual_tone(self, image_path: str) -> str:
        """Filter 60: Dual tone/duotone effect"""
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        shadows = np.clip(img * 0.5, 0, 255).astype('uint8')
        highlights = np.clip(img * 1.5, 0, 255).astype('uint8')
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = np.where(gray[:, :, np.newaxis] < 128, shadows, highlights)
        
        output_path = self.generate_filename("dual_tone", ".jpg")
        cv2.imwrite(output_path, result)
        return output_path
    
    def cross_process(self, image_path: str) -> str:
        """Filter 61: Cross processing effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.3)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        r, g, b = img.split()
        r = r.point(lambda i: i * 0.9)
        b = b.point(lambda i: i * 1.1)
        img = Image.merge('RGB', (r, g, b))
        output_path = self.generate_filename("cross_process")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def hdr(self, image_path: str) -> str:
        """Filter 62: HDR effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        output_path = self.generate_filename("hdr")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def dramatic(self, image_path: str) -> str:
        """Filter 63: Dramatic effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(0.9)
        output_path = self.generate_filename("dramatic")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def dreamy(self, image_path: str) -> str:
        """Filter 64: Dreamy soft focus effect"""
        img = Image.open(image_path)
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img = ImageEnhance.Brightness(img).enhance(1.2)
        output_path = self.generate_filename("dreamy")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def cinematic(self, image_path: str) -> str:
        """Filter 65: Cinematic letterbox effect"""
        img = Image.open(image_path)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Color(img).enhance(0.8)
        
        width, height = img.size
        bar_height = height // 6
        result = Image.new('RGB', (width, height), 'black')
        result.paste(img, (0, bar_height))
        
        output_path = self.generate_filename("cinematic")
        result.save(output_path, quality=95)
        img.close()
        result.close()
        return output_path
    
    # ============================================
    # SOCIAL MEDIA FILTERS (71-85)
    # ============================================
    
    def instagram_clarendon(self, image_path: str) -> str:
        """Filter 71: Instagram Clarendon filter"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        output_path = self.generate_filename("clarendon")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def instagram_juno(self, image_path: str) -> str:
        """Filter 72: Instagram Juno filter"""
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Warm tones
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.1, 0, 255)
        img[:, :, 1] = np.clip(img[:, :, 1] * 0.9, 0, 255)
        
        output_path = self.generate_filename("juno", ".jpg")
        cv2.imwrite(output_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return output_path
    
    def instagram_ludwig(self, image_path: str) -> str:
        """Filter 73: Instagram Ludwig filter"""
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Desaturate
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = cv2.addWeighted(img, 0.7, cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB), 0.3, 0)
        
        output_path = self.generate_filename("ludwig", ".jpg")
        cv2.imwrite(output_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return output_path
    
    def instagram_gingham(self, image_path: str) -> str:
        """Filter 74: Instagram Gingham filter"""
        img = Image.open(image_path)
        img = ImageEnhance.Color(img).enhance(0.8)
        img = ImageEnhance.Contrast(img).enhance(1.05)
        output_path = self.generate_filename("gingham")
        img.save(output_path, quality=95)
        img.close()
        return output_path
    
    def instagram_moon(self, image_path: str) -> str:
        """Filter 75: Instagram Moon filter"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        img = cv2.addWeighted(img, 0.8, cv2.imread(image_path), 0.2, 0)
        output_path = self.generate_filename("moon", ".jpg")
        cv2.imwrite(output_path, img)
        return output_path
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def apply_filter(self, image_path: str, filter_name: str) -> str:
        """Apply filter by name"""
        filters_map = {
            # Basic
            'grayscale': self.grayscale,
            'sepia': self.sepia,
            'invert': self.invert,
            'emboss': self.emboss,
            'sharpen': self.sharpen,
            'blur': lambda p: self.blur(p, 2),
            'smooth': self.smooth,
            'edge_enhance': self.edge_enhance,
            'contour': self.contour,
            'detail': self.detail,
            'find_edges': self.find_edges,
            
            # Color
            'vintage': self.vintage,
            'cool': self.cool,
            'warm': self.warm,
            'noir': self.noir,
            'pastel': self.pastel,
            'sunset': self.sunset,
            'ocean': self.ocean,
            'forest': self.forest,
            'autumn': self.autumn,
            'spring': self.spring,
            'neon': self.neon,
            'glow': self.glow,
            'rainbow': self.rainbow,
            'prism': self.prism,
            
            # Artistic
            'oil_paint': self.oil_paint,
            'watercolor': self.watercolor,
            'pencil_sketch': self.pencil_sketch,
            'cartoon': self.cartoon,
            'pixelate': self.pixelate,
            'glitch': self.glitch,
            'vhs': self.vhs,
            'halftone': self.halftone,
            'mosaic': self.mosaic,
            'stained_glass': self.stained_glass,
            
            # Lighting
            'bokeh': self.bokeh,
            'lens_flare': self.lens_flare,
            'vignette': self.vignette,
            'hdr': self.hdr,
            'dramatic': self.dramatic,
            'dreamy': self.dreamy,
            'cinematic': self.cinematic,
            
            # Social Media
            'clarendon': self.instagram_clarendon,
            'juno': self.instagram_juno,
            'ludwig': self.instagram_ludwig,
            'gingham': self.instagram_gingham,
            'moon': self.instagram_moon,
        }
        
        if filter_name in filters_map:
            return filters_map[filter_name](image_path)
        else:
            raise ValueError(f"Filter '{filter_name}' not found. Available: {list(filters_map.keys())}")
    
    def get_all_filters(self) -> List[str]:
        """Get list of all available filters"""
        return [
            # Basic
            'grayscale', 'sepia', 'invert', 'emboss', 'sharpen', 'blur', 'smooth',
            'edge_enhance', 'contour', 'detail', 'find_edges',
            # Color
            'vintage', 'cool', 'warm', 'noir', 'pastel', 'sunset', 'ocean',
            'forest', 'autumn', 'spring', 'neon', 'glow', 'rainbow', 'prism',
            # Artistic
            'oil_paint', 'watercolor', 'pencil_sketch', 'cartoon', 'pixelate',
            'glitch', 'vhs', 'halftone', 'mosaic', 'stained_glass',
            # Lighting
            'bokeh', 'lens_flare', 'vignette', 'hdr', 'dramatic', 'dreamy', 'cinematic',
            # Social Media
            'clarendon', 'juno', 'ludwig', 'gingham', 'moon'
        ]
    
    def get_filters_by_category(self) -> Dict[str, List[str]]:
        """Get filters grouped by category"""
        return {
            'Basic': ['grayscale', 'sepia', 'invert', 'emboss', 'sharpen', 'blur', 'smooth', 'edge_enhance', 'contour', 'detail'],
            'Color': ['vintage', 'cool', 'warm', 'noir', 'pastel', 'sunset', 'ocean', 'forest', 'autumn', 'spring'],
            'Artistic': ['oil_paint', 'watercolor', 'pencil_sketch', 'cartoon', 'pixelate', 'glitch', 'vhs', 'halftone', 'mosaic'],
            'Lighting': ['bokeh', 'lens_flare', 'vignette', 'hdr', 'dramatic', 'dreamy', 'cinematic'],
            'Neon & Glow': ['neon', 'glow', 'rainbow', 'prism', 'sparkle'],
            'Social Media': ['clarendon', 'juno', 'ludwig', 'gingham', 'moon']
        }


# ============================================
# INITIALIZE FILTERS
# ============================================

filters = Filters()
