"""
Post-processing functions for Gephi DOT files.
"""
import re

def post_process_gephi_dot(gephi_dot_filename):
    """
    Post-processes the Gephi DOT file to:
    1. Remove any non-empty line which is not "digraph G {" and does not start with a double quote
    2. Ensure the file ends with a closing brace "}"
    3. Reduce any succession of multiple empty lines to a single empty line
    """
    with open(gephi_dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process lines according to the rules
    processed_lines = []
    prev_line_empty = False
    
    for line in lines:
        line = line.rstrip()
        
        # Check if line is empty
        if not line.strip():
            # Only add empty line if previous line wasn't empty
            if not prev_line_empty:
                processed_lines.append("")
                prev_line_empty = True
            continue
        
        # Reset empty line tracker for non-empty lines
        prev_line_empty = False
        
        # Keep lines that are "digraph G {" or start with a double quote
        if line == "digraph G {" or line.lstrip().startswith('"'):
            processed_lines.append(line)
    
    # Run a second pass to ensure all empty line sequences are reduced to one
    final_lines = []
    prev_line_empty = False
    
    for line in processed_lines:
        if not line.strip():
            if not prev_line_empty:
                final_lines.append("")
                prev_line_empty = True
        else:
            final_lines.append(line)
            prev_line_empty = False
    
    # Ensure the file ends with a closing brace preceded by exactly one empty line
    # First remove any trailing content including the closing brace if it exists
    while final_lines and (not final_lines[-1].strip() or final_lines[-1] == "}"):
        final_lines.pop()
    
    # Add exactly one empty line followed by the closing brace
    final_lines.append("")
    final_lines.append("}")
    
    # Write the processed content back to the file
    with open(gephi_dot_filename, 'w', encoding='utf-8') as f:
        for line in final_lines:
            f.write(line + '\n')


def write_source_nodes_after_processing(gephi_dot_filename, source_nodes):
    """
    Ensures source nodes appear in the final DOT file, even after post-processing.
    This is a safeguard to ensure source nodes aren't accidentally filtered out.
    
    Args:
        gephi_dot_filename: Path to the Gephi DOT file
        source_nodes: List of source node definitions
    """
    with open(gephi_dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the position to insert nodes (after "digraph G {")
    insert_pos = 1  # Default to position after the first line
    for i, line in enumerate(lines):
        if line.strip() == "digraph G {":
            insert_pos = i + 1
            break
    
    # Insert blank line after digraph line if not already there
    if insert_pos < len(lines) and lines[insert_pos].strip() != "":
        lines.insert(insert_pos, "\n")
        insert_pos += 1
    
    # Check if source nodes already exist in the file
    existing_source_nodes = set()
    for line in lines:
        if "is_source_node=\"true\"" in line:
            # Extract the node ID
            node_match = re.search(r'"([^"]+)"', line)
            if node_match:
                existing_source_nodes.add(node_match.group(1))
    
    # Insert only source nodes that don't already exist
    new_lines = []
    for node_def in source_nodes:
        # Extract node ID
        node_match = re.search(r'"([^"]+)"', node_def)
        if node_match and node_match.group(1) not in existing_source_nodes:
            new_lines.append(node_def)
    
    # Only modify file if we have new nodes to add
    if new_lines:
        # Insert source nodes after the opening of the graph
        lines[insert_pos:insert_pos] = [node + "\n" for node in new_lines] + ["\n"]
        
        # Write back to the file
        with open(gephi_dot_filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)


