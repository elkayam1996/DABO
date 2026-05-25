from dataclasses import dataclass

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
    web_fetch,
)

from .runningTools import (
    run_python,
)

@dataclass
class ToolDesc:
    name: str
    description: str
    input_schema: dict
    output_schema: dict | None
    callable_ref: None


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

        self.TOOL_REGISTRY_DESCRIPTION = {
            "list_dir": "list_dir(path: str) -> list files and folders in a directory.",
            "read_file": "read_file(path: str) -> read text content from a file.",
            "write_file": "write_file(path: str, content: str) -> create or overwrite a file.",
            "edit_file": "edit_file(path: str, old_text: str, new_text: str) -> replace one exact text block in a file.",
            "apply_patch": "apply_patch(path: str, replacements: list[dict]) -> apply several old/new text replacements to one file.",
            "run_python": "run_python(path: str) -> run a Python file and return stdout, stderr, and return code.",
            "web_search": "web_search(query: str) -> search the web. Currently placeholder.",
            "web_fetch": "web_fetch(url: str) -> fetch readable text from a webpage.",
            "ask_user_approval": "ask_user_approval(action: str) -> ask the user to approve an action.",
        }

    def get_available_tools(self) -> str:
        lines = []

        for tool_name, description in self.TOOL_REGISTRY_DESCRIPTION.items():
            lines.append(f"- {tool_name}: {description}")

        return "\n".join(lines)

    def run_tool(self, tool_name: str, tool_input: dict) -> dict:
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