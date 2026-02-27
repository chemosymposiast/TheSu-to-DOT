"""
DOT file reorganization orchestrator.

This module contains the main function for reorganizing DOT files
by source, handling propositions, theses, and clusters.
"""
from bootstrap.primary_imports import re

def reorganize_dot_file(dot_filename):
    """
    Post-process the DOT file to reorganize nodes and edges by source.
    - Move PROPOSITION nodes near their related source subgraphs based on MATCHES relationships
    - Group nodes and edges by their source attribute
    - Ensure proper spacing between elements
    - Preserve all clusters and their contents
    - Maintain relationships between nodes, edges, and clusters
    - Handle special attributes and directives properly
    """
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content into lines for processing
    original_lines = content.split('\n')
    lines = [line for line in original_lines]  # Create a copy we can modify
    
    # Dictionaries to track all PROPOSITION-related elements and whether they've been written
    all_propositions = {}  # {prop_id: {"node_line": line, "written": False}}
    all_prop_related_nodes = {}  # {node_id: {"node_line": line, "written": False}}
    all_prop_related_edges = {}  # {edge_key: {"edge_line": line, "written": False}}
    
    # Extract the header (everything before the first node, edge, or subgraph)
    header_lines = []
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('"') or line_stripped.startswith('subgraph '):
            break
        if line:  # Only add non-empty lines to header
            header_lines.append(line)
    
    # Track node definitions and their sources
    node_lines = {}  # {node_id: line}
    node_to_source = {}  # {node_id: source_id}
    
    # Track proposition nodes specifically
    proposition_ids = set()
    proposition_lines = {}  # {prop_id: line}
    
    # Track special nodes (_to_, _in_etiology_in_, _func, _employed)
    special_node_lines = {}  # {node_id: line}
    
    # Track nodes with gephi_omitted attribute
    omitted_node_ids = set()  # Nodes with gephi_omitted="true"
    
    # Track all edges
    edge_lines = {}  # {(source_id, target_id): line}
    edge_to_source = {}  # {(source_id, target_id): source_id}
    cross_source_edges = []  # Edges that span across different sources
    omitted_node_edges = []  # Edges connecting to omitted nodes
    
    # Track special edges (xlabel, lhead, etc.)
    special_edges = []  # All edges with special attributes like xlabel
    edges_with_lhead = {}  # {edge_key: cluster_name}
    
    # Track edges that need special placement
    xlabel_edges = {}  # {source_node: [edge_lines]} - edges with xlabel, mapped by source
    func_edges = {}  # {func_node: [edge_lines]} - edges starting from a _func node
    employed_edges = {}  # {employed_node: [edge_lines]} - edges ending with an _employed node
    
    # Track which edges have been placed
    placed_edges = set()  # Keep track of edges that have already been placed
    
    # Track "MATCHES" pseudo-nodes for propositions
    proposition_to_matches = {}  # {prop_id: [pseudo_node_id]}
    thesis_id_from_matches = {}  # {pseudo_node_id: thesis_id}
    
    # Track proposition-thesis relationships
    proposition_to_thesis = {}  # {prop_id: thesis_id} - Based on MATCHES relationships
    
    # Track all clusters
    clusters = {}  # {cluster_name: {"lines": [], "source": None, "owner": None}}
    proposition_clusters = set()  # Clusters owned by propositions
    thesis_clusters = set()  # Clusters owned by theses
    
    # Track all source subgraphs
    source_subgraphs = {}  # {source_id: {"nodes": [], "edges": [], "clusters": []}}
    
    # Track thesis nodes to their source
    thesis_to_source = {}  # {thesis_id: source_id}
    
    # Function to extract element ID from cluster name
    def extract_element_id(cluster_name):
        # First try to match entailed clusters specifically
        entailed_match = re.search(r'cluster_(.+)_ENTAILED', cluster_name)
        if entailed_match:
            # Get the element ID part before _ENTAILED
            raw_id = entailed_match.group(1)
            # Convert from underscore format back to dot format if needed
            element_id = raw_id.replace('_', '.') if '_' in raw_id else raw_id
            return element_id
            
        # Otherwise use the original pattern for regular clusters
        match = re.search(r'cluster_.*?_([PT]\d+)_', cluster_name)
        if match:
            return match.group(1)
        
        return None
    
    # Function to extract thesis ID from matches pseudo-node
    def extract_thesis_id(pseudo_node_id):
        # Look for pattern: *_to_*T####_#
        match = re.search(r'_to_.*?(T\d+)_\d+', pseudo_node_id)
        if match:
            return match.group(1)
        return None
    
    # Function to normalize source IDs
    def normalize_source_id(source_id):
        return source_id.replace('_', '-')
    
    # First, extract all nodes and identify propositions and special nodes
    referenced_in_nodes = {}  # Add this new dictionary to track all IS REFERENCED IN pseudo-nodes

    for line in lines:
        line_stripped = line.strip()
        # Check if this is a node definition
        if line_stripped.startswith('"') and ' -> ' not in line_stripped:
            # Extract the node ID
            node_match = re.match(r'"([^"]+)"', line_stripped)
            if not node_match:
                continue
                
            node_id = node_match.group(1)
            
            # Check if this is a node with gephi_omitted attribute
            if 'gephi_omitted="true"' in line:
                omitted_node_ids.add(node_id)
            
            # Check if this is a special node (_to_, _in_etiology_in_, _func, _employed)
            if '_to_' in node_id or '_in_etiology_in_' in node_id or node_id.endswith('_func') or node_id.endswith('_employed'):
                special_node_lines[node_id] = line
                
                # If this is a "MATCHES" pseudo-node, extract the thesis ID
                if '_to_' in node_id and ('MATCHES' in line or 'label=<MATCHES' in line or 'gephi_label="matc"' in line):
                    thesis_id = extract_thesis_id(node_id)
                    if thesis_id:
                        thesis_id_from_matches[node_id] = thesis_id
                
                continue
            
            # If this is a "IS REFERENCED IN" pseudo-node, extract the source and target elements
            if '_referenced-in_' in node_id and ('IS REFERENCED IN' in line or 'label=<IS REFERENCED IN' in line):
                parts = node_id.split('_referenced-in_')
                if len(parts) == 2:
                    source_element = parts[0]  # The element being referenced
                    target_parts = parts[1].split('_', 1)
                    if len(target_parts) >= 1:
                        target_element = target_parts[0]  # The element containing the reference
                        # Store the pseudo-node along with source and target info
                        referenced_in_nodes[node_id] = {
                            'node_line': line,
                            'source': source_element,
                            'target': target_element
                        }
                        # Store it in node_to_source if the source element has a source
                        if source_element in node_to_source:
                            node_to_source[node_id] = node_to_source[source_element]

            # Check if this is a proposition node
            if '<b>PROPOSITION</b>' in line:
                proposition_ids.add(node_id)
                proposition_lines[node_id] = line
                # Track in our all_propositions dictionary
                all_propositions[node_id] = {"node_line": line, "written": False}
                continue
            
            # Check if this is a thesis node and map to its source
            if '<b>THESIS</b>' in line:
                source_id = None
                source_match = re.search(r'source="([^"]+)"', line)
                if source_match:
                    source_id = normalize_source_id(source_match.group(1))
                    # Extract thesis ID from the node ID
                    thesis_id_match = re.search(r'(T\d+)$', node_id)
                    if thesis_id_match:
                        thesis_id = thesis_id_match.group(1)
                        thesis_to_source[thesis_id] = source_id
            
            node_lines[node_id] = line
            
            # Extract source information if available
            source_id = None
            source_id_match = re.search(r'source_id="([^"]+)"', line)
            source_match = re.search(r'source="([^"]+)"', line)
            
            if source_id_match:
                source_id = normalize_source_id(source_id_match.group(1))
            elif source_match:
                source_id = normalize_source_id(source_match.group(1))
            
            if source_id:
                node_to_source[node_id] = source_id
    
    # Next, extract all edges and identify special attributes

    for line in lines:
        line_stripped = line.strip()
        # Check if this is an edge definition
        if line_stripped.startswith('"') and ' -> ' in line_stripped:
            # Extract source and target node IDs
            edge_match = re.match(r'"([^"]+)" -> "([^"]+)"', line_stripped)
            if not edge_match:
                continue
                
            source_node, target_node = edge_match.group(1), edge_match.group(2)
            edge_key = (source_node, target_node)
            edge_lines[edge_key] = line
            
            # Track edges connected to proposition nodes
            if source_node in proposition_ids or target_node in proposition_ids:
                all_prop_related_edges[edge_key] = {"edge_line": line, "written": False}
                # If this connects a proposition to a pseudo-node, also track the pseudo-node
                if source_node in proposition_ids and '_to_' in target_node:
                    if target_node in special_node_lines:
                        all_prop_related_nodes[target_node] = {"node_line": special_node_lines[target_node], "written": False}
                elif target_node in proposition_ids and '_to_' in source_node:
                    if source_node in special_node_lines:
                        all_prop_related_nodes[source_node] = {"node_line": special_node_lines[source_node], "written": False}
            
            # Track edges with xlabel for special placement
            if 'xlabel=' in line:
                if source_node not in xlabel_edges:
                    xlabel_edges[source_node] = []
                xlabel_edges[source_node].append(line)
            
            # Track edges starting from _func nodes
            if source_node.endswith('_func'):
                if source_node not in func_edges:
                    func_edges[source_node] = []
                func_edges[source_node].append(line)
            
            # Track edges ending at _employed nodes
            if target_node.endswith('_employed'):
                if target_node not in employed_edges:
                    employed_edges[target_node] = []
                employed_edges[target_node].append(line)
            
            # If this is a proposition connecting to a matches pseudo-node, track it
            if source_node in proposition_ids and target_node in thesis_id_from_matches:
                if source_node not in proposition_to_matches:
                    proposition_to_matches[source_node] = []
                proposition_to_matches[source_node].append(target_node)
            
            # Check if this edge connects to any omitted node
            if source_node in omitted_node_ids or target_node in omitted_node_ids:
                omitted_node_edges.append(line)
                continue
            
            # Check if this edge has an lhead directive
            lhead_match = re.search(r'lhead="([^"]+)"', line)
            if lhead_match:
                cluster_name = lhead_match.group(1)
                edges_with_lhead[edge_key] = cluster_name
                if source_node in proposition_ids:
                    proposition_clusters.add(cluster_name)
                else:
                    thesis_clusters.add(cluster_name)
            
            # Track edges with special attributes (xlabel, etc.)
            if 'xlabel=' in line or 'fontcolor=' in line or 'penwidth=' in line:
                special_edges.append(line)
            
            # Determine the source for this edge
            if source_node in proposition_ids or target_node in proposition_ids:
                # If this edge involves a proposition, it stays with propositions
                continue
                
            # Try to determine source from connected nodes
            source_source_id = node_to_source.get(source_node)
            target_source_id = node_to_source.get(target_node)
            
            if source_source_id and target_source_id:
                # If both nodes have same source, use that
                if source_source_id == target_source_id:
                    edge_to_source[edge_key] = source_source_id
                else:
                    # Edge between different sources - special handling
                    cross_source_edges.append(line)
            elif source_source_id:
                edge_to_source[edge_key] = source_source_id
            elif target_source_id:
                edge_to_source[edge_key] = target_source_id
    
    # Extract all clusters with their content
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this starts a cluster
        if line.startswith('subgraph cluster_'):
            cluster_match = re.match(r'subgraph (cluster_[^\s{]+)', line)
            if cluster_match:
                cluster_name = cluster_match.group(1)
                cluster_lines = [lines[i]]  # Start with the opening line
                
                # Extract the complete cluster definition
                depth = 1  # For nested braces
                j = i + 1
                
                while j < len(lines) and depth > 0:
                    if '{' in lines[j] and '}' not in lines[j]:
                        depth += 1
                    elif '}' in lines[j] and '{' not in lines[j]:
                        depth -= 1
                    
                    cluster_lines.append(lines[j])
                    j += 1
                
                if depth != 0:
                    # Something went wrong with brace matching - unbalanced
                    i += 1
                    continue
                
                # Extract element ID from the cluster name
                element_id = extract_element_id(cluster_name)
                
                # Special handling for entailed clusters
                is_entailed_cluster = "_ENTAILED" in cluster_name
                
                # Store the cluster with its complete definition
                clusters[cluster_name] = {
                    "lines": cluster_lines,
                    "source": None,
                    "owner": None,
                    "element_id": element_id
                }
                
                # For entailed clusters, set the owner directly from the element_id
                if is_entailed_cluster and element_id:
                    # The thesis node itself is the owner
                    owner_node = element_id
                    clusters[cluster_name]["owner"] = owner_node
                    
                    # Determine cluster source from its owner
                    if owner_node in node_to_source:
                        clusters[cluster_name]["source"] = node_to_source[owner_node]
                else:
                    # Determine the owner of this cluster from edges with lhead (original method)
                    for edge_key, lhead_cluster in edges_with_lhead.items():
                        if lhead_cluster == cluster_name:
                            owner_node = edge_key[0]  # Source node of the edge
                            clusters[cluster_name]["owner"] = owner_node
                            
                            # Determine cluster source from its owner
                            if owner_node in node_to_source:
                                clusters[cluster_name]["source"] = node_to_source[owner_node]
                
                # Skip ahead to after the cluster
                i = j
                continue
        
        i += 1    

    # Extract all source subgraphs
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this starts a source subgraph
        if line.startswith('subgraph source_'):
            source_match = re.match(r'subgraph (source_[^\s{]+)', line)
            if source_match:
                subgraph_name = source_match.group(1)
                source_id = normalize_source_id(subgraph_name[7:])  # Remove 'source_' prefix
                
                # Initialize the source subgraph if needed
                if source_id not in source_subgraphs:
                    source_subgraphs[source_id] = {
                        "nodes": [],
                        "edges": [],
                        "clusters": [],
                        "opening": [line]
                    }
                
                # Extract the subgraph label if present
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('"') and not lines[j].strip().startswith('subgraph'):
                    if lines[j].strip().startswith('label='):
                        source_subgraphs[source_id]["opening"].append(lines[j])
                        break
                    j += 1
                
                # Skip ahead - we don't process source subgraph content directly
                # since we'll be rebuilding it
                i = j + 1
                continue
        
        i += 1
    
    # Step 2: Organize elements by source
    
    # Assign nodes to their source subgraphs
    for node_id, source_id in node_to_source.items():
        if source_id and node_id in node_lines and node_id not in proposition_ids:
            # Initialize the source subgraph if needed
            if source_id not in source_subgraphs:
                source_subgraphs[source_id] = {
                    "nodes": [],
                    "edges": [],
                    "clusters": [],
                    "opening": [f'subgraph source_{source_id.replace("-", "_")} {{', f'label="{source_id}";']
                }
            
            source_subgraphs[source_id]["nodes"].append(node_lines[node_id])
    
    # Assign edges to their source subgraphs
    for edge_key, source_id in edge_to_source.items():
        if source_id and edge_key in edge_lines:
            if source_id not in source_subgraphs:
                source_subgraphs[source_id] = {
                    "nodes": [],
                    "edges": [],
                    "clusters": [],
                    "opening": [f'subgraph source_{source_id.replace("-", "_")} {{', f'label="{source_id}";']
                }
            
            source_subgraphs[source_id]["edges"].append(edge_lines[edge_key])
    
    # Assign clusters to their source subgraphs
    for cluster_name, cluster_info in clusters.items():
        source_id = cluster_info["source"]
        if source_id and cluster_name not in proposition_clusters:
            if source_id not in source_subgraphs:
                source_subgraphs[source_id] = {
                    "nodes": [],
                    "edges": [],
                    "clusters": [],
                    "opening": [f'subgraph source_{source_id.replace("-", "_")} {{', f'label="{source_id}";']
                }
                
            source_subgraphs[source_id]["clusters"].extend(cluster_info["lines"])
    
    # Map propositions to their related thesis nodes
    proposition_sources = {}  # {prop_id: source_id}
    for prop_id, matches_list in proposition_to_matches.items():
        if matches_list:
            # Get the first MATCHES pseudo-node
            first_match = matches_list[0]
            # Get the thesis ID from this matches node
            thesis_id = thesis_id_from_matches.get(first_match)
            if thesis_id:
                proposition_to_thesis[prop_id] = thesis_id
                # Find the source of this thesis (still needed for organizing)
                source_id = thesis_to_source.get(thesis_id)
                if source_id:
                    proposition_sources[prop_id] = source_id
    
    # Count propositions per thesis for alternating placement
    thesis_prop_count_before = {}  # {thesis_id: count}
    thesis_prop_count_after = {}   # {thesis_id: count}
    
    # Initialize counters
    for thesis_id in thesis_to_source:
        thesis_prop_count_before[thesis_id] = 0
        thesis_prop_count_after[thesis_id] = 0
    
    # Create a map to track which propositions should be placed before/after each thesis
    thesis_props_before = {}  # {thesis_id: [prop_ids]}
    thesis_props_after = {}   # {thesis_id: [prop_ids]}
    
    # Decide placement for each proposition
    for prop_id, thesis_id in proposition_to_thesis.items():
        # Count propositions for this thesis
        thesis_prop_count = len([p for p in proposition_to_thesis if proposition_to_thesis[p] == thesis_id])
        
        # Place first half after, second half before (with rounding that favors after)
        if thesis_prop_count_after.get(thesis_id, 0) < (thesis_prop_count + 1) // 2:
            # Place this proposition after the thesis
            if thesis_id not in thesis_props_after:
                thesis_props_after[thesis_id] = []
            thesis_props_after[thesis_id].append(prop_id)
            thesis_prop_count_after[thesis_id] = thesis_prop_count_after.get(thesis_id, 0) + 1
        else:
            # Place this proposition before the thesis
            if thesis_id not in thesis_props_before:
                thesis_props_before[thesis_id] = []
            thesis_props_before[thesis_id].append(prop_id)
            thesis_prop_count_before[thesis_id] = thesis_prop_count_before.get(thesis_id, 0) + 1

    # Step 3: Build the reorganized content
    new_lines = []
    
    # Add header
    new_lines.extend(header_lines)
    new_lines.append('')

    # Function to add a node and its associated cluster
    def add_node_and_cluster(node_id, node_line):
        # Mark this node as written if it's tracked
        if node_id in all_propositions:
            all_propositions[node_id]["written"] = True
            
        # Check if this node has an entailed cluster
        entailed_cluster_name = f"cluster_{node_id.replace('.', '_')}_ENTAILED"
        is_entailed_cluster = entailed_cluster_name in clusters
        
        if is_entailed_cluster:
            # For entailed clusters, write the cluster structure with the node inside
            cluster_lines = clusters[entailed_cluster_name]["lines"]
            
            # 1. Find the subgraph opening line
            opening_line = None
            for line in cluster_lines:
                if line.strip().startswith('subgraph'):
                    opening_line = line
                    break
            
            if opening_line:
                # Write the subgraph opening line
                new_lines.append(opening_line)
                
                # 2. Write the label and style lines
                for line in cluster_lines:
                    if 'label=' in line or 'style=' in line:
                        new_lines.append(line)
                
                # 3. Write the node inside the cluster
                new_lines.append(node_line)
                new_lines.append('')
                
                # 4. Write special nodes
                for special_id, special_line in special_node_lines.items():
                    if special_id.startswith(node_id + '_') or special_id.endswith('_' + node_id):
                        new_lines.append(special_line)
                        new_lines.append('')
                        
                        # Mark this special node as written if it's tracked
                        if special_id in all_prop_related_nodes:
                            all_prop_related_nodes[special_id]["written"] = True
                        
                        # Add edges for special nodes
                        if special_id.endswith('_func') and special_id in func_edges:
                            for edge_line in func_edges[special_id]:
                                new_lines.append(edge_line)
                                new_lines.append('')
                                placed_edges.add(edge_line)
                        
                        if special_id.endswith('_employed') and special_id in employed_edges:
                            for edge_line in employed_edges[special_id]:
                                new_lines.append(edge_line)
                                new_lines.append('')
                                placed_edges.add(edge_line)
                    
                    # Handle IS REFERENCED IN pseudo-nodes
                    elif '_referenced-in_' in special_id and special_id.startswith(node_id + '_referenced-in_'):
                        new_lines.append(special_line)
                        new_lines.append('')
                
                # 5. Write the cluster closing brace
                new_lines.append('}')
                new_lines.append('')
            else:
                # If we can't find the opening line for some reason, create a new cluster
                new_lines.append(f'\nsubgraph {entailed_cluster_name} {{')
                new_lines.append('label=<<font color="#82b366">Entailed</font>>')
                new_lines.append('style="dotted";')
                new_lines.append('')
                new_lines.append(node_line)
                new_lines.append('')
                new_lines.append('}')
                new_lines.append('')
        else:
            # Normal case (not an entailed cluster)
            # Write the node first
            new_lines.append(node_line)
            new_lines.append('')
            
            # Handle special nodes
            for special_id, special_line in special_node_lines.items():
                if special_id.startswith(node_id + '_') or special_id.endswith('_' + node_id):
                    new_lines.append(special_line)
                    new_lines.append('')
                    
                    # Mark this special node as written if it's tracked
                    if special_id in all_prop_related_nodes:
                        all_prop_related_nodes[special_id]["written"] = True
                    
                    # Add edges starting from this _func node
                    if special_id.endswith('_func') and special_id in func_edges:
                        for edge_line in func_edges[special_id]:
                            new_lines.append(edge_line)
                            new_lines.append('')
                            placed_edges.add(edge_line)
                    
                    # Add edges ending at this _employed node
                    if special_id.endswith('_employed') and special_id in employed_edges:
                        for edge_line in employed_edges[special_id]:
                            new_lines.append(edge_line)
                            new_lines.append('')
                            placed_edges.add(edge_line)

            # Handle IS REFERENCED IN pseudo-nodes (both directions)
            for ref_id, ref_info in referenced_in_nodes.items():
                # Case 1: Current node is the source (referenced in another node)
                if ref_info['source'] == node_id:
                    new_lines.append(ref_info['node_line'])
                    new_lines.append('')
                    if 'edge_in' in ref_info and ref_info['edge_in'] not in placed_edges:
                        new_lines.append(ref_info['edge_in'])
                        new_lines.append('')
                        placed_edges.add(ref_info['edge_in'])
                    if 'edge_out' in ref_info and ref_info['edge_out'] not in placed_edges:
                        new_lines.append(ref_info['edge_out'])
                        new_lines.append('')
                        placed_edges.add(ref_info['edge_out'])
                
                # Case 2: Current node is the target (references another node)
                elif ref_info['target'] == node_id:
                    new_lines.append(ref_info['node_line'])
                    new_lines.append('')
                    if 'edge_in' in ref_info and ref_info['edge_in'] not in placed_edges:
                        new_lines.append(ref_info['edge_in'])
                        new_lines.append('')
                        placed_edges.add(ref_info['edge_in'])
                    if 'edge_out' in ref_info and ref_info['edge_out'] not in placed_edges:
                        new_lines.append(ref_info['edge_out']) 
                        new_lines.append('')
                        placed_edges.add(ref_info['edge_out'])

            # Find and add any other associated cluster
            associated_cluster = None
            for cluster_name, cluster_info in clusters.items():
                if cluster_info["element_id"] and node_id.endswith(cluster_info["element_id"]):
                    associated_cluster = cluster_name
                    break
            
            # Add the associated cluster if found
            if associated_cluster:
                for line in clusters[associated_cluster]["lines"]:
                    new_lines.append(line)
                new_lines.append('')
        
        # Handle xlabel edges for nodes in clusters - this is common to both cases
        if is_entailed_cluster or (not is_entailed_cluster and 'associated_cluster' in locals() and associated_cluster):
            cluster_name = entailed_cluster_name if is_entailed_cluster else associated_cluster
            # Extract all nodes in this cluster
            cluster_nodes = []
            for line in clusters[cluster_name]["lines"]:
                node_match = re.match(r'"([^"]+)"', line.strip())
                if node_match:
                    cluster_nodes.append(node_match.group(1))
            
            # Add xlabel edges for nodes in this cluster
            for cluster_node in cluster_nodes:
                if cluster_node in xlabel_edges:
                    for edge_line in xlabel_edges[cluster_node]:
                        new_lines.append(edge_line)
                        new_lines.append('')
                        placed_edges.add(edge_line)

    # Function to add a proposition with its cluster and edges
    def add_proposition_with_related_elements(prop_id):
        # Add the proposition node
        add_node_and_cluster(prop_id, proposition_lines[prop_id])
        
        # Add edges connected to this proposition that have special attributes
        for edge_key, line in edge_lines.items():
            source_node, target_node = edge_key
            if (source_node == prop_id or target_node == prop_id) and line in special_edges:
                if line not in placed_edges:  # Only add if not already placed
                    new_lines.append(line)
                    new_lines.append('')
                    placed_edges.add(line)
                    # Mark this edge as written if it's tracked
                    if edge_key in all_prop_related_edges:
                        all_prop_related_edges[edge_key]["written"] = True
        
        # Add edges to omitted nodes
        for line in omitted_node_edges:
            if (f'"{prop_id}" ->' in line or f'-> "{prop_id}"' in line) and line not in placed_edges:
                new_lines.append(line)
                new_lines.append('')
                placed_edges.add(line)
        
        # Add other edges connected to this proposition
        for edge_key, line in edge_lines.items():
            source_node, target_node = edge_key
            if source_node == prop_id or target_node == prop_id:
                if line not in special_edges and line not in omitted_node_edges and line not in placed_edges:
                    new_lines.append(line)
                    new_lines.append('')
                    placed_edges.add(line)
                    # Mark this edge as written if it's tracked
                    if edge_key in all_prop_related_edges:
                        all_prop_related_edges[edge_key]["written"] = True
    
    # Process each source subgraph
    source_ids = source_subgraphs
    for source_id in source_ids:
        elements = source_subgraphs[source_id]
        
        # Skip empty sources
        if not elements["nodes"] and not elements["clusters"] and not elements["edges"]:
            continue
        
        # Add subgraph opening
        new_lines.append('')
        for line in elements["opening"]:
            new_lines.append(line)
        new_lines.append('')
        
        # Get all thesis nodes in this source
        thesis_nodes_in_source = []
        for node_line in elements["nodes"]:
            node_match = re.match(r'"([^"]+)"', node_line)
            if node_match:
                node_id = node_match.group(1)
                # Check if this is a thesis node
                thesis_id_match = re.search(r'(T\d+)$', node_id)
                if thesis_id_match and '<b>THESIS</b>' in node_line:
                    thesis_id = thesis_id_match.group(1)
                    thesis_nodes_in_source.append((node_id, node_line, thesis_id))
        
        # Add nodes for this source with thesis-proposition pairing
        for node_line in elements["nodes"]:
            # Skip thesis nodes as they'll be handled in thesis-proposition pairs
            node_match = re.match(r'"([^"]+)"', node_line)
            if node_match:
                node_id = node_match.group(1)
                
                # Check if this is a thesis node
                thesis_id_match = re.search(r'(T\d+)$', node_id)
                if thesis_id_match and '<b>THESIS</b>' in node_line:
                    # This is a thesis node - get its ID
                    thesis_id = thesis_id_match.group(1)
                    
                    # Add propositions that should appear before this thesis
                    if thesis_id in thesis_props_before:
                        for prop_id in thesis_props_before[thesis_id]:
                            if prop_id in proposition_lines:  # Check if we have this proposition
                                add_proposition_with_related_elements(prop_id)
                    
                    # Add the thesis node and its associated cluster
                    add_node_and_cluster(node_id, node_line)
                    
                    # Add propositions that should appear after this thesis
                    if thesis_id in thesis_props_after:
                        for prop_id in thesis_props_after[thesis_id]:
                            if prop_id in proposition_lines:  # Check if we have this proposition
                                add_proposition_with_related_elements(prop_id)
                else:
                    # This is not a thesis node, add it normally
                    # (except proposition nodes which will be added with their thesis)
                    if node_id not in proposition_ids:
                        add_node_and_cluster(node_id, node_line)
        
        # Add edges for this source
        for edge_line in elements["edges"]:
            # Skip edges that were already added elsewhere
            if edge_line not in placed_edges:
                new_lines.append(edge_line)
                new_lines.append('')
                placed_edges.add(edge_line)
        
        # Close the source subgraph
        new_lines.append('}')
        new_lines.append('')
    
    # Add any unmapped propositions at the end
    unmapped_propositions = [p for p in proposition_ids if p not in proposition_to_thesis]
    for prop_id in unmapped_propositions:
        if prop_id in proposition_lines:  # Check if we have this proposition
            add_proposition_with_related_elements(prop_id)
    
    # Add all remaining special edges that haven't been placed yet
    for line in special_edges:
        if line not in placed_edges:
            new_lines.append(line)
            new_lines.append('')
            placed_edges.add(line)
    
    # Add remaining omitted node edges that haven't been placed yet
    for line in omitted_node_edges:
        if line not in placed_edges:
            new_lines.append(line)
            new_lines.append('')
            placed_edges.add(line)
    
    # Add remaining cross-source edges that haven't been placed yet
    for line in cross_source_edges:
        if line not in placed_edges:
            new_lines.append(line)
            new_lines.append('')
            placed_edges.add(line)
    
    # First add any unwritten proposition nodes
    has_catch_all_content = (
        any(not info["written"] for info in all_propositions.values()) or
        any(not info["written"] for info in all_prop_related_nodes.values()) or
        any(not info["written"] and info["edge_line"] not in placed_edges
            for info in all_prop_related_edges.values())
    )
    if has_catch_all_content:
        new_lines.append('// Catch-all: propositions, MATCHES pseudo-nodes, prop-related edges; filtered pseudo-nodes may follow')
        new_lines.append('')
    
    for prop_id, info in all_propositions.items():
        if not info["written"]:
            new_lines.append(info["node_line"])
            new_lines.append('')
    
    # Then add any unwritten proposition-related nodes (like pseudo-nodes)
    for node_id, info in all_prop_related_nodes.items():
        if not info["written"]:
            new_lines.append(info["node_line"])
            new_lines.append('')
    
    # Finally add any unwritten proposition-related edges
    for edge_key, info in all_prop_related_edges.items():
        if not info["written"] and info["edge_line"] not in placed_edges:
            source_node, target_node = edge_key
            new_lines.append(info["edge_line"])
            new_lines.append('')
            placed_edges.add(info["edge_line"])
    
    # Close the main digraph
    new_lines.append('}')
    
    # Clean up multiple empty lines
    cleaned_lines = []
    prev_line_empty = False
    for line in new_lines:
        if not line.strip():
            if not prev_line_empty:
                cleaned_lines.append(line)
                prev_line_empty = True
        else:
            cleaned_lines.append(line)
            prev_line_empty = False
    
    # Write the reorganized content back to the file
    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))


