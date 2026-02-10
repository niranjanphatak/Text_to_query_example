import json
import os
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import re


class SchemaGenerator:
    """
    Generates MongoDB collection schemas by analyzing actual data
    and detecting relationships between collections
    """
    
    def __init__(self, db, schema_file_path: str):
        """
        Initialize schema generator
        
        Args:
            db: MongoDB database instance
            schema_file_path: Path to schemas.json file
        """
        self.db = db
        self.schema_file_path = schema_file_path
        
    def analyze_collection(self, collection_name: str, sample_size: int = 100) -> Dict:
        """
        Analyze a collection to infer its schema
        
        Args:
            collection_name: Name of the collection to analyze
            sample_size: Number of documents to sample
            
        Returns:
            Dictionary containing schema analysis results
        """
        collection = self.db[collection_name]
        
        # Get total document count
        total_docs = collection.count_documents({})
        
        if total_docs == 0:
            return {
                'collection': collection_name,
                'description': f'Collection {collection_name} (empty)',
                'fields': {},
                'indexes': [],
                'total_documents': 0,
                'sampled_documents': 0
            }
        
        # Sample documents
        actual_sample_size = min(sample_size, total_docs)
        documents = list(collection.aggregate([
            {'$sample': {'size': actual_sample_size}}
        ]))
        
        # Analyze fields
        field_analysis = self._analyze_fields(documents)
        
        # Get indexes
        indexes = self._detect_indexes(collection)
        
        # Build schema
        fields = {}
        for field_name, analysis in field_analysis.items():
            field_def = {
                'type': analysis['primary_type'],
                'description': self._generate_field_description(field_name)
            }
            
            # Add indexed flag
            if field_name in indexes:
                field_def['indexed'] = True
                if indexes[field_name].get('unique'):
                    field_def['unique'] = True
            
            # Add enum values if detected
            if analysis.get('enum_values'):
                field_def['enum'] = sorted(list(analysis['enum_values']))
            
            # Add example value
            if analysis.get('example'):
                field_def['example'] = analysis['example']
            
            # Handle nested objects
            if analysis['primary_type'] == 'object' and analysis.get('properties'):
                field_def['properties'] = analysis['properties']
            
            # Handle arrays
            if analysis['primary_type'] == 'array' and analysis.get('items'):
                field_def['items'] = analysis['items']
            
            fields[field_name] = field_def
        
        return {
            'collection': collection_name,
            'description': f'Auto-generated schema for {collection_name} collection',
            'fields': fields,
            'indexes': list(indexes.keys()),
            'total_documents': total_docs,
            'sampled_documents': actual_sample_size
        }
    
    def _analyze_fields(self, documents: List[Dict]) -> Dict:
        """
        Analyze fields across multiple documents to infer types
        
        Args:
            documents: List of documents to analyze
            
        Returns:
            Dictionary mapping field names to their analysis
        """
        field_stats = defaultdict(lambda: {
            'types': Counter(),
            'values': [],
            'present_count': 0,
            'null_count': 0
        })
        
        # Collect statistics
        for doc in documents:
            self._collect_field_stats(doc, field_stats, prefix='')
        
        # Analyze each field
        total_docs = len(documents)
        field_analysis = {}
        
        for field_name, stats in field_stats.items():
            # Determine primary type
            primary_type = stats['types'].most_common(1)[0][0] if stats['types'] else 'unknown'
            
            analysis = {
                'primary_type': primary_type,
                'presence_rate': stats['present_count'] / total_docs,
                'example': stats['values'][0] if stats['values'] else None
            }
            
            # Detect enums (fields with limited distinct values)
            if primary_type == 'string':
                unique_values = set(stats['values'])
                if len(unique_values) <= 10 and len(unique_values) > 1:
                    analysis['enum_values'] = unique_values
            
            # Handle nested objects
            if primary_type == 'object':
                # For now, just note it's an object
                # Could recursively analyze nested fields
                pass
            
            # Handle arrays
            if primary_type == 'array':
                # Determine array item type
                item_types = Counter()
                for val in stats['values']:
                    if isinstance(val, list) and val:
                        item_types[self._get_type(val[0])] += 1
                
                if item_types:
                    analysis['items'] = {
                        'type': item_types.most_common(1)[0][0]
                    }
            
            field_analysis[field_name] = analysis
        
        return field_analysis
    
    def _collect_field_stats(self, obj: Any, stats: Dict, prefix: str = ''):
        """
        Recursively collect field statistics from a document
        
        Args:
            obj: Object to analyze (dict, list, or primitive)
            stats: Statistics dictionary to update
            prefix: Field name prefix for nested fields
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_name = f"{prefix}.{key}" if prefix else key
                
                if value is None:
                    stats[field_name]['null_count'] += 1
                else:
                    stats[field_name]['present_count'] += 1
                    value_type = self._get_type(value)
                    stats[field_name]['types'][value_type] += 1
                    
                    # Store sample values (limit to 100)
                    if len(stats[field_name]['values']) < 100:
                        if value_type in ['string', 'integer', 'boolean']:
                            stats[field_name]['values'].append(value)
                        elif value_type == 'array':
                            stats[field_name]['values'].append(value)
    
    def _get_type(self, value: Any) -> str:
        """
        Determine the type of a value
        
        Args:
            value: Value to check
            
        Returns:
            Type name as string
        """
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            # Check if it's an ISO date string
            if self._is_iso_date(value):
                return 'date'
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        elif hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
            return 'objectId'
        elif isinstance(value, datetime):
            return 'date'
        else:
            return 'unknown'
    
    def _is_iso_date(self, value: str) -> bool:
        """Check if a string looks like an ISO date"""
        if not isinstance(value, str):
            return False
        
        # Simple pattern matching for ISO dates
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        return bool(re.match(iso_pattern, value))
    
    def _detect_indexes(self, collection) -> Dict:
        """
        Detect indexes on a collection
        
        Args:
            collection: MongoDB collection
            
        Returns:
            Dictionary mapping field names to index info
        """
        indexes = {}
        
        for index_info in collection.list_indexes():
            # Skip the default _id index
            if index_info['name'] == '_id_':
                continue
            
            # Extract field names from index
            for field_name, direction in index_info['key'].items():
                indexes[field_name] = {
                    'unique': index_info.get('unique', False)
                }
        
        # Always include _id as indexed
        indexes['_id'] = {'unique': True}
        
        return indexes
    
    def _generate_field_description(self, field_name: str) -> str:
        """
        Generate a human-readable description from a field name
        
        Args:
            field_name: Field name
            
        Returns:
            Description string
        """
        # Handle special cases
        if field_name == '_id':
            return 'Unique document identifier'
        
        # Convert snake_case or camelCase to words
        words = re.sub(r'([A-Z])', r' \1', field_name)
        words = words.replace('_', ' ').strip()
        
        # Capitalize first letter
        return words.capitalize()
    
    def detect_relationships(self, collections_data: Dict[str, Dict]) -> Dict:
        """
        Detect relationships between collections
        
        Args:
            collections_data: Dictionary mapping collection names to their analysis
            
        Returns:
            Dictionary containing relationship information
        """
        relationships = []
        collection_names = set(collections_data.keys())
        
        # Phase 1: Analyze each collection for potential foreign keys
        for source_collection, data in collections_data.items():
            fields = data.get('fields', {})
            
            for field_name, field_info in fields.items():
                # Look for fields that might be foreign keys
                if self._is_potential_foreign_key(field_name, field_info):
                    # Try to find matching collection
                    target_collection = self._find_target_collection(
                        field_name, 
                        collection_names
                    )
                    
                    if target_collection:
                        # Validate the relationship by checking actual data
                        relationship = self._validate_relationship(
                            source_collection,
                            field_name,
                            target_collection,
                            field_info
                        )
                        
                        if relationship:
                            relationships.append(relationship)
        
        # Phase 2: Detect shared correlation fields (e.g., event_tracking_id)
        correlation_fields = self._detect_correlation_fields(collections_data)
        relationships.extend(correlation_fields)
        
        # Build relationships section
        if relationships:
            return self._build_relationships_section(relationships)
        else:
            return {
                'description': 'No relationships detected between collections',
                'links': []
            }
    
    def _is_potential_foreign_key(self, field_name: str, field_info: Dict) -> bool:
        """
        Check if a field might be a foreign key
        
        Args:
            field_name: Name of the field
            field_info: Field information
            
        Returns:
            True if field might be a foreign key
        """
        # Check field name patterns
        fk_patterns = [
            r'.*_id$',      # ends with _id
            r'.*_ids$',     # ends with _ids (array of IDs)
            r'.*_ref$',     # ends with _ref
            r'.*_key$',     # ends with _key
        ]
        
        for pattern in fk_patterns:
            if re.match(pattern, field_name, re.IGNORECASE):
                return True
        
        return False
    
    def _find_target_collection(self, field_name: str, collection_names: Set[str]) -> str:
        """
        Find the target collection for a foreign key field
        
        Args:
            field_name: Name of the foreign key field
            collection_names: Set of available collection names
            
        Returns:
            Target collection name or None
        """
        # Remove common suffixes
        base_name = re.sub(r'_(id|ids|ref|key)$', '', field_name, flags=re.IGNORECASE)
        
        # Try exact match (plural/singular variations)
        candidates = [
            base_name,
            base_name + 's',
            base_name[:-1] if base_name.endswith('s') else None,
            base_name + 'es',
            base_name[:-2] if base_name.endswith('es') else None,
        ]
        
        for candidate in candidates:
            if candidate and candidate in collection_names:
                return candidate
        
        return None
    
    def _validate_relationship(
        self, 
        source_collection: str, 
        field_name: str, 
        target_collection: str,
        field_info: Dict
    ) -> Dict:
        """
        Validate a potential relationship by checking actual data
        
        Args:
            source_collection: Source collection name
            field_name: Foreign key field name
            target_collection: Target collection name
            field_info: Field information
            
        Returns:
            Relationship dictionary or None if not valid
        """
        try:
            # Sample some values from the source collection
            source_coll = self.db[source_collection]
            target_coll = self.db[target_collection]
            
            # Get sample foreign key values (non-null)
            pipeline = [
                {'$match': {field_name: {'$ne': None, '$exists': True}}},
                {'$limit': 50},
                {'$project': {field_name: 1}}
            ]
            
            sample_docs = list(source_coll.aggregate(pipeline))
            
            if not sample_docs:
                return None
            
            # Extract foreign key values
            fk_values = []
            is_array = field_info.get('type') == 'array'
            
            for doc in sample_docs:
                value = doc.get(field_name)
                if value is not None:
                    if is_array and isinstance(value, list):
                        fk_values.extend(value)
                    else:
                        fk_values.append(value)
            
            if not fk_values:
                return None
            
            # Check how many of these values exist in target collection
            # Sample up to 20 values to check
            check_values = fk_values[:20]
            
            # Convert ObjectId strings if needed
            from bson import ObjectId
            check_values_converted = []
            for val in check_values:
                if isinstance(val, str) and len(val) == 24:
                    try:
                        check_values_converted.append(ObjectId(val))
                    except:
                        check_values_converted.append(val)
                else:
                    check_values_converted.append(val)
            
            matches = target_coll.count_documents({
                '_id': {'$in': check_values_converted}
            })
            
            confidence = matches / len(check_values) if check_values else 0
            
            # Only consider it a relationship if confidence > 0.8
            if confidence > 0.8:
                # Determine relationship type
                rel_type = 'many-to-many' if is_array else 'many-to-one'
                
                return {
                    'from': source_collection,
                    'to': target_collection,
                    'type': rel_type,
                    'field': field_name,
                    'description': f'{source_collection} references {target_collection} via {field_name}',
                    'confidence': round(confidence, 2)
                }
        
        except Exception as e:
            print(f"Error validating relationship: {e}")
            return None
    
    def _detect_correlation_fields(self, collections_data: Dict[str, Dict]) -> List[Dict]:
        """
        Detect shared correlation fields across collections
        
        Args:
            collections_data: Dictionary mapping collection names to their analysis
            
        Returns:
            List of correlation relationships
        """
        correlations = []
        
        # Find fields that appear in multiple collections
        field_to_collections = defaultdict(list)
        
        for collection_name, data in collections_data.items():
            fields = data.get('fields', {})
            for field_name, field_info in fields.items():
                # Skip _id field
                if field_name == '_id':
                    continue
                # Look for indexed string fields that might be correlation IDs
                if (field_info.get('type') == 'string' and 
                    field_info.get('indexed') and
                    ('tracking' in field_name.lower() or 
                     'correlation' in field_name.lower() or
                     field_name.endswith('_id'))):
                    field_to_collections[field_name].append(collection_name)
        
        # Check fields that appear in 2+ collections
        for field_name, collection_list in field_to_collections.items():
            if len(collection_list) >= 2:
                # Validate that values actually overlap
                overlap = self._validate_correlation_field(field_name, collection_list)
                
                if overlap and overlap['confidence'] > 0.5:
                    correlations.append({
                        'type': 'correlation',
                        'field': field_name,
                        'collections': collection_list,
                        'description': f'Collections linked via shared {field_name} field',
                        'confidence': overlap['confidence'],
                        'sample_overlap': overlap['sample_count']
                    })
        
        return correlations
    
    def _validate_correlation_field(self, field_name: str, collection_list: List[str]) -> Dict:
        """
        Validate that a field actually correlates data across collections
        
        Args:
            field_name: Name of the correlation field
            collection_list: List of collections containing this field
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Sample values from the first collection
            first_coll = self.db[collection_list[0]]
            sample_docs = list(first_coll.aggregate([
                {'$match': {field_name: {'$ne': None, '$exists': True}}},
                {'$limit': 20},
                {'$project': {field_name: 1}}
            ]))
            
            if not sample_docs:
                return None
            
            sample_values = [doc[field_name] for doc in sample_docs if field_name in doc]
            
            if not sample_values:
                return None
            
            # Check how many of these values appear in other collections
            total_matches = 0
            total_checks = 0
            
            for other_coll_name in collection_list[1:]:
                other_coll = self.db[other_coll_name]
                matches = other_coll.count_documents({
                    field_name: {'$in': sample_values}
                })
                total_matches += matches
                total_checks += len(sample_values)
            
            if total_checks == 0:
                return None
            
            confidence = total_matches / total_checks
            
            return {
                'confidence': round(confidence, 2),
                'sample_count': total_matches
            }
            
        except Exception as e:
            print(f"Error validating correlation field {field_name}: {e}")
            return None
    
    def _build_relationships_section(self, relationships: List[Dict]) -> Dict:
        """
        Build the relationships section for schemas.json
        
        Args:
            relationships: List of detected relationships
            
        Returns:
            Relationships section dictionary
        """
        # Separate foreign key and correlation relationships
        fk_relationships = [r for r in relationships if r.get('type') != 'correlation']
        correlation_relationships = [r for r in relationships if r.get('type') == 'correlation']
        
        # Generate example queries
        example_queries = []
        
        # Foreign key relationship examples
        for rel in fk_relationships[:2]:  # Limit to 2 FK examples
            from_coll = rel.get('from')
            to_coll = rel.get('to')
            field = rel.get('field')
            
            if from_coll and to_coll and field:
                # Simple find query
                example_queries.append(
                    f"Find {from_coll} by {to_coll}: db.{from_coll}.find({{{field}: '<id>'}})"
                )
                
                # Lookup aggregation
                example_queries.append(
                    f"Join {from_coll} with {to_coll}: db.{from_coll}.aggregate([{{$lookup: {{from: '{to_coll}', localField: '{field}', foreignField: '_id', as: '{to_coll}_data'}}}}])"
                )
        
        # Correlation field examples
        for rel in correlation_relationships[:2]:  # Limit to 2 correlation examples
            field = rel.get('field')
            collections = rel.get('collections', [])
            
            if field and len(collections) >= 2:
                # Example query showing how to correlate data
                example_queries.append(
                    f"Find related records via {field}: db.{collections[0]}.find({{{field}: '<value>'}})"
                )
                
                # Multi-collection aggregation example
                coll_list = ', '.join(collections)
                example_queries.append(
                    f"Correlate {coll_list} via {field}: Use {field} to link records across collections"
                )
        
        return {
            'description': f'Detected {len(relationships)} relationship(s) between collections',
            'foreign_keys': fk_relationships,
            'correlations': correlation_relationships,
            'links': relationships,  # Keep for backward compatibility
            'example_queries': example_queries
        }
    
    def generate_schemas(
        self, 
        collection_names: List[str], 
        sample_size: int = 100,
        detect_relationships: bool = True,
        merge_strategy: str = 'merge'
    ) -> Dict:
        """
        Generate schemas for multiple collections
        
        Args:
            collection_names: List of collection names to analyze
            sample_size: Number of documents to sample per collection
            detect_relationships: Whether to detect relationships
            merge_strategy: 'merge' or 'overwrite'
            
        Returns:
            Dictionary containing generated schemas and statistics
        """
        # Analyze each collection
        collections_data = {}
        
        for collection_name in collection_names:
            print(f"Analyzing collection: {collection_name}")
            analysis = self.analyze_collection(collection_name, sample_size)
            collections_data[collection_name] = analysis
        
        # Detect relationships if requested and multiple collections
        relationships = None
        if detect_relationships and len(collection_names) > 1:
            print("Detecting relationships between collections...")
            relationships = self.detect_relationships(collections_data)
        
        # Build schemas structure
        schemas = {}
        for collection_name, data in collections_data.items():
            schemas[collection_name] = {
                'description': data['description'],
                'fields': data['fields']
            }
        
        # Merge with existing schemas if requested
        if merge_strategy == 'merge':
            schemas = self._merge_with_existing_schemas(schemas)
        
        # Build final structure
        final_schema = {
            'description': f'Auto-generated schemas for {len(collection_names)} collection(s)',
            'collections': schemas
        }
        
        if relationships:
            final_schema['relationships'] = relationships
        
        # Save to file
        self._save_schemas(final_schema)
        
        # Return statistics
        total_fields = sum(len(s['fields']) for s in schemas.values())
        
        return {
            'success': True,
            'generated_schemas': schemas,
            'relationships': relationships,
            'stats': {
                'collections_analyzed': len(collection_names),
                'relationships_found': len(relationships.get('links', [])) if relationships else 0,
                'total_fields': total_fields
            }
        }
    
    def _merge_with_existing_schemas(self, new_schemas: Dict) -> Dict:
        """
        Merge new schemas with existing schemas.json
        
        Args:
            new_schemas: New schemas to merge
            
        Returns:
            Merged schemas
        """
        if not os.path.exists(self.schema_file_path):
            return new_schemas
        
        try:
            with open(self.schema_file_path, 'r') as f:
                existing = json.load(f)
                existing_collections = existing.get('collections', {})
                
                # Merge: new schemas take precedence but preserve manual edits
                for coll_name, new_schema in new_schemas.items():
                    if coll_name in existing_collections:
                        # Merge fields
                        existing_fields = existing_collections[coll_name].get('fields', {})
                        new_fields = new_schema.get('fields', {})
                        
                        # Keep existing fields, add new ones
                        merged_fields = {**new_fields, **existing_fields}
                        new_schema['fields'] = merged_fields
                
                # Combine all collections
                all_collections = {**existing_collections, **new_schemas}
                return all_collections
        
        except Exception as e:
            print(f"Error merging schemas: {e}")
            return new_schemas
    
    def _save_schemas(self, schemas: Dict):
        """
        Save schemas to file
        
        Args:
            schemas: Schemas dictionary to save
        """
        os.makedirs(os.path.dirname(self.schema_file_path), exist_ok=True)
        
        with open(self.schema_file_path, 'w') as f:
            json.dump(schemas, f, indent=4)
        
        print(f"✓ Schemas saved to {self.schema_file_path}")
