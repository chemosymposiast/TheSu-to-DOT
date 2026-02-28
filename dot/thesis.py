"""Thesis-related DOT building functions.

Key functions: process_thesis_element, write_thesis_and_process_included_elements,
get_thesis_entailments, get_thesis_etiologies, get_thesis_analogies, get_thesis_references,
get_thesis_matching_propositions, process_matching_propositions, get_thesis_sequences,
process_thesis_sequences, process_matching_prop_sequences, draw_edges_with_prop_sequences
"""
from bootstrap.primary_imports import re
from xml_processing.extractors import extract_paraphrasis_text
from utils.text import pad_short_string
from dot.pseudo_nodes import (
    generate_unique_pseudo_node_id_entailments,
    generate_unique_pseudo_node_id_etiologies,
    generate_unique_pseudo_node_id_analogies,
    generate_unique_pseudo_node_id_references,
    generate_unique_pseudo_node_id_matching_propositions,
    generate_unique_pseudo_node_id_matching_sequences,
)
from dot.propositions import get_proposition_sequences, process_proposition_sequences, parse_phases_ref

def get_thesis_entailments(element, namespaces):
    """Extract entailment references from a THESIS element. Returns {entailed_by_ref: entailed_as}."""
    entailments_dict = {}
    entailments_group = element.find('./thesu:entailment', namespaces=namespaces)
    if entailments_group is not None:
        entailments = entailments_group.findall('.//thesu:entailedBy', namespaces=namespaces)
        for entailment in entailments:
            entailed_by_ref = entailment.get('{http://alchemeast.eu/thesu/ns/1.0}ref').split('#')[-1]
            entailed_as = entailment.get('{http://alchemeast.eu/thesu/ns/1.0}entailedAs')
            entailments_dict[entailed_by_ref] = entailed_as
    return entailments_dict

def get_thesis_etiologies(element, namespaces, element_id):
    """
    Extract etiology members from a THESIS element.
    Only includes references to external THESIS elements (not descendants of the current THESIS).
    
    Returns:
        dict: {referenced_element_id: {"is_cause": True/False, "is_end": True/False, "has_cause_siblings": True/False, "has_end_siblings": True/False}}
    """
    etiologies_dict = {}
    
    # Find etiologiesGroup in thesisType
    etiologies_group = element.find('./thesu:thesisType/thesu:etiologiesGroup', namespaces=namespaces)
    
    if etiologies_group is not None:
        etiologies = etiologies_group.findall('./thesu:etiology', namespaces=namespaces)
        
        for etiology in etiologies:
            # Process each etiology member
            etiology_members = etiology.findall('./thesu:etiologyMember', namespaces=namespaces)
            
            # Analyze siblings to determine relationship context
            has_cause_siblings = any(member.get('{http://alchemeast.eu/thesu/ns/1.0}cause') == "true" 
                                   for member in etiology_members)
            has_end_siblings = any(member.get('{http://alchemeast.eu/thesu/ns/1.0}end') == "true" 
                                  for member in etiology_members)
            
            for member in etiology_members:
                # Get the cause and end attributes
                is_cause = member.get('{http://alchemeast.eu/thesu/ns/1.0}cause') == "true"
                is_end = member.get('{http://alchemeast.eu/thesu/ns/1.0}end') == "true"
                
                # Find element references
                element_ref = member.find('./thesu:elementRef', namespaces=namespaces)
                if element_ref is not None:
                    # Get the complete reference
                    full_ref = element_ref.get('{http://alchemeast.eu/thesu/ns/1.0}ref')
                    referenced_id = full_ref.split('#')[-1]
                    
                    # Skip self-references
                    if referenced_id == element_id:
                        continue
                    
                    # Find the referenced element in the XML tree
                    # First get the root of the document
                    root = element.getroottree().getroot()
                    
                    # Find the referenced element by its ID
                    xpath_query = f".//*[@xml:id='{referenced_id}']"
                    referenced_elements = root.xpath(xpath_query, namespaces={'xml': 'http://www.w3.org/XML/1998/namespace'})
                    
                    # If the referenced element exists and is not a descendant of the current element
                    if referenced_elements:
                        referenced_element = referenced_elements[0]
                        
                        # Check if current element is an ancestor of the referenced element
                        # If it is, skip this reference as it's internal
                        is_ancestor = False
                        parent = referenced_element.getparent()
                        while parent is not None:
                            if parent == element:
                                is_ancestor = True
                                break
                            parent = parent.getparent()
                        
                        # Only add external references (not descendants)
                        if not is_ancestor:
                            etiologies_dict[referenced_id] = {
                                "is_cause": is_cause, 
                                "is_end": is_end,
                                "has_cause_siblings": has_cause_siblings,
                                "has_end_siblings": has_end_siblings
                            }
                
    return etiologies_dict

def get_thesis_analogies(element, namespaces):
    """
    Extract analogy members from a THESIS element.
    
    Returns:
        dict: {referenced_element_id: {"is_comparans": True/False}}
    """
    analogies_dict = {}
    
    # Use thesu: namespace prefix consistently
    analogies_group = element.find('./thesu:thesisType/thesu:analogiesGroup', namespaces=namespaces)
    
    if analogies_group is not None:
        analogies = analogies_group.findall('./thesu:analogy', namespaces=namespaces)
        
        for analogy in analogies:
            # Process each analogy member
            analogy_members = analogy.findall('./thesu:analogyMember', namespaces=namespaces)
            
            for member in analogy_members:
                # Get the comparans attribute
                is_comparans = member.get('{http://alchemeast.eu/thesu/ns/1.0}comparans') == "true"
                
                # Find element references
                element_ref = member.find('./thesu:elementRef', namespaces=namespaces)
                if element_ref is not None:
                    referenced_id = element_ref.get('{http://alchemeast.eu/thesu/ns/1.0}ref').split('#')[-1]
                    analogies_dict[referenced_id] = {"is_comparans": is_comparans}
                
    return analogies_dict

def get_thesis_references(element, namespaces):
    """
    Extract references from THESIS elements that are:
    1. Children of an 'includedRef' element (descendant of THESIS)
    2. Descendants of 'macroThemesGroup' (child of 'thesisType')
    
    Returns:
        dict: {referenced_element_id: source_location}
        where source_location is either "includedRef" or "macroThemes"
    """
    references_dict = {}
    
    # Case 1: Find elementRef within includedRef elements
    included_refs = element.findall('.//thesu:includedRef', namespaces=namespaces)
    for included_ref in included_refs:
        element_refs = included_ref.findall('.//thesu:elementRef', namespaces=namespaces)
        for elem_ref in element_refs:
            ref_id = elem_ref.get('{http://alchemeast.eu/thesu/ns/1.0}ref')
            if ref_id:
                # Extract the ID portion after the # symbol
                referenced_id = ref_id.split('#')[-1]
                references_dict[referenced_id] = "includedRef"
    
    # Case 2: Find elementRef within macroThemesGroup
    macro_themes_group = element.find('./thesu:thesisType/thesu:macroThemesGroup', namespaces=namespaces)
    if macro_themes_group is not None:
        element_refs = macro_themes_group.findall('.//thesu:elementRef', namespaces=namespaces)
        for elem_ref in element_refs:
            ref_id = elem_ref.get('{http://alchemeast.eu/thesu/ns/1.0}ref')
            if ref_id:
                # Extract the ID portion after the # symbol
                referenced_id = ref_id.split('#')[-1]
                references_dict[referenced_id] = "macroThemes"
    
    return references_dict

def get_thesis_matching_propositions(element, namespaces):
    """Extract matching proposition references and their types from a THESIS element."""
    matching_propositions_dict = {}
    matching_propositions_group = element.find('./thesu:matchingPropositionsGroup', namespaces=namespaces)
    if matching_propositions_group is not None:
        matching_propositions = matching_propositions_group.findall('.//thesu:matchingProposition', namespaces=namespaces)
        for matching_proposition in matching_propositions:
            prop_ref = matching_proposition.get('{http://alchemeast.eu/thesu/ns/1.0}propRef').split('#')[-1]
            matching_type = []

            attributes = ['extended', 'partial', 'generalized', 'specified', 'quoted', 'altered']
            for attr in attributes:
                attr_value = matching_proposition.get(f'{{http://alchemeast.eu/thesu/ns/1.0}}{attr}')
                if attr_value == 'true':
                    if attr == 'extended':
                        matching_type.append('extending')
                    elif attr == 'partial':
                        matching_type.append('being part of')
                    elif attr == 'generalized':
                        matching_type.append('generalizing')
                    elif attr == 'specified':
                        matching_type.append('specifying')
                    elif attr == 'quoted':
                        matching_type.append('being quoted')
                    elif attr == 'altered':
                        matching_type.append('altering')

            matching_type_str = ',<br/>'.join(matching_type) if matching_type else None
            matching_propositions_dict[prop_ref] = matching_type_str

    return matching_propositions_dict

def process_matching_propositions(element, element_id, namespaces, all_propositions, dot_file, written_lines, stored_edges, written_prop_phases, processed_propositions):
    """Process matching propositions: create nodes, pseudo-nodes, and store edges for later writing."""
    matching_propositions_dict = get_thesis_matching_propositions(element, namespaces)

    if matching_propositions_dict:
        for prop_ref in matching_propositions_dict:
            # Only process the proposition node if it hasn't been processed before
            if prop_ref not in processed_propositions:
                proposition_element = all_propositions.get(prop_ref)
                prop_id = prop_ref

                if proposition_element is not None:
                    # Mark as processed
                    processed_propositions.add(prop_ref)
                    
                    # Retrieve the paraphrasis of the PROPOSITION element
                    paraphrasis_elem = proposition_element.find("./thesu:paraphrasis", namespaces=namespaces)
                    paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
                    paraphrasis = re.sub(r'\s+', ' ', paraphrasis)
                    paraphrasis = re.sub(r'(.{1,50})(?:\s|$)', r'\1<br/>', paraphrasis)

                    # Create the node and write it to the dot file
                    node_line = f'"{prop_ref}" [label=<<b>PROPOSITION</b><br/><i>{paraphrasis}</i>>, gephi_label="PROP", shape="doubleoctagon", style="rounded,filled", fillcolor="#f9edff", color="#9673a6"];\n\n'
                    dot_file.write(node_line)

                    # Append the node line to written_lines
                    written_lines.append(node_line)  

                    # Iterate through the PROPOSITION's sequences
                    sequences_dict = get_proposition_sequences(proposition_element, namespaces, prop_id)
                    if sequences_dict:
                        written_lines = process_proposition_sequences(sequences_dict, prop_id, dot_file, written_lines, written_prop_phases)
                        
            # Create a pseudo-node with its own ID
            matching_type_str = matching_propositions_dict[prop_ref]
            pseudo_node_id = generate_unique_pseudo_node_id_matching_propositions(written_lines, prop_ref, element_id, 1)
            line_to_write = '"{}" [label=<{}>, gephi_label="matc", fontsize="11", shape="doubleoctagon", style="rounded,filled", fillcolor="#f9edff", color="#9673a6"];\n\n'.format(
                pseudo_node_id, 
                "MATCHES<br/><i>{}</i>".format(matching_type_str) if matching_type_str else "MATCHES"
            )
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            # Store the edges to write them later
            line_to_write = f'"{prop_ref}" -> "{pseudo_node_id}" [dir=none, color="#9673a6"];\n\n'
            stored_edges.append(line_to_write)

            line_to_write = f'"{pseudo_node_id}" -> "{element_id}" [color="#9673a6"];\n\n'
            stored_edges.append(line_to_write)

    return written_lines, processed_propositions

def get_thesis_sequences(element, namespaces, element_id):
    """Extract thesis sequences and phases from thesu:thesisType/thesu:sequencesGroup into a structured dict.

    Reads from the first thesu:sequence that does not contain thesu:maySubstitute.
    Each phase may include matchingPropositionPhases data (phasesRef, matching attributes) if present.
    """
    sequences_dict = {}
    sequences_group = element.find('.//thesu:thesisType/thesu:sequencesGroup', namespaces=namespaces)
    if sequences_group is not None:
        # Get all sequences
        all_sequences = sequences_group.findall('.//thesu:sequence', namespaces=namespaces)
        
        # Filter out sequences that contain 'maySubstitute' as child element
        filtered_sequences = []
        for seq in all_sequences:
            if seq.find('.//thesu:maySubstitute', namespaces=namespaces) is None:
                filtered_sequences.append(seq)
        
        # Only process the first filtered sequence (if any exist)
        if filtered_sequences:
            sequence = filtered_sequences[0]  # Only take the first one
            sequence_number = 50000
            sequence_number += 50000
            phase_absolute_number = sequence_number
            phase_relative_to_seq_number = 0
            sequence_id = sequence.get('{http://alchemeast.eu/thesu/ns/1.0}id')
            if sequence_id is None:
                xml_id = sequence.get('{http://www.w3.org/XML/1998/namespace}id')
                if xml_id is not None:
                    sequence_id = xml_id
                else:
                    sequence_id = f"{element_id}_Q{sequence_number}"
            else:
                sequence_id = f"{element_id}_{sequence_id}"
            phasesGroups = sequence.findall('.//thesu:phasesGroup', namespaces=namespaces)
            phase_relative_to_group_number = 0
            last_phase_group_number = None
            phases = sequence.findall('.//thesu:phase', namespaces=namespaces)
            
            for phase in phases:
                phase_absolute_number += 1
                phase_relative_to_seq_number += 1
                phase_group_number = None
                for i, phasesGroup in enumerate(phasesGroups):
                    if phase in phasesGroup.findall('.//thesu:phase', namespaces=namespaces):
                        phase_group_number = i + 1
                        break
                if last_phase_group_number == phase_group_number:
                    phase_relative_to_group_number += 1
                else:
                    phase_relative_to_group_number = 1
                last_phase_group_number = phase_group_number

                # Replace Q with q in the ID and add 3 more digits for phase number
                phase_id = sequence_id.replace("Q", "q") + f"{phase_relative_to_seq_number:03d}"

                original_xml_id = phase.get('{http://www.w3.org/XML/1998/namespace}id')
                
                # Look for direct paraphrasis child (not descendant)
                paraphrasis_elem = phase.find('./thesu:paraphrasis', namespaces=namespaces)
                if paraphrasis_elem is not None:
                    phase_paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
                    phase_paraphrasis = re.sub(r'\s+', ' ', phase_paraphrasis.strip())
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
                                    
                            phase_paraphrasis = re.sub(r'\s+', ' ', phase_paraphrasis.strip())
                        else:
                            phase_paraphrasis = "/"  # No freeText element found
                    else:
                        phase_paraphrasis = "/"  # No microThemedFreeText element found
                
                phase_paraphrasis = re.sub(r'(.{1,30})(?:\s|$)', r'\1<br/>', phase_paraphrasis)
                
                prop_phases_ref = phase.find('.//thesu:matchingPropositionPhases', namespaces=namespaces)
                attr_dict = {}
                parsed_phases_ref = None
                if prop_phases_ref is not None:
                    phases_ref = prop_phases_ref.get('{http://alchemeast.eu/thesu/ns/1.0}phasesRef')
                    parsed_phases_ref = parse_phases_ref(phases_ref)
                    
                    attributes = ['extended', 'partial', 'generalized', 'specified', 'quoted', 'altered']
                    for attr in attributes:
                        attr_value = prop_phases_ref.get(f'{{http://alchemeast.eu/thesu/ns/1.0}}{attr}')
                        if attr_value == 'true':
                            attr_dict[attr] = 'true'
                        else:
                            attr_dict[attr] = 'false'
                
                sequences_dict[phase_absolute_number] = {
                    'phase_id' : phase_id,
                    'sequence_id': sequence_id,
                    'phase_number': phase_relative_to_seq_number,
                    'phase_group_number': phase_group_number,
                    'phase_number_in_group': phase_relative_to_group_number,
                    'phase_paraphrasis': phase_paraphrasis,
                    'phase_absolute_number' : phase_absolute_number,
                    'parsed_phases_ref': parsed_phases_ref,
                    'matching_attributes': attr_dict,
                    'phase_element' : phase,
                    'sequence_element': sequence,
                    'original_xml_id': original_xml_id
                }
    return sequences_dict

def process_thesis_sequences(element, element_id, namespaces, dot_file, written_lines, all_propositions, written_prop_phases, implicit, color_fill, color_peripheries, style, filter_propositions, filter_matching_proposition_sequences):
    """Process thesis sequences: write phase nodes, clusters, and edges to the DOT file."""
    sequences_dict = get_thesis_sequences(element, namespaces, element_id)
    if sequences_dict:
        unique_sequence_ids = set([value['sequence_id'] for value in sequences_dict.values()])

        for sequence_id in unique_sequence_ids:
            # Filter the phases belonging to the same sequence_id
            sequence_dict_filtered = {k: v for k, v in sequences_dict.items() if v['sequence_id'] == sequence_id}
            
            cluster_id = f"{element_id}_{sequence_id}".replace('.', '_')
            cluster_label = f"<font color='{color_peripheries}'>Sequence</font>"
            cluster_lines = []
            
            # Add nodes for each phase in the sequence
            for phase_number, phase_data in sequence_dict_filtered.items():
                phase_id = phase_data['phase_id']
                phase_absolute_number = phase_data['phase_absolute_number']
                phase_paraphrasis = phase_data['phase_paraphrasis']
                label = f"{phase_data['phase_number']}"

                sequence_element = phase_data['sequence_element']
                phase_element = phase_data['phase_element']

                # Color calculation logic
                if filter_propositions or filter_matching_proposition_sequences:
                    fillcolor = color_fill
                    node_color = color_peripheries
                elif sequence_element.find('thesu:matchingPropositionSequence', namespaces) is not None:
                    # Get all matchingPropositionPhases elements for this phase
                    matching_prop_phases_elements = phase_element.findall('thesu:matchingPropositionPhases', namespaces=namespaces)
                    
                    # Get the matching proposition sequence elements that are direct children of the sequence
                    matching_prop_sequences = sequence_element.findall('./thesu:matchingPropositionSequence', namespaces=namespaces)
                    expected_matches = len(matching_prop_sequences)
                    
                    # Helper functions remain the same
                    def hex_to_rgb(hex_color):
                        hex_color = hex_color.lstrip('#')
                        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    
                    def rgb_to_hex(rgb):
                        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    
                    def interpolate_color(color1, color2, ratio):
                        biased_ratio = ratio ** 0.5
                        rgb1 = hex_to_rgb(color1)
                        rgb2 = hex_to_rgb(color2)
                        result = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * biased_ratio for i in range(3))
                        return rgb_to_hex(result)
                    
                    # Count valid matchingPropositionPhases, but only up to expected_matches
                    valid_matches = 0
                    
                    if expected_matches > 0:
                        # Check only up to expected_matches elements
                        for i, matching_prop_phases in enumerate(matching_prop_phases_elements):
                            if i >= expected_matches:
                                break
                                
                            phases_ref = matching_prop_phases.get('{http://alchemeast.eu/thesu/ns/1.0}phasesRef')
                            if phases_ref and phases_ref != "/" and phases_ref.strip():
                                # Try to parse it to validate
                                try:
                                    parsed_ref = parse_phases_ref(phases_ref)
                                    if parsed_ref:  # If we got a non-empty dictionary
                                        valid_matches += 1
                                except:
                                    # Parsing failed, don't increment valid_matches
                                    pass
                        
                        # Calculate the ratio of valid matches to expected matches
                        ratio = valid_matches / expected_matches
                        
                        # Base colors
                        dark_green_fill = "#c1d5c2"  # Dark green fill (no valid matches)
                        dark_green_border = "#a2b9a3"  # Dark green border (no valid matches)
                        light_green_fill = color_fill  # Light green fill (all valid matches)
                        light_green_border = color_peripheries  # Light green border (all valid matches)
                        
                        # Interpolate colors based on ratio
                        fillcolor = interpolate_color(dark_green_fill, light_green_fill, ratio)
                        node_color = interpolate_color(dark_green_border, light_green_border, ratio)
                    else:
                        # No matching sequences expected, use standard colors
                        fillcolor = color_fill
                        node_color = color_peripheries
                else:
                    fillcolor = color_fill
                    node_color = color_peripheries
                                                                                                        
                # Add paraphrasis as a separate attribute
                original_id_attr = f', original_xml_id="{phase_data["original_xml_id"]}"' if phase_data.get("original_xml_id") else ""
                node_line = f'"{phase_id}" [label=<<b>{label}</b><br/><i>{phase_paraphrasis}</i>>, gephi_label="ph.", phase_number="{label}", paraphrasis="{phase_paraphrasis.replace("<br/>", " ")}", shape="box", fillcolor="{fillcolor}", color="{node_color}", style="{style}"{original_id_attr}];\n\n'
                cluster_lines.append(node_line)

            # Add the cluster_id to the corresponding phase in sequences_dict
            sequences_dict[phase_absolute_number]['cluster_id'] = cluster_id 
                
            # Add edges between phases
            sorted_phase_numbers = sorted(sequence_dict_filtered.keys())
            for i in range(len(sorted_phase_numbers) - 1):
                source_phase_id = sequence_dict_filtered[sorted_phase_numbers[i]]['phase_id']
                target_phase_id = sequence_dict_filtered[sorted_phase_numbers[i + 1]]['phase_id']
                edge_style = "dashed" if implicit == "true" else "solid"
                edge_line = f'"{source_phase_id}" -> "{target_phase_id}" [dir=none, color="{node_color}", style="{edge_style}"];\n\n'
                cluster_lines.append(edge_line)

            # Add lines for the sequence cluster
            dot_file.write(f'\nsubgraph cluster_{cluster_id} {{\n')
            dot_file.write(f'label=<{cluster_label}>;\n\n')
            dot_file.write(f'peripheries=1;\n\n')
            for cluster_line in cluster_lines:
                dot_file.write(cluster_line)
            dot_file.write('}\n\n')
            written_lines.extend(cluster_lines)
            
            # Add edge from THESIS to the first phase
            first_phase_id = sequence_dict_filtered[min(sequence_dict_filtered.keys())]['phase_id']
            dot_file.write(f'"{element_id}" -> "{first_phase_id}" [dir=none, lhead="cluster_{cluster_id}", color="{node_color}"];\n\n')    
            
            # Check for matching sequences in PROPOSITIONs to process them
            written_lines = process_matching_prop_sequences(element, namespaces, all_propositions, sequence_dict_filtered, written_prop_phases, cluster_id, first_phase_id, written_lines, dot_file)

    return written_lines

def process_matching_prop_sequences(element, namespaces, all_propositions, sequence_dict_filtered, written_prop_phases, cluster_id, first_phase_id, written_lines, dot_file):
    """Process matching proposition sequences: write phase nodes and connect them to the thesis cluster."""
    # Track processed sequence references to avoid duplication
    processed_sequences = set()
    
    matching_propositions_group = element.find('.//thesu:matchingPropositionsGroup', namespaces=namespaces)
    if matching_propositions_group is not None:
        # First, collect all matching proposition sequences
        sequence_refs = []
        for sequence_dict in sequence_dict_filtered.values():
            sequence_element = sequence_dict['sequence_element']
            matching_sequences = sequence_element.findall('.//thesu:matchingPropositionSequence[@thesu:sequenceRef]', namespaces=namespaces)
            
            for match_seq in matching_sequences:
                prop_sequence_ref = match_seq.get('{http://alchemeast.eu/thesu/ns/1.0}sequenceRef')
                matching_sequence_id = prop_sequence_ref.split('#')[-1]
                
                # Only add if not already processed
                if matching_sequence_id not in processed_sequences:
                    sequence_refs.append(matching_sequence_id)
                    processed_sequences.add(matching_sequence_id)
        
        # Now process each matching sequence
        for seq_index, matching_sequence_id in enumerate(sequence_refs):
            # Find the matching proposition for this sequence
            first_prop_phase_id = None
            prop_cluster_id = None
            matching_prop_phases = {}
            
            for prop_id, proposition_element in all_propositions.items():
                matching_sequence = proposition_element.find(f'.//thesu:sequence[@xml:id="{matching_sequence_id}"]', namespaces=namespaces)
                
                if matching_sequence is not None:
                    # Find all proposition phases for this sequence
                    for prop_phase_id, prop_phase_data in written_prop_phases.items():
                        if matching_sequence_id in prop_phase_data.get('sequence_id', ''):
                            matching_prop_phases[prop_phase_id] = prop_phase_data
                            
                            # Store the first phase ID and cluster ID if not already set
                            if first_prop_phase_id is None:
                                first_prop_phase_id = prop_phase_data['phase_id']
                                prop_cluster_id = prop_phase_data.get('cluster_id')
                    
                    # If we found valid phases, process the connection
                    if first_prop_phase_id is not None and prop_cluster_id is not None:
                        # Update the sequence_dict_filtered to include information about which matchingPropositionPhases to use
                        for phase_data in sequence_dict_filtered.values():
                            phase_element = phase_data['phase_element']
                            matching_phases_elements = phase_element.findall('.//thesu:matchingPropositionPhases', namespaces=namespaces)
                            
                            # Check if we have a matching matchingPropositionPhases element for this sequence
                            if seq_index < len(matching_phases_elements):
                                # Get the phasesRef for the corresponding index
                                matching_phases_element = matching_phases_elements[seq_index]
                                phases_ref = matching_phases_element.get('{http://alchemeast.eu/thesu/ns/1.0}phasesRef')
                                parsed_phases_ref = parse_phases_ref(phases_ref)
                                
                                # Also get the attributes
                                attrs = {}
                                for attr in ['extended', 'partial', 'generalized', 'specified', 'quoted', 'altered']:
                                    attr_value = matching_phases_element.get(f'{{http://alchemeast.eu/thesu/ns/1.0}}{attr}')
                                    if attr_value == 'true':
                                        attrs[attr] = 'true'
                                    else:
                                        attrs[attr] = 'false'
                                
                                # Temporarily override the phase data for this particular sequence matching
                                phase_data_copy = phase_data.copy()
                                phase_data_copy['parsed_phases_ref'] = parsed_phases_ref
                                phase_data_copy['matching_attributes'] = attrs
                                
                                # Process this specific match
                                written_lines = draw_edges_with_prop_sequences(
                                    {phase_data['phase_absolute_number']: phase_data_copy}, 
                                    matching_prop_phases, 
                                    cluster_id, 
                                    prop_cluster_id, 
                                    first_phase_id, 
                                    first_prop_phase_id, 
                                    written_lines, 
                                    dot_file
                                )
                            else:
                                # Silent mode - no warning messages
                                pass
                        
                        break # Found the proposition, no need to continue looking
            
            # Silent mode - no warning if sequence not found
    
    return written_lines

def draw_edges_with_prop_sequences(sequence_dict_filtered, written_prop_phases, cluster_id, prop_cluster_id, first_phase_id, first_prop_phase_id, written_lines, dot_file):
    """Draw invisible edges connecting thesis phases to matching proposition phases."""
    # Use a counter to ensure unique pseudo-node IDs even across different sequence matches
    node_counter = 1
    while True:
        pseudo_node_id = generate_unique_pseudo_node_id_matching_sequences(written_lines, cluster_id, prop_cluster_id, node_counter)
        # Check if this exact ID already exists in the written lines
        if not any(f'"{pseudo_node_id}"' in line for line in written_lines):
            break
        node_counter += 1
    
    line_to_write = f'"{pseudo_node_id}" [shape="point", style="invis", gephi_invis="true"];\n\n'
    dot_file.write(line_to_write)
    written_lines.append(line_to_write)

    # Create the two edges
    line_to_write = f'"{pseudo_node_id}" -> "{first_prop_phase_id}" [dir=none, lhead="cluster_{prop_cluster_id}", style="invis", gephi_invis="true"];\n\n'
    dot_file.write(line_to_write)
    written_lines.append(line_to_write)

    line_to_write = f'"{pseudo_node_id}" -> "{first_phase_id}" [dir=none, lhead="cluster_{cluster_id}", style="invis", gephi_invis="true"];\n\n'
    dot_file.write(line_to_write)
    written_lines.append(line_to_write)
    
    # Map proposition phases by both their group number and their overall number
    prop_phases_by_group = {}
    prop_phases_by_number = {}
    
    # First, organize by group
    for phase_id, phase_data in written_prop_phases.items():
        group_num = phase_data.get('phase_group_number')
        if group_num not in prop_phases_by_group:
            prop_phases_by_group[group_num] = []
        prop_phases_by_group[group_num].append(phase_data)
    
    # Sort phases within each group by phase_number_in_group
    for group_num in prop_phases_by_group:
        prop_phases_by_group[group_num].sort(key=lambda x: x.get('phase_number_in_group', 0))
        
        # Now map by their sequence position (1-indexed within group)
        for i, phase in enumerate(prop_phases_by_group[group_num]):
            prop_phases_by_number[(group_num, i+1)] = phase

    # Store edges to write at the end for better z-ordering
    connection_edges = []

    # Add connections for phases with matchingPropositionPhases
    for phase_data in sequence_dict_filtered.values():
        phase_id = phase_data.get('phase_id')
        parsed_phases_ref = phase_data.get('parsed_phases_ref')
        
        if parsed_phases_ref is not None:
            # Get matching types for this phase data
            matching_type = []
            matching_attributes = phase_data.get('matching_attributes', {})
            attributes = ['extended', 'partial', 'generalized', 'specified', 'quoted', 'altered']
            gephi_label = "matc"  # Default
            
            for attr in attributes:
                attr_value = matching_attributes.get(attr)
                if attr_value == 'true':
                    if attr == 'extended':
                        matching_type.append('extends')
                        gephi_label = "exts"
                    elif attr == 'partial':
                        matching_type.append('is part of')
                        gephi_label = "part"
                    elif attr == 'generalized':
                        matching_type.append('generalizes')
                        gephi_label = "gens"
                    elif attr == 'specified':
                        matching_type.append('specifies')
                        gephi_label = "spec"
                    elif attr == 'quoted':
                        matching_type.append('is quoted in')
                        gephi_label = "qted"
                    elif attr == 'altered':
                        matching_type.append('alters')
                        gephi_label = "alts"
            
            matching_type_str = ',<br/>'.join(matching_type) if matching_type else 'matches'
            
            # Process each phase group reference
            connections_created = 0
            for group_num, phase_nums in parsed_phases_ref.items():
                if not phase_nums:
                    # If no specific phases mentioned, include all phases in the group
                    if group_num in prop_phases_by_group:
                        for matching_prop_phase in prop_phases_by_group[group_num]:
                            # Use simpler edge styling that won't create visual artifacts
                            line_to_write = f'"{matching_prop_phase["phase_id"]}" -> "{phase_id}" [xlabel=<{matching_type_str}>, fontsize=10, fontcolor="#9673a6", fontname="bold", color="#9673a6", style="dotted", penwidth=1.25, gephi_label={gephi_label}];\n\n'
                            connection_edges.append(line_to_write)
                            connections_created += 1
                else:
                    # Find specific phases in this group
                    for phase_num in phase_nums:
                        key = (group_num, phase_num)
                        if key in prop_phases_by_number:
                            matching_specific_phase = prop_phases_by_number[key]
                            # Use simpler edge styling that won't create visual artifacts
                            line_to_write = f'"{matching_specific_phase["phase_id"]}" -> "{phase_id}" [xlabel=<{matching_type_str}>, fontsize=10, fontcolor="#9673a6", fontname="bold", color="#9673a6", style="dotted", penwidth=1.25, gephi_label={gephi_label}];\n\n'
                            connection_edges.append(line_to_write)
                            connections_created += 1
                            
    # Write all the connection edges at the end
    for edge in connection_edges:
        dot_file.write(edge)
        written_lines.append(edge)
    
    return written_lines

def write_thesis_and_process_included_elements(element, element_id, element_type, element_speaker, paraphrasis, namespaces, dot_file, written_lines, retrieved_text, retrieved_text_snippet, locus, processed_propositions, source_id=None):
    """Write the thesis node and process all included elements (entailments, analogies, references, sequences)."""
    # Get both entailments and analogies
    entailments_dict = get_thesis_entailments(element, namespaces)
    etiologies_dict = get_thesis_etiologies(element, namespaces, element_id)
    analogies_dict = get_thesis_analogies(element, namespaces)
    
    # Checks for attributes and color
    extrinsic_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}extrinsic')
    implicit_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}implicit')
    
    if extrinsic_att == "true":
        color_fill = "#fcfffd"
        color_peripheries = "#666666"
        style = "rounded,filled,dashed"
        manifestation = "extrinsic"
        element_type_label = f"extr. {element_type}"
        implicit = "true"
    elif implicit_att == "true":
        color_fill = "#fcfffd"
        color_peripheries = "#666666"
        style = "rounded,filled,dashed"
        manifestation = "implicit"
        element_type_label = f"impl. {element_type}"
        implicit = "true"
    else:
        color_fill = "#f0faf0"
        color_peripheries = "#82b366"
        style = "rounded,filled"    
        manifestation = "explicit"
        element_type_label = f"{element_type}"
        implicit = "false"
    
    # Add source_id attribute if available
    source_attr = f', source="{source_id}"' if source_id else ''
    
    # Prepare node attributes
    label_content = (
        f'<<b>{element_type_label}</b><br/>'
        f'{pad_short_string(element_speaker, 30)}<br/>'
        f'{locus}<br/>'
        f'<i>{paraphrasis}</i>'
        f'<font point-size="12">"{retrieved_text_snippet}"</font>>'
    )
    
    locus_formatted = locus.replace(" (of ", "_").replace(")", "").replace("<i>", "").replace("</i>", "")
    paraphrasis_formatted = paraphrasis.replace("<br/>", " ")
    
    # Construct the node string
    node_str = (
        f'"{element_id}" ['
        f'label={label_content}, '
        f'gephi_label="{element_type[:4]}", '
        f'locus="{locus_formatted}", '
        f'speaker="{element_speaker.strip()}", '
        f'text="{retrieved_text}", '
        f'paraphrasis="{paraphrasis_formatted}", '
        f'manifestation="{manifestation}"'
        f'{source_attr}, '
        f'fillcolor="{color_fill}", '
        f'color="{color_peripheries}", '
        f'style="{style}", '
        f'shape="box", '
        f'margin="0.30,0.1"];\n\n'
    )

    # Determine if we need a cluster for the thesis
    needs_cluster = bool(entailments_dict)
    cluster_created = False
    
    # Create cluster if needed (for entailments)
    if needs_cluster:
        cluster_id = f"{element_id}_ENTAILED".replace('.', '_')
        cluster_label = "Entailed"
        dot_file.write(f'\nsubgraph cluster_{cluster_id} {{\n')
        dot_file.write(f'label=<<font color="{color_peripheries}">{cluster_label}</font>>\n')
        dot_file.write(f'style="dotted";\n\n')
        
        # Write the thesis node INSIDE the cluster
        dot_file.write(node_str)
        
        # Close the cluster
        dot_file.write('}\n\n\n')
        cluster_created = True
    else:
        # Write the thesis node (not in a cluster)
        dot_file.write(node_str)
            
    # Close the cluster if one was created
    if cluster_created:
        dot_file.write('}\n\n\n')
    
    # Process entailments if present
    if entailments_dict:
        for entailment in entailments_dict.items():
            entailed_by_ref = entailment[0]
            entailed_as = entailment[1].split('#')[-1]
            
            # Create a pseudo-node with its own ID
            pseudo_node_id = generate_unique_pseudo_node_id_entailments(written_lines, entailed_by_ref, element_id, 1)
            line_to_write = f'"{pseudo_node_id}" [label=<by {entailed_as},<br/>ENTAILS>, fontsize="11", style="{style}", fillcolor="{color_fill}", color="{color_peripheries}", shape="house"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            # Create the two edges
            line_to_write = f'"{entailed_by_ref}" -> "{pseudo_node_id}" [dir=none, color="{color_peripheries}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            line_to_write = f'"{pseudo_node_id}" -> "{element_id}" [color="{color_peripheries}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
    
    # Process etiologies if present
    if etiologies_dict:
        for referenced_id, etiology_info in etiologies_dict.items():
            is_cause = etiology_info["is_cause"]
            is_end = etiology_info["is_end"]
            has_cause_siblings = etiology_info["has_cause_siblings"]
            has_end_siblings = etiology_info["has_end_siblings"]
            
            # Create a pseudo-node with its own ID
            pseudo_node_id = generate_unique_pseudo_node_id_etiologies(written_lines, referenced_id, element_id, 1)
            
            # Determine the relationship label based on the attributes
            if is_cause:
                etiology_label = "ITS EFFECT<br/>in etiology"
            elif is_end:
                etiology_label = "ITS MEANS<br/>in etiology"
            else:
                # Not explicitly marked as cause or end
                if has_cause_siblings and not has_end_siblings:
                    etiology_label = "ITS CAUSE<br/>in etiology"
                elif has_end_siblings and not has_cause_siblings:
                    etiology_label = "ITS PURPOSE<br/>in etiology"
                elif has_cause_siblings and has_end_siblings:
                    etiology_label = "ITS CAUSE & PURPOSE<br/>in etiology"
                else:
                    etiology_label = "CORRELATED<br/>in etiology"
                
            # Use teal/turquoise colors for etiology nodes and edges (different from analogy's yellow)
            etiology_fill_color = "#e0ffff"  # Light cyan fill
            etiology_border_color = "#008b8b"  # Dark cyan border
            
            # Create the pseudo-node with teal coloring
            line_to_write = f'"{pseudo_node_id}" [label=<{etiology_label}>, fontsize="11", style="{style}", fillcolor="{etiology_fill_color}", color="{etiology_border_color}", shape="diamond"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            # Create the two edges - from referenced element to pseudo-node and from pseudo-node to current element
            line_to_write = f'"{referenced_id}" -> "{pseudo_node_id}" [dir=none, color="{etiology_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            line_to_write = f'"{pseudo_node_id}" -> "{element_id}" [color="{etiology_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

    # Process analogies if present
    if analogies_dict:
        for referenced_id, analogy_info in analogies_dict.items():
            is_comparans = analogy_info["is_comparans"]
            
            # Create a pseudo-node with its own ID
            pseudo_node_id = generate_unique_pseudo_node_id_analogies(written_lines, referenced_id, element_id, 1)
            
            # Set the label based on whether it's a comparans or not
            if is_comparans:
                analogy_label = "<i>as source</i>,<br/>COMPARED IN"
            else:
                analogy_label = "COMPARED IN"
                
            # Use yellow colors for analogy nodes and edges
            analogy_fill_color = "#ffffd0"  # Light yellow fill
            analogy_border_color = "#d4d400"  # Darker yellow border
            
            # Create the pseudo-node with yellow coloring
            line_to_write = f'"{pseudo_node_id}" [label=<{analogy_label}>, fontsize="11", style="{style}", fillcolor="{analogy_fill_color}", color="{analogy_border_color}", shape="diamond"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            # Create the two edges - from referenced element to pseudo-node and from pseudo-node to current element
            line_to_write = f'"{referenced_id}" -> "{pseudo_node_id}" [dir=none, color="{analogy_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            line_to_write = f'"{pseudo_node_id}" -> "{element_id}" [color="{analogy_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

    # Process references if present
    references_dict = get_thesis_references(element, namespaces)
    if references_dict:
        for referenced_id, ref_source in references_dict.items():
            # Create a pseudo-node with its own ID
            pseudo_node_id = generate_unique_pseudo_node_id_references(written_lines, element_id, referenced_id, 1)
            
            # Use olive colors for reference nodes and edges
            reference_fill_color = "#f0f3e0"  # Very light olive fill
            reference_border_color = "#708238"  # Olive border
            
            # Create the pseudo-node
            line_to_write = f'"{pseudo_node_id}" [label=<IS REFERENCED IN>, fontsize="11", style="rounded,filled", fillcolor="{reference_fill_color}", color="{reference_border_color}", shape="note"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            # Create the two edges - from referenced element to pseudo-node and from pseudo-node to current element
            line_to_write = f'"{referenced_id}" -> "{pseudo_node_id}" [dir=none, color="{reference_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)

            line_to_write = f'"{pseudo_node_id}" -> "{element_id}" [color="{reference_border_color}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
            
    return written_lines, implicit, color_fill, color_peripheries, style, processed_propositions

def process_thesis_element(element, element_type, namespaces, all_propositions, dot_file, written_lines, stored_edges, written_prop_phases, retrieved_text, retrieved_text_snippet, locus, processed_propositions, source_id=None):
    """Main entry: process a THESIS element and delegate to write_thesis_and_process_included_elements."""

    
    element_id = element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
    if element_id is None:
        element_id = element.get('{http://www.w3.org/XML/1998/namespace}id')
    
    # Get all speakers from speakersGroup
    speaker_elements = element.findall('.//thesu:speakersGroup/thesu:speaker', namespaces=namespaces)
    
    # Process speakers according to rank
    element_speaker = ""
    if speaker_elements:
        # Get rank for each speaker (default is 1 if not specified)
        speakers_with_rank = []
        for spk in speaker_elements:
            name_val = spk.get('{http://alchemeast.eu/thesu/ns/1.0}name')
            if name_val:
                speaker_name = name_val.split('#')[-1]
                rank_val = spk.get('{http://alchemeast.eu/thesu/ns/1.0}rank')
                rank = int(rank_val) if rank_val and rank_val.isdigit() else 1
                speakers_with_rank.append((speaker_name, rank))
        
        if speakers_with_rank:
            # Find minimum rank (highest priority)
            min_rank = min(rank for _, rank in speakers_with_rank)
            
            # Get all speakers with this highest priority rank
            top_speakers = [name for name, rank in speakers_with_rank if rank == min_rank]
            
            # Join speaker names with commas
            element_speaker = ", ".join(top_speakers)
    
    paraphrasis_elem = element.find("./thesu:paraphrasis", namespaces=namespaces)
    if paraphrasis_elem is not None:
        paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
        paraphrasis = re.sub(r'\s+', ' ', paraphrasis)
        paraphrasis = re.sub(r'(.{1,50})(?:\s|$)', r'\1<br/>', paraphrasis)
        paraphrasis = paraphrasis.replace('"', r'\"')
    else:
        paraphrasis = "/"

    # Write thesis and process entailments
    # write_thesis_and_process_included_elements is now in this module, so it can be called directly
    written_lines, implicit, color_fill, color_peripheries, style, processed_propositions = write_thesis_and_process_included_elements(element, element_id, element_type, pad_short_string(element_speaker, 30), paraphrasis, namespaces, dot_file, written_lines, retrieved_text, retrieved_text_snippet, locus, processed_propositions, source_id)
        
    # Check for matching PROPOSITION elements
    written_lines, processed_propositions = process_matching_propositions(element, element_id, namespaces, all_propositions, dot_file, written_lines, stored_edges, written_prop_phases, processed_propositions)
        
    # Iterate through the THESIS's sequences
    from config.runtime_settings import filter_propositions, filter_matching_proposition_sequences
    written_lines = process_thesis_sequences(element, element_id, namespaces, dot_file, written_lines, all_propositions, written_prop_phases, implicit, color_fill, color_peripheries, style, filter_propositions, filter_matching_proposition_sequences)

    return written_lines, processed_propositions
