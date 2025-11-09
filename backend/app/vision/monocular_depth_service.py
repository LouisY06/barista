"""
Monocular Depth Estimation Service
====================================
Single-camera depth estimation using deep learning models.

Uses MiDaS (Mixed Dataset for Monocular Depth Estimation) for accurate
depth maps from a single camera - no stereo setup required!
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import cv2
import numpy as np
import base64
import io
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

bp_mono_depth = Blueprint("monocular_depth", __name__, url_prefix="/api")

# Try to import torch and transformers for MiDaS
try:
    import torch
    import torchvision.transforms as transforms
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    DEPTH_MODEL_AVAILABLE = True
except ImportError:
    DEPTH_MODEL_AVAILABLE = False
    logger.warning("PyTorch/transformers not available. Install with: pip install torch transformers")


class MonocularDepthEstimator:
    """Monocular depth estimation using MiDaS model."""
    
    def __init__(self, model_name: str = "Intel/dpt-large"):
        """
        Initialize depth estimator.
        
        Args:
            model_name: HuggingFace model name. Options:
                - "Intel/dpt-large" (best quality, slower)
                - "Intel/dpt-hybrid-midas" (balanced)
                - "Intel/dpt-beit-large-512" (fast, good quality)
        """
        self.model = None
        self.processor = None
        self.device = None
        self.model_name = model_name
        self.is_loaded = False
        
        if not DEPTH_MODEL_AVAILABLE:
            logger.error("PyTorch/transformers not available. Cannot load depth model.")
            return
        
        self._load_model()
    
    def _load_model(self):
        """Load the depth estimation model."""
        try:
            logger.info(f"Loading monocular depth model: {self.model_name}")
            
            # Check if CUDA is available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # Load model and processor
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForDepthEstimation.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info("✓ Monocular depth model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load depth model: {e}")
            self.is_loaded = False
    
    def estimate_depth(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Estimate depth map from a single image.
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            depth_map: Depth map as numpy array (values in meters)
            metadata: Dictionary with depth statistics
        """
        if not self.is_loaded:
            raise RuntimeError("Depth model not loaded")
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        inputs = self.processor(images=image_rgb, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Predict depth
        with torch.no_grad():
            outputs = self.model(**inputs)
            predicted_depth = outputs.predicted_depth
        
        # Convert to numpy
        depth_map = predicted_depth.squeeze().cpu().numpy()
        
        # Normalize to meters (model outputs in meters)
        depth_map = depth_map.astype(np.float32)
        
        # Compute statistics
        valid_depths = depth_map[depth_map > 0]
        metadata = {
            "min_depth": float(np.min(valid_depths)) if len(valid_depths) > 0 else 0.0,
            "max_depth": float(np.max(valid_depths)) if len(valid_depths) > 0 else 0.0,
            "median_depth": float(np.median(valid_depths)) if len(valid_depths) > 0 else 0.0,
            "mean_depth": float(np.mean(valid_depths)) if len(valid_depths) > 0 else 0.0,
            "coverage": float(100 * len(valid_depths) / depth_map.size) if depth_map.size > 0 else 0.0,
            "shape": depth_map.shape
        }
        
        return depth_map, metadata
    
    def visualize_depth(self, depth_map: np.ndarray, colormap: str = "jet") -> np.ndarray:
        """
        Visualize depth map as color image.
        
        Args:
            depth_map: Depth map (in meters)
            colormap: Colormap name ('jet', 'viridis', 'plasma', etc.)
            
        Returns:
            Colored depth visualization
        """
        # Normalize depth for visualization
        valid_mask = depth_map > 0
        if not np.any(valid_mask):
            return np.zeros((*depth_map.shape, 3), dtype=np.uint8)
        
        valid_depths = depth_map[valid_mask]
        vmin, vmax = np.percentile(valid_depths, [5, 95])
        
        # Normalize to 0-255 and ensure uint8
        depth_normalized = np.zeros(depth_map.shape, dtype=np.uint8)
        depth_normalized[valid_mask] = np.clip(
            (depth_map[valid_mask] - vmin) / (vmax - vmin + 1e-6) * 255,
            0, 255
        ).astype(np.uint8)
        
        # Apply colormap (requires uint8 single channel)
        if colormap == "jet":
            depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        elif colormap == "viridis":
            depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_VIRIDIS)
        else:
            depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        
        # Set invalid pixels to black
        depth_colored[~valid_mask] = [0, 0, 0]
        
        return depth_colored


# Global depth estimator instance
_depth_estimator: Optional[MonocularDepthEstimator] = None


def get_depth_estimator() -> MonocularDepthEstimator:
    """Get or create the global depth estimator."""
    global _depth_estimator
    if _depth_estimator is None:
        _depth_estimator = MonocularDepthEstimator()
    return _depth_estimator


def _decode_image(request) -> Optional[np.ndarray]:
    """Decode image from request (multipart or base64)."""
    # Try multipart file
    if "image" in request.files:
        file = request.files["image"]
        arr = np.frombuffer(file.read(), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    
    # Try JSON base64
    if request.is_json and "image" in (request.json or {}):
        b64 = request.json["image"]
        if "," in b64:
            b64 = b64.split(",")[1]
        arr = np.frombuffer(base64.b64decode(b64), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    
    return None


@bp_mono_depth.get("/mono-depth/ping")
def mono_depth_ping():
    """Health check endpoint."""
    estimator = get_depth_estimator()
    return jsonify({
        "ok": True,
        "service": "monocular_depth",
        "model_loaded": estimator.is_loaded,
        "model_name": estimator.model_name if estimator.is_loaded else None
    })


@bp_mono_depth.post("/mono-depth/estimate")
def mono_depth_estimate():
    """
    Estimate depth from a single image.
    
    Accepts:
    - Multipart form data with 'image' file
    - JSON with 'image' as base64 encoded string
    
    Query parameters:
    - return_visualization: Include depth visualization (true/false, default: true)
    - colormap: Colormap for visualization ('jet', 'viridis', default: 'jet')
    - return_depth_map: Return raw depth map (true/false, default: false)
    
    Returns:
    {
        "ok": true,
        "depth_metadata": {
            "min_depth": 0.5,  // meters
            "max_depth": 3.2,
            "median_depth": 1.8,
            "mean_depth": 1.9,
            "coverage": 100.0,  // percentage
            "shape": [480, 640]
        },
        "visualization": "base64_encoded_image",  // if return_visualization=true
        "depth_map": "base64_encoded_array"  // if return_depth_map=true
    }
    """
    try:
        estimator = get_depth_estimator()
        
        if not estimator.is_loaded:
            return jsonify({
                "ok": False,
                "error": "Depth model not loaded. Install PyTorch and transformers."
            }), 500
        
        # Parse image
        image = _decode_image(request)
        if image is None:
            return jsonify({"ok": False, "error": "No image provided"}), 400
        
        # Get parameters
        return_viz = request.args.get("return_visualization", "true").lower() == "true"
        colormap = request.args.get("colormap", "jet")
        return_depth = request.args.get("return_depth_map", "false").lower() == "true"
        
        # Estimate depth
        depth_map, metadata = estimator.estimate_depth(image)
        
        # Build response
        response = {
            "ok": True,
            "depth_metadata": metadata
        }
        
        # Add visualization
        if return_viz:
            depth_viz = estimator.visualize_depth(depth_map, colormap)
            _, buffer = cv2.imencode('.jpg', depth_viz)
            viz_b64 = base64.b64encode(buffer).decode('utf-8')
            response["visualization"] = f"data:image/jpeg;base64,{viz_b64}"
        
        # Add depth map (compressed)
        if return_depth:
            # Compress depth map
            depth_bytes = depth_map.tobytes()
            depth_b64 = base64.b64encode(depth_bytes).decode('utf-8')
            response["depth_map"] = depth_b64
            response["depth_map_shape"] = list(depth_map.shape)
            response["depth_map_dtype"] = str(depth_map.dtype)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in mono_depth_estimate: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@bp_mono_depth.post("/mono-depth/get-depth-at-point")
def mono_depth_at_point():
    """
    Get depth value at a specific pixel coordinate.
    
    Request body (JSON):
    {
        "image": "base64_encoded_image",
        "x": 320,
        "y": 240
    }
    
    Returns:
    {
        "ok": true,
        "depth_meters": 1.5,
        "depth_mm": 1500.0,
        "point": {"x": 320, "y": 240}
    }
    """
    try:
        estimator = get_depth_estimator()
        
        if not estimator.is_loaded:
            return jsonify({
                "ok": False,
                "error": "Depth model not loaded"
            }), 500
        
        # Parse request
        if not request.is_json:
            return jsonify({"ok": False, "error": "JSON body required"}), 400
        
        data = request.json
        image = _decode_image(request)
        if image is None:
            return jsonify({"ok": False, "error": "No image provided"}), 400
        
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        
        # Estimate depth
        depth_map, _ = estimator.estimate_depth(image)
        
        # Get depth at point
        if 0 <= y < depth_map.shape[0] and 0 <= x < depth_map.shape[1]:
            depth_meters = float(depth_map[y, x])
            depth_mm = depth_meters * 1000.0
        else:
            return jsonify({
                "ok": False,
                "error": f"Point ({x}, {y}) out of bounds. Image shape: {depth_map.shape}"
            }), 400
        
        return jsonify({
            "ok": True,
            "depth_meters": depth_meters,
            "depth_mm": depth_mm,
            "point": {"x": x, "y": y}
        })
    
    except Exception as e:
        logger.error(f"Error in mono_depth_at_point: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500

