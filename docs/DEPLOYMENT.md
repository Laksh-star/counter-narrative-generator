# Deployment Guide

Complete guide for deploying Counter-Narrative Generator to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**
   - Create an account at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable billing for your account

2. **Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   # macOS
   brew install google-cloud-sdk

   # Or download from https://cloud.google.com/sdk/docs/install

   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Docker**
   - Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

4. **OpenRouter API Key**
   - Get your API key from [openrouter.ai/keys](https://openrouter.ai/keys)

## Step 1: GCP Project Setup

### Option A: Using the Setup Script (Recommended)

```bash
cd deployment
./setup-gcp.sh
```

This script will:
- Prompt for your GCP project ID
- Enable required APIs (Cloud Run, Container Registry, Cloud Build, Secret Manager)
- Create a secret for your OpenRouter API key
- Configure your project

### Option B: Manual Setup

```bash
# Set your project ID
PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create secret
echo "your_openrouter_api_key" | gcloud secrets create openrouter-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openrouter-api-key \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Step 2: Deploy Backend

### Using the Deploy Script

```bash
cd deployment
./deploy-backend.sh
```

### Manual Backend Deployment

```bash
cd backend

# Build image
PROJECT_ID=$(gcloud config get-value project)
docker build -t gcr.io/$PROJECT_ID/counter-narrative-backend .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/counter-narrative-backend

# Deploy to Cloud Run
gcloud run deploy counter-narrative-backend \
    --image gcr.io/$PROJECT_ID/counter-narrative-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600s \
    --set-secrets "OPENROUTER_API_KEY=openrouter-api-key:latest" \
    --set-env-vars "CORS_ORIGINS=*"
```

### Verify Backend

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe counter-narrative-backend \
    --region us-central1 \
    --format 'value(status.url)')

# Test health endpoint
curl $BACKEND_URL/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vectorstore_loaded": true,
  "api_key_configured": true
}
```

## Step 3: Deploy Frontend

### Using the Deploy Script

```bash
cd deployment
./deploy-frontend.sh
```

### Manual Frontend Deployment

```bash
cd frontend

# Get backend URL
PROJECT_ID=$(gcloud config get-value project)
BACKEND_URL=$(gcloud run services describe counter-narrative-backend \
    --region us-central1 \
    --format 'value(status.url)')

# Build image with backend URL
docker build \
    --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL \
    -t gcr.io/$PROJECT_ID/counter-narrative-frontend .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/counter-narrative-frontend

# Deploy to Cloud Run
gcloud run deploy counter-narrative-frontend \
    --image gcr.io/$PROJECT_ID/counter-narrative-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL"
```

### Access Your Application

```bash
# Get frontend URL
FRONTEND_URL=$(gcloud run services describe counter-narrative-frontend \
    --region us-central1 \
    --format 'value(status.url)')

echo "Application URL: $FRONTEND_URL"
```

Open the URL in your browser to access the application.

## Configuration Options

### Backend Configuration

**Memory and CPU**
```bash
--memory 2Gi              # Increase for better performance
--cpu 2                   # Increase for parallel processing
--min-instances 0         # Scale to zero when idle
--max-instances 10        # Limit concurrent instances
```

**Timeout**
```bash
--timeout 600s            # Max query execution time
```

**Environment Variables**
```bash
--set-env-vars "CORS_ORIGINS=https://your-domain.com"
--set-env-vars "FORETHOUGHT_MODEL=google/gemini-2.5-flash"
```

### Frontend Configuration

**Memory and CPU**
```bash
--memory 512Mi            # Usually sufficient
--cpu 1                   # Single CPU is enough
```

**Custom Domain**
```bash
gcloud run services update counter-narrative-frontend \
    --region us-central1 \
    --allow-unauthenticated

gcloud run domain-mappings create \
    --service counter-narrative-frontend \
    --region us-central1 \
    --domain your-domain.com
```

## Monitoring and Logs

### View Logs

```bash
# Backend logs
gcloud run services logs read counter-narrative-backend \
    --region us-central1 \
    --limit 50

# Frontend logs
gcloud run services logs read counter-narrative-frontend \
    --region us-central1 \
    --limit 50
```

### Cloud Console

Access logs and metrics at:
- Backend: https://console.cloud.google.com/run/detail/us-central1/counter-narrative-backend
- Frontend: https://console.cloud.google.com/run/detail/us-central1/counter-narrative-frontend

### Set Up Alerts

```bash
# Create alert for error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Counter-Narrative Error Rate" \
    --condition-display-name="Error Rate > 5%" \
    --condition-threshold-value=0.05
```

## Cost Management

### View Current Costs

```bash
gcloud billing projects describe $PROJECT_ID
```

Or visit: https://console.cloud.google.com/billing

### Set Budget Alerts

1. Go to [Cloud Console Billing](https://console.cloud.google.com/billing)
2. Select your billing account
3. Click "Budgets & alerts"
4. Create a new budget (e.g., $50/month)
5. Set alert thresholds (50%, 90%, 100%)

### Optimize Costs

**Scale to Zero**
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --min-instances 0
```

**Reduce Memory**
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --memory 1Gi
```

**Set Request Limits**
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --max-instances 5
```

## Updating Deployments

### Update Backend

```bash
cd backend
# Make your changes
docker build -t gcr.io/$PROJECT_ID/counter-narrative-backend .
docker push gcr.io/$PROJECT_ID/counter-narrative-backend
gcloud run deploy counter-narrative-backend \
    --image gcr.io/$PROJECT_ID/counter-narrative-backend \
    --region us-central1
```

### Update Frontend

```bash
cd frontend
# Make your changes
docker build -t gcr.io/$PROJECT_ID/counter-narrative-frontend .
docker push gcr.io/$PROJECT_ID/counter-narrative-frontend
gcloud run deploy counter-narrative-frontend \
    --image gcr.io/$PROJECT_ID/counter-narrative-frontend \
    --region us-central1
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service counter-narrative-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic counter-narrative-backend \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

## Troubleshooting

### Cold Start Issues

**Problem**: First request after idle period is slow (5-10s)

**Solution**: Keep at least one instance warm
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --min-instances 1
```

### Memory Issues

**Problem**: Service crashes with "out of memory" errors

**Solution**: Increase memory allocation
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --memory 4Gi
```

### Timeout Issues

**Problem**: Requests fail with timeout errors

**Solution**: Increase timeout
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --timeout 900s
```

### Secret Access Issues

**Problem**: Backend can't access OpenRouter API key

**Solution**: Grant secret access
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openrouter-api-key \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Security Best Practices

### Enable HTTPS Only

Cloud Run services are HTTPS by default. Never expose HTTP endpoints.

### Restrict CORS

```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --set-env-vars "CORS_ORIGINS=https://your-frontend-domain.com"
```

### Enable Authentication (Optional)

```bash
# Require authentication
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --no-allow-unauthenticated

# Create service account
gcloud iam service-accounts create counter-narrative-invoker

# Grant invoke permission
gcloud run services add-iam-policy-binding counter-narrative-backend \
    --region us-central1 \
    --member="serviceAccount:counter-narrative-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Regular Updates

```bash
# Update base images regularly
docker pull python:3.10-slim
docker pull node:20-alpine

# Rebuild and redeploy
./deploy-backend.sh
./deploy-frontend.sh
```

## Clean Up

### Delete Services

```bash
gcloud run services delete counter-narrative-backend --region us-central1
gcloud run services delete counter-narrative-frontend --region us-central1
```

### Delete Images

```bash
gcloud container images delete gcr.io/$PROJECT_ID/counter-narrative-backend
gcloud container images delete gcr.io/$PROJECT_ID/counter-narrative-frontend
```

### Delete Secrets

```bash
gcloud secrets delete openrouter-api-key
```

## Support

For deployment issues:
1. Check [Cloud Run documentation](https://cloud.google.com/run/docs)
2. Review logs in Cloud Console
3. Open an issue on GitHub
