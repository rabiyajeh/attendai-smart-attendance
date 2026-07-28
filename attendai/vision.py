from pathlib import Path
import numpy as np
from cryptography.fernet import Fernet
from .database import DATA_DIR

try:
    import cv2
    CV_IMPORT_ERROR = None
    CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
except (ImportError, OSError) as error:
    cv2 = None
    CV_IMPORT_ERROR = str(error)
    CASCADE = EYE_CASCADE = None

def cv_available():
    return cv2 is not None and CASCADE is not None and not CASCADE.empty()

def _cipher():
    DATA_DIR.mkdir(exist_ok=True)
    key_path = DATA_DIR / "embedding.key"
    if not key_path.exists():
        key_path.write_bytes(Fernet.generate_key())
    return Fernet(key_path.read_bytes())

def decode_image(file_bytes: bytes):
    if not cv_available():
        raise RuntimeError(f"OpenCV is unavailable: {CV_IMPORT_ERROR or 'classifier data could not be loaded'}")
    return cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)

def detect_and_embed(image):
    if not cv_available():
        return None, {"ok": False, "message": f"OpenCV is unavailable: {CV_IMPORT_ERROR or 'classifier data could not be loaded'}"}
    if image is None:
        return None, {"ok": False, "message": "Invalid image."}
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    faces = CASCADE.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=6, minSize=(90, 90))
    if len(faces) != 1:
        return None, {"ok": False, "message": "Show exactly one clearly visible face.", "faces": len(faces)}
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    if brightness < 45 or brightness > 220:
        return None, {"ok": False, "message": "Lighting is too dark or too bright."}
    if blur < 45:
        return None, {"ok": False, "message": "Image is blurry. Hold still and try again."}
    face = gray[y:y+h, x:x+w]
    eyes = EYE_CASCADE.detectMultiScale(face, scaleFactor=1.1, minNeighbors=5, minSize=(18, 18))
    normalized = cv2.equalizeHist(cv2.resize(face, (64, 64)))
    dct = cv2.dct(normalized.astype(np.float32) / 255.0)[:24, :24].flatten()
    dct /= np.linalg.norm(dct) + 1e-9
    quality = min(1.0, (blur / 300.0) * 0.55 + (1 - abs(brightness - 128) / 128) * 0.45)
    info = {"ok": True, "quality": quality, "brightness": brightness, "blur": blur,
            "eyes": len(eyes), "box": (int(x), int(y), int(w), int(h))}
    return dct.astype(np.float32), info

def encrypt_embedding(vector):
    return _cipher().encrypt(vector.tobytes())

def decrypt_embedding(payload):
    return np.frombuffer(_cipher().decrypt(payload), dtype=np.float32)

def similarity(a, b):
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9))

def annotate(image, box, label, color=(20, 190, 125)):
    x, y, w, h = box
    result = image.copy()
    cv2.rectangle(result, (x, y), (x+w, y+h), color, 3)
    cv2.rectangle(result, (x, max(0, y-30)), (x+w, y), color, -1)
    cv2.putText(result, label, (x+5, max(18, y-8)), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,255,255), 2)
    return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
