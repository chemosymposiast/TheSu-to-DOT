"""
Source subgraph handling for Gephi transformation.
"""
import re

def find_gephi_source_subgraphs(dot_content):
    """
    Find all THES, SUPP, and MISC nodes in the DOT file and group them by their source attribute.
    Uses only the explicit source attribute for associations instead of relying on subgraph structure.
    
    Args:
        dot_content: String content of the DOT file
    
    Returns:
        dict: Mapping of source IDs to their associated nodes
    """
    source_subgraphs = {}
    
    # Split the content by lines for processing
    lines = dot_content.split('\n')
    
    # Process each line
    for line in lines:
        # First check if this is a node definition
        if '"' in line and '[' in line and ']' in line:
            # Extract the node ID (between the first pair of quotes)
            node_match = re.match(r'"([^"]+)"', line)
            if node_match:
                node_id = node_match.group(1)
                
                # Check if this node has a source attribute
                source_match = re.search(r'source="([^"]+)"', line)
                if source_match:
                    source_id = source_match.group(1)
                    
                    # Initialize source entry if not exists
                    if source_id not in source_subgraphs:
                        source_subgraphs[source_id] = {
                            'id': source_id,
                            'nodes': []
                        }
                    
                    # Add node to its source group
                    source_subgraphs[source_id]['nodes'].append(node_id)
    
    return source_subgraphs


def create_gephi_source_nodes(source_subgraphs):
    """
    Create source nodes with optimal styling for each source subgraph.
    Source subgraphs are determined by the source attribute on nodes.
    
    Args:
        source_subgraphs: Dict mapping source IDs to their associated nodes
    
    Returns:
        list: Source node declarations for the DOT file
    """
    source_nodes = []
    
    for source_id, data in source_subgraphs.items():
        # Create a larger, prominently styled node for each source
        # Using a distinct but harmonious style compared to other nodes
        source_node = (
            f'"{source_id}" [label="SOURCE", source_id="{source_id}", '
            f'is_source_node="true", '
            f'shape="diamond", style="filled", '
            f'color="thistle", fillcolor="thistle", '
            f'fontcolor="black", fontsize="16", fontname="bold", '
            f'width="1.5", height="1.5", penwidth="2", margin="0.2,0.1"];'
        )
        source_nodes.append(source_node)    
    return source_nodes


def create_gephi_source_edges(source_subgraphs, dot_content):
    """
    Create edges connecting source nodes to their associated THES, SUPP, and MISC nodes.
    Associations are based on the source attribute on each node.
    Skips nodes with manifestation="extrinsic" attribute.
    
    Args:
        source_subgraphs: Dict mapping source IDs to their associated nodes
        dot_content: Original DOT file content to check for node attributes
        
    Returns:
        list: Edge declarations for the DOT file
    """
    source_edges = []
    
    # First, identify all nodes with manifestation="extrinsic"
    extrinsic_nodes = set()
    for line in dot_content.split('\n'):
        if 'manifestation="extrinsic"' in line:
            node_match = re.match(r'"([^"]+)"', line)
            if node_match:
                extrinsic_nodes.add(node_match.group(1))
    
    for source_id, data in source_subgraphs.items():
        # For each associated node, create an undirected edge to the source node
        for node_id in data['nodes']:
            # Skip creating edges for extrinsic nodes
            if node_id in extrinsic_nodes:
                continue
                
            edge = (
                f'"{source_id}" -> "{node_id}" '
                f'[dir="none", color="thistle", penwidth=0.8, style="dashed,bold"];\n\n'
            )
            source_edges.append(edge)
    
    return source_edges


