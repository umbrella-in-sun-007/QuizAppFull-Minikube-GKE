# Manual Cloud SQL Setup Guide

If you prefer to set up Cloud SQL manually or the automated script doesn't meet your needs, follow these steps.

## Step 1: Install Prerequisites

See `PREREQUISITES.md` for installing gcloud CLI.

## Step 2: Authenticate and Configure

```bash
# Login to GCP
gcloud auth login

# Set your project (replace with your actual project ID)
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Set region
export REGION="us-central1"
gcloud config set compute/region $REGION
```

## Step 3: Enable Required APIs

```bash
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## Step 4: Create Cloud SQL Instance

```bash
# Set instance configuration
export INSTANCE_NAME="quizapp-postgres-prod"
export DB_VERSION="POSTGRES_15"
export DB_TIER="db-g1-small"  # Adjust based on your needs

# Create instance (takes 5-10 minutes)
gcloud sql instances create $INSTANCE_NAME \
    --database-version=$DB_VERSION \
    --tier=$DB_TIER \
    --region=$REGION \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --database-flags=max_connections=500 \
    --availability-type=zonal \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase

# Get connection name
export CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME \
    --format='get(connectionName)')
echo "Connection Name: $CONNECTION_NAME"
```

## Step 5: Create Databases

```bash
# Create dev database
gcloud sql databases create dev --instance=$INSTANCE_NAME

# Create prod database
gcloud sql databases create prod --instance=$INSTANCE_NAME

# Verify
gcloud sql databases list --instance=$INSTANCE_NAME
```

## Step 6: Create Users and Set Passwords

```bash
# Generate secure passwords
export DEV_PASSWORD=$(openssl rand -base64 32)
export PROD_PASSWORD=$(openssl rand -base64 32)

# IMPORTANT: Save these passwords somewhere secure!
echo "Dev Password: $DEV_PASSWORD"
echo "Prod Password: $PROD_PASSWORD"

# Create dev user
gcloud sql users create dev_user \
    --instance=$INSTANCE_NAME \
    --password=$DEV_PASSWORD

# Create prod user
gcloud sql users create prod_user \
    --instance=$INSTANCE_NAME \
    --password=$PROD_PASSWORD
```

## Step 7: Store Passwords in Secret Manager (Optional but Recommended)

```bash
# Store dev password
echo -n "$DEV_PASSWORD" | gcloud secrets create quizapp-dev-db-password \
    --data-file=- \
    --replication-policy="automatic"

# Store prod password
echo -n "$PROD_PASSWORD" | gcloud secrets create quizapp-prod-db-password \
    --data-file=- \
    --replication-policy="automatic"

# Later, retrieve passwords:
# gcloud secrets versions access latest --secret=quizapp-dev-db-password
```

## Step 8: Set Up Local Development Access

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create quizapp-local-dev \
    --display-name="QuizApp Local Development"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Create and download key
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=quizapp-local-dev@${PROJECT_ID}.iam.gserviceaccount.com

# Secure the key file
chmod 600 gcp-key.json
```

### Install Cloud SQL Proxy

```bash
# Download
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64

# Make executable
chmod +x cloud-sql-proxy

# Move to PATH
sudo mv cloud-sql-proxy /usr/local/bin/

# Verify
cloud-sql-proxy --version
```

## Step 9: Create Environment File

Create a `.env` file in your project root:

```bash
cat > .env << EOF
# GCP Configuration
CONNECTION_NAME=$CONNECTION_NAME
GCP_KEY_PATH=$(pwd)/gcp-key.json

# Database Credentials (for dev database)
DEV_DB_PASSWORD=$DEV_PASSWORD

# Django Settings
DJANGO_SECRET_KEY=$(openssl rand -base64 32)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# Add to .gitignore
echo ".env" >> .gitignore
echo "gcp-key.json" >> .gitignore
```

## Step 10: Test Local Setup

```bash
# Start Docker Compose with Cloud SQL
docker-compose -f docker-compose.cloud-sql.yml up -d

# Check logs
docker-compose -f docker-compose.cloud-sql.yml logs cloud-sql-proxy
docker-compose -f docker-compose.cloud-sql.yml logs web

# Run migrations
docker-compose -f docker-compose.cloud-sql.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.cloud-sql.yml exec web python manage.py createsuperuser

# Access application at http://localhost:8000
```

## Step 11: Verify Database Connection

```bash
# Connect directly to dev database
gcloud sql connect $INSTANCE_NAME --user=dev_user --database=dev

# Inside psql:
# \dt                    # List tables
# \q                     # Quit
```

## Troubleshooting

### Cloud SQL Proxy Connection Issues

```bash
# Test proxy manually
cloud-sql-proxy $CONNECTION_NAME --port 5433

# In another terminal, test connection
PGPASSWORD=$DEV_PASSWORD psql -h 127.0.0.1 -p 5433 -U dev_user -d dev
```

### Docker Compose Issues

```bash
# View detailed logs
docker-compose -f docker-compose.cloud-sql.yml logs -f

# Restart services
docker-compose -f docker-compose.cloud-sql.yml down
docker-compose -f docker-compose.cloud-sql.yml up -d
```

### Permission Issues

```bash
# Verify service account has correct permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:quizapp-local-dev*"
```

## Cost Management

```bash
# Check current instance cost
gcloud sql instances describe $INSTANCE_NAME --format="value(settings.tier)"

# Stop instance when not in use (dev/test only)
gcloud sql instances patch $INSTANCE_NAME --activation-policy=NEVER

# Restart instance
gcloud sql instances patch $INSTANCE_NAME --activation-policy=ALWAYS
```

## Next Steps

1. ✅ Cloud SQL instance created
2. ✅ Local development environment configured
3. Test application thoroughly
4. Set up GKE deployment (see `gcp-database-migration-guide.md`)
5. Configure CI/CD pipeline
6. Set up monitoring and alerts

## Quick Reference Commands

```bash
# View all instances
gcloud sql instances list

# View databases
gcloud sql databases list --instance=$INSTANCE_NAME

# View users
gcloud sql users list --instance=$INSTANCE_NAME

# Connect to database
gcloud sql connect $INSTANCE_NAME --user=dev_user --database=dev

# View instance details
gcloud sql instances describe $INSTANCE_NAME

# Create backup
gcloud sql backups create --instance=$INSTANCE_NAME

# List backups
gcloud sql backups list --instance=$INSTANCE_NAME
```

## Important Notes

1. **Security**: Keep `gcp-key.json` and `.env` files secure and never commit to version control
2. **Costs**: db-g1-small costs ~$50/month. Monitor usage in GCP Console
3. **Backups**: Automated daily backups are configured at 3:00 AM
4. **Maintenance**: Weekly maintenance on Sundays at 4:00 AM
5. **Scaling**: You can change instance tier anytime with minimal downtime

For more detailed information, see the complete guide in `gcp-database-migration-guide.md`.
