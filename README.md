# Face Authentication Attendance System

A comprehensive Face Authentication system built with Python (FastAPI), OpenCV, and MediaPipe.

## Features
- **Registration**: Capture a burst of photos (auto-training) via webcam.
- **Attendance**: Secure "Punch-In" / "Punch-Out" with liveness checking.
- **Liveness Detection**: Prevents basic spoofing using Eye Aspect Ratio (MediaPipe).
- **History**: View attendance logs.
- **Lighting Robustness**: Uses CLAHE for image enhancement.

## Installation

1.  Navigate to the project directory:
    ```bash
    cd face_auth_system
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Run the start script:
    ```bash
    .\run.bat
    ```
    Or manually:
    ```bash
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  Open your browser to: `http://localhost:8000`

## Structure
- `main.py`: Backend API and server.
- `core/`: Authentication logic (LBPH) and Database.
- `static/`, `templates/`: Frontend UI.
- `docs/`: Detailed report.
