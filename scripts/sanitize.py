import cv2
import numpy as np
import PIL.Image

def sanitize(image: PIL.Image.Image) -> tuple[PIL.Image.Image, bool]:
    # 1. CLAHE Enhancement
    # Convert PIL image to numpy array RGB uint8. If image is grayscale, convert to RGB first
    if image.mode != "RGB":
        image = image.convert("RGB")
    img_np = np.array(image, dtype=np.uint8)

    # Convert RGB -> LAB
    lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    # Split into L, A, B channels
    l, a, b = cv2.split(lab)
    # Apply cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)) to L only
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    # Merge channels, convert LAB -> RGB
    merged = cv2.merge((cl, a, b))
    img_np = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)

    # 2. Text Artifact Removal
    # Convert to grayscale for detection only
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    H, W = gray.shape[:2]

    kept_rects = []
    total_inpaint_pixels = 0

    # Process entire image for bright text overlays (val > 180)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    # Dilate to merge individual letters into text blocks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 20 and h > 10:
            kept_rects.append((x, y, w, h))
            total_inpaint_pixels += w * h

    # Build binary inpaint mask: zeros image same H x W as input, fill 255 inside each kept bounding rect
    mask = np.zeros((H, W), dtype=np.uint8)
    for x, y, w, h in kept_rects:
        mask[y:y+h, x:x+w] = 255

    # If any rects found: inpaint the image
    if len(kept_rects) > 0:
        img_np = cv2.inpaint(img_np, mask, 3, cv2.INPAINT_TELEA)

    # 3. Metadata Scrub
    # Convert numpy array back to PIL Image (mode RGB)
    sanitized_pil_image = PIL.Image.fromarray(img_np, mode="RGB")
    # Set image.info = {}
    sanitized_pil_image.info = {}

    # 4. PHI Gate
    inpaint_ratio = total_inpaint_pixels / (H * W) if (H * W) > 0 else 0.0
    passed = inpaint_ratio <= 0.15

    return sanitized_pil_image, passed

def test_sanitize():
    img = PIL.Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
    out, passed = sanitize(img)
    assert isinstance(out, PIL.Image.Image)
    assert isinstance(passed, bool)
    assert out.size == (256, 256)
    print("sanitize() self-test passed")

if __name__ == "__main__":
    test_sanitize()
