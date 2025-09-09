import cv2
from insightface.app import FaceAnalysis

# Initialize the model once (global variable to avoid reloading)
app = None


def init_quality_checker():
    """Initialize the face analysis model once"""
    global app
    if app is None:
        app = FaceAnalysis(name="buffalo_l")
        app.prepare(ctx_id=0, det_size=(640, 640))
        print("✅ Quality checker initialized")


def check_face_quality(image, quality_threshold=0.6):
    """
    Check if a face image meets quality threshold

    Args:
        image: OpenCV image (numpy array) - can be face crop or full frame
        quality_threshold: Minimum quality score (0-1)

    Returns:
        tuple: (is_good_quality: bool, quality_score: float)
        - is_good_quality: True if quality >= threshold
        - quality_score: Face detection confidence (0-1), 0.0 if no face found
    """
    global app

    # Initialize if not already done
    if app is None:
        init_quality_checker()

    # Get faces from image
    faces = app.get(image)

    if not faces:
        return False, 0.0

    # Take the first detected face
    face = faces[0]
    score = face.det_score

    # Check if quality meets threshold
    is_good = score >= quality_threshold
    print("good for save it or no: ",is_good)
    return is_good, score

