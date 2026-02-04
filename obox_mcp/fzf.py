from __future__ import annotations

import asyncio

import anyio
import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxFzf",
    instructions=(
        "A tool for fuzzy filtering lists of strings using fzf. "
        "It provides a non-interactive way to apply fzf matching logic to any "
        "list of strings."
    ),
)


async def run_fzf_filter(items: list[str], query: str, args: list[str]) -> str:
    """Helper to run fzf --filter asynchronously."""
    success, msg = await utils.install_app("fzf")
    if not success:
        return f"Error: {msg}"

    fzf_args = ["fzf", "--filter", query, *args]
    input_data = "\n".join(items)
    return await utils.run_command_output(
        fzf_args,
        input_data=input_data,
        error_prefix="Error executing fzf",
        success_codes=[0, 1],
    )


@mcp.tool()
async def filter_file_content(
    file_path: str,
    query: str,
    exact: bool = False,
    ignore_case: bool = False,
) -> str:
    """
    Fuzzy filter the lines of a specific file.

    Args:
        file_path: Path to the file to filter.
        query: Fuzzy search pattern.
        exact: Enable exact-match.
        ignore_case: Case-insensitive match.
    """
    try:
        content = await anyio.Path(file_path).read_text()
        items = content.splitlines()

        args = []
        if exact:
            args.append("-e")
        if ignore_case:
            args.append("-i")

        return await run_fzf_filter(items, query, args)
    except Exception as e:
        return f"Error reading file {file_path}: {e!s}"


@mcp.tool()
async def search_files(
    query: str,
    path: str = ".",
    hidden: bool = False,
    no_ignore: bool = False,
) -> str:
    """
    Find files using 'fd' and then fuzzy filter the results with 'fzf'.

    Args:
        query: The fuzzy search pattern for filenames.
        path: The root directory to start searching from.
        hidden: Search hidden files and directories (-H).
        no_ignore: Do not respect .gitignore (-I).
    """
    fd_args = ["fd", "--type", "f", "--color", "never"]
    if hidden:
        fd_args.append("-H")
    if no_ignore:
        fd_args.append("-I")
    fd_args.append(path)

    # Ensure fd is installed
    success, msg = await utils.install_app("fd")
    if not success:
        return f"Error: {msg}"

    try:
        fd_process = await asyncio.create_subprocess_exec(
            *fd_args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        fd_stdout, fd_stderr = await fd_process.communicate()

        if fd_process.returncode != 0 and fd_process.returncode != 1:
            return f"Error listing files with fd: {fd_stderr.decode().strip()}"

        file_list = fd_stdout.decode().splitlines()
        if not file_list:
            return "No files found to search."

        return await run_fzf_filter(file_list, query, [])

    except FileNotFoundError:
        return (
            "Error: 'fd' or 'fzf' command not found. Please ensure they are installed."
        )
    except Exception as e:
        return f"Error during fuzzy file search: {e!s}"


# FastAPI integration for consistency
app = FastAPI(title="OboxFzf MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount MCP HTTP app
app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxFzf MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
