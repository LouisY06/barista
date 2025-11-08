"""
Test script to use laptop camera for object detection.

This script captures frames from your laptop camera and sends them to the backend
for YOLOv11 object detection, displaying the results in real-time.
"""

import cv2
import requests
import base64
import json
import numpy as np
from typing import Optional

# Backend URL
BACKEND_URL = "http://localhost:5001/api"


def capture_frame(camera):
    """Capture a frame from the camera."""
    ret, frame = camera.read()
    if not ret:
        return None
    return frame


def frame_to_base64(frame):
    """Convert OpenCV frame to base64 string."""
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{frame_base64}"


def detect_objects_in_frame(frame, endpoint="robot/detect-objects", confidence=0.25, object_type="all"):
    """
    Send frame to backend for object detection.
    
    Args:
        frame: OpenCV frame (numpy array)
        endpoint: API endpoint ('robot/find-cup' or 'robot/detect-objects')
        confidence: Confidence threshold
        object_type: Type of object ('cup', 'all')
        
    Returns:
        Detection results or None
    """
    try:
        # Convert frame to base64
        frame_base64 = frame_to_base64(frame)
        
        # Send to backend
        if endpoint == "robot/detect-objects":
            url = f"{BACKEND_URL}/{endpoint}?confidence={confidence}&object_type={object_type}"
        else:
            url = f"{BACKEND_URL}/{endpoint}?confidence={confidence}"
        
        response = requests.post(
            url,
            json={'image': frame_base64},
            timeout=10  # Increased timeout for model inference
        )
        
        if response.status_code == 200:
            result = response.json()
            # Debug: print what was detected
            if endpoint == "robot/detect-objects" and result.get('count', 0) > 0:
                print(f"Detected {result['count']} objects: {[obj['class_name'] for obj in result.get('objects', [])]}")
            return result
        elif response.status_code == 404 and endpoint == "robot/find-cup":
            # No cup found is expected sometimes
            return {'found': False}
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error detecting objects: {e}")
        import traceback
        traceback.print_exc()
        return None


def draw_detections(frame, detections, endpoint="robot/detect-objects"):
    """Draw detection results on frame."""
    if endpoint == "robot/find-cup":
        if detections and detections.get('found'):
            center = detections['center']
            bbox = detections['bbox']
            confidence = detections.get('confidence', 0)
            
            # Draw bounding box
            x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw center point
            cx, cy = center['x'], center['y']
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            
            # Draw label
            label = f"Cup ({confidence:.2f})"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            # No cup found
            cv2.putText(frame, "No cup detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    elif endpoint == "robot/detect-objects":
        if detections and detections.get('detections_found'):
            for obj in detections.get('objects', []):
                if 'bbox' in obj and 'center' in obj:
                    bbox = obj['bbox']
                    x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw center point
                    center = obj['center']
                    cv2.circle(frame, (center['x'], center['y']), 5, (0, 0, 255), -1)
                    
                    label = f"{obj['class_name']} ({obj['confidence']:.2f})"
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        elif detections and detections.get('count', 0) == 0:
            # No objects detected
            cv2.putText(frame, "No objects detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame


def main():
    """Main function to run camera detection."""
    print("Starting camera detection test...")
    print("Controls:")
    print("  'q' - Quit")
    print("  'c' - Cup detection mode (filters for cups only)")
    print("  'a' - All objects mode (shows everything YOLOv11 detects)")
    print("  '+' - Increase confidence threshold")
    print("  '-' - Decrease confidence threshold (recommended if nothing detected)")
    print("  SPACE - Toggle detection on/off")
    
    # Initialize camera - try different indices
    camera = None
    print("Searching for camera...")
    for i in range(3):
        print(f"Trying camera index {i}...")
        test_camera = cv2.VideoCapture(i)
        if test_camera.isOpened():
            ret, frame = test_camera.read()
            if ret and frame is not None:
                camera = test_camera
                print(f"✅ Camera {i} opened successfully!")
                break
            else:
                test_camera.release()
        else:
            test_camera.release()
    
    if camera is None:
        print("❌ Error: Could not open any camera")
        print("Possible issues:")
        print("  - Camera permissions not granted")
        print("  - Camera is being used by another app")
        print("  - No camera connected")
        print("\nOn macOS, check System Settings > Privacy & Security > Camera")
        return
    
    # Set camera resolution (optional)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Detection settings
    endpoint = "robot/detect-objects"  # Start with all objects to see what's detected
    object_type = "all"  # or "cup"
    confidence = 0.25  # Lower confidence to catch more objects
    detection_enabled = True
    frame_skip = 2  # Process every Nth frame to reduce load
    frame_count = 0
    
    print(f"\nMode: {endpoint} (object_type: {object_type})")
    print(f"Confidence: {confidence}")
    print("Starting detection...")
    print("TIP: If nothing is detected, try:")
    print("  - Lower confidence with '-' key")
    print("  - Switch to 'all objects' mode with 'a' key")
    print("  - Make sure objects are clearly visible in frame\n")
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame_count += 1
            
            # Process every Nth frame
            if detection_enabled and frame_count % frame_skip == 0:
                detections = detect_objects_in_frame(frame, endpoint, confidence, object_type)
                if detections:
                    frame = draw_detections(frame, detections, endpoint)
            
            # Display info
            info_text = [
                f"Mode: {endpoint} ({object_type})",
                f"Confidence: {confidence:.2f}",
                f"Detection: {'ON' if detection_enabled else 'OFF'}",
                "Press 'q' to quit, 'c' for cup, 'a' for all, '+/-' for confidence"
            ]
            y_offset = 20
            for i, text in enumerate(info_text):
                cv2.putText(frame, text, (10, y_offset + i * 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Resize if too large for display
            display_frame = frame.copy()
            height, width = display_frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_frame = cv2.resize(display_frame, (new_width, new_height))
            
            cv2.imshow('Barista Robot - Object Detection', display_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(30) & 0xFF  # Increased wait time for better responsiveness
            if key == ord('q'):
                break
            elif key == ord('c'):
                endpoint = "robot/detect-objects"
                object_type = "cup"
                print(f"Switched to cup detection mode")
            elif key == ord('a'):
                endpoint = "robot/detect-objects"
                object_type = "all"
                print(f"Switched to all objects detection mode")
            elif key == ord('+') or key == ord('='):
                confidence = min(0.95, confidence + 0.05)
                print(f"Confidence: {confidence:.2f}")
            elif key == ord('-') or key == ord('_'):
                confidence = max(0.1, confidence - 0.05)
                print(f"Confidence: {confidence:.2f}")
            elif key == ord(' '):
                detection_enabled = not detection_enabled
                print(f"Detection: {'ON' if detection_enabled else 'OFF'}")
    
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released. Goodbye!")


if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/api/health", timeout=2)
        if response.status_code == 200:
            print("Backend is running!")
        else:
            print("Warning: Backend may not be running properly")
    except Exception as e:
        print(f"Warning: Could not connect to backend: {e}")
        print("Make sure the backend server is running on http://localhost:5001")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            exit(1)
    
    main()

