#!/usr/bin/env python3
"""
Quick camera diagnostic to check what each camera sees.
"""

import cv2
import time

def test_camera(camera_idx):
    """Test a single camera and save what it sees."""
    print(f"\nTesting camera {camera_idx}...")
    
    cap = cv2.VideoCapture(camera_idx)
    
    if not cap.isOpened():
        print(f"  ❌ Camera {camera_idx} could not be opened")
        return None
    
    # Get camera properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"  ✓ Camera {camera_idx} opened successfully")
    print(f"    Resolution: {int(width)}x{int(height)}")
    print(f"    FPS: {fps}")
    
    # Warm up the camera (let auto-exposure adjust)
    print(f"  Warming up camera {camera_idx} (capturing 10 frames)...")
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            # Check brightness
            if frame is not None and frame.size > 0:
                brightness = frame.mean()
                print(f"    Frame {i+1}: brightness = {brightness:.1f}")
        time.sleep(0.1)
    
    # Capture final frame
    ret, frame = cap.read()
    
    cap.release()
    
    if not ret or frame is None:
        print(f"  ❌ Failed to capture from camera {camera_idx}")
        return None
    
    # Save the frame
    filename = f"camera_{camera_idx}_test.jpg"
    cv2.imwrite(filename, frame)
    
    # Calculate statistics
    brightness = frame.mean()
    print(f"  Final brightness: {brightness:.1f}")
    print(f"  Saved to: {filename}")
    
    if brightness < 5:
        print(f"  ⚠️  WARNING: Camera {camera_idx} image is very dark (brightness < 5)")
        print(f"      - Check if lens cap is on")
        print(f"      - Check if camera is pointing at something dark")
        print(f"      - Try adjusting lighting")
    
    return frame

def main():
    print("=" * 60)
    print("Camera Diagnostic Tool")
    print("=" * 60)
    
    # Test cameras 0 and 1
    frame0 = test_camera(0)
    frame1 = test_camera(1)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if frame0 is not None:
        print(f"✓ Camera 0: OK (brightness: {frame0.mean():.1f})")
    else:
        print(f"✗ Camera 0: FAILED")
    
    if frame1 is not None:
        print(f"✓ Camera 1: OK (brightness: {frame1.mean():.1f})")
    else:
        print(f"✗ Camera 1: FAILED")
    
    if frame0 is not None and frame1 is not None:
        print(f"\n✓ Both cameras working!")
        print(f"  Check camera_0_test.jpg and camera_1_test.jpg")
        
        # Check if they're similar (might be same camera)
        diff = cv2.absdiff(frame0, frame1).mean()
        print(f"\nDifference between cameras: {diff:.1f}")
        if diff < 10:
            print("  ⚠️  WARNING: Cameras appear very similar - might be the same camera!")
        else:
            print("  ✓ Cameras show different views")

if __name__ == "__main__":
    main()


