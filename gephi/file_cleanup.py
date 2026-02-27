"""
Cleanup functions for Gephi DOT files.
"""
import re

def remove_duplicate_gephi_edges(filename):
    """
    Reads a DOT file and removes duplicate edge definitions.
    Keeps the first occurrence of any edge between a specific source and target.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    seen_edges = set() # Stores tuples of (source_id, target_id)
    output_lines = []

    edge_pattern = re.compile(r'^\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*->\s*"([^"\\]*(?:\\.[^"\\]*)*)".*')

    duplicates_removed = 0
    for line in lines:
        match = edge_pattern.match(line)
        if match:
            source_id = match.group(1)
            target_id = match.group(2)
            edge_tuple = (source_id, target_id)

            if edge_tuple in seen_edges:
                duplicates_removed += 1
                continue # Skip this duplicate edge line
            else:
                seen_edges.add(edge_tuple)
                output_lines.append(line) # Keep the first occurrence
        else:
            output_lines.append(line) # Keep non-edge lines

    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate edge definition(s).")
        # Write the cleaned content back to the file
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)


def clean_edge_attributes(gephi_dot_filename):
    """
    Cleans up edge attributes in the Gephi DOT file:
    1. Removes "original_html" attributes from edges
    2. Removes "fontsize" attributes from edges 
    3. Removes "fontname" attributes from edges
    
    These modifications are applied before the general post-processing function.
    """
    with open(gephi_dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    
    for line in lines:
        # Check if this line represents an edge (contains " -> ")
        if " -> " in line and "[" in line and "]" in line:
            # Remove original_html attribute
            line = re.sub(r',\s*original_html="[^"]*"', '', line)
            
            # Remove fontsize attribute
            line = re.sub(r',\s*fontsize=\d+', '', line)
            line = re.sub(r'fontsize=\d+,\s*', '', line)
            
            # Remove fontname attribute
            line = re.sub(r',\s*fontname="[^"]*"', '', line)
            line = re.sub(r'fontname="[^"]*",\s*', '', line)
            
            # Fix any double commas or trailing commas before closing bracket
            line = re.sub(r',,', ',', line)
            line = re.sub(r',\s*\]', ']', line)
            
            # Fix case where first attribute was removed, leaving a leading comma
            line = re.sub(r'\[\s*,', '[', line)
        
        cleaned_lines.append(line)
    
    with open(gephi_dot_filename, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)


def remove_invisible_elements(dot_content):
    """Remove nodes and edges with gephi_invis="true" attribute."""
    lines = dot_content.split('\n')
    filtered_lines = []
    
    # Keep track of invisible nodes to also remove their edges
    invisible_nodes = []
    
    # First pass: identify invisible nodes
    for line in lines:
        if 'gephi_invis="true"' in line:
            # Extract node ID if this is a node definition
            node_match = re.search(r'"([^"]+)"', line)
            if node_match and '[' in line:
                invisible_nodes.append(node_match.group(1))
    
    # Second pass: filter out lines with invisible elements and their edges
    skip_next = False
    for i, line in enumerate(lines):
        # Skip if flagged from previous iteration
        if skip_next:
            skip_next = False
            continue
            
        # Skip lines with gephi_invis="true"
        if 'gephi_invis="true"' in line:
            # If this line ends with a semicolon, we're done
            if line.strip().endswith(';'):
                continue
            # If not, this might be a multi-line definition, so skip the next line too
            else:
                skip_next = True
                continue
        
        # Skip edges connected to invisible nodes
        skip_line = False
        for node in invisible_nodes:
            edge_pattern = f'"{node}" -> '
            reverse_edge_pattern = f' -> "{node}"'
            if edge_pattern in line or reverse_edge_pattern in line:
                skip_line = True
                break
        
        if not skip_line:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


