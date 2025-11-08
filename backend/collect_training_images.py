"""
Helper script to collect training images for custom model.

This script helps you capture and organize images for training.
"""

import cv2
import os
from pathlib import Path
import time

def collect_images(class_name: str, output_dir: str = "training_images", num_images: int = 100):
    """
    Collect images for a specific class.
    
    Args:
        class_name: Name of the class (e.g., "espresso_cup")
        output_dir: Directory to save images
        num_images: Number of images to collect
    """
    # Create output directory
    class_dir = Path(output_dir) / class_name
    class_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"Collecting images for: {class_name}")
    print(f"Target: {num_images} images")
    print(f"Output: {class_dir}")
    print("=" * 60)
    print("\nControls:")
    print("  SPACE/ENTER - Capture image")
    print("  's' - Skip (don't save)")
    print("  'q' - Quit")
    print("\nTips:")
    print("  - Vary angles and positions")
    print("  - Try different lighting")
    print("  - Include different backgrounds")
    print("=" * 60)
    
    # Open camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera")
        return
    
    captured = 0
    skipped = 0
    
    while captured < num_images:
        ret, frame = camera.read()
        if not ret:
            continue
        
        # Resize for display
        display_frame = frame.copy()
        height, width = display_frame.shape[:2]
        if width > 1280:
            scale = 1280 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        # Add info overlay
        info_text = [
            f"Class: {class_name}",
            f"Captured: {captured}/{num_images}",
            f"Skipped: {skipped}",
            "",
            "SPACE/ENTER - Capture",
            "'s' - Skip",
            "'q' - Quit"
        ]
        
        y_offset = 30
        for i, text in enumerate(info_text):
            cv2.putText(display_frame, text, (10, y_offset + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow(f'Collecting: {class_name}', display_frame)
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q'):
            print("\nStopping collection...")
            break
        elif key == ord(' ') or key == 13:  # SPACE or ENTER
            # Save image
            timestamp = int(time.time() * 1000)
            filename = f"{class_name}_{timestamp:013d}.jpg"
            filepath = class_dir / filename
            
            cv2.imwrite(str(filepath), frame)
            captured += 1
            print(f"✅ Saved: {filename} ({captured}/{num_images})")
        elif key == ord('s'):
            skipped += 1
            print(f"⏭️  Skipped ({skipped} total)")
    
    camera.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    print(f"Collection complete!")
    print(f"  Captured: {captured} images")
    print(f"  Skipped: {skipped} images")
    print(f"  Location: {class_dir}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Label these images with LabelImg or Roboflow")
    print("2. Organize into train/val folders")
    print("3. Create dataset.yaml file")
    print("4. Train model: python train_custom_model.py --data dataset.yaml")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect training images')
    parser.add_argument('--class', type=str, required=True,
                       dest='class_name',
                       help='Class name (e.g., espresso_cup)')
    parser.add_argument('--output', type=str, default='training_images',
                       help='Output directory')
    parser.add_argument('--num', type=int, default=100,
                       help='Number of images to collect')
    
    args = parser.parse_args()
    
    collect_images(
        class_name=args.class_name,
        output_dir=args.output,
        num_images=args.num
    )

