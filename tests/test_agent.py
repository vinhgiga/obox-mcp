import pytest
from pydantic_ai import (
    ModelResponse,
    TextPart,
    ToolCallPart,
    capture_run_messages,
    models,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from agent import python_manager_agent

# Use anyio as the default for testing
pytestmark = pytest.mark.anyio

# Safety measure to prevent making actual LLM calls
models.ALLOW_MODEL_REQUESTS = False


async def test_agent_initialization():
    """Test that the agent is initialized and can be overridden with TestModel."""
    with python_manager_agent.override(model=TestModel()):
        result = await python_manager_agent.run("What is my current python version?")
        # TestModel returns a JSON string describing what tool was called
        # or a generic response
        assert result.output is not None


async def test_agent_tool_calls():
    """Test that the agent calls the correct tools based on the prompt."""
    with python_manager_agent.override(model=TestModel()):
        # TestModel will attempt to call tools that match the request
        result = await python_manager_agent.run("List available python environments")

        # By default TestModel output is a representation of the tool calls it made
        assert "tool_list_available_python_environments" in result.output


async def test_agent_with_function_model():
    """Test the agent's decision logic using FunctionModel."""

    def mock_model(messages, _info):
        # If it's the first message, return a tool call
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("tool_get_env_info", {})])
        # Otherwise return a text response
        return ModelResponse(parts=[TextPart("Your environment is healthy.")])

    with python_manager_agent.override(model=FunctionModel(mock_model)):
        result = await python_manager_agent.run("Check my environment")
        assert "healthy" in result.output


async def test_agent_messages_capture():
    """Test that we can capture and inspect the messages exchange."""
    with capture_run_messages() as messages, python_manager_agent.override(
        model=TestModel()
    ):
        await python_manager_agent.run("Install requests")

    # Assert that at least one request and one response were exchanged
    assert len(messages) >= 2
    # Check that tool_install_package was called
    tool_calls = [
        p
        for m in messages
        if isinstance(m, ModelResponse)
        for p in m.parts
        if isinstance(p, ToolCallPart)
    ]
    assert any(tc.tool_name == "tool_install_package" for tc in tool_calls)
