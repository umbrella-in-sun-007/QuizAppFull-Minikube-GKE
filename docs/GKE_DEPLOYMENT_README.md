# GKE Production Deployment - Quick Reference

## 📑 Navigation
- [← Back to Main README](../README.md)
- [GCP Infrastructure Guide](gcp.md)
- [Kubernetes Guide](k8s.md)
- [Cloud SQL Setup](CLOUD_SQL_SETUP.md)
- [Project Status](PROJECT_STATUS.md)

## Table of Contents
1. [Deployment Status](#-deployment-status-success)
2. [Access Information](#access-information)
3. [Key Components](#key-components)
4. [Common Operations](#common-operations)
5. [Next Steps](#next-steps)

---

## ✅ Deployment Status: SUCCESS

**Cluster:** `quizapp-cluster` (us-central1)
**Namespace:** `production`
**Workload Identity:** Enabled (Secure access to Cloud SQL)
**Database:** `quizapp-postgres-prod` (Connected via private IP/Proxy)

---

## Access Information

**Ingress IP:** 34.117.237.73
**Domain:** `quizapp.example.com` (Update DNS to point to 34.117.237.73)

**Superuser Credentials:**
- Username: `neerajadhav`
- Email: `neerajadhav@duck.com`
- Password: `StU&ilS2706`

---

## Key Components

### 1. Application (`deployment.yaml`)
- **Replicas:** 2 (Autoscales to 10)
- **Image:** `gcr.io/data-rainfall-476920-v0/quizapp:latest`
- **Sidecar:** Cloud SQL Proxy (Secure DB connection)
- **Health Checks:** Liveness & Readiness probes configured

### 2. Service & Ingress (`service.yaml`, `ingress.yaml`)
- **Service:** ClusterIP (Internal load balancing)
- **Ingress:** Google Cloud Load Balancer
- **SSL:** Google-managed certificate (`quizapp-cert`)

### 3. Security
- **Workload Identity:** `quizapp-ksa` bound to `quizapp-gke-sa`
- **Secrets:** Database password & Django secret key stored in Kubernetes Secrets
- **Network:** Private communication with Cloud SQL

---

## Common Operations

### Check Status
```bash
# Pods
kubectl get pods -n production

# Services & Ingress
kubectl get svc,ingress -n production

# Logs
kubectl logs -n production -l app=quizapp -c web
```

### Updates
1. Build new image:
   ```bash
   docker build -t gcr.io/data-rainfall-476920-v0/quizapp:v2 -f Dockerfile.production .
   docker push gcr.io/data-rainfall-476920-v0/quizapp:v2
   ```
2. Update deployment:
   ```bash
   kubectl set image deployment/quizapp web=gcr.io/data-rainfall-476920-v0/quizapp:v2 -n production
   ```

### Database Management
```bash
# Run migrations
kubectl exec -it deployment/quizapp -n production -c web -- python manage.py migrate

# Create superuser
kubectl exec -it deployment/quizapp -n production -c web -- python manage.py createsuperuser
```

### Scaling
```bash
# Manual scale
kubectl scale deployment/quizapp --replicas=5 -n production

# Check HPA status
kubectl get hpa -n production
```

---

## Next Steps

1. **Wait for Ingress IP:** Run `kubectl get ingress -n production --watch` until an IP is assigned.
2. **Update DNS:** Point your domain (`quizapp.example.com`) to the Ingress IP.
3. **Verify SSL:** Wait for Google to provision the certificate (takes 15-60 mins).
4. **Monitor:** Check Google Cloud Console for logs and metrics.
