#!/bin/bash

# Backend Deployment Script for Google Cloud Run

set -e

echo "🚀 Deploying Counter-Narrative Generator Backend to Cloud Run"
echo ""

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project configured. Run ./setup-gcp.sh first."
    exit 1
fi

# Configuration
SERVICE_NAME="counter-narrative-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "📦 Building Docker image..."
cd ../backend
docker build -t $IMAGE_NAME .

echo ""
echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

echo ""
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600s \
    --set-secrets "OPENROUTER_API_KEY=openrouter-api-key:latest" \
    --set-env-vars "CORS_ORIGINS=*"

echo ""
echo "✅ Backend deployed successfully!"
echo ""

# Get the service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Test the health endpoint:"
echo "  curl $BACKEND_URL/api/health"
