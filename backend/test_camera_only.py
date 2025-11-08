"""
Simple camera test - just to verify camera access works.
"""

import cv2
import sys

def test_camera():
    """Test if we can access the camera."""
    print("Testing camera access...")
    print("=" * 50)
    
    # Try different camera indices
    for i in range(5):
        print(f"\nTrying camera index {i}...")
        camera = cv2.VideoCapture(i)
        
        if not camera.isOpened():
            print(f"  ❌ Camera {i}: Could not open")
            camera.release()
            continue
        
        # Try to read a frame
        ret, frame = camera.read()
        
        if not ret:
            print(f"  ❌ Camera {i}: Opened but cannot read frames")
            camera.release()
            continue
        
        if frame is None:
            print(f"  ❌ Camera {i}: Frame is None")
            camera.release()
            continue
        
        # Success!
        print(f"  ✅ Camera {i}: SUCCESS!")
        print(f"     Frame shape: {frame.shape}")
        print(f"     Frame size: {frame.shape[1]}x{frame.shape[0]}")
        
        # Try to display it
        print(f"     Attempting to display frame (press 'q' to quit)...")
        cv2.imshow(f'Camera {i} Test', frame)
        
        # Wait a bit
        key = cv2.waitKey(2000) & 0xFF
        cv2.destroyAllWindows()
        
        if key == ord('q'):
            break
        
        # Keep this camera for further testing
        print(f"\n✅ Camera {i} is working! You can use this camera.")
        camera.release()
        return i
    
    print("\n" + "=" * 50)
    print("❌ No working camera found!")
    print("\nTroubleshooting:")
    print("1. Check macOS camera permissions:")
    print("   System Settings > Privacy & Security > Camera")
    print("   Make sure Terminal (or your IDE) has camera access")
    print("\n2. Check if camera is being used by another app")
    print("   (Zoom, FaceTime, Photo Booth, etc.)")
    print("\n3. Try restarting your computer")
    print("\n4. On macOS, you may need to grant camera access")
    print("   when the permission dialog appears")
    
    return None

if __name__ == "__main__":
    print("Camera Diagnostic Test")
    print("=" * 50)
    print("This will test all available camera indices")
    print("=" * 50)
    
    working_camera = test_camera()
    
    if working_camera is not None:
        print(f"\n✅ Use camera index {working_camera} in your scripts!")
    else:
        print("\n❌ Camera access failed. Please check permissions.")
        sys.exit(1)

