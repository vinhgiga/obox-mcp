import os
import sys

import pytest

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import load_mcp_modules, mcp

# Use anyio for async tests
pytestmark = pytest.mark.anyio


async def test_all_tools_have_descriptions():
    """
    Test that all tools mounted in the main MCP server have a description.
    This ensures that LLMs have enough context to know when to use each tool.
    """
    # Load all modules to populate the tools list
    load_mcp_modules(["obox_mcp", "project_templates"])

    # get_tools returns a dictionary mapping tool names to tool objects
    tools = await mcp.get_tools()

    missing_descriptions = []

    for tool_name, tool in tools.items():
        # FastMCP tools have a description attribute
        # We check if it's None, empty, or just whitespace
        if (
            not hasattr(tool, "description")
            or not tool.description
            or not tool.description.strip()
        ):
            missing_descriptions.append(tool_name)

    assert not missing_descriptions, (
        f"The following tools are missing descriptions: {', '.join(missing_descriptions)}"
    )


if __name__ == "__main__":
    import asyncio

    async def main():
        # If run directly, just run the test logic
        load_mcp_modules(["obox_mcp", "project_templates"])
        tools = await mcp.get_tools()
        for tool_name, tool in tools.items():
            desc = getattr(tool, "description", "NO DESCRIPTION ATTRIBUTE")
            print(f"Tool: {tool_name}")
            print(f"Description: {desc}")
            print("-" * 20)

    asyncio.run(main())
