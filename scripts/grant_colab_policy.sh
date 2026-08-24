#!/bin/bash
set -euo pipefail

PROJECT_ID="fx-itnern"
MEMBER="group:fx-intern-dev@googlegroups.com"
CUSTOM_ROLE_ID="privateColabEnterpriseUser"
CUSTOM_ROLE="projects/${PROJECT_ID}/roles/${CUSTOM_ROLE_ID}"

# Copy the Colab Enterprise User role without the permission that lists every notebook.
PERMISSIONS="$(
  gcloud iam roles describe roles/aiplatform.colabEnterpriseUser --format=json \
    | jq -r '
        .includedPermissions
        - ["dataform.repositories.list", "resourcemanager.projects.list"]
        | join(",")
      '
)"

ROLE_FLAGS=(
  --project="$PROJECT_ID"
  --title="Private Colab Enterprise User"
  --description="Use Colab Enterprise without listing other users' notebooks"
  --permissions="$PERMISSIONS"
  --stage=GA
)

if gcloud iam roles describe "$CUSTOM_ROLE_ID" --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam roles update "$CUSTOM_ROLE_ID" "${ROLE_FLAGS[@]}"
else
  gcloud iam roles create "$CUSTOM_ROLE_ID" "${ROLE_FLAGS[@]}"
fi

# Let participants create/import notebooks and use their own runtimes.
for role in "$CUSTOM_ROLE" roles/aiplatform.notebookRuntimeUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$MEMBER" \
    --role="$role" \
    --condition=None
done
