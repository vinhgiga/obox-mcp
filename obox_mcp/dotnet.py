from __future__ import annotations

import asyncio
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "OboxDotNet",
    instructions=(
        "A tool to manage .NET solutions, projects, and packages using the dotnet CLI. "
        "It supports creating solutions/projects, adding/removing references, "
        "managing NuGet packages, and building/running/testing applications."
    ),
)


async def run_dotnet_async(args: List[str]) -> str:
    """Helper to run dotnet commands asynchronously and return output."""
    try:
        process = await asyncio.create_subprocess_exec(
            "dotnet",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip() or stdout.decode().strip()
            return f"Error executing dotnet {' '.join(args)}: {error_msg}"

        return stdout.decode().strip()
    except FileNotFoundError:
        return "Error: 'dotnet' command not found. Please ensure .NET SDK is installed."
    except Exception as e:
        return f"Error executing dotnet {' '.join(args)}: {e!s}"


# --- Solution Management ---


@mcp.tool(name="new_sln")
async def new_sln(name: str, output_dir: str = ".") -> str:
    """
    Creates a new empty solution file.
    Example: name='MySolution', output_dir='./src'
    """
    args = ["new", "sln", "-n", name, "-o", output_dir]
    return await run_dotnet_async(args)


@mcp.tool(name="list_sln_projects")
async def list_sln_projects(sln_file: Optional[str] = None) -> str:
    """
    Lists all projects within a solution.
    If sln_file is not provided, it looks for one in the current directory.
    """
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.append("list")
    return await run_dotnet_async(args)


@mcp.tool(name="add_project_to_sln")
async def add_project_to_sln(project_path: str, sln_file: Optional[str] = None) -> str:
    """
    Adds an existing project to a solution.
    """
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.extend(["add", project_path])
    return await run_dotnet_async(args)


@mcp.tool(name="remove_project_from_sln")
async def remove_project_from_sln(
    project_path: str, sln_file: Optional[str] = None
) -> str:
    """
    Removes a project from a solution.
    """
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.extend(["remove", project_path])
    return await run_dotnet_async(args)


# --- Project Management ---


@mcp.tool(name="new_project")
async def new_project(template: str, name: str, output_dir: str = ".") -> str:
    """
    Creates a new project based on a template (e.g., 'console', 'classlib', 'webapp').
    """
    args = ["new", template, "-n", name, "-o", output_dir]
    return await run_dotnet_async(args)


@mcp.tool(name="list_project_templates")
async def list_project_templates() -> str:
    """
    Lists all available project templates.
    """
    return await run_dotnet_async(["new", "--list"])


@mcp.tool(name="add_project_reference")
async def add_project_reference(project_file: str, reference_project: str) -> str:
    """
    Adds a project-to-project reference.
    """
    return await run_dotnet_async(["add", project_file, "reference", reference_project])


@mcp.tool(name="remove_project_reference")
async def remove_project_reference(project_file: str, reference_project: str) -> str:
    """
    Removes a project-to-project reference.
    """
    return await run_dotnet_async(
        ["remove", project_file, "reference", reference_project]
    )


@mcp.tool(name="list_project_references")
async def list_project_references(project_file: str) -> str:
    """
    Lists all project-to-project references for a project.
    """
    return await run_dotnet_async(["list", project_file, "reference"])


# --- Package Management ---


@mcp.tool(name="add_package")
async def add_package(
    project_file: str, package_name: str, version: Optional[str] = None
) -> str:
    """
    Adds a NuGet package to a project.
    Example: project_file='App.csproj', package_name='Newtonsoft.Json', version='13.0.1'
    """
    args = ["add", project_file, "package", package_name]
    if version:
        args.extend(["--version", version])
    return await run_dotnet_async(args)


@mcp.tool(name="remove_package")
async def remove_package(project_file: str, package_name: str) -> str:
    """
    Removes a NuGet package from a project.
    """
    return await run_dotnet_async(["remove", project_file, "package", package_name])


@mcp.tool(name="list_packages")
async def list_packages(project_file: str) -> str:
    """
    Lists all NuGet packages references for a project.
    """
    return await run_dotnet_async(["list", project_file, "package"])


# --- Build and Execution ---


@mcp.tool(name="build")
async def build(target: Optional[str] = None, configuration: str = "Debug") -> str:
    """
    Builds a project or solution.
    'target' can be a path to a .csproj or .sln file, or omitted for current directory.
    """
    args = ["build"]
    if target:
        args.append(target)
    args.extend(["-c", configuration])
    return await run_dotnet_async(args)


@mcp.tool(name="run_project")
async def run_project(project_file: Optional[str] = None) -> str:
    """
    Runs the project in the current folder or a specified project file.
    Note: This is an interactive/long-running command in a real terminal,
    but here it returns when the process exits.
    """
    args = ["run"]
    if project_file:
        args.extend(["--project", project_file])
    return await run_dotnet_async(args)


@mcp.tool(name="test")
async def test(target: Optional[str] = None) -> str:
    """
    Executes tests in a project or solution.
    """
    args = ["test"]
    if target:
        args.append(target)
    return await run_dotnet_async(args)


@mcp.tool(name="clean")
async def clean(target: Optional[str] = None) -> str:
    """
    Cleans the output of a project or solution.
    """
    args = ["clean"]
    if target:
        args.append(target)
    return await run_dotnet_async(args)


@mcp.tool(name="publish")
async def publish(
    target: Optional[str] = None,
    configuration: str = "Release",
    output_dir: Optional[str] = None,
) -> str:
    """
    Publishes the application for deployment.
    """
    args = ["publish"]
    if target:
        args.append(target)
    args.extend(["-c", configuration])
    if output_dir:
        args.extend(["-o", output_dir])
    return await run_dotnet_async(args)


# --- Info ---


@mcp.tool(name="get_dotnet_info")
async def get_dotnet_info() -> str:
    """
    Displays detailed information about the .NET SDKs and runtimes installed.
    """
    return await run_dotnet_async(["--info"])


# --- FastAPI integration ---

app = FastAPI(title="OboxDotNet MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
        print(f"Starting OboxDotNet MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
