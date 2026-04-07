#!/usr/bin/env python3
"""Test screenshot capture and state detection."""

from PIL import Image
from vision import PILScreenCapture, Region
from state_detector import SimpleGameStateDetector

print("=" * 60)
print("Screenshot Capture & State Detection Test")
print("=" * 60)

# Test 1: Screenshot capture
print("\n[Test 1] Screenshot Capture")
try:
    capture = PILScreenCapture()
    screenshot = capture.capture_fullscreen()
    print(f"  Screenshot captured: {screenshot.size}")
    print(f"  Format: {screenshot.format}")
    print("  [PASS]")
except Exception as e:
    print(f"  [FAIL] {e}")

# Test 2: State detection on reference images
print("\n[Test 2] State Detection on Reference Images (using SimpleGameStateDetector)")
try:
    detector = SimpleGameStateDetector(screens_dir="screens")
    print(f"  Loaded {len(detector.reference_states)} reference states")
    
    # Test on each reference image
    for state_name, ref_img in detector.reference_states.items():
        print(f"\n  Testing {state_name.name}...")
        # Convert numpy array back to PIL Image
        from PIL import Image as PILImage
        import numpy as np
        
        # ref_img is grayscale, convert to RGB for PIL Image
        ref_img_rgb = np.stack([ref_img] * 3, axis=-1)
        img_pil = PILImage.fromarray(ref_img_rgb.astype('uint8'))
        
        detected_state, confidence = detector.detect_state(img_pil)
        print(f"    Expected: {state_name.name}")
        print(f"    Detected: {detected_state.name}")
        print(f"    Confidence: {confidence:.3f}")
        
        if detected_state == state_name:
            print(f"    [PASS]")
        else:
            print(f"    [FAIL - Wrong state]")
    
except Exception as e:
    print(f"  [FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 3: Capture a screen region
print("\n[Test 3] Region Capture")
try:
    capture = PILScreenCapture()
    # Capture a small region in the center of screen
    region = Region(x=800, y=400, width=320, height=240)
    cropped = capture.capture_region(region)
    print(f"  Region captured: {cropped.size}")
    print("  [PASS]")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n" + "=" * 60)
print("Test Suite Complete")
print("=" * 60)
