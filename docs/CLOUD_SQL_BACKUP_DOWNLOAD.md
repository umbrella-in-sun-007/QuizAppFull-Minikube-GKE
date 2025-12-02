# Cloud SQL Backup & Download Guide

This guide explains how to export a Cloud SQL database and download the backup file to your local machine.

> [!NOTE]
> Cloud SQL automated backups cannot be downloaded directly. You must **export** the database to a Google Cloud Storage (GCS) bucket first.

## Prerequisites

1.  **Google Cloud Storage Bucket**: You need a bucket to store the export.
2.  **Permissions**: The Cloud SQL Service Account must have `Storage Object Admin` (or `Writer`) permissions on the bucket.

## Step 1: Create a Storage Bucket (If needed)

```bash
export PROJECT_ID="your-project-id"
export BUCKET_NAME="${PROJECT_ID}-sql-backups"
export REGION="us-central1"

# Create bucket
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION
```

## Step 2: Grant Permissions

Find your Cloud SQL Service Account email and grant it access to the bucket.

```bash
# Get Service Account Email
export SA_EMAIL=$(gcloud sql instances describe quizapp-postgres-prod \
    --format="value(serviceAccountEmailAddress)")

# Grant permissions
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin"
```

## Step 3: Export Database

Export the specific database (e.g., `prod`) to a SQL dump file in the bucket.

```bash
export INSTANCE_NAME="quizapp-postgres-prod"
export DATABASE_NAME="prod"
export TIMESTAMP=$(date +%Y%m%d-%H%M%S)
export EXPORT_URI="gs://${BUCKET_NAME}/backup-${DATABASE_NAME}-${TIMESTAMP}.sql"

# Run export
gcloud sql export sql $INSTANCE_NAME $EXPORT_URI \
    --database=$DATABASE_NAME
```

> [!TIP]
> This command runs asynchronously. You can check the status in the GCP Console under **Operations**.

## Step 4: Download the Backup

Once the export is complete, download the file using `gcloud storage`.

```bash
# List files to confirm
gcloud storage ls gs://$BUCKET_NAME

# Download to current directory
gcloud storage cp $EXPORT_URI ./
```

## Troubleshooting

### "Permission denied" during export
- Ensure the **Cloud SQL Service Account** (not your personal account) has `roles/storage.objectAdmin` on the bucket.
- Verify the bucket is in the same region as the Cloud SQL instance to avoid cross-region data transfer costs (though not strictly required for functionality).

### "Database does not exist"
- Check the `--database` flag. List databases with:
  ```bash
  gcloud sql databases list --instance=$INSTANCE_NAME
  ```
