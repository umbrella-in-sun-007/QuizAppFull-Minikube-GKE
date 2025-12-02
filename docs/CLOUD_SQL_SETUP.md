# Quick Start Guide - Shared Cloud SQL Setup

## 📑 Navigation
- [← Back to Main README](../README.md)
- [Cloud SQL Quick Reference](CLOUD_SQL_QUICK_REFERENCE.md)
- [GCP Infrastructure Guide](gcp.md)
- [GKE Deployment Guide](GKE_DEPLOYMENT_README.md)
- [Backup & Download Guide](CLOUD_SQL_BACKUP_DOWNLOAD.md)

## Table of Contents
1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Create Cloud SQL Instance](#step-1-create-cloud-sql-instance-10-minutes)
4. [Create Databases & Users](#step-2-create-databases--users)
5. [Local Development Setup](#step-3-set-up-local-development)
6. [GKE Deployment](#step-4-deploy-to-gke-optional)
7. [Common Commands](#common-commands)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

This guide shows you how to quickly set up your Wagtail QuizApp with a shared GCP Cloud SQL database for both local development and production.

## Architecture

**Single Cloud SQL Instance with Two Databases:**
- `dev` - Used by your local Docker Compose environment
- `prod` - Used by your GKE production deployment

**Benefits:** Data stays in sync, no need for separate database management, test with production-like setup locally.

---

## Prerequisites

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

---

## Step 1: Create Cloud SQL Instance (10 minutes)

```bash
# Set variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export INSTANCE_NAME="quizapp-postgres-prod"

# Enable APIs
gcloud services enable sqladmin.googleapis.com compute.googleapis.com

# Create instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-g1-small \
    --region=$REGION \
    --storage-size=20GB

# Get connection name
export CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME \
    --format='get(connectionName)')
echo $CONNECTION_NAME
```

---

## Step 2: Create Databases & Users

```bash
# Generate passwords
export DEV_PASSWORD=$(openssl rand -base64 32)
export PROD_PASSWORD=$(openssl rand -base64 32)

# Create databases
gcloud sql databases create dev --instance=$INSTANCE_NAME
gcloud sql databases create prod --instance=$INSTANCE_NAME

# Create users
gcloud sql users create dev_user \
    --instance=$INSTANCE_NAME \
    --password=$DEV_PASSWORD

gcloud sql users create prod_user \
    --instance=$INSTANCE_NAME \
    --password=$PROD_PASSWORD

# Save passwords (you'll need these)
echo "Dev Password: $DEV_PASSWORD"
echo "Prod Password: $PROD_PASSWORD"
```

---

## Step 3: Set Up Local Development

### Install Cloud SQL Proxy

```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create quizapp-local-dev

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Download key
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com
```

### Create .env File

```bash
cat > .env << EOF
CONNECTION_NAME=$CONNECTION_NAME
GCP_KEY_PATH=$(pwd)/gcp-key.json
DEV_DB_PASSWORD=$DEV_PASSWORD
DJANGO_SECRET_KEY=$(openssl rand -base64 32)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

### Use New Docker Compose

```bash
# Use the Cloud SQL version
docker-compose -f docker-compose.cloud-sql.yml up -d

# Run migrations
docker-compose -f docker-compose.cloud-sql.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.cloud-sql.yml exec web python manage.py createsuperuser

# Access at http://localhost:8000
```

---

## Step 4: Deploy to GKE (Optional)

### Create GKE Cluster

```bash
gcloud container clusters create quizapp-cluster \
    --region=$REGION \
    --num-nodes=2 \
    --workload-pool=${PROJECT_ID}.svc.id.goog

gcloud container clusters get-credentials quizapp-cluster --region=$REGION
```

### Set Up Workload Identity

```bash
# Create Kubernetes service account
kubectl create serviceaccount quizapp-ksa

# Create GCP service account
gcloud iam service-accounts create quizapp-gke-prod

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:quizapp-gke-prod@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Bind accounts
gcloud iam service-accounts add-iam-policy-binding \
    quizapp-gke-prod@${PROJECT_ID}.iam.gserviceaccount.com \
    --role=roles/iam.workloadIdentityUser \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[default/quizapp-ksa]"

kubectl annotate serviceaccount quizapp-ksa \
    iam.gke.io/gcp-service-account=quizapp-gke-prod@${PROJECT_ID}.iam.gserviceaccount.com
```

### Create Secrets

```bash
kubectl create secret generic quizapp-prod-db \
    --from-literal=password=$PROD_PASSWORD \
    --from-literal=username=prod_user \
    --from-literal=database=prod \
    --from-literal=connection-name=$CONNECTION_NAME

kubectl create secret generic quizapp-django \
    --from-literal=secret-key="$(openssl rand -base64 32)"
```

### Build & Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/$PROJECT_ID/quizapp:latest .

# Update deployment file
sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" k8s/deployment-cloud-sql.yaml

# Deploy
kubectl apply -f k8s/deployment-cloud-sql.yaml

# Get external IP
kubectl get svc quizapp-service -w

# Run migrations
kubectl exec -it $(kubectl get pod -l app=quizapp -o jsonpath='{.items[0].metadata.name}') \
    -- python manage.py migrate
```

---

## Common Commands

```bash
# Local Development
docker-compose -f docker-compose.cloud-sql.yml up -d      # Start
docker-compose -f docker-compose.cloud-sql.yml logs -f    # View logs
docker-compose -f docker-compose.cloud-sql.yml down       # Stop

# Connect to Cloud SQL directly
gcloud sql connect $INSTANCE_NAME --user=dev_user --database=dev

# GKE
kubectl get pods                                          # List pods
kubectl logs -l app=quizapp -c web -f                     # View logs
kubectl exec -it POD_NAME -- python manage.py shell      # Django shell
```

---

## Troubleshooting

### Cloud SQL Proxy Connection Failed
```bash
# Check proxy logs
docker-compose -f docker-compose.cloud-sql.yml logs cloud-sql-proxy

# Verify service account has permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:quizapp-local-dev*"
```

### Cannot Connect from Web Container
```bash
# Test network connectivity
docker-compose -f docker-compose.cloud-sql.yml exec web \
    nc -zv cloud-sql-proxy 5432
```

---

## Next Steps

1. ✅ Cloud SQL instance running with dev & prod databases
2. ✅ Local development using Cloud SQL
3. 🔲 Set up CI/CD pipeline
4. 🔲 Configure production domain and SSL
5. 🔲 Set up monitoring and alerts

For detailed documentation, see: `gcp-database-migration-guide.md`
