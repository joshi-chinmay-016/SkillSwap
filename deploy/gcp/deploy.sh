#!/usr/bin/env bash
# ==============================================================================
# SkillSwap Arena — Google Cloud Platform Production Deployment Pipeline
# Builds, tests, migrates, and deploys backend & frontend to GCP Cloud Run
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-${GCP_REGION:-us-central1}}"
REPO_NAME="skillswap-repo"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy.sh <GCP_PROJECT_ID> [GCP_REGION]"
    exit 1
fi

echo "================================================================="
echo " Starting SkillSwap Arena GCP Deployment ($PROJECT_ID / $REGION)"
echo "================================================================="

# 1. Enable Required GCP APIs
echo "==> Ensuring required GCP services are enabled..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    cloudbuild.googleapis.com \
    --project="$PROJECT_ID"

# 2. Ensure Artifact Registry Docker repository exists
echo "==> Checking Artifact Registry repository ($REPO_NAME)..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="SkillSwap Arena Production Container Images" \
        --project="$PROJECT_ID"
fi

REGISTRY_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

# 3. Build & Push Backend Container
echo "==> Building and pushing backend container image..."
gcloud builds submit backend \
    --tag="${REGISTRY_URL}/skillswap-backend:latest" \
    --project="$PROJECT_ID"

# 4. Build & Push Frontend Container
echo "==> Building and pushing frontend container image..."
gcloud builds submit frontend \
    --tag="${REGISTRY_URL}/skillswap-frontend:latest" \
    --project="$PROJECT_ID"

# 5. Run Database Migrations via Cloud Run Job
echo "==> Executing Alembic database migrations..."
gcloud run jobs deploy skillswap-db-migration \
    --image="${REGISTRY_URL}/skillswap-backend:latest" \
    --region="$REGION" \
    --command="alembic" \
    --args="upgrade,head" \
    --set-secrets="DATABASE_URL=skillswap-database-url:latest" \
    --project="$PROJECT_ID"

gcloud run jobs execute skillswap-db-migration --region="$REGION" --wait --project="$PROJECT_ID"

# 6. Deploy Backend to Cloud Run
echo "==> Deploying backend service to Cloud Run..."
gcloud run deploy skillswap-backend \
    --image="${REGISTRY_URL}/skillswap-backend:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --cpu=1 \
    --memory=1Gi \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="ENVIRONMENT=production" \
    --set-secrets="DATABASE_URL=skillswap-database-url:latest,SECRET_KEY=skillswap-secret-key:latest,REDIS_URL=skillswap-redis-url:latest,GEMINI_API_KEY=skillswap-gemini-key:latest,GOOGLE_CLIENT_ID=skillswap-google-client-id:latest,GOOGLE_CLIENT_SECRET=skillswap-google-client-secret:latest" \
    --project="$PROJECT_ID"

BACKEND_URL=$(gcloud run services describe skillswap-backend --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID")
echo "Backend deployed at: $BACKEND_URL"

# 7. Deploy Frontend to Cloud Run
echo "==> Deploying frontend service to Cloud Run..."
gcloud run deploy skillswap-frontend \
    --image="${REGISTRY_URL}/skillswap-frontend:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --port=80 \
    --cpu=0.5 \
    --memory=256Mi \
    --min-instances=1 \
    --max-instances=5 \
    --project="$PROJECT_ID"

FRONTEND_URL=$(gcloud run services describe skillswap-frontend --region="$REGION" --format='value(status.url)' --project="$PROJECT_ID")
echo "Frontend deployed at: $FRONTEND_URL"

echo "================================================================="
echo " SkillSwap Arena GCP Deployment Completed Successfully!"
echo " Frontend URL: $FRONTEND_URL"
echo " Backend API:  $BACKEND_URL"
echo " Health Check: ${BACKEND_URL}/health"
echo " Metrics:      ${BACKEND_URL}/metrics"
echo "================================================================="
