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
if [ ! -f backend/models/clip.safetensors ]; then
  mkdir -p backend/models
  backend/.venv/bin/python -c "
import shutil, sys
sys.path.insert(0, 'backend')
import open_clip
from huggingface_hub import hf_hub_download
from pipeline.embeddings import MODEL_NAME, PRETRAINED
repo = open_clip.get_pretrained_cfg(MODEL_NAME, PRETRAINED)['hf_hub'].strip('/')
path = hf_hub_download(repo, 'open_clip_model.safetensors')
shutil.copyfile(path, 'backend/models/clip.safetensors')
"
fi

echo "==> Backend binary"
(cd backend && .venv/bin/pyinstaller atelier-backend.spec --noconfirm --log-level ERROR)

echo "==> Desktop app"
(cd frontend && npm ci && npm run tauri build -- --bundles app)

# Tauri copies resources with symlinks resolved, which duplicates the big
# PyTorch libraries (~400 MB). Re-copy the backend keeping its symlinks.
BUNDLE=frontend/src-tauri/target/release/bundle
APP="$BUNDLE/macos/Atelier.app"
rm -rf "$APP/Contents/Resources/backend"
ditto backend/dist/atelier-backend "$APP/Contents/Resources/backend"
codesign --force --deep --sign - "$APP"

echo "==> DMG"
VERSION=$(node -p "require('./frontend/src-tauri/tauri.conf.json').version")
STAGING=$(mktemp -d)
ditto "$APP" "$STAGING/Atelier.app"
ln -s /Applications "$STAGING/Applications"
mkdir -p "$BUNDLE/dmg"
DMG="$BUNDLE/dmg/Atelier_${VERSION}_$(uname -m).dmg"
hdiutil create -volname Atelier -srcfolder "$STAGING" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGING"

echo "Done: $DMG"
