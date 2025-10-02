# K3s Deployment Guide

This directory contains Kubernetes manifests for deploying Script-to-Storyboards to K3s.

## Prerequisites

### For Mac (Development)

1. **k3d** installed (`brew install k3d`)
2. **kubectl** installed
3. **Docker Desktop** running

### For Linux Server (Production)

1. **K3s** installed on your server
2. **kubectl** configured to connect to your K3s cluster
3. **Docker** installed

## Quick Start

### 1. Setup kubectl to connect to remote K3s

**Option A: SSH Tunnel (Recommended)**

```bash
# Create SSH tunnel
ssh -L 6443:localhost:6443 calvin -N -f

# Your existing kubeconfig should work now
kubectl get nodes
```

**Option B: Copy kubeconfig from remote server**

```bash
# On remote server
ssh calvin "sudo cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/calvin-k3s.yaml

# Edit the file and change server address
# From: server: https://127.0.0.1:6443
# To:   server: https://YOUR_SERVER_IP:6443

# Use the config
export KUBECONFIG=~/.kube/calvin-k3s.yaml
kubectl get nodes
```

### 2. Deploy to K3s

```bash
# Make scripts executable
chmod +x k8s/deploy.sh k8s/undeploy.sh

# Run deployment
./k8s/deploy.sh
```

The script will:

1. ✅ Build Docker images locally
2. ✅ Import images to k3s
3. ✅ Deploy API and Frontend
4. ✅ Optionally deploy Ingress

### 3. Access the Application

**Frontend**:

- Via NodePort: `http://<node-ip>:30866`
- Via localhost (if using SSH tunnel): `http://localhost:30866`

**API**:

- Internal only: `http://storyboard-api:8000`

**With Ingress** (optional):

- Add to `/etc/hosts`: `<node-ip> storyboard.local`
- Access: `http://storyboard.local`

## Manual Deployment

If you prefer to deploy manually:

```bash
# 1. Build and import images
cd /path/to/script-to-storyboards
docker-compose build

# Import to k3s
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
docker save script-to-storyboards-frontend:latest | sudo k3s ctr images import -

# 2. Deploy to k3s
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Optional: Deploy Ingress
kubectl apply -f k8s/ingress.yaml
```

## Management Commands

```bash
# View pods
kubectl get pods

# View services
kubectl get services

# View logs
kubectl logs -f deployment/storyboard-api
kubectl logs -f deployment/storyboard-frontend

# Restart deployment
kubectl rollout restart deployment/storyboard-api
kubectl rollout restart deployment/storyboard-frontend

# Scale deployment
kubectl scale deployment/storyboard-api --replicas=2

# Delete all resources
./k8s/undeploy.sh
# Or manually:
kubectl delete -f k8s/
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>
```

### Image pull errors

Make sure images are imported to k3s:

```bash
# List images in k3s
sudo k3s ctr images list | grep storyboard

# Re-import if needed
docker save script-to-storyboards-api:latest | sudo k3s ctr images import -
```

### Cannot connect to cluster

```bash
# Test connection
kubectl cluster-info

# Check SSH tunnel (if using)
ps aux | grep "ssh.*6443"

# Recreate tunnel
ssh -L 6443:localhost:6443 calvin -N -f
```

### Service not accessible

```bash
# Check service
kubectl get svc

# Get NodePort
kubectl get svc storyboard-frontend -o jsonpath='{.spec.ports[0].nodePort}'

# Test from within cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Then: wget -O- http://storyboard-api:8000/health
```

## Configuration

### Change NodePort

Edit `k8s/frontend-deployment.yaml`:

```yaml
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30866 # Change this (30000-32767)
```

### Add Persistent Storage

If you need to persist data, add volumes to deployments:

```yaml
spec:
  template:
    spec:
      volumes:
        - name: data
          hostPath:
            path: /data/storyboard
      containers:
        - name: api
          volumeMounts:
            - name: data
              mountPath: /app/data
```

### Resource Limits

Adjust in deployment files:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Architecture

```
┌───────────────────┐
│  Ingress          │ (Optional)
│  storyboard.local │
└────────┬──────────┘
         │
    ┌────┴─────┬────────────┐
    │          │            │
┌───▼────┐  ┌──▼──────┐ ┌───▼──────┐
│Frontend│  │   API   │ │Database  │
│NodePort│  │ClusterIP│ │(External)│
│  :30866│  │  :8000  │ │          │
└────────┘  └─────────┘ └──────────┘
```

## Clean Up

```bash
# Remove all resources
./k8s/undeploy.sh

# Or manually
kubectl delete -f k8s/
```
