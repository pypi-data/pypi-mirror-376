from mcp.server import Server

from jupyter_agent_toolkit.notebook import NotebookSession
from jupyter_agent_toolkit.utils.execution import (
    invoke_code_cell,
    invoke_markdown_cell,
)
from jupyter_agent_toolkit.utils.packages import update_dependencies


def register_all_tools(server: Server, session: NotebookSession) -> None:
    """Register notebook tools with MCP."""

    async def _ensure_started():
        if not await session.is_connected():
            await session.start()

    @server.tool(name="notebook.markdown.add")
    async def notebook_markdown_add(content: str):
        """Append a markdown cell and return its index."""
        await _ensure_started()
        idx = await invoke_markdown_cell(session, content)
        return {"ok": True, "index": idx}

    @server.tool(name="notebook.code.run")
    async def notebook_code_run(content: str):
        """Append a code cell, execute it, and return rich outputs."""
        await _ensure_started()
        res = await invoke_code_cell(session, content)
        return {"ok": res.status == "ok", **res.__dict__}

    @server.tool(name="notebook.packages.add")
    async def notebook_packages_add(packages: list[str]):
        """Ensure the given packages are available in the kernel."""
        await _ensure_started()
        ok = await update_dependencies(session.kernel, packages)
        return {"ok": ok, "packages": packages}
