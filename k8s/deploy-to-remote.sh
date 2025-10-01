#!/bin/bash

# One-click deployment to remote K3s server

set -e

echo "🚀 Deploying to remote K3s server..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REMOTE_HOST="44.213.117.91"
REMOTE_DIR="~/k8s-deploy"

# Navigate to project root
cd "$(dirname "$0")/.."

# Step 1: Package
echo -e "${YELLOW}📦 Step 1/3: Building and packaging...${NC}"
./k8s/package.sh

if [ ! -d "k8s-package" ]; then
    echo -e "${RED}❌ Package directory not found${NC}"
    exit 1
fi

# Step 2: Upload
echo ""
echo -e "${YELLOW}📤 Step 2/3: Uploading to $REMOTE_HOST...${NC}"

# Test SSH connection
if ! ssh -o ConnectTimeout=5 "$REMOTE_HOST" "echo 'SSH connection OK'" &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to $REMOTE_HOST${NC}"
    echo "Please check:"
    echo "  1. SSH config (~/.ssh/config) has entry for '$REMOTE_HOST'"
    echo "  2. SSH key is set up correctly"
    echo "  3. Server is accessible"
    exit 1
fi

# Upload with rsync (only transfers changes)
echo "Using rsync for incremental transfer (only changed files)..."
rsync -avzP --partial k8s-package/ "$REMOTE_HOST:$REMOTE_DIR/k8s-package/"

echo -e "${GREEN}✅ Upload completed${NC}"

# Step 3: Deploy
echo ""
echo -e "${YELLOW}🚀 Step 3/3: Deploying on remote server...${NC}"
echo ""

ssh "$REMOTE_HOST" << 'ENDSSH'
set -e

cd ~/k8s-deploy/k8s-package

# Make scripts executable
chmod +x deploy.sh undeploy.sh

# Run deployment
echo ""
echo "🚀 Starting deployment..."
./deploy.sh
ENDSSH

echo ""
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   http://<server-ip>/"
echo ""
echo "📋 Remote management commands:"
echo "  ssh $REMOTE_HOST 'kubectl get pods'"
echo "  ssh $REMOTE_HOST 'kubectl logs -f deployment/storyboard-api'"
echo "  ssh $REMOTE_HOST 'kubectl get ingress'"
echo ""
echo "🗑️  To undeploy:"
echo "  ssh $REMOTE_HOST 'cd ~/k8s-deploy/k8s-package && ./undeploy.sh'"
