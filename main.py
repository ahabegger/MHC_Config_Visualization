# There are four goals for this code:
# 1.) Download the Configuration Snapshot for a specified client or library with Selenium
# 2.) Parse the JSON files to extract the network graph data using plotly
# 3.) Create a network graph using plotly
# 4.) Display the network graph with DASH
import csv
import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask
import Graph
from Content import download_message_content_as_csv, download_incentive_content_as_csv, \
    download_client_custom_fields_content_as_csv, download_client_page_layout_content_as_csv
from Nodes import find_nodes


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

    app.layout = html.Div([
        html.H1("Configuration Network Analyzer"),

        html.Div([
            dcc.Dropdown(
                id="snapshot-dropdown",
                options=[{"label": s, "value": s} for s in snapshots],
                placeholder="Select a snapshot to view",
                value=snapshots[0] if snapshots else None
            ),
            html.Button("Refresh Snapshot List", id="refresh-button"),
            html.Button("Refresh Graph", id="refresh-graph-button"),
            dcc.Graph(id="network-graph", style={"height": "800px"})
        ], style={"border": "1px solid #ddd", "padding": "20px"}),

        html.H3("* = Elements could be referrenced by non-uploaded elements or by queries"),
        html.Div([
            html.Button("Download Incentive Content", id="download-incentive-button"),
            html.Button("Download Message Content", id="download-message-button"),
            html.Button("Download Custom Fields Content", id="download-custom-fields-button"),
            html.Button("Download Page Layout Content**", id="download-page-layout-button")
        ], style={"textAlign": "center", "marginTop": "20px"}),
        html.Div("** = Only downloads HTML Elements from page layouts",
                 style={"textAlign": "center", "fontSize": "12px", "color": "#555", "marginTop": "5px"})
    ], style={"max-width": "1200px", "margin": "0 auto", "padding": "20px"})


    # Update the callback in `main.py`
    @app.callback(
        Output("network-graph", "figure"),
        [Input("snapshot-dropdown", "value")]
    )
    def update_graph(selected_snapshot):
        if not selected_snapshot:
            return {}
        try:
            # Pass the selected files to the Graph function
            return Graph.create_network_graph(selected_snapshot)
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


    @app.callback(
        Output("download-incentive-button", "n_clicks"),
        Input("download-incentive-button", "n_clicks"),
        Input("snapshot-dropdown", "value")
    )
    def download_incentive_content(n_clicks, selected_snapshot):
        download_incentive_content_as_csv(n_clicks, selected_snapshot)
        return None

    @app.callback(
        Output("download-message-button", "n_clicks"),
        Input("download-message-button", "n_clicks"),
        Input("snapshot-dropdown", "value")
    )
    def download_message_content(n_clicks, selected_snapshot):
        download_message_content_as_csv(n_clicks, selected_snapshot)
        return None

    @app.callback(
        Output("download-custom-fields-button", "n_clicks"),
        Input("download-custom-fields-button", "n_clicks"),
        Input("snapshot-dropdown", "value")
    )
    def download_custom_fields_content(n_clicks, selected_snapshot):
        download_client_custom_fields_content_as_csv(n_clicks, selected_snapshot)
        return None

    @app.callback(
        Output("download-page-layout-button", "n_clicks"),
        Input("download-page-layout-button", "n_clicks"),
        Input("snapshot-dropdown", "value")
    )
    def download_page_layout_content(n_clicks, selected_snapshot):
        download_client_page_layout_content_as_csv(n_clicks, selected_snapshot)
        return None

    return app





if __name__ == "__main__":
    app = main()
    app.run(debug=True)



