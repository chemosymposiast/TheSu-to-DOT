"""
DOT content processing for Gephi transformation.
"""
import re
from .colors import hex_to_closest_color

def process_gephi_dot_content(dot_content, 
                             matching_nodes, employed_nodes, function_nodes, 
                             entailment_nodes, analogy_nodes, reference_nodes, etiology_nodes):
    """
    Process the DOT content line by line, skipping pseudo-nodes.
    Phase nodes and edges are expected to be already processed.
    
    Returns:
        tuple: (processed_lines, empty_list)
    """
    processed_lines = []

    for line in dot_content.split('\n'):
        skip_line = False
        
        # Skip lines related to matching proposition pseudo-nodes
        for pseudo_id in matching_nodes:
            if f'"{pseudo_id}"' in line or f'-> "{pseudo_id}"' in line or f'"{pseudo_id}" ->' in line:
                skip_line = True
                break
                
        # Skip lines related to employed pseudo-nodes
        for employed_id in employed_nodes:
            if f'"{employed_id}"' in line or f'-> "{employed_id}"' in line or f'"{employed_id}" ->' in line:
                skip_line = True
                break
                
        # Skip lines related to function pseudo-nodes
        for func_id in function_nodes:
            if f'"{func_id}"' in line or f'-> "{func_id}"' in line or f'"{func_id}" ->' in line:
                skip_line = True
                break
                
        # Skip lines related to entailment pseudo-nodes
        for entailment_id in entailment_nodes:
            if f'"{entailment_id}"' in line or f'-> "{entailment_id}"' in line or f'"{entailment_id}" ->' in line:
                skip_line = True
                break
                
        # Skip lines related to analogy pseudo-nodes
        for analogy_id in analogy_nodes:
            if f'"{analogy_id}"' in line or f'-> "{analogy_id}"' in line or f'"{analogy_id}" ->' in line:
                skip_line = True
                break

        # Skip lines related to reference pseudo-nodes
        for reference_id in reference_nodes:
            if f'"{reference_id}"' in line or f'-> "{reference_id}"' in line or f'"{reference_id}" ->' in line:
                skip_line = True
                break
                
        # Skip lines related to etiology pseudo-nodes
        for etiology_id in etiology_nodes:
            if f'"{etiology_id}"' in line or f'-> "{etiology_id}"' in line or f'"{etiology_id}" ->' in line:
                skip_line = True
                break
        
        if skip_line:
            continue
                
        # Process proposition nodes to extract paraphrasis before replacing the label
        if 'gephi_label="PROP"' in line and 'label=<' in line:
            # Extract paraphrasis from HTML label
            label_match = re.search(r'label=<.*?<i>(.*?)</i>.*?>', line)
            if label_match:
                paraphrasis_text = label_match.group(1)
                # Clean HTML from paraphrasis
                paraphrasis_text = re.sub(r'<br/>', ' ', paraphrasis_text)
                paraphrasis_text = re.sub(r'<[^>]+>', '', paraphrasis_text)
                # Escape quotes
                paraphrasis_text = paraphrasis_text.replace('"', '\\"')
                # Add paraphrasis attribute if not already present
                if 'paraphrasis=' not in line:
                    line = line.replace(']', f', paraphrasis="{paraphrasis_text}"]')
        
        # Process remaining lines as before
        if re.search(r'\blabel=.*,', line) and re.search(r'\bgephi_label=.*,', line):
            line = re.sub(r'\blabel=.*?(?:,\s*)?(?=\bgephi_label)', '', line)
            line = re.sub(r'\bgephi_label=', 'label=', line)
        
        # Handle xlabel attributes with HTML content
        if 'xlabel=<' in line:
            # Find the start of the HTML content
            xlabel_pos = line.find('xlabel=<')
            if xlabel_pos != -1:
                content_start = xlabel_pos + 8  # Skip "xlabel=<"
                
                # Find the matching closing bracket with proper nesting
                content_end = -1
                bracket_level = 1
                
                for i in range(content_start, len(line)):
                    if line[i] == '<':
                        bracket_level += 1
                    elif line[i] == '>':
                        bracket_level -= 1
                        
                    if bracket_level == 0:
                        content_end = i
                        break
                
                if content_end > content_start:
                    # Extract the full HTML content
                    html_content = line[content_start:content_end]
                    
                    # Create plain text by removing HTML tags
                    plain_text = html_content
                    plain_text = re.sub(r'<br/>', ', ', plain_text)  # Replace <br/> with comma+space
                    plain_text = re.sub(r'<[^>]+>', '', plain_text)  # Remove other HTML tags
                    plain_text = plain_text.strip()
                    
                    # Replace the entire xlabel attribute
                    orig_attr = f'xlabel=<{html_content}>'
                    new_attrs = f'label="{plain_text}", original_html="{html_content}"'
                    
                    # Find where to insert in the attributes
                    attr_start = line.rfind('[', 0, xlabel_pos)
                    if attr_start != -1:
                        # Replace the xlabel attribute while keeping other attributes
                        attr_str = line[attr_start:].replace(orig_attr, new_attrs)
                        line = line[:attr_start] + attr_str
        
        # Handle plain text xlabel attributes
        elif 'xlabel="' in line:
            xlabel_match = re.search(r'xlabel="([^"]+)"', line)
            if xlabel_match:
                label_text = xlabel_match.group(1)
                # Replace the entire xlabel attribute
                line = line.replace(xlabel_match.group(0), f'label="{label_text}"')
        
        # Handle gephi_label if present
        if 'gephi_label=' in line and 'label=' not in line:
            line = re.sub(r'gephi_label=', 'label=', line)
        elif 'gephi_label=' in line and 'label=' in line:
            line = re.sub(r',\s*gephi_label=[^,\]]+', '', line)

        # Stage 3: Add "label="_" before "gephi_invis="true" 
        if re.search(r'gephi_invis="true"', line):
            line = re.sub(r'gephi_invis="true"', 'label="_", gephi_invis="true"', line)

        # Stage 4: Color attributes Gephi adaptation 
        if re.search(r'\bfillcolor="(#[0-9a-fA-F]{6})"', line):
            line = re.sub(r'\bcolor="(#[0-9a-fA-F]{6})"', r'label_color="\1"', line)
            line = re.sub(r'\bfillcolor="(#[0-9a-fA-F]{6})"', r'color="\1"', line)

        # Stage 5: Convert remaining HEX codes to HTML color names
        line = re.sub(r'(#[0-9a-fA-F]{6})', hex_to_closest_color, line)
        
        # Clean up any syntax issues
        line = line.replace('[ ', '[').replace(' ]', ']')
        line = line.replace(',,', ',').replace(', ,', ',')
        line = line.replace(', ]', ']')
        
        processed_lines.append(line)
        
    return processed_lines, []


