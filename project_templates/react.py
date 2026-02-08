from __future__ import annotations

import asyncio
import os
import textwrap

from fastmcp import FastMCP

from obox_mcp import utils

mcp = FastMCP(
    "OboxReact",
    instructions=(
        "A tool to initialize a new React project with Vite, pnpm, Tailwind CSS v4, "
        "TanStack Query, and Tabler Icons. "
        "After successful initialization, you MUST call the `project_runner` tool "
        "from the `obox_mcp.just` server to finalize the setup."
    ),
)


async def run_command_async(
    args: list[str], cwd: str | None = None
) -> tuple[int, str, str]:
    """Helper to run commands asynchronously and return (returncode, stdout, stderr)."""
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        return 1, "", str(e)


@mcp.tool(name="init_project")
async def init_project(path: str) -> str:
    """
    Initializes a new React project at the specified path.
    Setup includes:
    - Vite (React + TypeScript)
    - Tailwind CSS v4
    - TanStack Query
    - Tabler Icons React

    Args:
        path: The absolute path where the project should be initialized.
    """
    if not os.path.isabs(path):
        # Try to make it absolute if it starts with ~
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            return "Error: Path must be absolute."

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    # 0. Ensure pnpm is installed
    success, msg = await utils.install_app("pnpm")
    if not success:
        return f"Error ensuring 'pnpm' is installed: {msg}"

    # 1. pnpm create vite . --template react-ts --no-interactive
    rc, stdout, stderr = await run_command_async(
        [
            "pnpm",
            "create",
            "vite",
            ".",
            "--template",
            "react-ts",
            "--no-interactive",
        ],
        cwd=path,
    )
    if rc != 0:
        return f"Error during 'pnpm create vite': {stderr or stdout}"

    # 2. Install dependencies
    # First install base template dependencies (this ensures React and types are present)
    rc, stdout, stderr = await run_command_async(["pnpm", "install"], cwd=path)
    if rc != 0:
        return f"Error during 'pnpm install': {stderr or stdout}"

    # Then add the new requested packages
    rc, stdout, stderr = await run_command_async(
        [
            "pnpm",
            "add",
            "tailwindcss",
            "@tailwindcss/vite",
            "@tanstack/react-query",
            "@tabler/icons-react",
        ],
        cwd=path,
    )
    if rc != 0:
        return f"Error during 'pnpm add': {stderr or stdout}"

    # 3. Configure vite.config.ts for Tailwind v4
    vite_config_path = os.path.join(path, "vite.config.ts")
    vite_config_content = textwrap.dedent("""\
        import { defineConfig } from 'vite'
        import react from '@vitejs/plugin-react'
        import tailwindcss from '@tailwindcss/vite'

        // https://vitejs.dev/config/
        export default defineConfig({
          plugins: [
            react(),
            tailwindcss(),
          ],
          server: {
            proxy: {
              '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\\/api/, ''),
              },
            },
          },
        })
    """)

    def write_vite_config():
        with open(vite_config_path, "w") as f:
            f.write(vite_config_content)

    await asyncio.to_thread(write_vite_config)

    # 4. Configure src/index.css for Tailwind v4
    index_css_path = os.path.join(path, "src", "index.css")
    index_css_content = textwrap.dedent("""\
        /* @layer theme, base, components, mantine, utilities; */

        @import "tailwindcss";

        /* @layer mantine {
          @import "@mantine/core/styles.layer.css";
        } */
    """)

    def write_index_css():
        with open(index_css_path, "w") as f:
            f.write(index_css_content)

    await asyncio.to_thread(write_index_css)

    # 5. Create a basic App.tsx with TanStack Query and Tabler Icons
    app_tsx_path = os.path.join(path, "src", "App.tsx")
    app_tsx_content = textwrap.dedent("""\
        import {
          QueryClient,
          QueryClientProvider,
          useQuery
        } from '@tanstack/react-query'
        import {
          IconRocket,
          IconCode,
          IconExternalLink
        } from '@tabler/icons-react'
        // import { MantineProvider, createTheme } from '@mantine/core'

        const queryClient = new QueryClient()
        // const theme = createTheme({})

        function Dashboard() {
          const { data, isLoading } = useQuery({
            queryKey: ['hello'],
            queryFn: async () => {
              await new Promise(r => setTimeout(r, 1000))
              return { message: "Obox React Template is ready!" }
            }
          })

          return (
            <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col
              items-center justify-center p-8">
              <div className="max-w-2xl w-full bg-slate-900 border border-slate-800
                rounded-2xl p-8 shadow-2xl">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                    <IconRocket size={32} />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold">Obox React Template</h1>
                    <p className="text-slate-400">
                      Vite + React + TS + Tailwind v4
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-2 text-sm font-medium
                      text-slate-500">
                      <IconCode size={16} />
                      <span>TanStack Query Status</span>
                    </div>
                    {isLoading ? (
                      <p className="animate-pulse text-blue-400">
                        Fetching workspace state...
                      </p>
                    ) : (
                      <p className="text-emerald-400 font-mono">
                        {data?.message}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-950 rounded-lg border border-slate-800
                      flex flex-col gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wider
                        text-slate-500">
                        Styling
                      </span>
                      <span className="text-sm">Tailwind CSS v4</span>
                    </div>
                    <div className="p-4 bg-slate-950 rounded-lg border border-slate-800
                      flex flex-col gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wider
                        text-slate-500">
                        Icons
                      </span>
                      <span className="text-sm">Tabler Icons</span>
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-800 flex
                  justify-between items-center text-sm text-slate-500">
                  <span>Built with Obox MCP</span>
                  <a
                    href="https://vitejs.dev"
                    target="_blank"
                    className="flex items-center gap-1 hover:text-blue-400
                      transition-colors"
                  >
                    Docs <IconExternalLink size={14} />
                  </a>
                </div>
              </div>
            </div>
          )
        }

        export default function App() {
          return (
            <QueryClientProvider client={queryClient}>
              {/* <MantineProvider theme={theme}> */}
                <Dashboard />
              {/* </MantineProvider> */}
            </QueryClientProvider>
          )
        }
    """)

    def write_app_tsx():
        with open(app_tsx_path, "w") as f:
            f.write(app_tsx_content)

    await asyncio.to_thread(write_app_tsx)

    return (
        f"\n✨ React project successfully initialized at: {path}\n"
        "Tech Stack: Vite (React + TS), Tailwind CSS v4, "
        "TanStack Query, Tabler Icons.\n\n"
        "🚀 **Next Step**: Call the `project_runner` tool to finalize the setup "
        "and generate a `justfile` for running the project.\n"
    )


if __name__ == "__main__":
    mcp.run()
