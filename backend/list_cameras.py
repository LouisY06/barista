#!/usr/bin/env python3
"""
List all available cameras and test them.
"""

import cv2

def list_cameras():
    """List all available camera indices."""
    print("=" * 60)
    print("SCANNING FOR AVAILABLE CAMERAS...")
    print("=" * 60)
    
    available_cameras = []
    
    # Test cameras 0-10
    for i in range(11):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                available_cameras.append({
                    'index': i,
                    'width': width,
                    'height': height,
                    'fps': fps
                })
                
                print(f"✓ Camera {i}: {width}x{height} @ {fps:.1f} fps")
                
                # Save a test frame to identify
                cv2.imwrite(f'camera_{i}_test.jpg', frame)
                print(f"  → Saved test image: camera_{i}_test.jpg")
            cap.release()
    
    print("\n" + "=" * 60)
    print(f"Found {len(available_cameras)} camera(s)")
    print("=" * 60)
    
    if len(available_cameras) == 0:
        print("\n❌ No cameras found!")
        print("\n💡 To use iPhone as camera:")
        print("   1. Connect iPhone to Mac via USB")
        print("   2. On iPhone: Settings > Face ID & Passcode > Allow Accessories When Locked")
        print("   3. Or use Continuity Camera (wireless):")
        print("      - Make sure iPhone and Mac are on same WiFi")
        print("      - On Mac: System Settings > Camera > Allow iPhone to connect")
        print("   4. Or use apps like EpocCam, Camo, or DroidCam")
    else:
        print("\n📸 To use iPhone:")
        print("   1. Check the test images (camera_X_test.jpg) to identify which is your iPhone")
        print("   2. Note the camera index number")
        print("   3. Use that index in the depth script")
    
    return available_cameras

if __name__ == "__main__":
    cameras = list_cameras()


