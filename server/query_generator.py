import os
import json
from typing import Dict, Any
from openai import OpenAI
from schema_loader import SchemaLoader
from config import Config

class QueryGenerator:
    """
    Generates MongoDB queries from plain English using AI
    IMPORTANT: Only schema structures are passed to AI, never actual data
    """
    
    def __init__(self, schema_loader: SchemaLoader):
        self.schema_loader = schema_loader
        
        # All configuration comes from Config class (loaded from .env, no defaults)
        api_key = Config.OPENAI_API_KEY
        base_url = Config.OPENAI_BASE_URL
        self.model_name = Config.OPENAI_MODEL
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        print(f"✓ Query Generator initialized with OpenAI")
        print(f"  - Base URL: {base_url}")
        print(f"  - Model: {self.model_name}")
    
    def generate_query(self, user_input: str) -> Dict[str, Any]:
        """
        Generate MongoDB query from plain English input
        Only schema structures are sent to AI
        """
        
        # Get schema context (structure only, no data)
        schema_context = self.schema_loader.get_all_schemas_summary()
        
        # Create prompt for AI
        system_prompt, user_prompt = self._create_prompt(user_input, schema_context)
        
        # Generate query using AI
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = self._parse_ai_response(response.choices[0].message.content)
            return result
        except Exception as e:
            raise Exception(f"AI query generation failed: {str(e)}")
    
    def _create_prompt(self, user_input: str, schema_context: str) -> tuple[str, str]:
        """
        Create prompt for AI model
        IMPORTANT: Only schema structures are included, never actual data
        Returns: (system_prompt, user_prompt)
        """
        
        # Load system prompt from file
        prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        system_prompt_path = os.path.join(prompts_dir, 'system_prompt.txt')
        user_prompt_template_path = os.path.join(prompts_dir, 'user_prompt_template.txt')
        
        try:
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            print(f"Warning: System prompt file not found at {system_prompt_path}")
            # Fallback to inline prompt
            system_prompt = """You are a MongoDB query expert. Convert the user's plain English request into a valid MongoDB query.
Return ONLY valid JSON in the specified format."""
        
        try:
            with open(user_prompt_template_path, 'r') as f:
                user_prompt_template = f.read()
        except FileNotFoundError:
            print(f"Warning: User prompt template not found at {user_prompt_template_path}")
            user_prompt_template = """AVAILABLE SCHEMAS:
{schema_context}

USER REQUEST:
{user_input}

Generate the MongoDB query now:"""
        
        # Calculate date references for time-based queries
        from datetime import datetime, timedelta
        current_date = datetime.now()
        
        # Format user prompt with actual values
        user_prompt = user_prompt_template.format(
            schema_context=schema_context,
            current_time=current_date.isoformat(),
            seven_days_ago=(current_date - timedelta(days=7)).isoformat(),
            ten_days_ago=(current_date - timedelta(days=10)).isoformat(),
            thirty_days_ago=(current_date - timedelta(days=30)).isoformat(),
            user_input=user_input
        )
        
        return system_prompt, user_prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract query information"""
        
        # Clean up response text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            # Check for ```json ... ``` or just ``` ... ```
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Fallback: remove lines starting with ```
                lines = response_text.split('\n')
                response_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
        
        # Find the first '{' and last '}' if we haven't already extracted clean JSON
        if not (response_text.startswith('{') and response_text.endswith('}')):
            start_index = response_text.find('{')
            end_index = response_text.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                response_text = response_text[start_index:end_index+1]
        
        try:
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['collection', 'query_type', 'query', 'explanation']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate collection exists
            if result['collection'] not in self.schema_loader.get_collection_names():
                raise ValueError(f"Invalid collection: {result['collection']}")
            
            # Validate query type
            valid_types = ['find', 'aggregate', 'count']
            if result['query_type'] not in valid_types:
                raise ValueError(f"Invalid query type: {result['query_type']}")
            
            return result
        
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise Exception(f"Invalid AI response: {str(e)}")
