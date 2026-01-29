#!/bin/bash

# Google Cloud Platform Setup Script
# This script initializes GCP project for Counter-Narrative Generator deployment

set -e

echo "🚀 Setting up Google Cloud Platform for Counter-Narrative Generator"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it from:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Prompt for project ID
read -p "Enter your GCP Project ID: " PROJECT_ID
gcloud config set project $PROJECT_ID

echo ""
echo "📦 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com

echo ""
echo "🔐 Setting up secrets..."
read -sp "Enter your OPENROUTER_API_KEY: " API_KEY
echo ""

# Create secret
echo "$API_KEY" | gcloud secrets create openrouter-api-key \
    --data-file=- \
    --replication-policy="automatic" || \
    echo "Secret already exists, updating..." && \
    echo "$API_KEY" | gcloud secrets versions add openrouter-api-key --data-file=-

echo ""
echo "✅ GCP setup complete!"
echo ""
echo "Next steps:"
echo "1. Run ./deploy-backend.sh to deploy the backend service"
echo "2. Run ./deploy-frontend.sh to deploy the frontend service"
