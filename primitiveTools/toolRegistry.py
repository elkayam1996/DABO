from .IOTools import (
    list_dir,
    read_file,
    write_file,
    edit_file,
    apply_patch,
    ask_user_approval,
)

from .webTools import (
    web_search,
    web_fetch
)

from .runningTools import (
    run_python
)

class ToolRegistry:

    def __init__(self) -> None:
        self.TOOL_REGISTRY = {
            "list_dir": list_dir,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "apply_patch": apply_patch,
            "run_python": run_python,
            "web_search": web_search,
            "web_fetch": web_fetch,
            "ask_user_approval": ask_user_approval,
        }

    def get_available_tools(self) -> list[str]:
        return list(self.TOOL_REGISTRY.keys())

    def run_tool(self,tool_name: str, tool_input: dict) -> dict:
        if tool_name not in self.TOOL_REGISTRY:
            return {
                "ok": False,
                "error": f"Unknown tool: {tool_name}",
            }

        tool_func = self.TOOL_REGISTRY[tool_name]

        try:
            return tool_func(**tool_input)
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }