# Complete Setup Guide

Step-by-step guide from cloning the repository to running locally and deploying to Cloud Run.

## Overview

This guide covers three ways to use Counter-Narrative Generator:
1. **Web App (Docker)** - Recommended for most users
2. **CLI (Python)** - For programmatic access and scripts
3. **Cloud Run (Production)** - For public deployment

## Prerequisites

### Required
- Git
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

### For Web App & Cloud Run
- Docker Desktop ([install here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

### For CLI Only
- Python 3.10+
- pip

### For Cloud Run Deployment
- Google Cloud SDK ([install here](https://cloud.google.com/sdk/docs/install))
- Google Cloud account with billing enabled

---

## Part 1: Clone & Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Laksh-star/counter-narrative-generator.git
cd counter-narrative-generator
```

### 2. Configure API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
# macOS/Linux
nano .env

# Windows
notepad .env
```

Add this line to `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

**Save and close the file.**

---

## Part 2: Test Web App Locally (Docker)

This is the **recommended** way to test the full application.

### Step 1: Start Services

```bash
docker-compose up --build
```

**What happens:**
- Downloads necessary Docker images (~2-3 minutes first time)
- Builds backend and frontend containers
- Loads vector store (~5 minutes with 15,969 chunks)
- Starts both services

**Look for these success messages:**
```
backend  | ✅ VectorStore already loaded with 15,969 chunks
backend  | ✅ API ready to accept requests
backend  | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend | ▲ Next.js 14.0.0
frontend | - Local:        http://localhost:3000
```

### Step 2: Access the Application

Open your browser:
- **Frontend**: http://localhost:3000
- **Backend API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

### Step 3: Run a Test Query

1. Enter a belief: **"You need product-market fit before scaling"**
2. Click **Submit**
3. Watch real-time progress:
   - Forethought: Searching...
   - Quickaction: Structuring...
   - Examiner: Synthesizing...
4. Review results (should take 30-60 seconds)

### Step 4: Stop Services

Press `Ctrl+C` in the terminal, then:

```bash
docker-compose down
```

### Troubleshooting Web App

**Backend won't start**
```bash
# Check logs
docker-compose logs backend

# Common issue: API key not loaded
# Verify .env file exists and has OPENROUTER_API_KEY
```

**"No contrarian perspectives found"**
- Vector store may not be loaded - check backend logs
- Try a different belief
- Ensure 15,969 chunks loaded successfully

**Port already in use**
```bash
# Stop other services using ports 3000 or 8000
# macOS/Linux
lsof -ti:3000 | xargs kill
lsof -ti:8000 | xargs kill

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## Part 3: Test CLI (Python)

For command-line usage or programmatic access.

### Step 1: Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Load Vector Store

**First time only** (~6 minutes):

```bash
python main.py load
```

Expected output:
```
Loading chunks from content/output/chunks.jsonl
Processing 15,969 chunks...
✓ Created vector store with 15,969 chunks
```

**Verify**:
```bash
python main.py stats
```

Should show:
```
Vector Store Statistics:
- Total chunks: 15,969
- Episodes: ~300
- Topics: 12 categories
```

### Step 3: Run Test Queries

**Basic query:**
```bash
python main.py query "You need product-market fit before scaling"
```

**With topic filter:**
```bash
python main.py query "Move fast and break things" --topics growth-strategy product-development
```

**With user context:**
```bash
python main.py query "Focus on one thing" --user-context "B2B SaaS, 50 customers, deciding between features"
```

**Save to file:**
```bash
python main.py query "VC funding is essential" -o outputs/result.json
```

**Interactive mode:**
```bash
python main.py interactive
```

### Step 4: Deactivate Virtual Environment

```bash
deactivate
```

### Troubleshooting CLI

**"OPENROUTER_API_KEY not found"**
```bash
# Ensure .env file exists in backend/ directory
cp .env.example .env
# Edit .env and add your key
```

**"ChromaDB not found" or empty results**
```bash
# Reload vector store
python main.py load --force
```

**"ModuleNotFoundError"**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

---

## Part 4: Deploy to Google Cloud Run

For production deployment with auto-scaling and public access.

### Step 1: Install & Configure Google Cloud SDK

**Install:**
```bash
# macOS
brew install google-cloud-sdk

# Other OS: Download from https://cloud.google.com/sdk/docs/install
```

**Authenticate:**
```bash
gcloud auth login
gcloud auth application-default login
```

### Step 2: Create GCP Project

```bash
# Create new project
gcloud projects create your-project-id --name="Counter-Narrative"

# Set as active project
gcloud config set project your-project-id

# Enable billing
# Visit: https://console.cloud.google.com/billing
# Link billing account to your project
```

### Step 3: Run Setup Script

```bash
cd deployment
./setup-gcp.sh
```

**What it does:**
- Enables required APIs (Cloud Run, Container Registry, Secret Manager)
- Creates secret for OpenRouter API key
- Configures project settings

**You'll be prompted for:**
- Project ID
- OpenRouter API key
- Region (recommend: us-central1)

### Step 4: Deploy Backend

```bash
./deploy-backend.sh
```

**This will:**
- Build backend Docker image
- Push to Google Container Registry
- Deploy to Cloud Run
- Display backend URL

**Takes:** ~5-10 minutes

### Step 5: Deploy Frontend

```bash
./deploy-frontend.sh
```

**This will:**
- Build frontend with backend URL
- Push to Container Registry
- Deploy to Cloud Run
- Display frontend URL

**Takes:** ~3-5 minutes

### Step 6: Access Your Deployed App

```bash
# Get URLs
gcloud run services describe counter-narrative-frontend \
    --region us-central1 \
    --format 'value(status.url)'
```

Open the URL in your browser.

### Step 7: Test Deployed App

1. Visit your frontend URL
2. Run a test query: "You need product-market fit before scaling"
3. Verify results appear

### Troubleshooting Cloud Run

**Build fails on Apple Silicon (M1/M2/M3)**
```bash
# Add this to deployment scripts before docker build:
docker buildx build --platform linux/amd64 -t IMAGE_NAME .
```

**"Secret not found" error**
```bash
# Recreate secret
echo "your_api_key" | gcloud secrets create openrouter-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Grant access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openrouter-api-key \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

**"Out of memory" errors**
```bash
# Increase backend memory
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --memory 4Gi
```

**Timeout errors**
```bash
# Increase timeout
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --timeout 900s
```

### Managing Costs

**View current costs:**
```bash
# Visit: https://console.cloud.google.com/billing
```

**Set budget alerts:**
1. Go to [Cloud Billing](https://console.cloud.google.com/billing)
2. Select "Budgets & alerts"
3. Create budget ($50/month recommended)
4. Set alerts at 50%, 90%, 100%

**Scale to zero when idle:**
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --min-instances 0
```

**Keep warm for better UX (~$10-30/month):**
```bash
gcloud run services update counter-narrative-backend \
    --region us-central1 \
    --min-instances 1
```

---

## Next Steps

### Customize Configuration

**Change models** (edit `.env`):
```bash
# Budget option (~$0.01/query)
FORETHOUGHT_MODEL=google/gemini-2.5-flash-lite
QUICKACTION_MODEL=google/gemini-2.5-flash-lite
EXAMINER_MODEL=google/gemini-2.5-flash

# Premium option (~$0.08/query)
EXAMINER_MODEL=anthropic/claude-opus-4.5
```

### Monitor Usage

```bash
# Backend logs
docker-compose logs -f backend

# Cloud Run logs
gcloud run services logs read counter-narrative-backend \
    --region us-central1 \
    --limit 100
```

### Update Deployment

```bash
# Make changes to code

# Rebuild and redeploy
cd deployment
./deploy-backend.sh
./deploy-frontend.sh
```

---

## Quick Reference

### Local Web App
```bash
# Start
docker-compose up --build

# Access
open http://localhost:3000

# Stop
docker-compose down
```

### CLI
```bash
# Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py load

# Query
python main.py query "Your belief here"

# Stop
deactivate
```

### Cloud Run
```bash
# Deploy
cd deployment
./setup-gcp.sh
./deploy-backend.sh
./deploy-frontend.sh

# Get URL
gcloud run services describe counter-narrative-frontend \
    --region us-central1 \
    --format 'value(status.url)'

# Update
./deploy-backend.sh  # After changes
```

---

## Help & Support

- **Documentation**: [README.md](README.md), [USER_GUIDE.md](USER_GUIDE.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Issues**: https://github.com/Laksh-star/counter-narrative-generator/issues
- **API Docs**: http://localhost:8000/docs (when running locally)

---

**🎉 You're all set!** Start challenging conventional wisdom with evidence-based contrarian perspectives.
