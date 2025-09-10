#!/usr/bin/env python3
"""
GPT-5 Model Support Patch
Handles temperature and other parameter restrictions for GPT-5 models
"""
import os
import sys

def patch_for_gpt5():
    """Patch environment and configuration for GPT-5 models"""
    
    # Check if using GPT-5 models
    llm_provider = os.getenv('GPTR_LLM_PROVIDER', 'openai')
    llm_model = os.getenv('GPTR_LLM_MODEL', '')
    
    if llm_provider == 'gpt5' or 'gpt-5' in llm_model.lower() or 'gpt5' in llm_model.lower():
        print(f"[GPT-5 Patch] Detected GPT-5 model: {llm_model}", file=sys.stderr)
        
        # GPT-5 doesn't support custom temperature, must use default (1.0)
        # Set environment variable to override temperature
        os.environ['TEMPERATURE'] = '1.0'
        os.environ['GPTR_TEMPERATURE'] = '1.0'
        
        # GPT-5 specific settings
        os.environ['GPTR_NO_CUSTOM_TEMPERATURE'] = 'true'
        
        # Use OpenAI provider with GPT-5 model name
        if llm_provider == 'gpt5':
            os.environ['OPENAI_API_MODEL'] = llm_model or 'gpt-5'
            os.environ['SMART_LLM_MODEL'] = llm_model or 'gpt-5'
            os.environ['FAST_LLM_MODEL'] = 'gpt-5-mini'
            os.environ['SUMMARY_LLM_MODEL'] = 'gpt-5-nano'
        
        print(f"[GPT-5 Patch] Applied settings: temperature=1.0 (default), model={os.getenv('OPENAI_API_MODEL')}", file=sys.stderr)
        return True
    
    return False


def monkey_patch_temperature():
    """Monkey patch the create_chat_completion to remove temperature for GPT-5"""
    try:
        from gpt_researcher.utils import llm
        
        original_create = llm.create_chat_completion if hasattr(llm, 'create_chat_completion') else None
        
        if original_create:
            async def patched_create_chat_completion(
                messages,
                model=None,
                temperature=None,
                max_tokens=None,
                llm_provider=None,
                stream=False,
                websocket=None,
                max_retries=3,
                **kwargs
            ):
                # Check if using GPT-5
                model_name = model or os.getenv('OPENAI_API_MODEL', '')
                if 'gpt-5' in model_name.lower() or 'gpt5' in model_name.lower():
                    # Remove temperature for GPT-5 models
                    temperature = None
                    kwargs.pop('temperature', None)
                    print(f"[GPT-5 Patch] Removed temperature parameter for {model_name}", file=sys.stderr)
                
                # Call original function
                return await original_create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    llm_provider=llm_provider,
                    stream=stream,
                    websocket=websocket,
                    max_retries=max_retries,
                    **kwargs
                )
            
            # Replace the function
            llm.create_chat_completion = patched_create_chat_completion
            print("[GPT-5 Patch] Successfully monkey-patched create_chat_completion", file=sys.stderr)
    except Exception as e:
        print(f"[GPT-5 Patch] Warning: Could not monkey patch: {e}", file=sys.stderr)


if __name__ == '__main__':
    # Apply patches
    patch_for_gpt5()
    monkey_patch_temperature()
    print("[GPT-5 Patch] Patches applied successfully")