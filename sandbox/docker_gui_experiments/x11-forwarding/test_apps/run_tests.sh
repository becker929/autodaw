#!/bin/bash

echo "=== Docker GUI Test Suite - X11 Forwarding ==="
echo "Running various GUI applications to test X11 forwarding..."
echo

echo "1. Testing xeyes (should show animated eyes following cursor):"
xeyes &
XEYES_PID=$!
sleep 3
kill $XEYES_PID 2>/dev/null

echo "2. Testing xclock (should show analog clock):"
xclock &
XCLOCK_PID=$!
sleep 3
kill $XCLOCK_PID 2>/dev/null

echo "3. Testing Python Tkinter GUI:"
python3 /home/appuser/test_apps/simple_gui.py &
GUI_PID=$!
sleep 5
kill $GUI_PID 2>/dev/null

echo
echo "All tests completed. If you saw GUI windows, X11 forwarding is working!"
echo "To run individual tests:"
echo "  xeyes"
echo "  xclock"
echo "  python3 /home/appuser/test_apps/simple_gui.py"
echo "  firefox"
