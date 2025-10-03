#!/bin/bash
set -e

echo "🔄 Updating Frontend in K8s..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Rebuild Docker image (includes docs rebuild)
echo -e "${YELLOW}📦 Step 1/3: Rebuilding Docker image (including MkDocs docs)...${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Load K8s-specific env variables
if [ -f "frontend/.env.k8s.local" ]; then
    echo "Using .env.k8s.local for local K8s deployment..."
    set -a
    source frontend/.env.k8s.local
    set +a
fi

echo "Building with VITE_API_BASE_URL=${VITE_API_BASE_URL}..."
docker-compose -f docker/compose/docker-compose.yml build frontend

# 2. Import to k3d/k3s
echo -e "${YELLOW}📥 Step 2/3: Importing to cluster...${NC}"

# Detect cluster type
if command -v k3d &> /dev/null && kubectl config current-context | grep -q "k3d"; then
    # k3d cluster
    CLUSTER_NAME=$(kubectl config current-context | sed 's/k3d-//')
    if [ -z "$CLUSTER_NAME" ]; then
        CLUSTER_NAME="calvin"
    fi
    echo "Detected k3d cluster: $CLUSTER_NAME"
    k3d image import script-to-storyboards-frontend:latest -c "$CLUSTER_NAME"
elif command -v k3s &> /dev/null; then
    # k3s cluster
    echo "Detected k3s cluster"
    docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -
else
    # Generic kubernetes - try docker save/load
    echo "Using generic import method..."
    docker save script-to-storyboards-frontend:latest | kubectl apply -f -
fi

# 3. Restart deployment
echo -e "${YELLOW}🔄 Step 3/3: Restarting deployment...${NC}"
kubectl rollout restart deployment/storyboard-frontend
kubectl rollout status deployment/storyboard-frontend --timeout=60s

echo ""
echo -e "${GREEN}✅ Frontend updated successfully!${NC}"
echo ""
echo "📋 What was updated:"
echo "   - React frontend application"
echo "   - MkDocs project documentation"
echo "   - Nginx configuration"
echo ""
echo "🌐 Access the application:"
if kubectl get ingress storyboard-ingress &> /dev/null; then
    echo "   - Frontend: http://localhost:8080/ (if port-forwarded)"
    echo "   - Docs: http://localhost:8080/docs/"
else
    echo "   - Run: kubectl port-forward -n kube-system service/traefik 8080:80"
    echo "   - Then visit: http://localhost:8080"
fi
