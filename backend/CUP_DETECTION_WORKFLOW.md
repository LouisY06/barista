# Cup Detection Workflow

## What Happens When a Cup is Detected

### 1. Detection Phase (Current - Test Script)
```
Camera Frame → YOLOv11 Processing → Detection Result
```

**Visual Feedback:**
- ✅ Green bounding box around cup
- ✅ Red center point marker
- ✅ Confidence score label
- ✅ "No cup detected" message if nothing found

### 2. Robot Workflow (Production)

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Order Received                                  │
│ Backend sends: ORDER:ESPRESSO:MEDIUM:NONE               │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Robot Captures Image                            │
│ Camera takes photo of workspace                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: Send to Backend for Detection                  │
│ POST /api/robot/find-cup with image                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: YOLOv11 Detects Cup                            │
│ Returns: {"found": true, "center": {"x": 320, "y": 240}}│
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: Convert Pixel to Robot Coordinates             │
│ Pixel (320, 240) → Robot (X: 150mm, Y: 200mm, Z: 50mm) │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 6: Move Robot Arm to Cup Position                │
│ moveToPosition(150, 200, 50)                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 7: Lower Arm and Dispense Ingredients            │
│ - Lower to cup                                          │
│ - Dispense espresso                                     │
│ - Add milk (if needed)                                  │
│ - Stir (if needed)                                      │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ Step 8: Return to Home Position                       │
│ returnToHomePosition()                                  │
│ Send: STATUS:COMPLETE                                   │
└─────────────────────────────────────────────────────────┘
```

## Coordinate Conversion Example

**Camera Image (640x480 pixels):**
```
Cup detected at pixel (320, 240)
```

**Robot Workspace (calibrated):**
```
Workspace: 300mm x 400mm
Camera FOV: 60 degrees
Height: 500mm above workspace

Conversion:
- Pixel X (320) → Robot X: 150mm (from left edge)
- Pixel Y (240) → Robot Y: 200mm (from front edge)
- Z: 50mm (height above cup)
```

## Error Handling

**If no cup detected:**
- Robot sends: `CV:NO_CUP_FOUND`
- Robot waits or retries
- May request human intervention

**If multiple cups detected:**
- Robot selects cup with highest confidence
- Or selects cup closest to center of workspace
- Or uses first cup in detection list

## Current Test Script Behavior

When you run `test_camera_detection.py`:
- ✅ Shows visual feedback (bounding boxes, center point)
- ✅ Displays confidence scores
- ✅ Real-time detection from laptop camera
- ❌ Does NOT move robot arm (just visual testing)
- ❌ Does NOT execute drink sequence (testing only)

The test script is for **validating that YOLOv11 can detect cups correctly** before integrating with the actual robot hardware.

