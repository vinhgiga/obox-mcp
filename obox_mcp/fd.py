from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxFd",
    instructions=(
        "Search for files and directories within the codebase using patterns or names. "
        "It respects .gitignore rules and skips hidden files by default. "
        "Ideal for locating specific source files."
    ),
)


async def run_fd_async(args: list[str]) -> str:
    """Helper to run fd commands asynchronously and return output."""
    success, msg = await utils.install_app("fd")
    if not success:
        return f"Error: {msg}"

    return await utils.run_command_output(
        ["fd", *args], error_prefix="Error executing fd", success_codes=[0, 1]
    )


@mcp.tool()
async def search_files(
    regex: str | None = None,
    glob: str | None = None,
    path: str | None = None,
) -> str:
    """
    Search for files and directories in the codebase.

    Args:
        regex: A regular expression pattern to match filenames.
        glob: A glob pattern to match filenames (e.g. `*.py`, `**/*.js`).
        path: The root directory to start searching from.
    """
    args = []

    if glob:
        args.append("-g")
        args.append(glob)
    elif regex:
        args.append(regex)

    if path:
        args.append(path)

    return await run_fd_async(args)


# FastAPI integration for consistency
app = FastAPI(title="OboxFd MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount MCP HTTP app
app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxFd MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
