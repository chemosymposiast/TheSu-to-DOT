"""
Normalization functions for DOT files.

This module handles normalization of line breaks and formatting in DOT files.
"""


def normalize_dot_file_line_breaks(dot_filename):
    """
    Normalize line breaks in the DOT file with specific rules:
    - Keep subgraph cluster declarations, label, and style declarations together
    - Ensure an empty line before each subgraph cluster declaration
    - Keep the initial digraph declaration and its parameters together
    - Ensure proper spacing between node and edge definitions
    """
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into lines and remove trailing whitespace
    lines = [line.rstrip() for line in content.split('\n')]
    
    # Process the lines
    normalized = []
    i = 0
    in_header = True
    in_subgraph = False
    subgraph_declaration_group = []
    
    while i < len(lines):
        current_line = lines[i]
        stripped_line = current_line.strip()
        
        # Handle the header section (digraph, compound, etc.)
        if in_header:
            if stripped_line.startswith('digraph') or stripped_line in ('compound=true;', 'newrank=true;', 'rankdir=', 'splines='):
                normalized.append(current_line)
                i += 1
                continue
            else:
                # End of header
                in_header = False
                if normalized and not normalized[-1] == '':
                    normalized.append('')  # Add a blank line after header
        
        # Handle subgraph declarations
        if stripped_line.startswith('subgraph cluster_'):
            in_subgraph = True
            
            # Ensure there's an empty line before the subgraph
            if normalized and normalized[-1] != '':
                normalized.append('')
            
            subgraph_declaration_group = [current_line]
            i += 1
            # Collect all lines belonging to the subgraph declaration (label, peripheries, etc.)
            while i < len(lines) and not lines[i].strip().startswith('"') and not lines[i].strip() == '}':
                subgraph_declaration_group.append(lines[i].rstrip())
                i += 1
            
            # Add all subgraph declaration lines with no empty lines between them
            normalized.extend(subgraph_declaration_group)
            continue
        
        # Handle closing subgraph
        if in_subgraph and stripped_line == '}':
            normalized.append(current_line)
            in_subgraph = False
            i += 1
            if i < len(lines) and lines[i].strip():  # If next line is not empty
                normalized.append('')  # Add a single blank line after subgraph
            continue
        
        # Handle node and edge definitions
        if stripped_line.startswith('"') and (' -> ' in stripped_line or '[' in stripped_line):
            if normalized and normalized[-1].strip() and not normalized[-1].strip().startswith('subgraph') and not normalized[-1].strip() == '{':
                normalized.append('')  # Add a blank line before node/edge if previous line wasn't a subgraph start
            
            normalized.append(current_line)
            
            # Skip any existing empty lines
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        
        # Default case: add the line
        normalized.append(current_line)
        i += 1
    
    # Collapse runs of more than 1 consecutive blank line
    collapsed = []
    blank_count = 0
    for line in normalized:
        if line == '':
            blank_count += 1
            if blank_count <= 1:
                collapsed.append(line)
        else:
            blank_count = 0
            collapsed.append(line)

    # Write the normalized content back to the file
    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(collapsed))


def collapse_excess_blank_lines(dot_filename, max_consecutive=1):
    """Reduce any run of more than *max_consecutive* blank lines to exactly
    *max_consecutive* blank lines throughout the file."""
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    # \n repeated (max_consecutive+2) or more times → (max_consecutive+1) newlines
    pattern = r'\n{' + str(max_consecutive + 2) + r',}'
    replacement = '\n' * (max_consecutive + 1)
    collapsed = re.sub(pattern, replacement, content)

    if collapsed != content:
        with open(dot_filename, 'w', encoding='utf-8') as f:
            f.write(collapsed)
