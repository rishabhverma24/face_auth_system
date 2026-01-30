// Common JS for Face Auth App

let videoStream = null;

async function startCamera() {
    const video = document.getElementById('video');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('#cam-status'); // Only on index

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = videoStream;
        
        if (statusDot) statusDot.classList.add('active');
        if (statusText) statusText.textContent = "Camera Active";
        
    } catch (err) {
        console.error("Error accessing camera:", err);
        if (statusText) statusText.textContent = "Camera Error";
        showMessage("Could not access camera. Please allow permissions.", "error");
    }
}

function captureImage() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    if (!videoStream) {
        showMessage("Camera not started", "error");
        return null;
    }
    
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    return canvas.toDataURL('image/jpeg', 0.8);
}

function showMessage(msg, type) {
    const el = document.getElementById('message');
    el.textContent = msg;
    el.style.color = type === 'error' ? 'var(--error)' : (type === 'success' ? 'var(--accent)' : 'var(--text-main)');
    
    // Pulse effect
    el.classList.remove('pulse');
    void el.offsetWidth; // trigger reflow
    el.classList.add('pulse');
}
