"""Pseudo-node ID generation for DOT graphs.

Key functions: pseudo_node_exists, generate_unique_pseudo_node_id_*
"""


def pseudo_node_exists(written_lines, unique_id):
    """Return True if a pseudo-node with the given unique_id already exists in written_lines."""
    for line in written_lines:
        if f'"{unique_id}"' in line:
            return True
    return False

def generate_unique_pseudo_node_id_targets(written_lines, element_id, target_ref, suffix):
    """Generate a unique ID for target pseudo-nodes, avoiding collisions with existing written lines."""
    unique_id = f"{element_id}_to_{target_ref}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{element_id}_to_{target_ref}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{element_id}_to_{target_ref}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_entailments(written_lines, entailed_by_ref, element_id, suffix):
    """Generate a unique ID for entailment pseudo-nodes, avoiding collisions with existing written lines."""
    unique_id = f"{entailed_by_ref}_to_{element_id}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{entailed_by_ref}_to_{element_id}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{entailed_by_ref}_to_{element_id}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_etiologies(written_lines, referenced_id, element_id, suffix):
    """
    Generate a unique ID for etiology pseudo-nodes.
    
    Args:
        written_lines: List of lines already written to the DOT file
        referenced_id: ID of the referenced element in the etiology
        element_id: ID of the element containing the etiology
        suffix: A suffix to ensure uniqueness
        
    Returns:
        str: A unique ID for the pseudo-node
    """
    base_id = f"{referenced_id}_in_etiology_in_{element_id}_{suffix}"
    while any(base_id in line for line in written_lines):
        suffix += 1
        base_id = f"{referenced_id}_in_etiology_in_{element_id}_{suffix}"
    return base_id

def generate_unique_pseudo_node_id_analogies(written_lines, referenced_id, element_id, suffix):
    """
    Generate a unique ID for analogy pseudo-nodes.
    
    Args:
        written_lines: List of lines already written to the DOT file
        referenced_id: ID of the referenced element in the analogy
        element_id: ID of the element containing the analogy
        suffix: A suffix to ensure uniqueness
        
    Returns:
        str: A unique ID for the pseudo-node
    """
    unique_id = f"{referenced_id}_analogy_to_{element_id}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{referenced_id}_analogy_to_{element_id}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{referenced_id}_analogy_to_{element_id}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_references(written_lines, element_id, referenced_id, suffix):
    """
    Generate a unique ID for reference pseudo-nodes.
    
    Args:
        written_lines: List of lines already written to the DOT file
        element_id: ID of the element containing the reference
        referenced_id: ID of the referenced element
        suffix: A suffix to ensure uniqueness
        
    Returns:
        str: A unique ID for the pseudo-node
    """
    unique_id = f"{referenced_id}_referenced-in_{element_id}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{referenced_id}_referenced-in_{element_id}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{referenced_id}_referenced-in_{element_id}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_matching_propositions(written_lines, prop_ref, element_id, suffix):
    """Generate a unique ID for matching-proposition pseudo-nodes, avoiding collisions with existing written lines."""
    unique_id = f"{prop_ref}_to_{element_id}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{prop_ref}_to_{element_id}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{prop_ref}_to_{element_id}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_matching_sequences(written_lines, cluster_id, prop_cluster_id, suffix):
    """Generate a unique ID for matching-sequence pseudo-nodes, avoiding collisions with existing written lines."""
    unique_id = f"{cluster_id}_to_{prop_cluster_id}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{cluster_id}_to_{prop_cluster_id}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{cluster_id}_to_{prop_cluster_id}_{numeric_suffix}"
        return unique_id

def generate_unique_pseudo_node_id_matching_phases(written_lines, prop_phase_ref, current_phase, suffix):
    """Generate a unique ID for matching-phase pseudo-nodes, avoiding collisions with existing written lines."""
    unique_id = f"{prop_phase_ref}_to_{current_phase}_{suffix}"
    
    # If the suffix is a string like "unspecified", we need to handle differently
    if isinstance(suffix, str) and not suffix.isdigit():
        counter = 1
        temp_unique_id = unique_id
        while pseudo_node_exists(written_lines, temp_unique_id):
            temp_unique_id = f"{prop_phase_ref}_to_{current_phase}_{suffix}_{counter}"
            counter += 1
        return temp_unique_id
    else:
        # Original logic for numeric suffixes
        numeric_suffix = int(suffix) if isinstance(suffix, str) else suffix
        while pseudo_node_exists(written_lines, unique_id):
            numeric_suffix += 1
            unique_id = f"{prop_phase_ref}_to_{current_phase}_{numeric_suffix}"
        return unique_id
