# Training Custom YOLOv11 Model for Barista Robot

This guide will help you train YOLOv11 to detect your specific items (cups, ingredients, etc.) with better accuracy.

## Overview

Training a custom model involves:
1. **Collecting images** of your items
2. **Labeling images** with bounding boxes
3. **Organizing dataset** in YOLO format
4. **Training the model**
5. **Using the trained model**

## Step 1: Collect Images

### Option A: Use Your Camera Script
```bash
cd backend
python collect_training_images.py
```

### Option B: Manual Collection
- Take 100-500+ photos of each item you want to detect
- Include different:
  - Angles
  - Lighting conditions
  - Backgrounds
  - Item positions
  - Variations (different cup types, etc.)

**Recommended:**
- **Minimum**: 100 images per class
- **Better**: 300+ images per class
- **Best**: 500+ images per class

## Step 2: Label Images

You need to draw bounding boxes around objects in each image.

### Recommended Tools:

1. **LabelImg** (Free, Simple)
   ```bash
   pip install labelImg
   labelImg
   ```
   - Open image folder
   - Draw boxes around objects
   - Save as YOLO format (.txt files)

2. **Roboflow** (Web-based, Easy)
   - Go to https://roboflow.com
   - Upload images
   - Label online
   - Export as YOLOv11 format

3. **CVAT** (Advanced)
   - More features
   - Good for teams

### Labeling Process:
1. Open each image
2. Draw bounding box around object
3. Assign class label (e.g., "espresso_cup", "milk_bottle")
4. Save annotation (creates .txt file with same name as image)

### YOLO Label Format:
Each image needs a `.txt` file with same name:
```
class_id center_x center_y width height
```
Example: `0 0.5 0.5 0.3 0.4`
- All values are normalized (0.0 to 1.0)
- `center_x, center_y` = center of box
- `width, height` = box dimensions

## Step 3: Organize Dataset

Create this folder structure:

```
your_dataset/
├── images/
│   ├── train/          # 70% of images
│   │   ├── img001.jpg
│   │   ├── img001.txt  # Label file
│   │   ├── img002.jpg
│   │   └── img002.txt
│   ├── val/            # 20% of images
│   │   ├── img101.jpg
│   │   └── img101.txt
│   └── test/           # 10% of images (optional)
│       ├── img201.jpg
│       └── img201.txt
```

**Split your data:**
- 70% training
- 20% validation
- 10% test (optional)

## Step 4: Create Dataset YAML

Create `barista_dataset.yaml`:

```yaml
path: /Users/louisyu/barista/backend/datasets/barista
train: images/train
val: images/val

names:
  0: espresso_cup
  1: latte_cup
  2: cappuccino_cup
  3: milk_bottle
  4: espresso_machine

nc: 5
```

## Step 5: Train the Model

### Quick Start:
```bash
cd backend
python train_custom_model.py --data barista_dataset.yaml --model l --epochs 100 --device mps
```

### Parameters:
- `--data`: Path to your dataset YAML
- `--model`: Model size (`n`=nano, `s`=small, `m`=medium, `l`=large, `x`=xlarge)
  - Use `l` or `x` for better accuracy on powerful machines
- `--epochs`: Number of training iterations (100-300 recommended)
- `--device`: 
  - `mps` for Apple Silicon (M1/M2/M3)
  - `0` for NVIDIA GPU
  - `cpu` for CPU only
- `--batch`: Batch size (reduce if out of memory)

### Training Time:
- **Nano (n)**: ~30 min - 2 hours
- **Large (l)**: ~2-6 hours
- **XLarge (x)**: ~4-10 hours

## Step 6: Use Your Trained Model

After training, the best model is saved at:
```
runs/detect/barista_custom/weights/best.pt
```

### Update object_detection.py:
```python
# In object_detection.py, change:
self.model = YOLO('yolo11n.pt')  # Old

# To:
self.model = YOLO('runs/detect/barista_custom/weights/best.pt')  # New
```

Or use it directly:
```python
from app.object_detection import ObjectDetector

detector = ObjectDetector(
    model_path='runs/detect/barista_custom/weights/best.pt',
    confidence_threshold=0.5
)
```

## Tips for Better Results

1. **More Data = Better Results**
   - Collect diverse images
   - Include edge cases (weird angles, lighting)

2. **Good Labels**
   - Tight bounding boxes
   - Consistent labeling
   - Label all instances in image

3. **Data Augmentation**
   - YOLOv11 does this automatically
   - Rotations, flips, color changes

4. **Model Size**
   - Start with `n` (nano) for quick testing
   - Use `l` or `x` for production

5. **Training Time**
   - Monitor validation loss
   - Stop if overfitting (val loss increases)

## Example: Training for Cup Detection

```bash
# 1. Collect images
python collect_training_images.py

# 2. Label with LabelImg
labelImg

# 3. Organize dataset
mkdir -p datasets/barista/images/{train,val}
# Move 70% to train, 20% to val

# 4. Create dataset.yaml
# (see example above)

# 5. Train
python train_custom_model.py \
  --data barista_dataset.yaml \
  --model l \
  --epochs 150 \
  --device mps \
  --name barista_cups

# 6. Use trained model
# Update object_detection.py to use best.pt
```

## Troubleshooting

**Out of Memory:**
- Reduce `--batch` size (try 8, 4, or 2)
- Use smaller model (`n` or `s`)
- Reduce `--imgsz` (try 416 instead of 640)

**Poor Results:**
- Collect more training data
- Check label quality
- Try larger model (`l` or `x`)
- Train for more epochs

**Training Too Slow:**
- Use GPU if available (`--device 0`)
- Use Apple Silicon (`--device mps`)
- Use smaller model for testing

