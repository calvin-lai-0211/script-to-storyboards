# Docker Deployment Guide

> 💡 **新功能：Docker Bake 支持**
> 本项目已支持 Docker Bake，提供更快的并行构建和共享缓存。
> 详见：[Docker Bake 构建指南](DOCKER-BAKE.md)

This guide explains how to deploy the Script-to-Storyboards application using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+ (推荐 2.17+ 以使用 Bake)
- Docker Buildx (Docker Desktop 自带)

## Quick Start

### 使用 Docker Bake（推荐）

```bash
# 方法 1: 使用构建脚本
./build.sh

# 方法 2: 让 Compose 自动使用 Bake
docker-compose build
docker-compose up -d
```

### 传统方式

### 1. Build Frontend

First, build the frontend locally to generate the `dist` directory:

```bash
cd frontend
npm install  # or: pnpm install
npm run build  # or: pnpm build
cd ..
```

### 2. Build and Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f frontend
```

### 3. Access the Application

- Frontend: http://localhost
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Architecture

```
┌─────────────┐     ┌──────────────┐
│  Frontend   │────▶│     API      │
│  (Nginx)    │     │  (FastAPI)   │
│   Port 80   │     │  Port 8000   │
└─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │   (External) │
                    └──────────────┘
```

## Configuration

### Environment Variables

#### API Service
The API uses configuration from `utils/config.py`. If you need to override database settings, you can add environment variables in `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - DB_HOST=your-database-host
      - DB_NAME=script_to_storyboards
      - DB_USER=postgres
      - DB_PASSWORD=your-password
```

#### Frontend Service
The frontend API URL is configured in the `.env` file before building. To change it:

1. Create/Edit `frontend/.env`:
```bash
VITE_API_BASE_URL=http://your-api-url:8000
```

2. Rebuild frontend:
```bash
cd frontend
npm run build
cd ..
docker-compose up -d --build frontend
```

### Production Deployment

For production, update `docker-compose.yml`:

1. **Remove development volumes** (comment out the volumes section in api service)
2. **Set proper API URL** in frontend build args
3. **Add SSL/TLS** using a reverse proxy like Traefik or Nginx Proxy Manager
4. **Set resource limits**:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Development Mode

For development with hot-reload:

```bash
# API: The volumes are already mounted in docker-compose.yml
docker-compose up api

# Frontend: Run locally with Vite dev server
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Check Service Health

```bash
# Check all services
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost/health
```

### View Container Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs frontend

# Follow logs
docker-compose logs -f api
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build api
```

## Network Architecture

- **storyboard-network**: Bridge network for internal service communication
- Frontend can access API via service name `api:8000`
- External access:
  - Frontend: `http://localhost:80`
  - API: `http://localhost:8000`

## Health Checks

Both services have health checks configured:

- **API**: Checks `/health` endpoint every 30s
- **Frontend**: Checks nginx health every 30s

View health status:
```bash
docker-compose ps
```

## Security Notes

1. **Change default passwords** in `utils/config.py` before deploying to production
2. **Use environment variables** for sensitive data instead of hardcoding
3. **Enable HTTPS** using a reverse proxy in production
4. **Limit exposed ports** - only expose what's necessary
5. **Update base images** regularly for security patches

## Nginx Configuration

The frontend uses Nginx with:
- Gzip compression
- Static asset caching (1 year)
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- SPA fallback routing
- Optional API proxy at `/api`

To modify nginx config, edit `frontend/nginx.conf` and rebuild.
