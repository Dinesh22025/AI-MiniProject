import base64
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import cv2
import numpy as np

# Try to import MediaPipe, fallback to OpenCV-only if it fails
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("MediaPipe not available, using OpenCV-only detection")


@dataclass
class VisionResult:
    status: str
    confidence: float
    head_tilt: float
    gaze_offset: float
    faces: int


class DriverMonitor:
    def __init__(self):
        # Always initialize OpenCV components
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
        
        # Try to initialize MediaPipe
        self.mesh = None
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                print("MediaPipe FaceMesh initialized successfully")
            except Exception as e:
                print(f"MediaPipe initialization failed: {e}")
                self.mesh = None
        
        # Counters for sustained detection
        self.drowsy_counter = 0
        self.yawn_counter = 0
        self.distraction_counter = 0
        self.normal_counter = 0

    @staticmethod
    def _decode_image(image_b64: str) -> np.ndarray:
        payload = image_b64.split(",")[-1]
        image_data = base64.b64decode(payload)
        np_img = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        return frame

    @staticmethod
    def _distance(a, b) -> float:
        if hasattr(a, 'x'):
            return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
        else:
            return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _analyze_with_opencv_only(self, frame) -> Dict:
        """Fallback analysis using only OpenCV"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            # Reset all counters when no face detected
            self.drowsy_counter = 0
            self.yawn_counter = 0
            self.distraction_counter = 0
            return {
                "status": "no_face_detected",
                "confidence": 0.8,
                "head_tilt": 0,
                "gaze_offset": 0,
                "faces": 0,
                "ear": 0,
                "mar": 0,
            }
        
        face = faces[0]
        
        # Estimate head tilt from face rectangle
        head_tilt = 0
        x, y, w, h = face
        aspect_ratio = w / h
        if aspect_ratio < 0.7 or aspect_ratio > 1.3:
            head_tilt = abs(1.0 - aspect_ratio) * 10
        
        # Estimate gaze from eye detection
        gaze_offset = 0
        if len(eyes) > 0:
            face_center_x = face[0] + face[2] // 2
            eye_positions = []
            for (ex, ey, ew, eh) in eyes:
                eye_center_x = ex + ew // 2
                eye_positions.append(eye_center_x)
            
            if eye_positions:
                avg_eye_x = sum(eye_positions) / len(eye_positions)
                gaze_offset = abs(avg_eye_x - face_center_x) / face[2] * 100
        
        # Improved state detection with proper priority
        status = "focused"
        confidence = 0.7
        
        # Priority 1: Drowsiness detection (no eyes detected for sustained period)
        if len(eyes) == 0:
            self.drowsy_counter += 1
            self.yawn_counter = 0  # Clear yawn counter when drowsy
            if self.drowsy_counter >= 4:
                status = "drowsy"
                confidence = 0.85
        else:
            self.drowsy_counter = max(0, self.drowsy_counter - 1)
        
        # Priority 2: Distraction detection (only if not drowsy)
        if status == "focused" and (head_tilt > 8 or gaze_offset > 20):
            self.distraction_counter += 1
            if self.distraction_counter >= 3:
                status = "distracted"
                confidence = 0.75
        else:
            self.distraction_counter = max(0, self.distraction_counter - 1)
        
        # Reset counters when focused
        if status == "focused":
            self.normal_counter += 1
            if self.normal_counter > 2:
                self.drowsy_counter = max(0, self.drowsy_counter - 1)
                self.yawn_counter = max(0, self.yawn_counter - 1)
                self.distraction_counter = max(0, self.distraction_counter - 1)
        else:
            self.normal_counter = 0
        
        # Estimate EAR and MAR for compatibility
        estimated_ear = 0.30 if len(eyes) > 0 else 0.15
        estimated_mar = 0.04
        
        return {
            "status": status,
            "confidence": round(float(confidence), 3),
            "head_tilt": round(float(head_tilt), 2),
            "gaze_offset": round(float(gaze_offset), 2),
            "faces": len(faces),
            "ear": estimated_ear,
            "mar": estimated_mar,
        }

    def _ear(self, landmarks, indices: Tuple[int, int, int, int, int, int]) -> float:
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in indices]
        return (self._distance(p2, p6) + self._distance(p3, p5)) / (2.0 * self._distance(p1, p4) + 1e-6)

    def _mar(self, landmarks) -> float:
        # More accurate mouth aspect ratio calculation
        upper_lip = [landmarks[13], landmarks[14], landmarks[15], landmarks[16], landmarks[17], landmarks[18]]
        lower_lip = [landmarks[402], landmarks[403], landmarks[404], landmarks[405], landmarks[406], landmarks[407]]
        left_corner = landmarks[61]
        right_corner = landmarks[291]
        
        vertical_dist = 0
        for i in range(len(upper_lip)):
            vertical_dist += self._distance(upper_lip[i], lower_lip[i])
        vertical_dist /= len(upper_lip)
        
        horizontal_dist = self._distance(left_corner, right_corner)
        return vertical_dist / (horizontal_dist + 1e-6)

    def _detect_yawn(self, landmarks, ear_value) -> Tuple[bool, float]:
        mar = self._mar(landmarks)
        
        # Get mouth landmarks for better yawn detection
        mouth_top = landmarks[13]  # Upper lip center
        mouth_bottom = landmarks[14]  # Lower lip center
        mouth_left = landmarks[61]  # Left mouth corner
        mouth_right = landmarks[291]  # Right mouth corner
        
        # Calculate mouth opening metrics
        mouth_height = self._distance(mouth_top, mouth_bottom)
        mouth_width = self._distance(mouth_left, mouth_right)
        mouth_aspect_ratio = mouth_height / (mouth_width + 1e-6)
        
        # Yawn detection: mouth must be significantly open AND eyes should be relatively open
        # This prevents drowsy (closed eyes) from being classified as yawning
        is_yawning = (
            mar > 0.08 and  # Mouth is open
            mouth_aspect_ratio > 0.5 and  # Mouth height vs width ratio
            ear_value > 0.25 and  # Eyes are NOT closed (prevents drowsy misclassification)
            self.drowsy_counter < 2  # Not currently drowsy
        )
        
        if is_yawning:
            self.yawn_counter += 1
            self.normal_counter = 0
        else:
            self.yawn_counter = max(0, self.yawn_counter - 1)
        
        return self.yawn_counter >= 2, mar

    def _detect_drowsiness(self, landmarks, eyes_detected) -> Tuple[bool, float]:
        # More precise eye landmarks for EAR calculation
        left_ear = self._ear(landmarks, (33, 160, 158, 133, 153, 144))
        right_ear = self._ear(landmarks, (362, 385, 387, 263, 373, 380))
        ear = (left_ear + right_ear) / 2.0
        
        # Stricter drowsiness detection to avoid false positives
        is_drowsy = ear < 0.25 or (ear < 0.28 and eyes_detected == 0)
        
        if is_drowsy:
            self.drowsy_counter += 1
            self.normal_counter = 0
            # Clear yawn counter when drowsy to prevent misclassification
            self.yawn_counter = 0
        else:
            self.drowsy_counter = max(0, self.drowsy_counter - 1)
        
        return self.drowsy_counter >= 3, ear

    def _detect_distraction(self, landmarks) -> Tuple[bool, float, float]:
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        nose = landmarks[1]
        
        head_tilt = abs(left_eye.y - right_eye.y)
        eye_center_x = (left_eye.x + right_eye.x) / 2.0
        gaze_offset = abs(eye_center_x - nose.x)
        
        is_distracted = gaze_offset > 0.08 or head_tilt > 0.07
        
        if is_distracted:
            self.distraction_counter += 1
            self.normal_counter = 0
        else:
            self.distraction_counter = max(0, self.distraction_counter - 1)
        
        return self.distraction_counter >= 4, head_tilt, gaze_offset

    def analyze(self, image_b64: str) -> Dict:
        frame = self._decode_image(image_b64)
        if frame is None:
            return {"status": "no_frame", "confidence": 0, "head_tilt": 0, "gaze_offset": 0, "faces": 0}

        try:
            # If MediaPipe is not available or failed to initialize, use OpenCV-only
            if self.mesh is None:
                return self._analyze_with_opencv_only(frame)
            
            # Try MediaPipe analysis
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mesh_result = self.mesh.process(rgb)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)

            if not mesh_result.multi_face_landmarks:
                self.drowsy_counter = 0
                self.yawn_counter = 0
                self.distraction_counter = 0
                return {
                    "status": "no_face_detected",
                    "confidence": 0.8,
                    "head_tilt": 0,
                    "gaze_offset": 0,
                    "faces": len(faces),
                    "ear": 0,
                    "mar": 0,
                }

            landmarks = mesh_result.multi_face_landmarks[0].landmark
            
            # First detect drowsiness and distraction
            is_drowsy, ear_value = self._detect_drowsiness(landmarks, len(eyes))
            is_distracted, head_tilt, gaze_offset = self._detect_distraction(landmarks)
            
            # Only check for yawning if NOT drowsy (prevents misclassification)
            is_yawning, mar_value = self._detect_yawn(landmarks, ear_value)

            status = "focused"
            confidence = 0.9

            # Priority order: Drowsiness > Distraction > Yawning > Focused
            if is_drowsy:
                status = "drowsy"
                confidence = min(1.0, (0.30 - ear_value) * 8)
                self.normal_counter = 0
                # Don't reset yawn counter here, let it decay naturally
                self.distraction_counter = max(0, self.distraction_counter - 1)
                print(f"DEBUG: Drowsy detected - EAR: {ear_value:.3f}, Counter: {self.drowsy_counter}")
            elif is_distracted:
                status = "distracted"
                confidence = min(1.0, (gaze_offset + head_tilt) * 8)
                self.normal_counter = 0
                # Reduce other counters when distracted
                self.yawn_counter = max(0, self.yawn_counter - 1)
                print(f"DEBUG: Distracted - Gaze: {gaze_offset:.3f}, Tilt: {head_tilt:.3f}")
            elif is_yawning and not is_drowsy:  # Only yawn if not drowsy
                status = "yawning"
                confidence = min(1.0, mar_value * 8)
                self.normal_counter = 0
                print(f"DEBUG: Yawning detected - MAR: {mar_value:.3f}, EAR: {ear_value:.3f}, Counter: {self.yawn_counter}")
            else:
                self.normal_counter += 1
                if self.normal_counter > 2:
                    # Gradually reset all counters when focused
                    self.drowsy_counter = max(0, self.drowsy_counter - 1)
                    self.yawn_counter = max(0, self.yawn_counter - 1)
                    self.distraction_counter = max(0, self.distraction_counter - 1)

            return {
                "status": status,
                "confidence": round(float(confidence), 3),
                "head_tilt": round(float(head_tilt * 100), 2),
                "gaze_offset": round(float(gaze_offset * 100), 2),
                "faces": int(len(faces) or 1),
                "ear": round(float(ear_value), 3),
                "mar": round(float(mar_value), 3),
            }
            
        except Exception as e:
            print(f"MediaPipe analysis failed, falling back to OpenCV: {e}")
            # Fallback to OpenCV-only analysis
            return self._analyze_with_opencv_only(frame)
