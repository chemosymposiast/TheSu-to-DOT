"""
Edge validation and redirection functions for DOT files.

This module handles validation of edges and redirection of invalid edges
to their ancestor THESIS elements. When elements_to_exclude is set, missing
nodes that are excluded elements are substituted with "filtered" pseudo-nodes
instead of being redirected or removed.
"""
from bootstrap.primary_imports import re
from bootstrap.delayed_imports import ET

# Styling for filtered pseudo-nodes (mirrors omitted nodes from dot/support.py)
_FILTERED_NODE_STYLES = {
    "THESIS": {"fill": "#f0faf0", "border": "#82b366", "shape": "box", "style": "rounded,filled", "gephi_label": "THES"},
    "SUPPORT": {"fill": "#dae8fc", "border": "#7c9ac7", "shape": "ellipse", "style": "rounded,filled", "gephi_label": "SUPP"},
}


def _infer_element_type_from_id(node_id):
    """Infer THESIS or SUPPORT from node ID pattern (e.g. T190127 -> THESIS, S184328 -> SUPPORT)."""
    id_parts = node_id.split(".")
    last_part = id_parts[-1] if id_parts else node_id
    if last_part.upper().startswith("T") and last_part[1:2].isdigit():
        return "THESIS"
    if last_part.upper().startswith("S") and last_part[1:2].isdigit():
        return "SUPPORT"
    return "THESIS"  # Default fallback


def _get_excluded_element_type(elem_id, xml_root, namespaces):
    """Get element type (THESIS/SUPPORT) from XML, or infer from ID."""
    if xml_root is None:
        return _infer_element_type_from_id(elem_id)
    try:
        elements = xml_root.xpath(f'.//*[@xml:id="{elem_id}"]', namespaces=namespaces)
        if not elements:
            # Try with just the local part (e.g. T190127 from tlg0007_tlg112.T190127)
            id_parts = elem_id.split(".")
            if len(id_parts) > 1:
                elements = xml_root.xpath(f'.//*[@xml:id="{id_parts[-1]}"]', namespaces=namespaces)
        if elements:
            tag = elements[0].tag
            if "THESIS" in tag:
                return "THESIS"
            if "SUPPORT" in tag:
                return "SUPPORT"
    except Exception:
        pass
    return _infer_element_type_from_id(elem_id)


def _make_filtered_node_line(excluded_id, element_type):
    """Create a DOT node definition line for a filtered pseudo-node."""
    style = _FILTERED_NODE_STYLES.get(element_type, _FILTERED_NODE_STYLES["THESIS"])
    gephi_label = style.get("gephi_label", "ELEM")
    label = f"<b>{element_type}</b><br/><i>(filtered)</i>"
    # Extract source from excluded_id (e.g. tlg0007_tlg112.T190127 -> tlg0007_tlg112)
    source_attr = ""
    if "." in excluded_id:
        source_id = excluded_id.rsplit(".", 1)[0]
        source_attr = f', source="{source_id}"'
    return (
        f'"{excluded_id}_filtered" [label=<{label}>, gephi_label="{gephi_label}", '
        f'gephi_filtered="true", fontsize="11", fillcolor="{style["fill"]}", '
        f'color="{style["border"]}", style="{style["style"]}", shape="{style["shape"]}"{source_attr}];\n\n'
    )


def redirect_or_remove_invalid_edges(dot_filename, xml_filename, namespaces, elements_to_exclude=None):
    """
    Removes edges where one or both referenced nodes do not have an explicit definition
    in the DOT file. Before removing:
    - If the missing node is in elements_to_exclude, substitutes it with a "filtered" pseudo-node.
    - Otherwise, tries to preserve edges by redirecting missing nodes to their ancestor
      THESIS elements if the ancestor exists as a defined node in the DOT.
    Uses strict line-by-line parsing based on DOT syntax.
    Re-parses the original XML file to ensure ancestor lookups are accurate.
    """
    # --- Re-parse the original XML file ---
    xml_root_original = None
    try:
        xml_tree_original = ET.parse(xml_filename)
        xml_root_original = xml_tree_original.getroot()
        # Successfully re-parsed original XML
    except ET.ParseError as e:
        print(f"ERROR: Failed to re-parse original XML file '{xml_filename}': {e}")
        print("WARNING: Ancestor redirection for missing nodes will be skipped.")
    except FileNotFoundError:
        print(f"ERROR: Original XML file not found at '{xml_filename}'")
        print("WARNING: Ancestor redirection for missing nodes will be skipped.")

    # Read the DOT file lines
    with open(dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # --- Pass 1: Identify all explicitly defined nodes and all edge references --- 
    defined_nodes = set()
    edge_references = set() # All nodes mentioned in edges
    edges_data = [] # Store tuples of (line_index, source, target, original_line)
    
    # Regex patterns based on strict DOT syntax
    # Node: optional space, quoted ID, optional attrs in [], optional ;, optional space
    # Must NOT contain ->
    node_def_pattern = re.compile(r'^\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$') 
    # Edge: optional space, quoted ID, ->, quoted ID, optional attrs in [], optional ;, optional space
    edge_def_pattern = re.compile(r'^\s*"([^"]+)"\s*->\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$')

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Skip empty lines and simple comments
        if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('#'):
            continue
            
        # Skip graph/subgraph/attribute lines that don't define nodes/edges
        if line_stripped.startswith(('digraph', 'graph', 'subgraph', '{', '}')) or \
           ( '=' in line_stripped and '->' not in line_stripped and not line_stripped.startswith('"') ):
             continue

        # IMPORTANT: Check for edge first because its pattern is more specific
        edge_match = edge_def_pattern.match(line_stripped)
        if edge_match:
            source = edge_match.group(1)
            target = edge_match.group(2)
            edge_references.add(source)
            edge_references.add(target)
            edges_data.append((i, source, target, line))
            # print(f"  Line {i+1}: Found edge {source} -> {target}")
            continue # Found an edge, move to next line

        # If not an edge, check if it's a node definition
        node_match = node_def_pattern.match(line_stripped)
        if node_match:
            # Check again it doesn't contain '->' just to be absolutely sure
            if '->' not in line_stripped:
                 node_id = node_match.group(1)
                 defined_nodes.add(node_id)
                 # print(f"  Line {i+1}: Found node definition {node_id}")
                 continue # Found a node, move to next line
        
        # If it's neither a node nor an edge according to patterns, we keep it as is (could be complex attribute etc.)
        # print(f"  Line {i+1}: Kept non-node/edge line: {line_stripped}")

    # --- Calculate Missing Nodes --- 
    missing_nodes = edge_references - defined_nodes

    # --- Build excluded set and type mapping ---
    excluded_set = set()
    excluded_type_cache = {}
    if elements_to_exclude:
        excluded_set = set(str(x).strip() for x in elements_to_exclude if x)
    for elem_id in excluded_set:
        excluded_type_cache[elem_id] = _get_excluded_element_type(elem_id, xml_root_original, namespaces)

    # Track filtered nodes we create (to avoid duplicates and to add definitions)
    filtered_nodes_to_add = {}  # excluded_id -> node_definition_line

    # --- Helper function to find ancestor THESIS --- 
    # Ensure ancestor check uses the definitive `defined_nodes` set and the re-parsed XML
    def find_thesis_ancestor(node_id, valid_defined_nodes, xml_root_to_search, local_namespaces):
        if xml_root_to_search is None: # Skip if original XML failed to parse
             return None
             
        id_parts = node_id.split('.')
        extracted_id = id_parts[-1] if len(id_parts) > 1 else node_id
        # print(f"  Attempting XML lookup for node_id: {node_id} (using extracted: {extracted_id})")
        found_element = None
        try:
            for lookup_id in [node_id, extracted_id]:
                if not lookup_id: continue
                # Use the provided xml_root_to_search and local_namespaces
                xpath_query = f'//*[@xml:id="{lookup_id}"]'
                elements = xml_root_to_search.xpath(xpath_query, namespaces=local_namespaces)
                if elements and len(elements) > 0:
                    found_element = elements[0]
                    # print(f"    Found XML element with ID '{lookup_id}', tag: {found_element.tag}")
                    break
            if found_element is None: return None
            # Use the provided local_namespaces for tag checking
            if found_element.tag == f'{{{local_namespaces["thesu"]}}}THESIS':
                thesis_id = found_element.get(f'{{{local_namespaces["xml"]}}}id')
                # print(f"    Element itself is THESIS '{thesis_id}'")
                if thesis_id in valid_defined_nodes: return thesis_id
            # Use the provided local_namespaces for ancestor lookup
            ancestors = found_element.xpath('ancestor::thesu:THESIS', namespaces=local_namespaces)
            if ancestors and len(ancestors) > 0:
                ancestor_thesis = ancestors[0]
                thesis_id = ancestor_thesis.get(f'{{{local_namespaces["xml"]}}}id')
                # print(f"    Found THESIS ancestor '{thesis_id}' in XML.")
                if thesis_id in valid_defined_nodes:
                    # print(f"    Ancestor THESIS '{thesis_id}' exists in DOT. Using it.")
                    return thesis_id
                # else: print(f"    Ancestor THESIS '{thesis_id}' NOT FOUND in DOT.")
        except Exception as e:
            print(f"    XML lookup error for {node_id}: {str(e)}")
        return None

    # --- Pass 2: Process lines, modify/remove invalid edges --- 
    processed_lines = {} # Use dict to store lines by index, allows modification/removal
    for i, line in enumerate(lines):
        processed_lines[i] = line # Initialize with original lines
        
    edges_to_process = sorted(edges_data, key=lambda x: x[0], reverse=True) # Process bottom-up
    
    invalid_removed_count = 0
    preserved_redirected_count = 0

    for index, source_node, target_node, original_line in edges_to_process:
        source_missing = source_node in missing_nodes
        target_missing = target_node in missing_nodes

        if not source_missing and not target_missing:
            # print(f"  Line {index+1}: Kept valid edge: {original_line.strip()}")
            continue # Both nodes defined, edge is valid

        # --- Edge has at least one missing node --- 
        final_source = source_node
        final_target = target_node
        can_preserve = True # Assume we can preserve initially
        needs_modification = False

        # Attempt to resolve missing source: prefer filtered pseudo-node if excluded
        if source_missing:
            if source_node in excluded_set:
                final_source = f"{source_node}_filtered"
                needs_modification = True
                if source_node not in filtered_nodes_to_add:
                    elem_type = excluded_type_cache.get(source_node, _infer_element_type_from_id(source_node))
                    filtered_nodes_to_add[source_node] = _make_filtered_node_line(source_node, elem_type)
            else:
                ancestor = find_thesis_ancestor(source_node, defined_nodes, xml_root_original, namespaces)
                if ancestor:
                    final_source = ancestor
                    needs_modification = True
                else:
                    can_preserve = False # Cannot resolve source, edge must be removed

        # Attempt to resolve missing target (only if source is resolved or wasn't missing)
        if target_missing and can_preserve:
            if target_node in excluded_set:
                final_target = f"{target_node}_filtered"
                needs_modification = True
                if target_node not in filtered_nodes_to_add:
                    elem_type = excluded_type_cache.get(target_node, _infer_element_type_from_id(target_node))
                    filtered_nodes_to_add[target_node] = _make_filtered_node_line(target_node, elem_type)
            else:
                ancestor = find_thesis_ancestor(target_node, defined_nodes, xml_root_original, namespaces)
                if ancestor:
                    final_target = ancestor
                    needs_modification = True
                else:
                    can_preserve = False # Cannot resolve target, edge must be removed
        
        # Ensure we don't create self-loops after redirection
        if final_source == final_target:
             can_preserve = False

        # Apply changes based on preservation possibility
        if can_preserve:
            if needs_modification:
                # Safely reconstruct the line to preserve attributes
                indentation = original_line[:len(original_line) - len(original_line.lstrip())]
                original_target_str = f'"{target_node}"'
                target_end_pos_match = re.search(re.escape(original_target_str), original_line)

                if target_end_pos_match:
                    target_end_pos = target_end_pos_match.end()
                    rest_of_line = original_line[target_end_pos:]
                    # Construct the new line carefully, preserving the part after the target ID
                    modified_line = f'{indentation}"{final_source}" -> "{final_target}"{rest_of_line}'
                    # print(f"  MODIFIED line {index+1} to: {modified_line.strip()}") # Optional debug
                else:
                    # Fallback or error if the original target string isn't found (shouldn't happen)
                    print(f"  WARNING: Could not locate target node '{target_node}' in line {index+1} for safe modification. Removing edge.")
                    modified_line = None # Mark for removal if reconstruction fails

                # Check if modification resulted in removal
                if modified_line is None:
                    processed_lines[index] = None
                    # Avoid double counting if already marked for removal
                    if not (source_missing or target_missing): # Only increment if it wasn't already doomed
                         invalid_removed_count += 1
                    continue # Skip incrementing preserved count
                else:
                     processed_lines[index] = modified_line
                     preserved_redirected_count += 1

            # else: No modification needed, edge was already valid and can_preserve is True
            # No action needed here, the original line remains in processed_lines[index]
        else:
            # Cannot preserve, mark for removal
            processed_lines[index] = None # Mark for removal
            invalid_removed_count += 1

    # --- Filter out removed lines and create final output --- 
    final_lines = [line for i, line in sorted(processed_lines.items()) if line is not None]

    # --- Insert filtered node definitions before the final closing brace ---
    if filtered_nodes_to_add:
        closing_brace_index = -1
        for i in range(len(final_lines) - 1, -1, -1):
            if final_lines[i].strip() == "}":
                closing_brace_index = i
                break
        if closing_brace_index >= 0:
            insert_lines = [""] + list(filtered_nodes_to_add.values())
            final_lines = final_lines[:closing_brace_index] + insert_lines + final_lines[closing_brace_index:]
            print(f"  Added {len(filtered_nodes_to_add)} filtered pseudo-node(s) for excluded elements.")

    # --- Final Report --- 
    print(f"  Removed {invalid_removed_count} invalid edges.")
    print(f"  Preserved/redirected {preserved_redirected_count} edges with originally missing nodes.")
    # --- Write the processed content back to the file ---
    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
