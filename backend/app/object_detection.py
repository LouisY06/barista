"""
Object detection module using YOLOv11 for robot arm vision system.

This module handles:
- Cup/container detection
- Ingredient detection
- Workspace monitoring
- Quality control
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
from pathlib import Path


class ObjectDetector:
    """YOLOv11-based object detector for barista robot."""
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the object detector.
        
        Args:
            model_path: Path to custom YOLOv11 model. If None, uses pretrained YOLOv11n.
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.is_loaded = False
        
        # Load model
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
            print(f"Loaded custom YOLOv11 model from {model_path}")
        else:
            # Check for custom trained model first
            custom_model_paths = [
                'runs/detect/barista_custom/weights/best.pt',
                'runs/detect/barista_cups/weights/best.pt',
            ]
            
            custom_model = None
            for path in custom_model_paths:
                if os.path.exists(path):
                    custom_model = path
                    break
            
            if custom_model:
                self.model = YOLO(custom_model)
                print(f"Loaded custom trained model: {custom_model}")
            else:
                # Use YOLOv11n (nano) by default - fastest and smallest
                # For better accuracy on powerful machines, change to:
                # - 'yolo11s.pt' (Small) - Better accuracy, still fast
                # - 'yolo11m.pt' (Medium) - Good balance
                # - 'yolo11l.pt' (Large) - High accuracy
                # - 'yolo11x.pt' (Extra Large) - Best accuracy, slower inference
                self.model = YOLO('yolo11n.pt')  # Downloads automatically if not present
                print("Loaded YOLOv11n pretrained model")
                print("Note: Train custom model for better accuracy on your specific items")
                print("      See TRAINING_GUIDE.md for instructions")
        
        self.is_loaded = True
        
        # Define classes relevant to barista robot
        # These are COCO dataset classes - you can train custom model for specific objects
        self.relevant_classes = {
            'cup': 41,  # cup
            'bottle': 39,  # bottle
            'bowl': 40,  # bowl
            # Add more as needed
        }
    
    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        """
        Detect objects in an image.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detection dictionaries with keys:
            - class_id: Class ID
            - class_name: Class name
            - confidence: Confidence score
            - bbox: Bounding box [x1, y1, x2, y2]
            - center: Center point (x, y)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        # Run inference
        results = self.model(image, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Get class and confidence
                class_id = int(box.cls[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                # Calculate center point
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'center': [float(center_x), float(center_y)]
                }
                
                detections.append(detection)
        
        return detections
    
    def detect_cups(self, image: np.ndarray) -> List[Dict]:
        """
        Detect cups/containers in the image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of cup detections
        """
        all_detections = self.detect_objects(image)
        cup_detections = [
            det for det in all_detections 
            if det['class_name'] in ['cup', 'bottle', 'bowl'] or 
               det['class_id'] in self.relevant_classes.values()
        ]
        return cup_detections
    
    def detect_in_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> List[Dict]:
        """
        Detect objects in a specific region of interest.
        
        Args:
            image: Input image
            region: Region of interest as (x1, y1, x2, y2)
            
        Returns:
            List of detections within the region
        """
        x1, y1, x2, y2 = region
        roi = image[y1:y2, x1:x2]
        
        detections = self.detect_objects(roi)
        
        # Adjust coordinates to full image space
        for det in detections:
            det['bbox'][0] += x1
            det['bbox'][1] += y1
            det['bbox'][2] += x1
            det['bbox'][3] += y1
            det['center'][0] += x1
            det['center'][1] += y1
        
        return detections
    
    def annotate_image(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on image.
        
        Args:
            image: Input image
            detections: List of detection dictionaries
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw center point
            center_x, center_y = map(int, det['center'])
            cv2.circle(annotated, (center_x, center_y), 5, (255, 0, 0), -1)
        
        return annotated
    
    def load_custom_model(self, model_path: str):
        """
        Load a custom trained YOLOv11 model.
        
        Args:
            model_path: Path to custom model file (.pt)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        self.model = YOLO(model_path)
        print(f"Loaded custom model from {model_path}")
        self.is_loaded = True


# Global detector instance
_detector: Optional[ObjectDetector] = None


def get_detector(model_path: Optional[str] = None, confidence: float = 0.5) -> ObjectDetector:
    """
    Get or create the global detector instance.
    
    Args:
        model_path: Optional path to custom model
        confidence: Confidence threshold
        
    Returns:
        ObjectDetector instance
    """
    global _detector
    
    if _detector is None:
        _detector = ObjectDetector(model_path=model_path, confidence_threshold=confidence)
    
    return _detector


def detect_from_file(image_path: str) -> List[Dict]:
    """
    Detect objects from an image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        List of detections
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    detector = get_detector()
    return detector.detect_objects(image)


def detect_from_array(image_array: np.ndarray) -> List[Dict]:
    """
    Detect objects from a numpy array.
    
    Args:
        image_array: Image as numpy array (BGR format)
        
    Returns:
        List of detections
    """
    detector = get_detector()
    return detector.detect_objects(image_array)

