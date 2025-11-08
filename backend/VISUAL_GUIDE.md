# What You Should See When a Cup is Detected

## Visual Indicators

When YOLOv11 detects a cup in your camera feed, you'll see:

### 1. **Green Bounding Box**
```
┌─────────────────┐
│                 │  ← Green rectangle around the cup
│      CUP        │
│                 │
└─────────────────┘
```

### 2. **Red Center Dot**
```
┌─────────────────┐
│                 │
│        •        │  ← Red dot at center (robot target point)
│                 │
└─────────────────┘
```

### 3. **Label Text**
```
cup (0.95)  ← Shows object name and confidence score
┌─────────────────┐
│                 │
│        •        │
│                 │
└─────────────────┘
```

## Complete Example

When a cup is detected, you'll see all three together:

```
cup (0.85)  ← Label at top of box
┌─────────────────┐
│                 │  ← Green box
│      CUP        │
│        •        │  ← Red center dot
│                 │
└─────────────────┘
```

## What the Colors Mean

- **Green Box**: Bounding box showing detected object boundaries
- **Red Dot**: Center point - this is where the robot arm will target
- **White Text**: Object name and confidence (0.0 to 1.0, higher is better)

## If No Cup is Detected

You'll see red text at the top of the screen:
```
No cup detected
```

Or if in "all objects" mode:
```
No objects detected
```

## Tips for Better Detection

1. **Good Lighting**: Make sure the cup is well-lit
2. **Clear View**: Cup should be clearly visible, not obscured
3. **Lower Confidence**: If nothing detected, press `-` to lower threshold
4. **Try "All Objects" Mode**: Press `a` to see everything YOLOv11 detects (not just cups)

## Expected Confidence Scores

- **0.7-1.0**: Very confident detection (excellent)
- **0.5-0.7**: Good detection (reliable)
- **0.3-0.5**: Weak detection (may be incorrect)
- **Below 0.3**: Usually filtered out

