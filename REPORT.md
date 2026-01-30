# Face Authentication System Report

## Model and Approach
We utilize a robust and lightweight approach for face authentication:

1.  **Face Recognition (LBPH)**: 
    - We use the **Local Binary Patterns Histograms (LBPH)** algorithm provided by OpenCV.
    - **Why LBPH?**: Unlike Deep Learning methods (ResNet/dlib) which require heavy dependencies and GPU acceleration for speed, LBPH is efficient, works well on CPUs, and is robust against local monotonic grayscale transformations.
    - **Training**: The model is "trained" on a set of ~10 images per user, creating histograms of local texture patterns.

2.  **Liveness Detection (Spoof Prevention)**:
    - We use **MediaPipe Face Mesh** to estimate the **Eye Aspect Ratio (EAR)**.
    - The system ensures the user is "live" by checking if eyes are open (and can be extended to detect blinks). This prevents static photo attacks.

3.  **Lighting Handling**:
    - **CLAHE**: We preprocess images using Contrast Limited Adaptive Histogram Equalization. This normalizes the lighting, allowing the system to work in dim or unevenly lit environments.

## Training Process
- **Registration**: When a user registers, the system captures a "burst" of 10 images in 2-3 seconds.
- **Preprocessing**: Each image is converted to grayscale and cropped to the face region using Haar Cascades.
- **Model Update**: The LBPH model is retrained with the new data + existing data and saved to `data/trainer.yml`.

## Accuracy Expectations
- **Ideal Conditions**: 90-95% accuracy.
- **LBPH Characteristics**: Good at rejecting strangers (high distance). Identify might fluctuate if lighting changes drastically compared to training, but CLAHE mitigates this.

## Known Failure Cases
1.  **Face Not Detected**: If the user is too far or backlighting is too strong.
2.  **Closed Eyes**: Liveness check will block authentication if eyes are closed (or if glasses obscure eyes).
3.  **Drastic Appearance Changes**: Beard/Glasses might require re-registration for best results with LBPH.
