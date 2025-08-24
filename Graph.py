import os
import networkx as nx

from Nodes import find_nodes, create_secondary_nodes
import plotly.graph_objects as go
import math


def create_network_graph(snapshot_name):
    """Create a network graph from the JSON configuration files, grouped by program."""
    snapshot_folder = os.path.join("Snapshots", snapshot_name)

    # Debug: Check if snapshot folder exists
    if not os.path.exists(snapshot_folder):
        print(f"Error: Snapshot folder '{snapshot_folder}' does not exist")
        return None

    json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]

    # Debug: Check if JSON files were found
    if not json_files:
        print(f"Error: No JSON files found in '{snapshot_folder}'")
        return None

    nodes = find_nodes(json_files, snapshot_folder)
    # Debug: Check if nodes were created
    if not nodes:
        print("Error: No nodes found")
        return None

    print(f"Found {len(nodes)} initial nodes")

    nodes = create_secondary_nodes(nodes)
    print(f"Total nodes after secondary creation: {len(nodes)}")

    # Create a NetworkX graph
    G = nx.DiGraph()

    # Add nodes to the graph
    for node in nodes:
        G.add_node(node['name'],
                   display_name=node['display_name'],
                   type=node['class'],
                   query=node['query'],
                   name=node['display_name'],
                   program=node['program'],
                   order=node['order'])

    # Add edges based on connections
    for node in nodes:
        source_node = node['name']
        connections = node.get('connections', [])

        for connection in connections:
            if connection in G.nodes():
                G.add_edge(source_node, connection,
                           relation="references",
                           edge_type="configuration_reference")

    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    # Group nodes by program
    program_nodes = {}
    for node in G.nodes():
        program = G.nodes[node]['program']
        if program not in program_nodes:
            program_nodes[program] = []
        program_nodes[program].append(node)

    # Create clustered positions
    pos = {}
    programs = list(program_nodes.keys())
    num_programs = len(programs)

    # Calculate cluster centers in a grid layout
    grid_size = math.ceil(math.sqrt(num_programs))
    cluster_spacing = 8  # Distance between cluster centers

    # Store cluster centers for labels
    cluster_centers = {}

    for i, program in enumerate(programs):
        # Calculate cluster center position
        row = i // grid_size
        col = i % grid_size
        center_x = col * cluster_spacing
        center_y = row * cluster_spacing

        # Store cluster center for label placement
        cluster_centers[program] = (center_x, center_y)

        # Get nodes for this program
        program_node_list = program_nodes[program]

        if len(program_node_list) == 1:
            # Single node, place at center
            pos[program_node_list[0]] = (center_x, center_y)
        else:
            # Multiple nodes, create subgraph and layout within cluster
            program_subgraph = G.subgraph(program_node_list)

            # Use spring layout for nodes within the cluster
            cluster_pos = nx.spring_layout(program_subgraph, k=1, iterations=50, scale=2)

            # Offset all positions to the cluster center
            for node in program_node_list:
                if node in cluster_pos:
                    pos[node] = (cluster_pos[node][0] + center_x,
                                 cluster_pos[node][1] + center_y)

    # Define colors for different node types
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

    # Prepare edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines')

    # Create program label traces
    label_traces = []
    even = True
    for program, (center_x, center_y) in cluster_centers.items():
        # Calculate actual cluster bounds for better label positioning

        if program in program_nodes:
            program_x = [pos[node][0] for node in program_nodes[program] if node in pos]
            program_y = [pos[node][1] for node in program_nodes[program] if node in pos]

            if program_x and program_y:
                # Position label at top of cluster
                label_x = center_x
                if even:
                    label_y = max(program_y) + 1  # Position above the cluster
                    even = False
                else:
                    label_y = min(program_y) - 1 # Position below the cluster
                    even = True

                label_trace = go.Scatter(
                    x=[label_x],
                    y=[label_y],
                    mode='text',
                    text=[program.replace('ClientProgram:', '')],
                    textfont=dict(size=10, color='rgba(128, 128, 128, 0.8)'),
                    textposition='middle center',
                    showlegend=False,
                    hoverinfo='none'
                )
                label_traces.append(label_trace)

    # Prepare node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    for node in G.nodes():
        if node in pos:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Create hover text
            node_info = G.nodes[node]

            context_hover_text = (f"<b>Name:</b> {node_info['display_name']}<br>"
                          f"<b>Type:</b> {node_info['type']}<br>"
                          f"<b>Program:</b> {node_info['program']}<br>")

            refers_to_hover_text = f"<b>Refers To ({len(list(G.successors(node)))}):</b><br>"
            for successor in list(G.successors(node)):
                refers_to_hover_text += f"  {successor}<br>"
            if node_info['query'] == "True":
                refers_to_hover_text += "  <b>Query<br>"

            referred_by_hover_text = f"<b>Referred By* ({len(list(G.predecessors(node)))}):</b><br>"
            for predecessor in list(G.predecessors(node)):
                referred_by_hover_text += f"  {predecessor}<br>"
            if node_info['order'] == "secondary":
                warning_hover_text = f"<b>Warning:</b> This is an implied element and could be missing context"
            else:
                warning_hover_text = ""

            hover_text = context_hover_text + refers_to_hover_text + referred_by_hover_text + warning_hover_text
            node_text.append(hover_text)

            # Set color based on type
            node_color.append(class_colors.get(node_info['type'], class_colors['default']))

            # Set size based on connections
            connection_count = len(list(G.successors(node))) + len(list(G.predecessors(node)))
            node_size.append(max(8, min(20, 10 + connection_count * 2)))

    node_trace = go.Scatter(x=node_x, y=node_y,
                            mode='markers',
                            hoverinfo='text',
                            text=node_text,
                            marker=dict(size=node_size,
                                        color=node_color,
                                        line=dict(width=2, color='white')))

    # Combine all traces
    all_traces = [edge_trace] + label_traces + [node_trace]

    # Create the figure
    fig = go.Figure(data=all_traces,
                    layout=go.Layout(
                        title=f'Configuration Network for {snapshot_name} (Clustered by Program)',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='rgba(240,240,240,0.8)',
                        autosize=True,
                        height=800))

    return fig


if __name__ == "__main__":
    snapshot_name = "NDP2"  # Replace with your snapshot name
    graph = create_network_graph(snapshot_name)
    print(graph)  # This will print the graph object, you can visualize it using Plotly or NetworkX