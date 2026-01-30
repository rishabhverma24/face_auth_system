@echo off
echo Starting Face Auth System...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
