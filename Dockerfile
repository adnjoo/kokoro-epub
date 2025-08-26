# Dockerfile.worker
# CUDA runtime base (12.2 pairs with PyTorch cu121 wheels fine)
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: Python, ffmpeg (for pydub), libsndfile (for soundfile), and basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    ffmpeg \
    libsndfile1 \
    ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy just requirements first (better caching)
COPY requirements.txt /app/requirements.txt

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Install PyTorch with CUDA wheels (cu121 works on CUDA 12.2 runtime)
RUN pip3 install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch torchvision torchaudio

# Install the rest of requirements
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy entire repo into container
COPY . /app

# 👇 Switch into your app/ folder where cli.py lives
WORKDIR /app/app

# Run CLI by default
ENTRYPOINT ["python3", "cli.py"]
