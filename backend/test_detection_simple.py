"""
Simple test script to debug object detection.
Takes a single photo and shows what YOLOv11 detects.
"""

import cv2
import requests
import base64
import json

BACKEND_URL = "http://localhost:5001/api"

def test_detection():
    """Test detection with a single camera frame."""
    print("Opening camera...")
    
    # Try different camera indices (0, 1, 2)
    camera = None
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
    
    print("=" * 60)
    print("CONTROLS:")
    print("  SPACE or ENTER - Capture frame for detection")
    print("  'a' - Auto-capture mode (captures every 2 seconds)")
    print("  'q' or ESC - Quit")
    print("=" * 60)
    print("\nMake sure the camera window has focus!")
    
    frame_count = 0
    auto_capture = False
    last_capture_time = 0
    
    while True:
        ret, frame = camera.read()
        if not ret:
            print(f"Failed to grab frame (attempt {frame_count})")
            frame_count += 1
            if frame_count > 10:
                print("Too many failed attempts. Exiting.")
                break
            continue
        
        frame_count = 0  # Reset on success
        
        # Resize if too large
        height, width = frame.shape[:2]
        if width > 1280:
            scale = 1280 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Add text overlay
        display_frame = frame.copy()
        cv2.putText(display_frame, "Press SPACE/ENTER to capture, 'a' for auto, 'q' to quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if auto_capture:
            cv2.putText(display_frame, "AUTO-CAPTURE MODE", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Camera - Press SPACE/ENTER to capture, Q to quit', display_frame)
        
        import time
        current_time = time.time()
        should_capture = False
        
        key = cv2.waitKey(30) & 0xFF  # Increased wait time
        
        if key == ord('q') or key == 27:  # 'q' or ESC
            print("Quitting...")
            break
        elif key == ord('a'):
            auto_capture = not auto_capture
            print(f"Auto-capture: {'ON' if auto_capture else 'OFF'}")
        elif key == ord(' ') or key == 13:  # SPACE or ENTER
            should_capture = True
            print("\n📸 Manual capture triggered!")
        elif auto_capture and (current_time - last_capture_time) >= 2.0:
            should_capture = True
            print("\n📸 Auto-capture triggered!")
        
        if should_capture:
            print(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
            last_capture_time = current_time
            
            # Convert to base64
            print("Encoding image...")
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            image_data = f"data:image/jpeg;base64,{frame_base64}"
            print(f"Image encoded: {len(image_data)} characters")
            
            # Test with very low confidence to see everything
            print("Sending to backend (confidence=0.1)...")
            url = f"{BACKEND_URL}/robot/detect-objects?confidence=0.1&object_type=all"
            
            try:
                response = requests.post(
                    url,
                    json={'image': image_data},
                    timeout=20
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    count = result.get('count', 0)
                    print(f"\n{'='*60}")
                    print(f"✅ Detection successful!")
                    print(f"{'='*60}")
                    print(f"Found {count} objects:\n")
                    
                    if count > 0:
                        for i, obj in enumerate(result.get('objects', []), 1):
                            print(f"  {i}. {obj['class_name']} (confidence: {obj['confidence']:.2f})")
                            if 'center' in obj:
                                print(f"     Center: ({obj['center']['x']}, {obj['center']['y']})")
                    else:
                        print("  ⚠️  No objects detected.")
                        print("\n  Suggestions:")
                        print("  - Make sure objects are clearly visible in frame")
                        print("  - Try pointing at common objects (cup, bottle, person, etc.)")
                        print("  - Check backend is running: curl http://localhost:5001/api/health")
                elif response.status_code == 403:
                    print(f"\n❌ Error 403: Backend rejected request")
                    print("  Backend might not be running or CORS issue")
                    print("  Check: curl http://localhost:5001/api/health")
                else:
                    print(f"\n❌ Error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"\n❌ Connection Error: Backend not running!")
                print("  Start backend: cd backend && python -m app.main")
                print("  (Backend should be on port 5001)")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n{'='*60}")
            if auto_capture:
                print("Auto-capture mode: Next capture in 2 seconds...")
            else:
                print("Press SPACE/ENTER to capture again, 'a' for auto, 'q' to quit")
            print(f"{'='*60}\n")
    
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Check backend
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print("⚠️  Backend may not be running properly")
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        print("Make sure the backend server is running on http://localhost:5001")
        exit(1)
    
    test_detection()

