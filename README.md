# AutoDAW - Automated Digital Audio Workstation

A web-based genetic algorithm optimization system combining GA+JSI+Audio Oracle for automated digital audio workstation parameter tuning.

## Overview

AutoDAW integrates three powerful components:

1. **Genetic Algorithm (GA)** - Population-based optimization using pymoo
2. **Just Sort It (JSI)** - Adaptive quicksort algorithm for ranking with minimal comparisons
3. **Audio Oracle** - Librosa-based comparison system for audio analysis
4. **Web Interface** - React frontend with FastAPI backend for human-in-the-loop optimization

## Features

- 🎵 **Web-based Audio Comparisons** - Listen to and compare audio samples through a modern web interface
- 📊 **Population Visualization** - View current and historical GA populations with Bradley-Terry strength indicators
- 💾 **SQLite Persistence** - All user feedback and optimization data stored locally
- 📈 **Real-time Statistics** - Track comparison progress and preference distributions
- 🔄 **Synchronous GA Operations** - Web API endpoints for creating sessions and managing optimization
- 🎛️ **REAPER Integration** - Automated audio rendering using REAPER project files

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI Backend│    │  REAPER Project │
│                 │    │                  │    │                 │
│ • Audio Player  │◄──►│ • GA Engine      │◄──►│ • Audio Render  │
│ • Comparisons   │    │ • JSI Ranking    │    │ • Parameter Set │
│ • Population UI │    │ • SQLite DB      │    │                 │
│ • Statistics    │    │ • BT Calculations│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- **Node.js 16+** with npm
- **REAPER** project in `reaper/` directory

### Option 1: Using the startup script (Recommended)

```bash
./start.sh
```

### Option 2: Using Make commands

```bash
make dev-setup  # Install all dependencies
make start      # Start both backend and frontend
```

### Option 3: Manual startup

```bash
# Install dependencies
uv sync
cd autodaw/frontend && npm install

# Start backend (Terminal 1)
uv run python main.py

# Start frontend (Terminal 2)
cd autodaw/frontend && npm start
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage Workflow

### 1. Create GA Session
- Navigate to the **Sessions** tab
- Click "New Session" and configure:
  - Session name
  - Target frequency (Hz)
  - Population size (4-32 individuals)
- Click "Create Session"

### 2. Initialize Population
- Select your session and click "Initialize"
- This generates the first population and renders audio files using REAPER

### 3. Evaluate Comparisons
- Go to the **Comparisons** tab
- Listen to Option A and Option B audio samples
- Select your preferred option
- Set confidence level (0-100%)
- Add optional notes
- Submit preference

### 4. View Results
- **Populations** tab: Browse generations and view Bradley-Terry strengths
- **Statistics** tab: Track progress and preference distributions
- Solutions are ranked by user feedback using JSI algorithm

## API Endpoints

### Sessions
- `POST /api/sessions` - Create new GA session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details

### Populations
- `POST /api/populations/initialize` - Initialize first population
- `GET /api/sessions/{id}/populations` - Get session populations
- `GET /api/populations/{id}` - Get population with BT strengths

### Comparisons
- `GET /api/comparisons/next` - Get next comparison to evaluate
- `POST /api/comparisons/{id}/preference` - Submit user preference

### Audio & Stats
- `GET /api/audio/{id}/stream` - Stream audio file
- `GET /api/stats` - Get comparison statistics

## Database Schema

The application uses SQLite with the following main tables:

- `ga_sessions` - Optimization sessions
- `populations` - GA populations by generation
- `solutions` - Individual solutions with parameters
- `audio_files` - Rendered audio file metadata
- `comparisons` - Pairwise comparison data
- `bt_strengths` - Bradley-Terry model strengths

## Development

### Project Structure

```
autodaw/
├── autodaw/
│   ├── backend/           # FastAPI backend
│   │   └── main.py
│   ├── core/              # Core logic
│   │   ├── database.py    # SQLite models
│   │   └── ga_jsi_engine.py # GA+JSI engine
│   └── frontend/          # React frontend
│       └── src/
├── reaper/                # REAPER project files
├── demos/                 # Original demo implementations
├── main.py               # Backend entry point
├── start.sh              # Startup script
└── Makefile              # Development commands
```

### Make Commands

```bash
make help          # Show all commands
make install       # Install dependencies
make start         # Start both servers
make start-backend # Backend only
make start-frontend# Frontend only
make stop          # Stop all servers
make status        # Check service status
make test          # Run tests
make clean         # Clean artifacts
```

### Development Notes

- Backend uses **FastAPI** with automatic OpenAPI documentation
- Frontend is **React + TypeScript** with Axios for API calls
- Audio streaming uses FastAPI's `StreamingResponse`
- Real-time updates via polling (WebSocket support planned)
- All user preferences stored in SQLite for persistence

## Technical Details

### GA+JSI Integration

The system uses a novel approach where:

1. **GA generates** parameter sets for audio synthesis
2. **REAPER renders** audio files from parameters
3. **Users evaluate** pairwise audio comparisons
4. **JSI algorithm** efficiently ranks solutions using minimal comparisons
5. **Bradley-Terry model** estimates solution strengths with confidence intervals

### Audio Oracle

Instead of automated frequency analysis, the system relies on human preference feedback, making it suitable for subjective audio quality optimization beyond simple frequency matching.

### Comparison Strategy

- Generates all possible pairwise comparisons initially
- Could be extended with active learning strategies
- JSI minimizes comparisons needed for reliable ranking

## Future Enhancements

- [ ] **WebSocket integration** for real-time updates
- [ ] **Active learning** comparison selection strategies
- [ ] **Multi-objective optimization** for complex audio metrics
- [ ] **Batch audio processing** for faster rendering
- [ ] **Export capabilities** for optimized parameters
- [ ] **User authentication** and session management
- [ ] **Advanced visualizations** for population evolution

## Dependencies

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **pymoo** - Genetic algorithm framework
- **librosa** - Audio analysis
- **choix** - Bradley-Terry implementation

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Axios** - HTTP client
- **Lucide React** - Icons

## License

This project builds upon the existing demo implementations in the `demos/` directory and integrates them into a unified web application for practical audio optimization workflows.

## Troubleshooting

### Common Issues

1. **"REAPER project not found"**
   - Ensure `reaper/` directory exists with valid REAPER project files
   - Check that the path in `ga_jsi_engine.py` is correct

2. **Audio playback issues**
   - Verify audio files are being generated in `reaper/renders/`
   - Check browser audio permissions and format support

3. **Database errors**
   - Delete `autodaw.db` to reset database
   - Check file permissions in project directory

4. **Port conflicts**
   - Backend uses port 8000, frontend uses port 3000
   - Modify ports in configuration if needed

For more detailed troubleshooting, check the console logs in both backend and frontend terminals.
