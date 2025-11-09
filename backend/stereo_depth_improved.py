#!/usr/bin/env python3
"""
IMPROVED Stereo Depth Algorithm - Built from Scratch
Uses state-of-the-art techniques for robust depth estimation.
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
    """Capture stereo images with improved settings."""
    print(f"📸 Capturing from cameras {cam_left} and {cam_right}...")
    
    cap_left = cv2.VideoCapture(cam_left)
    cap_right = cv2.VideoCapture(cam_right)
    
    if not cap_left.isOpened() or not cap_right.isOpened():
        print("❌ Could not open cameras")
        return None, None
    
    # Set camera properties for better quality
    for cap in [cap_left, cap_right]:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    
    # Warm up cameras (more frames for better auto-exposure)
    print("  Warming up cameras...")
    for _ in range(10):
        cap_left.read()
        cap_right.read()
    
    ret_left, img_left = cap_left.read()
    ret_right, img_right = cap_right.read()
    
    cap_left.release()
    cap_right.release()
    
    if not ret_left or not ret_right:
        return None, None
    
    print(f"✓ Captured: {img_left.shape}")
    return img_left, img_right


def preprocess_images(img_left, img_right):
    """
    Enhanced preprocessing for better feature detection and matching.
    """
    print("🔧 Preprocessing images...")
    
    # Convert to grayscale
    gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray_left = clahe.apply(gray_left)
    gray_right = clahe.apply(gray_right)
    
    # Denoise while preserving edges
    gray_left = cv2.fastNlMeansDenoising(gray_left, None, 10, 7, 21)
    gray_right = cv2.fastNlMeansDenoising(gray_right, None, 10, 7, 21)
    
    print("✓ Preprocessing complete")
    return gray_left, gray_right


def compute_improved_disparity(gray_left, gray_right):
    """
    Improved disparity computation using optimized SGBM parameters.
    
    Uses state-of-the-art Semi-Global Block Matching with carefully tuned parameters.
    """
    print("\n📊 Computing disparity map with improved SGBM...")
    
    # Optimized parameters for high-quality depth maps
    window_size = 3  # Smaller for finer details
    min_disp = 0
    num_disp = 16 * 16  # 256 disparities for wide depth range
    
    # Create SGBM matcher with optimized parameters
    left_matcher = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        P1=8 * 3 * window_size ** 2,      # Smoothness parameter 1
        P2=32 * 3 * window_size ** 2,     # Smoothness parameter 2
        disp12MaxDiff=1,                   # Left-right consistency check
        uniquenessRatio=5,                 # Lower = more matches (increased from 10)
        speckleWindowSize=200,             # Larger for better filtering
        speckleRange=2,                    # Stricter speckle filter
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    
    # Compute disparity
    print("  Computing left disparity...")
    disparity_left = left_matcher.compute(gray_left, gray_right)
    
    # Convert to float
    disparity_left = disparity_left.astype(np.float32) / 16.0
    
    # Try WLS filter if available, otherwise use bilateral filter
    try:
        print("  Applying WLS filter...")
        right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)
        disparity_right = right_matcher.compute(gray_right, gray_left)
        disparity_right = disparity_right.astype(np.float32) / 16.0
        
        wls_filter = cv2.ximgproc.createDisparityWLSFilter(left_matcher)
        wls_filter.setLambda(8000)
        wls_filter.setSigmaColor(1.2)
        
        filtered_disp = wls_filter.filter(
            (disparity_left * 16).astype(np.int16), 
            gray_left, 
            disparity_map_right=(disparity_right * 16).astype(np.int16)
        )
        filtered_disp = filtered_disp.astype(np.float32) / 16.0
        print("  ✓ WLS filtering applied")
    except (AttributeError, cv2.error):
        print("  WLS filter not available, using bilateral filter...")
        # Fallback: bilateral filter for edge-preserving smoothing
        disp_uint16 = (disparity_left * 16).astype(np.uint16)
        disp_filtered = cv2.bilateralFilter(disp_uint16.astype(np.float32), 9, 75, 75)
        filtered_disp = disp_filtered / 16.0
        print("  ✓ Bilateral filtering applied")
    
    # Post-processing: fill small holes
    print("  Post-processing...")
    
    # Morphological closing to fill small holes
    kernel = np.ones((5, 5), np.uint8)
    mask = (filtered_disp > 0).astype(np.uint8) * 255
    mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Inpainting for remaining holes
    disp_normalized = cv2.normalize(filtered_disp, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    inpaint_mask = (mask_closed == 0).astype(np.uint8) * 255
    disp_inpainted = cv2.inpaint(disp_normalized, inpaint_mask, 5, cv2.INPAINT_TELEA)
    
    # Convert back to disparity range
    final_disp = disp_inpainted.astype(np.float32) / 255.0
    final_disp = final_disp * (filtered_disp[filtered_disp > 0].max() - filtered_disp[filtered_disp > 0].min())
    final_disp += filtered_disp[filtered_disp > 0].min()
    
    # Keep original valid pixels
    final_disp[filtered_disp > 0] = filtered_disp[filtered_disp > 0]
    
    valid_pixels = np.sum(final_disp > 0)
    total_pixels = final_disp.shape[0] * final_disp.shape[1]
    coverage = 100 * valid_pixels / total_pixels
    
    print(f"✓ Disparity computed: {valid_pixels:,}/{total_pixels:,} pixels ({coverage:.1f}% coverage)")
    
    return final_disp


def disparity_to_depth_improved(disparity, baseline_mm=100, focal_length=None, img_width=None):
    """
    Improved depth computation with outlier rejection.
    
    Depth = (baseline * focal_length) / disparity
    """
    print("\n🎯 Converting disparity to depth...")
    
    if focal_length is None:
        # Estimate focal length (typical for webcams)
        focal_length = img_width * 0.8
    
    # Create depth map
    depth_map = np.zeros_like(disparity, dtype=np.float32)
    valid_mask = disparity > 1.0
    
    if not np.any(valid_mask):
        print("⚠️  No valid disparity values")
        return depth_map
    
    # Compute depth
    depth_map[valid_mask] = (baseline_mm * focal_length) / (disparity[valid_mask] + 1e-6)
    
    # Robust outlier rejection using percentiles
    valid_depths = depth_map[valid_mask]
    p5, p95 = np.percentile(valid_depths, [5, 95])
    median = np.median(valid_depths)
    
    # Filter outliers
    depth_map[depth_map < p5 * 0.5] = 0
    depth_map[depth_map > p95 * 2.0] = 0
    
    # Median filter to remove remaining noise
    depth_map_uint16 = (depth_map * 16).astype(np.uint16)
    depth_map_filtered = cv2.medianBlur(depth_map_uint16, 5)
    depth_map = depth_map_filtered.astype(np.float32) / 16.0
    
    valid_depths = depth_map[depth_map > 0]
    print(f"✓ Depth range: {valid_depths.min():.1f} - {valid_depths.max():.1f} mm")
    print(f"  Median: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)")
    
    return depth_map


def create_improved_3d_points(depth_map, img, subsample=2):
    """
    Create dense 3D point cloud with improved subsampling.
    """
    print("\n🌐 Creating 3D point cloud...")
    
    h, w = depth_map.shape
    
    # Create coordinate grids
    x, y = np.meshgrid(np.arange(0, w, subsample), np.arange(0, h, subsample))
    
    # Get depths
    depths = depth_map[y, x]
    
    # Filter valid points
    valid_mask = depths > 0
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    depths_valid = depths[valid_mask]
    
    # Convert to 3D (camera coordinate system)
    points_3d = np.zeros((len(depths_valid), 3))
    points_3d[:, 0] = x_valid - w/2  # X (horizontal)
    points_3d[:, 1] = y_valid - h/2  # Y (vertical)
    points_3d[:, 2] = depths_valid    # Z (depth)
    
    # Get colors
    colors = img[y_valid, x_valid] / 255.0
    
    print(f"✓ Point cloud: {len(points_3d):,} points")
    
    return points_3d, colors


def detect_surfaces_improved(points_3d, min_points=100):
    """
    Improved surface detection using RANSAC plane fitting.
    """
    print("\n🔍 Detecting planar surfaces...")
    
    if len(points_3d) < min_points:
        print("⚠️  Not enough points for surface detection")
        return [], np.full(len(points_3d), -1)
    
    # Spatial clustering
    clustering = DBSCAN(eps=50, min_samples=50).fit(points_3d)
    labels = clustering.labels_
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"  Found {n_clusters} spatial clusters")
    
    surfaces = []
    surface_labels = np.full(len(points_3d), -1, dtype=int)
    
    # Fit planes to each cluster
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_points = points_3d[mask]
        
        if len(cluster_points) < min_points:
            continue
        
        try:
            # Fit plane: Z = aX + bY + c
            X = cluster_points[:, :2]
            y = cluster_points[:, 2]
            
            ransac = RANSACRegressor(
                residual_threshold=30,
                min_samples=50,
                max_trials=1000,
                random_state=0
            )
            ransac.fit(X, y)
            
            inlier_mask = ransac.inlier_mask_
            n_inliers = np.sum(inlier_mask)
            
            if n_inliers > min_points:
                # Compute plane parameters
                a, b = ransac.estimator_.coef_
                c = ransac.estimator_.intercept_
                
                # Normal vector
                normal = np.array([-a, -b, 1])
                normal = normal / np.linalg.norm(normal)
                
                # Centroid
                centroid = cluster_points[inlier_mask].mean(axis=0)
                
                surfaces.append({
                    'n_points': n_inliers,
                    'normal': normal,
                    'centroid': centroid,
                    'plane_params': (a, b, c)
                })
                
                # Label points
                global_mask = np.where(mask)[0][inlier_mask]
                surface_labels[global_mask] = len(surfaces) - 1
        
        except Exception as e:
            continue
    
    print(f"✓ Detected {len(surfaces)} surfaces")
    
    return surfaces, surface_labels


def create_improved_visualization(img_left, img_right, depth_map, points_3d, colors, surfaces, surface_labels):
    """
    Create comprehensive visualization with improved layout.
    """
    print("\n📊 Creating visualization...")
    
    fig = plt.figure(figsize=(24, 16))
    
    # 1. Left image
    ax1 = fig.add_subplot(3, 4, 1)
    ax1.imshow(cv2.cvtColor(img_left, cv2.COLOR_BGR2RGB))
    ax1.set_title('Left Camera View', fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # 2. Right image
    ax2 = fig.add_subplot(3, 4, 2)
    ax2.imshow(cv2.cvtColor(img_right, cv2.COLOR_BGR2RGB))
    ax2.set_title('Right Camera View', fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    # 3. Depth map (color-coded)
    ax3 = fig.add_subplot(3, 4, 3)
    depth_vis = np.copy(depth_map)
    depth_vis[depth_map <= 0] = np.nan
    
    # Use percentile for better contrast
    valid_depths = depth_map[depth_map > 0]
    vmin, vmax = np.percentile(valid_depths, [2, 98])
    
    im = ax3.imshow(depth_vis, cmap='jet', vmin=vmin, vmax=vmax)
    ax3.set_title('IMPROVED Depth Map\n(Blue=Close, Red=Far)', fontsize=14, fontweight='bold')
    ax3.axis('off')
    plt.colorbar(im, ax=ax3, label='Depth (mm)', fraction=0.046)
    
    # 4. Depth histogram
    ax4 = fig.add_subplot(3, 4, 4)
    ax4.hist(valid_depths, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax4.axvline(np.median(valid_depths), color='red', linestyle='--', linewidth=2,
               label=f'Median: {np.median(valid_depths):.0f}mm')
    ax4.set_xlabel('Depth (mm)', fontsize=12)
    ax4.set_ylabel('Pixel Count', fontsize=12)
    ax4.set_title('Depth Distribution', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5-6. 3D Point Clouds
    for idx, (subplot_idx, title, coloring) in enumerate([
        (5, '3D Point Cloud (True Colors)', colors),
        (6, '3D Point Cloud (Depth Colored)', None)
    ]):
        ax = fig.add_subplot(3, 4, subplot_idx, projection='3d')
        
        # Subsample for performance
        subsample = max(1, len(points_3d) // 10000)
        pts = points_3d[::subsample]
        
        if coloring is None:
            c = pts[:, 2]
            scatter = ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=c, cmap='jet', s=0.5, alpha=0.6)
            plt.colorbar(scatter, ax=ax, shrink=0.5, label='Depth (mm)')
        else:
            cols = coloring[::subsample]
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=cols, s=0.5, alpha=0.6)
        
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        ax.set_zlabel('Depth (mm)')
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    # 7. Surface segmentation
    ax7 = fig.add_subplot(3, 4, 7, projection='3d')
    if len(surfaces) > 0:
        subsample = max(1, len(points_3d) // 10000)
        pts = points_3d[::subsample]
        surf_labels = surface_labels[::subsample]
        
        colors_surf = plt.cm.tab20(surf_labels % 20)
        colors_surf[surf_labels == -1] = [0.5, 0.5, 0.5, 0.3]
        
        ax7.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=colors_surf, s=0.5, alpha=0.7)
        ax7.set_title(f'Surface Segmentation ({len(surfaces)} surfaces)', fontsize=14, fontweight='bold')
    else:
        ax7.text2D(0.5, 0.5, 'No surfaces detected', ha='center', va='center', transform=ax7.transAxes)
        ax7.set_title('Surface Segmentation', fontsize=14, fontweight='bold')
    
    ax7.set_xlabel('X')
    ax7.set_ylabel('Y')
    ax7.set_zlabel('Depth')
    
    # 8. Depth overlay
    ax8 = fig.add_subplot(3, 4, 8)
    ax8.imshow(cv2.cvtColor(img_left, cv2.COLOR_BGR2RGB))
    depth_overlay = np.copy(depth_vis)
    ax8.imshow(depth_overlay, cmap='jet', alpha=0.5, vmin=vmin, vmax=vmax)
    ax8.set_title('Depth Overlay on Image', fontsize=14, fontweight='bold')
    ax8.axis('off')
    
    # 9. Top-down view
    ax9 = fig.add_subplot(3, 4, 9)
    subsample = max(1, len(points_3d) // 5000)
    pts = points_3d[::subsample]
    scatter = ax9.scatter(pts[:, 0], pts[:, 2], c=pts[:, 2], cmap='jet', s=1, alpha=0.5)
    ax9.set_xlabel('X Position (pixels)')
    ax9.set_ylabel('Depth (mm)')
    ax9.set_title('Top-Down View', fontsize=14, fontweight='bold')
    ax9.grid(True, alpha=0.3)
    ax9.invert_yaxis()
    plt.colorbar(scatter, ax=ax9, label='Depth (mm)')
    
    # 10. Side view
    ax10 = fig.add_subplot(3, 4, 10)
    scatter2 = ax10.scatter(pts[:, 1], pts[:, 2], c=pts[:, 2], cmap='jet', s=1, alpha=0.5)
    ax10.set_xlabel('Y Position (pixels)')
    ax10.set_ylabel('Depth (mm)')
    ax10.set_title('Side View', fontsize=14, fontweight='bold')
    ax10.grid(True, alpha=0.3)
    ax10.invert_yaxis()
    plt.colorbar(scatter2, ax=ax10, label='Depth (mm)')
    
    # 11. Statistics
    ax11 = fig.add_subplot(3, 4, 11)
    ax11.axis('off')
    
    stats_text = f"""
IMPROVED STEREO DEPTH STATISTICS
═════════════════════════════════

Algorithm: Enhanced SGBM + WLS Filter
Coordinate System: Camera 0 Reference

Dense Coverage:
  Total pixels: {depth_map.size:,}
  Valid depth: {len(valid_depths):,}
  Coverage: {100*len(valid_depths)/depth_map.size:.1f}%

3D Reconstruction:
  Total points: {len(points_3d):,}
  Surfaces: {len(surfaces)}

Depth Range:
  Min: {valid_depths.min():.1f} mm ({valid_depths.min()/10:.1f} cm)
  Max: {valid_depths.max():.1f} mm ({valid_depths.max()/10:.1f} cm)
  Median: {np.median(valid_depths):.1f} mm ({np.median(valid_depths)/10:.1f} cm)
  Mean: {valid_depths.mean():.1f} mm

Improvements:
  ✓ WLS filtering (edge-aware)
  ✓ Left-right consistency
  ✓ Adaptive preprocessing
  ✓ Robust outlier rejection
  ✓ Inpainting for holes

Baseline: {100}mm (estimated)
Measure camera separation for accuracy!
"""
    
    ax11.text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax11.set_title('Statistics & Info', fontsize=14, fontweight='bold')
    
    # 12. Coverage map
    ax12 = fig.add_subplot(3, 4, 12)
    coverage_map = (depth_map > 0).astype(np.uint8) * 255
    ax12.imshow(coverage_map, cmap='gray')
    ax12.set_title(f'Coverage Map ({100*len(valid_depths)/depth_map.size:.1f}%)', fontsize=14, fontweight='bold')
    ax12.axis('off')
    
    plt.tight_layout()
    plt.savefig('improved_depth_graph.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: improved_depth_graph.png")
    plt.close(fig)


def main():
    print("=" * 80)
    print("IMPROVED STEREO DEPTH ALGORITHM")
    print("Rebuilt from scratch with state-of-the-art techniques")
    print("=" * 80)
    
    # Get camera indices
    cam_left = 0
    cam_right = 1
    
    if len(sys.argv) >= 3:
        try:
            cam_left = int(sys.argv[1])
            cam_right = int(sys.argv[2])
        except ValueError:
            pass
    
    print(f"\n📸 Using cameras: {cam_left} (left) and {cam_right} (right)")
    
    # 1. Capture
    print("\n[1/6] Capturing stereo images...")
    img_left, img_right = capture_stereo_images(cam_left, cam_right)
    
    if img_left is None or img_right is None:
        print("❌ Failed to capture")
        return
    
    cv2.imwrite('captured_left.jpg', img_left)
    cv2.imwrite('captured_right.jpg', img_right)
    
    # 2. Preprocess
    print("\n[2/6] Preprocessing...")
    gray_left, gray_right = preprocess_images(img_left, img_right)
    
    # 3. Compute disparity
    print("\n[3/6] Computing disparity...")
    disparity = compute_improved_disparity(gray_left, gray_right)
    
    # 4. Convert to depth
    print("\n[4/6] Converting to depth...")
    depth_map = disparity_to_depth_improved(disparity, baseline_mm=100, img_width=img_left.shape[1])
    
    # 5. Create 3D points
    print("\n[5/6] Creating 3D point cloud...")
    points_3d, colors = create_improved_3d_points(depth_map, img_left, subsample=2)
    
    # 6. Detect surfaces
    print("\n[6/6] Detecting surfaces...")
    surfaces, surface_labels = detect_surfaces_improved(points_3d)
    
    # Visualize
    print("\nCreating visualization...")
    create_improved_visualization(img_left, img_right, depth_map, points_3d, colors, surfaces, surface_labels)
    
    print("\n" + "=" * 80)
    print("✅ IMPROVED STEREO DEPTH COMPLETE!")
    print("=" * 80)
    print("\nOutput: improved_depth_graph.png")
    
    valid_depths = depth_map[depth_map > 0]
    print(f"\n📊 Results:")
    print(f"  Coverage: {100*len(valid_depths)/depth_map.size:.1f}%")
    print(f"  3D points: {len(points_3d):,}")
    print(f"  Surfaces: {len(surfaces)}")
    print(f"  Depth: {valid_depths.min():.0f}-{valid_depths.max():.0f}mm (median: {np.median(valid_depths):.0f}mm)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

