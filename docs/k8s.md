# Kubernetes Deployment Guide

This guide covers the steps to deploy the QuizApp application on Kubernetes. It includes instructions for local testing using **Minikube** and production deployment on **Google Kubernetes Engine (GKE)**.

## Prerequisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed.
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed (for local testing).
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed (for GKE).
- Docker installed.

## 1. Prepare Kubernetes Manifests

Create a directory named `k8s` in your project root and create the following YAML files.

### `k8s/configmap.yaml`
Stores non-sensitive configuration.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: quizapp-config
data:
  DJANGO_SETTINGS_MODULE: "quizapp.settings.production"
  DJANGO_ALLOWED_HOSTS: "*"
  PORT: "8000"
```

### `k8s/secret.yaml`
Stores sensitive data. **Do not commit actual secrets to version control.**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: quizapp-secret
type: Opaque
stringData:
  DJANGO_SECRET_KEY: "your-super-secret-key"
  DATABASE_URL: "postgres://user:password@host:5432/dbname" # Update based on environment
```

### `k8s/deployment.yaml`
Defines the application pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quizapp
spec:
  replicas: 1
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
          image: quizapp:latest # Change for GKE
          imagePullPolicy: IfNotPresent # Important for Minikube local images
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: quizapp-config
            - secretRef:
                name: quizapp-secret
          livenessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
```

### `k8s/service.yaml`
Exposes the application within the cluster.

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
  type: LoadBalancer # Use LoadBalancer for simple Minikube/GKE access
```

---

## 2. Local Deployment on Minikube

### Step 1: Start Minikube
```bash
minikube start
```

### Step 2: Use Minikube's Docker Daemon
This allows Minikube to see images you build locally without pushing to a registry.
```bash
eval $(minikube docker-env)
```

### Step 3: Build the Image
```bash
docker build -t quizapp:latest .
```

### Step 4: Deploy a Local Postgres (Optional)
For local testing, you can deploy a simple Postgres pod or use SQLite (if configured). If using Postgres, deploy it inside the cluster:

```bash
# Simple Postgres Deployment for testing
kubectl create deployment postgres --image=postgres:15
kubectl set env deployment/postgres POSTGRES_PASSWORD=postgres
kubectl expose deployment postgres --port=5432
```
*Update `k8s/secret.yaml` `DATABASE_URL` to: `postgres://postgres:postgres@postgres:5432/postgres`*

### Step 5: Apply Manifests
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 6: Run Migrations
```bash
# Get the pod name
POD_NAME=$(kubectl get pods -l app=quizapp -o jsonpath="{.items[0].metadata.name}")

# Run migrate
kubectl exec -it $POD_NAME -- python manage.py migrate
kubectl exec -it $POD_NAME -- python manage.py createsuperuser
```

### Step 7: Access the App
```bash
minikube service quizapp-service
```

---

## 3. Deployment on GKE

### Step 1: Connect to Cluster
Ensure you have created the cluster (see `gcp.md`) and connected to it:
```bash
gcloud container clusters get-credentials quizapp-cluster --zone us-central1-a
```

### Step 2: Update Secrets for Cloud SQL
Update `k8s/secret.yaml` with your Cloud SQL credentials.
The `DATABASE_URL` format depends on how you connect (Private IP or Cloud SQL Auth Proxy).
For simplicity with Private IP (if enabled):
`postgres://<DB_USER>:<DB_PASS>@<PRIVATE_IP>:5432/<DB_NAME>`

### Step 3: Update Deployment Image
Update `k8s/deployment.yaml` to use the image from Artifact Registry:
```yaml
image: us-central1-docker.pkg.dev/YOUR_PROJECT_ID/quizapp-repo/quizapp:v1
imagePullPolicy: Always
```

### Step 4: Apply Manifests
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 5: Run Migrations
```bash
POD_NAME=$(kubectl get pods -l app=quizapp -o jsonpath="{.items[0].metadata.name}")
kubectl exec -it $POD_NAME -- python manage.py migrate
```

### Step 6: Access the App
Get the external IP of the LoadBalancer:
```bash
kubectl get service quizapp-service
```
It may take a minute for the `EXTERNAL-IP` to be assigned.
