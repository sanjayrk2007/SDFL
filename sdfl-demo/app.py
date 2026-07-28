"""
SDFL Demo Backend — polyp segmentation + MC Dropout uncertainty
=================================================================

WHAT THIS DOES
  - Accepts an uploaded endoscopy image
  - Runs N=20 MC Dropout forward passes through ResUNet++
  - Returns: mean segmentation mask + per-pixel uncertainty (variance) map
  - Falls back to a MOCK inference if no real checkpoint is found, so the
    frontend can be demoed today even before e8_final.pth exists.

HOW TO PLUG IN THE REAL MODEL (once E8 checkpoint is ready)
  1. Copy Sanjay's model.py (ResUNetPlusPlus class) into this backend/ folder.
  2. Copy checkpoints/e8_final.pth into backend/checkpoints/e8_final.pth
  3. That's it — REAL_MODEL_AVAILABLE will flip to True automatically and
     mock mode turns off.

RUN
  cd backend
  pip install fastapi uvicorn python-multipart pillow numpy torch torchvision
  uvicorn app:app --reload --port 8000

Frontend expects this server at http://localhost:8000
"""

import base64
import io
import os
from typing import Tuple

import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw

app = FastAPI(title="SDFL Polyp Segmentation Demo")

# Allow the frontend (opened as a local file or on another port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

IMG_SIZE = 256
N_MC_PASSES = 20
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "e8_final.pth")
MODEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "model.py")

REAL_MODEL_AVAILABLE = os.path.exists(CHECKPOINT_PATH) and os.path.exists(MODEL_FILE_PATH)

_model = None
_torch = None
_transform = None


def convert_bn_to_gn(model, num_groups=4):
    import torch
    import torch.nn as nn
    for name, module in model.named_children():
        if isinstance(module, nn.BatchNorm2d):
            device = module.weight.device if module.weight is not None else torch.device("cpu")
            gn = nn.GroupNorm(num_groups=num_groups, num_channels=module.num_features).to(device)
            if module.weight is not None:
                gn.weight.data.copy_(module.weight.data)
            if module.bias is not None:
                gn.bias.data.copy_(module.bias.data)
            setattr(model, name, gn)
        else:
            convert_bn_to_gn(module, num_groups)

def disable_inplace_relu(model):
    import torch.nn as nn
    for name, module in model.named_children():
        if isinstance(module, nn.ReLU):
            module.inplace = False
        else:
            disable_inplace_relu(module)

def fix_model_for_opacus(model):
    convert_bn_to_gn(model, num_groups=4)
    disable_inplace_relu(model)

def _lazy_load_real_model():
    """Import torch + Sanjay's ResUNetPlusPlus + checkpoint, only if available."""
    global _model, _torch, _transform
    if _model is not None:
        return

    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import transforms

    _torch = torch
    _transform = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # model.py must define: class ResUNetPlusPlus(nn.Module)
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from model import ResUNetPlusPlus  # noqa: E402

    net = ResUNetPlusPlus()
    fix_model_for_opacus(net)
    
    state = torch.load(CHECKPOINT_PATH, map_location="cpu")
    net.load_state_dict(state)
    net.eval()

    # Patch in nn.Dropout layers before final Conv2d(1,1) if not already present
    # Exact logic matching e8_server.py:MCDropoutInference
    has_dropout = any(isinstance(layer, (nn.Dropout, nn.Dropout2d)) for layer in net.output_head)
    if not has_dropout:
        new_head = nn.Sequential(
            nn.Dropout(p=0.5),
            *list(net.output_head)
        )
        net.output_head = new_head

    # Keep dropout layers active for MC Dropout while everything else stays in eval mode
    for m in net.modules():
        if isinstance(m, (nn.Dropout, nn.Dropout2d)):
            m.train()

    _model = net


def _run_real_inference(img: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
    """Returns (mean_mask [H,W] in [0,1], uncertainty [H,W] variance)."""
    from scipy.ndimage import gaussian_filter

    _lazy_load_real_model()
    x = _transform(img).unsqueeze(0)  # (1, 3, 256, 256)

    preds = []
    with _torch.no_grad():
        for _ in range(N_MC_PASSES):
            out = _model(x)  # (1, 1, 256, 256), sigmoid already applied per spec
            preds.append(out.squeeze().cpu().numpy())

    stacked = np.stack(preds, axis=0)  # (N, H, W)
    mean_mask = stacked.mean(axis=0)
    raw_uncertainty = stacked.var(axis=0)

    # Apply spatial Gaussian filter to smooth high-frequency dropout noise
    smoothed_unc = gaussian_filter(raw_uncertainty, sigma=2.0)

    # Focus uncertainty on predicted lesion regions & boundaries (gradient-weighted spatial calibration)
    grad_y, grad_x = np.gradient(mean_mask)
    boundary_weight = np.abs(grad_y) + np.abs(grad_x)
    boundary_weight = boundary_weight / (boundary_weight.max() + 1e-8)

    uncertainty = smoothed_unc * (0.1 + 0.9 * (mean_mask + boundary_weight))
    return mean_mask, uncertainty


def _run_mock_inference(img: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
    """
    Deterministic, plausible-looking placeholder so the UI is fully testable
    before the real e8_final.pth checkpoint exists. Produces an elliptical
    'lesion' blob roughly in the image's brightest region, plus a ring of
    elevated uncertainty around its boundary (mimicking real MC Dropout
    behaviour, where uncertainty concentrates at segmentation edges).
    """
    gray = np.array(img.convert("L").resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32) / 255.0

    yy, xx = np.mgrid[0:IMG_SIZE, 0:IMG_SIZE]
    # center the blob near the brightest patch, offset toward image center for stability
    cy, cx = IMG_SIZE * 0.55, IMG_SIZE * 0.48
    ry, rx = IMG_SIZE * 0.16, IMG_SIZE * 0.13

    dist = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2
    mean_mask = np.clip(1.2 - dist, 0, 1) ** 2
    mean_mask = mean_mask * (0.6 + 0.4 * gray)  # let underlying image brightness modulate it
    mean_mask = np.clip(mean_mask, 0, 1)

    # uncertainty ring at the mask boundary (dist ~ 1.0)
    uncertainty = np.exp(-((dist - 1.0) ** 2) / 0.08) * 0.15
    return mean_mask, uncertainty


def _colorize_mask(base_img: Image.Image, mask: np.ndarray, color=(45, 212, 191), alpha=0.45) -> Image.Image:
    """Overlay a translucent colored mask on top of the base image."""
    base = base_img.convert("RGBA").resize((IMG_SIZE, IMG_SIZE))
    overlay = Image.new("RGBA", (IMG_SIZE, IMG_SIZE), (0, 0, 0, 0))
    mask_img = (mask * 255).astype(np.uint8)
    alpha_channel = (mask_img * alpha).astype(np.uint8)
    color_layer = np.zeros((IMG_SIZE, IMG_SIZE, 4), dtype=np.uint8)
    color_layer[..., 0] = color[0]
    color_layer[..., 1] = color[1]
    color_layer[..., 2] = color[2]
    color_layer[..., 3] = alpha_channel
    overlay = Image.fromarray(color_layer, mode="RGBA")
    return Image.alpha_composite(base, overlay)


def _heatmap(mask: np.ndarray) -> Image.Image:
    """Render a variance map as an amber-on-dark heatmap."""
    norm = mask / (mask.max() + 1e-8)
    rgb = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    rgb[..., 0] = (norm * 245).astype(np.uint8)   # R
    rgb[..., 1] = (norm * 166).astype(np.uint8)   # G
    rgb[..., 2] = (norm * 35).astype(np.uint8)    # B
    return Image.fromarray(rgb, mode="RGB")


def _to_base64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "real_model_available": REAL_MODEL_AVAILABLE}


@app.get("/metrics")
def get_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "results", "e8_metrics.json")
    if os.path.exists(metrics_path):
        import json
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"error": "metrics_file_not_found"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid or corrupted image file uploaded."}
        )

    if REAL_MODEL_AVAILABLE:
        mean_mask, uncertainty = _run_real_inference(img)
    else:
        mean_mask, uncertainty = _run_mock_inference(img)

    # Ensure mask is strictly bounded in [0, 1]
    mean_mask = np.clip(mean_mask, 0.0, 1.0)

    # Apply spatial Gaussian smoothing to reduce high-frequency pixel noise
    from scipy.ndimage import gaussian_filter
    uncertainty = gaussian_filter(uncertainty, sigma=2.5)
    uncertainty = uncertainty / (uncertainty.max() + 1e-8)

    overlay_img = _colorize_mask(img, mean_mask)
    heatmap_img = _heatmap(uncertainty)

    # Confidence calculation: Mean probability of predicted lesion foreground (where probability > 0.3)
    # If no region exceeds 0.3 threshold (weak prediction), fall back to top 2% mean
    foreground = mean_mask[mean_mask > 0.3]
    if foreground.size > 0:
        dice_proxy = float(np.mean(foreground))
    else:
        top_pixels = np.sort(mean_mask.ravel())[-int(mean_mask.size * 0.02):]
        dice_proxy = float(np.mean(top_pixels)) if top_pixels.size > 0 else 0.0
    mean_uncertainty = float(uncertainty.mean())

    return JSONResponse(
        {
            "mode": "real" if REAL_MODEL_AVAILABLE else "mock",
            "overlay_png_base64": _to_base64_png(overlay_img),
            "heatmap_png_base64": _to_base64_png(heatmap_img),
            "peak_confidence": round(dice_proxy, 3),
            "mean_uncertainty": round(mean_uncertainty, 4),
            "n_mc_passes": N_MC_PASSES,
        }
    )

