#!/bin/bash

# Frontend Deployment Script for Google Cloud Run

set -e

echo "🚀 Deploying Counter-Narrative Generator Frontend to Cloud Run"
echo ""

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project configured. Run ./setup-gcp.sh first."
    exit 1
fi

# Get backend URL
BACKEND_SERVICE="counter-narrative-backend"
REGION="us-central1"
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)' 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend service not found. Deploy backend first with ./deploy-backend.sh"
    exit 1
fi

# Configuration
SERVICE_NAME="counter-narrative-frontend"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Backend URL: $BACKEND_URL"
echo ""
echo "📦 Building Docker image..."
cd ../frontend
docker build \
    --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL \
    -t $IMAGE_NAME .

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
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL"

echo ""
echo "✅ Frontend deployed successfully!"
echo ""

# Get the service URL
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "🎉 Deployment complete! Access your app at:"
echo "   $FRONTEND_URL"
