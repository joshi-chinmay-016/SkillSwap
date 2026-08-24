#!/usr/bin/env bash
# ==============================================================================
# SkillSwap Arena — GCP Secret Manager Provisioning Script
# Securely initializes production secrets and grants least-privilege IAM roles
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./setup-secrets.sh <GCP_PROJECT_ID>"
    exit 1
fi

echo "==> Configuring Secret Manager secrets for project: $PROJECT_ID"

create_or_update_secret() {
    local SECRET_NAME="$1"
    local SECRET_VAL="$2"

    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "Secret $SECRET_NAME already exists. Adding new version..."
        echo -n "$SECRET_VAL" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
    else
        echo "Creating secret $SECRET_NAME..."
        echo -n "$SECRET_VAL" | gcloud secrets create "$SECRET_NAME" --data-file=- --replication-policy="automatic" --project="$PROJECT_ID"
    fi
}

echo "Generating cryptographically secure JWT signing key..."
JWT_SECRET=$(openssl rand -hex 32)
create_or_update_secret "skillswap-secret-key" "$JWT_SECRET"

echo "Provisioning placeholder templates for external credentials (update values as needed)..."
create_or_update_secret "skillswap-database-url" "postgresql://skillswap_app:CHANGEME@10.0.0.3:5432/skillswap_prod"
create_or_update_secret "skillswap-redis-url" "redis://10.0.0.4:6379/0"
create_or_update_secret "skillswap-gemini-key" "AIzaSy_YOUR_PROD_GEMINI_KEY"
create_or_update_secret "skillswap-google-client-id" "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
create_or_update_secret "skillswap-google-client-secret" "GOCSPX_YOUR_GOOGLE_CLIENT_SECRET"

echo "Granting Secret Accessor role to Cloud Run backend service account..."
BACKEND_SA="skillswap-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com"

SECRETS=(
    "skillswap-secret-key"
    "skillswap-database-url"
    "skillswap-redis-url"
    "skillswap-gemini-key"
    "skillswap-google-client-id"
    "skillswap-google-client-secret"
)

for S in "${SECRETS[@]}"; do
    gcloud secrets add-iam-policy-binding "$S" \
        --member="serviceAccount:${BACKEND_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" >/dev/null
done

echo "==> Secret Manager setup successfully completed."
