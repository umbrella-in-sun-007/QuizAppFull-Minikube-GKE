#!/bin/bash

# Configuration
PROJECT_ID="data-rainfall-476920-v0"
REGION="us-central1"

echo "WARNING: This script will delete ALL resources for project $PROJECT_ID"
echo "Resources to be deleted:"
echo "- GKE Cluster: quizapp-cluster (Regional: $REGION)"
echo "- Cloud SQL Instance: quizapp-postgres-prod"
echo "- Storage Buckets: data-rainfall-476920-v0-sql-backups, quizapp-media-476920"
echo "- Artifact Registry: quizapp-repo, gcr.io"
echo "- Secrets: quizapp-dev-db-password, quizapp-prod-db-password"
echo "- Service Account: quizapp-sa"
echo ""
echo "Starting cleanup in 5 seconds..."
sleep 5

# 1. Delete GKE Cluster
echo "Deleting GKE Cluster..."
gcloud container clusters delete quizapp-cluster --region=$REGION --quiet --async
echo "Cluster deletion triggered asynchronously."

# 2. Delete Cloud SQL Instance
echo "Deleting Cloud SQL Instance..."
gcloud sql instances delete quizapp-postgres-prod --quiet
echo "Cloud SQL instance deleted."

# 3. Delete Storage Buckets
echo "Deleting Storage Buckets..."
gcloud storage rm -r gs://data-rainfall-476920-v0-sql-backups --quiet || echo "Bucket not found or already deleted"
gcloud storage rm -r gs://quizapp-media-476920 --quiet || echo "Bucket not found or already deleted"

# 4. Delete Artifact Registry
echo "Deleting Artifact Registry..."
gcloud artifacts repositories delete quizapp-repo --location=$REGION --quiet || echo "quizapp-repo not found"
gcloud artifacts repositories delete gcr.io --location=us --quiet || echo "gcr.io not found or cannot be deleted"

# 5. Delete Secrets
echo "Deleting Secrets..."
gcloud secrets delete quizapp-dev-db-password --quiet || echo "Secret not found"
gcloud secrets delete quizapp-prod-db-password --quiet || echo "Secret not found"

# 6. Delete Service Account
echo "Deleting Service Account..."
gcloud iam service-accounts delete quizapp-sa@${PROJECT_ID}.iam.gserviceaccount.com --quiet || echo "SA not found"

echo "Cleanup commands issued. GKE cluster deletion may take a few more minutes to complete in the background."
