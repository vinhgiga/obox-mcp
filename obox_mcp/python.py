from __future__ import annotations

import asyncio
import contextlib
import os

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxPython",
    instructions=(
        "A tool to manage Python environments and packages using uv in an "
        "asynchronous way. It supports configuring environments, installing "
        "packages, and querying environment state."
    ),
)


class EnvInfo(BaseModel):
    python_version: str
    venv_path: str | None
    installed_python_versions: list[str]
    project_name: str | None


async def run_uv_async(args: list[str]) -> str:
    """Helper to run uv commands asynchronously and return output."""
    return await utils.run_command_output(
        ["uv", *args], error_prefix="Error executing uv"
    )


async def list_available_python_environments_func() -> str:
    """
    Lists all available Python versions using 'uv python list'.
    Shows installed versions and versions available for download.
    """
    return await run_uv_async(["python", "list"])


@mcp.tool(name="list_available_python_environments")
async def list_available_python_environments() -> str:
    """
    Lists all available Python versions using 'uv python list'.
    Shows installed versions and versions available for download.
    """
    return await list_available_python_environments_func()


async def configure_python_environment_func(version: str) -> str:
    """
    Configures the project's Python environment to a specific version
    using 'uv venv --python'. Example versions: '3.11', '3.12', '3.10.12'.
    """
    return await run_uv_async(["venv", "--python", version])


@mcp.tool(name="configure_python_environment")
async def configure_python_environment(version: str) -> str:
    """
    Configures the project's Python environment to a specific version
    using 'uv venv --python'. Example versions: '3.11', '3.12', '3.10.12'.
    """
    return await configure_python_environment_func(version)


def self_read_pyproject():
    """Helper to read project name from pyproject.toml."""
    try:
        with open("pyproject.toml") as f:
            for line in f:
                if line.startswith("name ="):
                    return line.split("=")[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


async def get_env_info_func() -> str:
    """
    Retrieves detailed information about the current Python environment and uv
    configuration.
    Returns a JSON string with python version, venv path, and available python versions.
    """
    try:
        py_ver_task = run_uv_async(["python", "--version"])
        py_list_task = run_uv_async(["python", "list"])

        py_ver, py_list_raw = await asyncio.gather(py_ver_task, py_list_task)

        venv_path = None
        with contextlib.suppress(Exception):
            venv_path = await run_uv_async(["venv", "--show"])

        py_list = [line.strip() for line in py_list_raw.split("\n") if line.strip()]

        project_name = None
        if os.path.exists("pyproject.toml"):
            # Using async file read for consistency
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, self_read_pyproject)
            if content:
                project_name = content

        info = EnvInfo(
            python_version=py_ver,
            venv_path=venv_path,
            installed_python_versions=py_list,
            project_name=project_name,
        )
        return info.model_dump_json(indent=2)
    except Exception as e:
        return f"Error gathering environment info: {e!s}"


@mcp.tool(name="get_env_info")
async def get_env_info() -> str:
    """
    Retrieves detailed information about the current Python environment and uv
    configuration.
    Returns a JSON string with python version, venv path, and available python versions.
    """
    return await get_env_info_func()


async def install_python_package_func(package_name: str) -> str:
    """
    Installs a specified Python package to the current project using 'uv add'.
    This will update the pyproject.toml and lockfile.
    Example: 'requests', 'pandas==2.1.0'
    """
    return await run_uv_async(["add", package_name])


@mcp.tool(name="install_python_package")
async def install_python_package(package_name: str) -> str:
    """
    Installs a specified Python package to the current project using 'uv add'.
    This will update the pyproject.toml and lockfile.
    Example: 'requests', 'pandas==2.1.0'
    """
    return await install_python_package_func(package_name)


async def get_list_python_packages_installed_func() -> str:
    """
    Returns a list of all installed Python packages in the current environment
    using 'uv pip list'.
    """
    return await run_uv_async(["pip", "list"])


@mcp.tool(name="get_list_python_packages_installed")
async def get_list_python_packages_installed() -> str:
    """
    Returns a list of all installed Python packages in the current environment
    using 'uv pip list'.
    """
    return await get_list_python_packages_installed_func()


async def uv_sync_func() -> str:
    """
    Synchronizes the project's environment with the lockfile ('uv sync').
    Ensures all dependencies in pyproject.toml are installed.
    """
    return await run_uv_async(["sync"])


@mcp.tool(name="uv_sync")
async def uv_sync() -> str:
    """
    Synchronizes the project's environment with the lockfile ('uv sync').
    Ensures all dependencies in pyproject.toml are installed.
    """
    return await uv_sync_func()


# Optional: FastAPI integration
app = FastAPI(title="OboxPython MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount MCP HTTP app
app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxPython MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
