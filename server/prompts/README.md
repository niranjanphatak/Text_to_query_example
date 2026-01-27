# Prompts Directory

This directory contains prompt templates used by the AI query generator.

## Files

### `system_prompt.txt`
The system prompt that defines the AI's role and behavior as a MongoDB query expert.

**Key Instructions:**
- Query generation rules
- Date handling guidelines
- Response format requirements
- Field type conversion logic

**When to modify:**
- Adding new query types
- Changing date handling behavior
- Updating response format
- Adding new MongoDB operators support

### `user_prompt_template.txt`
Template for the user-facing prompt that includes schema context and user input.

**Placeholders:**
- `{schema_context}`: Replaced with actual collection schemas
- `{current_time}`: Current timestamp
- `{seven_days_ago}`: Date 7 days ago
- `{ten_days_ago}`: Date 10 days ago
- `{thirty_days_ago}`: Date 30 days ago
- `{user_input}`: User's natural language query

**When to modify:**
- Adding new date references
- Changing prompt structure
- Adding additional context

## Usage

The `QueryGenerator` class in `query_generator.py` automatically loads these templates:

```python
# Loads system_prompt.txt
with open('prompts/system_prompt.txt', 'r') as f:
    system_prompt = f.read()

# Loads and formats user_prompt_template.txt
with open('prompts/user_prompt_template.txt', 'r') as f:
    template = f.read()
    
user_prompt = template.format(
    schema_context=schemas,
    current_time=datetime.now().isoformat(),
    # ... other placeholders
)
```

## Best Practices

1. **Keep prompts focused**: Each file should have a single, clear purpose
2. **Use placeholders**: Make templates reusable with `{placeholder}` syntax
3. **Document changes**: Update this README when modifying prompts
4. **Test thoroughly**: Changes to prompts affect all query generation
5. **Version control**: Track prompt changes to understand AI behavior evolution

## Fallback Behavior

If prompt files are not found, the system falls back to minimal inline prompts to ensure the application continues to function.
