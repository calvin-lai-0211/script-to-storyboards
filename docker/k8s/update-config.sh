#!/bin/bash

# Quick update script for K8s configurations on remote server
# Usage: ./update-config.sh [ingress|api|frontend|all]

set -e

# Configuration
REMOTE_HOST="44.213.117.91"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Navigate to k8s directory
cd "$(dirname "$0")"

# Parse argument
COMPONENT="${1:-all}"

update_file() {
    local file=$1
    local name=$2

    echo -e "${YELLOW}📤 Uploading $name...${NC}"
    scp "$file" "$REMOTE_HOST:/tmp/"

    echo -e "${YELLOW}🔄 Applying $name...${NC}"
    ssh "$REMOTE_HOST" "kubectl apply -f /tmp/$(basename $file)"
}

case "$COMPONENT" in
    ingress)
        update_file "ingress.yaml" "Ingress"
        ;;
    api)
        update_file "api-deployment.yaml" "API Deployment"
        ssh "$REMOTE_HOST" "kubectl rollout restart deployment/storyboard-api"
        ;;
    frontend)
        update_file "frontend-deployment.yaml" "Frontend Deployment"
        update_file "nginx-configmap.yaml" "Nginx ConfigMap"
        ssh "$REMOTE_HOST" "kubectl rollout restart deployment/storyboard-frontend"
        ;;
    all)
        update_file "nginx-configmap.yaml" "Nginx ConfigMap"
        update_file "api-deployment.yaml" "API Deployment"
        update_file "frontend-deployment.yaml" "Frontend Deployment"
        update_file "ingress.yaml" "Ingress"
        echo -e "${YELLOW}🔄 Restarting deployments...${NC}"
        ssh "$REMOTE_HOST" "kubectl rollout restart deployment/storyboard-api"
        ssh "$REMOTE_HOST" "kubectl rollout restart deployment/storyboard-frontend"
        ;;
    *)
        echo "Usage: $0 [ingress|api|frontend|all]"
        echo ""
        echo "Examples:"
        echo "  $0 ingress    - Update only ingress configuration"
        echo "  $0 api        - Update API deployment"
        echo "  $0 frontend   - Update frontend deployment and nginx config"
        echo "  $0 all        - Update all configurations (default)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Update completed!${NC}"
echo ""
echo "📋 Check status:"
echo "  ssh $REMOTE_HOST 'kubectl get ingress'"
echo "  ssh $REMOTE_HOST 'kubectl get pods'"
