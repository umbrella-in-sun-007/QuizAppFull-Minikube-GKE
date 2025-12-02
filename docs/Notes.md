# Hybrid Deployment Guide: Local Kubernetes + GCP Cloud SQL

This guide details how to deploy the Quiz App on a 3-node local cluster (College Infra) while offloading the database to Google Cloud SQL.

**Architecture:**
*   **Compute**: 3x Ubuntu Machines (1 Master, 2 Workers) in College Lab.
*   **Orchestration**: Kubernetes (v1.28+) managed by `kubeadm`.
*   **Database**: PostgreSQL 15 on Google Cloud SQL (Managed Service).
*   **Load Balancing**: MetalLB (Layer 2) to expose the app on the College LAN.

---

## Phase 1: Prepare the Machines (All Nodes)
*Run these commands on ALL 3 machines (Master & Workers).*

### 1. Prerequisites
*   **OS**: Ubuntu 22.04 LTS (Recommended).
*   **Network**: Static IPs for all nodes.
*   **Privileges**: Root or sudo access.

### 2. Disable Swap & Install Container Runtime
Kubernetes requires swap to be disabled.
```bash
# Disable swap immediately
sudo swapoff -a
# Disable swap permanently in /etc/fstab
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# Enable IPv4 forwarding
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Sysctl params required by setup
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# Install Containerd
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
# Set SystemdCgroup = true in config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
sudo systemctl restart containerd
```

### 3. Install Kubeadm, Kubelet, Kubectl
```bash
sudo apt-get update
# apt-transport-https may be a dummy package; if so, you can skip that package
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Download the public signing key for the Kubernetes package repositories
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add the Kubernetes apt repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

---

## Phase 2: Initialize the Cluster (Master Node Only)

### 1. Initialize Control Plane
Run this **ONLY** on the Master node.
```bash
# Replace <MASTER_IP> with the actual IP of this machine
sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=<MASTER_IP>
```

### 2. Configure Kubectl
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 3. Install Network Plugin (Calico)
```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml
```

### 4. Get Join Command
Copy the `kubeadm join ...` command outputted by the init step. If you lost it:
```bash
kubeadm token create --print-join-command
```

---

## Phase 3: Join Workers (Worker Nodes Only)
Run the join command you copied from the Master on **Worker 1** and **Worker 2**.
```bash
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> --discovery-token-ca-cert-hash sha256:<HASH>
```

*Verify on Master:*
```bash
kubectl get nodes
# Status should eventually become 'Ready' for all nodes.
```

---

## Phase 4: Configure Load Balancing (MetalLB)
Since you don't have a cloud LoadBalancer, use MetalLB to assign a LAN IP to your service.

### 1. Install MetalLB
```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
```

### 2. Configure IP Pool
Find a range of unused IPs in your college network (e.g., `10.0.0.240` to `10.0.0.250`).
Create `metallb-config.yaml`:
```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 10.0.0.240-10.0.0.250  # <--- CHANGE THIS TO YOUR NETWORK RANGE
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: example
  namespace: metallb-system
```
Apply it:
```bash
kubectl apply -f metallb-config.yaml
```

---

## Phase 5: Database Setup (GCP Cloud SQL)

1.  **Create Instance**: Go to GCP Console -> SQL -> Create Instance -> PostgreSQL 15.
2.  **Configure Connectivity**:
    *   **Public IP**: Enable Public IP.
    *   **Authorized Networks**: Add the **Public IP of your College Gateway/Router**. (Ask network admin "What is our egress IP?").
3.  **Create Database & User**:
    *   DB Name: `quizapp`
    *   User: `quizadmin`
    *   Password: `StrongPassword123`
4.  **Get Connection URL**:
    *   `postgres://quizadmin:StrongPassword123@<GCP_PUBLIC_IP>:5432/quizapp`

---

## Phase 6: Deploy Application

### 1. Create Secret for Database
```bash
kubectl create secret generic quiz-secrets \
  --from-literal=DATABASE_URL='postgres://quizadmin:StrongPassword123@<GCP_PUBLIC_IP>:5432/quizapp' \
  --from-literal=DJANGO_SECRET_KEY='your-production-secret-key' \
  --from-literal=DJANGO_ALLOWED_HOSTS='*'
```

### 2. Deployment Manifest (`deployment.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quizapp
spec:
  replicas: 3  # High availability
  selector:
    matchLabels:
      app: quizapp
  template:
    metadata:
      labels:
        app: quizapp
    spec:
      containers:
      - name: quizapp
        image: your-dockerhub-username/quizapp:latest # <--- PUSH YOUR IMAGE TO DOCKER HUB FIRST
        ports:
        - containerPort: 8000
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "quizapp.settings.production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: quiz-secrets
              key: DATABASE_URL
        - name: DJANGO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: quiz-secrets
              key: DJANGO_SECRET_KEY
        - name: DJANGO_ALLOWED_HOSTS
          valueFrom:
            secretKeyRef:
              name: quiz-secrets
              key: DJANGO_ALLOWED_HOSTS
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 3. Service Manifest (`service.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: quizapp-service
spec:
  selector:
    app: quizapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### 4. Deploy
```bash
# 1. Build and Push Image (Run on dev machine)
docker build -t your-dockerhub-username/quizapp:latest .
docker push your-dockerhub-username/quizapp:latest

# 2. Apply Manifests (Run on Master Node)
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 5. Access the App
Check the external IP assigned by MetalLB:
```bash
kubectl get svc quizapp-service
```
You should see an `EXTERNAL-IP` (e.g., `10.0.0.240`). Access `http://10.0.0.240` from any computer in the college labs.

---

## Phase 7: Maintenance & Scaling

*   **Scale Up**: `kubectl scale deployment quizapp --replicas=5`
*   **Update App**:
    1.  `docker build ...` & `docker push ...`
    2.  `kubectl rollout restart deployment quizapp`
*   **Logs**: `kubectl logs -l app=quizapp`
*   **Monitor**: Use `kubectl top nodes` and `kubectl top pods` (requires Metrics Server).
