# Cloud SQL Deployment - Quick Reference

## ✅ Deployment Complete!

### Access Your Application

**Application URL:** http://localhost:8000
**Admin Panel:** http://localhost:8000/admin/

**Superuser Credentials:**
- Username: `neerajadhav`
- Email: `neerajadhav@duck.com`
- Password: `my-secure-password`

---

## Instance Details

**Cloud SQL PostgreSQL:**
- Instance Name: `quizapp-postgres-prod`
- Connection: `data-rainfall-476920-v0:us-central1:quizapp-postgres-prod`
- IP Address: `35.223.142.162`
- Region: `us-central1`
- Version: PostgreSQL 15
- Tier: `db-f1-micro`

**Databases:**
- `dev` - Local development (currently in use)
- `prod` - Production (for GKE deployment)

**Users:**
- `dev_user` - Dev database access
- `prod_user` - Prod database access

---

## Common Commands

### Start/Stop Application

```bash
# Start
docker compose -f docker-compose.cloud-sql.yml up -d

# Stop
docker compose -f docker-compose.cloud-sql.yml down

# Restart
docker compose -f docker-compose.cloud-sql.yml restart
```

### View Logs

```bash
# All logs
docker compose -f docker-compose.cloud-sql.yml logs -f

# Specific service
docker compose -f docker-compose.cloud-sql.yml logs -f web
docker compose -f docker-compose.cloud-sql.yml logs -f cloud-sql-proxy
```

### Django Management Commands

```bash
# Run migrations
docker compose -f docker-compose.cloud-sql.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.cloud-sql.yml exec web python manage.py createsuperuser

# Django shell
docker compose -f docker-compose.cloud-sql.yml exec web python manage.py shell

# Collect static files
docker compose -f docker-compose.cloud-sql.yml exec web python manage.py collectstatic
```

### Database Access

```bash
# Via gcloud (direct connection)
gcloud sql connect quizapp-postgres-prod --user=dev_user --database=dev

# Via psql (through Cloud SQL Proxy)
# First, get the password from .env file
PGPASSWORD=<DEV_DB_PASSWORD> psql -h localhost -p 5432 -U dev_user -d dev
```

### Cloud SQL Management

```bash
# Check instance status
gcloud sql instances describe quizapp-postgres-prod

# List databases
gcloud sql databases list --instance=quizapp-postgres-prod

# List users
gcloud sql users list --instance=quizapp-postgres-prod

# Create manual backup
gcloud sql backups create --instance=quizapp-postgres-prod

# List backups
gcloud sql backups list --instance=quizapp-postgres-prod

# Export and Download Backup
# See: docs/CLOUD_SQL_BACKUP_DOWNLOAD.md
```

---

## File Structure

```
/run/media/super/Data/Projects/QuizAppFull/
├── .env                              # Environment variables (DON'T COMMIT)
├── gcp-key.json                      # Service account key (DON'T COMMIT)
├── docker-compose.cloud-sql.yml      # Docker Compose for Cloud SQL
├── Dockerfile.cloud-sql-proxy        # Custom Cloud SQL Proxy image
├── continue-setup.sh                 # Database setup script
└── quizapp/settings/dev.py           # Django dev settings with Cloud SQL
```

---

## Configuration Files

### Environment Variables (.env)

```bash
CONNECTION_NAME=data-rainfall-476920-v0:us-central1:quizapp-postgres-prod
GCP_KEY_PATH=/run/media/super/Data/Projects/QuizAppFull/gcp-key.json
DEV_DB_PASSWORD=<stored in file>
DJANGO_SECRET_KEY=<stored in file>
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Django Settings

Current: `quizapp.settings.dev`
- Database: Cloud SQL dev database
- Debug: True
- Fallback: SQLite (if USE_CLOUD_SQL=false)

---

## Troubleshooting

### Application won't start

```bash
# Check container status
docker compose -f docker-compose.cloud-sql.yml ps

# View detailed logs
docker compose -f docker-compose.cloud-sql.yml logs

# Restart containers
docker compose -f docker-compose.cloud-sql.yml restart
```

### Database connection issues

```bash
# Check Cloud SQL Proxy logs
docker compose -f docker-compose.cloud-sql.yml logs cloud-sql-proxy

# Verify Cloud SQL instance is running
gcloud sql instances describe quizapp-postgres-prod --format="value(state)"

# Test connection directly
gcloud sql connect quizapp-postgres-prod --user=dev_user --database=dev
```

### Can't access admin panel

1. Verify superuser exists:
   ```bash
   docker compose -f docker-compose.cloud-sql.yml exec web python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> User.objects.filter(is_superuser=True)
   ```

2. Reset superuser password if needed:
   ```bash
   docker compose -f docker-compose.cloud-sql.yml exec web python manage.py changepassword neerajadhav
   ```

---

## Cost Management

**Current Setup:** ~$12-15/month
- Instance: db-f1-micro (~$10/month)
- Storage: 10GB SSD (~$1.70/month)
- Backups: ~$0.80/month

**To reduce costs:**
```bash
# Stop instance when not in use (dev/test only!)
gcloud sql instances patch quizapp-postgres-prod --activation-policy=NEVER

# Restart when needed
gcloud sql instances patch quizapp-postgres-prod --activation-policy=ALWAYS
```

---

## Security Checklist

- [x] `.env` added to `.gitignore`
- [x] `gcp-key.json` added to `.gitignore`
- [x] Passwords stored in Secret Manager
- [x] Service account with minimal permissions
- [x] Separate dev/prod databases
- [x] Automated backups enabled
- [ ] SSL/TLS for production connections (for GKE deployment)
- [ ] Rotate passwords regularly

---

## Next Steps

### Immediate
1. ✅ Test application at http://localhost:8000
2. ✅ Login to admin panel
3. Import existing data (if any)
4. Test all application features

### For Production
1. Deploy to GKE (see gcp-database-migration-guide.md)
2. Use `prod` database for production
3. Set up CI/CD pipeline
4. Configure custom domain and SSL
5. Set up monitoring and alerts

---

## Support Resources

- **Walkthrough:** `/home/super/.gemini/antigravity/brain/.../walkthrough.md`
- **Full Guide:** `gcp-database-migration-guide.md`
- **Setup Script:** `continue-setup.sh`

**Cloud SQL Documentation:**
- https://cloud.google.com/sql/docs/postgres
- https://cloud.google.com/sql/docs/postgres/connect-docker

**Django on GCP:**
- https://cloud.google.com/python/django
- https://cloud.google.com/python/django/kubernetes-engine
