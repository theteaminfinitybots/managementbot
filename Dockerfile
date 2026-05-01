# Use stable modern base (no buster issues)
FROM python:3.10-slim

ENV PIP_NO_CACHE_DIR=1
ENV DEBIAN_FRONTEND=noninteractive

# Install only required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Clone your bot
WORKDIR /root
RUN git clone https://github.com/theteinfinitybots/managemenbot.git

WORKDIR /root/AloneRobot

# (Optional) copy your custom config if exists
COPY ./AloneRobot/config.py /root/AloneRobot/AloneRobot/config.py

# Install Python deps
RUN pip install -r requirements.txt

# Start bot
CMD ["python", "-m", "AloneRobot"]
