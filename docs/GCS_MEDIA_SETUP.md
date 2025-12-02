# Google Cloud Storage for Media Files

This guide explains how media files (images, documents) are stored in Google Cloud Storage (GCS) for both Production and Development environments.

## Overview

- **Bucket Name:** `quizapp-media-476920`
- **Location:** `us-central1`
- **Access:** Public Read (for media files)
- **Service Account:** `quizapp-gke-sa` (Production), `gcp-key.json` (Development)

## Configuration

### 1. Requirements
The following packages are installed:
- `django-storages[google]`
- `google-cloud-storage`

### 2. Django Settings
In `production.py` and `dev.py`:
```python
if os.getenv("GS_BUCKET_NAME"):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": os.getenv("GS_BUCKET_NAME"),
            "default_acl": "publicRead",
        },
    }
```

### 3. Environment Variables
- `GS_BUCKET_NAME`: Name of the GCS bucket.
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the service account key (Dev only). In Prod, Workload Identity is used.

## Usage

### Production (GKE)
- The application automatically uses GCS for all `FileField` and `ImageField` uploads.
- Workload Identity authorizes the pod to write to the bucket.
- Media URL: `https://storage.googleapis.com/quizapp-media-476920/...`

### Development (Local)
- The local Docker container is configured to use the SAME bucket.
- It uses the `gcp-key.json` mounted at `/tmp/gcp-key.json`.
- **Note:** Files uploaded locally will be visible in production and vice versa.

## Verification
To verify GCS is working:
1. Log in to the Wagtail Admin.
2. Go to **Images** and upload a new image.
3. Right-click the image and select "Copy Image Address".
4. The URL should start with `https://storage.googleapis.com/quizapp-media-476920/`.
