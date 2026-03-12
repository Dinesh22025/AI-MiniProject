#!/usr/bin/env python3
"""
Test script to verify the vision detection improvements
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from vision import DriverMonitor
import cv2
import base64

def test_vision_detection():
    print("Testing Vision Detection System...")
    print("=" * 50)
    
    # Initialize the monitor
    monitor = DriverMonitor()
    
    # Test with webcam if available
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No webcam found. Please connect a webcam to test.")
            return
        
        print("✅ Webcam detected. Starting real-time analysis...")
        print("📋 Detection Priority: Drowsy → Distracted → Yawning → Focused")
        print("🔍 EAR < 0.25 = Drowsy | MAR > 0.08 + Eyes Open = Yawn")
        print("👀 Gaze > 8% or Tilt > 7% = Distracted")
        print("\nPress 'q' to quit, 's' to see current status")
        print("-" * 50)
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            frame_count += 1
            
            # Convert frame to base64 (same as frontend)
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode()
            
            # Analyze frame
            result = monitor.analyze(frame_b64)
            
            # Display results every 30 frames (roughly 1 second at 30fps)
            if frame_count % 30 == 0:
                status = result['status']
                confidence = result['confidence']
                ear = result['ear']
                mar = result['mar']
                
                # Color coding for status
                status_color = {
                    'focused': '🟢',
                    'drowsy': '🔴',
                    'yawning': '🟡',
                    'distracted': '🟠',
                    'no_face_detected': '⚪'
                }.get(status, '⚫')
                
                print(f"{status_color} Status: {status.upper()} | "
                      f"Confidence: {confidence:.2f} | "
                      f"EAR: {ear:.3f} | "
                      f"MAR: {mar:.3f} | "
                      f"Faces: {result['faces']}")
            
            # Show video feed
            cv2.putText(frame, f"Status: {result['status']}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"EAR: {result['ear']:.3f}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"MAR: {result['mar']:.3f}", (10, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Driver Monitor Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print(f"\n📊 Current Analysis:")
                print(f"   Status: {result['status']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   EAR: {result['ear']:.3f}")
                print(f"   MAR: {result['mar']:.3f}")
                print(f"   Head Tilt: {result['head_tilt']:.2f}°")
                print(f"   Gaze Offset: {result['gaze_offset']:.2f}%")
                print(f"   Faces Detected: {result['faces']}")
                print("-" * 30)
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_detection()