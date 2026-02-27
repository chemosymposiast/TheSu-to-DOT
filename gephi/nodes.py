"""
Node finding functions for Gephi transformation.
"""
import re

def find_gephi_matching_proposition_nodes(dot_content):
    """
    Find all matching proposition pseudo-nodes in the DOT content.
    
    Returns:
        dict: {pseudo_node_id: {'source': prop_id, 'target': element_id, 'type': matching_type_str}}
    """
    matching_nodes = {}
    
    # Find all matching proposition pseudo-nodes
    matching_node_pattern = re.compile(r'"([^"]+_to_[^"]+_\d+)" \[label=<(?:MATCHES<br/><i>(.*?)</i>|MATCHES)>')
    for match in matching_node_pattern.finditer(dot_content):
        pseudo_id = match.group(1)
        matching_type = match.group(2) if match.group(2) else "matches"
        matching_nodes[pseudo_id] = {'type': matching_type, 'source': None, 'target': None}
        
    return matching_nodes


def find_gephi_employed_nodes(dot_content):
    """
    Find all "EMPLOYED IN" pseudo-nodes in the DOT content.
    
    Returns:
        dict: {employed_node_id: {'sources': [elements], 'target': support_id}}
    """
    employed_nodes = {}
    
    # Find all "EMPLOYED IN" pseudo-nodes
    employed_node_pattern = re.compile(r'"([^"]+_employed)" \[label="EMPLOYED IN"')
    for match in employed_node_pattern.finditer(dot_content):
        employed_id = match.group(1)
        employed_nodes[employed_id] = {'sources': [], 'target': None}
        
    return employed_nodes


def find_gephi_function_nodes(dot_content):
    """
    Find all function nodes (used for target mediation) in the DOT content.
    
    Returns:
        dict: {func_node_id: {'source': support_id, 'targets': [target_ids], 'function': function_label}}
    """
    function_nodes = {}
    
    # Find all function nodes (used for target mediation)
    function_node_pattern = re.compile(r'"([^"]+_func)" \[label="([^"]+)", gephi_label="[^"]+", gephi_omitted="false"')
    for match in function_node_pattern.finditer(dot_content):
        func_id = match.group(1)
        function_label = match.group(2)
        function_nodes[func_id] = {'source': None, 'targets': [], 'function': function_label}
        
    return function_nodes


def find_gephi_entailment_nodes(dot_content):
    """
    Find all entailment pseudo-nodes in the DOT content.
    
    Returns:
        dict: {pseudo_node_id: {'source': entailing_id, 'target': entailed_id, 'entailed_as': entailed_as}}
    """
    entailment_nodes = {}
    
    # Find all entailment pseudo-nodes - they have labels containing "ENTAILS"
    entailment_pattern = re.compile(r'"([^"]+_to_[^"]+_\d+)" \[label=<by ([^,]+),<br/>ENTAILS>')
    for match in entailment_pattern.finditer(dot_content):
        pseudo_id = match.group(1)
        entailed_as = match.group(2)
        entailment_nodes[pseudo_id] = {'source': None, 'target': None, 'entailed_as': entailed_as}
        
    return entailment_nodes


def find_gephi_etiology_nodes(dot_content):
    """
    Find all etiology pseudo-nodes in the DOT content.
    
    Returns:
        dict: {pseudo_node_id: {'source': source_id, 'target': target_id, 'relation_type': str}}
    """
    etiology_nodes = {}
    
    # Find all etiology pseudo-nodes - they have labels containing etiology relationship types
    patterns = [
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<ITS EFFECT<br/>in etiology>', 'EFFECT'),
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<ITS MEANS<br/>in etiology>', 'MEANS'),
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<ITS CAUSE<br/>in etiology>', 'CAUSE'),
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<ITS PURPOSE<br/>in etiology>', 'PURPOSE'),
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<ITS CAUSE & PURPOSE<br/>in etiology>', 'CAUSE_PURPOSE'),
        (r'"([^"]+_in_etiology_in_[^"]+_\d+)" \[label=<CORRELATED<br/>in etiology>', 'CORRELATED')
    ]
    
    # Find all etiology nodes
    for pattern, relation_type in patterns:
        for match in re.finditer(pattern, dot_content):
            pseudo_id = match.group(1)
            etiology_nodes[pseudo_id] = {'source': None, 'target': None, 'relation_type': relation_type}
    
    return etiology_nodes


def find_gephi_analogy_nodes(dot_content):
    """
    Find all analogy pseudo-nodes in the DOT content.
    
    Returns:
        dict: {pseudo_node_id: {'source': source_id, 'target': target_id, 'is_comparans': bool}}
    """
    analogy_nodes = {}
    
    # Find all analogy pseudo-nodes - they have labels containing "compared"
    comparans_pattern = re.compile(r'"([^"]+_analogy_to_[^"]+_\d+)" \[label=<<i>as source</i>,<br/>COMPARED IN>')
    normal_pattern = re.compile(r'"([^"]+_analogy_to_[^"]+_\d+)" \[label=<COMPARED IN>')
    
    # Find comparans nodes
    for match in comparans_pattern.finditer(dot_content):
        pseudo_id = match.group(1)
        analogy_nodes[pseudo_id] = {'source': None, 'target': None, 'is_comparans': True}
    
    # Find regular analogy nodes
    for match in normal_pattern.finditer(dot_content):
        pseudo_id = match.group(1)
        analogy_nodes[pseudo_id] = {'source': None, 'target': None, 'is_comparans': False}
        
    return analogy_nodes


def find_gephi_reference_nodes(dot_content):
    """Find all reference pseudo-nodes in the DOT file."""
    reference_nodes = {}
    
    # Pattern to match reference pseudo-nodes by ID pattern even if node definition is missing
    # This will find any node IDs with the _referenced-in_ pattern in edges
    edge_pattern = r'"([^"]+_referenced-in_[^"]+)" -> |-> "([^"]+_referenced-in_[^"]+)"'
    
    # Find all reference pseudo-node IDs in edges
    for match in re.finditer(edge_pattern, dot_content):
        node_id = match.group(1) if match.group(1) else match.group(2)
        if node_id not in reference_nodes:
            reference_nodes[node_id] = None
    
    # Then find proper node definitions if they exist
    for node_id in list(reference_nodes.keys()):
        node_pattern = r'"' + re.escape(node_id) + r'" \[(.*?)label=<IS REFERENCED IN(.*?)\];'
        node_match = re.search(node_pattern, dot_content, re.DOTALL)
        if node_match:
            reference_nodes[node_id] = node_match.group(0)
    
    return reference_nodes


