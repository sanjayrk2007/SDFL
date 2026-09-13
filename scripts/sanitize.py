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

    # Define corner regions:
    # top_region    = rows 0 to int(H * 0.10), full width
    # bottom_region = rows int(H * 0.90) to H, full width
    top_limit = int(H * 0.10)
    bottom_limit = int(H * 0.90)

    kept_rects = []
    total_inpaint_pixels = 0

    # Process top region
    top_region = gray[0:top_limit, :]
    if top_region.size > 0:
        _, thresh_top = cv2.threshold(top_region, 200, 255, cv2.THRESH_BINARY)
        contours_top, _ = cv2.findContours(thresh_top, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours_top:
            x, y, w, h = cv2.boundingRect(c)
            if w > 20 and h > 8:
                kept_rects.append((x, y, w, h))
                total_inpaint_pixels += w * h

    # Process bottom region
    bottom_region = gray[bottom_limit:H, :]
    if bottom_region.size > 0:
        _, thresh_bottom = cv2.threshold(bottom_region, 200, 255, cv2.THRESH_BINARY)
        contours_bottom, _ = cv2.findContours(thresh_bottom, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours_bottom:
            x, y, w, h = cv2.boundingRect(c)
            if w > 20 and h > 8:
                # Map bounding rect coordinates back to full image coordinate space
                mapped_y = y + bottom_limit
                kept_rects.append((x, mapped_y, w, h))
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
    # inpaint_ratio = total_inpaint_pixels / (H * W)
    inpaint_ratio = total_inpaint_pixels / (H * W) if (H * W) > 0 else 0.0
    # If inpaint_ratio > 0.05: passed = False, else: passed = True
    passed = inpaint_ratio <= 0.05

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
