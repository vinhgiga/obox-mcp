from __future__ import annotations

from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server for installer
mcp = FastMCP(
    "OboxInstaller",
    instructions=(
        "Tools to install development dependencies like Homebrew on macOS "
        "and Scoop on Windows."
    ),
)


@mcp.tool(name="install_package_manager")
async def install_package_manager() -> str:
    """
    Automatically detects the OS and installs the appropriate package manager:
    - macOS: Homebrew
    - Windows: Scoop
    """
    _, message = await utils.install_package_manager()
    return message


@mcp.tool(name="install_app")
async def install_app(app_name: str, scoop_bucket: str | None = None) -> str:
    """
    Install an application using the system's package manager.
    - On macOS: uses Homebrew
    - On Windows: uses Scoop (optionally adds a bucket)
    """
    _, message = await utils.install_app(app_name, scoop_bucket)
    return message


@mcp.tool(name="add_bucket")
async def add_bucket(bucket_name: str) -> str:
    """
    Add a bucket to Scoop (Windows only).
    """
    _, message = await utils.add_scoop_bucket(bucket_name)
    return message


@mcp.tool(name="search_package")
async def search_package(name: str) -> str:
    """
    Search for a package using the system's package manager.
    - On macOS: brew search {name}
    - On Windows: scoop search {name}
    """
    _, message = await utils.search_package(name)
    return message


if __name__ == "__main__":
    mcp.run()
