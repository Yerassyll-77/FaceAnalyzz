"""
Face analysis service using DeepFace library.
Analyzes facial expressions and computes stress level.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Suppress TensorFlow warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Stress weights: negative emotions contribute more to stress
STRESS_WEIGHTS = {
    "angry": 0.30,
    "disgust": 0.15,
    "fear": 0.25,
    "sad": 0.20,
    "surprise": 0.05,
    "happy": -0.15,
    "neutral": 0.0,
}


def _to_native(emotions: dict) -> dict:
    """Convert numpy float32 values to native Python float."""
    return {k: float(v) for k, v in emotions.items()}


def compute_stress_level(emotions: dict) -> float:
    """Compute stress level (0-100) from emotion probabilities (0-100 scale)."""
    stress = 0.0
    for emotion, weight in STRESS_WEIGHTS.items():
        stress += emotions.get(emotion, 0) * weight
    return round(max(0.0, min(100.0, stress)), 1)


def analyze_face(image_path: str) -> dict:
    """
    Analyze a face image and return emotion analysis results.

    Returns dict with keys:
        success, emotions, dominant_emotion, stress_level, confidence, error
    """
    try:
        from deepface import DeepFace

        # Try multiple detector backends — opencv is fastest, retinaface is most accurate
        detector_backends = ["opencv", "ssd", "mtcnn"]
        last_error = None

        for backend in detector_backends:
            try:
                results = DeepFace.analyze(
                    img_path=image_path,
                    actions=["emotion"],
                    enforce_detection=True,
                    detector_backend=backend,
                    silent=True,
                )

                if not results:
                    continue

                result = results[0] if isinstance(results, list) else results
                emotions = _to_native(result.get("emotion", {}))

                if not emotions:
                    continue

                dominant_emotion = result.get("dominant_emotion", max(emotions, key=emotions.get))
                stress_level = compute_stress_level(emotions)
                confidence = float(emotions.get(dominant_emotion, 0)) / 100

                return {
                    "success": True,
                    "emotions": emotions,
                    "dominant_emotion": dominant_emotion,
                    "stress_level": float(stress_level),
                    "confidence": float(confidence),
                }

            except ValueError:
                last_error = f"Backend {backend}: face not detected"
                continue
            except Exception as e:
                last_error = str(e)
                continue

        # If all backends failed, try once more with enforce_detection=False
        try:
            results = DeepFace.analyze(
                img_path=image_path,
                actions=["emotion"],
                enforce_detection=False,
                detector_backend="opencv",
                silent=True,
            )

            if results:
                result = results[0] if isinstance(results, list) else results
                emotions = _to_native(result.get("emotion", {}))
                if emotions:
                    dominant_emotion = result.get("dominant_emotion", max(emotions, key=emotions.get))
                    stress_level = compute_stress_level(emotions)
                    confidence = float(emotions.get(dominant_emotion, 0)) / 100
                    return {
                        "success": True,
                        "emotions": emotions,
                        "dominant_emotion": dominant_emotion,
                        "stress_level": float(stress_level),
                        "confidence": float(confidence),
                    }
        except Exception:
            pass

        return {
            "success": False,
            "error": "Bet tabilmady. Suretde bet anyqtalmady. Basqa suret salyp koriniz.",
        }

    except ImportError:
        return {
            "success": False,
            "error": "DeepFace kutaphanasy ornатylmagan. pip install deepface",
        }

    except Exception as e:
        logger.error(f"Face analysis error: {e}", exc_info=True)
        return {"success": False, "error": f"Taldau qatesi: {str(e)}"}


def analyze_face_array(np_image):
    """
    Live re3im u4in: numpy massivin qabyldap, fail saqtamai DeepFace-pen taldaidy.
    Tek opencv backend qoldanyladi (e3 zhyldam).
    """
    try:
        from deepface import DeepFace

        try:
            results = DeepFace.analyze(
                img_path=np_image,
                actions=["emotion"],
                enforce_detection=True,
                detector_backend="opencv",
                silent=True,
            )
        except ValueError:
            return {"success": False, "face_detected": False, "error": "Bet tabilmady"}

        if not results:
            return {"success": False, "face_detected": False, "error": "Bet tabilmady"}

        result = results[0] if isinstance(results, list) else results
        emotions = _to_native(result.get("emotion", {}))

        if not emotions:
            return {"success": False, "face_detected": False, "error": "Bet tabilmady"}

        dominant_emotion = result.get("dominant_emotion", max(emotions, key=emotions.get))
        stress_level = compute_stress_level(emotions)
        confidence = float(emotions.get(dominant_emotion, 0)) / 100

        # Bounding box (live oerlay u4in)
        region = result.get("region", {}) or {}
        face_box = {
            "x": int(region.get("x", 0)),
            "y": int(region.get("y", 0)),
            "w": int(region.get("w", 0)),
            "h": int(region.get("h", 0)),
        }

        return {
            "success": True,
            "face_detected": True,
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "stress_level": float(stress_level),
            "confidence": float(confidence),
            "face_box": face_box,
        }

    except ImportError:
        return {"success": False, "error": "DeepFace ornатylmagan"}
    except Exception as e:
        logger.error(f"Live analyze error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
