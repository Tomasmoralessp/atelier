# Installation Guide

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.9+
- Git

### Quick Start

```bash
# Clone repository
git clone <https://github.com/Tomasmoralessp/atelier.git>
cd atelier

# Start development environment
docker-compose up -d

# Access services
- Web UI: http://localhost:3000
- API: http://localhost:8000
```

### Manual Setup (without Docker)

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend setup
cd frontend
npm install
npm run dev
```

## NAS Deployment

### Prerequisites for NAS

- Docker support on your NAS
- Sufficient RAM (minimum 2GB)
- Stable internet connection for model downloads
- Port availability (8000 for API, 3000 for web)

### Configuration

The application is configurable through environment variables. Create a `.env` file in the root directory:

```bash
# Example .env configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000
DATA_DIR=/volume1/atelier_gallery
```

### Running on NAS

```bash
# Clone and configure
git clone <repository-url>
cd atelier

# Update docker-compose.yml with your NAS paths
# Then start services
docker-compose up -d
```

## Environment Variables

### Backend Configuration

- `PYTHONPATH=/app` - Python path for imports
- `DATABASE_URL` - PostgreSQL connection string (if different from default)
- `CACHE_DIR` - Directory for cached embeddings (default: pipeline/cache)

### Frontend Configuration

- `VITE_API_URL` - API endpoint URL
- `VITE_APP_NAME` - Application name

## Resource Requirements

### Local Development

- RAM: 2GB minimum
- Storage: 500MB+ for application data
- CPU: Modern processor

### NAS Deployment

- RAM: 2GB minimum (recommended 4GB)
- Storage: 1GB+ for application and cache
- Network: Stable connection for initial model downloads

## Troubleshooting

### Model Download Issues

If models fail to download:

```bash
# Manually download models to cache directory
mkdir -p backend/pipeline/cache
# Add model files manually if needed
```

### Port Conflicts

```bash
# Change ports in docker-compose.yml
# Or stop existing processes
sudo lsof -i :8000
sudo kill -9 <PID>
```

## Performance Tuning

### For Resource-Constrained Environments

1. Reduce batch sizes in `backend/pipeline/embeddings.py`
2. Adjust cache directory location to faster storage
3. Monitor memory usage with Docker stats

### Memory Optimization

```bash
# Check current usage
docker stats atelier_backend

# Limit container memory
docker run --memory="1g" <image-name>
```

## Backup and Recovery

### Data Backup

```bash
# Backup database
docker exec fastapi_backend pg_dump -U postgres atelier > backup.sql

# Backup data directory
tar -czf atelier_backup.tar.gz ~/atelier_gallery
```

### Restore Process

1. Restore database from SQL dump
2. Restore data directory to `~/atelier_gallery`
3. Restart containers
