from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import pybase64
import json
from typing import List
from core.auth import FaceAuthSystem
from core.db import Database

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Systems
auth_system = FaceAuthSystem()
db = Database()

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register_page")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/history_page")
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

def read_image_from_base64(base64_string: str) -> np.ndarray:
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    decoded_data = pybase64.b64decode(base64_string)
    np_data = np.frombuffer(decoded_data, np.uint8)
    img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
    return img

@app.post("/api/register")
async def register(name: str = Form(...), images: str = Form(...)): 
    # images is a JSON string of list of base64 strings
    try:
        image_list_b64 = json.loads(images)
        cv_images = []
        for b64 in image_list_b64:
            img = read_image_from_base64(b64)
            if img is not None:
                cv_images.append(img)
        
        if not cv_images:
             return JSONResponse(content={"success": False, "message": "No valid images received"}, status_code=400)
             
        result = auth_system.register_user(name, cv_images)
        return JSONResponse(content=result)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.post("/api/identify")
async def identify(image: str = Form(...), type: str = Form(...)):
    try:
        img = read_image_from_base64(image)
        if img is None:
             return JSONResponse(content={"success": False, "message": "Invalid image data"}, status_code=400)

        # 1. Check Liveness
        liveness = auth_system.check_liveness(img)
        if not liveness["is_live"]:
             return JSONResponse(content={"success": False, "message": liveness["reason"] + ". Please blink/open eyes."}, status_code=400)
             
        # 2. Identify
        result = auth_system.identify_user(img)
        if result["success"]:
            # 3. Log
            # Pass name from result, ID from result.
            log_success = db.log_attendance(str(result["user_id"]), result["name"], type)
            if log_success:
                message = f"Punched {type} for {result['name']}"
            else:
                message = f"Already Punched {type} recently, {result['name']}"
            
            return JSONResponse(content={"success": True, "message": message, "user": result["name"]})
        else:
            return JSONResponse(content={"success": False, "message": "User not recognized. Try getting closer or better light."})
            
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.get("/api/history")
async def get_history():
    return JSONResponse(content=db.get_history())
