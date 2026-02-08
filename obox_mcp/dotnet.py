from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxDotNet",
    instructions="Manage .NET projects, solutions, and packages via dotnet CLI.",
)


async def run_dotnet_async(args: list[str]) -> str:
    """Helper to run dotnet commands asynchronously and return output."""
    return await utils.run_command_output(
        ["dotnet", *args], error_prefix="Error executing dotnet"
    )


# --- Solution Management ---


@mcp.tool(name="new_sln")
async def new_sln(name: str, output_dir: str = ".") -> str:
    """Creates a new empty solution file."""
    args = ["new", "sln", "-n", name, "-o", output_dir]
    return await run_dotnet_async(args)


@mcp.tool(name="list_sln_projects")
async def list_sln_projects(sln_file: str | None = None) -> str:
    """Lists all projects within a solution."""
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.append("list")
    return await run_dotnet_async(args)


@mcp.tool(name="add_project_to_sln")
async def add_project_to_sln(project_path: str, sln_file: str | None = None) -> str:
    """Adds an existing project to a solution."""
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.extend(["add", project_path])
    return await run_dotnet_async(args)


@mcp.tool(name="remove_project_from_sln")
async def remove_project_from_sln(
    project_path: str, sln_file: str | None = None
) -> str:
    """Removes a project from a solution."""
    args = ["sln"]
    if sln_file:
        args.append(sln_file)
    args.extend(["remove", project_path])
    return await run_dotnet_async(args)


# --- Project Management ---


@mcp.tool(name="new_project")
async def new_project(template: str, name: str, output_dir: str = ".") -> str:
    """Creates a new project from a template."""
    args = ["new", template, "-n", name, "-o", output_dir]
    result = await run_dotnet_async(args)
    if "successfully" in result.lower():
        return (
            f"{result}\n\n"
            "🚀 **Next Step**: Call the `project_runner` tool to finalize the setup "
            "and generate a `justfile` for running the project."
        )
    return result


@mcp.tool(name="list_project_templates")
async def list_project_templates() -> str:
    """Lists all available project templates."""
    return await run_dotnet_async(["new", "--list"])


@mcp.tool(name="add_project_reference")
async def add_project_reference(project_file: str, reference_project: str) -> str:
    """Adds a project-to-project reference."""
    return await run_dotnet_async(["add", project_file, "reference", reference_project])


@mcp.tool(name="remove_project_reference")
async def remove_project_reference(project_file: str, reference_project: str) -> str:
    """Removes a project-to-project reference."""
    return await run_dotnet_async(
        ["remove", project_file, "reference", reference_project]
    )


@mcp.tool(name="list_project_references")
async def list_project_references(project_file: str) -> str:
    """Lists project-to-project references."""
    return await run_dotnet_async(["list", project_file, "reference"])


# --- Package Management ---


@mcp.tool(name="get_dotnet_version")
async def get_dotnet_version() -> str:
    """Gets the current .NET SDK version."""
    try:
        # This will return something like '8.0.100'
        version = await run_dotnet_async(["--version"])
        version = version.strip()
        if version and not version.startswith("Error"):
            return version
    except Exception as e:
        return f"Error detecting .NET version: {e!s}"
    return "Unknown"


@mcp.tool(name="add_package")
async def add_package(
    project_file: str, package_name: str, version: str | None = None
) -> str:
    """Adds a NuGet package with automatic versioning."""
    original_version = version
    if not version:
        detected = await get_dotnet_version()
        if detected and not (detected.startswith("Error") or detected == "Unknown"):
            major = detected.split(".")[0]
            version = f"{major}.*"

    args = ["add", project_file, "package", package_name]
    if version:
        args.extend(["--version", version])

    result = await run_dotnet_async(args)
    if (
        "Error" in result
        and original_version is None
        and version
        and version.endswith(".*")
    ):
        fallback_args = ["add", project_file, "package", package_name]
        return await run_dotnet_async(fallback_args)

    return result


@mcp.tool(name="remove_package")
async def remove_package(project_file: str, package_name: str) -> str:
    """Removes a NuGet package from a project."""
    return await run_dotnet_async(["remove", project_file, "package", package_name])


@mcp.tool(name="list_packages")
async def list_packages(project_file: str) -> str:
    """Lists all NuGet packages for a project."""
    return await run_dotnet_async(["list", project_file, "package"])


# --- Build and Execution ---


@mcp.tool(name="build")
async def build(target: str | None = None, configuration: str = "Debug") -> str:
    """Builds a project or solution."""
    args = ["build"]
    if target:
        args.append(target)
    args.extend(["-c", configuration])
    return await run_dotnet_async(args)


@mcp.tool(name="run_project")
async def run_project(project_file: str | None = None) -> str:
    """Runs the project."""
    args = ["run"]
    if project_file:
        args.extend(["--project", project_file])
    return await run_dotnet_async(args)


@mcp.tool(name="test")
async def test(target: str | None = None) -> str:
    """Executes tests in a project or solution."""
    args = ["test"]
    if target:
        args.append(target)
    return await run_dotnet_async(args)


@mcp.tool(name="clean")
async def clean(target: str | None = None) -> str:
    """Cleans the output of a project or solution."""
    args = ["clean"]
    if target:
        args.append(target)
    return await run_dotnet_async(args)


@mcp.tool(name="publish")
async def publish(
    target: str | None = None,
    configuration: str = "Release",
    output_dir: str | None = None,
) -> str:
    """Publishes the application for deployment."""
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
    """Displays detailed .NET environment info."""
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
