#!/usr/bin/env python3
"""Migrate all data from (default) database to gc-db database in production."""

import sys
from google.cloud import firestore

def migrate_collection(db_source, db_target, collection_name):
    """Migrate all documents from one collection to another."""
    print(f"\n📋 Migrating collection: {collection_name}")

    source_ref = db_source.collection(collection_name)
    target_ref = db_target.collection(collection_name)

    docs = list(source_ref.stream())

    if not docs:
        print(f"   ⚠️  Collection is empty, skipping")
        return 0

    migrated = 0
    for doc in docs:
        doc_data = doc.to_dict()
        doc_id = doc.id

        # Copy document to target database
        target_ref.document(doc_id).set(doc_data)
        migrated += 1

        # Redact sensitive fields for display
        display_data = doc_data.copy()
        if 'passwordHash' in display_data:
            display_data['passwordHash'] = '[REDACTED]'

        print(f"   ✅ Migrated: {doc_id}")
        if 'email' in display_data:
            print(f"      Email: {display_data.get('email')}")

    print(f"   📊 Total migrated: {migrated} documents")
    return migrated

def verify_migration(db_source, db_target, collection_name):
    """Verify that migration was successful."""
    print(f"\n🔍 Verifying collection: {collection_name}")

    source_count = len(list(db_source.collection(collection_name).stream()))
    target_count = len(list(db_target.collection(collection_name).stream()))

    if source_count == target_count:
        print(f"   ✅ Verification successful: {target_count} documents in both databases")
        return True
    else:
        print(f"   ❌ Verification failed: source={source_count}, target={target_count}")
        return False

def main():
    """Main migration function."""
    project_id = "gadgetcloud-prd"

    print("=" * 70)
    print("🚀 Production Database Migration: (default) → gc-db")
    print("=" * 70)

    # Connect to databases
    print(f"\n🔍 Connecting to databases in project: {project_id}")
    db_source = firestore.Client(project=project_id, database="(default)")
    db_target = firestore.Client(project=project_id, database="gc-db")

    collections = ["gc-users", "gc-items", "gc-repairs", "gc-common-config"]
    total_migrated = 0

    # Migrate all collections
    for collection_name in collections:
        count = migrate_collection(db_source, db_target, collection_name)
        total_migrated += count

    print("\n" + "=" * 70)
    print(f"📊 Migration Summary")
    print("=" * 70)
    print(f"   Total documents migrated: {total_migrated}")

    # Verify migration
    print("\n" + "=" * 70)
    print(f"🔍 Verification")
    print("=" * 70)

    all_verified = True
    for collection_name in collections:
        if not verify_migration(db_source, db_target, collection_name):
            all_verified = False

    if all_verified:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update production Cloud Run to use gc-db database")
        print("2. Test the production deployment")
        print("3. Delete the (default) database")
        return 0
    else:
        print("\n❌ Migration verification failed!")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
