"""
Unit tests for ReviewerAgent.

Tests the core functionality of the ReviewerAgent including:
- Draft review process
- Guidelines compliance checking  
- Review decision making
- Integration with workflow
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from multi_agents.agents.reviewer import ReviewerAgent


class TestReviewerAgent:
    """Test suite for ReviewerAgent functionality."""

    @pytest.fixture
    def agent(self):
        """Create ReviewerAgent instance for testing."""
        return ReviewerAgent(
            websocket=Mock(),
            stream_output=AsyncMock(),
            headers={}
        )

    @pytest.fixture
    def mock_task(self):
        """Mock task configuration."""
        return {
            "model": "gpt-4",
            "verbose": True,
            "follow_guidelines": True,
            "guidelines": ["Be comprehensive", "Use reliable sources"]
        }

    @pytest.fixture
    def draft_state(self, mock_task):
        """Mock draft state for testing."""
        return {
            "task": mock_task,
            "draft": "Test draft content"
        }

    @pytest.mark.asyncio
    async def test_run_method_exists_and_callable(self, agent):
        """Test that run method exists and is callable."""
        assert hasattr(agent, 'run')
        assert callable(getattr(agent, 'run'))

    @pytest.mark.asyncio
    @patch('multi_agents.agents.reviewer.call_model')
    async def test_run_with_guidelines_enabled(self, mock_call_model, agent, draft_state):
        """Test run method with guidelines enabled."""
        mock_call_model.return_value = "Some review feedback"
        
        result = await agent.run(draft_state)
        
        assert isinstance(result, dict)
        assert "review" in result
        assert result["review"] == "Some review feedback"
        mock_call_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_guidelines_disabled(self, agent, draft_state):
        """Test run method with guidelines disabled."""
        draft_state["task"]["follow_guidelines"] = False
        
        result = await agent.run(draft_state)
        
        assert isinstance(result, dict)
        assert "review" in result
        assert result["review"] is None

    @pytest.mark.asyncio
    @patch('multi_agents.agents.reviewer.call_model')
    async def test_review_draft_accept(self, mock_call_model, agent, draft_state):
        """Test review_draft accepting a draft."""
        mock_call_model.return_value = "None - the draft is acceptable"
        
        result = await agent.review_draft(draft_state)
        
        assert result is None

    @pytest.mark.asyncio
    @patch('multi_agents.agents.reviewer.call_model')
    async def test_review_draft_request_revision(self, mock_call_model, agent, draft_state):
        """Test review_draft requesting revision."""
        expected_feedback = "Please improve the conclusion section"
        mock_call_model.return_value = expected_feedback
        
        result = await agent.review_draft(draft_state)
        
        assert result == expected_feedback

    @pytest.mark.asyncio
    @patch('multi_agents.agents.reviewer.call_model')
    async def test_review_with_previous_revision_notes(self, mock_call_model, agent, draft_state):
        """Test review process with previous revision notes."""
        draft_state["revision_notes"] = "Previous feedback was addressed"
        mock_call_model.return_value = "Additional minor changes needed"
        
        result = await agent.review_draft(draft_state)
        
        assert result == "Additional minor changes needed"
        # Verify the prompt includes revision context
        call_args = mock_call_model.call_args[0]
        prompt_content = call_args[0][1]["content"]
        assert "Previous feedback was addressed" in prompt_content

    @pytest.mark.asyncio
    @patch('multi_agents.agents.reviewer.call_model')
    async def test_verbose_logging(self, mock_call_model, agent, draft_state):
        """Test verbose logging functionality."""
        mock_call_model.return_value = "Review feedback"
        
        await agent.run(draft_state)
        
        # Verify stream_output was called for logging
        agent.stream_output.assert_called()