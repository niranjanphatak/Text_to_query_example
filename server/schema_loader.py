import os
import json
from typing import Dict, List

class SchemaLoader:
    """
    Loads and manages MongoDB collection schemas
    Only schema structures are loaded, never actual data
    """
    
    def __init__(self, schema_directory: str):
        self.schema_directory = schema_directory
        self.schemas = {}
        self.load_schemas()
    
    def load_schemas(self):
        """Load all schema files from the schema directory"""
        if not os.path.exists(self.schema_directory):
            print(f"Warning: Schema directory not found: {self.schema_directory}")
            return
        
        # First, check if schemas.json exists (new format)
        schemas_file = os.path.join(self.schema_directory, 'schemas.json')
        if os.path.exists(schemas_file):
            try:
                with open(schemas_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check if it's the new multi-collection format
                    if 'collections' in data:
                        print(f"✓ Loading schemas from schemas.json (multi-collection format)")
                        for collection_name, collection_schema in data['collections'].items():
                            # Convert to standard schema format
                            schema = {
                                'collection': collection_name,
                                'description': collection_schema.get('description', ''),
                                'fields': collection_schema.get('fields', {}),
                                'indexes': self._extract_indexes(collection_schema.get('fields', {}))
                            }
                            self.schemas[collection_name] = schema
                            print(f"  ✓ Loaded schema: {collection_name}")
                        return
            except Exception as e:
                print(f"✗ Error loading schemas.json: {e}")
        
        # Fallback: Load individual schema files (old format)
        for filename in os.listdir(self.schema_directory):
            if filename.endswith('.json') and filename != 'schemas.json':
                filepath = os.path.join(self.schema_directory, filename)
                try:
                    with open(filepath, 'r') as f:
                        schema = json.load(f)
                        collection_name = schema.get('collection')
                        if collection_name:
                            self.schemas[collection_name] = schema
                            print(f"✓ Loaded schema: {collection_name}")
                except Exception as e:
                    print(f"✗ Error loading schema {filename}: {e}")
    
    def _extract_indexes(self, fields: Dict) -> List[Dict]:
        """Extract index information from fields"""
        indexes = []
        for field_name, field_info in fields.items():
            if field_info.get('indexed'):
                indexes.append({
                    'field': field_name,
                    'unique': field_info.get('unique', False)
                })
        return indexes
    
    def get_schema(self, collection_name: str) -> Dict:
        """Get schema for a specific collection"""
        return self.schemas.get(collection_name)
    
    def get_all_schemas(self) -> Dict:
        """Get all loaded schemas"""
        return self.schemas
    
    def get_schema_summary(self, collection_name: str) -> str:
        """
        Get a human-readable summary of a schema
        This is what gets passed to AI - structure only, no data
        """
        schema = self.get_schema(collection_name)
        if not schema:
            return f"Schema not found for collection: {collection_name}"
        
        summary = f"Collection: {collection_name}\n"
        summary += f"Description: {schema.get('description', 'N/A')}\n\n"
        summary += "Fields:\n"
        
        fields = schema.get('fields', {})
        for field_name, field_info in fields.items():
            field_type = field_info.get('type', 'unknown')
            field_desc = field_info.get('description', '')
            summary += f"  - {field_name} ({field_type}): {field_desc}\n"
            
            # Handle nested objects
            if field_type == 'object' and 'properties' in field_info:
                for prop_name, prop_info in field_info['properties'].items():
                    prop_type = prop_info.get('type', 'unknown')
                    summary += f"    - {field_name}.{prop_name} ({prop_type})\n"
            
            # Handle arrays
            if field_type == 'array' and 'items' in field_info:
                items_type = field_info['items'].get('type', 'unknown')
                summary += f"    (array of {items_type})\n"
            
            # Show enum values if available
            if 'enum' in field_info:
                summary += f"    Allowed values: {', '.join(field_info['enum'])}\n"
        
        # Add indexes information
        if 'indexes' in schema:
            summary += "\nIndexes:\n"
            for index in schema['indexes']:
                field = index.get('field', 'unknown')
                unique = ' (unique)' if index.get('unique') else ''
                summary += f"  - {field}{unique}\n"
        
        return summary
    
    def get_all_schemas_summary(self) -> str:
        """
        Get summary of all schemas
        This is passed to AI for context - structure only
        """
        summary = "Available Collections:\n\n"
        
        for collection_name in self.schemas.keys():
            schema = self.schemas[collection_name]
            summary += f"• {collection_name}: {schema.get('description', 'N/A')}\n"
        
        summary += "\n" + "=" * 60 + "\n\n"
        
        for collection_name in self.schemas.keys():
            summary += self.get_schema_summary(collection_name)
            summary += "\n" + "=" * 60 + "\n\n"
        
        return summary
    
    def get_collection_names(self) -> List[str]:
        """Get list of all collection names"""
        return list(self.schemas.keys())
