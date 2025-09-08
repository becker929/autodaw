.PHONY: help build test clean x11-test vnc-test

help:
	@echo "Docker GUI Experiments Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  build      - Build all Docker containers"
	@echo "  x11-test   - Test X11 forwarding approach"
	@echo "  vnc-test   - Test VNC server approach"
	@echo "  test       - Test both approaches"
	@echo "  clean      - Clean up containers and images"
	@echo "  setup      - Run interactive setup script"

build:
	@echo "Building X11 forwarding container..."
	cd x11-forwarding && docker-compose build
	@echo "Building VNC server container..."
	cd vnc-server && docker-compose build
	@echo "All containers built successfully!"

x11-test:
	@echo "Testing X11 forwarding approach..."
	cd x11-forwarding && ./setup.sh && docker-compose --profile test up --abort-on-container-exit test-suite

vnc-test:
	@echo "Testing VNC server approach..."
	cd vnc-server && docker-compose up -d vnc-gui
	@echo "VNC server started on localhost:5900"
	@echo "Connect with: open vnc://localhost:5900"

test: x11-test vnc-test

clean:
	@echo "Cleaning up containers..."
	cd x11-forwarding && docker-compose down || true
	cd vnc-server && docker-compose down || true
	docker image prune -f
	@echo "Cleanup complete!"

setup:
	./setup_all.sh
