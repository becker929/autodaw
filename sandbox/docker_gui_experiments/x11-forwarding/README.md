# X11 Forwarding Approach

This approach uses X11 forwarding to display GUI applications from Docker containers on the macOS desktop via XQuartz.

## Prerequisites

1. **Install XQuartz:**
   ```bash
   brew install --cask xquartz
   ```
   Or download from: https://www.xquartz.org/

2. **Configure XQuartz:**
   - Restart your Mac after installation
   - Open XQuartz
   - Go to Preferences > Security
   - Check "Allow connections from network clients"
   - Restart XQuartz

## Quick Start

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This will configure X11 permissions and create the necessary environment files.

2. **Start the container:**
   ```bash
   # Interactive shell
   docker-compose up gui-app

   # Run Firefox directly
   docker-compose --profile firefox up firefox

   # Run test suite
   docker-compose --profile test up test-suite
   ```

## Manual Setup (if setup.sh doesn't work)

1. **Get your host IP:**
   ```bash
   ifconfig en0 | grep inet | awk '$1=="inet" {print $2}'
   ```

2. **Allow X11 connections:**
   ```bash
   xhost + YOUR_IP_ADDRESS
   ```

3. **Set DISPLAY variable:**
   ```bash
   export DISPLAY=YOUR_IP_ADDRESS:0
   ```

4. **Create .env file:**
   ```
   DISPLAY=YOUR_IP_ADDRESS:0
   ```

## Test Applications

Once the container is running, you can test various GUI applications:

```bash
# In the container shell
xeyes          # Animated eyes that follow cursor
xclock         # Analog clock
python3 test_apps/simple_gui.py  # Custom Tkinter GUI
firefox        # Web browser
```

## Troubleshooting

**No display appears:**
- Ensure XQuartz is running
- Check that "Allow connections from network clients" is enabled in XQuartz preferences
- Verify the DISPLAY variable is set correctly
- Try running `xhost +` to allow all connections (less secure)

**Permission denied errors:**
- Run the setup script again
- Manually run `xhost + YOUR_IP_ADDRESS`

**Container can't connect to display:**
- Check your network connection
- Verify the IP address in the DISPLAY variable is correct
- Try using `host.docker.internal` instead of the IP address

## Security Notes

This approach requires opening X11 network connections, which has security implications. Only use on trusted networks. The setup script limits access to your specific IP address, but you can use `xhost +` to allow all connections if needed (less secure).
