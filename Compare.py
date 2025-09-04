from typing import Dict, List
import os
from dash import html
import Graph
from Nodes import find_nodes
import json as _json
import difflib


def _load_nodes(snapshot: str) -> Dict[str, dict]:
    """Load nodes for a snapshot into a dict keyed by node name."""
    folder = os.path.join("Snapshots", snapshot)
    files = [f for f in os.listdir(folder) if f.endswith('.json')]
    nodes = find_nodes(files, folder)
    by_name = {n['name']: n for n in nodes}
    return by_name


def _classify_diff(a_node: dict | None, b_node: dict | None) -> str:
    """Return 'distinct', 'same', or 'changed' comparing two node entries by name.
    Distinct: present in one side only.
    Same: present in both and JSON/primary-ness equivalent.
    Changed: present in both but JSON differs or primary/secondary status differs.
    """
    if a_node is None or b_node is None:
        return 'distinct'

    # If one is primary and the other is secondary, treat as changed
    a_primary = (a_node.get('order') == 'primary') and bool(a_node.get('json'))
    b_primary = (b_node.get('order') == 'primary') and bool(b_node.get('json'))
    if a_primary != b_primary:
        return 'changed'

    a_json = a_node.get('json') or ''
    b_json = b_node.get('json') or ''
    if a_json == b_json:
        return 'same'
    else:
        return 'changed'


def _pretty(n: str) -> str:
    try:
        # n is like <<Type:Display[ClientProgram:Program]>>
        base = n[2:].split('[', 1)[0]
        return base
    except Exception:
        return n


def _truncate_depth(val, depth: int, max_depth: int):
    """Recursively copy the structure, replacing values deeper than max_depth with a placeholder."""
    if depth >= max_depth:
        return "<… depth limit …>"
    if isinstance(val, dict):
        # keep keys sorted for stable output
        return {k: _truncate_depth(val[k], depth + 1, max_depth) for k in sorted(val.keys())}
    if isinstance(val, list):
        return [_truncate_depth(v, depth + 1, max_depth) for v in val]
    if isinstance(val, tuple):
        return tuple(_truncate_depth(v, depth + 1, max_depth) for v in val)
    return val


def _node_json_pretty(node: dict | None, max_depth: int = 10) -> str:
    if not node:
        return ""
    raw = node.get('raw')
    try:
        if raw is not None:
            truncated = _truncate_depth(raw, 0, max_depth)
            return _json.dumps(truncated, indent=2, sort_keys=True)
    except Exception:
        pass
    # fallback to whatever string we had
    val = node.get('json') or ""
    return val


def _leading_spaces(s: str) -> int:
    cnt = 0
    for ch in s:
        if ch == ' ':
            cnt += 1
        else:
            break
    return cnt


def _dedent_block(block: List[str]) -> List[str]:
    """Remove the minimum common leading spaces from non-empty lines in a block.
    Preserves relative indentation (depth) while making the block flush-left in its column.
    """
    non_empty = [ln for ln in block if ln.strip() != ""]
    if not non_empty:
        return block
    min_indent = min(_leading_spaces(ln) for ln in non_empty)
    if min_indent <= 0:
        return block
    return [ln[min_indent:] if len(ln) >= min_indent else ln for ln in block]


def _two_column_diff(a_text: str, b_text: str, left_label: str | None = None, right_label: str | None = None) -> html.Div:
    """Produce a two-column, line-based diff with red removals (left) and green additions (right).
    Changed blocks are dedented to align like prettified JSON (flush-left within each column).
    Includes optional column labels.
    """
    a_lines = a_text.splitlines()
    b_lines = b_text.splitlines()
    sm = difflib.SequenceMatcher(a=a_lines, b=b_lines)

    left_col_children: List[html.Div] = []
    right_col_children: List[html.Div] = []

    base_style = {
        'fontFamily': 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        'fontSize': '12px',
        'whiteSpace': 'pre',
        'padding': '1px 0px',
        'borderBottom': '1px solid #f0f0f0',
        'text-align': 'left'
    }
    add_style = {**base_style, 'backgroundColor': '#e6ffed', 'color': '#22863a'}  # green
    del_style = {**base_style, 'backgroundColor': '#ffeef0', 'color': '#cb2431'}  # red
    eq_style = {**base_style}
    empty_style = {**base_style, 'color': '#999'}

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            # Dedent equal blocks too for consistent left alignment
            left_block = _dedent_block(a_lines[i1:i2])
            right_block = _dedent_block(b_lines[j1:j2])
            height = max(len(left_block), len(right_block))
            for idx in range(height):
                ltxt = left_block[idx] if idx < len(left_block) else ""
                rtxt = right_block[idx] if idx < len(right_block) else ""
                left_col_children.append(html.Div(ltxt if ltxt != "" else "", style=(eq_style if ltxt != "" else empty_style)))
                right_col_children.append(html.Div(rtxt if rtxt != "" else "", style=(eq_style if rtxt != "" else empty_style)))
        elif tag == 'replace':
            # Dedent both sides to align like prettified JSON
            left_block = _dedent_block(a_lines[i1:i2])
            right_block = _dedent_block(b_lines[j1:j2])
            height = max(len(left_block), len(right_block))
            for idx in range(height):
                ltxt = left_block[idx] if idx < len(left_block) else ""
                rtxt = right_block[idx] if idx < len(right_block) else ""
                left_col_children.append(html.Div(ltxt if ltxt != "" else "", style=(del_style if ltxt != "" else empty_style)))
                right_col_children.append(html.Div(rtxt if rtxt != "" else "", style=(add_style if rtxt != "" else empty_style)))
        elif tag == 'delete':
            left_block = _dedent_block(a_lines[i1:i2])
            for k in range(len(left_block)):
                left_col_children.append(html.Div(left_block[k], style=del_style))
            for _ in range(len(left_block)):
                right_col_children.append(html.Div("", style=empty_style))
        elif tag == 'insert':
            right_block = _dedent_block(b_lines[j1:j2])
            for _ in range(len(right_block)):
                left_col_children.append(html.Div("", style=empty_style))
            for k in range(len(right_block)):
                right_col_children.append(html.Div(right_block[k], style=add_style))

    header_style = {
        'fontWeight': 600,
        'padding': '4px 0px',
        'borderBottom': '1px solid #e1e4e8',
        'backgroundColor': '#f8f9fa'
    }

    container = html.Div([
        html.Div(left_label or "Snapshot A", style=header_style),
        html.Div(right_label or "Snapshot B", style=header_style),
        html.Div(left_col_children, style={'overflowX': 'auto'}),
        html.Div(right_col_children, style={'overflowX': 'auto'})
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gridAutoRows': 'auto',
        'columnGap': '8px',
        'border': '1px solid #e1e4e8',
        'borderRadius': '6px',
        'backgroundColor': '#fff'
    })
    return container


def build_compare(snapshot_a: str, snapshot_b: str):
    """Build side-by-side compare figures and a differences list for two snapshots.

    Returns: (fig_a, fig_b, diff_children)
    - fig_a: plotly figure for snapshot A with borders colored by diff status
    - fig_b: plotly figure for snapshot B with borders colored by diff status
    - diff_children: Dash HTML children summarizing adds/removes/changes
    """
    a_nodes = _load_nodes(snapshot_a)
    b_nodes = _load_nodes(snapshot_b)

    a_names = set(a_nodes.keys())
    b_names = set(b_nodes.keys())
    all_names = sorted(a_names | b_names)

    # Build border override maps for each figure
    a_borders: Dict[str, str] = {}
    b_borders: Dict[str, str] = {}

    added_in_b: List[str] = []  # present only in B
    added_in_a: List[str] = []  # present only in A
    changed: List[str] = []  # present in both but different

    for name in all_names:
        a_node = a_nodes.get(name)
        b_node = b_nodes.get(name)
        status = _classify_diff(a_node, b_node)

        if status == 'distinct':
            if a_node and not b_node:
                a_borders[name] = 'distinct'
                added_in_a.append(name)
            elif b_node and not a_node:
                b_borders[name] = 'distinct'
                added_in_b.append(name)
            else:
                # Shouldn't happen, but default to distinct both
                a_borders[name] = 'distinct'
                b_borders[name] = 'distinct'
        elif status == 'same':
            a_borders[name] = 'same'
            b_borders[name] = 'same'
        elif status == 'changed':
            a_borders[name] = 'changed'
            b_borders[name] = 'changed'
            changed.append(name)

    # Create figures using Graph with border overrides (primary nodes only)
    fig_a = Graph.create_network_graph(snapshot_a, border_override=a_borders, include_secondary=False)
    fig_b = Graph.create_network_graph(snapshot_b, border_override=b_borders, include_secondary=False)

    # Build differences UI
    unique_to_b_section = html.Div([
        html.H2(f"Unique to {snapshot_b} (Snapshot B):"),
        html.Ul([html.Li(n) for n in added_in_b] or [html.Li("None")])
    ])

    unique_to_a_section = html.Div([
        html.H2(f"Unique to {snapshot_a} (Snapshot A):"),
        html.Ul([html.Li(n) for n in added_in_a] or [html.Li("None")])
    ])

    # Place the unique sections side-by-side in two columns (A on left, B on right)
    unique_two_col = html.Div([
        unique_to_a_section,
        unique_to_b_section
    ], className="two-col")

    # Changed section with details and two-column diff
    changed_sections: List[html.Details] = []
    for n in changed:
        a_text = _node_json_pretty(a_nodes.get(n), max_depth=10)
        b_text = _node_json_pretty(b_nodes.get(n), max_depth=10)
        details = html.Details([
            html.Summary(n),
            html.Div(_two_column_diff(a_text, b_text, left_label=f"{snapshot_a}", right_label=f"{snapshot_b}"), style={'marginTop': '6px'})
        ], open=False)
        changed_sections.append(details)

    changed_section = html.Div([
        html.H2("Changed:"),
        html.Div(changed_sections or [html.Div("None")])
    ])

    diff_children = html.Div([changed_section, unique_two_col])

    return fig_a, fig_b, diff_children
