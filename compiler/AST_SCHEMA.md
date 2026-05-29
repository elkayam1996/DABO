# DABO AST Schema v0.4 — Short Version

This is the compact AST schema reference.

The AST says **what should happen**.  
Runtime records/logs say **what actually happened**.

---

## AST Schema With Field Explanations

```json
{
  "ast_version": "0.4",                 // Schema version. Validator should check this.

  "mission": "string",                  // The full goal for the local executor.

  "nodes": [                            // List of all plan nodes.
    {
      "id": "string",                   // Unique node id. Examples: "1", "1.1", "2.3.1".

      "node_type": "ACTION | GROUP | VERIFY | APPROVAL",
                                         // ACTION: local LLM performs one atomic task.
                                         // GROUP: runtime controls child nodes.
                                         // VERIFY: local LLM checks previous work.
                                         // APPROVAL: ask user before risky action.

      "title": "string",                // Short readable node name for logs/UI.

      "task": {
        "objective": "string",          // Atomic goal of this node.
        "steps": [],                    // Concrete steps for local LLM to follow.
        "constraints": []               // Rules/limits for this node.
      },

      "depends_on": [],                 // Node ids that must finish before this node runs.

      "execution": {
        "mode": "ATOMIC | SEQUENCE | PARALLEL | IF | FORALL"
                                         // ATOMIC: run this node once.
                                         // SEQUENCE: run children in order.
                                         // PARALLEL: children are independent.
                                         // IF: choose then/else branch.
                                         // FORALL: loop over a collection.
      },

      "inputs": [],                     // Data this node needs from previous results,
                                         // mission, loop item, constants, or user.

      "suggested_tools": [],            // Recommended tools. Not a restriction.
                                         // Local LLM still receives all available tools.

      "result": {
        "key": "string_or_null",        // Where to save this node result in result_store.
        "description": "string",        // What the result should contain.
        "must_include": []              // Required content in the result.
      },

      "success": []                     // Conditions that mean this node is complete.
    }
  ]
}
```

---

## Execution Mode Shapes

Use the matching shape inside `execution`.

### ATOMIC

Used for `ACTION`, `VERIFY`, and `APPROVAL`.

```json
{
  "mode": "ATOMIC"
}
```

Meaning: runtime sends this one node to the local LLM.

---

### SEQUENCE

Used for `GROUP`.

```json
{
  "mode": "SEQUENCE",
  "children": ["1.1", "1.2", "1.3"]
}
```

Meaning: run children one after another.

---

### PARALLEL

Used for `GROUP`.

```json
{
  "mode": "PARALLEL",
  "children": ["2.1", "2.2"]
}
```

Meaning: children do not depend on each other. MVP can still run them one by one.

---

### IF

Used for `GROUP`.

```json
{
  "mode": "IF",
  "condition": "app_run_result.returncode != 0",
  "then": ["3.1"],
  "else": ["3.2"]
}
```

Meaning: if condition is true, run `then`; otherwise run `else`.

---

### FORALL

Used for `GROUP`.

```json
{
  "mode": "FORALL",
  "item": "file",
  "collection": "python_files",
  "do": ["4.1"]
}
```

Meaning: for every item in `python_files`, bind it as `file`, then run nodes in `do`.

---

## Input Shape

```json
{
  "name": "string",                     // Local name for this input inside the node.
  "source": "NODE_RESULT | MISSION | LOOP_ITEM | CONSTANT | USER",
                                         // NODE_RESULT: output from previous node.
                                         // MISSION: root mission string.
                                         // LOOP_ITEM: current FORALL item.
                                         // CONSTANT: fixed value inside AST.
                                         // USER: user-provided value.

  "from_node": "string_or_null",        // Node that produced this input, if relevant.
  "key": "string",                      // Result key / mission key / constant key.
  "value": null                         // Only used for CONSTANT input.
}
```

Example:

```json
{
  "name": "created_app_files",
  "source": "NODE_RESULT",
  "from_node": "1",
  "key": "created_app_files",
  "value": null
}
```

---

## Important Rules

```text
1. Runtime walks the AST. Local LLM does not decide global order.
2. Local LLM executes one ATOMIC node at a time.
3. ACTION / VERIFY / APPROVAL should use ATOMIC.
4. GROUP should use SEQUENCE / PARALLEL / IF / FORALL.
5. suggested_tools are recommendations only.
6. AST does not store dynamic runtime facts like exact created files unless already known.
7. Dynamic outputs are saved after execution in runtime records.
8. result.key is how later nodes find previous outputs.
9. success is the only completion contract for the node.
```

---

## Minimal Example

```json
{
  "ast_version": "0.4",
  "mission": "Create a small local todo app.",
  "nodes": [
    {
      "id": "1",
      "node_type": "ACTION",
      "title": "Create app files",
      "task": {
        "objective": "Create the initial files for a simple local todo app.",
        "steps": [
          "Choose a simple file structure.",
          "Create the needed Python files.",
          "Report every created file path in the result."
        ],
        "constraints": [
          "Do not create files outside the project folder."
        ]
      },
      "depends_on": [],
      "execution": {
        "mode": "ATOMIC"
      },
      "inputs": [
        {
          "name": "target_folder",
          "source": "CONSTANT",
          "from_node": null,
          "key": "target_folder",
          "value": "todo_app"
        }
      ],
      "suggested_tools": ["write_file"],
      "result": {
        "key": "created_app_files",
        "description": "A report of all files created for the app.",
        "must_include": [
          "created file paths",
          "main entry file path"
        ]
      },
      "success": [
        "At least one app file was created.",
        "The result reports every created file path.",
        "The result identifies the main entry file."
      ]
    }
  ]
}
```
