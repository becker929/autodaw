#!/bin/bash

echo "=== Docker GUI Test Suite - VNC Server ==="
echo "Running various GUI applications in the virtual display..."
echo "Connect VNC viewer to localhost:5900 to see the applications"
echo

# Ensure we're using the virtual display
export DISPLAY=:99

echo "1. Starting xeyes (animated eyes)..."
xeyes &
XEYES_PID=$!

echo "2. Starting xclock (analog clock)..."
xclock &
XCLOCK_PID=$!

echo "3. Starting Python Tkinter GUI..."
python3 /home/vncuser/test_apps/simple_gui.py &
GUI_PID=$!

echo "4. Starting xterm (terminal window)..."
xterm &
XTERM_PID=$!

echo
echo "All GUI applications started in background."
echo "Connect your VNC viewer to localhost:5900 to see them."
echo "No password required for this demo."
echo
echo "To kill all test applications:"
echo "  kill $XEYES_PID $XCLOCK_PID $GUI_PID $XTERM_PID"
echo
echo "To start Firefox:"
echo "  firefox &"
echo
echo "Press Ctrl+C to stop this script (applications will keep running)"

# Keep script running
while true; do
    sleep 10
    echo "VNC server running... Connect to localhost:5900"
done
