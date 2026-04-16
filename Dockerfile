FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with verbose output and ignore errors
RUN pip install --no-cache-dir --default-timeout=100 \
    pyrogram==2.0.106 \
    Pillow==10.1.0 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    moviepy==1.0.3 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    aiohttp==3.9.1 \
    gTTS==2.2.4 \
    openai-whisper==20231117 \
    aiofiles==23.2.1 \
    pydantic==2.5.0 \
    colorama==0.4.6 \
    tqdm==4.66.1 \
    psutil==5.9.6

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp_media thumbnails fonts stickers effects backups logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_WEBHOOK=False
ENV PORT=8080

# Expose port for webhook
EXPOSE 8080

# Run the bot
CMD ["python", "-u", "bot.py"]
