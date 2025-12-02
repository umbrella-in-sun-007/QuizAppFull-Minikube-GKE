#!/bin/bash
# Cloud SQL Setup Script
# This script sets up a Cloud SQL instance with dev and prod databases

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cloud SQL Setup for QuizApp ===${NC}\n"

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: openssl not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"

# Get user input
read -p "Enter your GCP Project ID: " PROJECT_ID
read -p "Enter region (default: us-central1): " REGION
REGION=${REGION:-us-central1}

read -p "Enter instance name (default: quizapp-postgres-prod): " INSTANCE_NAME
INSTANCE_NAME=${INSTANCE_NAME:-quizapp-postgres-prod}

read -p "Enter instance tier (default: db-g1-small): " DB_TIER
DB_TIER=${DB_TIER:-db-g1-small}

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Instance: $INSTANCE_NAME"
echo "  Tier: $DB_TIER"
echo ""

read -p "Proceed with setup? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Set project
echo -e "\n${GREEN}[1/10] Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable APIs
echo -e "\n${GREEN}[2/10] Enabling required APIs...${NC}"
gcloud services enable sqladmin.googleapis.com compute.googleapis.com secretmanager.googleapis.com

# Generate passwords
echo -e "\n${GREEN}[3/10] Generating secure passwords...${NC}"
DEV_PASSWORD=$(openssl rand -base64 32)
PROD_PASSWORD=$(openssl rand -base64 32)

# Store in Secret Manager
echo -e "\n${GREEN}[4/10] Storing passwords in Secret Manager...${NC}"
echo -n "$DEV_PASSWORD" | gcloud secrets create quizapp-dev-db-password \
    --data-file=- --replication-policy="automatic" 2>/dev/null || \
    echo -n "$DEV_PASSWORD" | gcloud secrets versions add quizapp-dev-db-password --data-file=-

echo -n "$PROD_PASSWORD" | gcloud secrets create quizapp-prod-db-password \
    --data-file=- --replication-policy="automatic" 2>/dev/null || \
    echo -n "$PROD_PASSWORD" | gcloud secrets versions add quizapp-prod-db-password --data-file=-

# Create Cloud SQL instance
echo -e "\n${GREEN}[5/10] Creating Cloud SQL instance (this takes 5-10 minutes)...${NC}"
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=$DB_TIER \
    --region=$REGION \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --database-flags=max_connections=500 \
    --availability-type=zonal \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --quiet || echo "Instance already exists, continuing..."

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format='get(connectionName)')
echo -e "${GREEN}✓ Connection name: $CONNECTION_NAME${NC}"

# Create databases
echo -e "\n${GREEN}[6/10] Creating databases...${NC}"
gcloud sql databases create dev --instance=$INSTANCE_NAME 2>/dev/null || echo "Database 'dev' already exists"
gcloud sql databases create prod --instance=$INSTANCE_NAME 2>/dev/null || echo "Database 'prod' already exists"

# Create users
echo -e "\n${GREEN}[7/10] Creating database users...${NC}"
gcloud sql users create dev_user \
    --instance=$INSTANCE_NAME \
    --password=$DEV_PASSWORD 2>/dev/null || \
    gcloud sql users set-password dev_user \
    --instance=$INSTANCE_NAME \
    --password=$DEV_PASSWORD

gcloud sql users create prod_user \
    --instance=$INSTANCE_NAME \
    --password=$PROD_PASSWORD 2>/dev/null || \
    gcloud sql users set-password prod_user \
    --instance=$INSTANCE_NAME \
    --password=$PROD_PASSWORD

# Create service account for local development
echo -e "\n${GREEN}[8/10] Creating service account for local access...${NC}"
gcloud iam service-accounts create quizapp-local-dev \
    --display-name="QuizApp Local Development" 2>/dev/null || \
    echo "Service account already exists"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" \
    --quiet

# Download key
echo -e "\n${GREEN}[9/10] Downloading service account key...${NC}"
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com \
    --quiet || echo "Key file already exists"

# Create .env file
echo -e "\n${GREEN}[10/10] Creating .env file...${NC}"
cat > .env << EOF
# GCP Configuration
CONNECTION_NAME=$CONNECTION_NAME
GCP_KEY_PATH=$(pwd)/gcp-key.json

# Database Credentials
DEV_DB_PASSWORD=$DEV_PASSWORD

# Django Settings
DJANGO_SECRET_KEY=$(openssl rand -base64 32)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# Add to .gitignore
grep -qxF '.env' .gitignore 2>/dev/null || echo '.env' >> .gitignore
grep -qxF 'gcp-key.json' .gitignore 2>/dev/null || echo 'gcp-key.json' >> .gitignore

# Create credentials file for reference (without sensitive data)
cat > .env.credentials << EOF
# Cloud SQL Setup - Credentials Reference
# Created: $(date)

Project ID: $PROJECT_ID
Region: $REGION
Instance Name: $INSTANCE_NAME
Connection Name: $CONNECTION_NAME

Dev Database: dev
Dev User: dev_user
Dev Password: (stored in Secret Manager: quizapp-dev-db-password)

Prod Database: prod
Prod User: prod_user
Prod Password: (stored in Secret Manager: quizapp-prod-db-password)

Service Account: quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com
Key File: ./gcp-key.json

To retrieve passwords:
gcloud secrets versions access latest --secret=quizapp-dev-db-password
gcloud secrets versions access latest --secret=quizapp-prod-db-password
EOF

echo -e "\n${GREEN}=== Setup Complete! ===${NC}\n"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Install Cloud SQL Proxy:"
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
echo -e "${GREEN}Configuration saved to:${NC}"
echo "  - .env (environment variables)"
echo "  - .env.credentials (credentials reference)"
echo "  - gcp-key.json (service account key)"
echo ""
echo -e "${YELLOW}IMPORTANT: Keep gcp-key.json and .env secure and never commit to git!${NC}"
