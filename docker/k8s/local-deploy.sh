#!/bin/bash

# K3s Deployment Script for Script-to-Storyboards

set -e

echo "🚀 Deploying to K3s..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check if we can connect to k3s
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to k3s cluster. Please check your kubeconfig.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Connected to k3s cluster${NC}"

# Build Docker images locally first
echo -e "${YELLOW}📦 Building Docker images...${NC}"
cd "$(dirname "$0")/../.."

# Load K8s-specific env variables
if [ -f "frontend/.env.k8s.local" ]; then
    echo "Using .env.k8s.local for local K8s deployment..."
    # Source the .env.k8s.local file to load environment variables
    set -a
    source frontend/.env.k8s.local
    set +a
else
    echo "Warning: frontend/.env.k8s.local not found, using default API URL"
fi

# Build Docker images
echo "Building Docker images with VITE_API_BASE_URL=${VITE_API_BASE_URL}..."
docker-compose -f docker/docker-compose.yml build

# Import images to k3s/k3d
echo -e "${YELLOW}📥 Importing images to cluster...${NC}"

# Detect if using k3d or k3s
if command -v k3d &> /dev/null; then
    # Mac/k3d environment
    echo "Detected k3d, importing images..."

    # Get cluster name from kubeconfig or use default
    CLUSTER_NAME=$(kubectl config current-context | sed 's/k3d-//')
    if [ -z "$CLUSTER_NAME" ]; then
        CLUSTER_NAME="calvin"
    fi

    k3d image import script-to-storyboards-api:latest -c "$CLUSTER_NAME"
    k3d image import script-to-storyboards-frontend:latest -c "$CLUSTER_NAME"
elif command -v k3s &> /dev/null; then
    # Linux/k3s environment
    echo "Detected k3s, importing images..."
    docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
    docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -
else
    # Generic kubernetes - images should already be available
    echo "⚠️  Neither k3d nor k3s detected."
    echo "Assuming images are already available in the cluster."
    echo "If pods fail to start, you may need to push images to a registry."
fi

echo -e "${GREEN}✅ Images imported${NC}"

# Apply Kubernetes manifests
echo -e "${YELLOW}📋 Applying Kubernetes manifests...${NC}"

# Delete old deployments first (to avoid selector immutable error)
# kubectl delete deployment storyboard-api storyboard-frontend --ignore-not-found=true

# Apply ConfigMap first
kubectl apply -f docker/k8s/nginx-configmap.yaml

# Apply Redis deployment
kubectl apply -f docker/k8s/redis-deployment.yaml

# Apply deployments
kubectl apply -f docker/k8s/api-deployment.yaml
kubectl apply -f docker/k8s/frontend-deployment.yaml

# Apply Ingress (default to yes for port 80 access)
read -p "Do you want to deploy Ingress on port 80? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    kubectl apply -f docker/k8s/ingress.yaml
    echo -e "${GREEN}✅ Ingress deployed on port 80${NC}"
fi

# Restart deployments to ensure new images are used
echo -e "${YELLOW}🔄 Restarting deployments to use new images...${NC}"
kubectl rollout restart deployment/storyboard-api
kubectl rollout restart deployment/storyboard-frontend

# Wait for deployments to be ready
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"

kubectl wait --for=condition=available --timeout=120s deployment/storyboard-api
kubectl wait --for=condition=available --timeout=120s deployment/storyboard-frontend

echo -e "${GREEN}✅ Deployments are ready!${NC}"

# Show status
echo ""
echo -e "${GREEN}📊 Deployment Status:${NC}"
kubectl get deployments
echo ""
kubectl get services
echo ""
kubectl get pods

# Get access information
echo ""
echo -e "${GREEN}📍 Access Information:${NC}"

# If using Ingress
if kubectl get ingress storyboard-ingress &> /dev/null; then
    echo "✅ Ingress on port 80:"
    echo "   - Frontend: http://<server-ip>/"
    echo "   - API: http://<server-ip>/api/"
    echo ""
    echo "   Replace <server-ip> with your server's IP address"
else
    # Get ClusterIP for services
    FRONTEND_IP=$(kubectl get service storyboard-frontend -o jsonpath='{.spec.clusterIP}')
    API_IP=$(kubectl get service storyboard-api -o jsonpath='{.spec.clusterIP}')
    echo "Services (internal only):"
    echo "   - Frontend: http://$FRONTEND_IP"
    echo "   - API: http://$API_IP:8000"
    echo ""
    echo "⚠️  Without Ingress, services are only accessible within the cluster."
    echo "   Run the deploy script again and choose 'Y' for Ingress."
fi

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📋 Useful commands:"
echo "  View logs: kubectl logs -f deployment/storyboard-api"
echo "  Delete: kubectl delete -f docker/k8s/"
echo "  Restart: kubectl rollout restart deployment/storyboard-api"
