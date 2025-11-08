"""
Helper functions for robot-to-backend CV communication.

This module provides utilities for robots to easily communicate with the backend
for object detection tasks.
"""

import requests
import base64
from typing import Optional, Dict, Tuple
from pathlib import Path


class RobotCVClient:
    """
    Client for robot to communicate with backend CV system.
    
    This can be used by robots (like Raspberry Pi, ESP32-CAM, etc.) to send
    images to the backend for object detection.
    """
    
    def __init__(self, backend_url: str = "http://localhost:5001"):
        """
        Initialize the robot CV client.
        
        Args:
            backend_url: Base URL of the backend server
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_base = f"{self.backend_url}/api"
    
    def find_cup(self, image_path: Optional[str] = None, 
                  image_bytes: Optional[bytes] = None,
                  image_base64: Optional[str] = None,
                  confidence: float = 0.5) -> Dict:
        """
        Find a cup in an image.
        
        Args:
            image_path: Path to image file
            image_bytes: Image as bytes
            image_base64: Image as base64 string
            confidence: Confidence threshold
            
        Returns:
            Dictionary with cup coordinates or error
        """
        url = f"{self.api_base}/robot/find-cup?confidence={confidence}"
        
        # Prepare image data
        files = None
        data = None
        
        if image_path:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(url, files=files)
        elif image_bytes:
            files = {'image': ('image.jpg', image_bytes, 'image/jpeg')}
            response = requests.post(url, files=files)
        elif image_base64:
            # Remove data URL prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            data = {'image': image_base64}
            response = requests.post(url, json=data)
        else:
            raise ValueError("Must provide image_path, image_bytes, or image_base64")
        
        response.raise_for_status()
        return response.json()
    
    def detect_objects(self, image_path: Optional[str] = None,
                      image_bytes: Optional[bytes] = None,
                      image_base64: Optional[str] = None,
                      object_type: str = 'cup',
                      confidence: float = 0.5) -> Dict:
        """
        Detect objects in an image.
        
        Args:
            image_path: Path to image file
            image_bytes: Image as bytes
            image_base64: Image as base64 string
            object_type: Type of object to detect ('cup', 'all', etc.)
            confidence: Confidence threshold
            
        Returns:
            Dictionary with detection results
        """
        url = f"{self.api_base}/robot/detect-objects?object_type={object_type}&confidence={confidence}"
        
        files = None
        data = None
        
        if image_path:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(url, files=files)
        elif image_bytes:
            files = {'image': ('image.jpg', image_bytes, 'image/jpeg')}
            response = requests.post(url, files=files)
        elif image_base64:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            data = {'image': image_base64}
            response = requests.post(url, json=data)
        else:
            raise ValueError("Must provide image_path, image_bytes, or image_base64")
        
        response.raise_for_status()
        return response.json()
    
    def get_cup_coordinates(self, image_path: Optional[str] = None,
                           image_bytes: Optional[bytes] = None,
                           image_base64: Optional[str] = None,
                           confidence: float = 0.5) -> Optional[Tuple[int, int]]:
        """
        Get cup coordinates as a simple tuple (x, y).
        
        Returns None if no cup found, otherwise returns (x, y) coordinates.
        
        Args:
            image_path: Path to image file
            image_bytes: Image as bytes
            image_base64: Image as base64 string
            confidence: Confidence threshold
            
        Returns:
            Tuple of (x, y) coordinates or None
        """
        try:
            result = self.find_cup(image_path, image_bytes, image_base64, confidence)
            if result.get('found'):
                center = result['center']
                return (center['x'], center['y'])
        except Exception as e:
            print(f"Error finding cup: {e}")
        
        return None


# Example usage for robots
def example_robot_usage():
    """
    Example of how a robot would use the CV client.
    
    This would typically run on the robot (Raspberry Pi, ESP32, etc.)
    """
    # Initialize client
    client = RobotCVClient(backend_url="http://192.168.1.100:5000")
    
    # Option 1: From image file
    result = client.find_cup(image_path="/path/to/camera/image.jpg")
    if result.get('found'):
        x, y = result['center']['x'], result['center']['y']
        print(f"Cup found at: ({x}, {y})")
        # Move robot arm to position
    else:
        print("No cup found")
    
    # Option 2: From camera capture (bytes)
    # camera.capture() returns image bytes
    # image_bytes = camera.capture()
    # result = client.find_cup(image_bytes=image_bytes)
    
    # Option 3: Simple coordinate extraction
    # coords = client.get_cup_coordinates(image_path="image.jpg")
    # if coords:
    #     x, y = coords
    #     move_robot_arm(x, y)

