#!/bin/bash
set -euo pipefail

PROJECT_ID="fx-itnern"
MEMBER="group:fx-intern-dev@googlegroups.com"
ROLES=(
  "roles/aiplatform.colabEnterpriseUser"
  "roles/aiplatform.notebookRuntimeUser"
  "roles/dataform.editor"
)
LOCATION="asia-northeast1"

# Grant project level IAM roles to the MEMBER
for role in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$MEMBER" \
    --role="$role"
done

NOTEBOOK_ROLE="roles/dataform.codeEditor"

BASE_URL="https://dataform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/repositories"
TOKEN="$(gcloud auth print-access-token)"

WORK_DIR="$(mktemp -d /tmp/grant-colab-policy.XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

api() {
  local method="$1" url="$2"
  shift 2
  curl --fail --silent --show-error -X "$method" \
    -H "Authorization: Bearer ${TOKEN}" \
    "$@" \
    "$url"
}

# Collect every notebook (Dataform repository) in the location, page by page.
page_token=""
while :; do
  api GET "${BASE_URL}?pageSize=1000&pageToken=${page_token}" > "${WORK_DIR}/page.json"
  jq -r '.repositories // [] | .[].name' "${WORK_DIR}/page.json" >> "${WORK_DIR}/notebooks.txt"
  page_token="$(jq -r '.nextPageToken // ""' "${WORK_DIR}/page.json")"
  [[ -n "$page_token" ]] || break
done

# The applied policy is the same for every notebook.
jq -n \
  --arg role "${NOTEBOOK_ROLE}" \
  --arg member "${MEMBER}" \
  '{"policy": {"bindings": [{"role": $role, "members": [$member]}]}}' \
  > "${WORK_DIR}/policy.json"

while read -r notebook; do
  echo "Granting ${NOTEBOOK_ROLE} on ${notebook}"

  # Replace the resource-level IAM policy outright, dropping existing bindings.
  api POST "https://dataform.googleapis.com/v1/${notebook}:setIamPolicy" \
    -H "Content-Type: application/json" \
    --data-binary "@${WORK_DIR}/policy.json" \
    | jq .
done < "${WORK_DIR}/notebooks.txt"
