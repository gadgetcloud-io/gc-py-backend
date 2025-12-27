#!/usr/bin/env python3
"""
Create Test Users for Each Role

This script creates test users for customer, partner, support, and admin roles
in the Firestore database.
"""

import os
import sys
from datetime import datetime
from passlib.context import CryptContext
from google.cloud import firestore

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_test_users(project_id: str = "gadgetcloud-stg", database_id: str = "gc-db"):
    """Create test users for each role"""

    # Initialize Firestore client
    db = firestore.Client(project=project_id, database=database_id)

    # Define test users
    test_users = [
        {
            "userId": "test-customer-001",
            "email": "customer@gadgetcloud.io",
            "password": "Customer123!",
            "firstName": "Test",
            "lastName": "Customer",
            "mobile": "+919876543210",
            "role": "customer",
            "status": "active"
        },
        {
            "userId": "test-partner-001",
            "email": "partner@gadgetcloud.io",
            "password": "Partner123!",
            "firstName": "Test",
            "lastName": "Partner",
            "mobile": "+919876543211",
            "role": "partner",
            "status": "active"
        },
        {
            "userId": "test-support-001",
            "email": "support@gadgetcloud.io",
            "password": "Support123!",
            "firstName": "Test",
            "lastName": "Support",
            "mobile": "+919876543212",
            "role": "support",
            "status": "active"
        },
        {
            "userId": "test-admin-001",
            "email": "admin@gadgetcloud.io",
            "password": "Admin123!",
            "firstName": "Test",
            "lastName": "Admin",
            "mobile": "+919876543213",
            "role": "admin",
            "status": "active"
        }
    ]

    print(f"Creating test users in project: {project_id}, database: {database_id}")
    print("=" * 80)

    created_count = 0
    skipped_count = 0

    for user_data in test_users:
        email = user_data["email"]
        password = user_data.pop("password")  # Remove password from user_data
        user_id = user_data["userId"]
        role = user_data["role"]

        # Check if user already exists
        users_ref = db.collection("gc-users")
        existing_user = users_ref.where("email", "==", email).limit(1).get()

        if len(list(existing_user)) > 0:
            print(f"⏭️  SKIPPED: {email} (already exists)")
            skipped_count += 1
            continue

        # Hash password
        hashed_password = hash_password(password)

        # Create user document
        user_doc = {
            "userId": user_id,
            "email": email,
            "passwordHash": hashed_password,
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "mobile": user_data.get("mobile"),
            "role": role,
            "status": "active",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "updatedAt": datetime.utcnow().isoformat() + "Z"
        }

        # Save to Firestore
        users_ref.document(user_id).set(user_doc)

        print(f"✅ CREATED: {email} (role: {role}, password: {password})")
        created_count += 1

    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total:   {len(test_users)}")

    if created_count > 0:
        print("\n🔑 Test User Credentials:")
        print("=" * 80)
        for user_data in test_users:
            # Reconstruct password (we removed it earlier)
            role = user_data["role"]
            password = f"{role.capitalize()}123!"
            print(f"\n{role.upper()} User:")
            print(f"  Email:    {user_data['email']}")
            print(f"  Password: {password}")
            print(f"  Role:     {role}")
        print("\n" + "=" * 80)

    return created_count, skipped_count


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create test users for each role")
    parser.add_argument(
        "--project",
        default="gadgetcloud-stg",
        help="GCP project ID (default: gadgetcloud-stg)"
    )
    parser.add_argument(
        "--database",
        default="gc-db",
        help="Firestore database ID (default: gc-db)"
    )

    args = parser.parse_args()

    try:
        created, skipped = create_test_users(args.project, args.database)

        if created > 0:
            print("\n✅ Test users created successfully!")
            print("\nYou can now login at: https://gadgetcloud-stg.web.app")
        else:
            print("\nℹ️  No new users created (all already exist)")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error creating test users: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
