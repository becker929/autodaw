FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install VNC server, desktop environment, and applications
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    x11-apps \
    x11-utils \
    python3 \
    python3-pip \
    python3-tk \
    firefox \
    xterm \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash vncuser

# Set up VNC directory and password
USER vncuser
WORKDIR /home/vncuser
RUN mkdir -p ~/.vnc

# Create VNC startup script
RUN echo '#!/bin/bash\n\
xrdb $HOME/.Xresources\n\
xsetroot -solid grey\n\
fluxbox &\n\
x11vnc -forever -usepw -create -display :99 &\n\
' > ~/.vnc/xstartup && chmod +x ~/.vnc/xstartup

# Copy test applications
COPY test_apps/ ./test_apps/

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting virtual display and VNC server..."\n\
# Start virtual framebuffer\n\
Xvfb :99 -screen 0 1024x768x24 &\n\
export DISPLAY=:99\n\
\n\
# Start window manager\n\
fluxbox &\n\
\n\
# Start VNC server (no password for demo - use x11vnc -storepasswd to set one)\n\
x11vnc -display :99 -forever -nopw -listen localhost -xkb &\n\
\n\
echo "VNC server started on port 5900"\n\
echo "Connect with VNC viewer to localhost:5900"\n\
echo ""\n\
echo "Available test commands:"\n\
echo "  xeyes &"\n\
echo "  xclock &"\n\
echo "  python3 test_apps/simple_gui.py &"\n\
echo "  firefox &"\n\
echo ""\n\
\n\
# Keep container running\n\
tail -f /dev/null\n\
' > ~/start_vnc.sh && chmod +x ~/start_vnc.sh

# Expose VNC port
EXPOSE 5900

# Set display for applications
ENV DISPLAY=:99

CMD ["/home/vncuser/start_vnc.sh"]
