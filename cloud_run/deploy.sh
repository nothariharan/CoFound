#!/usr/bin/env bash
# CoFounder ADK Planner — deployment notes (requires GCP billing for Cloud Run / Agent Engine)
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-cofound-agent}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-cofounder-adk-planner}"

# Build and deploy the standalone planner service to Cloud Run:
# gcloud run deploy "${SERVICE_NAME}" \
#   --source ./cloud_run \
#   --project "${PROJECT_ID}" \
#   --region "${REGION}" \
#   --allow-unauthenticated \
#   --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY},GEMINI_PRO_MODEL=gemini-2.5-pro,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"

# Optional: deploy the same ADK agent to Vertex AI Agent Engine (billing required):
# adk deploy agent_engine \
#   --project="${PROJECT_ID}" \
#   --location="${REGION}" \
#   --display_name=cofounder-planner \
#   ../backend/agents/adk/planner_agent.py

echo "Edit this script, uncomment commands, and run after GCP billing is enabled."
