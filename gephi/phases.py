"""
Phase processing functions for Gephi DOT files.
"""
import re

def process_phases_only(input_dot, output_dot):
    """
    Process only phase nodes and their connections.
    """    
    with open(input_dot, 'r', encoding='utf-8') as f:
        dot_content = f.read()
    
    # Find phase clusters and their contents
    cluster_parents, phase_to_cluster = find_gephi_phase_clusters(dot_content)
    
    # Process only phase-to-phase edges
    processed_lines = []
    new_phase_edges = []
    
    for line in dot_content.split('\n'):
        skip_line = False
        
        # Check if this is a phase-to-phase edge
        # Look for any edge where both endpoints are phases in the same cluster
        if ' -> ' in line and ';' in line:  # Basic edge detection
            edge_match = re.search(r'"([^"]+)" -> "([^"]+)"', line)
            if edge_match:
                source_id = edge_match.group(1)
                target_id = edge_match.group(2)
                
                # If both source and target are phases in the same cluster, replace this edge
                if (source_id in phase_to_cluster and target_id in phase_to_cluster and 
                    phase_to_cluster[source_id] == phase_to_cluster[target_id]):
                    cluster_id = phase_to_cluster[source_id]
                    parent_id = cluster_parents.get(cluster_id)
                    
                    if parent_id:
                        # Create direct edges from each phase to the parent
                        new_phase_edge1 = f'"{source_id}" -> "{parent_id}" [style="dashed", color="gray"];'
                        new_phase_edge2 = f'"{target_id}" -> "{parent_id}" [style="dashed", color="gray"];'
                        new_phase_edges.append(new_phase_edge1)
                        new_phase_edges.append(new_phase_edge2)
                    
                    skip_line = True
        
        # Skip parent-to-cluster edges with lhead attribute
        if "lhead=\"cluster_" in line and "dir=none" in line:
            skip_line = True
        
        if not skip_line:
            processed_lines.append(line)
    
    # Find the last closing brace in the file
    # Reverse search from the end of the file
    for i in range(len(processed_lines) - 1, -1, -1):
        if processed_lines[i].strip() == '}':
            closing_brace_index = i
            break
    else:
        # If no closing brace is found, append at the end
        closing_brace_index = len(processed_lines)
        processed_lines.append('}')
    
    # Add a blank line before the new edges if not already there
    if closing_brace_index > 0 and processed_lines[closing_brace_index-1].strip() != '':
        processed_lines.insert(closing_brace_index, '')
        closing_brace_index += 1  # Adjust index after insertion
    
    # Insert unique edges before the final closing brace
    unique_phase_edges = list(set(new_phase_edges))
    if unique_phase_edges:
        processed_lines = (processed_lines[:closing_brace_index] + 
                          unique_phase_edges + 
                          processed_lines[closing_brace_index:])
    
    # Write the phase-processed content to output file
    with open(output_dot, 'w', encoding='utf-8') as f:
        for line in processed_lines:
            line = line.rstrip()
            f.write(line + '\n')
    
    return phase_to_cluster, cluster_parents


def find_gephi_phase_clusters(dot_content):
    """
    Find all clusters and their parent nodes for phase connections in the DOT content.
    Uses a line-by-line approach for more reliable parsing.
    """
    # Format: {cluster_id: parent_node_id}
    cluster_parents = {}
    # Format: {phase_node_id: cluster_id}
    phase_to_cluster = {}
    
    # Find parent-cluster relationships
    parent_cluster_pattern = re.compile(r'"([^"]+)" -> "[^"]+" \[.*?lhead="(cluster_[^"]+)"')
    for match in parent_cluster_pattern.finditer(dot_content):
        parent_id = match.group(1)
        cluster_id = match.group(2)
        cluster_parents[cluster_id] = parent_id
    
    # Process line by line to find phases in clusters
    lines = dot_content.split('\n')
    current_cluster = None
    
    for line in lines:
        # Check for cluster start
        if line.strip().startswith('subgraph cluster_'):
            cluster_match = re.search(r'subgraph (cluster_[^{ ]+)', line)
            if cluster_match:
                current_cluster = cluster_match.group(1)
        
        # Check for node with gephi_label="ph."
        elif current_cluster and 'gephi_label="ph."' in line:
            node_match = re.search(r'"([^"]+)"', line)
            if node_match:
                phase_id = node_match.group(1)
                phase_to_cluster[phase_id] = current_cluster
        
        # Check for cluster end
        elif line.strip() == '}' and current_cluster:
            current_cluster = None
    
    return cluster_parents, phase_to_cluster


