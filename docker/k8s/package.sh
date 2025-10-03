#!/bin/bash

# Package Script - Build and export Docker images for remote deployment

set -e

echo "📦 Packaging for remote K3s deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Navigate to project root
cd "$(dirname "$0")/../.."

# Create package directory
PACKAGE_DIR="k8s-package"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

echo -e "${YELLOW}🔨 Building frontend...${NC}"

# Load K8s remote-specific env variables
if [ -f "frontend/.env.k8s.remote" ]; then
    echo "Using .env.k8s.remote for remote K8s deployment..."
    set -a
    source frontend/.env.k8s.remote
    set +a
else
    echo "Warning: frontend/.env.k8s.remote not found, using default API URL"
fi

echo -e "${YELLOW}🐳 Building Docker images for linux/amd64...${NC}"
# Build for AMD64 platform (Ubuntu server) with K8s remote env
echo "Building with VITE_API_BASE_URL=${VITE_API_BASE_URL}..."
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose -f docker/compose/docker-compose.yml build
# Build for ARM64 platform (Apple M1/M2)
# DOCKER_DEFAULT_PLATFORM=linux/arm64 docker-compose build

echo -e "${YELLOW}💾 Exporting Docker images...${NC}"
docker save script-to-storyboards-api:latest -o "$PACKAGE_DIR/api-image.tar"
docker save script-to-storyboards-frontend:latest -o "$PACKAGE_DIR/frontend-image.tar"

echo -e "${YELLOW}📋 Copying K8s manifests...${NC}"
# 使用生产环境配置
cp docker/k8s/api-deployment.prod.yaml "$PACKAGE_DIR/api-deployment.yaml"
cp docker/k8s/redis-deployment.yaml "$PACKAGE_DIR/"
cp docker/k8s/frontend-deployment.yaml "$PACKAGE_DIR/"
cp docker/k8s/ingress.yaml "$PACKAGE_DIR/"
cp docker/k8s/nginx-configmap.yaml "$PACKAGE_DIR/"
cp docker/k8s/undeploy.sh "$PACKAGE_DIR/"

echo -e "${YELLOW}📝 Creating deployment script...${NC}"
cat > "$PACKAGE_DIR/deploy.sh" << 'EOF'
#!/bin/bash

# Remote Deployment Script for K3s

set -e

echo "🚀 Deploying to K3s..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if k3s is available
if ! command -v k3s &> /dev/null; then
    echo -e "${RED}❌ k3s not found. Please install k3s first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found k3s${NC}"

# Import Docker images
echo -e "${YELLOW}📥 Importing Docker images to k3s...${NC}"
if [ -f "api-image.tar" ]; then
    echo "Importing API image..."
    sudo k3s ctr images import api-image.tar
else
    echo -e "${RED}❌ api-image.tar not found${NC}"
    exit 1
fi

if [ -f "frontend-image.tar" ]; then
    echo "Importing frontend image..."
    sudo k3s ctr images import frontend-image.tar
else
    echo -e "${RED}❌ frontend-image.tar not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Images imported${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}⚠️  kubectl not found, using k3s kubectl${NC}"
    KUBECTL="sudo k3s kubectl"
else
    KUBECTL="kubectl"
fi

# Apply Kubernetes manifests
echo -e "${YELLOW}📋 Applying Kubernetes manifests...${NC}"

$KUBECTL apply -f nginx-configmap.yaml
$KUBECTL apply -f redis-deployment.yaml
$KUBECTL apply -f api-deployment.yaml
$KUBECTL apply -f frontend-deployment.yaml

# Ask about Ingress
read -p "Deploy Ingress on port 80? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    $KUBECTL apply -f ingress.yaml
    echo -e "${GREEN}✅ Ingress deployed on port 80${NC}"
fi

# Force restart to pick up new images (since we use :latest tag)
echo -e "${YELLOW}🔄 Restarting deployments to use new images...${NC}"
$KUBECTL rollout restart deployment/storyboard-api
$KUBECTL rollout restart deployment/storyboard-frontend

# Wait for deployments
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
$KUBECTL wait --for=condition=available --timeout=120s deployment/storyboard-api
$KUBECTL wait --for=condition=available --timeout=120s deployment/storyboard-frontend

echo -e "${GREEN}✅ Deployments are ready!${NC}"

# Show status
echo ""
echo -e "${GREEN}📊 Deployment Status:${NC}"
$KUBECTL get deployments
echo ""
$KUBECTL get services
echo ""
$KUBECTL get pods

# Get server IP
echo ""
echo -e "${GREEN}📍 Access Information:${NC}"
if $KUBECTL get ingress storyboard-ingress &> /dev/null; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "✅ Application deployed with Ingress on port 80:"
    echo "   - Frontend: http://$SERVER_IP/"
    echo "   - API: http://$SERVER_IP/api/"
    echo "   - API Docs: http://$SERVER_IP/api/docs"
else
    echo "⚠️  Ingress not deployed. Services are only accessible within cluster."
fi

echo ""
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo "📋 Useful commands:"
echo "  View logs: kubectl logs -f deployment/storyboard-api"
echo "  Restart: kubectl rollout restart deployment/storyboard-api"
echo "  Delete: ./undeploy.sh"
EOF

chmod +x "$PACKAGE_DIR/deploy.sh"

# Show package info
PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" | cut -f1)
echo ""
echo -e "${GREEN}✅ Package created: $PACKAGE_DIR ($PACKAGE_SIZE)${NC}"
echo ""
echo "📋 Package contents:"
echo "  - api-image.tar (Docker image)"
echo "  - frontend-image.tar (Docker image)"
echo "  - K8s manifests (yaml files)"
echo "  - deploy.sh (deployment script)"
echo "  - undeploy.sh (cleanup script)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  Automated: ./k8s/deploy-to-remote.sh"
echo ""
echo "  Or manual:"
echo "  1. rsync -avzP k8s-package/ <remote>:~/k8s-deploy/k8s-package/"
echo "  2. ssh <remote>"
echo "  3. cd ~/k8s-deploy/k8s-package"
echo "  4. ./deploy.sh"
