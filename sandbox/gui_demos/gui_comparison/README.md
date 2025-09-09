# Audio Comparison GUI Demo

A web interface for conducting pairwise audio comparisons with preference recording. Users can listen to two audio samples at a time and indicate their preference with confidence levels and notes.

## Architecture

- **Backend**: FastAPI server with RESTful endpoints for audio management and comparison data
- **Frontend**: React application with modern UI for audio playback and preference selection
- **Data Storage**: In-memory storage (stubbed for demonstration)

## Features

- Pairwise audio comparison interface
- Audio playback controls for each sample
- Preference selection with confidence scoring
- Optional notes for each comparison
- Statistics dashboard showing progress and preference distribution
- Responsive design with modern UI/UX

## Setup Instructions

### Quick Start (Recommended)

1. Navigate to the project directory:
```bash
cd comparison-gui-demo
```

2. **Option A - Using startup script:**
```bash
./start.sh
```

3. **Option B - Using Make commands:**
```bash
make dev-setup
make start
```

The backend will be available at `http://localhost:8000` and frontend at `http://localhost:3000`

### Make Commands

- `make help` - Show all available commands
- `make install` - Install all dependencies (backend + frontend)
- `make start` - Start both backend and frontend servers
- `make start-backend` - Start only the FastAPI backend server
- `make start-frontend` - Start only the React frontend server
- `make stop` - Stop all running servers
- `make status` - Check if services are running
- `make test` - Run test suite
- `make clean` - Clean build artifacts and dependencies
- `make dev-setup` - Complete development environment setup

### Manual Setup (Alternative)

#### Backend Setup

1. Install Python dependencies:
```bash
uv sync
```

2. Start the FastAPI server:
```bash
uv run python run_backend.py
```

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

## API Endpoints

### Audio Management
- `GET /api/audio-files` - List all audio files
- `POST /api/audio-files/upload` - Upload new audio file
- `GET /api/audio/{file_id}/stream` - Stream audio file

### Comparisons
- `GET /api/comparisons/next` - Get next unrated comparison pair
- `GET /api/comparisons` - List all comparison pairs
- `GET /api/comparisons/{id}` - Get specific comparison
- `POST /api/comparisons/{id}/preference` - Submit preference for comparison
- `POST /api/comparisons/generate` - Generate new comparison pairs

### Statistics
- `GET /api/stats` - Get comparison statistics and progress

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Listen to Option A and Option B audio samples
4. Select your preferred option by clicking on it
5. Adjust confidence level using the slider
6. Add optional notes about your preference
7. Submit your preference to proceed to the next comparison

## Development Notes

- Audio playback is currently stubbed - actual audio streaming requires implementing file serving
- Data persistence uses in-memory storage - replace with database for production
- File upload functionality is stubbed - implement actual file storage and processing
- Audio metadata extraction using librosa is prepared but not implemented

## Future Enhancements

- Real audio file storage and streaming
- Database persistence for comparison data
- Advanced audio analysis and visualization
- Export comparison results
- Batch comparison generation algorithms
- User authentication and session management
