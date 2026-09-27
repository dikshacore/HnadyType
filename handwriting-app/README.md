# Handwriting synthesis app — starter scaffold

## Structure

- `backend/` — FastAPI service: enrollment scanning pipeline, glyph storage, generation API
- `frontend/` — Next.js app: signup/login, enrollment wizard, glyph review, generator UI

## Backend setup

```
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# create a .env with DATABASE_URL, JWT_SECRET, storage credentials (see app/config.py)
uvicorn app.main:app --reload
```

Generate the printable enrollment sheets:
```
cd backend/enrollment_sheets
python generate_sheets.py
```

## Frontend setup

```
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE` in `.env.local` if the backend isn't on `http://localhost:8000`.

## What's stubbed and needs a real implementation next

- **Object storage** (`storage.upload` / `storage.download` calls throughout `enrollment_pipeline.py` and `routers/generate.py`) — wire up S3/MinIO/R2 via boto3.
- **Vectorization** (`services/vectorize.py`) — shell out to `potrace` on each binary glyph crop.
- **Confidence classifier** (`services/classifier.py`) — train a small CNN on EMNIST + your own accumulating review-corrected data, then load it in `ConfidenceClassifier._load_model`.
- **PNG/PDF export** (`routers/generate.py`) — rasterize the generated SVG server-side (e.g. `cairosvg`).
- **Corner/fiducial detection in the browser** (`SheetUpload.tsx`'s `quickQualityCheck`) — currently just checks resolution; upgrade to real corner detection with opencv.js if you want stronger pre-upload validation.

## Where the "coarticulation" fix lives

Both `backend/app/services/renderer.py` and `frontend/lib/svgRenderer.ts` implement the same resolution order: whole-word crop → bigram crop → single-glyph stitching. This is what keeps generated text from looking like independently stamped letters — see the technical approach discussion for why.

## Roadmap after this scaffold works end to end

1. Get Option A (glyph stitching) fully working and shippable.
2. Start collecting cross-user review-corrected labels to train a real confidence classifier.
3. Evaluate investing in the style-transfer generative model (Stage 2 of the ML roadmap) once you have real usage data.
