# Docker GUI Experiments

This subproject explores running GUI applications inside Docker containers on macOS using virtual displays.

## Approaches Implemented

### 1. X11 Forwarding (x11-forwarding/)
Uses XQuartz to forward X11 display from container to host macOS desktop.

**Requirements:**
- XQuartz installed on macOS host
- Network access between container and host

### 2. VNC Server (vnc-server/)
Self-contained solution with virtual framebuffer and VNC server inside container.

**Requirements:**
- VNC client (built-in Screen Sharing on macOS, or VNC Viewer)
- No host dependencies

## Quick Start

**Prerequisites:**
- Docker Desktop for Mac installed and running
- For X11 approach: XQuartz installed and configured

**Option 1: Interactive Setup**
```bash
./setup_all.sh
```

**Option 2: Makefile Commands**
```bash
make build      # Build all containers
make vnc-test   # Test VNC approach
make x11-test   # Test X11 approach (requires XQuartz)
make clean      # Clean up
```

**Option 3: Manual Setup**
1. Choose an approach (X11 or VNC)
2. Navigate to the respective directory
3. Run `docker-compose up`
4. Follow the specific instructions in each approach's README

## Test Applications

Each approach includes test applications:
- xeyes (simple X11 test)
- xclock (clock display)
- Simple Python Tkinter GUI
- Firefox web browser

## Security Notes

X11 forwarding requires opening network connections to the X server, which has security implications. VNC approach is more isolated but requires port forwarding.
