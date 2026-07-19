# SDFL Demo — Polyp Segmentation + Uncertainty Viewer

This is the demo app your friend asked for: upload an endoscopy image, see the
predicted polyp segmentation and the MC Dropout uncertainty map.

## Folder structure
```
sdfl-demo/
  backend/
    app.py              <- FastAPI inference server
    model.py             <- (you add this: Sanjay's ResUNetPlusPlus)
    checkpoints/
      e8_final.pth        <- (you add this: the trained E8 checkpoint)
  frontend/
    index.html            <- the viewer UI, open directly in a browser
```

## Step 1 — Run it right now, with no trained model
The backend already works in **mock mode** — it fakes a plausible-looking
segmentation + uncertainty ring so you can test the whole UI today.

```bash
cd backend
pip install fastapi uvicorn python-multipart pillow numpy
uvicorn app:app --reload --port 8000
```

Then just open `frontend/index.html` in a browser (double-click it, or
`open frontend/index.html`). Upload any image — you'll see the mock overlay
and heatmap render, with a "MOCK MODE" badge in the top right so nobody
mistakes it for a real prediction.

## Step 2 — Swap in the real model once E8 is trained
1. Copy Sanjay's `model.py` (the file with `class ResUNetPlusPlus(nn.Module)`)
   into `backend/model.py`.
2. Copy `checkpoints/e8_final.pth` (from the E8 task in your plan) into
   `backend/checkpoints/e8_final.pth`.
3. Install the real ML deps: `pip install torch torchvision`.
4. Restart the server. The badge will flip to "REAL MODEL LOADED" automatically
   — `app.py` detects the checkpoint + model.py and switches out of mock mode
   with no code changes needed.

## What it actually computes (once real model is loaded)
- Preprocesses the upload: resize to 256×256, normalize with the same
  mean/std your augmentation pipeline uses.
- Runs the model **20 times** with dropout layers kept active (MC Dropout),
  per your E8 spec.
- Mean of the 20 output masks → the segmentation overlay (teal).
- Variance across the 20 outputs → the uncertainty heatmap (amber);
  higher variance = model disagrees with itself = flag for review.

## If you want this hosted instead of run locally
This is a plain FastAPI + static HTML app — it deploys as-is to any host that
runs Python (Render, Railway, a VM, etc.). Just make sure the checkpoint file
size fits your host's limits, and update `API_BASE` in `index.html` to point
at the deployed backend URL instead of `localhost:8000`.
