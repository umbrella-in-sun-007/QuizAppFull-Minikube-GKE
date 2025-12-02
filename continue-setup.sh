#!/bin/bash
# Cloud SQL Setup - Continue After Instance Creation
# Run this script after the Cloud SQL instance shows STATUS=RUNNABLE

set -e

PROJECT_ID="data-rainfall-476920-v0"
INSTANCE_NAME="quizapp-postgres-prod"

# Passwords (generated securely)
DEV_PASSWORD="SjeeTlHfhcxou1OBFYAf1y3xpicTT0C4Jrgp6qsStcM="
PROD_PASSWORD="tpv4xnA3/FAXR0m7vVFq0/F32joN6FpnE1QhlXDPGPk="
DJANGO_SECRET="GtOJ65BaVkyhRZTnmL03KM4KZdtKNyuPy9qYZPYRuEw="

echo "===  Continuing Cloud SQL Setup  ==="
echo ""

# Wait for instance to be ready
echo "[1/8] Checking instance status..."
STATUS=$(gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format="value(state)")
if [ "$STATUS" != "RUNNABLE" ]; then
    echo "ERROR: Instance is not ready yet. Current status: $STATUS"
    echo "Please wait a few more minutes and run this script again."
    exit 1
fi

echo "✓ Instance is RUNNABLE"

# Get connection name
echo "[2/8] Getting connection name..."
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format='get(connectionName)')
echo "✓ Connection name: $CONNECTION_NAME"

# Create databases
echo "[3/8] Creating databases..."
gcloud sql databases create dev --instance=$INSTANCE_NAME --project=$PROJECT_ID 2>/dev/null || echo "  Database 'dev' already exists"
gcloud sql databases create prod --instance=$INSTANCE_NAME --project=$PROJECT_ID 2>/dev/null || echo "  Database 'prod' already exists"
echo "✓ Databases created"

# Create users
echo "[4/8] Creating database users..."
gcloud sql users create dev_user \
    --instance=$INSTANCE_NAME \
    --password="$DEV_PASSWORD" \
    --project=$PROJECT_ID 2>/dev/null || echo "  User 'dev_user' already exists"

gcloud sql users create prod_user \
    --instance=$INSTANCE_NAME \
    --password="$PROD_PASSWORD" \
    --project=$PROJECT_ID 2>/dev/null || echo "  User 'prod_user' already exists"
echo "✓ Users created"

# Store passwords in Secret Manager
echo "[5/8] Storing passwords in Secret Manager..."
echo -n "$DEV_PASSWORD" | gcloud secrets create quizapp-dev-db-password \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$DEV_PASSWORD" | gcloud secrets versions add quizapp-dev-db-password --data-file=- --project=$PROJECT_ID

echo -n "$PROD_PASSWORD" | gcloud secrets create quizapp-prod-db-password \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$PROD_PASSWORD" | gcloud secrets versions add quizapp-prod-db-password --data-file=- --project=$PROJECT_ID

echo "✓ Passwords stored in Secret Manager"

# Create service account
echo "[6/8] Creating service account for local access..."
gcloud iam service-accounts create quizapp-local-dev \
    --display-name="QuizApp Local Development" \
    --project=$PROJECT_ID 2>/dev/null || echo "  Service account already exists"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" \
    --quiet

echo "✓ Service account created and granted permissions"

# Download key
echo "[7/8] Downloading service account key..."
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com \
    --project=$PROJECT_ID \
    --quiet 2>/dev/null || echo "  Key file may already exist"

chmod 600 gcp-key.json 2>/dev/null || true
echo "✓ Service account key downloaded"

# Create .env file
echo "[8/8] Creating .env file..."
cat > .env << EOF
# GCP Configuration
CONNECTION_NAME=$CONNECTION_NAME
GCP_KEY_PATH=$(pwd)/gcp-key.json

# Database Credentials (Dev Database)
DEV_DB_PASSWORD=$DEV_PASSWORD

# Django Settings
DJANGO_SECRET_KEY=$DJANGO_SECRET
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# Update .gitignore
grep -qxF '.env' .gitignore 2>/dev/null || echo '.env' >> .gitignore
grep -qxF 'gcp-key.json' .gitignore 2>/dev/null || echo 'gcp-key.json' >> .gitignore

echo "✓ .env file created"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Credentials saved:"
echo "  - .env (environment variables)"
echo "  - gcp-key.json (service account key)"
echo ""
echo "Next steps:"
echo "1. Install Cloud SQL Proxy (if not installed):"
echo "   curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64"
echo "   chmod +x cloud-sql-proxy"
echo "   sudo mv cloud-sql-proxy /usr/local/bin/"
echo ""
echo "2. Start your application:"
echo "   docker-compose -f docker-compose.cloud-sql.yml up -d"
echo ""
echo "3. Run migrations:"
echo "   docker-compose -f docker-compose.cloud-sql.yml exec web python manage.py migrate"
echo ""
echo "Instance details:"
echo "  Name: $INSTANCE_NAME"
echo "  Connection: $CONNECTION_NAME"
echo "  IP: $(gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format='value(ipAddresses[0].ipAddress)')"
echo ""
