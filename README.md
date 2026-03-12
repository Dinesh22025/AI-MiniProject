# Driver AI Co-Pilot - Unified Application

A unified full-stack application combining React frontend with Flask backend for driver monitoring and AI assistance. The frontend is served directly from the Flask backend for seamless integration.

## Project Structure

```
driver-ai-copilot/
├── frontend/          # React/Vite application
│   ├── src/          # React source code
│   ├── public/       # Static assets
│   ├── dist/         # Built frontend (served by Flask)
│   └── package.json
├── backend/          # Flask API server
│   ├── app/          # Flask application
│   ├── run.py        # Server entry point
│   └── requirements.txt
├── start.py          # Unified application launcher
├── start.bat         # Windows launcher
└── package.json      # Root package.json for unified commands
```

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Windows
start.bat

# Or using Python directly
python start.py
```

### Option 2: Manual Setup
1. **Install all dependencies:**
   ```bash
   npm run install:all
   ```

2. **Build and start the unified application:**
   ```bash
   npm start
   ```

## Running the Application

### Unified Mode (Production-like)
The frontend is built and served by the Flask backend:
```bash
npm start
# or
python start.py
# or
start.bat
```

Access the application at: **http://localhost:5000**

### Development Mode
Run frontend and backend separately with hot reload:
```bash
npm run dev
```

This starts:
- Flask backend on `http://localhost:5000`
- Vite dev server on `http://localhost:5173` (with API proxying)

## API Endpoints

- `GET /` - Serves the React application
- `GET /health` - Health check
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/monitor/analyze` - Real-time face analysis
- `GET /api/history` - Detection history
- `GET /api/me` - User profile
- `PUT /api/settings` - Update user settings

## Features

### Frontend (React)
- 🎯 Real-time driver monitoring dashboard
- 👤 User authentication and profiles
- 📊 Detection history and analytics
- ⚙️ Customizable settings (alerts, themes)
- 📱 Responsive design

### Backend (Flask)
- 🤖 AI-powered face detection (MediaPipe + OpenCV)
- 😴 Drowsiness detection (Eye Aspect Ratio)
- 🥱 Yawning detection (Mouth Aspect Ratio)
- 👀 Distraction detection (Gaze tracking)
- 🔐 JWT authentication
- 💾 SQLite database
- 🚨 Real-time alerts

### Vision Detection System
- **Priority Order**: Drowsiness → Distraction → Yawning → Focused
- **Drowsiness**: EAR < 0.25 (eyes closed/closing)
- **Yawning**: MAR > 0.08 + eyes open (prevents drowsy misclassification)
- **Distraction**: Gaze offset > 8% or head tilt > 7°
- **Fallback**: OpenCV-only mode if MediaPipe fails

## Development Commands

```bash
# Install all dependencies
npm run install:all

# Development mode (hot reload)
npm run dev

# Build frontend only
npm run build

# Start unified application
npm start

# Start production mode (assumes frontend is built)
npm run start:prod

# Test vision detection
npm run test:vision

# Clean build files
npm run clean
```

## Technologies Used

- **Frontend:** React 18, Vite, Axios, Modern CSS
- **Backend:** Flask, MediaPipe, OpenCV, SQLAlchemy
- **Database:** SQLite (development)
- **Authentication:** JWT tokens
- **Vision AI:** MediaPipe Face Mesh, OpenCV Haar Cascades

## System Requirements

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Webcam** for real-time monitoring
- **Windows/Linux/macOS** support

## Troubleshooting

### Common Issues

1. **"Frontend not built" error**
   ```bash
   npm run build
   ```

2. **Camera access denied**
   - Allow camera permissions in browser
   - Check if camera is being used by another application

3. **MediaPipe import error**
   ```bash
   cd backend
   pip install --upgrade mediapipe opencv-python
   ```

4. **Port already in use**
   - Kill process using port 5000
   - Or modify port in `backend/run.py`

### Debug Mode
For detailed vision detection debugging:
```bash
cd backend
python test_vision_fix.py
```

## Architecture

The application uses a unified architecture where:
1. **Flask backend** serves the built React frontend
2. **API routes** are prefixed with `/api/`
3. **Static files** are served from `frontend/dist/`
4. **React Router** is handled by Flask catch-all route
5. **CORS** is configured for development mode

This provides the benefits of:
- ✅ Single server deployment
- ✅ No CORS issues in production
- ✅ Simplified configuration
- ✅ Better performance
- ✅ Easier deployment