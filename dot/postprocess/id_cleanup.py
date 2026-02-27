"""
ID cleanup functions for DOT files.

This module handles replacement and cleanup of XML IDs in DOT files.
"""
from bootstrap.primary_imports import re


def replace_original_xml_ids(dot_filename):
    """
    Post-process the DOT file to replace any references to original_xml_id with the actual node ID.
    Also handles cases where original_xml_id was incorrectly written as c=.
    """
    # Read the file content
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Step 1: Build a mapping from H IDs to q IDs
    h_to_q_mapping = {}
    
    # Find all nodes with original_xml_id attributes
    original_id_pattern = re.compile(r'"([^"]+\.q\d{9})"[^[]*\[.*?original_xml_id="([^"]+\.H\d{6})"')
    for match in original_id_pattern.finditer(content):
        q_id = match.group(1)
        h_id = match.group(2)
        
        # Store the mapping: Original H ID → DOT q ID
        h_to_q_mapping[h_id] = q_id
        
        # Also store just the ID portion for pattern matching
        h_suffix = h_id.split(".")[-1]
        q_suffix = q_id.split(".")[-1]
        h_to_q_mapping[h_suffix] = q_suffix
    
    # Step 2: Replace all H IDs with their q equivalents in all edge definitions
    modified_content = content
    
    # Process each H→q mapping
    for h_id, q_id in h_to_q_mapping.items():
        if "." in h_id:  # Full ID with prefix (e.g., katsaros_liritzis_laskaris_2010.H131225)
            # Find edges that reference this full H ID
            edge_pattern = re.compile(r'-> *"(' + re.escape(h_id) + r')"')
            modified_content = edge_pattern.sub(r'-> "' + q_id + r'"', modified_content)
            
            # Also handle if the H ID is at the start of an edge
            start_pattern = re.compile(r'(^|\n)"(' + re.escape(h_id) + r')" *->')
            modified_content = start_pattern.sub(r'\1"' + q_id + r'" ->', modified_content)
        else:  # Just the ID suffix (e.g., H131225)
            # This handles cases where the prefix might be different
            # Find edges that end with this H ID suffix
            edge_suffix_pattern = re.compile(r'-> *"([^"]+\.)(' + re.escape(h_id) + r')"')
            modified_content = edge_suffix_pattern.sub(r'-> "\1' + q_id + r'"', modified_content)
            
            # Also handle if the H ID is at the start of an edge
            start_suffix_pattern = re.compile(r'(^|\n)"([^"]+\.)(' + re.escape(h_id) + r')" *->')
            modified_content = start_suffix_pattern.sub(r'\1"\2' + q_id + r'" ->', modified_content)
    
    # Step 3: Only now, after all edges have been fixed, remove the original_xml_id attributes
    attr_pattern = re.compile(r', original_xml_id="[^"]+"')
    modified_content = attr_pattern.sub('', modified_content)
    
    # Also handle different spacing
    attr_pattern2 = re.compile(r',original_xml_id="[^"]+"')
    modified_content = attr_pattern2.sub('', modified_content)
    
    # Clean up any potential double commas or trailing commas that might result
    modified_content = re.sub(r',\s*,', ',', modified_content)
    modified_content = re.sub(r',\s*\]', ']', modified_content)
    
    # Step 4: Fix any remaining malformed edges (ones with label content instead of target ID)
    bad_edge_pattern = re.compile(r'-> *" *\[label=<')
    
    # Get all lines of the modified content
    lines = modified_content.split('\n')
    
    # Process each line individually to handle malformed edges
    for i, line in enumerate(lines):
        match = bad_edge_pattern.search(line)
        if match:
            # Extract the source node ID
            source_match = re.match(r'"([^"]+)"', line)
            if source_match and source_match.group(1).endswith('_func'):
                source_id = source_match.group(1)
                support_id = source_id.split('_func')[0]
                
                # Extract the base prefix (e.g., katsaros_liritzis_laskaris_2010)
                prefix = support_id.split('.')[0]
                
                # Find a matching q ID for this source prefix
                for h_id, q_id in h_to_q_mapping.items():
                    if "." in h_id and h_id.startswith(prefix):
                        # Extract style attributes from the malformed edge
                        style_match = re.search(r'\[([^\]]+)\];?$', line)
                        style_str = ''
                        if style_match:
                            style_str = style_match.group(1)
                            # Clean up any label content
                            style_str = re.sub(r'label=<[^>]*>,?\s*', '', style_str).strip()
                            style_str = re.sub(r'gephi_label="[^"]*",?\s*', '', style_str).strip()
                            
                            # Make sure we have something
                            if not style_str:
                                style_str = 'color="#000000", style="solid"'
                        else:
                            style_str = 'color="#000000", style="solid"'
                        
                        # Create a fixed edge
                        fixed_line = f'"{source_id}" -> "{q_id}" [{style_str}];'
                        lines[i] = fixed_line
                        break
    
    # Recombine the lines
    modified_content = '\n'.join(lines)
    
    # Write the modified content back to the file
    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.write(modified_content)
