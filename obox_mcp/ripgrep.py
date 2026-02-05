from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxRipgrep",
    instructions=(
        "A tool to search for patterns in files recursively using ripgrep (rg). "
        "It respects .gitignore rules and skips hidden files by default. "
        "Ideal for codebase exploration and finding string occurrences."
    ),
)


async def run_rg_async(args: list[str]) -> str:
    """Helper to run rg commands asynchronously and return output."""
    success, msg = await utils.install_app("ripgrep", command_name="rg")
    if not success:
        return f"Error: {msg}"

    return await utils.run_command_output(
        ["rg", *args], error_prefix="Error executing rg", success_codes=[0, 1]
    )


@mcp.tool()
async def search(
    regex: str,
    path: str = ".",
    glob: list[str] | None = None,
) -> str:
    """
    Search for a regex pattern in a directory recursively using ripgrep.

    Args:
        regex: The regex pattern to search for.
        path: The directory or file to search in (default is current directory).
        glob: Optional glob patterns to include/exclude files (e.g., ["*.py", "!*.log"]).
    """  # noqa: E501
    args = []

    if glob:
        for g in glob:
            args.append("-g")
            args.append(g)

    args.extend([regex, path])

    return await run_rg_async(args)


@mcp.tool()
async def list_files(
    path: str = ".",
    glob: list[str] | None = None,
) -> str:
    """
    List files that would be searched by ripgrep, respecting .gitignore.

    Args:
        path: The directory to list files from.
        glob: Optional glob patterns to filter files.
    """
    args = ["--files"]
    if glob:
        for g in glob:
            args.append("-g")
            args.append(g)
    args.append(path)
    return await run_rg_async(args)


@mcp.tool()
async def list_file_types() -> str:
    """
    Lists all supported file types that can be used with ripgrep filtering.
    """
    return await run_rg_async(["--type-list"])


# FastAPI integration for consistency
app = FastAPI(title="OboxRipgrep MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount MCP HTTP app
app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxRipgrep MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
