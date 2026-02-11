#!/usr/bin/env python3
"""
Test script to verify ChatOpenAI integration with custom base URL
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import Config

def test_chatopen_ai():
    """Test ChatOpenAI with custom base URL"""
    
    print("=" * 60)
    print("Testing ChatOpenAI with Custom Base URL")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
        print("\n✓ Configuration validated")
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        return
    
    # Display configuration
    print(f"\nBase URL: {Config.OPENAI_BASE_URL}")
    print(f"Model: {Config.OPENAI_MODEL}")
    print(f"API Key: {'*' * 20}")
    
    # Initialize ChatOpenAI
    try:
        client = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=100
        )
        print("\n✓ ChatOpenAI client initialized")
    except Exception as e:
        print(f"\n✗ Failed to initialize ChatOpenAI: {e}")
        return
    
    # Test with a simple query
    try:
        print("\n" + "=" * 60)
        print("Testing simple query...")
        print("=" * 60)
        
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Say 'Hello, ChatOpenAI is working!' in a friendly way.")
        ]
        
        print("\nSending request to AI...")
        response = client.invoke(messages)
        
        print("\n✓ Response received:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)
        
        print("\n✅ ChatOpenAI integration test PASSED!")
        
    except Exception as e:
        print(f"\n✗ Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatopen_ai()
