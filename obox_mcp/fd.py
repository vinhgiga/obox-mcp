from __future__ import annotations

import asyncio
import shlex
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "OboxFd",
    instructions=(
        "Find entries in filesystem by pattern, extension, size, etc. "
        "It respects .gitignore rules and skips hidden files by default."
    ),
)


async def run_fd_async(args: List[str]) -> str:
    """Helper to run fd commands asynchronously and return output."""
    try:
        # We assume 'fd' is installed. If not, it might fail.
        # Check for 'fdfind' which is common on some systems like Ubuntu.
        cmd = "fd"
        process = await asyncio.create_subprocess_exec(
            cmd, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0 and process.returncode != 1:
            # fd returns 1 if no matches are found, which is fine.
            # Other non-zero codes might be errors.
            # However, fd help says:
            # Exit code 0: matches found
            # Exit code 1: no matches found
            # So 1 is not an error.
            if process.returncode == 1:
                return "No entries found."

            error_msg = stderr.decode().strip() or stdout.decode().strip()
            return f"Error executing fd {' '.join(args)} (Exit code {process.returncode}): {error_msg}"

        output = stdout.decode().strip()
        if not output and process.returncode == 1:
            return "No entries found."

        return output
    except FileNotFoundError:
        return "Error: 'fd' command not found. Please ensure fd-find is installed."
    except Exception as e:
        return f"Error executing fd {' '.join(args)}: {e!s}"


@mcp.tool()
async def find(
    pattern: Optional[str] = None,
    path: Optional[str] = None,
    hidden: bool = False,
    no_ignore: bool = False,
    case_sensitive: bool = False,
    ignore_case: bool = False,
    glob: bool = False,
    absolute_path: bool = False,
    list_details: bool = False,
    follow: bool = False,
    full_path: bool = False,
    max_depth: Optional[int] = None,
    exclude: Optional[List[str]] = None,
    file_type: Optional[str] = None,
    extension: Optional[List[str]] = None,
    size: Optional[str] = None,
    changed_within: Optional[str] = None,
    changed_before: Optional[str] = None,
    owner: Optional[str] = None,
) -> str:
    """
    Find entries in the filesystem using fd.

    Args:
        pattern: The search pattern (regular expression by default).
        path: The root directory for the search.
        hidden: Search hidden files and directories (-H).
        no_ignore: Do not respect .gitignore or .fdignore files (-I).
        case_sensitive: Case-sensitive search (default: smart case) (-s).
        ignore_case: Case-insensitive search (default: smart case) (-i).
        glob: Use glob-based search instead of regular expression (-g).
        absolute_path: Show absolute instead of relative paths (-a).
        list_details: Use a long listing format with file metadata (-l).
        follow: Follow symbolic links (-L).
        full_path: Search full absolute path instead of just filename (-p).
        max_depth: Set maximum search depth (-d).
        exclude: Exclude entries that match the given glob pattern (-E).
        file_type: Filter by type: file (f), directory (d), symlink (l), executable (x), empty (e).
        extension: Filter by file extension (-e).
        size: Limit results based on the size of files (-S).
        changed_within: Filter by file modification time (newer than).
        changed_before: Filter by file modification time (older than).
        owner: Filter by owning user and/or group (user:group).
    """
    args = []
    if hidden:
        args.append("-H")
    if no_ignore:
        args.append("-I")
    if case_sensitive:
        args.append("-s")
    if ignore_case:
        args.append("-i")
    if glob:
        args.append("-g")
    if absolute_path:
        args.append("-a")
    if list_details:
        args.append("-l")
    if follow:
        args.append("-L")
    if full_path:
        args.append("-p")

    if max_depth is not None:
        args.extend(["-d", str(max_depth)])

    if exclude:
        for ex in exclude:
            args.extend(["-E", ex])

    if file_type:
        args.extend(["-t", file_type])

    if extension:
        for ext in extension:
            args.extend(["-e", ext])

    if size:
        args.extend(["-S", size])

    if changed_within:
        args.extend(["--changed-within", changed_within])

    if changed_before:
        args.extend(["--changed-before", changed_before])

    if owner:
        args.extend(["-o", owner])

    if pattern:
        args.append(pattern)

    if path:
        args.append(path)

    return await run_fd_async(args)


@mcp.tool()
async def execute(
    command: str,
    pattern: Optional[str] = None,
    path: Optional[str] = None,
    extension: Optional[List[str]] = None,
    file_type: Optional[str] = None,
    batch: bool = False,
) -> str:
    """
    Execute a command for each search result found by fd.

    Args:
        command: The command to execute. Use '{}' as a placeholder for the result path.
        pattern: The search pattern.
        path: The root directory for the search.
        extension: Filter by file extension.
        file_type: Filter by type: file (f), directory (d), etc.
        batch: If True, execute the command once with all search results at once (-X).
               Otherwise, execute once per result (-x).
    """
    args = []
    if batch:
        args.append("-X")
    else:
        args.append("-x")

    args.extend(shlex.split(command))

    if extension:
        for ext in extension:
            args.extend(["-e", ext])

    if file_type:
        args.extend(["-t", file_type])

    if pattern:
        args.append(pattern)

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
