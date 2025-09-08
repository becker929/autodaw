# VNC Server Approach

This approach runs a complete virtual desktop environment inside the Docker container with VNC access. No host dependencies required.

## Features

- **Self-contained**: No need to install XQuartz or configure host X11
- **Virtual framebuffer**: Uses Xvfb for headless display
- **Window manager**: Fluxbox lightweight desktop environment
- **VNC server**: x11vnc for remote access
- **Multiple configurations**: Basic, test suite, and secure versions

## Quick Start

1. **Start the VNC server:**
   ```bash
   # Basic VNC server (no password)
   docker-compose up vnc-gui

   # With test applications pre-loaded
   docker-compose --profile test up vnc-tests

   # Secure version with password
   docker-compose --profile secure up vnc-secure
   ```

2. **Connect with VNC viewer:**
   - **macOS built-in**: Open Finder → Go → Connect to Server → `vnc://localhost:5900`
   - **VNC Viewer**: Download from RealVNC and connect to `localhost:5900`
   - **Command line**: `open vnc://localhost:5900` (macOS)

## Port Mapping

- `5900` - Basic VNC server (no password)
- `5901` - Test suite VNC server
- `5902` - Secure VNC server (password: `dockergui`)

## Test Applications

Once connected via VNC, you can run applications in the virtual desktop:

```bash
# Open terminal in VNC desktop, then run:
xeyes &          # Animated eyes
xclock &         # Analog clock
python3 test_apps/simple_gui.py &  # Custom Tkinter GUI
firefox &        # Web browser
xterm &          # Additional terminal
```

## Container Shell Access

To run commands inside the container:

```bash
# Get shell access
docker-compose exec vnc-gui bash

# Run specific commands
docker-compose exec vnc-gui xeyes
docker-compose exec vnc-gui python3 test_apps/simple_gui.py
```

## VNC Connection Methods

### macOS Built-in Screen Sharing

1. Open Finder
2. Press `Cmd+K` (or Go → Connect to Server)
3. Enter: `vnc://localhost:5900`
4. Click Connect

### Third-party VNC Viewers

- **RealVNC Viewer**: https://www.realvnc.com/en/connect/download/viewer/
- **TigerVNC**: Available via Homebrew: `brew install tiger-vnc`

## Troubleshooting

**VNC connection refused:**
- Check that the container is running: `docker ps`
- Verify port mapping: `docker port docker-gui-vnc`
- Check container logs: `docker logs docker-gui-vnc`

**Applications don't appear:**
- Make sure you're connected to the VNC session
- Check that DISPLAY is set to `:99` in the container
- Try running applications with `&` to run in background

**Performance issues:**
- VNC can be slower than X11 forwarding
- Reduce color depth if needed
- Consider using a lighter window manager

## Security Notes

- Basic configuration has no VNC password (suitable for local testing only)
- Use the secure profile for password protection
- VNC traffic is unencrypted - only use on trusted networks
- Consider SSH tunneling for remote access: `ssh -L 5900:localhost:5900 user@host`

## Customization

Edit the Dockerfile to:
- Change desktop environment (XFCE, LXDE, etc.)
- Install additional applications
- Modify screen resolution (change `1024x768x24`)
- Add VNC password by default
