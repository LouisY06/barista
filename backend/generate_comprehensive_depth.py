#!/usr/bin/env python3
"""
Enhanced depth graph generator with surface detection and dense mapping.
Creates comprehensive depth visualization of the entire scene.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import DBSCAN
from sklearn.linear_model import RANSACRegressor
import warnings
import sys
warnings.filterwarnings('ignore')

def capture_stereo_images(cam_left=0, cam_right=1):
    """Capture images from two cameras."""
    print(f"Capturing from cameras {cam_left} and {cam_right}...")
    
    cap_left = cv2.VideoCapture(cam_left)
    cap_right = cv2.VideoCapture(cam_right)
    
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("Error: Could not open cameras")
        return None, None
    
    # Warm up cameras
    for _ in range(5):
        cap_left.read()
        cap_right.read()
    
    ret_left, img_left = cap_left.read()
    ret_right, img_right = cap_right.read()
    
    cap_left.release()
    cap_right.release()
    
    if not ret_left or not ret_right:
        return None, None
    
    print(f"✓ Captured images: {img_left.shape}")
    return img_left, img_right


def compute_dense_disparity(img1, img2):
    """
    Compute dense disparity map using Semi-Global Block Matching (SGBM).
    This creates a depth value for EVERY pixel, not just feature points.
    """
    print("\n📊 Computing DENSE disparity map (this gives depth for every pixel)...")
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray1 = clahe.apply(gray1)
    gray2 = clahe.apply(gray2)
    
    # SGBM parameters tuned for comprehensive depth mapping
    window_size = 5
    min_disp = 0
    num_disp = 16 * 12  # 192 disparities for good range
    
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        P1=8 * 3 * window_size ** 2,
        P2=32 * 3 * window_size ** 2,
        disp12MaxDiff=2,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32,
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    
    # Compute disparity
    disparity = stereo.compute(gray1, gray2).astype(np.float32) / 16.0
    
    # Post-process: median filter to reduce noise
    valid_mask = disparity > 0
    if np.any(valid_mask):
        disparity_uint = (disparity * 16).astype(np.uint16)
        disparity_filtered = cv2.medianBlur(disparity_uint, 5)
        disparity = disparity_filtered.astype(np.float32) / 16.0
    
    valid_pixels = np.sum(disparity > 0)
    total_pixels = disparity.shape[0] * disparity.shape[1]
    coverage = 100 * valid_pixels / total_pixels
    
    print(f"✓ Dense disparity computed: {valid_pixels:,}/{total_pixels:,} pixels ({coverage:.1f}% coverage)")
    
    return disparity


def disparity_to_depth(disparity, baseline_mm=100, focal_length=None, img_width=None):
    """
    Convert disparity map to depth map.
    Depth = (baseline * focal_length) / disparity
    """
    if focal_length is None:
        # Estimate focal length from image width
        focal_length = img_width * 0.7
    
    # Create depth map
    depth_map = np.zeros_like(disparity, dtype=np.float32)
    valid_mask = disparity > 1.0  # Avoid division by very small numbers
    
    depth_map[valid_mask] = (baseline_mm * focal_length) / (disparity[valid_mask] + 1e-6)
    
    # Filter outliers
    if np.any(valid_mask):
        median_depth = np.median(depth_map[valid_mask])
        # Keep depths within reasonable range
        depth_map[depth_map > median_depth * 5] = 0
        depth_map[depth_map < median_depth * 0.1] = 0
    
    return depth_map


def create_3d_point_cloud(depth_map, img, subsample=5):
    """
    Create 3D point cloud from depth map.
    Returns points in camera coordinate system.
    """
    h, w = depth_map.shape
    
    # Create mesh grid of pixel coordinates
    x, y = np.meshgrid(np.arange(0, w, subsample), np.arange(0, h, subsample))
    
    # Get corresponding depths
    depths = depth_map[y, x]
    
    # Filter valid points
    valid_mask = depths > 0
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    depths_valid = depths[valid_mask]
    
    # Convert to 3D coordinates (centered at image center)
    points_3d = np.zeros((len(depths_valid), 3))
    points_3d[:, 0] = x_valid - w/2  # X (horizontal from center)
    points_3d[:, 1] = y_valid - h/2  # Y (vertical from center)
    points_3d[:, 2] = depths_valid    # Z (depth)
    
    # Get colors from image
    colors = img[y_valid, x_valid] / 255.0  # Normalize to 0-1
    
    print(f"✓ Created 3D point cloud: {len(points_3d):,} points")
    
    return points_3d, colors


def detect_surfaces(points_3d, colors, n_surfaces=5):
    """
    Detect planar surfaces in the point cloud using RANSAC and clustering.
    """
    print(f"\n🔍 Detecting surfaces in point cloud...")
    
    if len(points_3d) < 100:
        print("⚠️  Not enough points for surface detection")
        return None, None
    
    # Cluster points spatially using DBSCAN
    clustering = DBSCAN(eps=50, min_samples=50).fit(points_3d)
    labels = clustering.labels_
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"✓ Found {n_clusters} spatial clusters")
    
    surfaces = []
    surface_labels = np.full(len(points_3d), -1, dtype=int)
    
    # For each cluster, try to fit a plane
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_points = points_3d[mask]
        
        if len(cluster_points) < 50:
            continue
        
        try:
            # Fit plane using RANSAC: Z = aX + bY + c
            X = cluster_points[:, :2]  # X, Y coordinates
            y = cluster_points[:, 2]   # Z coordinates
            
            ransac = RANSACRegressor(residual_threshold=20, random_state=0)
            ransac.fit(X, y)
            
            inlier_mask = ransac.inlier_mask_
            n_inliers = np.sum(inlier_mask)
            
            if n_inliers > 100:  # Significant surface
                # Get plane parameters
                a, b = ransac.estimator_.coef_
                c = ransac.estimator_.intercept_
                
                # Compute plane normal
                normal = np.array([-a, -b, 1])
                normal = normal / np.linalg.norm(normal)
                
                surfaces.append({
                    'cluster_id': cluster_id,
                    'n_points': n_inliers,
                    'plane_params': (a, b, c),
                    'normal': normal,
                    'centroid': cluster_points[inlier_mask].mean(axis=0)
                })
                
                # Mark surface points
                global_mask = np.where(mask)[0][inlier_mask]
                surface_labels[global_mask] = len(surfaces) - 1
        
        except Exception as e:
            continue
    
    print(f"✓ Detected {len(surfaces)} planar surfaces")
    for i, surf in enumerate(surfaces):
        print(f"  Surface {i+1}: {surf['n_points']:,} points, normal={surf['normal']}")
    
    return surfaces, surface_labels


def create_comprehensive_visualization(img1, img2, depth_map, points_3d, colors, surfaces, surface_labels):
    """Create comprehensive visualization with surface detection."""
    
    fig = plt.figure(figsize=(24, 14))
    
    # 1. Original images
    ax1 = fig.add_subplot(3, 4, 1)
    ax1.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    ax1.set_title('Camera 0 (Reference View)', fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    ax2 = fig.add_subplot(3, 4, 2)
    ax2.imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    ax2.set_title('Camera 1 (Second View)', fontsize=12, fontweight='bold')
    ax2.axis('off')
    
    # 2. Dense depth map (color-coded)
    ax3 = fig.add_subplot(3, 4, 3)
    depth_vis = np.copy(depth_map)
    depth_vis[depth_map <= 0] = np.nan
    
    im = ax3.imshow(depth_vis, cmap='jet', interpolation='nearest')
    ax3.set_title('DENSE Depth Map\n(Blue=Close, Red=Far)', fontsize=12, fontweight='bold')
    ax3.axis('off')
    plt.colorbar(im, ax=ax3, label='Depth (mm)', fraction=0.046)
    
    # 3. Depth histogram
    ax4 = fig.add_subplot(3, 4, 4)
    valid_depths = depth_map[depth_map > 0]
    if len(valid_depths) > 0:
        ax4.hist(valid_depths, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
        ax4.axvline(np.median(valid_depths), color='red', linestyle='--', linewidth=2, 
                   label=f'Median: {np.median(valid_depths):.1f}mm')
        ax4.set_xlabel('Distance from Camera 0 (mm)')
        ax4.set_ylabel('Number of Pixels')
        ax4.set_title('Depth Distribution', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 4. 3D point cloud (colored by image)
    ax5 = fig.add_subplot(3, 4, 5, projection='3d')
    subsample = max(1, len(points_3d) // 5000)
    pts = points_3d[::subsample]
    cols = colors[::subsample]
    
    ax5.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=cols, s=1, alpha=0.5)
    ax5.set_xlabel('X (pixels)')
    ax5.set_ylabel('Y (pixels)')
    ax5.set_zlabel('Depth (mm)')
    ax5.set_title('3D Point Cloud\n(True Colors)', fontsize=12, fontweight='bold')
    
    # 5. 3D point cloud (colored by depth)
    ax6 = fig.add_subplot(3, 4, 6, projection='3d')
    depths_sub = pts[:, 2]
    scatter = ax6.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=depths_sub, cmap='jet', s=1, alpha=0.5)
    ax6.set_xlabel('X (pixels)')
    ax6.set_ylabel('Y (pixels)')
    ax6.set_zlabel('Depth (mm)')
    ax6.set_title('3D Point Cloud\n(Depth Colored)', fontsize=12, fontweight='bold')
    plt.colorbar(scatter, ax=ax6, shrink=0.5, label='Depth (mm)')
    
    # 6. Surface segmentation
    ax7 = fig.add_subplot(3, 4, 7, projection='3d')
    if surfaces is not None and len(surfaces) > 0:
        # Color by surface
        surface_colors = plt.cm.tab10(surface_labels[::subsample] % 10)
        surface_colors[surface_labels[::subsample] == -1] = [0.5, 0.5, 0.5, 0.3]  # Gray for non-surface
        
        ax7.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=surface_colors, s=1, alpha=0.6)
        ax7.set_title(f'Detected Surfaces ({len(surfaces)})\n(Each color = 1 surface)', 
                     fontsize=12, fontweight='bold')
    else:
        ax7.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=cols, s=1, alpha=0.5)
        ax7.set_title('Point Cloud\n(No surfaces detected)', fontsize=12, fontweight='bold')
    
    ax7.set_xlabel('X (pixels)')
    ax7.set_ylabel('Y (pixels)')
    ax7.set_zlabel('Depth (mm)')
    
    # 7. Top-down view
    ax8 = fig.add_subplot(3, 4, 8)
    scatter2 = ax8.scatter(pts[:, 0], pts[:, 2], c=depths_sub, cmap='jet', s=1, alpha=0.5)
    ax8.set_xlabel('X Position (pixels)')
    ax8.set_ylabel('Depth from Camera 0 (mm)')
    ax8.set_title('Top-Down View (Bird\'s Eye)', fontsize=12, fontweight='bold')
    ax8.grid(True, alpha=0.3)
    ax8.invert_yaxis()  # Invert so farther objects are at top
    plt.colorbar(scatter2, ax=ax8, label='Depth (mm)')
    
    # 8. Statistics
    ax9 = fig.add_subplot(3, 4, 9)
    ax9.axis('off')
    
    valid_depths = depth_map[depth_map > 0]
    stats_text = f"""
COMPREHENSIVE DEPTH STATISTICS
══════════════════════════════

Coordinate System:
  Origin: Camera 0 optical center
  Z-axis: Into the scene
  Color: Blue=Close | Red=Far

Dense Coverage:
  Total pixels: {depth_map.size:,}
  Valid depth: {len(valid_depths):,}
  Coverage: {100*len(valid_depths)/depth_map.size:.1f}%

3D Point Cloud:
  Total points: {len(points_3d):,}
  
Depth Range (from Camera 0):
  Min: {valid_depths.min():.1f} mm ({valid_depths.min()/10:.1f} cm)
  Max: {valid_depths.max():.1f} mm ({valid_depths.max()/10:.1f} cm)
  Median: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)

Surfaces Detected:
  Planar surfaces: {len(surfaces) if surfaces else 0}
"""
    
    if surfaces and len(surfaces) > 0:
        stats_text += "\n  Surface points:\n"
        for i, surf in enumerate(surfaces[:5]):  # Show first 5
            stats_text += f"    #{i+1}: {surf['n_points']:,} pts\n"
    
    stats_text += """
⚠ CALIBRATION:
Baseline: 100mm (ESTIMATED)
Measure camera separation!
"""
    
    ax9.text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    ax9.set_title('Statistics', fontsize=14, fontweight='bold')
    
    # 9. Depth map overlay on image
    ax10 = fig.add_subplot(3, 4, 10)
    ax10.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    
    # Create semi-transparent depth overlay
    depth_overlay = np.copy(depth_map)
    depth_overlay[depth_map <= 0] = np.nan
    
    im2 = ax10.imshow(depth_overlay, cmap='jet', alpha=0.4, interpolation='nearest')
    ax10.set_title('Depth Overlay on Image', fontsize=12, fontweight='bold')
    ax10.axis('off')
    plt.colorbar(im2, ax=ax10, label='Depth (mm)', fraction=0.046)
    
    # 10. Side view
    ax11 = fig.add_subplot(3, 4, 11)
    scatter3 = ax11.scatter(pts[:, 1], pts[:, 2], c=depths_sub, cmap='jet', s=1, alpha=0.5)
    ax11.set_xlabel('Y Position (pixels)')
    ax11.set_ylabel('Depth from Camera 0 (mm)')
    ax11.set_title('Side View', fontsize=12, fontweight='bold')
    ax11.grid(True, alpha=0.3)
    ax11.invert_yaxis()
    plt.colorbar(scatter3, ax=ax11, label='Depth (mm)')
    
    # 11. Surface normals visualization
    ax12 = fig.add_subplot(3, 4, 12, projection='3d')
    if surfaces and len(surfaces) > 0:
        # Plot surfaces with normals
        for i, surf in enumerate(surfaces):
            color = plt.cm.tab10(i % 10)[:3]
            centroid = surf['centroid']
            normal = surf['normal'] * 100  # Scale for visibility
            
            # Draw arrow for normal
            ax12.quiver(centroid[0], centroid[1], centroid[2],
                       normal[0], normal[1], normal[2],
                       color=color, arrow_length_ratio=0.3, linewidth=2)
        
        # Plot point cloud
        surface_colors = plt.cm.tab10(surface_labels[::subsample] % 10)
        ax12.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=surface_colors, s=1, alpha=0.3)
        ax12.set_title(f'Surface Normals\n({len(surfaces)} surfaces)', fontsize=12, fontweight='bold')
    else:
        ax12.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=cols, s=1, alpha=0.5)
        ax12.set_title('Point Cloud', fontsize=12, fontweight='bold')
    
    ax12.set_xlabel('X')
    ax12.set_ylabel('Y')
    ax12.set_zlabel('Depth')
    
    plt.tight_layout()
    plt.savefig('comprehensive_depth_graph.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved comprehensive visualization to: comprehensive_depth_graph.png")
    plt.close(fig)


def main():
    print("=" * 70)
    print("COMPREHENSIVE DEPTH GRAPH GENERATOR")
    print("with Surface Detection and Dense Mapping")
    print("=" * 70)
    
    # Get camera indices from command line or use defaults
    cam_left = 0
    cam_right = 1
    
    if len(sys.argv) >= 3:
        try:
            cam_left = int(sys.argv[1])
            cam_right = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid camera indices. Using defaults (0, 1)")
    elif len(sys.argv) == 2:
        print("⚠️  Need both camera indices. Usage: python generate_comprehensive_depth.py <left_cam> <right_cam>")
        print("   Using defaults: cameras 0 and 1")
    
    print(f"\n📸 Using cameras: {cam_left} (left) and {cam_right} (right)")
    print("   To use iPhone: First run 'python list_cameras.py' to find iPhone camera index")
    
    # 1. Capture stereo images
    print("\n[1/5] Capturing stereo images...")
    img_left, img_right = capture_stereo_images(cam_left=cam_left, cam_right=cam_right)
    
    if img_left is None or img_right is None:
        print("❌ Failed to capture images")
        return
    
    cv2.imwrite('captured_left.jpg', img_left)
    cv2.imwrite('captured_right.jpg', img_right)
    
    # 2. Compute dense disparity map
    print("\n[2/5] Computing dense disparity (every pixel gets a depth)...")
    disparity = compute_dense_disparity(img_left, img_right)
    
    valid_pixels = np.sum(disparity > 0)
    if valid_pixels < 1000:
        print(f"\n⚠️  WARNING: Very few valid depth pixels ({valid_pixels})")
        print("💡 TO IMPROVE:")
        print("  1. 💡 Improve lighting - add more light to the scene")
        print("  2. 💡 Ensure even illumination (no harsh shadows)")
        print("  3. Position cameras side-by-side with overlapping views")
        print("  4. Add textured objects (patterns, details, not plain surfaces)")
    
    # 3. Convert disparity to depth
    print("\n[3/5] Converting disparity to depth map...")
    depth_map = disparity_to_depth(disparity, baseline_mm=100, img_width=img_left.shape[1])
    
    valid_depths = depth_map[depth_map > 0]
    print(f"✓ Depth range: {valid_depths.min():.1f} to {valid_depths.max():.1f} mm")
    print(f"  Median depth: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)")
    
    # 4. Create 3D point cloud
    print("\n[4/5] Creating 3D point cloud...")
    points_3d, colors = create_3d_point_cloud(depth_map, img_left, subsample=3)
    
    # 5. Detect surfaces
    print("\n[5/5] Detecting planar surfaces...")
    surfaces, surface_labels = detect_surfaces(points_3d, colors)
    
    # 6. Create comprehensive visualization
    print("\nCreating comprehensive visualization...")
    create_comprehensive_visualization(img_left, img_right, depth_map, points_3d, colors, surfaces, surface_labels)
    
    print("\n" + "=" * 70)
    print("✅ COMPREHENSIVE DEPTH GRAPH COMPLETE!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - comprehensive_depth_graph.png (main visualization)")
    print("  - captured_left.jpg (camera 0 view)")
    print("  - captured_right.jpg (camera 1 view)")
    
    print(f"\n📊 Summary:")
    print(f"  Dense coverage: {100*len(valid_depths)/depth_map.size:.1f}% of pixels")
    print(f"  3D points: {len(points_3d):,}")
    print(f"  Surfaces detected: {len(surfaces) if surfaces else 0}")
    print(f"  Depth range: {valid_depths.min():.1f} - {valid_depths.max():.1f} mm")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

