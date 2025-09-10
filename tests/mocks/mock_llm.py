"""
Mock implementations for LLM dependencies.

Provides consistent, controllable responses for testing without 
making actual API calls to external services.
"""
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self, default_response: str = "Mock LLM response"):
        self.default_response = default_response
        self.call_history: List[Dict[str, Any]] = []
        
    async def call_model(
        self, 
        prompt: List[Dict[str, str]], 
        model: str = "gpt-4",
        response_format: Optional[str] = None,
        **kwargs
    ) -> str:
        """Mock call_model function."""
        call_info = {
            "prompt": prompt,
            "model": model, 
            "response_format": response_format,
            "kwargs": kwargs
        }
        self.call_history.append(call_info)
        
        # Return specific responses based on prompt content
        if isinstance(prompt, list) and len(prompt) > 1:
            user_content = prompt[1].get("content", "").lower()
            
            # Review-specific responses
            if "review" in user_content and "accept" in user_content:
                if "good enough" in user_content or "meets all" in user_content:
                    return "None"
                else:
                    return "Please improve the methodology section"
                    
            # Research-specific responses  
            if "research" in user_content:
                return "Research findings: Mock data about the topic"
                
            # Revision-specific responses
            if "revise" in user_content:
                return "Revised content with improvements"
                
        return self.default_response
    
    def get_call_count(self) -> int:
        """Get number of calls made to mock LLM."""
        return len(self.call_history)
        
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get details of the last call made."""
        return self.call_history[-1] if self.call_history else None
        
    def reset_history(self):
        """Clear call history."""
        self.call_history.clear()


# Global mock instance for easy use in tests
mock_llm = MockLLMProvider()


def create_mock_call_model():
    """Create a mock call_model function."""
    return AsyncMock(side_effect=mock_llm.call_model)