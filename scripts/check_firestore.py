#!/usr/bin/env python3
"""
Check Firestore data - Quick database inspection tool

Usage:
  python scripts/check_firestore.py                    # Check all collections (uses .env config)
  python scripts/check_firestore.py --collection users # Check specific collection
  python scripts/check_firestore.py --project stg      # Override project (prd or stg)
"""
import argparse
from google.cloud import firestore
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_collection(db, collection_name, display_name=None):
    """Check and display a Firestore collection"""
    if display_name is None:
        display_name = collection_name
    
    print(f"\n📋 {display_name}:")
    print("-" * 60)
    
    coll_ref = db.collection(collection_name)
    docs = coll_ref.stream()
    
    doc_count = 0
    for doc in docs:
        doc_count += 1
        doc_data = doc.to_dict()
        
        # Redact sensitive fields
        if 'passwordHash' in doc_data:
            doc_data['passwordHash'] = '[REDACTED]'
        
        print(f"\nDocument ID: {doc.id}")
        print(json.dumps(doc_data, indent=2, default=str))
    
    if doc_count == 0:
        print("  (empty)")
    
    print(f"\n{'=' * 60}")
    print(f"Total documents: {doc_count}")
    return doc_count

def main():
    # Get project ID and database from environment or use defaults
    default_project = os.getenv('PROJECT_ID', 'gadgetcloud-prd')
    default_database = os.getenv('FIRESTORE_DATABASE', 'gcdb')

    parser = argparse.ArgumentParser(description='Check Firestore data')
    parser.add_argument('--project', default=default_project,
                       help=f'GCP project (default: {default_project} from .env)')
    parser.add_argument('--collection', help='Specific collection to check (gc-users, gc-items, etc.)')
    parser.add_argument('--database', default=default_database,
                       help=f'Firestore database name (default: {default_database} from .env)')

    args = parser.parse_args()

    print(f"=== Firestore Data Check ===")
    print(f"Project: {args.project}")
    print(f"Database: {args.database}\n")
    
    # Initialize Firestore client
    try:
        db = firestore.Client(project=args.project, database=args.database)
    except Exception as e:
        print(f"Error connecting to Firestore: {e}")
        sys.exit(1)
    
    # Check specific collection or all collections
    if args.collection:
        check_collection(db, args.collection)
    else:
        # Check all known collections
        total = 0
        total += check_collection(db, "gc-users", "Users Collection (gc-users)")
        total += check_collection(db, "gc-items", "Items Collection (gc-items)")
        total += check_collection(db, "gc-repairs", "Repairs Collection (gc-repairs)")
        total += check_collection(db, "gc-common-config", "Config Collection (gc-common-config)")
        
        print(f"\n{'=' * 60}")
        print(f"Grand total: {total} documents across all collections")

if __name__ == "__main__":
    main()
