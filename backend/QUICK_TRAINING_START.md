# Quick Start: Training Your Custom Model

## Fastest Path to Custom Detection

### 1. Collect Images (5-10 minutes)
```bash
cd backend

# Collect images for each item you want to detect
python collect_training_images.py --class espresso_cup --num 100
python collect_training_images.py --class latte_cup --num 100
python collect_training_images.py --class milk_bottle --num 100
```

### 2. Label Images (30-60 minutes)

**Option A: Use Roboflow (Easiest)**
1. Go to https://roboflow.com
2. Create free account
3. Upload your images
4. Label online (draw boxes)
5. Export as YOLOv11 format

**Option B: Use LabelImg**
```bash
pip install labelImg
labelImg
# Open your training_images folder
# Draw boxes, save as YOLO format
```

### 3. Organize Dataset (5 minutes)

```bash
mkdir -p datasets/barista/images/{train,val}

# Move 70% of labeled images to train/
# Move 20% to val/
```

### 4. Create dataset.yaml

Create `barista_dataset.yaml`:
```yaml
path: /Users/louisyu/barista/backend/datasets/barista
train: images/train
val: images/val

names:
  0: espresso_cup
  1: latte_cup
  2: milk_bottle

nc: 3
```

### 5. Train Model (1-4 hours)

```bash
python train_custom_model.py \
  --data barista_dataset.yaml \
  --model l \
  --epochs 100 \
  --device mps
```

### 6. Use Your Model

The trained model will automatically be used if it exists at:
- `runs/detect/barista_custom/weights/best.pt`

Or specify it manually:
```python
detector = ObjectDetector(model_path='runs/detect/barista_custom/weights/best.pt')
```

## That's It!

Your custom model will now detect your specific items with much better accuracy!

