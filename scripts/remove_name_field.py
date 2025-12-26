#!/usr/bin/env python3
"""
Remove 'name' field from all gc-users documents

This script removes the redundant 'name' field from existing user documents.
The name can be computed from firstName and lastName when needed.
"""

import sys
from google.cloud import firestore

def remove_name_field(project_id: str, database: str = "gc-db"):
    """Remove name field from all users in gc-users collection"""

    # Initialize Firestore client
    db = firestore.Client(project=project_id, database=database)

    # Get all users
    users_ref = db.collection("gc-users")
    docs = users_ref.stream()

    updated_count = 0
    skipped_count = 0

    print(f"Scanning gc-users collection in {project_id}/{database}...")

    for doc in docs:
        user_data = doc.to_dict()

        # Check if name field exists
        if "name" in user_data:
            # Remove the name field
            doc.reference.update({
                "name": firestore.DELETE_FIELD
            })
            print(f"✓ Removed 'name' field from user {doc.id} ({user_data.get('email')})")
            updated_count += 1
        else:
            print(f"- User {doc.id} has no 'name' field, skipping")
            skipped_count += 1

    print(f"\nSummary:")
    print(f"  Updated: {updated_count} users")
    print(f"  Skipped: {skipped_count} users")
    print(f"  Total: {updated_count + skipped_count} users")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove_name_field.py <project_id> [database]")
        print("Example: python remove_name_field.py gadgetcloud-prd gc-db")
        sys.exit(1)

    project = sys.argv[1]
    database = sys.argv[2] if len(sys.argv) > 2 else "gc-db"

    print(f"This will remove the 'name' field from all users in {project}/{database}")
    confirm = input("Continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("Aborted")
        sys.exit(0)

    remove_name_field(project, database)
    print("\nDone!")
