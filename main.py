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

    # Get list of existing snapshots
    snapshots = [d for d in os.listdir("Snapshots") if os.path.isdir(os.path.join("Snapshots", d))]

    # Create the Dash application
    server = Flask(__name__)
    app = dash.Dash(__name__, server=server)

    # Colors matching Graph.py
    class_colors = {
        'MessageConfig': '#1f77b4',
        'ClientTopic': '#ff7f0e',
        'StandaloneFormula': '#2ca02c',
        'ClientPageLayout': '#d62728',
        'CustomFieldDef': '#bcbd22',
        'ClientProgram': '#17becf',
        'MessageCategory': '#9467bd',
        'Incentive': '#8c564b',
        'Rule': '#e377c2',
        'RuleSet': '#7f7f7f',
        'default': '#17becf'
    }

    # Shared button styles to make the button section nicer
    base_button_style = {
        "padding": "10px 14px",
        "margin": "6px",
        "border": "none",
        "borderRadius": "6px",
        "color": "#fff",
        "fontWeight": "600",
        "cursor": "pointer",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.12)"
    }
    button_styles = {
        "incentive": {"backgroundColor": class_colors['Incentive']},
        "message": {"backgroundColor": class_colors['MessageConfig']},
        "custom": {"backgroundColor": class_colors['CustomFieldDef']},
        "layout": {"backgroundColor": class_colors['ClientPageLayout']}
    }

    class_names = [
        "MessageConfig","ClientTopic","StandaloneFormula","ClientPageLayout",
        "CustomFieldDef","ClientProgram","MessageCategory","Incentive","Rule","RuleSet"
    ]
    class_options = [
        {"label": html.Span(name, style={"color": class_colors.get(name, class_colors['default'])}), "value": name}
        for name in class_names
    ]

    app.layout = html.Div([
        html.Div([
            html.H1("MHC Configuration Visualization Tool", style={
                "textAlign": "center",
                "color": "#2c3e50",
                "fontSize": "34px",
                "margin": "0 0 6px"
            }),
            html.P("By Alex Habegger - GitHub: @ahabegger",
                   style={"textAlign": "center", "fontSize": "14px", "color": "#6b7280", "margin": 0})
        ], style={
            "padding": "16px 20px",
            "background": "linear-gradient(90deg, #f7f9fc, #eef2f7)",
            "border": "1px solid #e5e9f2",
            "borderRadius": "8px",
            "marginBottom": "16px",
            "boxShadow": "0 1px 2px rgba(0,0,0,0.06)"
        }),

        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="snapshot-dropdown",
                    options=[{"label": s, "value": s} for s in snapshots],
                    placeholder="Select a snapshot to view",
                    value=snapshots[0] if snapshots else None,
                    style={"minWidth": "320px", "flex": "1 1 320px"}
                ),
                html.Button("Refresh Snapshot List", id="refresh-button",
                            style={**base_button_style, "backgroundColor": "#6c757d"}),
                html.Button("Refresh Graph", id="refresh-graph-button",
                            style={**base_button_style, "backgroundColor": class_colors['MessageConfig']})
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "10px",
                "alignItems": "center",
                "justifyContent": "center",
                "marginBottom": "10px"
            }),

            # Collapsible filter section - classes
            html.Details([
                html.Summary("Filter By Element"),
                dcc.Checklist(
                    id="class-filter",
                    options=class_options,
                    value=class_names,
                    labelStyle={"display": "inline-block", "marginRight": "12px", "marginBottom": "6px"},
                    inputStyle={"marginRight": "6px"}
                )
            ], open=False, style={"margin": "10px 0"}),

            # Collapsible filter section - programs
            html.Details([
                html.Summary("Filter By Program"),
                dcc.Checklist(
                    id="program-filter",
                    options=[],  # populated dynamically based on selected snapshot
                    value=[],    # default to all programs in snapshot via callback
                    labelStyle={"display": "inline-block", "marginRight": "12px", "marginBottom": "6px"},
                    inputStyle={"marginRight": "6px"}
                )
            ], open=False, style={"margin": "10px 0"}),

            dcc.Graph(id="network-graph", style={"height": "800px"}),
            # Add this div to display clicked node information
            html.Div(id="node-info", style={
                "margin": "20px 0",
                "padding": "15px",
                "border": "1px solid #ddd",
                "borderRadius": "5px",
                "backgroundColor": "#f9f9f9"
            })
        ], style={"border": "1px solid #ddd", "padding": "20px"}),

        html.H3("* = Elements could be referrenced by non-uploaded elements or by queries"),
        html.H3("** = Implied elements created to represent references to non-uploaded elements (missing context)"),
        html.Div([
            html.Button("Download Incentive Content", id="download-incentive-button",
                        title="Export Incentive content to CSV",
                        style={**base_button_style, **button_styles["incentive"]}),
            html.Button("Download Message Content", id="download-message-button",
                        title="Export Message content to CSV",
                        style={**base_button_style, **button_styles["message"]}),
            html.Button("Download Custom Fields Content", id="download-custom-fields-button",
                        title="Export Custom Field definitions to CSV",
                        style={**base_button_style, **button_styles["custom"]}),
            html.Button("Download Page Layout Content***", id="download-page-layout-button",
                        title="Export Page Layout HTML content to CSV",
                        style={**base_button_style, **button_styles["layout"]})
        ], style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "10px",
            "justifyContent": "center",
            "alignItems": "center",
            "marginTop": "20px"
        }),

        # Download status box (below the buttons)
        dcc.Loading(
            id="download-loading",
            type="default",
            color="#999",
            children=html.Div(id="download-status", style={
                "margin": "10px auto 0",
                "maxWidth": "900px",
                "padding": "10px 12px",
                "border": "1px solid #ddd",
                "borderRadius": "5px",
                "backgroundColor": "#f9f9f9",
                "textAlign": "center",
                "minHeight": "24px",
                "color": "#333"
            })
        ),

        html.Div("*** = Only downloads HTML Elements from page layouts",
                 style={"textAlign": "center", "fontSize": "12px", "color": "#555", "marginTop": "5px"})
    ], style={"max-width": "1200px", "margin": "0 auto", "padding": "20px"})


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
        [Input("snapshot-dropdown", "value"), Input("class-filter", "value"), Input("program-filter", "value")]
    )
    def update_graph(selected_snapshot, included_classes, included_programs):
        if not selected_snapshot:
            return {}
        try:
            return Graph.create_network_graph(selected_snapshot, include_classes=included_classes, include_programs=included_programs)
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
            return html.Div("Click a node to see details", style={"color": "#666"})

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

            return html.Div("Click a node to see details", style={"color": "#666"})

        except Exception as e:
            return html.Div(f"Error loading node details: {str(e)}")


    return app





if __name__ == "__main__":
    app = main()
    app.run(debug=True)

