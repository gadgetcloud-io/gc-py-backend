#!/usr/bin/env python3
"""Migrate customer1 user from gcdb to gc-db database."""

import os
import sys
from google.cloud import firestore

def migrate_user():
    """Migrate customer1@gadgetcloud.io from gcdb to gc-db."""
    project_id = "gadgetcloud-stg"

    # Connect to gcdb database
    print(f"🔍 Connecting to gcdb database...")
    db_source = firestore.Client(project=project_id, database="gcdb")

    # Connect to gc-db database
    print(f"🔍 Connecting to gc-db database...")
    db_target = firestore.Client(project=project_id, database="gc-db")

    # Find customer1 user in gcdb
    print(f"\n📋 Searching for customer1@gadgetcloud.io in gcdb...")
    users_ref = db_source.collection("gc-users")
    query = users_ref.where("email", "==", "customer1@gadgetcloud.io").limit(1)
    docs = list(query.stream())

    if not docs:
        print("❌ User customer1@gadgetcloud.io not found in gcdb")
        return False

    user_doc = docs[0]
    user_data = user_doc.to_dict()
    user_id = user_doc.id

    print(f"✅ Found user: {user_data.get('name')} ({user_data.get('email')})")
    print(f"   Document ID: {user_id}")

    # Check if user already exists in gc-db
    print(f"\n🔍 Checking if user exists in gc-db...")
    target_query = db_target.collection("gc-users").where("email", "==", "customer1@gadgetcloud.io").limit(1)
    target_docs = list(target_query.stream())

    if target_docs:
        print(f"⚠️  User already exists in gc-db (ID: {target_docs[0].id})")
        print(f"   Skipping migration.")
        return True

    # Copy user to gc-db
    print(f"\n📝 Copying user to gc-db...")
    target_ref = db_target.collection("gc-users").document(user_id)
    target_ref.set(user_data)

    print(f"✅ Successfully migrated customer1@gadgetcloud.io to gc-db")
    print(f"   Document ID: {user_id}")

    # Verify
    print(f"\n🔍 Verifying migration...")
    verify_doc = target_ref.get()
    if verify_doc.exists:
        print(f"✅ Verification successful")
        return True
    else:
        print(f"❌ Verification failed")
        return False

if __name__ == "__main__":
    try:
        success = migrate_user()
        if success:
            print("\n✅ Migration completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Migration failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
