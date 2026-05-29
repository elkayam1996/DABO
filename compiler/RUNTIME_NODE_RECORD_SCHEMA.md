# DABO Runtime Node Record Schema v0.1 — Compact

This record is created after one AST node runs.

The AST says what should happen.  
The runtime record says what actually happened.

---

## Schema

```json
{
  "node_id": "string",                  // AST node id that produced this record.

  "status": "SUCCESS | FAILED | SKIPPED",
                                         // SUCCESS: node completed.
                                         // FAILED: node ran but failed.
                                         // SKIPPED: node was not executed.

  "output_key": "string_or_null",       // Same key as AST result.key.
                                         // This is the memory name for the output.

  "output": {},                         // Actual data produced by the node.
                                         // Can include created files, modified files,
                                         // summaries, decisions, extracted data,
                                         // run results, etc.

  "errors": []                          // Error messages. Empty if success.
}
```

---

## Example

```json
{
  "node_id": "1",
  "status": "SUCCESS",
  "output_key": "created_app_files",
  "output": {
    "summary": "Created a simple todo app.",
    "entry_file": "todo_app/main.py",
    "files": [
      {
        "path": "todo_app/main.py",
        "status": "created",
        "role": "main entry file"
      },
      {
        "path": "todo_app/README.md",
        "status": "created",
        "role": "usage instructions"
      }
    ]
  },
  "errors": []
}
```

---

## How Later Nodes Use It

If a later AST node has this input:

```json
{
  "name": "created_app_files",
  "source": "NODE_RESULT",
  "from_node": "1",
  "key": "created_app_files",
  "value": null
}
```

The executor loads:

```text
node_records["1"].output
```

and passes it to the later node as:

```text
created_app_files
```

---

## Rules

```text
1. output_key = memory name.
2. output = actual data.
3. Keep output useful for future nodes.
4. Do not store debug/tool logs here.
5. Tool logs can be a separate system later.
```
