from pathlib import Path


def safe_path(path: str) -> Path:
    """
    Converts a string path into a real full path.

    This version does NOT limit access to the current project folder.
    Later you can add permission limits here.
    """
    return Path(path).expanduser().resolve()


def list_dir(path: str = ".") -> dict:
    folder = safe_path(path)

    if not folder.exists():
        return {"ok": False, "error": "Folder does not exist."}

    if not folder.is_dir():
        return {"ok": False, "error": "Path is not a folder."}

    items = []

    for item in folder.iterdir():
        items.append({
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
            "path": str(item),
        })

    return {"ok": True, "items": items}


def read_file(path: str) -> dict:
    file_path = safe_path(path)

    if not file_path.exists():
        return {"ok": False, "error": "File does not exist."}

    if not file_path.is_file():
        return {"ok": False, "error": "Path is not a file."}

    content = file_path.read_text(encoding="utf-8")

    return {"ok": True, "content": content}


def write_file(path: str, content: str) -> dict:
    file_path = safe_path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    return {"ok": True, "path": str(file_path)}


def edit_file(path: str, old_text: str, new_text: str) -> dict:
    file_path = safe_path(path)

    if not file_path.exists():
        return {"ok": False, "error": "File does not exist."}

    if not file_path.is_file():
        return {"ok": False, "error": "Path is not a file."}

    content = file_path.read_text(encoding="utf-8")

    if old_text not in content:
        return {"ok": False, "error": "old_text was not found in file."}

    content = content.replace(old_text, new_text, 1)
    file_path.write_text(content, encoding="utf-8")

    return {"ok": True, "path": str(file_path)}


def apply_patch(path: str, replacements: list[dict[str, str]]) -> dict:
    file_path = safe_path(path)

    if not file_path.exists():
        return {"ok": False, "error": "File does not exist."}

    if not file_path.is_file():
        return {"ok": False, "error": "Path is not a file."}

    content = file_path.read_text(encoding="utf-8")

    for replacement in replacements:
        old = replacement["old"]
        new = replacement["new"]

        if old not in content:
            return {
                "ok": False,
                "error": f"Could not find text to replace: {old}",
            }

        content = content.replace(old, new, 1)

    file_path.write_text(content, encoding="utf-8")

    return {"ok": True, "path": str(file_path)}


def ask_user_approval(action: str) -> dict:
    print("\nApproval required:")
    print(action)

    answer = input("Approve? yes/no: ").strip().lower()

    return {
        "ok": answer in ["yes", "y"],
        "approved": answer in ["yes", "y"],
    }