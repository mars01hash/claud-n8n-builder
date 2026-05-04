#!/usr/bin/env python3
"""
extract_workflow.py
Parses an n8n workflow.json and outputs:
  - Individual node JSON files → nodes/{node_name}.json
  - Per-node guide stubs     → nodes/{node_name}.guide.md
  - A workflow summary       → stdout or --summary-file

Usage:
    python extract_workflow.py --input workflow.json --output-dir nodes/
    python extract_workflow.py --input workflow.json --output-dir nodes/ --summary-file summary.md
    python extract_workflow.py --input workflow.json --list-nodes
    python extract_workflow.py --input workflow.json --get-node "Fetch User from Postgres"
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime


def slugify(name: str) -> str:
    """Convert a node name to a safe filename slug."""
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    return s


def describe_node_io(node: dict) -> tuple[str, str]:
    """Produce human-readable input/output descriptions based on node type."""
    ntype = node.get("type", "")
    params = node.get("parameters", {})

    input_desc = "Standard n8n items from the previous node."
    output_desc = "Standard n8n items passed to the next node."

    if "webhook" in ntype:
        method = params.get("httpMethod", "POST")
        path = params.get("path", "/")
        input_desc = f"HTTP {method} request to `/{path}` — body/query/headers available via `$json`."
        output_desc = "Parsed request data: `$json.body`, `$json.query`, `$json.headers`."

    elif "httpRequest" in ntype:
        method = params.get("method", "GET")
        url = params.get("url", "")
        input_desc = f"Items from previous node. URL: `{url}` (method: {method})."
        output_desc = "Response JSON or binary from the HTTP call."

    elif ntype.endswith(".set"):
        fields = params.get("fields", {}).get("values", [])
        field_names = [f.get("name", "") for f in fields]
        output_desc = f"Items with new/overwritten fields: {', '.join(f'`{n}`' for n in field_names)}."

    elif ntype.endswith(".if"):
        output_desc = "`main[0]` = true branch items. `main[1]` = false branch items."

    elif ntype.endswith(".switch"):
        output_desc = "Multiple output branches based on matched rules."

    elif ntype.endswith(".code"):
        mode = params.get("mode", "runOnceForAllItems")
        input_desc = (
            "All items via `$input.all()` (runOnceForAllItems mode)."
            if mode == "runOnceForAllItems"
            else "Current item via `$input.item` (runOnceForEachItem mode)."
        )
        output_desc = "Items returned from the JavaScript/Python code block."

    elif ntype.endswith(".postgres"):
        op = params.get("operation", "select")
        table = params.get("table", {})
        table_name = table.get("value", "") if isinstance(table, dict) else table
        input_desc = f"Items to use for Postgres `{op}` on table `{table_name}`."
        output_desc = f"Rows returned from Postgres `{op}` operation."

    elif ntype.endswith(".slack"):
        op = params.get("operation", "post")
        resource = params.get("resource", "message")
        input_desc = f"Items providing data for Slack `{resource}.{op}` call."
        output_desc = "Slack API response with message timestamp and channel."

    elif "manualTrigger" in ntype:
        input_desc = "N/A — this is the workflow entry point (manual execution)."
        output_desc = "Empty item `{}` passed to the first downstream node."

    elif "scheduleTrigger" in ntype:
        input_desc = "N/A — triggered by cron schedule."
        output_desc = "Timestamp item with execution metadata."

    return input_desc, output_desc


def extract_expressions(node: dict) -> list[str]:
    """Find all {{ }} expressions used in the node's parameters."""
    params_str = json.dumps(node.get("parameters", {}))
    return re.findall(r'\{\{.*?\}\}', params_str)


def build_node_guide(node: dict, connections: dict) -> str:
    """Generate a guide.md for a single node."""
    name = node.get("name", "Unknown")
    ntype = node.get("type", "")
    tv = node.get("typeVersion", "?")
    params = node.get("parameters", {})
    creds = node.get("credentials", {})

    input_desc, output_desc = describe_node_io(node)
    expressions = extract_expressions(node)

    # Find what this node connects to
    outgoing = []
    if name in connections:
        for port_idx, port in enumerate(connections[name].get("main", [])):
            for edge in port:
                outgoing.append(f"`{edge['node']}` (port {port_idx})")

    # Find what connects to this node
    incoming = []
    for src, conn_data in connections.items():
        for port in conn_data.get("main", []):
            for edge in port:
                if edge.get("node") == name:
                    incoming.append(f"`{src}`")

    params_table = ""
    if isinstance(params, dict):
        rows = []
        for k, v in params.items():
            val_str = json.dumps(v) if not isinstance(v, str) else v
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            rows.append(f"| `{k}` | `{val_str}` | — |")
        params_table = "\n".join(rows) if rows else "_No parameters_"

    creds_section = ""
    if creds:
        creds_section = "\n## Credentials\n"
        for cred_type, cred_info in creds.items():
            creds_section += f"- **{cred_type}**: `{cred_info.get('name', 'unnamed')}`\n"

    expressions_section = ""
    if expressions:
        expressions_section = "\n## Expressions Used\n"
        for expr in set(expressions):
            expressions_section += f"- `{expr}`\n"

    return f"""# Node: {name}

**Type:** `{ntype}`
**TypeVersion:** `{tv}`
**Disabled:** `{node.get('disabled', False)}`
**On Error:** `{node.get('onError', 'stopWorkflow')}`

## Connections
- **Incoming from:** {', '.join(incoming) if incoming else '_trigger / entry point_'}
- **Outgoing to:** {', '.join(outgoing) if outgoing else '_terminal node_'}

## Parameters

| Parameter | Value | Notes |
|---|---|---|
{params_table}
{creds_section}{expressions_section}
## Input Expected
{input_desc}

## Output Produced
{output_desc}

---
_Auto-generated by extract_workflow.py on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_
"""


def build_summary(workflow: dict) -> str:
    """Generate a workflow-level summary."""
    name = workflow.get("name", "Unnamed Workflow")
    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", {})
    settings = workflow.get("settings", {})

    trigger_nodes = [
        n for n in nodes
        if any(t in n.get("type", "") for t in ["Trigger", "webhook", "manualTrigger", "scheduleTrigger"])
    ]

    all_creds = {}
    for node in nodes:
        for cred_type, cred_info in node.get("credentials", {}).items():
            all_creds[cred_type] = cred_info.get("name", "unnamed")

    node_types = sorted({n.get("type", "").split(".")[-1] for n in nodes})

    return f"""# Workflow Summary: {name}

**Total Nodes:** {len(nodes)}
**Active:** {workflow.get('active', False)}
**Execution Order:** {settings.get('executionOrder', 'v1')}
**Version ID:** `{workflow.get('versionId', 'N/A')}`

## Triggers
{chr(10).join(f'- `{n["name"]}` (`{n["type"]}`)'  for n in trigger_nodes) or '- None found'}

## Node Types Used
{chr(10).join(f'- `{t}`' for t in node_types)}

## Credentials Required
{chr(10).join(f'- **{ct}**: {cn}' for ct, cn in all_creds.items()) or '- None'}

## Execution Flow
```
{chr(10).join(f'{src}  -->  {", ".join(e["node"] for port in data.get("main", []) for e in port)}' for src, data in connections.items())}
```

---
_Generated by extract_workflow.py on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_
"""


def main():
    parser = argparse.ArgumentParser(description="Extract and document n8n workflow nodes")
    parser.add_argument("--input", "-i", required=True, help="Path to workflow.json")
    parser.add_argument("--output-dir", "-o", type=str, default="nodes", help="Directory for node output files")
    parser.add_argument("--summary-file", "-s", type=str, help="Write workflow summary to this file")
    parser.add_argument("--list-nodes", action="store_true", help="Print node names and types only")
    parser.add_argument("--get-node", "-g", type=str, help="Extract a single node by name")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    workflow = json.loads(input_path.read_text(encoding="utf-8"))
    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", {})

    if args.list_nodes:
        print(f"Workflow: {workflow.get('name', 'Unnamed')} — {len(nodes)} nodes\n")
        for node in nodes:
            print(f"  [{node.get('typeVersion', '?')}] {node.get('name'):<40} {node.get('type')}")
        sys.exit(0)

    if args.get_node:
        target = next((n for n in nodes if n.get("name") == args.get_node), None)
        if not target:
            print(f"ERROR: Node '{args.get_node}' not found.", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(target, indent=2))
        sys.exit(0)

    # Full extraction
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for node in nodes:
        slug = slugify(node.get("name", f"node_{node.get('id', 'unknown')}"))

        # Write node JSON
        node_json_path = output_dir / f"{slug}.json"
        node_json_path.write_text(json.dumps(node, indent=2), encoding="utf-8")

        # Write node guide
        node_guide_path = output_dir / f"{slug}.guide.md"
        node_guide_path.write_text(build_node_guide(node, connections), encoding="utf-8")

        print(f"  Extracted: {node.get('name')} → {slug}.json + {slug}.guide.md")

    # Write summary
    summary = build_summary(workflow)
    if args.summary_file:
        Path(args.summary_file).write_text(summary, encoding="utf-8")
        print(f"\nSummary written to: {args.summary_file}")
    else:
        print("\n" + summary)

    print(f"\nDone. {len(nodes)} nodes extracted to '{output_dir}/'")


if __name__ == "__main__":
    main()
