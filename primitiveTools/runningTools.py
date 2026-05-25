import subprocess
def run_python(path: str) -> dict:
    file_path = safe_path(path)

    if not file_path.exists():
        return {"ok": False, "error": "Python file does not exist."}

    result = subprocess.run(
        ["python", str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }
