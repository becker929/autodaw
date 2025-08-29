# Vision Debugging System

A comprehensive vision-based debugging system for REAPER automation that allows capturing and analyzing visual information during automation workflows.

## Features

### 1. Screenshot Capture
- **Full screen capture**: Capture entire desktop
- **REAPER window capture**: Automatically detect and capture REAPER window
- **Region capture**: Capture specific screen regions
- **Metadata tracking**: Store timestamps, descriptions, and context

### 2. Automation Monitoring
- **Beacon file monitoring**: Watch automation status and capture screenshots on changes
- **Workflow integration**: Automatic capture during automation sessions
- **Status tracking**: Visual documentation of automation progress

### 3. Analysis Tools
- **REAPER state analysis**: Analyze current REAPER state from screenshots
- **Window detection**: Automatically find and focus on REAPER windows
- **Debug reports**: Generate comprehensive visual debug reports

## Installation

### Install Dependencies

```bash
# Install vision debugging dependencies
uv run install_vision_deps.py

# Or manually:
uv add pyautogui pillow
```

### macOS Permissions

On macOS, you'll need to grant screen recording permissions:

1. System Preferences → Security & Privacy → Privacy
2. Select "Screen Recording" from the left panel
3. Add Terminal or your Python application
4. Restart your terminal

## Usage

### 1. Enable Vision Debugging in Workflows

Add the `--vision-debug` flag to any automation command:

```bash
# Run octave sweep with vision debugging
uv run main_v2.py octave-sweep --vision-debug

# Run parameter discovery with vision debugging
uv run main_v2.py discover --vision-debug

# Run custom parameter sweep with vision debugging
uv run main_v2.py custom-sweep octave:-1:1:3 --vision-debug
```

When enabled, the system will:
- Capture screenshots at session start and end
- Monitor beacon file and capture on status changes
- Generate debug reports with all captured images
- Save everything to `~/Desktop/reaper_debug/`

### 2. Manual Vision Debugging

Use the standalone vision debugging commands:

```bash
# Capture a screenshot
uv run main_v2.py vision-debug screenshot "My debug capture"

# Capture REAPER window specifically
uv run main_v2.py vision-debug reaper

# Analyze current REAPER state
uv run main_v2.py vision-debug analyze

# Monitor beacon file with screenshots
uv run main_v2.py vision-debug monitor /path/to/beacon.txt session_id
```

### 3. Programmatic Usage

```python
from src.vision_debugger import VisionDebugger

# Create debugger
debugger = VisionDebugger()

# Capture screenshot
metadata = debugger.capture_screenshot(
    session_id="my_session",
    description="Debug capture"
)

# Capture REAPER window
reaper_capture = debugger.capture_reaper_window("reaper_debug")

# Monitor automation with vision
captures = debugger.monitor_beacon_and_capture(
    beacon_file=Path("beacon.txt"),
    session_id="monitoring",
    capture_interval=3.0,
    timeout=60.0
)

# Analyze REAPER state
analysis = debugger.analyze_reaper_state()
print(f"REAPER responsive: {analysis['reaper_responsive']}")

# Generate debug report
report_path = debugger.create_debug_report("my_session")
```

## Output Structure

Vision debugging creates the following files:

```
~/Desktop/reaper_debug/
├── session1_20241201_143022_123.png     # Screenshots
├── session1_20241201_143025_456.png
├── session1_20241201_143028_789.png
└── session1_debug_report.json           # Debug report
```

### Debug Report Format

```json
{
  "session_id": "session1",
  "generated_at": "2024-12-01T14:30:30",
  "total_screenshots": 5,
  "screenshots": [
    {
      "timestamp": "20241201_143022_123",
      "description": "Session start - {'octave': -2.0}",
      "file_path": "/Users/.../session1_20241201_143022_123.png",
      "window_title": "REAPER - serum1.RPP",
      "automation_status": "RUNNING"
    }
  ]
}
```

## Integration with Existing Workflows

The vision debugging system integrates seamlessly with existing workflows:

### WorkflowOrchestrator Integration

```python
# Enable vision debugging in orchestrator
orchestrator = MultiParameterWorkflowOrchestrator(
    system_config,
    enable_vision_debug=True
)

# Vision debugging will automatically:
# 1. Capture session start/end screenshots
# 2. Monitor beacon file with visual captures
# 3. Generate debug reports
# 4. Handle threading for non-blocking operation
```

### Automatic Features

When vision debugging is enabled:

- **Session Start**: Captures initial REAPER state
- **Status Monitoring**: Captures on beacon file changes (RUNNING, COMPLETED, ERROR)
- **Session End**: Captures final state with success/failure status
- **Report Generation**: Creates comprehensive debug report
- **Cleanup**: Manages screenshot storage and cleanup

## Troubleshooting

### Common Issues

1. **Permission Denied**: Grant screen recording permissions on macOS
2. **PyAutoGUI Import Error**: Run `uv run install_vision_deps.py`
3. **REAPER Window Not Found**: Ensure REAPER is running and visible
4. **Threading Issues**: Vision monitoring runs in background threads

### Debug Tips

1. **Test Basic Capture**: Use `uv run main_v2.py vision-debug screenshot` first
2. **Check REAPER Detection**: Use `uv run main_v2.py vision-debug reaper`
3. **Verify Permissions**: Check System Preferences → Security & Privacy
4. **Monitor Logs**: Watch console output for vision debugging messages

## Advanced Configuration

### Custom Debug Directory

```python
from pathlib import Path
from src.vision_debugger import VisionDebugger

# Use custom debug directory
debugger = VisionDebugger(debug_dir=Path("/custom/debug/path"))
```

### Capture Intervals

```python
# Monitor with custom intervals
captures = debugger.monitor_beacon_and_capture(
    beacon_file=beacon_path,
    session_id="custom",
    capture_interval=1.0,  # Capture every second
    timeout=300.0          # 5 minute timeout
)
```

### Cleanup Management

```python
# Clean up old screenshots
debugger.cleanup_old_screenshots(days_old=3)  # Remove files older than 3 days
```

## Performance Considerations

- Screenshots are saved as PNG files (~1-5MB each)
- Monitoring creates 1 screenshot per status change (typically 3-5 per session)
- Background monitoring uses minimal CPU
- Automatic cleanup prevents disk space issues

## Security Notes

- Vision debugging captures full screen content
- Screenshots may contain sensitive information
- Debug reports are saved locally only
- Consider cleanup policies for production use

