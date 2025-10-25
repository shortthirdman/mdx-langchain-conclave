# GCP Deployment Guide for BakeryAI

This guide provides the steps to deploy the BakeryAI Docker container to Google Cloud Platform (GCP) using Artifact Registry and Cloud Run.

## 1. Prerequisites: gcloud CLI Setup

First, make sure you have the `gcloud` CLI installed and authenticated.

```bash
# Authenticate with GCP
gcloud auth login

# Configure your project and region (replace with your details)
gcloud config set project your-project-id
gcloud config set run/region us-central1
gcloud config set compute/region us-central1
```

## 2. Create an Artifact Registry Repository

You need a place to store your Docker image.

```bash
# Create a Docker repository in Artifact Registry (replace with your details)
gcloud artifacts repositories create bakery-repo --repository-format=docker --location=us-central1 --description="BakeryAI Docker repository"
```

## 3. Authenticate Docker

Configure Docker to use your GCP credentials to push images to Artifact Registry.

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## 4. Build and Push the Docker Image

Navigate to the project root directory before running these commands.

```bash
# Define your image name (use this command for PowerShell)
$env:IMAGE_NAME="us-central1-docker.pkg.dev/your-project-id/bakery-repo/bakery-api:latest"

# Build the image using the Dockerfile in the deployment directory
docker build -t $env:IMAGE_NAME -f deployment/Dockerfile .

# Push the image to Artifact Registry
docker push $env:IMAGE_NAME
```

## 5. Deploy to Cloud Run

This step deploys your container image to Cloud Run.

```powershell
# Read and format variables from .env, then deploy
$vars = (Get-Content .\.env | Where-Object { $_ -notmatch '^#' -and $_ -match '=' } | ForEach-Object { 
    $line = $_.Replace('LANGSMITH_API_KEY', 'LANGCHAIN_API_KEY').Replace('LANGSMITH_PROJECT', 'LANGCHAIN_PROJECT');
    $key, $value = $line -split '=', 2; 
    "$key=$value" 
}) -join ','

gcloud run deploy bakery-api `
  --image $env:IMAGE_NAME `
  --platform managed `
  --region us-central1 `
  --set-env-vars="$vars" `
  --allow-unauthenticated
```


After deployment, GCP will provide you with a public URL for your service.
