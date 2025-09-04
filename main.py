# There are four goals for this code:
# 1.) Download the Configuration Snapshot for a specified client or library with Selenium
# 2.) Parse the JSON files to extract the network graph data using plotly
# 3.) Create a network graph using plotly
# 4.) Display the network graph with DASH

import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, ALL, State
from flask import Flask
import Graph
from Click import node_clicked
from Content import download_message_content_as_csv, download_incentive_content_as_csv, \
    download_client_custom_fields_content_as_csv, download_client_page_layout_content_as_csv
from Nodes import find_nodes, create_secondary_nodes
import json


def main():
    # Check if Snapshots directory exists, create if not
    if not os.path.exists("Snapshots"):
        os.makedirs("Snapshots")

    if not os.path.exists("Content"):
        os.makedirs("Content")

    # Print absolute locations to help users place files
    snapshots_abs = os.path.abspath("Snapshots")
    content_abs = os.path.abspath("Content")
    print(f"Snapshots folder: {snapshots_abs}")
    print(f"Content folder:   {content_abs}")
    print("To add a new snapshot, create a subfolder under the Snapshots folder and put your .json files inside it.")

    # Get list of existing snapshots
    snapshots = [d for d in os.listdir("Snapshots") if os.path.isdir(os.path.join("Snapshots", d))]

    # Create the Dash application
    server = Flask(__name__)
    app = dash.Dash(
        __name__,
        server=server,
        assets_folder=os.path.join(os.path.dirname(__file__), 'Styling', 'CSS'),
        suppress_callback_exceptions=True
    )

    class_names = [
        "MessageConfig","ClientTopic","StandaloneFormula","ClientPageLayout",
        "CustomFieldDef","ClientProgram","MessageCategory","Incentive","Rule","RuleSet", "ClientRaffle",
        "ClientReward","ClientTaskHandlerDefinition"
    ]

    class_options = [
        {"label": html.Span(name, className=f"label-{name}"), "value": name}
        for name in class_names
    ]

    # --- Page Layouts ---
    def home_layout():
        return html.Div([
            html.Div([
                html.H1("MHC Configuration Visualization Tool"),
                html.P("By Alex Habegger - GitHub: @ahabegger")
            ], className="header-card"),

            html.Details([
                html.Summary("How to Add Snapshots", className="filter-summary"),
                html.Div([
                    html.P("Where to add new snapshots:", className="helper-text"),
                    html.P("Place JSON files under this folder (one subfolder per snapshot):"),
                    html.P(["Snapshots folder: ", html.Code(snapshots_abs)]),
                    html.P("After adding a folder, click 'Refresh Snapshot List' to see it in the dropdown."),
                    html.P(["Content folder (CSV exports): ", html.Code(content_abs)])
                ], className="status-box")
            ], open=False, className="filter-section"),

            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id="snapshot-dropdown",
                        options=[{"label": s, "value": s} for s in snapshots],
                        placeholder="Select a snapshot to view",
                        value=snapshots[0] if snapshots else None,
                        className="snapshot-dropdown"
                    ),
                    html.Button("Refresh Snapshot List", id="refresh-button", className="btn btn-secondary"),
                    html.Button("Refresh Graph", id="refresh-graph-button", className="btn btn-message"),
                    dcc.Link("Compare Snapshots →", href="/compare", className="btn btn-secondary", id="go-compare-link")
                ], className="controls-row"),

                # Collapsible filter section - classes
                html.Details([
                    html.Summary("Filter By Element", className="filter-summary"),
                    dcc.Checklist(
                        id="class-filter",
                        options=class_options,
                        value=class_names,
                        className="checklist"
                    )
                ], open=False, className="filter-section"),

                # Collapsible filter section - programs
                html.Details([
                    html.Summary("Filter By Program", className="filter-summary"),
                    dcc.Checklist(
                        id="program-filter",
                        options=[],  # populated dynamically based on selected snapshot
                        value=[],    # default to all programs in snapshot via callback
                        className="checklist"
                    )
                ], open=False, className="filter-section"),

                # Collapsible filter section - search by node name
                html.Details([
                    html.Summary("Filter By Search", className="filter-summary"),
                    html.Div([
                        html.Span("🔎", className="search-icon"),
                        dcc.Input(
                            id="search-filter",
                            type="text",
                            placeholder="Type to include nodes whose name contains...",
                            value="",
                            debounce=True,
                            className="search-input"
                        ),
                        html.Button("Reset", id="reset-search-button", title="Clear search", className="search-reset-btn")
                    ], className="search-input-wrapper")
                ], open=False, className="filter-section"),

                # New: Highlight section - search within raw JSON
                html.Details([
                    html.Summary("Highlight By Search In JSON", className="filter-summary"),
                    html.Div([
                        html.Span("🧩", className="search-icon"),
                        dcc.Input(
                            id="json-highlight",
                            type="text",
                            placeholder="Highlight nodes whose raw JSON contains...",
                            value="",
                            debounce=True,
                            className="search-input"
                        ),
                        html.Button("Reset", id="reset-json-highlight", title="Clear JSON highlight", className="search-reset-btn")
                    ], className="search-input-wrapper"),
                    html.Div([
                        html.P("Enter a Regular Expression (case-insensitive) to test against each node's raw JSON.", className="helper-text"),
                        html.P("For help with Regular Expressions, see https://regex101.com/ or https://regexr.com/ of use ChatGPT to generate patterns.", className="helper-text"),
                        html.P("Border colors: Green = matches, Red = does not match, Black = not applicable (no JSON).", className="helper-note"),
                        html.P("If both highlight fields are used, a node must match all provided patterns to be green.", className="helper-note"),
                        html.P(" ", className="helper-note"),  # Extra space
                        html.P("Outline Legend:", style={'fontWeight': '600', 'marginRight': '8px'}),
                        html.P([
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #2ecc71', 'marginRight': '6px'}),
                            html.Span("Match", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #e74c3c', 'marginRight': '6px'}),
                            html.Span("No match", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #000000', 'marginRight': '6px'}),
                            html.Span("N/A", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '2px solid #ffffff', 'boxShadow': '0 0 0 1px #ccc inset', 'marginRight': '6px'}),
                            html.Span("Default", className="helper-note"),
                        ], className="legend-row", style={'display': 'flex', 'alignItems': 'center', 'gap': '2px', 'margin': '6px 0 10px'})
                    ])
                ], open=False, className="filter-section"),

                # New: Highlight section - search within extracted content
                html.Details([
                    html.Summary("Highlight By Search in Content", className="filter-summary"),
                    html.Div([
                        html.Span("✨", className="search-icon"),
                        dcc.Input(
                            id="content-highlight",
                            type="text",
                            placeholder="Highlight nodes whose extracted content contains...",
                            value="",
                            debounce=True,
                            className="search-input"
                        ),
                        html.Button("Reset", id="reset-content-highlight", title="Clear Content highlight", className="search-reset-btn")
                    ], className="search-input-wrapper"),
                    html.Div([
                        html.P("Enter a Regular Expression (case-insensitive) to test against extracted node content (e.g., message bodies, field defaults, HTML blocks).", className="helper-text"),
                        html.P("For help with Regular Expressions, see https://regex101.com/ or https://regexr.com/ of use ChatGPT to generate patterns.", className="helper-text"),
                        html.P("Border colors: Green = matches, Red = does not match, Black = not applicable (no or empty content).", className="helper-note"),
                        html.P("If both highlight fields are used, a node must match all provided patterns to be green.", className="helper-note"),
                        html.P(" ", className="helper-note"),  # Extra space
                        html.P("Outline Legend:", style={'fontWeight': '600', 'marginRight': '8px'}),
                        html.P([
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #2ecc71', 'marginRight': '6px'}),
                            html.Span("Match", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #e74c3c', 'marginRight': '6px'}),
                            html.Span("No match", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #000000', 'marginRight': '6px'}),
                            html.Span("N/A", className="helper-note", style={'marginRight': '12px'}),
                            html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '2px solid #ffffff', 'boxShadow': '0 0 0 1px #ccc inset', 'marginRight': '6px'}),
                            html.Span("Default", className="helper-note"),
                        ], className="legend-row", style={'display': 'flex', 'alignItems': 'center', 'gap': '2px', 'margin': '6px 0 10px'})
                    ])
                ], open=False, className="filter-section"),


                dcc.Graph(id="network-graph", className="network-graph"),
                # Add this div to display clicked node information
                html.Div(id="node-info", className="node-info-box")
            ], className="panel-box"),

            html.H3("* = Elements could be referrenced by non-uploaded elements or by queries"),
            html.H3("** = Implied elements created to represent references to non-uploaded elements (missing context)"),
            html.Div([
                html.Button("Download Incentive Content", id="download-incentive-button",
                            title="Export Incentive content to CSV", className="btn btn-incentive"),
                html.Button("Download Message Content", id="download-message-button",
                            title="Export Message content to CSV", className="btn btn-message"),
                html.Button("Download Custom Fields Content", id="download-custom-fields-button",
                            title="Export Custom Field definitions to CSV", className="btn btn-custom"),
                html.Button("Download Page Layout Content***", id="download-page-layout-button",
                            title="Export Page Layout HTML content to CSV", className="btn btn-layout")
            ], className="buttons-row"),

            # Download status box (below the buttons)
            dcc.Loading(
                id="download-loading",
                type="default",
                color="#999",
                children=html.Div(id="download-status", className="status-box")
            ),

            html.Div("*** = Only downloads HTML Elements from page layouts", className="footnote")
        ], className="app-container")

    def compare_layout():
        # Rebuild snapshots list to reflect latest
        current_snapshots = [d for d in os.listdir("Snapshots") if os.path.isdir(os.path.join("Snapshots", d))]
        return html.Div([
            html.Div([
                html.H1("Compare Snapshots"),
                html.P("Select two snapshots to compare their configuration graphs side-by-side."),
                dcc.Link("← Back to Graph", href="/", className="btn btn-secondary")
            ], className="header-card"),

            # Compare legend
            html.Div([
                html.Span("Outline Legend:", style={'fontWeight': '600', 'marginRight': '8px'}),
                html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #000000', 'marginRight': '6px'}),
                html.Span("Same", className="helper-note", style={'marginRight': '12px'}),
                html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #f39c12', 'marginRight': '6px'}),
                html.Span("Changed", className="helper-note", style={'marginRight': '12px'}),
                html.Span(" ", style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'borderRadius': '50%', 'backgroundColor': '#ddd', 'border': '3px solid #e74c3c', 'marginRight': '6px'}),
                html.Span("Distinct", className="helper-note"),
            ], className="legend-row", style={'display': 'flex', 'alignItems': 'center', 'gap': '2px', 'margin': '0 0 10px'}),

            # Controls row with snapshot selectors
            html.Div([
                html.Div([
                    html.Label("Snapshot A"),
                    dcc.Dropdown(
                        id="compare-snapshot-a",
                        options=[{"label": s, "value": s} for s in current_snapshots],
                        value=(current_snapshots[0] if current_snapshots else None),
                        placeholder="Select Snapshot A",
                        className="snapshot-dropdown"
                    )
                ], className="compare-picker"),
                html.Div([
                    html.Label("Snapshot B"),
                    dcc.Dropdown(
                        id="compare-snapshot-b",
                        options=[{"label": s, "value": s} for s in current_snapshots],
                        value=(current_snapshots[1] if current_snapshots and len(current_snapshots) > 1 else (current_snapshots[0] if current_snapshots else None)),
                        placeholder="Select Snapshot B",
                        className="snapshot-dropdown"
                    )
                ], className="compare-picker"),
                html.Button("Refresh Snapshot List", id="compare-refresh-button", className="btn btn-secondary"),
                html.Button("Compare", id="compare-run-button", className="btn btn-message")
            ], className="controls-row"),

            html.Div([
                html.Div([
                    html.H2("Snapshot A"),
                    dcc.Graph(id="compare-graph-a", className="network-graph")
                ], className="panel-box"),
                html.Div([
                    html.H2("Snapshot B"),
                    dcc.Graph(id="compare-graph-b", className="network-graph")
                ], className="panel-box")
            ], className="two-col"),

            html.H1("Differences"),
            html.Div(id="compare-diff")
        ], className="app-container")

    # Provide a validation layout that includes all components from all pages
    app.validation_layout = html.Div([
        dcc.Location(id='url'),
        home_layout(),
        compare_layout()
    ])

    # Router
    app.layout = html.Div([
        dcc.Location(id='url'),
        html.Div(id='page-content')
    ])

    @app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
    def display_page(pathname):
        if pathname == '/compare':
            return compare_layout()
        return home_layout()

    # Populate program filter options and defaults when snapshot changes
    @app.callback(
        [Output("program-filter", "options"), Output("program-filter", "value")],
        Input("snapshot-dropdown", "value")
    )
    def populate_program_filter(selected_snapshot):
        if not selected_snapshot:
            return [], []
        try:
            snapshot_folder = os.path.join("Snapshots", selected_snapshot)
            json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
            nodes = find_nodes(json_files, snapshot_folder)
            nodes = create_secondary_nodes(nodes)
            programs = sorted({n.get('program') for n in nodes if n.get('program')})
            options = [{"label": p, "value": p} for p in programs]
            return options, programs
        except Exception as e:
            print(f"Error populating program filter: {e}")
            return [], []

    # Update the graph based on filters
    @app.callback(
        Output("network-graph", "figure"),
        [Input("snapshot-dropdown", "value"), Input("class-filter", "value"), Input("program-filter", "value"), Input("search-filter", "value"), Input("json-highlight", "value"), Input("content-highlight", "value")]
    )
    def update_graph(selected_snapshot, included_classes, included_programs, search_text, json_highlight, content_highlight):
        if not selected_snapshot:
            return {}
        try:
            return Graph.create_network_graph(
                selected_snapshot,
                include_classes=included_classes,
                include_programs=included_programs,
                name_contains=(search_text or None),
                highlight_json_contains=(json_highlight or None),
                highlight_content_contains=(content_highlight or None)
            )
        except Exception as e:
            print(f"Error creating graph: {e}")
            return {}

    @app.callback(
        Output("snapshot-dropdown", "options"),
        Input("refresh-button", "n_clicks")
    )
    def refresh_snapshots(n_clicks):
        snapshots = [d for d in os.listdir("Snapshots") if os.path.isdir(os.path.join("Snapshots", d))]
        return [{"label": s, "value": s} for s in snapshots]

    # Reset search filter
    @app.callback(
        Output("search-filter", "value"),
        Input("reset-search-button", "n_clicks")
    )
    def reset_search(n_clicks):
        if n_clicks:
            return ""
        return dash.no_update

    # Reset JSON highlight
    @app.callback(
        Output("json-highlight", "value"),
        Input("reset-json-highlight", "n_clicks")
    )
    def reset_json_highlight(n_clicks):
        if n_clicks:
            return ""
        return dash.no_update

    # Reset Content highlight
    @app.callback(
        Output("content-highlight", "value"),
        Input("reset-content-highlight", "n_clicks")
    )
    def reset_content_highlight(n_clicks):
        if n_clicks:
            return ""
        return dash.no_update

    # Unified download handler that also updates the status box
    @app.callback(
        [
            Output("download-incentive-button", "n_clicks"),
            Output("download-message-button", "n_clicks"),
            Output("download-custom-fields-button", "n_clicks"),
            Output("download-page-layout-button", "n_clicks"),
            Output("download-status", "children"),
        ],
        [
            Input("download-incentive-button", "n_clicks"),
            Input("download-message-button", "n_clicks"),
            Input("download-custom-fields-button", "n_clicks"),
            Input("download-page-layout-button", "n_clicks"),
        ],
        State("snapshot-dropdown", "value")
    )
    def handle_downloads(inc_clicks, msg_clicks, cf_clicks, pl_clicks, selected_snapshot):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Default returns: no updates + empty status
        reset_vals = [dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        status = ""

        if not selected_snapshot:
            status = "Please select a snapshot before downloading."
            return reset_vals[0], reset_vals[1], reset_vals[2], reset_vals[3], status

        try:
            if trigger_id == "download-incentive-button" and inc_clicks:
                status = download_incentive_content_as_csv(inc_clicks, selected_snapshot) or ""
                reset_vals[0] = None
            elif trigger_id == "download-message-button" and msg_clicks:
                status = download_message_content_as_csv(msg_clicks, selected_snapshot) or ""
                reset_vals[1] = None
            elif trigger_id == "download-custom-fields-button" and cf_clicks:
                status = download_client_custom_fields_content_as_csv(cf_clicks, selected_snapshot) or ""
                reset_vals[2] = None
            elif trigger_id == "download-page-layout-button" and pl_clicks:
                status = download_client_page_layout_content_as_csv(pl_clicks, selected_snapshot) or ""
                reset_vals[3] = None
        except Exception as e:
            status = f"Error during download: {e}"

        return reset_vals[0], reset_vals[1], reset_vals[2], reset_vals[3], status

    @app.callback(
        Output("node-info", "children"),
        [
            Input("network-graph", "clickData"),
            Input({"type": "node-link", "name": ALL}, "n_clicks"),
            Input("snapshot-dropdown", "value"),
        ]
    )
    def display_clicked_node_info(clickData, node_link_clicks, selected_snapshot):
        if not selected_snapshot:
            return html.Div("Click a node to see details", className="muted-text")

        # Determine what triggered the callback
        ctx = dash.callback_context
        triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        try:
            snapshot_folder = os.path.join("Snapshots", selected_snapshot)
            json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
            nodes = find_nodes(json_files, snapshot_folder)
            nodes = create_secondary_nodes(nodes)

            # If a connection link button was clicked
            if triggered and triggered.startswith("{"):
                try:
                    trig_id = json.loads(triggered)
                    if isinstance(trig_id, dict) and trig_id.get("type") == "node-link":
                        clicked_node = trig_id.get("name")
                        node_details = next((n for n in nodes if n['name'] == clicked_node), None)
                        if node_details:
                            return node_clicked(node_details, nodes)
                except Exception:
                    pass

            # Fallback to graph click handling
            if clickData and 'points' in clickData:
                point = clickData['points'][0]
                if 'customdata' in point:
                    clicked_node = point['customdata']
                    node_details = next((n for n in nodes if n['name'] == clicked_node), None)
                    if node_details:
                        return node_clicked(node_details, nodes)

            return html.Div("Click a node to see details", className="muted-text")

        except Exception as e:
            return html.Div(f"Error loading node details: {str(e)}")

    # --- Compare page callbacks ---
    from Compare import build_compare

    @app.callback(
        [Output("compare-graph-a", "figure"), Output("compare-graph-b", "figure"), Output("compare-diff", "children"), Output("compare-snapshot-a", "options"), Output("compare-snapshot-b", "options")],
        [Input("compare-snapshot-a", "value"), Input("compare-snapshot-b", "value"), Input("compare-refresh-button", "n_clicks"), Input("compare-run-button", "n_clicks")]
    )
    def update_compare(a, b, _refresh_clicks, _run_clicks):
        # keep snapshot options fresh
        snaps = [d for d in os.listdir("Snapshots") if os.path.isdir(os.path.join("Snapshots", d))]
        options = [{"label": s, "value": s} for s in snaps]
        if not a or not b or a == b:
            # Empty figures and guidance when invalid selection
            msg = "Select two different snapshots to compare."
            empty = {"data": [], "layout": {"title": msg}}
            return empty, empty, html.Div(msg, className="muted-text"), options, options
        try:
            fig_a, fig_b, diff_children = build_compare(a, b)
            return fig_a, fig_b, diff_children, options, options
        except Exception as e:
            err = html.Div(f"Error comparing snapshots: {e}")
            empty = {"data": [], "layout": {"title": "Error"}}
            return empty, empty, err, options, options

    return app


if __name__ == "__main__":
    app = main()
    app.run(debug=True)
