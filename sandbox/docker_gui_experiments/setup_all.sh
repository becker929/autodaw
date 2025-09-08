#!/bin/bash

echo "=== Docker GUI Experiments Setup ==="
echo
echo "This script will help you set up and test Docker GUI applications on macOS."
echo "Two approaches are available:"
echo "  1. X11 Forwarding (requires XQuartz)"
echo "  2. VNC Server (self-contained)"
echo

# Function to test X11 approach
test_x11() {
    echo "=== Testing X11 Forwarding Approach ==="
    cd x11-forwarding

    if [ ! -f .env ]; then
        echo "Running X11 setup..."
        ./setup.sh
    fi

    echo "Building X11 container..."
    docker-compose build

    echo "Starting test suite..."
    docker-compose --profile test up --abort-on-container-exit test-suite

    cd ..
}

# Function to test VNC approach
test_vnc() {
    echo "=== Testing VNC Server Approach ==="
    cd vnc-server

    echo "Building VNC container..."
    docker-compose build

    echo "Starting VNC server..."
    docker-compose up -d vnc-gui

    echo "VNC server started. Connect to localhost:5900"
    echo "Testing applications..."

    # Give VNC server time to start
    sleep 5

    # Run test applications
    docker-compose exec vnc-gui bash -c "
        export DISPLAY=:99
        xeyes &
        xclock &
        python3 test_apps/simple_gui.py &
        echo 'Test applications started. Connect VNC viewer to localhost:5900'
    "

    cd ..
}

# Function to check prerequisites
check_prereqs() {
    echo "=== Checking Prerequisites ==="

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker Desktop for Mac."
        echo "   https://docs.docker.com/desktop/install/mac-install/"
        return 1
    fi
    echo "✅ Docker found"

    # Check docker-compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ docker-compose not found. Please install Docker Compose."
        return 1
    fi
    echo "✅ docker-compose found"

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running. Please start Docker Desktop."
        return 1
    fi
    echo "✅ Docker daemon running"

    return 0
}

# Function to show menu
show_menu() {
    echo
    echo "Choose an option:"
    echo "1) Test X11 Forwarding approach"
    echo "2) Test VNC Server approach"
    echo "3) Test both approaches"
    echo "4) Build all containers"
    echo "5) Clean up all containers"
    echo "6) Show connection info"
    echo "q) Quit"
    echo
}

# Function to build all
build_all() {
    echo "=== Building All Containers ==="

    echo "Building X11 container..."
    cd x11-forwarding && docker-compose build && cd ..

    echo "Building VNC container..."
    cd vnc-server && docker-compose build && cd ..

    echo "All containers built successfully!"
}

# Function to clean up
cleanup() {
    echo "=== Cleaning Up ==="

    echo "Stopping and removing containers..."
    cd x11-forwarding && docker-compose down && cd ..
    cd vnc-server && docker-compose down && cd ..

    echo "Removing unused images..."
    docker image prune -f

    echo "Cleanup complete!"
}

# Function to show connection info
show_info() {
    echo "=== Connection Information ==="
    echo
    echo "X11 Forwarding:"
    echo "  • Requires XQuartz installed and configured"
    echo "  • Applications appear directly on macOS desktop"
    echo "  • Run: cd x11-forwarding && ./setup.sh && docker-compose up gui-app"
    echo
    echo "VNC Server:"
    echo "  • Self-contained virtual desktop"
    echo "  • Connect VNC viewer to localhost:5900"
    echo "  • Run: cd vnc-server && docker-compose up vnc-gui"
    echo "  • macOS: Finder → Go → Connect to Server → vnc://localhost:5900"
    echo
    echo "Test Commands:"
    echo "  • xeyes (animated eyes)"
    echo "  • xclock (analog clock)"
    echo "  • python3 test_apps/simple_gui.py (custom GUI)"
    echo "  • firefox (web browser)"
    echo
}

# Main script
if ! check_prereqs; then
    exit 1
fi

while true; do
    show_menu
    read -p "Enter your choice: " choice

    case $choice in
        1)
            test_x11
            ;;
        2)
            test_vnc
            ;;
        3)
            test_x11
            echo
            test_vnc
            ;;
        4)
            build_all
            ;;
        5)
            cleanup
            ;;
        6)
            show_info
            ;;
        q|Q)
            echo "Goodbye!"
            break
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac

    echo
    read -p "Press Enter to continue..."
done
