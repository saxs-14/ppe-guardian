# PPE Guardian

Computer-vision workplace safety MVP: checks whether people in camera footage are wearing
required PPE (helmet, hi-vis vest), per configurable site rules.

## Problem statement

Manually walking a site to check PPE compliance doesn't scale, and incidents are often
discovered after the fact rather than prevented.

## Solution

Point a camera (or upload footage) at a work zone. Each detected person is checked against
that zone's required PPE items and logged as compliant or not, with a live dashboard and
CSV export for audits.

## Features

- Person detection via OpenCV DNN (MobileNet-SSD)
- PPE presence check (helmet, hi-vis vest) per person
- Configurable per-zone rules (construction / mining / warehouse ship by default)
- Compliance dashboard: daily percentage, event history
- CSV export
- Demo mode using a bundled real worker-zone video clip

## Architecture

```text
frontend (React/Vite/TS/Tailwind)  ->  backend (FastAPI)  ->  SQLite
                                              |
                       OpenCV DNN person detector -> colour heuristic (vest) +
                       colour heuristic OR trained MobileNetV2 classifier (helmet)
```

## Technology stack

Python, FastAPI, SQLAlchemy, SQLite, OpenCV (DNN module), PyTorch/TorchVision (helmet
classifier) on the backend; React, TypeScript, Vite, Tailwind CSS on the frontend. Same
MobileNet-SSD person detector as SafeSpeed AI.

## Folder structure

```text
ppe-guardian/
├── backend/
│   ├── app/
│   │   └── ml_model/  # Trained TorchScript helmet classifier (ppe_helmet_classifier.pt)
│   ├── models/        # MobileNet-SSD prototxt + caffemodel
│   ├── demo/           # Bundled demo video
│   └── tests/
├── frontend/
│   └── src/             # Landing page + dashboard
├── docker-compose.yml
└── README.md
```

## Installation

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Model files must exist at `backend/models/MobileNetSSD_deploy.{prototxt,caffemodel}` —
fetch instructions in SafeSpeed AI's README apply identically here.

```bash
cd frontend && npm install
```

## Environment variables

See `backend/.env.example`: `ZONE_RULES_JSON` (per-zone required items), `DEFAULT_ZONE`,
`UPLOAD_DIR`, `MAX_UPLOAD_MB`, `CORS_ORIGINS`.

## Running locally

```bash
# Terminal 1
cd backend && venv\Scripts\activate && uvicorn app.main:app --reload
# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173. Docker: `docker compose up --build`.

## Demo instructions

Click **Run demo clip** on the dashboard — no camera or upload required. The bundled clip
(`backend/demo/worker-zone-demo.mp4`) is real footage from the Intel IoT DevKit sample
video set (CC-BY 4.0), verified during development to reliably trigger person detection.

## API documentation

Docs at `/docs`. Key endpoints: `POST /api/analyze/demo`, `POST /api/analyze/image`,
`GET /api/events`, `GET /api/events/export`, `GET /api/dashboard/summary`.

## Database

SQLite: `analysis_sessions`, `compliance_events`.

## Security considerations

- **API key required on every endpoint except `/api/health`.** Set `API_KEY` (backend
  `.env`) and `VITE_API_KEY` (frontend `.env`) to the same value before deploying anywhere
  reachable outside your own machine — the default (`dev-local-key-change-me`) is for
  local development only. Single-tenant "licensed instance" model, not per-user accounts.
- Rate limiting (10 req/60s/IP) on `/api/analyze*`.
- Upload size/type validated server-side, CORS restricted, no secrets in source.

## Privacy considerations

Footage of workers is personal data. No facial recognition or identity matching is
performed — people are tracked only as anonymous frame-to-frame positions to avoid
double-counting, never linked to an identity. Deployers must post appropriate signage per
local workplace-monitoring law.

## Limitations

- **Helmet detection combines a colour heuristic with a trained MobileNetV2 classifier**
  (frozen ImageNet backbone + trained classifier head), fine-tuned on a public
  helmet/no-helmet dataset (320 images), reaching **92.2% held-out validation accuracy**.
  Helmet is flagged present if *either* signal fires. **The training dataset skews toward
  motorcycle-helmet photos, not construction hard hats** — a real domain shift (the same
  class of issue AgriVision hit, see that project's README) that hasn't been empirically
  re-verified against this project's own construction-site demo images the way AgriVision's
  was, so treat the model's real-world accuracy on hard hats as unverified, not equal to
  92.2%.
- **Vest detection is colour-heuristic only** — no real, publicly downloadable safety-vest
  image dataset was found in the time available, so it has none of the above. It will
  misfire on e.g. a yellow shirt (false positive) or a vest colour outside the configured
  ranges (false negative). A production system should source a labeled vest dataset (or
  collect one from the actual site cameras) and fine-tune a model the same way the helmet
  classifier was.
- Detector (MobileNet-SSD) is a lightweight 2017 model — best on eye-level/moderately
  elevated views; verified to work on the bundled demo clip.
- No liveness/anti-tamper checks — a photo of a compliant worker held up to the camera
  would currently pass.

## Business model

**Target customers**: construction sites, mining operations, manufacturing plants,
warehouses/logistics yards.

**Revenue**: per-camera monthly subscription, site-wide subscription, enterprise
multi-site licensing.

## Future improvements

- Source a real vest dataset and train a classifier, matching what's now done for helmets
- Re-verify the helmet classifier against real construction-site photos (it was trained on
  a motorcycle-helmet-skewed dataset) and retrain/fine-tune on-domain if accuracy drops
- Move to a proper object detector (YOLO) fine-tuned on real PPE images for both classes
- Add authentication/RBAC for the dashboard
- Live RTSP ingestion instead of upload-only
- Per-worker (not just per-frame) compliance history via badge/ID correlation, opt-in only

## Screenshots

Run locally (see "Running locally") and click **Run demo clip** on `/app`.
