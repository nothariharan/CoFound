#!/usr/bin/env bash
# cofounder adk planner — deployment notes (requires gcp billing for cloud run / agent engine)
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-cofound-agent}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-cofounder-adk-planner}"

# build and deploy the standalone planner service to cloud run
# gcloud run deploy "${service_name}" \
# --source ./cloud_run \
# --project "${project_id}" \
# --region "${region}" \
# --allow unauthenticated \
# --set env vars "google_api_key=${google_api_key},gemini_pro_model=gemini 2.5 pro,google_cloud_project=${project_id}"

# optional: deploy the same adk agent to vertex ai agent engine (billing required)
# adk deploy agent_engine \
# --project="${project_id}" \
# --location="${region}" \
# --display_name=cofounder planner \
# ../backend/agents/adk/planner_agent.py

echo "Edit this script, uncomment commands, and run after GCP billing is enabled."
