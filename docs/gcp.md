# GCP Infrastructure Provisioning Guide

This guide outlines the `gcloud` commands required to set up the infrastructure for the QuizApp on Google Cloud Platform.

## Prerequisites
Ensure you have the Google Cloud SDK installed and initialized.

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Set your preferred region and zone
export REGION="us-central1"
export ZONE="us-central1-a"
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

## 1. Enable Required APIs
Enable the necessary services for GKE, Cloud SQL, Artifact Registry, and Storage.

```bash
gcloud services enable \
    artifactregistry.googleapis.com \
    container.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com
```

## 2. Artifact Registry (Docker Repository)
Create a repository to store your Docker images.

```bash
export REPO_NAME="quizapp-repo"

gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for QuizApp"

# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

## 3. Cloud SQL (PostgreSQL)
Provision a managed PostgreSQL instance.

```bash
export INSTANCE_NAME="quizapp-db-instance"
export DB_NAME="quizapp"
export DB_USER="quizapp-user"
export DB_PASSWORD="secure-password-here" # Change this!

# Create the instance (this may take a few minutes)
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=$DB_PASSWORD

# Create the database
gcloud sql databases create $DB_NAME \
    --instance=$INSTANCE_NAME

# Create a user
gcloud sql users create $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=$DB_PASSWORD
```

## 4. Google Kubernetes Engine (GKE)
Create a standard GKE cluster.

```bash
export CLUSTER_NAME="quizapp-cluster"

gcloud container clusters create $CLUSTER_NAME \
    --region=$ZONE \
    --num-nodes=1 \
    --machine-type=e2-medium \
    --scopes=https://www.googleapis.com/auth/cloud-platform

# Get credentials to use kubectl
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE
```

## 5. Google Cloud Storage (Media Files)
Create a bucket for storing user-uploaded media files.

```bash
export BUCKET_NAME="${PROJECT_ID}-media"

# Create the bucket
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION

# Make the bucket public (Optional: Only if you want direct public access to media)
# Note: For production, consider using signed URLs or specific IAM permissions.
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member=allUsers \
    --role=roles/storage.objectViewer
```

## 6. Service Account (IAM)
Create a service account for the application to access Cloud SQL and Storage.

```bash
export SA_NAME="quizapp-sa"

# Create Service Account
gcloud iam service-accounts create $SA_NAME \
    --display-name="QuizApp Service Account"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Grant Storage Object Admin role (for media upload)
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create a key file (for use in Kubernetes Secrets)
gcloud iam service-accounts keys create key.json \
    --iam-account=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

## 7. Build and Push Image
Build your Docker image and push it to the registry.

```bash
export IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/quizapp:v1"

# Build the image
docker build -t $IMAGE_TAG .

# Push the image
docker push $IMAGE_TAG
```
