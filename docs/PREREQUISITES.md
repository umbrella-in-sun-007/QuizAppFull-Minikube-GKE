# Prerequisites Installation Guide

## Install Google Cloud SDK (gcloud CLI)

### For Linux (Debian/Ubuntu)

```bash
# Add the Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the Cloud SDK
sudo apt-get update && sudo apt-get install google-cloud-cli

# Verify installation
gcloud --version
```

### For Arch Linux / Manjaro

```bash
# Install from AUR or official repos
yay -S google-cloud-sdk
# OR
sudo pacman -S google-cloud-cli

# Verify installation
gcloud --version
```

### Alternative: Install via Script

```bash
# Download the install script
curl https://sdk.cloud.google.com | bash

# Restart your shell
exec -l $SHELL

# Initialize gcloud
gcloud init

# Verify installation
gcloud --version
```

## Initial Configuration

After installation, configure gcloud:

```bash
# Login to your Google Cloud account
gcloud auth login

# List your projects
gcloud projects list

# Set your default project
gcloud config set project YOUR_PROJECT_ID

# Set default region
gcloud config set compute/region us-central1
```

## Install Cloud SQL Proxy

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64

# Make it executable
chmod +x cloud-sql-proxy

# Move to system path
sudo mv cloud-sql-proxy /usr/local/bin/

# Verify installation
cloud-sql-proxy --version
```

## Next Steps

After installing gcloud CLI and configuring it:

1. Run the automated setup script:
   ```bash
   ./setup-cloud-sql.sh
   ```

2. Or follow the manual setup guide in `CLOUD_SQL_SETUP.md`

## Troubleshooting

### gcloud command not found after installation

```bash
# Restart your shell
exec -l $SHELL

# Or source the completion script
source ~/.bashrc
# OR
source ~/.zshrc
```

### Permission denied when running gcloud

```bash
# Make sure gcloud is in your PATH
echo $PATH

# Add to PATH if needed (add to ~/.bashrc or ~/.zshrc)
export PATH=$PATH:$HOME/google-cloud-sdk/bin
```
