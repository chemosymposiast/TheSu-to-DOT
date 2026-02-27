"""Proposition-related DOT building functions.

Key functions: process_referenced_propositions, get_proposition_sequences,
parse_phases_ref, process_proposition_sequences
"""
from bootstrap.primary_imports import re, random
from xml_processing.extractors import extract_paraphrasis_text
from xml_processing.selectors import get_all_proposition_ids

def process_referenced_propositions(filtered_elements, namespaces, all_propositions, dot_file, written_lines, written_prop_phases, processed_propositions):
    """Process all propositions referenced in filtered elements, writing DOT nodes and sequences."""
    all_proposition_ids = get_all_proposition_ids(filtered_elements, namespaces)
    for prop_id in all_proposition_ids:
        # Skip if this proposition has already been processed
        if prop_id in processed_propositions:
            continue
            
        proposition_element = all_propositions.get(prop_id)
        if proposition_element is not None:
            # Mark as processed
            processed_propositions.add(prop_id)
            
            paraphrasis_elem = proposition_element.find("./thesu:paraphrasis", namespaces=namespaces)
            paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
            paraphrasis = re.sub(r'\s+', ' ', paraphrasis)
            paraphrasis = re.sub(r'(.{1,50})(?:\s|$)', r'\1<br/>', paraphrasis)
            node_line = f'"{prop_id}" [label=<<b>PROPOSITION</b><br/><i>{paraphrasis}</i>>, gephi_label="PROP", shape="doubleoctagon", style="rounded,filled", fillcolor="#f9edff", color="#9673a6"];\n\n'
            dot_file.write(node_line)
            written_lines.append(node_line)
            
            # Process the sequences of the proposition
            sequences_dict = get_proposition_sequences(proposition_element, namespaces, prop_id, written_prop_phases)
            if sequences_dict:
                written_lines = process_proposition_sequences(sequences_dict, prop_id, dot_file, written_lines, written_prop_phases)
    
    return written_lines, written_prop_phases, processed_propositions

def get_proposition_sequences(element, namespaces, element_id, written_prop_phases):
    """Extract proposition sequences and phases from an element into a structured dict."""
    sequences_dict = {}
    sequences_group = element.find('.//thesu:propositionType/thesu:sequencesGroup', namespaces=namespaces)
    
    if sequences_group is not None:
        sequences = sequences_group.findall('.//thesu:sequence', namespaces=namespaces)
        for sequence in sequences:
            sequence_number = 0
            
            sequence_id = sequence.get('{http://alchemeast.eu/thesu/ns/1.0}id')
            if sequence_id is None:
                xml_id = sequence.get('{http://www.w3.org/XML/1998/namespace}id')
                if xml_id is not None:
                    sequence_id = xml_id
                else:
                    sequence_id = f"{element_id}_Q{random.randrange(100000)}"
            
            phasesGroups = sequence.findall('.//thesu:phasesGroup', namespaces=namespaces)
            
            # Process each phase group sequentially
            for phase_group_number, phasesGroup in enumerate(phasesGroups, 1):
                phase_relative_to_group_number = 0
                newPhases = phasesGroup.find('.//thesu:newPhases', namespaces=namespaces)
                phases = []
                
                if newPhases is not None:
                    phases = newPhases.findall('.//thesu:phase', namespaces=namespaces)
                
                for phase in phases:
                    sequence_number += 1
                    phase_relative_to_group_number += 1

                    # Replace Q with q in the ID and add 3 more digits for sequence number
                    phase_id = sequence_id.replace("Q", "q") + f"{sequence_number:03d}"

                    # Look for direct paraphrasis child (not descendant)
                    paraphrasis_elem = phase.find('./thesu:paraphrasis', namespaces=namespaces)
                    
                    if paraphrasis_elem is not None:
                        # Extract the text, including any tail text
                        phase_paraphrasis = paraphrasis_elem.text or ""
                        
                        # Get text from all children and any tail text
                        for child in paraphrasis_elem:
                            if child.tail:
                                phase_paraphrasis += child.tail
                                
                        phase_paraphrasis = re.sub(r'\s+', ' ', phase_paraphrasis).strip()
                    else:
                        # Try to find microThemedFreeText and then freeText
                        micro_themed = phase.find('./thesu:microThemedFreeText', namespaces=namespaces)
                        if micro_themed is not None:
                            free_text_elem = micro_themed.find('./thesu:freeText', namespaces=namespaces)
                            if free_text_elem is not None:
                                # Extract the text, including any tail text
                                phase_paraphrasis = free_text_elem.text or ""
                                
                                # Get any tail text from children
                                for child in free_text_elem:
                                    if child.tail:
                                        phase_paraphrasis += child.tail
                                        
                                phase_paraphrasis = re.sub(r'\s+', ' ', phase_paraphrasis).strip()
                            else:
                                phase_paraphrasis = "/"  # No freeText element found
                        else:
                            phase_paraphrasis = "/"  # No microThemedFreeText element found
                    
                    phase_paraphrasis = re.sub(r'(.{1,30})(?:\s|$)', r'\1<br/>', phase_paraphrasis)

                    sequences_dict[sequence_number] = {
                        'phase_id': phase_id,
                        'sequence_id': sequence_id,
                        'phase_number': sequence_number,
                        'phase_group_number': phase_group_number,  # The group number (1-based)
                        'phase_number_in_group': phase_relative_to_group_number,  # Position within group (1-based)
                        'phase_paraphrasis': phase_paraphrasis
                    }
    
    return sequences_dict

def parse_phases_ref(phases_ref):
    """
    Parse a phasesRef string like "1.1,1.4-5,2.1" into structured data.
    Returns a dictionary where:
    - keys are phase group numbers
    - values are lists of specific phase numbers within that group
    
    For example, "1.1,1.4-5,2.1" would return:
    {
        1: [1, 4, 5],
        2: [1]
    }
    """
    if not phases_ref or phases_ref == "/":
        return {}
    
    result = {}
    # Split by commas to get individual references
    for ref_part in phases_ref.split(','):
        try:
            if '-' in ref_part:
                # Handle range notation (e.g., "1.4-5")
                range_parts = ref_part.split('-')
                if '.' in range_parts[0]:
                    # Extract group number and start phase
                    group_num, start_phase = map(int, range_parts[0].split('.'))
                    # For the end, either use the full value or just the phase number
                    if '.' in range_parts[1]:
                        _, end_phase = map(int, range_parts[1].split('.'))
                    else:
                        end_phase = int(range_parts[1])
                    
                    # Initialize the group if not already there
                    if group_num not in result:
                        result[group_num] = []
                    
                    # Add all phases in the range
                    result[group_num].extend(list(range(start_phase, end_phase + 1)))
                else:
                    # This is a range of group numbers without specific phases
                    start_group, end_group = map(int, range_parts)
                    for group_num in range(start_group, end_group + 1):
                        # Add an empty list for each group
                        if group_num not in result:
                            result[group_num] = []
            elif '.' in ref_part:
                # Handle specific phase notation (e.g., "1.1")
                group_num, phase_num = map(int, ref_part.split('.'))
                if group_num not in result:
                    result[group_num] = []
                result[group_num].append(phase_num)
            else:
                # Just a group number without specific phases
                group_num = int(ref_part)
                if group_num not in result:
                    result[group_num] = []
        except (ValueError, TypeError):
            # Skip any invalid reference parts
            continue
    
    return result

def process_proposition_sequences(sequences_dict, element_id, dot_file, written_lines, written_prop_phases):
    """Write DOT nodes and edges for proposition sequences to the dot file."""
    if sequences_dict:
        # Get unique sequence IDs
        unique_sequence_ids = set([value['sequence_id'] for value in sequences_dict.values()])
        
        for sequence_id in unique_sequence_ids:
            # Filter the phases belonging to the same sequence_id
            sequence_dict_filtered = {k: v for k, v in sequences_dict.items() if v['sequence_id'] == sequence_id}
            
            # Create cluster ID for this sequence
            cluster_id = f"{element_id}_{sequence_id}".replace('.', '_')
            
            # Add the cluster_id to all phases in this sequence (both in sequence_dict_filtered and sequences_dict)
            for sequence_number, seq_dict in sequence_dict_filtered.items():
                seq_dict['cluster_id'] = cluster_id
                # Also update the original dictionary
                sequences_dict[sequence_number]['cluster_id'] = cluster_id
            
            # Generate the cluster for this sequence
            cluster_lines = []
            
            # Add a subgraph for the current sequence
            dot_file.write(f'\nsubgraph cluster_{cluster_id} {{\n')
            dot_file.write(f'label=<<font color=\'#9673a6\'>Sequence</font>>;\n')
            dot_file.write('peripheries=1;\n\n')
            
            # Add nodes for each phase in the sequence
            for phase_number, phase_data in sorted(sequence_dict_filtered.items()):
                phase_id = phase_data['phase_id']
                phase_paraphrasis = phase_data['phase_paraphrasis']
                label = f"{phase_data['phase_number']}"
                
                # Store the phase data for later reference in matching processes
                written_prop_phases[phase_id] = phase_data
                
                # Create the node - Add paraphrasis as a separate attribute
                node_line = f'"{phase_id}" [label=<<b>{label}</b><br/><i>{phase_paraphrasis}</i>>, gephi_label="ph.", phase_number="{label}", paraphrasis="{phase_paraphrasis.replace("<br/>", " ")}", shape="box", style="rounded,filled", color="#9673a6", fillcolor="#f9edff"];\n\n'
                dot_file.write(node_line)
                cluster_lines.append(node_line)
            
            # Add edges between phases
            sorted_phase_numbers = sorted(sequence_dict_filtered.keys())
            for i in range(len(sorted_phase_numbers) - 1):
                source_phase_id = sequence_dict_filtered[sorted_phase_numbers[i]]['phase_id']
                target_phase_id = sequence_dict_filtered[sorted_phase_numbers[i + 1]]['phase_id']
                edge_line = f'"{source_phase_id}" -> "{target_phase_id}" [dir=none, color="#9673a6"];\n\n'
                dot_file.write(edge_line)
                cluster_lines.append(edge_line)
            
            # Close the subgraph
            dot_file.write('}\n\n')
            written_lines.extend(cluster_lines)
            
            # Create edge from the PROPOSITION node to the first phase of this sequence
            first_phase_id = sequence_dict_filtered[min(sequence_dict_filtered.keys())]['phase_id']
            line_to_write = f'"{element_id}" -> "{first_phase_id}" [dir=none, lhead="cluster_{cluster_id}", color="#9673a6"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
    
    return written_lines
