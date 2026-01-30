import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
from typing import List, Tuple, Dict, Any, Optional
from .db import Database

class FaceAuthSystem:
    def __init__(self):
        self.db = Database()
        # Initialize LBPH Face Recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.model_path = os.path.join("data", "trainer.yml")
        self.faces_dir = os.path.join("data", "faces")
        
        # Ensure directories exist
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Load model if exists
        if os.path.exists(self.model_path):
            self.recognizer.read(self.model_path)
            print("Model loaded.")
        else:
            print("No model found. Please register users.")

        # Initialize MediaPipe Face Landmarker for liveness
        base_options = python.BaseOptions(model_asset_path=os.path.join("data", "face_landmarker.task"))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.5)
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

        # Haar cascade for face detection (needed for LBPH training/cropping)
        # We use MediaPipe for liveness, but OpenCV needs grayscale crops for LBPH.
        # We can use MediaPipe bbox or Haar. Haar is simpler for just cropping grayscale.
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


    def preprocess_image(self, image_np: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE to the Value channel of HSV image to handle varying lighting.
        """
        lab = cv2.cvtColor(image_np, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final

    def detect_face_crop(self, image_np: np.ndarray) -> Optional[np.ndarray]:
        """
        Detects face using Haar Cascade and returns the cropped grayscale face.
        """
        # Preprocess lighting first
        img = self.preprocess_image(image_np)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return None
            
        # Return the largest face
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        return gray[y:y+h, x:x+w]

    def check_liveness(self, images_np: List[np.ndarray]) -> Dict[str, Any]:
        """
        Checks for liveness by detecting a blink across a sequence of frames.
        Returns the best frame (most open eyes) if live.
        """
        ear_history = []
        valid_frames = []

        for img in images_np:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
            detection_result = self.landmarker.detect(mp_image)

            if not detection_result.face_landmarks:
                ear_history.append(None)
                continue

            face_landmarks = detection_result.face_landmarks[0]

            # EAR calculation
            def eye_aspect_ratio(indices):
                p1 = np.array([face_landmarks[indices[0]].x, face_landmarks[indices[0]].y])
                p2 = np.array([face_landmarks[indices[1]].x, face_landmarks[indices[1]].y])
                p3 = np.array([face_landmarks[indices[2]].x, face_landmarks[indices[2]].y])
                p4 = np.array([face_landmarks[indices[3]].x, face_landmarks[indices[3]].y])
                p5 = np.array([face_landmarks[indices[4]].x, face_landmarks[indices[4]].y])
                p6 = np.array([face_landmarks[indices[5]].x, face_landmarks[indices[5]].y])
                A = np.linalg.norm(p2 - p6)
                B = np.linalg.norm(p3 - p5)
                C = np.linalg.norm(p1 - p4)
                return (A + B) / (2.0 * C)

            left_ear = eye_aspect_ratio([362, 385, 387, 263, 373, 380])
            right_ear = eye_aspect_ratio([33, 160, 158, 133, 153, 144])
            avg_ear = (left_ear + right_ear) / 2.0
            
            ear_history.append(avg_ear)
            valid_frames.append((avg_ear, img))

        # Analysis
        if not valid_frames:
             print("[Liveness] No face detected in any frame.")
             return {"is_live": False, "reason": "No face detected in any frame"}

        ears = [e for e in ear_history if e is not None]
        if not ears:
             print("[Liveness] No EAR calculated.")
             return {"is_live": False, "reason": "No face detected"}

        min_ear = min(ears)
        max_ear = max(ears)
        
        print(f"[Liveness] Min EAR: {min_ear:.3f}, Max EAR: {max_ear:.3f}")
        
        # Blink thresholds (Relaxed slightly)
        CLOSED_THRESH = 0.21  # Was 0.18 (Easier to detect closed/blink)
        OPEN_THRESH = 0.23    # Was 0.22 (Requires slightly more open - no, wait, keep it reasonable)
        # Actually, let's keep OPEN_THRESH reasonable. 0.23 is fine.
        
        has_closed = min_ear < CLOSED_THRESH
        has_open = max_ear > OPEN_THRESH
        
        if has_closed and has_open:
            # Find best frame (max EAR) to use for recognition
            best_frame_tuple = max(valid_frames, key=lambda x: x[0])
            print("[Liveness] Blink Detected! PASS.")
            return {
                "is_live": True, 
                "reason": "Blink Detected", 
                "best_image": best_frame_tuple[1]
            }
        else:
            reason = f"Liveness Failed. Min: {min_ear:.2f} (Need < {CLOSED_THRESH}), Max: {max_ear:.2f} (Need > {OPEN_THRESH})"
            print(f"[Liveness] {reason}")
            return {
                "is_live": False, 
                "reason": "Blink not detected. Ensure you blink naturally."
            }

    def train_model(self):
        """Retrains the LBPH model with all faces in data/faces."""
        faces = []
        ids = []
        
        users = self.db.get_users()
        user_ids = {u["id"] for u in users}
        
        print("Training model...")
        
        for root, dirs, files in os.walk(self.faces_dir):
            for file in files:
                if file.endswith("jpg") or file.endswith("png"):
                    path = os.path.join(root, file)
                    # Extract User ID from folder name (faces/1/...) or filename
                    # We assume structure: data/faces/{user_id}/{count}.jpg
                    try:
                         # Get parent folder name
                        parent = os.path.basename(os.path.dirname(path))
                        user_id = int(parent) 
                        
                        img = cv2.imread(path)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        # Ensure it's cropped? The register function saves CROPPED faces.
                        # But let's detect to be safe if we saved full images.
                        # Actually, save CROPPED in register to save space and time.
                        # Let's assume content is face.
                        faces.append(gray)
                        ids.append(user_id)
                    except Exception as e:
                        print(f"Skipping {path}: {e}")

        if faces:
            self.recognizer.train(faces, np.array(ids))
            self.recognizer.save(self.model_path)
            print("Model trained and saved.")
        else:
            print("No data to train.")

    def register_user(self, name: str, images: List[np.ndarray]) -> Dict[str, Any]:
        """
        Registers a user with a list of images. 
        Saves cropped faces and retrains model.
        """
        # 1. Create User in DB
        # Only create if logic allows. DB `add_user` returns ID.
        # But we might need check unique name first? `db.add_user` does that roughly.
        # Let's iterate.
        
        # We need a dummy encoding for the interface? No, DB schema has 'encoding'.
        # We'll just pass empty list or Dummy.
        user_id = self.db.add_user(name, []) 
        
        # 2. Save Images
        user_dir = os.path.join(self.faces_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        saved_count = 0
        for i, img in enumerate(images):
            # Detect and Crop
            crop = self.detect_face_crop(img)
            if crop is not None:
                # Save grayscale crop
                path = os.path.join(user_dir, f"{i}.jpg")
                cv2.imwrite(path, crop)
                saved_count += 1
        
        if saved_count == 0:
            return {"success": False, "message": "No valid faces detected in samples."}
            
        # 3. Retrain
        self.train_model()
        
        return {"success": True, "user_id": user_id, "faces_saved": saved_count}

    def identify_user(self, image_np: np.ndarray) -> Dict[str, Any]:
        """Identifies user using LBPH."""
        crop = self.detect_face_crop(image_np)
        if crop is None:
            return {"success": False, "message": "No face detected"}
            
        try:
            # Predict
            # LBPH returns (label, confidence). Confidence is Distance (Lower is better).
            # 0 is exact match. < 50 is good. > 80 is probably unknown.
            label, confidence = self.recognizer.predict(crop)
            
            if confidence < 70: # Threshold
                user = next((u for u in self.db.get_users() if str(u["id"]) == str(label)), None)
                if user:
                    return {
                        "success": True,
                        "user_id": user["id"],
                        "name": user["name"],
                        "confidence": confidence
                    }
            
            return {"success": False, "message": "User unknown", "confidence": confidence}
            
        except cv2.error:
            return {"success": False, "message": "Model not trained yet."}
