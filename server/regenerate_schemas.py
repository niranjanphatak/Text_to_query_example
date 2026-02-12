#!/usr/bin/env python3
"""
Script to regenerate schemas without any example data or enum values.
This ensures the schema contains ONLY structural information.
"""

import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from schema_generator import SchemaGenerator
from config import Config

def regenerate_clean_schemas():
    """Regenerate schemas without any example data"""
    
    print("=" * 60)
    print("Regenerating Schemas (No Data, Structure Only)")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
        print("\n✓ Configuration validated")
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        return
    
    # Connect to MongoDB
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.DB_NAME]
        print(f"✓ Connected to MongoDB: {Config.DB_NAME}")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return
    
    # Get all collections
    collections = db.list_collection_names()
    print(f"\n✓ Found {len(collections)} collections:")
    for coll in collections:
        print(f"  - {coll}")
    
    # Initialize schema generator
    schema_file_path = os.path.join('./data/schemas', 'schemas.json')
    generator = SchemaGenerator(db, schema_file_path)
    
    # Generate schemas (overwrite mode to replace existing schemas)
    print(f"\n{'=' * 60}")
    print("Generating schemas...")
    print(f"{'=' * 60}\n")
    
    result = generator.generate_schemas(
        collections,
        sample_size=100,
        detect_relationships=True,
        merge_strategy='overwrite'  # Overwrite to ensure clean schemas
    )
    
    if result['success']:
        print(f"\n{'=' * 60}")
        print("✅ Schema Generation Complete!")
        print(f"{'=' * 60}")
        print(f"Collections analyzed: {result['stats']['collections_analyzed']}")
        print(f"Relationships found: {result['stats']['relationships_found']}")
        print(f"Total fields: {result['stats']['total_fields']}")
        print(f"\n✓ Schemas saved to: {schema_file_path}")
        print("\n⚠️  IMPORTANT: The new schemas contain NO example data or enum values")
        print("   Only structural information (field names, types, indexes) is included.")
    else:
        print(f"\n✗ Schema generation failed")

if __name__ == "__main__":
    regenerate_clean_schemas()
