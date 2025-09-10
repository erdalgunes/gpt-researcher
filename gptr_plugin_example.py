#!/usr/bin/env python3
"""
Example GPT Researcher Plugin
Demonstrates the plugin protocol for the microkernel
"""
import sys
import json
import os
from typing import Dict, Any

def main():
    """Plugin entry point - reads JSON from stdin, writes JSON to stdout"""
    
    # Read input from kernel
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        error = {"error": f"Failed to parse input: {e}"}
        print(json.dumps(error), file=sys.stderr)
        return 1
    
    # Extract command and args
    command = input_data.get('command')
    args = input_data.get('args', {})
    config = input_data.get('config', {})
    
    # Also read from environment variables
    llm_provider = os.getenv('GPTR_LLM_PROVIDER', config.get('llm_provider', 'openai'))
    data_source = os.getenv('GPTR_DATA_SOURCE', config.get('data_source', 'web'))
    
    # Example plugin logic
    result = {
        "status": "success",
        "command": command,
        "message": f"Plugin executed successfully",
        "config": {
            "llm_provider": llm_provider,
            "data_source": data_source,
        },
        "args": args
    }
    
    # Write output as JSON
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())