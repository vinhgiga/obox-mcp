from __future__ import annotations

import shlex

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxFd",
    instructions=(
        "Find entries in filesystem by pattern, extension, size, etc. "
        "It respects .gitignore rules and skips hidden files by default."
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
async def find(
    pattern: str | None = None,
    path: str | None = None,
    hidden: bool = False,
    no_ignore: bool = False,
    case_sensitive: bool = False,
    ignore_case: bool = False,
    glob: bool = False,
    absolute_path: bool = False,
    list_details: bool = False,
    follow: bool = False,
    full_path: bool = False,
    max_depth: int | None = None,
    exclude: list[str] | None = None,
    file_type: str | None = None,
    extension: list[str] | None = None,
    size: str | None = None,
    changed_within: str | None = None,
    changed_before: str | None = None,
    owner: str | None = None,
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
        file_type: Filter by type: file (f), directory (d), symlink (l),
                   executable (x), empty (e).
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
    pattern: str | None = None,
    path: str | None = None,
    extension: list[str] | None = None,
    file_type: str | None = None,
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
