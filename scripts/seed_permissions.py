#!/usr/bin/env python3
"""
Seed Permissions Script

Initializes the gc-permissions collection with default role permissions.
Run this script once when setting up the system for the first time.

Usage:
    python scripts/seed_permissions.py
"""

import sys
import os
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.permission_service import PermissionService


async def seed_permissions():
    """Seed default permissions for all roles"""

    print("Seeding permissions for GadgetCloud roles...")
    print("=" * 60)

    # Customer Role Permissions
    customer_permissions = {
        "items": {
            "actions": ["view", "create", "edit", "delete"],
            "scope": "own"  # Can only access their own items
        },
        "profile": {
            "actions": ["view", "edit"],
            "scope": "own"
        },
        "repairs": {
            "actions": ["view", "create"],
            "scope": "own"
        }
    }

    await PermissionService.create_role_permissions(
        role="customer",
        description="Standard customer with access to personal devices and repairs",
        resources=customer_permissions
    )
    print("✓ Created permissions for role: customer")

    # Partner Role Permissions
    partner_permissions = {
        "items": {
            "actions": ["view", "create", "edit", "delete"],
            "scope": "own"
        },
        "profile": {
            "actions": ["view", "edit"],
            "scope": "own"
        },
        "repairs": {
            "actions": ["view", "edit", "update_status"],
            "scope": "assigned"  # Can access repairs assigned to them
        },
        "inventory": {
            "actions": ["view", "edit"],
            "scope": "own"
        },
        "customers": {
            "actions": ["view"],
            "scope": "assigned"  # Can view customers they service
        }
    }

    await PermissionService.create_role_permissions(
        role="partner",
        description="Service partner with access to assigned repairs and inventory",
        resources=partner_permissions
    )
    print("✓ Created permissions for role: partner")

    # Support Role Permissions
    support_permissions = {
        "items": {
            "actions": ["view"],
            "scope": "all"  # Can view all items for support purposes
        },
        "profile": {
            "actions": ["view", "edit"],
            "scope": "own"
        },
        "repairs": {
            "actions": ["view", "edit", "update_status"],
            "scope": "all"  # Can manage all repairs
        },
        "customers": {
            "actions": ["view"],
            "scope": "all"  # Can view all customers
        },
        "support_tickets": {
            "actions": ["view", "create", "edit", "resolve"],
            "scope": "all"
        },
        "audit_logs": {
            "actions": ["view"],
            "scope": "own"  # Can only view their own actions
        }
    }

    await PermissionService.create_role_permissions(
        role="support",
        description="Support staff with access to customer data and support tickets",
        resources=support_permissions
    )
    print("✓ Created permissions for role: support")

    # Admin Role Permissions
    admin_permissions = {
        "items": {
            "actions": ["view", "create", "edit", "delete"],
            "scope": "all"
        },
        "profile": {
            "actions": ["view", "edit"],
            "scope": "own"  # Admins can only edit their own profile
        },
        "repairs": {
            "actions": ["view", "create", "edit", "delete"],
            "scope": "all"
        },
        "users": {
            "actions": ["view", "create", "edit", "delete", "change_role", "deactivate"],
            "scope": "all"
        },
        "customers": {
            "actions": ["view", "edit"],
            "scope": "all"
        },
        "partners": {
            "actions": ["view", "create", "edit", "deactivate"],
            "scope": "all"
        },
        "support_tickets": {
            "actions": ["view", "create", "edit", "delete", "resolve"],
            "scope": "all"
        },
        "audit_logs": {
            "actions": ["view", "export"],
            "scope": "all"  # Can view all audit logs
        },
        "permissions": {
            "actions": ["view", "edit"],
            "scope": "all"  # Can manage role permissions
        },
        "inventory": {
            "actions": ["view", "create", "edit", "delete"],
            "scope": "all"
        }
    }

    await PermissionService.create_role_permissions(
        role="admin",
        description="Full system administrator with all permissions",
        resources=admin_permissions
    )
    print("✓ Created permissions for role: admin")

    print("=" * 60)
    print("✅ All permissions seeded successfully!")
    print()
    print("Role Summary:")
    print("  - customer: Personal devices and repairs")
    print("  - partner:  Assigned repairs and inventory")
    print("  - support:  Customer support and tickets")
    print("  - admin:    Full system access")
    print()


async def verify_permissions():
    """Verify that all permissions were created correctly"""

    print("Verifying permissions...")
    print("-" * 60)

    roles = ["customer", "partner", "support", "admin"]

    for role in roles:
        perms = await PermissionService.get_role_permissions(role)
        if perms:
            resource_count = len(perms.get("resources", {}))
            print(f"  ✓ {role:12} - {resource_count} resources configured")
        else:
            print(f"  ✗ {role:12} - NOT FOUND")

    print("-" * 60)
    print()


async def main():
    """Main function"""
    try:
        # Seed permissions
        await seed_permissions()

        # Verify permissions
        await verify_permissions()

        print("🎉 Permission seeding completed successfully!")
        print()
        print("Next steps:")
        print("  1. Create Firestore composite indexes for audit logs")
        print("  2. Test the permission system with sample users")
        print()

    except Exception as e:
        print(f"❌ Error seeding permissions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
