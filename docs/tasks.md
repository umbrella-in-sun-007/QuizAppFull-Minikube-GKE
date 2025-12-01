# Deployment Tasks for QuizApp on GKE

## Current Progress
- [x] **Application Codebase**: Django/Wagtail application structure is ready.
- [x] **Containerization**: 
    - `Dockerfile` exists (needs minor update).
    - `docker-compose.yml` exists for local testing.
    - `gunicorn.conf.py` is ready.
- [x] **Static Files**: Configured to use `Whitenoise` in `quizapp/settings/production.py`.
- [x] **Database Configuration**: Application is ready to connect to Postgres via `DATABASE_URL`.

## Next Steps

### 1. Docker Configuration
- [ ] **Update Dockerfile**: Add `CMD` instruction to start the application using Gunicorn.
    ```dockerfile
    CMD ["gunicorn", "-c", "gunicorn.conf.py", "quizapp.wsgi:application"]
    ```

### 2. Infrastructure Setup (Google Cloud)
- [ ] **Artifact Registry**: Create a repository to store Docker images.
- [ ] **GKE Cluster**: Provision a Standard or Autopilot GKE cluster.
- [ ] **Cloud SQL**: Provision a PostgreSQL instance.
    - Create a database (e.g., `quizapp`).
    - Create a user and password.
- [ ] **Service Account**: Set up Workload Identity or download a service account key for Cloud SQL access (if using Cloud SQL Auth Proxy).

### 3. Kubernetes Manifests
Create a `k8s/` directory and the following files:
- [ ] **`k8s/secrets.yaml`**: Store sensitive data (`DJANGO_SECRET_KEY`, `DATABASE_URL` or DB credentials).
- [ ] **`k8s/configmap.yaml`**: Store non-sensitive config (`DJANGO_SETTINGS_MODULE`, `DJANGO_ALLOWED_HOSTS`).
- [ ] **`k8s/deployment.yaml`**: Define the application deployment.
    - Configure liveness and readiness probes.
    - Mount secrets/configmaps.
    - (Optional) Sidecar for Cloud SQL Auth Proxy if using Cloud SQL.
- [ ] **`k8s/service.yaml`**: Expose the deployment internally (ClusterIP).
- [ ] **`k8s/ingress.yaml`**: Expose the service to the internet (ManagedCertificate + Ingress).
- [ ] **`k8s/migration-job.yaml`**: A Job to run `python manage.py migrate` before/during deployment.

### 4. Deployment Execution
- [ ] Build and push the Docker image to Artifact Registry.
- [ ] Apply Secrets and ConfigMaps.
- [ ] Run the Migration Job.
- [ ] Apply Deployment and Service.
- [ ] Configure DNS for the Ingress IP.

### 5. Post-Deployment
- [ ] Create a superuser (via `kubectl exec` or a temporary job).
- [ ] Verify static files are serving correctly.
- [ ] Verify media file persistence (Note: Local filesystem storage in containers is ephemeral. For production, consider configuring `django-storages` with Google Cloud Storage).
