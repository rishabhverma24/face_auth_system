# Face Authentication Attendance System Documentation

## 1. Model and Approach Used

This project implements a localized face authentication system combining **Computer Vision** and **Machine Learning** techniques to ensure speed, privacy, and offline capability.

### Core Components
*   **Face Detection**: Uses **Haar Cascade Classifiers** (OpenCV) for detecting face regions in real-time. This technique was chosen for its speed and low computational cost, making it suitable for standard CPUs.
*   **Face Recognition**: Uses the **LBPH (Local Binary Patterns Histograms)** algorithm from `opencv-contrib-python`.
    *   *Why LBPH?* Unlike Deep Learning models (like FaceNet) that require massive datasets and GPUs, LBPH works well with small datasets (even 10-20 images per user) and is robust to local lighting changes. It learns the texture of the face rather than just geometric features.
*   **Liveness Detection (Spoof Prevention)**: Uses **Google MediaPipe Face Landmarker**.
    *   The system creates a dense 3D facial mesh (478 landmarks) to analyze facial geometry.
    *   It specifically calculates the **Eye Aspect Ratio (EAR)** to ensure the user's eyes are open and looking at the camera, distinguishing valid users from accidental captures or inanimate objects.

## 2. Training Process

The system follows a simple "Register -> Train -> Recognize" workflow:

1.  **Data Collection**:
    *   When a new user registers, the system captures a series of images (e.g., 30 frames) from the webcam.
    *   Each frame is processed to detect the face, crop it to the region of interest, and convert it to grayscale.
    *   These samples are saved in `data/faces/<user_id>/`.
2.  **Model Training**:
    *   The `FaceAuthSystem.train_model()` method reads all saved face samples.
    *   It computes the LBP histograms for every image and associates them with the User ID.
    *   The trained model state is serialized and saved to `data/trainer.yml`.
3.  **Inference**:
    *   The system loads `trainer.yml` at startup.
    *   Live frames are processed to extract face histograms, which are compared against the stored histograms using Chi-square distance.

## 3. Accuracy Expectations

*   **Recognition Accuracy**: ~85-95% under controlled lighting conditions with registered users.
*   **False Acceptance Rate (FAR)**: Low. The system uses a strict confidence threshold (distance < 70) to prevent unauthorized access.
*   **Performance**: Real-time processing (~15-30 FPS) on standard CPU hardware.

## 4. Known Failure Cases & Limitations

*   **Lighting conditions**: Extreme backlighting or very low light can prevent Haar Cascades from detecting the face, or cause LBPH to misclassify due to shadow textures.
*   **Occlusions**: Heavy glasses, face masks, or hair covering the eyes will fail the Liveness Detection (EAR check) or reduce recognition accuracy.
*   **Extreme Angles**: The system is trained primarily on frontal faces. Profile views (side faces) may not be recognized.
*   **Spoofing**:
    *   *Basic Protection*: The system rejects objects that strictly do not match human facial geometry (via MediaPipe).
    *   *Limitation*: High-quality printed photos or video replays with open eyes might still pass the basic "eyes open" check. Advanced liveness (e.g., blink detection, smile challenge) would be needed for higher security.
