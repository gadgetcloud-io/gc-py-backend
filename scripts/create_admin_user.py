#!/usr/bin/env python3
"""
Create Admin User

Creates a test admin user for testing admin endpoints.

Usage:
    python scripts/create_admin_user.py
"""

import sys
import os
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.user_service import UserService


async def create_admin_user():
    """Create an admin user for testing"""

    email = "admin@gadgetcloud.io"
    password = "Admin123!"
    first_name = "Admin"
    last_name = "User"

    print("Creating admin user...")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print()

    try:
        # Check if user already exists
        existing_user = await UserService.get_user_by_email(email)
        if existing_user:
            print(f"✓ Admin user already exists with ID: {existing_user['id']}")
            print(f"  Role: {existing_user.get('role')}")
            print()
            return existing_user["id"]

        # Create admin user
        user = await UserService.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="admin"  # Set as admin
        )

        print(f"✅ Admin user created successfully!")
        print(f"  ID: {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        print()

        print("You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print()

        return user["id"]

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_admin_user())
