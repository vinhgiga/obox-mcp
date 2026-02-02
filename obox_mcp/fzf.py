from __future__ import annotations

import asyncio
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "OboxFzf",
    instructions=(
        "A tool for fuzzy filtering lists of strings using fzf. "
        "It provides a non-interactive way to apply fzf matching logic to any list of strings."
    ),
)


async def run_fzf_filter(items: List[str], query: str, args: List[str]) -> str:
    """Helper to run fzf --filter asynchronously."""
    try:
        # Construct the command with --filter
        # fzf --filter=query [other args]
        fzf_args = ["--filter", query] + args

        process = await asyncio.create_subprocess_exec(
            "fzf",
            *fzf_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Join items with newlines and encode
        # We use \n as delimiter. If items contain \n, fzf will treat them as multiple entries.
        input_data = "\n".join(items).encode()
        stdout, stderr = await process.communicate(input=input_data)

        if process.returncode == 0:
            return stdout.decode().strip()
        if process.returncode == 1:
            return "No matches found."
        error_msg = stderr.decode().strip() or stdout.decode().strip()
        return f"Error executing fzf {' '.join(fzf_args)} (Exit code {process.returncode}): {error_msg}"

    except FileNotFoundError:
        return "Error: 'fzf' command not found. Please ensure fzf is installed."
    except Exception as e:
        return f"Error executing fzf: {e!s}"


@mcp.tool()
async def filter_items(
    items: List[str],
    query: str,
    exact: bool = False,
    ignore_case: bool = False,
    smart_case: bool = True,
    no_sort: bool = False,
    nth: Optional[str] = None,
    with_nth: Optional[str] = None,
    delimiter: Optional[str] = None,
    tiebreak: Optional[str] = None,
) -> str:
    """
    Fuzzy filter a list of items using fzf matching logic.

    Args:
        items: The list of strings to filter.
        query: The fuzzy search pattern.
        exact: Enable exact-match.
        ignore_case: Case-insensitive match.
        smart_case: Smart-case match (default).
        no_sort: Do not sort the result.
        nth: Comma-separated list of field index expressions for limiting search scope.
             Example: "2,3..5", "-1" (last field).
        with_nth: Transform the presentation of each line using field index expressions.
        delimiter: Field delimiter regex (default: AWK-style).
        tiebreak: Comma-separated list of sort criteria to apply when scores are tied:
                  length, chunk, pathname, begin, end, index.
    """
    args = []
    if exact:
        args.append("-e")

    if ignore_case:
        args.append("-i")
    elif not smart_case:
        args.append("+i")  # Case-sensitive

    if no_sort:
        args.append("+s")

    if nth:
        args.extend(["--nth", nth])

    if with_nth:
        args.extend(["--with-nth", with_nth])

    if delimiter:
        args.extend(["--delimiter", delimiter])

    if tiebreak:
        args.extend(["--tiebreak", tiebreak])

    return await run_fzf_filter(items, query, args)


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
        with open(file_path) as f:
            lines = f.readlines()

        # Strip trailing newlines for items
        items = [line.rstrip("\n") for line in lines]

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
