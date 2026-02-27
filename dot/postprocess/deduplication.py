"""
Deduplication functions for DOT files.

This module handles removal of duplicate definitions in DOT files.
"""


def remove_duplicate_definitions(dot_filename):
    """
    Post-processes the DOT file to remove duplicate node/edge definitions.
    Only keeps the first occurrence of any line starting with a double quote (").
    """
    with open(dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track unique lines that start with a double quote
    seen_definitions = set()
    processed_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if this line starts with a double quote
        if line_stripped.startswith('"'):
            # If we've seen this definition before, skip it
            if line_stripped in seen_definitions:
                continue
            
            # Otherwise, add it to our set of seen definitions
            seen_definitions.add(line_stripped)
        
        # Keep this line
        processed_lines.append(line)
    
    # Write the processed content back to the file
    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
