from __future__ import annotations

import asyncio

from pydantic_ai import Agent

from obox_mcp.python import (
    configure_python_environment_func,
    get_env_info_func,
    get_list_python_packages_installed_func,
    install_python_package_func,
    list_available_python_environments_func,
)

# Define the Agent
python_manager_agent = Agent(
    'openai:gpt-4o',
    system_prompt=(
        "You are an expert Python environment manager. "
        "Your task is to help the user manage their Python environment using uv. "
        "You can check environment info, install packages, and configure python versions. "
        "Always check the current environment before making changes."
    ),
)


@python_manager_agent.tool_plain
async def tool_list_available_python_environments() -> str:
    """Lists available Python versions."""
    return await list_available_python_environments_func()


@python_manager_agent.tool_plain
async def tool_configure_python_environment(version: str) -> str:
    """Configures the Python environment to a specific version."""
    return await configure_python_environment_func(version)


@python_manager_agent.tool_plain
async def tool_get_env_info() -> str:
    """Gets information about the current environment."""
    return await get_env_info_func()


@python_manager_agent.tool_plain
async def tool_install_package(package_name: str) -> str:
    """Installs a Python package."""
    return await install_python_package_func(package_name)


@python_manager_agent.tool_plain
async def tool_list_packages() -> str:
    """Lists installed packages."""
    return await get_list_python_packages_installed_func()


async def example_run():
    print("Running agent example...")
    # result = await python_manager_agent.run("What is my current python version?")
    # print(result.data)
    print("Agent initialized with async tools.")


if __name__ == "__main__":
    asyncio.run(example_run())
