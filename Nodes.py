import json
import os
import re

def find_nodes(files, folder):
    nodes = []
    for json_file in files:
        json_code = json.load(open(os.path.join(folder, json_file), 'r'))

        if not isinstance(json_code, list):
            new_json_code = []
            for json_category in json_code['_children'].keys():
                json_items = json_code['_children'][json_category]
                if isinstance(json_items, list):
                    for json_item in json_items:
                        if isinstance(json_item, dict) and '__reference_comparison_key' in json_item:
                            new_json_code.append(json_item)
            json_code = new_json_code


        for item in json_code:
            node = {}
            if not isinstance(item, dict):
                continue

            node_name = item.get("__reference_comparison_key")
            if node_name:
                node['name'] = node_name
                node['display_name'] = node_name[2:].split("[")[0].strip().split(":")[1].strip()
                node_type = classify_item_type(node_name)
                node['class'] = node_type
                node['program'] = node_name.split("[")[1].strip()[:-3].replace("ClientProgram:", "")

                item_string = str(item)
                node['content'] = get_content(item, node_type, item_string)
                # Build connections and filter out self-references
                refs = get_references(item_string)
                node['connections'] = [r for r in refs if r != node_name]
                node['order'] = "primary"
                node['query'] = "False"
                if "qry" in item_string:
                    node['query'] = "True"

                # Attach the raw JSON for collapsible Raw JSON view
                node['raw'] = item

                my_array = []

                if node_type is not None:
                    nodes.append(node)

    return nodes


def get_content(json_obj, node_type, string):
    """Extract the content from the item name."""
    if node_type == "MessageConfig":
        return json_obj['message']['body'], json_obj['message']['subject'], json_obj['message']['notificationText']
    if node_type == "Incentive":
        return json_obj['name'], json_obj['info']
    if node_type == "CustomFieldDef":
        default_value = json_obj['defaultValue']
        if "_dummy__formula" in string and default_value is None:
            default_value = "Calculated Using Formula"
        return json_obj['fieldType'], json_obj['fieldDataType'], default_value
    if node_type == "ClientPageLayout":
        content = ""
        if 'pageLayoutElements' in json_obj:
            for section in json_obj['pageLayoutElements']:
                if 'HTMLContent' in section:
                    html_content = section['HTMLContent']
                    if html_content is not None:
                        if html_content.strip() != "":
                            content += html_content + '\n'
            return content

    return None


def classify_item_type(name):
    """Classify the item type based on its name."""
    if "<<MessageConfig:" in name:
        return "MessageConfig"
    elif "<<ClientTopic:" in name:
        return "ClientTopic"
    elif "<<StandaloneFormula:" in name:
        return "StandaloneFormula"
    elif "<<ClientPageLayout:" in name:
        return "ClientPageLayout"
    elif "<<MessageCategory:" in name:
        return "MessageCategory"
    elif "<<CustomFieldDef:" in name:
        return "CustomFieldDef"
    elif "<<Incentive:" in name:
        return "Incentive"
    elif "<<Rule:" in name:
        return "Rule"
    elif "<<ClientRaffle:" in name:
        return "ClientRaffle"
    elif "<<ClientReward:" in name:
        return "ClientReward"
    elif "<<ClientProgram" in name:
        return "ClientProgram"
    elif "<<ClientTaskHandlerDefinition:" in name:
        return "ClientTaskHandlerDefinition"
    elif "<<RuleSet:" in name:
        if "None" not in name:
            return "RuleSet"
        else:
            return None
    else:
        return None



def get_references(string):
    """Extract references from the item string."""
    references = []

    for match in re.finditer(r'<<(?:[^>]+)>>', string):
        reference = match.group(0).strip()
        if reference and str(reference) not in references:
            if classify_item_type(str(reference)) is not None:
                references.append(str(reference))
    return references


def create_secondary_nodes(nodes):
    all_nodes = []
    all_nodes_names = set()

    for node in nodes:
        all_nodes_names.add(node['name'])
        all_nodes.append(node)

    for node in all_nodes:
        for connection in node['connections']:
            connection = str(connection).strip()
            if connection not in all_nodes_names:

                all_nodes_names.add(connection)
                if connection.startswith("<<") and connection.endswith(">>") and ":" in connection:
                    pass
                else:
                    continue

                if classify_item_type(connection) == "ClientProgram":
                    new_node = {
                        'name': connection,
                        'display_name': connection.split(":")[1].strip()[:-2],
                        'class': classify_item_type(connection),
                        'program': connection.split(":")[1].strip()[:-2],
                        'content': None,
                        'connections': [],
                        'order': "secondary",
                        'query': "False"
                    }
                else:
                    new_node = {
                        'name': connection,
                        'display_name': connection[2:].split("[")[0].strip().split(":")[1].strip(),
                        'class': classify_item_type(connection),
                        'program': connection.split("[")[1].strip()[:-3].replace("ClientProgram:", ""),
                        'content': None,
                        'connections': [],
                        'order': "secondary",
                        'query': "False"
                    }

                if new_node['class'] is not None:
                    all_nodes.append(new_node)

    return all_nodes
