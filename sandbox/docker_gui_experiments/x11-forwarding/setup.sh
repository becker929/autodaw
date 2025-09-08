#!/bin/bash

echo "=== Docker GUI X11 Forwarding Setup for macOS ==="
echo

# Check if XQuartz is installed
if ! command -v xquartz &> /dev/null && ! ls /Applications/Utilities/XQuartz.app &> /dev/null; then
    echo "❌ XQuartz not found. Please install XQuartz first:"
    echo "   brew install --cask xquartz"
    echo "   OR download from: https://www.xquartz.org/"
    echo
    echo "After installing XQuartz:"
    echo "1. Restart your Mac"
    echo "2. Open XQuartz and go to Preferences > Security"
    echo "3. Check 'Allow connections from network clients'"
    echo "4. Restart XQuartz"
    exit 1
fi

echo "✅ XQuartz found"

# Get the host IP address
if command -v ifconfig &> /dev/null; then
    HOST_IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}' | head -n1)
    if [ -z "$HOST_IP" ]; then
        HOST_IP=$(ifconfig en1 | grep inet | awk '$1=="inet" {print $2}' | head -n1)
    fi
else
    echo "❌ ifconfig not found. Cannot determine host IP address."
    exit 1
fi

if [ -z "$HOST_IP" ]; then
    echo "❌ Could not determine host IP address."
    echo "   Make sure you're connected to a network (Wi-Fi or Ethernet)"
    exit 1
fi

echo "✅ Host IP address: $HOST_IP"

# Set up X11 permissions
echo "Setting up X11 permissions..."
xhost + $HOST_IP

# Export DISPLAY variable
export DISPLAY=$HOST_IP:0
echo "✅ DISPLAY set to: $DISPLAY"

# Create .env file for docker-compose
cat > .env << EOF
DISPLAY=$HOST_IP:0
EOF

echo "✅ Created .env file with DISPLAY=$HOST_IP:0"
echo
echo "=== Setup Complete ==="
echo
echo "You can now run:"
echo "  docker-compose up gui-app                    # Interactive bash shell"
echo "  docker-compose --profile firefox up firefox # Run Firefox"
echo "  docker-compose --profile test up test-suite # Run test suite"
echo
echo "Or run individual commands in the container:"
echo "  docker-compose exec gui-app xeyes"
echo "  docker-compose exec gui-app xclock"
echo "  docker-compose exec gui-app python3 test_apps/simple_gui.py"
echo
echo "Note: Make sure XQuartz is running before starting containers!"
