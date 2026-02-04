from __future__ import annotations

import asyncio
import os

import anyio
from fastmcp import FastMCP
from pydantic import BaseModel

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxNodeJS",
    instructions=(
        "A tool to manage Node.js environments and packages using fnm and pnpm in "
        "an asynchronous way. It supports installing Node.js versions, managing "
        "packages, and querying environment state."
    ),
)


class NodeEnvInfo(BaseModel):
    node_version: str
    pnpm_version: str
    installed_node_versions: list[str]
    project_name: str | None


async def run_command_async(cmd: str, args: list[str], cwd: str | None = None) -> str:
    """Helper to run commands asynchronously and return output."""
    if cmd in ["fnm", "pnpm"]:
        success, msg = await utils.install_app(cmd)
        if not success:
            return f"Error installing {cmd}: {msg}"

    return await utils.run_command_output([cmd, *args], cwd=cwd)


@mcp.tool(name="install_nodejs_tools")
async def install_nodejs_tools() -> str:
    """
    Installs fnm (Fast Node Manager) and pnpm.
    On macOS, uses Homebrew. On Windows, uses Scoop.
    """
    results = []

    # Install fnm
    _success, msg = await utils.install_app("fnm")
    results.append(f"fnm: {msg}")

    # Install pnpm
    _success, msg = await utils.install_app("pnpm")
    results.append(f"pnpm: {msg}")

    return "\n".join(results)


@mcp.tool(name="list_node_versions")
async def list_node_versions() -> str:
    """
    Lists all installed Node.js versions using 'fnm ls'.
    """
    return await run_command_async("fnm", ["ls"])


@mcp.tool(name="list_remote_node_versions")
async def list_remote_node_versions() -> str:
    """
    Lists available remote Node.js versions using 'fnm ls-remote'.
    """
    return await run_command_async("fnm", ["ls-remote"])


@mcp.tool(name="install_node_version")
async def install_node_version(version: str) -> str:
    """
    Installs a specific Node.js version using 'fnm install'.
    Example versions: '20', '18.17.0', 'latest'.
    """
    return await run_command_async("fnm", ["install", version])


@mcp.tool(name="use_node_version")
async def use_node_version(version: str) -> str:
    """
    Sets the current Node.js version using 'fnm use'.
    Note: This may require a shell restart or 'eval $(fnm env)' to reflect in
    some terminals.
    """
    return await run_command_async("fnm", ["use", version])


@mcp.tool(name="get_nodejs_info")
async def get_nodejs_info(root_dir: str | None = None) -> str:
    """
    Retrieves detailed information about the current Node.js environment.
    """
    try:
        if root_dir is None:
            root_dir = await utils.find_project_root("package.json")

        node_ver_task = run_command_async("node", ["--version"], cwd=root_dir)
        pnpm_ver_task = run_command_async("pnpm", ["--version"], cwd=root_dir)
        fnm_list_task = run_command_async("fnm", ["ls"], cwd=root_dir)

        node_ver, pnpm_ver, fnm_list_raw = await asyncio.gather(
            node_ver_task, pnpm_ver_task, fnm_list_task
        )

        fnm_list = [line.strip() for line in fnm_list_raw.split("\n") if line.strip()]

        project_name = None
        pkg_json_path = (
            os.path.join(root_dir, "package.json") if root_dir else "package.json"
        )
        if os.path.exists(pkg_json_path):
            import json

            content = await anyio.Path(pkg_json_path).read_text()
            data = json.loads(content)
            project_name = data.get("name")

        info = NodeEnvInfo(
            node_version=node_ver,
            pnpm_version=pnpm_ver,
            installed_node_versions=fnm_list,
            project_name=project_name,
        )
        return info.model_dump_json(indent=2)
    except Exception as e:
        return f"Error gathering environment info: {e!s}"


@mcp.tool(name="pnpm_add")
async def pnpm_add(
    packages: list[str], dev: bool = False, root_dir: str | None = None
) -> str:
    """
    Installs packages using 'pnpm add'.
    Use dev=True for devDependencies.
    Example: packages=["tailwindcss", "axios"]
    """
    if root_dir is None:
        root_dir = await utils.find_project_root("package.json")
    args = ["add", *packages]
    if dev:
        args.append("-D")
    return await run_command_async("pnpm", args, cwd=root_dir)


@mcp.tool(name="pnpm_install")
async def pnpm_install(root_dir: str | None = None) -> str:
    """
    Installs all dependencies in package.json using 'pnpm install'.
    """
    if root_dir is None:
        root_dir = await utils.find_project_root("package.json")
    return await run_command_async("pnpm", ["install"], cwd=root_dir)


@mcp.tool(name="pnpm_run")
async def pnpm_run(script: str, root_dir: str | None = None) -> str:
    """
    Runs a script defined in package.json using 'pnpm run <script>'.
    """
    if root_dir is None:
        root_dir = await utils.find_project_root("package.json")
    return await run_command_async("pnpm", ["run", script], cwd=root_dir)


if __name__ == "__main__":
    mcp.run()
