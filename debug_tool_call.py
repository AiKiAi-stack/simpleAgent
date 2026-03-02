#!/usr/bin/env python3
"""Debug script to check tool call format from vLLM."""

import sys
sys.path.insert(0, '.')

from agent_framework.llm_client import LLMClient
from agent_framework.tools.schemas import get_tool_schemas
from agent_framework.prompts import get_system_message
import json

def test_tool_call_format():
    """Test what format vLLM returns for tool calls."""
    
    client = LLMClient()
    tools = get_tool_schemas()
    system_message = get_system_message()
    
    # Simple test message that should trigger a tool call
    messages = [
        system_message,
        {"role": "user", "content": "List files in /tmp directory"}
    ]
    
    print("Sending request to vLLM...")
    print(f"Tools: {json.dumps(tools, indent=2)}")
    print()
    
    response = client.chat_completion(
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    print("Response received:")
    print(f"  Content: {response['content'][:200] if response['content'] else 'None'}")
    print(f"  Tool calls type: {type(response['tool_calls'])}")
    print(f"  Tool calls: {response['tool_calls']}")
    print()
    
    if response['tool_calls']:
        print(f"Number of tool calls: {len(response['tool_calls'])}")
        for idx, tc in enumerate(response['tool_calls']):
            print(f"\n  Tool call {idx + 1}:")
            print(f"    Type: {type(tc)}")
            print(f"    Dir: {[x for x in dir(tc) if not x.startswith('_')]}")
            print(f"    ID: {tc.id}")
            print(f"    Function: {tc.function}")
            print(f"    Function type: {type(tc.function)}")
            print(f"    Function dir: {[x for x in dir(tc.function) if not x.startswith('_')]}")
            print(f"    Function name: {tc.function.name}")
            print(f"    Function arguments: {tc.function.arguments}")
            print(f"    Arguments type: {type(tc.function.arguments)}")
            
            # Try to parse arguments
            try:
                args = json.loads(tc.function.arguments)
                print(f"    Parsed args: {args}")
            except Exception as e:
                print(f"    Failed to parse arguments: {e}")
    else:
        print("No tool calls in response!")
    
    return response

if __name__ == "__main__":
    try:
        test_tool_call_format()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
