import csv
import os

from Nodes import find_nodes


def download_message_content_as_csv(n_clicks, selected_snapshot):
    if n_clicks:
        print("Download Message Content clicked")
        if not selected_snapshot:
            return None
        else:
            try:
                snapshot_folder = os.path.join("Snapshots", selected_snapshot)
                json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
                nodes = find_nodes(json_files, snapshot_folder)

                # Delete Old CSV file if it exists
                csv_file_path = os.path.join("Content", f"{selected_snapshot}_messages.csv")
                if os.path.exists(csv_file_path):
                    os.remove(csv_file_path)
                    print(f"Removed old CSV file: {csv_file_path}")

                # Write message content to csv file using proper CSV writer
                with open(os.path.join("Content", f"{selected_snapshot}_messages.csv"), "w", newline='',
                          encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Identification", "Program", "System Name", "Subject", "Body", "Notification Text",
                         "References"])
                    for node in nodes:
                        if node['class'] == "MessageConfig":
                            writer.writerow([
                                node['name'],
                                node['program'],
                                node['display_name'],
                                node['content'][1],  # subject
                                node['content'][0],  # body
                                node['content'][2],  # notification text
                                ';'.join(node['connections'])
                            ])
                print(
                    f"Message content downloaded to {os.path.join('Content', f'{selected_snapshot}_messages.csv')}")
            except Exception as e:
                print(f"Error writing message content: {e}")
    return None

def download_incentive_content_as_csv(n_clicks, selected_snapshot):
    if n_clicks:
        print("Download Incentive Content clicked")
        if not selected_snapshot:
            return None
        else:
            try:
                snapshot_folder = os.path.join("Snapshots", selected_snapshot)
                json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
                nodes = find_nodes(json_files, snapshot_folder)

                # Delete Old CSV file if it exists
                csv_file_path = os.path.join("Content", f"{selected_snapshot}_incentives.csv")
                if os.path.exists(csv_file_path):
                    os.remove(csv_file_path)
                    print(f"Removed old CSV file: {csv_file_path}")

                # Write incentive content to csv file using proper CSV writer
                with open(os.path.join("Content", f"{selected_snapshot}_incentives.csv"), "w", newline='',
                          encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Identification", "Program", "System Name", "Display Name", "Content", "References"])

                    for node in nodes:
                        if node['class'] == "Incentive":
                            writer.writerow([
                                node['name'],
                                node['program'],
                                node['display_name'],
                                node['content'][0],
                                node['content'][1],
                                ';'.join(node['connections'])
                            ])
                print(
                    f"Incentive content downloaded to {os.path.join('Content', f'{selected_snapshot}_incentives.csv')}")
            except Exception as e:
                print(f"Error writing incentive content: {e}")

def download_client_custom_fields_content_as_csv(n_clicks, selected_snapshot):
    if n_clicks:
        print("Download Custom Fields Content clicked")
        if not selected_snapshot:
            return None
        else:
            try:
                snapshot_folder = os.path.join("Snapshots", selected_snapshot)
                json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
                nodes = find_nodes(json_files, snapshot_folder)

                # Delete Old CSV file if it exists
                csv_file_path = os.path.join("Content", f"{selected_snapshot}_custom_fields.csv")
                if os.path.exists(csv_file_path):
                    os.remove(csv_file_path)
                    print(f"Removed old CSV file: {csv_file_path}")

                # Write custom fields content to csv file using proper CSV writer
                with open(os.path.join("Content", f"{selected_snapshot}_custom_fields.csv"), "w", newline='',
                          encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Identification", "Program", "System Name", "Class Type", "Field Type", "Default Value",
                         "References"])

                    for node in nodes:
                        if node['class'] == "CustomFieldDef":
                            writer.writerow([
                                node['name'],
                                node['program'],
                                node['display_name'],
                                node['content'][0],
                                node['content'][1],
                                node['content'][2] if node['content'][2] is not None else "None",
                                ';'.join(node['connections'])
                            ])
                print(
                    f"Custom fields content downloaded to {os.path.join('Content', f'{selected_snapshot}_custom_fields.csv')}")
            except Exception as e:
                print(f"Error writing custom fields content: {e}")
    return None

def download_client_page_layout_content_as_csv(n_clicks, selected_snapshot):
    if n_clicks:
        print("Download Page Layout Content clicked")
        if not selected_snapshot:
            return None
        else:
            try:
                snapshot_folder = os.path.join("Snapshots", selected_snapshot)
                json_files = [f for f in os.listdir(snapshot_folder) if f.endswith('.json')]
                nodes = find_nodes(json_files, snapshot_folder)

                # Delete Old CSV file if it exists
                csv_file_path = os.path.join("Content", f"{selected_snapshot}_page_layouts.csv")
                if os.path.exists(csv_file_path):
                    os.remove(csv_file_path)
                    print(f"Removed old CSV file: {csv_file_path}")

                # Write page layout content to csv file using proper CSV writer
                with open(os.path.join("Content", f"{selected_snapshot}_page_layouts.csv"), "w", newline='',
                          encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Identification", "Program", "System Name", "HTML Content", "References"])

                    for node in nodes:
                        if node['class'] == "ClientPageLayout":
                            writer.writerow([
                                node['name'],
                                node['program'],
                                node['display_name'],
                                node['content'] if node['content'] is not None else "None",
                                ';'.join(node['connections'])
                            ])
                print(
                    f"Page layout content downloaded to {os.path.join('Content', f'{selected_snapshot}_page_layouts.csv')}")
            except Exception as e:
                print(f"Error writing page layout content: {e}")
    return None
