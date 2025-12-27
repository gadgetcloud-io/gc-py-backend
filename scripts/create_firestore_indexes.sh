#!/bin/bash
#
# Create Firestore Composite Indexes for Audit Logs
#
# Usage: ./scripts/create_firestore_indexes.sh [project-id] [database-id]
#
# Examples:
#   ./scripts/create_firestore_indexes.sh gadgetcloud-prd gc-db
#   ./scripts/create_firestore_indexes.sh gadgetcloud-stg gc-db
#

PROJECT_ID="${1:-gadgetcloud-prd}"
DATABASE_ID="${2:-gc-db}"

echo "=================================================="
echo "Creating Firestore Indexes"
echo "=================================================="
echo "Project:  $PROJECT_ID"
echo "Database: $DATABASE_ID"
echo "--------------------------------------------------"
echo

# Index 1: eventType + timestamp (descending)
echo "Creating index: gc-audit-logs (eventType ASC, timestamp DESC)..."
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="$DATABASE_ID" \
  --collection-group=gc-audit-logs \
  --field-config=field-path=eventType,order=ascending \
  --field-config=field-path=timestamp,order=descending \
  --quiet 2>&1 || echo "  ℹ️  Index may already exist or be building"

echo

# Index 2: actorId + timestamp (descending)
echo "Creating index: gc-audit-logs (actorId ASC, timestamp DESC)..."
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="$DATABASE_ID" \
  --collection-group=gc-audit-logs \
  --field-config=field-path=actorId,order=ascending \
  --field-config=field-path=timestamp,order=descending \
  --quiet 2>&1 || echo "  ℹ️  Index may already exist or be building"

echo

# Index 3: targetId + timestamp (descending)
echo "Creating index: gc-audit-logs (targetId ASC, timestamp DESC)..."
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="$DATABASE_ID" \
  --collection-group=gc-audit-logs \
  --field-config=field-path=targetId,order=ascending \
  --field-config=field-path=timestamp,order=descending \
  --quiet 2>&1 || echo "  ℹ️  Index may already exist or be building"

echo
echo "=================================================="
echo "Index Creation Complete"
echo "=================================================="
echo
echo "Note: Indexes may take 10-15 minutes to build."
echo "Check status at:"
echo "https://console.cloud.google.com/firestore/databases/$DATABASE_ID/indexes?project=$PROJECT_ID"
echo
