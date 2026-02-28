"""
File I/O functions for Gephi DOT files.
"""
def write_gephi_dot_file(gephi_dot_filename, processed_lines, direct_edges):
    """
    Write the final Gephi DOT file with all modifications.
    Ensures all new edges are inserted at the end of the graph before the final closing brace.
    Normalizes line breaks for consistent formatting.
    """
    # Add the direct replacement edges for pseudo-nodes
    unique_direct_edges = list(set(direct_edges))
    
    # Find the LAST closing brace in the file by searching in reverse
    closing_brace_index = -1
    for i in range(len(processed_lines) - 1, -1, -1):
        if processed_lines[i].strip() == '}':
            closing_brace_index = i
            break
    
    if closing_brace_index == -1:
        # If no closing brace is found, append at the end
        closing_brace_index = len(processed_lines)
        processed_lines.append('}')
    
    # Add a blank line before the new edges if not already there
    if closing_brace_index > 0 and processed_lines[closing_brace_index-1].strip() != '':
        processed_lines.insert(closing_brace_index, '')
        closing_brace_index += 1  # Adjust index after insertion
    
    if unique_direct_edges:
        # Insert direct edges before the final closing brace
        processed_lines = (processed_lines[:closing_brace_index] + 
                          unique_direct_edges + 
                          processed_lines[closing_brace_index:])
    
    # Normalize line breaks
    normalized_lines = normalize_line_breaks(processed_lines)
    
    # Write the modified content to the Gephi DOT file
    with open(gephi_dot_filename, 'w', encoding='utf-8') as gephi_file:
        for line in normalized_lines:
            gephi_file.write(line + '\n')


def normalize_line_breaks(lines):
    """
    Normalize line breaks in the DOT file:
    - Ensure exactly one empty line between non-empty lines
    - No empty lines after the final closing brace
    """
    # Remove trailing whitespace from all lines
    lines = [line.rstrip() for line in lines]
    
    # Find the last closing brace
    closing_brace_index = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            closing_brace_index = i
            break
    
    if closing_brace_index == -1:
        closing_brace_index = len(lines)
    
    # Process lines up to the closing brace
    normalized = []
    i = 0
    while i < closing_brace_index:
        current_line = lines[i]
        normalized.append(current_line)
        
        # If this is a non-empty line, ensure exactly one empty line follows
        if current_line.strip():
            # Add exactly one empty line (unless we're just before the closing brace)
            if i + 1 < closing_brace_index:
                normalized.append('')
                
                # Skip any existing empty lines
                i += 1
                while i < closing_brace_index and not lines[i].strip():
                    i += 1
                continue
        
        i += 1
    
    # Add the closing brace (if it exists)
    if closing_brace_index < len(lines):
        normalized.append(lines[closing_brace_index])
    
    return normalized


