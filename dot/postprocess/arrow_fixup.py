"""
Arrow direction fixup for DOT files.
Processes DOT files to correct arrow directions based on node positions.
"""
from bootstrap.primary_imports import os, re, subprocess


def fix_arrow_directions(dot_filename, output_dot_filename=None):
    """
    Process a DOT file to fix arrow directions based on node positions.
    Makes edges point downward (top-to-bottom) by default, with special exceptions.
    Preserves all original edge attributes.
    """
    if output_dot_filename is None:
        # Use the original file name
        output_dot_filename = dot_filename

    # Validate that we can read the file
    try:
        # Read the DOT file with UTF-8 encoding
        with open(dot_filename, 'r', encoding='utf-8') as f:
            dot_content = f.read()
    except Exception:
        return dot_filename

    # Compute node positions
    node_positions = compute_node_positions(dot_filename)

    # If we couldn't compute node positions, return the original file
    if not node_positions:
        return dot_filename

    # Parse all edges from the DOT file
    edges = parse_edges(dot_content)

    # Identify edges that need direction reversal
    edges_to_reverse = identify_edges_to_reverse(edges, node_positions)

    if edges_to_reverse:
        # Modify the DOT content to reverse arrow directions
        modified_content = modify_arrow_directions(dot_content, edges_to_reverse)

        # Write the modified DOT file with UTF-8 encoding
        try:
            with open(output_dot_filename, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception:
            return dot_filename

    return output_dot_filename


def compute_node_positions(dot_filename):
    """
    Use GraphViz to compute the layout positions of all nodes.
    """
    try:
        # Get absolute path to the dot file
        dot_path = os.path.abspath(dot_filename)

        # Set a timeout to avoid hanging
        timeout_seconds = 30

        # Run dot with -Tplain to get node positions without rendering
        command = ["dot", "-Tplain", dot_path]

        result = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",  # Explicitly set encoding to UTF-8
            check=False,       # Don't raise exception - handle errors manually
            timeout=timeout_seconds  # Set a timeout to avoid hanging
        )

        # Check if the command was successful
        if result.returncode != 0:
            return {}

        plain_output = result.stdout
        if not plain_output:
            return {}

        # Extract node positions from plain output
        node_positions = {}
        line_count = 0

        # Process each line of the plain output
        for line in plain_output.splitlines():
            line_count += 1
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Only process node lines
            if line.startswith("node"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    try:
                        node_id = parts[1].strip('"')
                        x = float(parts[2])
                        y = float(parts[3])
                        node_positions[node_id] = {'x': x, 'y': y}
                    except Exception:
                        continue

        return node_positions

    except subprocess.TimeoutExpired:
        return {}
    except Exception:
        return {}


def parse_edges(dot_content):
    """
    Extract all directed edges from the DOT file content.
    Carefully preserve all original edge attributes.
    """
    edges = []
    
    # Regex to match edge definitions
    # This captures: source node, target node, and edge attributes if present
    edge_pattern = re.compile(r'"([^"]+)"\s+->\s+"([^"]+)"(?:\s+\[(.*?)\])?;', re.DOTALL)
    
    for match in edge_pattern.finditer(dot_content):
        source_id = match.group(1)
        target_id = match.group(2)
        attributes = match.group(3) or ""
        
        # Skip edges that are invisible
        if 'style="invis"' in attributes:
            continue
        
        # Check if this is an undirected edge - dir=none must be present WITHOUT dir="back"
        is_undirected = re.search(r'dir\s*=\s*["\']?none["\']?', attributes) is not None
        
        # Check if this edge already has dir="back"
        already_reversed = re.search(r'dir\s*=\s*["\']?back["\']?', attributes) is not None
        
        # Skip edges that have dir="both" or are bidirectional
        if re.search(r'dir\s*=\s*["\']?both["\']?', attributes):
            continue
        
        edges.append({
            'source': source_id,
            'target': target_id,
            'full_match': match.group(0),
            'attributes': attributes,
            'is_undirected': is_undirected,
            'already_reversed': already_reversed
        })
    
    return edges


def identify_edges_to_reverse(edges, node_positions):
    """
    Identify edges that need their arrow directions reversed to maintain proper logical flow.
    
    In DOT/GraphViz, edges naturally flow from top to bottom (rankdir="TB"), with
    arrows pointing downward by default. However, in our knowledge graph, many logical
    relationships (support, justification, entailment) should actually point upward
    to represent their true logical direction.
    
    This function identifies edges where:
    1. The source node is positioned ABOVE the target node in the visualization
       (meaning source_y < target_y, as y-coordinates increase going down)
    2. But the logical relationship actually flows upward
    
    These edges need to be reversed with dir="back" to ensure the arrows point
    in the logically correct direction in the final visualization.
    """
    edges_to_reverse = []
    
    for edge in edges:
        source_id = edge['source']
        target_id = edge['target']
        
        # Skip undirected edges (those with dir="none")
        if edge['is_undirected']:
            continue
            
        # Skip edges that are already reversed with dir="back"
        if edge['already_reversed']:
            continue
        
        # Check if both nodes have position information
        if source_id in node_positions and target_id in node_positions:
            source_y = node_positions[source_id]['y']
            target_y = node_positions[target_id]['y']
            
            # In DOT, y-coordinates increase going down from the top
            # We want arrows to point downward (top to bottom), which is the natural DOT direction
            # Therefore, we need to reverse edges where the source is positioned BELOW the target
            # This means source_y > target_y (since higher y means lower on the page)
            if source_y < target_y:
                edges_to_reverse.append(edge)
    
    return edges_to_reverse


def modify_arrow_directions(dot_content, edges_to_reverse):
    """
    Modify the DOT file to reverse the direction of specified edges.
    Carefully preserves all original edge attributes.
    """
    modified_content = dot_content
    
    for edge in edges_to_reverse:
        original_edge = edge['full_match']
        
        # Make sure we're not modifying an undirected edge
        if edge.get('is_undirected', False):
            continue
            
        # Make sure we're not modifying an already reversed edge
        if edge.get('already_reversed', False):
            continue
        
        # Prepare the modified edge with dir="back"
        if '[' in original_edge:
            # Edge already has attributes
            # Add dir="back" to existing attributes, preserving them all
            if edge['attributes']:
                if ',' in edge['attributes'].strip()[-1:]:
                    # If attributes end with a comma, just add dir="back"
                    new_attrs = edge['attributes'] + ' dir="back"'
                else:
                    # Otherwise, add comma and dir="back"
                    new_attrs = edge['attributes'] + ', dir="back"'
                    
                modified_edge = original_edge.replace(
                    f'[{edge["attributes"]}]', 
                    f'[{new_attrs}]'
                )
            else:
                # Empty attributes case
                modified_edge = original_edge.replace(
                    '[]', 
                    '[dir="back"]'
                )
        else:
            # Edge doesn't have attributes yet
            modified_edge = original_edge.replace(
                ';', 
                ' [dir="back"];'
            )
        
        # Replace the original edge with the modified one
        modified_content = modified_content.replace(original_edge, modified_edge)
    
    return modified_content
