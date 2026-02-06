from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxBat",
    instructions="Read files with line ranges using bat.",
)


async def _read_file(
    path: str,
    line_range: str | None = None,
    style: str = "numbers",
) -> str:
    max_lines = 500
    final_range = "1:500"

    if line_range:
        if ":" in line_range:
            parts = line_range.split(":")
            if len(parts) > 2:
                return (
                    "Error: Invalid line range format. Use 'N', 'N:M', 'N:', or ':M'."
                )

            start_str, end_str = parts

            try:
                start = int(start_str) if start_str else 1
            except ValueError:
                return "Error: Invalid start line number."

            if end_str:
                try:
                    end = int(end_str)
                except ValueError:
                    return "Error: Invalid end line number."
            else:
                end = start + max_lines - 1

            if end < start:
                return "Error: End line must be >= start line."

            if (end - start + 1) > max_lines:
                return f"Error: Line range exceeds maximum of {max_lines} lines."

            final_range = f"{start}:{end}"

        else:
            try:
                _ = int(line_range)
                final_range = line_range
            except ValueError:
                return "Error: Invalid line number."
    else:
        final_range = "1:500"

    # Ensure bat is installed
    success, msg = await utils.install_app("bat")
    if not success:
        return f"Error: {msg}"

    args = ["bat", "--line-range", final_range]
    args.extend(["--style", style])
    args.extend(["--color", "never"])
    args.append(path)
    return await utils.run_command_output(
        args, error_prefix="Error reading file with bat"
    )


@mcp.tool()
async def read_file(
    path: str,
    line_range: str | None = None,
    style: str = "numbers",
) -> str:
    """
    Read a file with support for line ranges. Enforces a maximum limit of 500 lines per read.

    Args:
        path: Absolute path to the file to read.
        line_range: Line range to read (e.g., "30:", "30:50", ":50", "10").
        style: Output style. Options: 'default', 'plain', 'numbers', 'changes', 'grid', 'header', 'snip'.
        Default is 'numbers' to show line numbers.
    """  # noqa: E501
    return await _read_file(path, line_range, style)


# FastAPI integration for consistency
app = FastAPI(title="OboxBat MCP Service")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount MCP HTTP app
app.mount("/mcp", mcp.http_app())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxBat MCP as HTTP server on port {port}...")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        mcp.run()
