#!/usr/bin/env python3
"""
Test script for monocular depth estimation.
Captures from a single camera and estimates depth.
"""

import cv2
import numpy as np
import requests
import base64
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def encode_image(img):
    """Encode image to base64."""
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')


def test_mono_depth(camera_idx=0, use_api=True):
    """Test monocular depth estimation."""
    print("=" * 80)
    print("MONOCULAR DEPTH ESTIMATION TEST")
    print("=" * 80)
    
    # Capture image
    print(f"\n📸 Capturing from camera {camera_idx}...")
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        print(f"❌ Could not open camera {camera_idx}")
        return
    
    # Warm up
    for _ in range(10):
        cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to capture frame")
        return
    
    print(f"✓ Captured: {frame.shape}")
    cv2.imwrite('test_mono_input.jpg', frame)
    
    if use_api:
        # Test via API
        print("\n🌐 Testing via API...")
        url = "http://localhost:5001/api/mono-depth/estimate"
        
        files = {
            'image': ('test.jpg', cv2.imencode('.jpg', frame)[1].tobytes(), 'image/jpeg')
        }
        
        params = {
            'return_visualization': 'true',
            'return_depth_map': 'true',
            'colormap': 'jet'
        }
        
        try:
            response = requests.post(url, files=files, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    metadata = data.get('depth_metadata', {})
                    print(f"\n✓ Depth estimation successful!")
                    print(f"  Min depth: {metadata.get('min_depth', 0):.3f} m")
                    print(f"  Max depth: {metadata.get('max_depth', 0):.3f} m")
                    print(f"  Median depth: {metadata.get('median_depth', 0):.3f} m")
                    print(f"  Coverage: {metadata.get('coverage', 0):.1f}%")
                    
                    # Save visualization
                    if 'visualization' in data:
                        viz_b64 = data['visualization'].split(',')[1]
                        viz_bytes = base64.b64decode(viz_b64)
                        viz_img = cv2.imdecode(np.frombuffer(viz_bytes, np.uint8), cv2.IMREAD_COLOR)
                        cv2.imwrite('test_mono_depth_viz.jpg', viz_img)
                        print(f"\n✓ Saved visualization: test_mono_depth_viz.jpg")
                    
                    # Decode depth map if provided
                    if 'depth_map' in data:
                        depth_bytes = base64.b64decode(data['depth_map'])
                        depth_shape = tuple(data['depth_map_shape'])
                        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(depth_shape)
                        
                        # Create comprehensive visualization
                        create_visualization(frame, depth_map, metadata)
                        print(f"✓ Saved comprehensive visualization: test_mono_depth_comprehensive.png")
                else:
                    print(f"❌ Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ API error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Direct test (requires model to be loaded)
        print("\n⚠️  Direct testing requires model to be loaded in the service")
        print("   Use --api flag or test via the API endpoint")


def create_visualization(image, depth_map, metadata):
    """Create comprehensive visualization."""
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Original image
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax1.set_title('Original Image', fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    # 2. Depth map (colored)
    ax2 = fig.add_subplot(2, 3, 2)
    valid_mask = depth_map > 0
    if np.any(valid_mask):
        vmin, vmax = np.percentile(depth_map[valid_mask], [5, 95])
        im = ax2.imshow(depth_map, cmap='jet', vmin=vmin, vmax=vmax)
        ax2.set_title('Depth Map (Meters)\nBlue=Close, Red=Far', fontsize=12, fontweight='bold')
        plt.colorbar(im, ax=ax2, label='Depth (m)', fraction=0.046)
    ax2.axis('off')
    
    # 3. Depth overlay
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if np.any(valid_mask):
        vmin, vmax = np.percentile(depth_map[valid_mask], [5, 95])
        ax3.imshow(depth_map, cmap='jet', alpha=0.5, vmin=vmin, vmax=vmax)
    ax3.set_title('Depth Overlay', fontsize=12, fontweight='bold')
    ax3.axis('off')
    
    # 4. Depth histogram
    ax4 = fig.add_subplot(2, 3, 4)
    if np.any(valid_mask):
        valid_depths = depth_map[valid_mask]
        ax4.hist(valid_depths, bins=50, edgecolor='black', alpha=0.7)
        ax4.axvline(metadata.get('median_depth', 0), color='r', linestyle='--', 
                   label=f"Median: {metadata.get('median_depth', 0):.2f}m")
        ax4.set_xlabel('Depth (meters)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Depth Distribution', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 5. Depth in mm
    ax5 = fig.add_subplot(2, 3, 5)
    depth_mm = depth_map * 1000.0
    if np.any(valid_mask):
        vmin_mm, vmax_mm = np.percentile(depth_mm[valid_mask], [5, 95])
        im2 = ax5.imshow(depth_mm, cmap='jet', vmin=vmin_mm, vmax=vmax_mm)
        ax5.set_title('Depth Map (Millimeters)', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=ax5, label='Depth (mm)', fraction=0.046)
    ax5.axis('off')
    
    # 6. Statistics
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    
    stats_text = f"""
MONOCULAR DEPTH ESTIMATION
══════════════════════════

Model: Intel DPT-Large
Single Camera: ✓

Depth Statistics:
  Min: {metadata.get('min_depth', 0):.3f} m
  Max: {metadata.get('max_depth', 0):.3f} m
  Median: {metadata.get('median_depth', 0):.3f} m
  Mean: {metadata.get('mean_depth', 0):.3f} m

Coverage: {metadata.get('coverage', 0):.1f}%

Image Size: {metadata.get('shape', [0, 0])}

✓ No stereo setup required
✓ Works with single camera
✓ Deep learning based
"""
    
    ax6.text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax6.set_title('Statistics', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('test_mono_depth_comprehensive.png', dpi=150, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    camera_idx = 0
    if len(sys.argv) > 1:
        try:
            camera_idx = int(sys.argv[1])
        except ValueError:
            pass
    
    use_api = True
    if len(sys.argv) > 2 and sys.argv[2] == "--no-api":
        use_api = False
    
    test_mono_depth(camera_idx, use_api)

