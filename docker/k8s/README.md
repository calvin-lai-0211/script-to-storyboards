# K8s Deployment

Kubernetes deployment configurations for Script-to-Storyboards.

## Quick Start

See [Quick Start Guide](../docs/QUICKSTART.md) for deployment instructions.

## Documentation

All documentation has been moved to the `docs/` directory:

- **[Quick Start Guide](../docs/QUICKSTART.md)** - Fast deployment for Mac (k3d) and Linux (k3s)
- **[Remote Deployment Guide](../docs/REMOTE-DEPLOY.md)** - One-click deployment from Mac to remote K3s server ⭐
- **[Full Deployment Guide](../docs/README.md)** - Detailed setup instructions
- **[API Routing Guide](../docs/API-ROUTING.md)** - How API routing works through Ingress
- **[Ingress Guide](../docs/INGRESS-GUIDE.md)** - Port 80 Ingress configuration

## Deployment Scripts

### For Remote K3s Server (Recommended)

- **`deploy-to-remote.sh`** - 🚀 One-click: build, package, upload, and deploy to remote K3s server
- **`package.sh`** - Build and package Docker images for manual deployment

### For Local/Direct Deployment

- **`deploy.sh`** - Automated deployment (supports both k3d and k3s)
- **`undeploy.sh`** - Clean up all resources

## Configuration Files

- `api-deployment.yaml` - API service deployment
- `frontend-deployment.yaml` - Frontend service deployment
- `ingress.yaml` - Ingress routing configuration
- `nginx-configmap.yaml` - Nginx configuration
- `k3d-config.yaml` - k3d cluster configuration (Mac only)
