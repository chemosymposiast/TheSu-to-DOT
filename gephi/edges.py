"""
Edge processing and creation functions for Gephi transformation.
"""
import re

def process_gephi_edges_for_entailment_nodes(dot_content, entailment_nodes):
    """
    Find and process edges connected to entailment pseudo-nodes.
    Updates the input dictionaries with connection information.
    """
    # Find edges connected to entailment pseudo-nodes
    edge_pattern = re.compile(r'"([^"]+)" -> "([^"]+)"')
    for match in edge_pattern.finditer(dot_content):
        source = match.group(1)
        target = match.group(2)
        
        # Check if target is an entailment pseudo-node
        if target in entailment_nodes:
            entailment_nodes[target]['source'] = source
        
        # Check if source is an entailment pseudo-node
        elif source in entailment_nodes:
            entailment_nodes[source]['target'] = target


def process_gephi_edges_for_etiology_nodes(dot_content, etiology_nodes):
    """
    Find and process edges connected to etiology pseudo-nodes.
    Updates the input dictionary with connection information.
    """
    # Find edges connected to etiology pseudo-nodes
    edge_pattern = re.compile(r'"([^"]+)" -> "([^"]+)"')
    for match in edge_pattern.finditer(dot_content):
        source = match.group(1)
        target = match.group(2)
        
        # Check if target is an etiology pseudo-node
        if target in etiology_nodes:
            etiology_nodes[target]['source'] = source
        
        # Check if source is an etiology pseudo-node
        elif source in etiology_nodes:
            etiology_nodes[source]['target'] = target


def process_gephi_edges_for_analogy_nodes(dot_content, analogy_nodes):
    """
    Find and process edges connected to analogy pseudo-nodes.
    Updates the input dictionaries with connection information.
    """
    # Find edges connected to analogy pseudo-nodes
    edge_pattern = re.compile(r'"([^"]+)" -> "([^"]+)"')
    for match in edge_pattern.finditer(dot_content):
        source = match.group(1)
        target = match.group(2)
        
        # Check if target is an analogy pseudo-node
        if target in analogy_nodes:
            analogy_nodes[target]['source'] = source
        
        # Check if source is an analogy pseudo-node
        elif source in analogy_nodes:
            analogy_nodes[source]['target'] = target


def process_gephi_edges_for_reference_nodes(dot_content, reference_nodes):
    """
    Process edges connected to reference pseudo-nodes to extract the actual 
    reference relationships. Also handles cases where node definitions are missing.
    """
    # For each reference node, find its incoming and outgoing edges
    for node_id in reference_nodes:
        # Pattern for incoming edge (source -> pseudo-node)
        in_pattern = r'"([^"]+)" -> "' + re.escape(node_id) + r'" \[([^\]]*)\];'
        
        # Pattern for outgoing edge (pseudo-node -> target)
        out_pattern = r'"' + re.escape(node_id) + r'" -> "([^"]+)" \[([^\]]*)\];'
        
        # Find the source and target nodes
        in_match = re.search(in_pattern, dot_content)
        out_match = re.search(out_pattern, dot_content)
        
        if in_match and out_match:
            source_node = in_match.group(1)
            target_node = out_match.group(1)
            
            # Store source and target in the node info
            if reference_nodes[node_id] is None:
                # This handles case where node definition is missing
                reference_nodes[node_id] = {
                    'node': f'"{node_id}" [label=<IS REFERENCED IN>, fontsize="11", style="rounded,filled", fillcolor="#f0f3e0", color="#708238", shape="note"];',
                    'source': source_node,
                    'target': target_node,
                    'in_edge': in_match.group(0),
                    'out_edge': out_match.group(0)
                }
            else:
                reference_nodes[node_id] = {
                    'node': reference_nodes[node_id],
                    'source': source_node,
                    'target': target_node,
                    'in_edge': in_match.group(0),
                    'out_edge': out_match.group(0)
                }


def process_gephi_edges_for_pseudonodes(dot_content, matching_nodes, employed_nodes, function_nodes):
    """
    Find and process edges connected to all types of pseudo-nodes.
    Updates the input dictionaries with connection information.
    """
    # Find edges connected to pseudo-nodes (matching, employed, and function nodes)
    edge_pattern = re.compile(r'"([^"]+)" -> "([^"]+)"')
    for match in edge_pattern.finditer(dot_content):
        source = match.group(1)
        target = match.group(2)
        
        # Check if target is a matching pseudo-node
        if target in matching_nodes:
            matching_nodes[target]['source'] = source
        
        # Check if source is a matching pseudo-node
        elif source in matching_nodes:
            matching_nodes[source]['target'] = target
            
        # Check if target is an employed pseudo-node
        elif target in employed_nodes:
            employed_nodes[target]['sources'].append(source)
        
        # Check if source is an employed pseudo-node
        elif source in employed_nodes:
            employed_nodes[source]['target'] = target
        
        # Check if target is a function pseudo-node
        elif target in function_nodes:
            function_nodes[target]['source'] = source
        
        # Check if source is a function pseudo-node
        elif source in function_nodes:
            function_nodes[source]['targets'].append(target)


def create_gephi_direct_entailment_edges(entailment_nodes):
    """
    Create direct replacement edges for entailment connections.
    
    Args:
        entailment_nodes: Dict mapping pseudo-node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the entailment pseudo-nodes
    """
    direct_edges = []
    for pseudo_id, data in entailment_nodes.items():
        if data['source'] and data['target']:
            # Create direct edge from entailing element to entailed element
            # with entailment information as a separate attribute
            entailed_as = data['entailed_as']
            direct_edges.append(f'"{data["source"]}" -> "{data["target"]}" [label="ENTAILS", entailment_type="{entailed_as}", color="dimgray", fontcolor="dimgray", penwidth=1.5];\n\n')
            
    return direct_edges


def create_gephi_direct_etiology_edges(etiology_nodes):
    """
    Create direct replacement edges for etiology connections.
    
    Args:
        etiology_nodes: Dict mapping pseudo-node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the etiology pseudo-nodes
    """
    direct_edges = []
    for pseudo_id, data in etiology_nodes.items():
        if data['source'] and data['target']:
            # Get the relation type for the attribute
            relation_type = data['relation_type']
            
            # Use a consistent label for all etiology edges
            label = "IN ETIOLOGY"
            
            # Use HTML color name instead of hex code
            etiology_color = "darkcyan"
            
            direct_edges.append(f'"{data["source"]}" -> "{data["target"]}" [label="{label}", relation_type="{relation_type}", color="{etiology_color}", fontcolor="{etiology_color}", penwidth=1.5];\n\n')
            
    return direct_edges


def create_gephi_direct_analogy_edges(analogy_nodes):
    """
    Create direct replacement edges for analogy connections.
    
    Args:
        analogy_nodes: Dict mapping pseudo-node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the analogy pseudo-nodes
    """
    direct_edges = []
    for pseudo_id, data in analogy_nodes.items():
        if data['source'] and data['target']:
            # Get the comparans attribute value
            comparans_attr = "true" if data['is_comparans'] else "false"
            
            # Always use "compared in" as the label but add comparans attribute
            direct_edges.append(f'"{data["source"]}" -> "{data["target"]}" [label="COMPARED IN", comparans="{comparans_attr}", color="darkslateblue", fontcolor="darkslateblue", penwidth=1.5];\n\n')
            
    return direct_edges


def create_gephi_direct_matching_edges(matching_nodes):
    """
    Create direct replacement edges for matching proposition connections.
    
    Args:
        matching_nodes: Dict mapping pseudo-node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the matching proposition pseudo-nodes
    """
    direct_edges = []
    for pseudo_id, data in matching_nodes.items():
        if data['source'] and data['target']:
            # Clean up the matching type text - remove HTML tags and convert verb forms
            matching_type = data['type']
            # Remove HTML tags
            matching_type = re.sub(r'<br/>', ' ', matching_type)
            
            # Convert verb forms
            matching_type = matching_type.replace('extending', 'extends')
            matching_type = matching_type.replace('being part of', 'is part of')
            matching_type = matching_type.replace('generalizing', 'generalizes')
            matching_type = matching_type.replace('specifying', 'specifies')
            matching_type = matching_type.replace('being quoted', 'is quoted in')
            matching_type = matching_type.replace('altering', 'alters')
            
            # Use "indigo" for dark purple color
            direct_edges.append(f'"{data["source"]}" -> "{data["target"]}" [label="{matching_type}", color="indigo", fontcolor="indigo", penwidth=1.5];\n\n')
            
    return direct_edges


def create_gephi_direct_employed_edges(employed_nodes):
    """
    Create direct replacement edges for employed elements.
    
    Args:
        employed_nodes: Dict mapping employed node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the employed pseudo-nodes
    """
    direct_edges = []
    for employed_id, data in employed_nodes.items():
        if data['target'] and data['sources']:
            # For each source element that was connected to the employed pseudo-node
            for source in data['sources']:
                # Create direct edge from employed element to support, with appropriate label and styling
                direct_edges.append(f'"{source}" -> "{data["target"]}" [label="in", color="darkgoldenrod", fontcolor="darkgoldenrod", penwidth=1.5];\n\n')
                
    return direct_edges


def create_gephi_direct_reference_edges(reference_nodes):
    """
    Create direct edges that replace reference pseudo-nodes.
    
    Args:
        reference_nodes: Dict mapping pseudo-node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the reference pseudo-nodes
    """
    direct_edges = []
    
    for pseudo_id, data in reference_nodes.items():
        if data['source'] and data['target']:
            # Create direct edge with standard styling
            reference_color = "olivedrab"
            
            direct_edges.append(f'"{data["source"]}" -> "{data["target"]}" [label="REFERENCED IN", color="{reference_color}", fontcolor="{reference_color}", penwidth=1.5];\n\n')
            
    return direct_edges


def create_gephi_direct_function_edges(function_nodes):
    """
    Create direct replacement edges for function nodes (support-target connections).
    
    Args:
        function_nodes: Dict mapping function node IDs to their connection info
        
    Returns:
        list: Direct edges that replace the function pseudo-nodes
    """
    direct_edges = []
    for func_id, data in function_nodes.items():
        if data['source'] and data['targets']:
            support_id = data['source']
            function_label = data['function']
            
            # For each target connected to this function pseudo-node
            for target_id in data['targets']:
                # Create direct edge from support to target with function info in label
                direct_edges.append(f'"{support_id}" -> "{target_id}" [label="{function_label}", color="steelblue", fontcolor="steelblue", penwidth=1.5];\n\n')
                
    return direct_edges


