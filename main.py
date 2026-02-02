from __future__ import annotations

import importlib
import os
import sys
from typing import Any

from fastmcp import FastMCP

# Initialize the main MCP server
mcp = FastMCP(
    "OboxDev",
    instructions=(
        "The main entry point for Obox development tools. "
        "Combines multiple MCP servers."
    ),
)


def load_mcp_modules():
    """Dynamically load all MCP modules from the mcp/ directory and mount them."""
    # Ensure the current directory is in sys.path so we can import modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    mcp_dir = os.path.join(current_dir, "obox_mcp")
    if not os.path.exists(mcp_dir):
        print(f"Error: Directory {mcp_dir} not found.")
        return

    # Iterate through the files in obox_mcp/
    for filename in sorted(os.listdir(mcp_dir)):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = f"obox_mcp.{filename[:-3]}"
            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Check for standard MCP instance names: mcp, server, or app
                sub_app: Any = None
                for attr in ["mcp", "server", "app"]:
                    val = getattr(module, attr, None)
                    if isinstance(val, FastMCP):
                        sub_app = val
                        break

                if sub_app:
                    # Mount the sub-app to the main app with a prefix
                    # The prefix is derived from the filename
                    prefix = filename[:-3]
                    mcp.mount(sub_app, prefix=prefix)
                    print(f"✅ Mounted MCP from {module_name} with prefix: {prefix}")
                else:
                    print(f"⚠️  No FastMCP instance found in {module_name}")

            except Exception as e:
                print(f"❌ Error loading {module_name}: {e}")


if __name__ == "__main__":
    # Load and mount all MCPs
    load_mcp_modules()

    # Check for CLI arguments
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        import uvicorn

        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Starting OboxDev MCP as HTTP server on port {port}...")

        # Create a FastAPI app and mount the MCP's HTTP app
        from fastapi import FastAPI

        app = FastAPI(title="OboxDev MCP Portal")
        app.mount("/mcp", mcp.http_app())

        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        # Run the MCP server (default is stdio)
        print("Starting OboxDev MCP on stdio...")
        mcp.run()
