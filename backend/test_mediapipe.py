#!/usr/bin/env python3

import sys
import traceback

def test_mediapipe():
    try:
        print("Testing MediaPipe installation...")
        import mediapipe as mp
        print("[OK] MediaPipe imported successfully")
        
        print("Testing FaceMesh initialization...")
        mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        print("[OK] FaceMesh initialized successfully")
        
        print("Testing OpenCV...")
        import cv2
        print("[OK] OpenCV imported successfully")
        
        print("Testing face cascade...")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        print("[OK] Face cascade loaded successfully")
        
        print("\nSUCCESS: All components working! Backend should work now.")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_mediapipe()
    sys.exit(0 if success else 1)