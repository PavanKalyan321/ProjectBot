FROM python:3.9-slim

# Install system dependencies including Tesseract OCR, X11, and GUI tools
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    xvfb \
    x11-utils \
    scrot \
    python3-tk \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ ./backend/

# Set environment variables
ENV PYTHONPATH=/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV DISPLAY=:99

# Create directory for logs and data
RUN mkdir -p logs data backend

# Add entrypoint script for X11 setup
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python.*bot.py" > /dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]

# Default command to run the bot
CMD ["python3", "backend/bot.py"]