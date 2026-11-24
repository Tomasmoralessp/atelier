# Deployment Guide

## Building Desktop Applications

To build the desktop applications for Atelier Gallery:

1. Make sure you have Tauri CLI installed:
```bash
npm install -g @tauri-apps/cli
```

2. Build for all platforms:
```bash
cd frontend
npm run tauri build
```

3. The built applications will be located in:
```
frontend/src-tauri/target/release/bundle/
```

## Adding Built Applications to Git

To include the built executables in git:

1. Create a directory for releases:
```bash
mkdir -p releases/desktop
```

2. Copy the built files:
```bash
cp -r frontend/src-tauri/target/release/bundle/* releases/desktop/
```

3. Add to git:
```bash
git add releases/
git commit -m "Add built desktop applications"
git push origin main
```

## Docker Image Optimization

The Dockerfiles have been optimized for reduced image size:

- Using `python:3.9-slim` base images
- Multi-stage builds where appropriate
- `--no-cache-dir` for pip installations
- Using `npm ci --only=production` for frontend builds
- Removing unnecessary build dependencies

## Production Deployment

For production deployment, ensure:

1. Persistent data volume is configured properly
2. Environment variables are set correctly
3. Firewall rules allow necessary ports (8000 for API, 3000 for web)
4. SSL certificates are configured for HTTPS in production