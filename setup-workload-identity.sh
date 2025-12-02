#!/bin/bash
# Setup Workload Identity for GKE
set -e

PROJECT_ID="data-rainfall-476920-v0"
CLUSTER_NAME="quizapp-cluster"
CLUSTER_REGION="us-central1"
NAMESPACE="production"
KSA_NAME="quizapp-ksa"
GSA_NAME="quizapp-gke-sa"
GSA_EMAIL="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Setting up Workload Identity for QuizApp ==="
echo ""

# Create Google Service Account
echo "[1/6] Creating Google Service Account..."
gcloud iam service-accounts create $GSA_NAME \
    --display-name="QuizApp GKE Service Account" \
    --project=$PROJECT_ID 2>/dev/null || echo "  Service account already exists"

# Grant Cloud SQL Client role
echo "[2/6] Granting Cloud SQL Client permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${GSA_EMAIL}" \
    --role="roles/cloudsql.client" \
    --quiet

# Create namespace
echo "[3/6] Creating Kubernetes namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create Kubernetes Service Account
echo "[4/6] Creating Kubernetes Service Account..."
kubectl create serviceaccount $KSA_NAME \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Bind KSA to GSA (Workload Identity)
echo "[5/6] Binding Kubernetes SA to Google SA..."
gcloud iam service-accounts add-iam-policy-binding $GSA_EMAIL \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${KSA_NAME}]" \
    --project=$PROJECT_ID

# Annotate Kubernetes Service Account
echo "[6/6] Annotating Kubernetes Service Account..."
kubectl annotate serviceaccount $KSA_NAME \
    --namespace=$NAMESPACE \
    iam.gke.io/gcp-service-account=$GSA_EMAIL \
    --overwrite

echo ""
echo "✓ Workload Identity setup complete!"
echo ""
echo "Details:"
echo "  Google Service Account: $GSA_EMAIL"
echo "  Kubernetes Service Account: $KSA_NAME"
echo "  Namespace: $NAMESPACE"
echo ""
echo "Verify with:"
echo "  kubectl describe sa $KSA_NAME -n $NAMESPACE"
