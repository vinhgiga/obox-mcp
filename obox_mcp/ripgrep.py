from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxRipgrep",
    instructions=(
        "A tool to search for regex patterns within the content of files recursively "
        "using ripgrep (rg). It respects .gitignore rules by default and can "
        "optionally search hidden files. Ideal for codebase exploration and "
        "finding string occurrences within the source code."
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
    glob: list[str] | None = None,
    hidden: bool = False,
) -> str:
    """
    Search for a regex pattern in the codebase.
    This tool searches through the contents of files.

    Args:
        regex: The regex pattern to search for in file contents.
        glob: Optional glob patterns to include/exclude files (e.g., ["*.py", "!*.log"]).
        hidden: Search hidden files and directories (default: False).
    """  # noqa: E501
    args = []

    if hidden:
        args.append("--hidden")

    if glob:
        for g in glob:
            args.append("-g")
            args.append(g)

    args.extend([regex, "."])

    return await run_rg_async(args)


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
