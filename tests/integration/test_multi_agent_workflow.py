"""
Integration tests for multi-agent workflow.

Tests the interaction between different agents and the overall
workflow execution, ensuring proper communication and data flow.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from multi_agents.agents.editor import EditorAgent
from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent
from tests.mocks.mock_llm import mock_llm, create_mock_call_model


class TestMultiAgentWorkflow:
    """Integration tests for multi-agent system."""

    @pytest.fixture
    def mock_task(self):
        """Mock task configuration for integration tests."""
        return {
            "query": "Integration test query",
            "model": "gpt-4",
            "verbose": False,
            "follow_guidelines": True,
            "guidelines": ["Be accurate", "Be comprehensive"],
            "max_sections": 2,
            "include_human_feedback": False
        }

    @pytest.fixture
    def editor_agent(self):
        """Create EditorAgent for integration testing."""
        return EditorAgent(
            websocket=Mock(),
            stream_output=AsyncMock(),
            headers={}
        )

    @pytest.fixture(autouse=True)
    def setup_mock_llm(self):
        """Setup mock LLM for all tests."""
        mock_llm.reset_history()
        yield
        mock_llm.reset_history()

    @pytest.mark.asyncio
    @patch('multi_agents.agents.editor.ResearchAgent')
    @patch('multi_agents.agents.editor.ReviewerAgent') 
    @patch('multi_agents.agents.editor.ReviserAgent')
    async def test_workflow_agent_initialization(
        self, mock_reviser, mock_reviewer, mock_researcher, editor_agent
    ):
        """Test that workflow properly initializes all agents."""
        # Mock the agent classes
        mock_researcher.return_value = Mock()
        mock_reviewer.return_value = Mock()
        mock_reviser.return_value = Mock()
        
        # Test agent initialization
        agents = editor_agent._initialize_agents()
        
        assert "research" in agents  # Note: key is 'research' not 'researcher'
        assert "reviewer" in agents
        assert "reviser" in agents

    @pytest.mark.asyncio
    @patch('multi_agents.agents.editor.call_model')
    async def test_research_planning_workflow(self, mock_call_model, editor_agent, mock_task):
        """Test the research planning workflow."""
        mock_plan = {
            "title": "Integration Test Research",
            "date": "2025-09-10",
            "sections": ["Introduction", "Analysis"]
        }
        mock_call_model.return_value = mock_plan
        
        research_state = {
            "task": mock_task,
            "initial_research": "Mock initial research data"
        }
        
        result = await editor_agent.plan_research(research_state)
        
        assert result["title"] == mock_plan["title"]
        assert result["sections"] == mock_plan["sections"]
        assert len(result["sections"]) <= mock_task["max_sections"]

    @pytest.mark.asyncio
    async def test_reviewer_workflow_integration(self):
        """Test reviewer integration in workflow context."""
        reviewer = ReviewerAgent()
        
        draft_state = {
            "task": {
                "model": "gpt-4",
                "verbose": False,
                "follow_guidelines": True,
                "guidelines": ["Be accurate"]
            },
            "draft": "Mock draft content for review"
        }
        
        with patch('multi_agents.agents.reviewer.call_model') as mock_call:
            # Return feedback string for review
            mock_call.return_value = "The draft needs improvement in accuracy section."
            result = await reviewer.run(draft_state)
            
            assert isinstance(result, dict)
            assert "review" in result
            # Mock should return feedback for review requests
            assert result["review"] is not None
            assert "improvement" in result["review"]

    @pytest.mark.asyncio
    async def test_workflow_decision_logic(self):
        """Test the workflow decision logic for accept/revise."""
        reviewer = ReviewerAgent()
        
        # Test accept decision
        accept_state = {
            "task": {
                "model": "gpt-4", 
                "verbose": False,
                "follow_guidelines": True,
                "guidelines": ["Be accurate"]
            },
            "draft": "This is a good enough draft that meets all guidelines"
        }
        
        with patch('multi_agents.agents.reviewer.call_model') as mock_call:
            mock_call.return_value = "None"  # Accept response
            result = await reviewer.run(accept_state)
            
            # Check workflow decision path
            assert result["review"] is None  # Should trigger "accept" path

    @pytest.mark.asyncio
    async def test_agent_communication_flow(self):
        """Test communication flow between agents."""
        # Reviewer processes the research result  
        reviewer = ReviewerAgent()
        draft_state = {
            "task": {"model": "gpt-4", "verbose": False, "follow_guidelines": True, "guidelines": []},
            "draft": "Research results draft content"
        }
        
        with patch('multi_agents.agents.reviewer.call_model') as mock_call:
            # Return "None" string which gets converted to None in review_draft
            mock_call.return_value = "None"
            review_result = await reviewer.run(draft_state)
            
            # Verify data flow
            assert review_result["review"] is None  # Accept decision