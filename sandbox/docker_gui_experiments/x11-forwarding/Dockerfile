FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install X11 applications and utilities
RUN apt-get update && apt-get install -y \
    x11-apps \
    x11-utils \
    xauth \
    python3 \
    python3-pip \
    python3-tk \
    firefox \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser
WORKDIR /home/appuser

# Copy test applications
COPY test_apps/ ./test_apps/

# Set display environment variable (will be overridden by docker-compose)
ENV DISPLAY=:0

CMD ["bash"]
