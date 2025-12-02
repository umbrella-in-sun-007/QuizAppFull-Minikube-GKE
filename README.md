# QuizAppFull

## Project Overview
A robust, scalable Quiz Application built with Django, designed to handle high traffic loads. This application has been successfully deployed on Google Cloud Platform (GCP) and proven to handle **300 concurrent users** seamlessly.

## Key Features
- **Scalable Architecture**: Built to run on Kubernetes (GKE) with Cloud SQL.
- **High Performance**: Optimized for concurrent usage (tested with 300+ users).
- **Secure**: Integrated with Google Secret Manager for secure credential management.
- **User Friendly**: Intuitive interface for taking quizzes.

## Documentation
Detailed documentation is available in the `docs/` directory:

- **Setup Guides**:
    - [Manual Cloud SQL Setup](docs/MANUAL_SETUP.md)
    - [GCP Infrastructure Guide](docs/gcp.md)
    - [Kubernetes Deployment](docs/GKE_DEPLOYMENT_README.md)
    - [Local Development Prerequisites](docs/PREREQUISITES.md)

- **Reference**:
    - [Cloud SQL Quick Reference](docs/CLOUD_SQL_QUICK_REFERENCE.md)
    - [Backup & Download Guide](docs/CLOUD_SQL_BACKUP_DOWNLOAD.md)
    - [Tasks & TODOs](docs/tasks.md)

## Success Story
This project was deployed to GCP using a microservices architecture. During stress testing and live usage, it successfully managed 300 concurrent users taking quizzes simultaneously without performance degradation.

## Project Status
✅ **Completed** - See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for details.
