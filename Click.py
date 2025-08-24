from dash import html
import json


def node_clicked(node_data, all_nodes=None):
    """Return a details panel for a clicked node with collapsible sections.
    - Content: only if there is meaningful content (not empty/only N/A)
    - Connections: always included, with counts and clickable items
    - Raw JSON: only if raw exists and is non-empty
    """
    if not node_data:
        return [html.P("Click on a node to see details here.")]

    print(f"Node clicked: {node_data}")

    node_class = node_data.get('class', 'N/A')
    content = node_data.get('content')

    # Helper to determine if there is meaningful content to show
    def has_meaningful_content(n_class, cont):
        if cont is None:
            return False
        if n_class == "MessageConfig" and isinstance(cont, (list, tuple)) and len(cont) >= 3:
            body, subject, notification = cont[0], cont[1], cont[2]
            return any((isinstance(x, str) and x.strip()) or (x is not None and not isinstance(x, str)) for x in (body, subject, notification))
        if n_class == "Incentive" and isinstance(cont, (list, tuple)) and len(cont) >= 2:
            return any((isinstance(x, str) and x.strip()) or (x is not None and not isinstance(x, str)) for x in (cont[0], cont[1]))
        if n_class == "CustomFieldDef" and isinstance(cont, (list, tuple)) and len(cont) >= 3:
            return any((isinstance(x, str) and x.strip()) or (x is not None and not isinstance(x, str)) for x in (cont[0], cont[1], cont[2]))
        if n_class == "ClientPageLayout":
            return bool(str(cont or "").strip())
        if isinstance(cont, (list, tuple)):
            return any(str(x).strip() for x in cont if x is not None)
        return bool(str(cont).strip())

    show_content_section = has_meaningful_content(node_class, content)

    # Prepare content body based on node type (only if meaningful)
    content_children = []
    if show_content_section:
        if node_class == "MessageConfig" and isinstance(content, (list, tuple)) and len(content) >= 3:
            body = content[0] if content[0] is not None else 'N/A'
            subject = content[1] if content[1] is not None else 'N/A'
            notification = content[2] if content[2] is not None else 'N/A'
            content_children = [
                html.Div([
                    html.P("Subject:"),
                    html.Pre(str(subject), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ]),
                html.Div([
                    html.P("Notification Text:"),
                    html.Pre(str(notification), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ]),
                html.Div([
                    html.P("Body:"),
                    html.Pre(str(body), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ])
            ]
        elif node_class == "Incentive" and isinstance(content, (list, tuple)) and len(content) >= 2:
            content_children = [
                html.Div([
                    html.P("Incentive Name::"),
                    html.Pre(str(content[0] if content[0] is not None else ''),
                             style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ]),
                html.Div([
                    html.P("Info:"),
                    html.Pre(str(content[1] if content[1] is not None else ''), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ])
            ]
        elif node_class == "CustomFieldDef" and isinstance(content, (list, tuple)) and len(content) >= 3:
            content_children = [
                html.P(f"Field Type: {content[0] if content[0] is not None else 'N/A'}"),
                html.P(f"Data Type: {content[1] if content[1] is not None else 'N/A'}"),
                html.P(f"Default: {content[2] if content[2] is not None else 'N/A'}"),
            ]
        elif node_class == "ClientPageLayout":
            content_children = [
                html.Div([
                    html.P("HTML Content:"),
                    html.Pre(str(content or ''), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})
                ])
            ]
        else:
            if isinstance(content, (list, tuple)):
                items = [str(part) for part in content if str(part).strip()]
                content_children = [html.P(x) for x in items]
            else:
                content_children = [html.Pre(str(content), style={"whiteSpace": "pre-wrap", "overflowX": "auto"})]

    # Prepare connections section
    outgoing_refs = node_data.get('connections', []) or []

    def make_node_item(name, display):
        return html.Li(
            html.Button(
                display,
                id={"type": "node-link", "name": name},
                n_clicks=0,
                title=name,
                style={
                    "background": "none",
                    "border": "none",
                    "padding": 0,
                    "margin": 0,
                    "color": "#0b67c1",
                    "textDecoration": "underline",
                    "cursor": "pointer",
                    "font": "inherit"
                }
            )
        )

    outgoing_items = [make_node_item(ref, ref) for ref in outgoing_refs]

    incoming_items = []
    if all_nodes:
        seen = set()
        for n in all_nodes:
            for ref in (n.get('connections', []) or []):
                if ref == node_data.get('name') and n['name'] not in seen:
                    seen.add(n['name'])
                    incoming_items.append(make_node_item(n['name'], n['name']))

    # Summary with counts
    summary_label = f"Connections ({len(outgoing_items)} out, {len(incoming_items)} in)"

    if node_data.get('order') == 'secondary':
        disclosure = " **"
    else:
        disclosure = ""

    connections_section = html.Details([
        html.Summary(summary_label),
        html.Div([
            html.P(f"Refers To ({len(outgoing_items)}){disclosure}:"),
            html.Ul(outgoing_items) if outgoing_items else html.P("None"),
            html.P(f"Referred By ({len(incoming_items)})*:"),
            html.Ul(incoming_items) if incoming_items else html.P("None"),
        ])
    ], open=False)

    # Raw JSON section (collapsible) - include only if raw present and non-empty
    raw_obj = node_data.get('raw')
    show_raw_section = raw_obj is not None and bool(raw_obj)
    raw_section = None
    if show_raw_section:
        try:
            raw_pretty = json.dumps(raw_obj, indent=2, default=str)
        except Exception:
            raw_pretty = str(raw_obj)
        raw_section = html.Details([
            html.Summary("Raw JSON"),
            html.Div([
                html.Pre(raw_pretty, style={"whiteSpace": "pre-wrap", "overflowX": "auto", "maxHeight": "300px"})
            ])
        ], open=False)

    # Assemble details with conditional sections
    name_suffix = " **" if node_data.get('order') == 'secondary' else ""

    details = [
        html.P(f"Name: {node_data.get('name', 'N/A')}{name_suffix}"),
        html.P(f"Display Name: {node_data.get('display_name', 'N/A')}"),
        html.P(f"Type: {node_data.get('class', 'N/A')}"),
        html.P(f"Program: {node_data.get('program', 'N/A')}"),
        html.P(f"Includes Query: {node_data.get('query', 'N/A')}"),
    ]

    # Only include Content if we have meaningful content (not empty/only N/A)
    if show_content_section and content_children:
        details.append(html.Details([
            html.Summary("Content"),
            html.Div(content_children)
        ], open=False))

    # Connections are always included
    details.append(connections_section)

    # Only include Raw JSON if present
    if raw_section is not None:
        details.append(raw_section)

    return details
