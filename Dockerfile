FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p temp_media thumbnails fonts stickers logs
# Copy application
COPY . .

# Create directories
RUN mkdir -p temp_media thumbnails fonts stickers

# Run bot
CMD ["python", "bot.mx"]
