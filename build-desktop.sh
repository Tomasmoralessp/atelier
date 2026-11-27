#!/bin/bash
# Build the standalone desktop app (frontend + bundled backend + model weights).
# Output: frontend/src-tauri/target/release/bundle/
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Backend environment"
if [ ! -x backend/.venv/bin/python ]; then
  python3.11 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt pyinstaller
fi

echo "==> Model weights (downloaded once, bundled for offline use)"
if [ ! -f backend/models/RN50-openai.safetensors ]; then
  mkdir -p backend/models
  backend/.venv/bin/python -c "
from huggingface_hub import hf_hub_download
import shutil
path = hf_hub_download('timm/resnet50_clip.openai', 'open_clip_model.safetensors')
shutil.copy(path, 'backend/models/RN50-openai.safetensors')
"
fi

echo "==> Backend binary"
(cd backend && .venv/bin/pyinstaller atelier-backend.spec --noconfirm --log-level ERROR)

echo "==> Desktop app"
(cd frontend && npm ci && npm run tauri build)

echo "Done: frontend/src-tauri/target/release/bundle/"
