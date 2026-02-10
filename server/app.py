from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from pymongo import MongoClient
from query_generator import QueryGenerator
from schema_loader import SchemaLoader
from schema_generator import SchemaGenerator
from config import Config

app = Flask(__name__, static_folder='../ui', static_url_path='')
CORS(app)

# Validate configuration on startup
try:
    Config.validate()
    Config.display()
except ValueError as e:
    print(f"\n❌ Configuration Error: {e}\n")
    print("Please check your .env file and ensure all required values are set.")
    print("See .env.example for reference.\n")
    exit(1)

# MongoDB Configuration from Config class
MONGO_URI = Config.MONGO_URI
DB_NAME = Config.DB_NAME

# Initialize MongoDB client
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    print(f"✓ Connected to MongoDB: {DB_NAME}")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    db = None

# Initialize Schema Loader and Query Generator
schema_loader = SchemaLoader('./data/schemas')
query_generator = QueryGenerator(schema_loader)

def convert_dates_in_query(obj):
    """
    Recursively convert ISO date strings to datetime objects in queries
    This allows MongoDB to properly compare dates stored as ISODate objects
    """
    from dateutil import parser
    
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            if isinstance(value, str):
                # Try to parse as ISO date
                try:
                    # Check if it looks like an ISO date string
                    if 'T' in value and (value.count('-') >= 2 or value.count(':') >= 2):
                        new_obj[key] = parser.isoparse(value)
                    else:
                        new_obj[key] = value
                except (ValueError, parser.ParserError):
                    new_obj[key] = value
            elif isinstance(value, (dict, list)):
                new_obj[key] = convert_dates_in_query(value)
            else:
                new_obj[key] = value
        return new_obj
    elif isinstance(obj, list):
        return [convert_dates_in_query(item) for item in obj]
    else:
        return obj

def bson_to_json(obj):
    """
    Recursively convert BSON-specific types (ObjectId, datetime) to JSON-serializable formats.
    """
    from bson import ObjectId
    from datetime import datetime
    
    if isinstance(obj, dict):
        return {k: bson_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [bson_to_json(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

@app.route('/')
def index():
    """Serve the UI"""
    return send_from_directory('../ui', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    mongo_status = 'connected' if db is not None else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb': mongo_status,
        'schemas_loaded': len(schema_loader.get_all_schemas())
    })

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    """Get all available collection schemas"""
    schemas = schema_loader.get_all_schemas()
    return jsonify({
        'success': True,
        'schemas': schemas
    })

@app.route('/api/convert', methods=['POST'])
def convert_text_to_query():
    """
    Convert plain English text to MongoDB query
    Only schema structure is sent to AI, never actual data
    """
    try:
        data = request.json
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'No input text provided'
            }), 400
        
        # Generate MongoDB query using AI (only schemas are passed, not data)
        result = query_generator.generate_query(user_input)
        
        print(f"DEBUG: Converted '{user_input}' to:")
        print(f"  Collection: {result['collection']}")
        print(f"  Type: {result['query_type']}")
        print(f"  Query: {json.dumps(result['query'])}")
        
        return jsonify({
            'success': True,
            'query': result['query'],
            'collection': result['collection'],
            'query_type': result['query_type'],
            'explanation': result['explanation']
        })
    
    except Exception as e:
        print(f"✗ Query generation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute_query():
    """
    Execute MongoDB query and return results
    """
    try:
        if db is None:
            return jsonify({
                'success': False,
                'error': 'MongoDB not connected'
            }), 503
        
        data = request.json
        collection_name = data.get('collection')
        query = data.get('query')
        query_type = data.get('query_type', 'find')
        
        if not collection_name or query is None:
            return jsonify({
                'success': False,
                'error': 'Collection name and query are required'
            }), 400
        
        collection = db[collection_name]
        
        # Execute query based on type
        if query_type == 'find':
            # Handle find query
            filter_query = query.get('filter', {})
            projection = query.get('projection')
            sort = query.get('sort')
            limit = query.get('limit', 100)
            
            # No date conversion needed - dates are stored as ISO strings
            
            cursor = collection.find(filter_query, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            
            cursor = cursor.limit(limit)
            results = [bson_to_json(doc) for doc in cursor]
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results),
                'query_type': 'find'
            })
        
        elif query_type == 'aggregate':
            # Handle aggregation pipeline
            pipeline = query.get('pipeline', [])
            
            # No date conversion needed - dates are stored as ISO strings
            
            results = [bson_to_json(doc) for doc in list(collection.aggregate(pipeline))]
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results),
                'query_type': 'aggregate'
            })
        
        elif query_type == 'count':
            # Handle count query
            filter_query = query.get('filter', {})
            count = collection.count_documents(filter_query)
            
            return jsonify({
                'success': True,
                'count': count,
                'query_type': 'count'
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported query type: {query_type}'
            }), 400
    
    except Exception as e:
        print(f"✗ Query execution failed: {e}")
        print(f"  Collection: {collection_name if 'collection_name' in locals() else 'unknown'}")
        print(f"  Query: {json.dumps(query) if 'query' in locals() else 'unknown'}")
        return jsonify({
            'success': False,
            'error': str(e),
            'query': query if 'query' in locals() else None
        }), 500

@app.route('/api/collections', methods=['GET'])
def get_collections():
    """Get list of available collections"""
    try:
        if db is None:
            return jsonify({
                'success': False,
                'error': 'MongoDB not connected'
            }), 503
        
        collections = db.list_collection_names()
        
        return jsonify({
            'success': True,
            'collections': collections
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-schema', methods=['POST'])
def generate_schema():
    """
    Generate schemas from existing MongoDB collections
    with automatic relationship detection
    """
    try:
        if db is None:
            return jsonify({
                'success': False,
                'error': 'MongoDB not connected'
            }), 503
        
        data = request.json
        collection_names = data.get('collections', [])
        sample_size = data.get('sample_size', 100)
        detect_relationships = data.get('detect_relationships', True)
        merge_strategy = data.get('merge_strategy', 'merge')
        
        if not collection_names:
            return jsonify({
                'success': False,
                'error': 'No collections specified'
            }), 400
        
        # Validate that collections exist
        existing_collections = db.list_collection_names()
        invalid_collections = [c for c in collection_names if c not in existing_collections]
        
        if invalid_collections:
            return jsonify({
                'success': False,
                'error': f'Collections not found: {", ".join(invalid_collections)}',
                'available_collections': existing_collections
            }), 400
        
        # Initialize schema generator
        schema_file_path = os.path.join('./data/schemas', 'schemas.json')
        generator = SchemaGenerator(db, schema_file_path)
        
        # Generate schemas
        print(f"Generating schemas for {len(collection_names)} collection(s)...")
        result = generator.generate_schemas(
            collection_names,
            sample_size=sample_size,
            detect_relationships=detect_relationships,
            merge_strategy=merge_strategy
        )
        
        # Reload schema loader to pick up new schemas
        schema_loader.reload_schemas()
        
        print(f"✓ Schema generation complete!")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"✗ Schema generation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Text-to-MongoDB Query Server")
    print("=" * 60)
    print(f"Database: {DB_NAME}")
    print(f"Schemas loaded: {len(schema_loader.get_all_schemas())}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
