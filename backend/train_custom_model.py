"""
Train a custom YOLOv11 model for barista robot object detection.

This script helps you train YOLOv11 on your custom dataset to detect
specific items like your cup types, ingredients, etc.
"""

from ultralytics import YOLO
import os
from pathlib import Path

def train_model(
    data_yaml: str,
    model_size: str = 'n',  # n, s, m, l, x
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = 'cpu',  # 'cpu', '0' for GPU, 'mps' for Apple Silicon
    project: str = 'runs/detect',
    name: str = 'barista_custom'
):
    """
    Train a custom YOLOv11 model.
    
    Args:
        data_yaml: Path to dataset YAML file (see dataset_format.yaml)
        model_size: Model size ('n', 's', 'm', 'l', 'x')
        epochs: Number of training epochs
        imgsz: Image size for training
        batch: Batch size
        device: Device to use ('cpu', '0' for GPU, 'mps' for Apple Silicon)
        project: Project directory
        name: Run name
    """
    print("=" * 60)
    print("YOLOv11 Custom Model Training")
    print("=" * 60)
    
    # Load pretrained model
    model_name = f'yolo11{model_size}.pt'
    print(f"\nLoading pretrained model: {model_name}")
    model = YOLO(model_name)
    
    # Check if dataset exists
    if not os.path.exists(data_yaml):
        print(f"\n❌ Error: Dataset file not found: {data_yaml}")
        print("\nCreate a dataset YAML file (see dataset_format.yaml)")
        return None
    
    print(f"\nDataset configuration: {data_yaml}")
    print(f"Model size: {model_size}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch}")
    print(f"Device: {device}")
    
    # Train the model
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        patience=50,  # Early stopping patience
        save=True,
        plots=True
    )
    
    print("\n" + "=" * 60)
    print("✅ Training completed!")
    print("=" * 60)
    
    # Best model path
    best_model = f"{project}/{name}/weights/best.pt"
    if os.path.exists(best_model):
        print(f"\nBest model saved at: {best_model}")
        print(f"\nTo use this model, update object_detection.py:")
        print(f"  detector = ObjectDetector(model_path='{best_model}')")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train custom YOLOv11 model')
    parser.add_argument('--data', type=str, required=True,
                       help='Path to dataset YAML file')
    parser.add_argument('--model', type=str, default='n',
                       choices=['n', 's', 'm', 'l', 'x'],
                       help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='Image size for training')
    parser.add_argument('--batch', type=int, default=16,
                       help='Batch size')
    parser.add_argument('--device', type=str, default='mps',
                       help='Device (cpu, 0 for GPU, mps for Apple Silicon)')
    parser.add_argument('--name', type=str, default='barista_custom',
                       help='Run name')
    
    args = parser.parse_args()
    
    train_model(
        data_yaml=args.data,
        model_size=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=args.name
    )

