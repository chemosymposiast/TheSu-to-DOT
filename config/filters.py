"""Filter parsing and application for propositions, sequences, and thesis focus.

Key functions: parse_custom_prop_filters, parse_custom_seq_phase_filters,
apply_custom_prop_filters, apply_custom_seq_phase_filters, apply_thesis_focus_filter
"""
from bootstrap.delayed_imports import ET
from xml_processing.selectors import find_parent_thesis


def parse_custom_prop_filters(filter_strings):
    """Parses a list of 'thesis_id to proposition_id' strings into a dict: {prop_id: [thesis_id1, ...]}. """
    filters = {}
    if not filter_strings:
        return filters
    for f_str in filter_strings:
        parts = f_str.split(" to ")
        if len(parts) == 2:
            thesis_id = parts[0].strip()
            # Handle optional '#' prefix and ensure it's a valid ID format if needed
            prop_id = parts[1].strip().lstrip('#') 
            if prop_id not in filters:
                filters[prop_id] = []
            # Avoid duplicate thesis IDs for the same prop
            if thesis_id not in filters[prop_id]: 
                 filters[prop_id].append(thesis_id)
        else:
            print(f"Warning: Invalid custom proposition filter format skipped: '{f_str}'")
    return filters
    

def parse_custom_seq_phase_filters(filter_strings):
    """Parses a list of 'thesis_id to sequence_id' strings into a dict: {seq_id: [thesis_id1, ...]}. """
    filters = {}
    if not filter_strings:
        return filters
    for f_str in filter_strings:
        parts = f_str.split(" to ")
        if len(parts) == 2:
            thesis_id = parts[0].strip()
            seq_id = parts[1].strip().lstrip('#') 
            if seq_id not in filters:
                filters[seq_id] = []
            if thesis_id not in filters[seq_id]: 
                 filters[seq_id].append(thesis_id)
        else:
            print(f"Warning: Invalid custom sequence/phase filter format skipped: '{f_str}'")
    return filters



# Function to apply the complex custom proposition filtering logic
def apply_custom_prop_filters(xml_root, all_propositions, custom_prop_filters_map, namespaces):
    """Applies custom proposition filters to remove matchingProposition elements 
       and their related sequences/phases based on a {prop_id: [thesis_id,...]} map."""
    if not custom_prop_filters_map:
        return

    propositions_to_filter = list(custom_prop_filters_map.keys())
    # Store {prop_id: [seq_id1, seq_id2, ...]}
    prop_sequences_map = {} 
    # Store {prop_id: [thesis_element1, thesis_element2,...]} to link prop to affected theses
    affected_thesis_elements_map = {} 

    # Store results for summary logging: {(prop_id, thesis_id): {"seq_removed": bool, "phases_removed_count": int}}
    filter_summary = {}

    # --- Action 1: Remove matchingProposition based on propRef and parent Thesis ID ---
    matching_props_to_remove = []
    # Use namespace-aware XPath
    for match_prop in xml_root.xpath('.//thesu:matchingProposition', namespaces=namespaces):
        # Get attribute using QName for namespace awareness
        prop_ref = match_prop.get(ET.QName(namespaces['thesu'], 'propRef'))
        if not prop_ref:
            continue

        prop_ref_id = prop_ref.lstrip('#')
        if prop_ref_id in propositions_to_filter:
            # Find the parent THESIS element
            parent_thesis = find_parent_thesis(match_prop, namespaces) 
            if parent_thesis is not None: 
                # Get xml:id using QName
                thesis_id = parent_thesis.get(ET.QName(namespaces['xml'], 'id'))
                # Check if this specific thesis-proposition pair is in the filter map
                if thesis_id in custom_prop_filters_map.get(prop_ref_id, []):
                    matching_props_to_remove.append(match_prop)
                    # Initialize summary entry
                    summary_key = (prop_ref_id, thesis_id)
                    if summary_key not in filter_summary:
                        filter_summary[summary_key] = {"seq_removed": False, "phases_removed_count": 0}
                        
                    # Store the actual thesis element associated with the prop_id filter
                    if prop_ref_id not in affected_thesis_elements_map:
                         affected_thesis_elements_map[prop_ref_id] = []
                    # Avoid adding the same element multiple times if multiple props point to it
                    if parent_thesis not in affected_thesis_elements_map[prop_ref_id]:
                         affected_thesis_elements_map[prop_ref_id].append(parent_thesis) 


    # Perform the removal after iteration to avoid modifying the tree while iterating
    for mp in matching_props_to_remove:
        parent = mp.getparent()
        if parent is not None:
            try:
                parent.remove(mp)
                # Suppressed: print(f"INFO (PropFilter): Removed matchingProposition with propRef {mp.get(...)} from Thesis {thesis_id}")
            except ValueError:
                 print(f"DEBUG (PropFilter): Could not remove matchingProposition with propRef {mp.get(ET.QName(namespaces['thesu'], 'propRef'))} - possibly already removed.")


    # --- Action 2: Identify sequences within the targeted propositions ---
    for prop_id in propositions_to_filter:
        # Only process if this prop_id actually led to a removal
        if prop_id in affected_thesis_elements_map and prop_id in all_propositions: 
            prop_elem = all_propositions[prop_id]
            # Use namespace-aware XPath for 'sequence' elements with 'xml:id'
            sequences = prop_elem.xpath('.//thesu:sequence[@xml:id]', namespaces=namespaces)
            # Fallback for xml:id without namespace prefix (less ideal) - ensure xml ns is used
            if not sequences:
                sequences = prop_elem.xpath('.//thesu:sequence[@*[namespace-uri()="{}" and local-name()="id"]]'.format(namespaces['xml']), namespaces=namespaces)


            if sequences:
                prop_sequences_map[prop_id] = [seq.get(ET.QName(namespaces['xml'], 'id')) for seq in sequences]


    # --- Action 3: Process matchingPropositionSequence and matchingPropositionPhases ---
    # Track (parent_sequence_element_instance) to avoid reprocessing siblings within the same parent sequence
    processed_parent_sequences_prop_filter = set() 

    # Iterate through propositions that had matchingProps removed and had sequences identified
    for prop_id, target_sequence_ids in prop_sequences_map.items():
        if not target_sequence_ids or prop_id not in affected_thesis_elements_map:
            continue # Skip if no sequences or no matchingProps were removed for this prop_id

        # Iterate through the actual thesis elements affected by this specific prop_id filter
        for thesis_element in affected_thesis_elements_map[prop_id]:
            thesis_id = thesis_element.get(ET.QName(namespaces['xml'], 'id'))
            
            # Find potentially relevant matchingPropositionSequence elements within this specific thesis
            seqs_to_check = thesis_element.xpath('.//thesu:matchingPropositionSequence', namespaces=namespaces)
            
            sequences_to_process_in_parent = {} # {parent_sequence: [(m_seq_to_remove, original_index)]}

            # First pass: Identify all m_seq elements to remove within this thesis, grouped by parent
            for m_seq in seqs_to_check:
                seq_ref = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'))
                if not seq_ref or seq_ref.lstrip('#') not in target_sequence_ids:
                    continue # This sequenceRef doesn't match the filtered proposition's sequences

                parent_sequence = m_seq.getparent()
                # Ensure parent is a thesu:sequence element
                if parent_sequence is None or parent_sequence.tag != ET.QName(namespaces['thesu'], 'sequence'):
                    print(f"DEBUG (PropFilter): Skipping matchingPropositionSequence {seq_ref} - parent is not thesu:sequence or is None.")
                    continue

                # If this parent hasn't been processed yet in this filter run
                if parent_sequence not in processed_parent_sequences_prop_filter:
                     # Find siblings (including self for index) relative to the parent
                     siblings = parent_sequence.xpath('./thesu:matchingPropositionSequence', namespaces=namespaces)
                     try:
                         removed_index = siblings.index(m_seq)
                         num_siblings = len(siblings)
                         
                         if parent_sequence not in sequences_to_process_in_parent:
                             sequences_to_process_in_parent[parent_sequence] = []
                         # Store the element and its *original* index before any removals in this parent
                         sequences_to_process_in_parent[parent_sequence].append((m_seq, removed_index, num_siblings)) 

                     except ValueError:
                          print(f"DEBUG (PropFilter): Error finding index for {seq_ref} in parent {parent_sequence.tag}. Skipping.")
                          continue 

            # Second pass: Process removals and phase adjustments per parent_sequence
            for parent_sequence, items_to_remove in sequences_to_process_in_parent.items():
                if parent_sequence in processed_parent_sequences_prop_filter:
                     continue # Already handled this parent in this filter run

                # Sort items by ORIGINAL index descending
                items_to_remove.sort(key=lambda x: x[1], reverse=True)
                # Handle corresponding matchingPropositionPhases
                # Find the sibling <phase> elements containing the matchingPropositionPhases
                # These are nested under phasesGroup/newPhases relative to the parent_sequence
                phase_elements = parent_sequence.xpath('.//thesu:newPhases/thesu:phase[thesu:matchingPropositionPhases]', namespaces=namespaces)
                phases_to_remove_map = {} # {phase_element: [mpp_to_remove, ...]}

                if phase_elements:
                    phases_info = {} # {phase_element: [mpp_sibling1, mpp_sibling2,...]}
                    for phase_element in phase_elements:
                        # Find direct MPP children of this phase
                        mpp_siblings = phase_element.xpath('./thesu:matchingPropositionPhases', namespaces=namespaces)
                        phases_info[phase_element] = mpp_siblings
                    
                    # Determine which phases need removal 
                    for m_seq, removed_index, num_m_seq_siblings in items_to_remove:
                        seq_ref_id = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'), 'unknown')
                        # Check within each relevant phase element
                        for phase_element, mpp_siblings in phases_info.items():
                            num_mpp_siblings = len(mpp_siblings)
                            phase_to_remove = None

                            if num_m_seq_siblings == 1 and num_mpp_siblings == 1:
                                phase_to_remove = mpp_siblings[0]
                            elif num_mpp_siblings >= 1 and removed_index < num_mpp_siblings:
                                # Find the MPP sibling at the same index as the removed M_SEQ sibling
                                phase_to_remove = mpp_siblings[removed_index]                            
                            if phase_to_remove is not None:
                                # Store the phase element (parent) and the MPP child to remove
                                if phase_element not in phases_to_remove_map:
                                    phases_to_remove_map[phase_element] = []
                                if phase_to_remove not in phases_to_remove_map[phase_element]: 
                                    phases_to_remove_map[phase_element].append(phase_to_remove)
                
                # Perform removals (m_seq first)
                for m_seq, _, _ in items_to_remove: # Index already used, no longer needed
                    seq_ref_id = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'), 'unknown')
                    try:
                        parent_sequence.remove(m_seq)
                        print(f"PropFilter: Removed matchingPropositionSequence with seqRef {seq_ref_id} from Thesis {thesis_id}")
                    except ValueError:
                         print(f"DEBUG (PropFilter): Could not remove m_seq {seq_ref_id} - already gone?")
                
                # Remove phase elements
                for phase_element, mpp_to_remove_list in phases_to_remove_map.items():
                    for mpp_to_remove in mpp_to_remove_list:
                        try:
                            phase_element.remove(mpp_to_remove)
                            # Increment phase count in summary
                            summary_key = (prop_id, thesis_id)
                            if summary_key in filter_summary:
                                filter_summary[summary_key]["phases_removed_count"] += 1
                            # Suppressed: print(f"INFO (PropFilter): Removed matchingPropositionPhases from phase {phase_element.get(...)} in Thesis {thesis_id}")
                        except ValueError:
                            # MPP already removed, maybe by another rule targeting the same phase? Or already gone.
                            print(f"DEBUG (PropFilter): Could not remove matchingPropositionPhases from phase {phase_element.get(ET.QName(namespaces['xml'], 'id'), '?')} - already gone?")

                # Mark this parent sequence as processed for this filter run
                processed_parent_sequences_prop_filter.add(parent_sequence)

# Function to apply the custom sequence/phase filtering logic based on Thesis ID -> Sequence ID mapping
def apply_custom_seq_phase_filters(xml_root, seq_to_thesis_map, namespaces):
    """Applies custom filters to remove matchingPropositionSequence and related 
       matchingPropositionPhases based on a {sequence_id: [thesis_id,...]} map."""
    if not seq_to_thesis_map:
        return

    print(f"--- Applying Custom Sequence/Phase Filters based on Thesis->Sequence Mappings ---")

    # Track parent sequences processed within this filter step to avoid redundant sibling calculations/removals
    processed_parent_sequences_seq_filter = set()
    
    # Store results for summary logging: {(seq_id, thesis_id): {"phases_removed_count": int}}
    filter_summary_seq = {}
    
    # Find all matchingPropositionSequence elements in the document
    all_matching_seqs = xml_root.xpath('.//thesu:matchingPropositionSequence', namespaces=namespaces)

    sequences_to_process_in_parent = {} # {parent_sequence: [(m_seq_to_remove, original_index, num_siblings)]}

    # First pass: Identify elements to remove based on sequenceRef AND ancestor Thesis ID matching the map
    for m_seq in all_matching_seqs:
        seq_ref = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'))
        if not seq_ref:
            continue

        seq_ref_id = seq_ref.lstrip('#')
        # Check if this sequence ID is part of any filter rule
        if seq_ref_id in seq_to_thesis_map:
            parent_sequence = m_seq.getparent()
            # Ensure parent is a thesu:sequence element
            if parent_sequence is None or parent_sequence.tag != ET.QName(namespaces['thesu'], 'sequence'):
                print(f"DEBUG (SeqFilter): Skipping {seq_ref_id} - parent is not thesu:sequence or is None.")
                continue

            # Find the ancestor THESIS for this specific m_seq instance
            ancestor_thesis = find_parent_thesis(m_seq, namespaces)
            if ancestor_thesis is None:
                print(f"DEBUG (SeqFilter): Skipping {seq_ref_id} - could not find ancestor THESIS.")
                continue
            
            ancestor_thesis_id = ancestor_thesis.get(ET.QName(namespaces['xml'], 'id'))

            summary_key_seq = (seq_ref_id, ancestor_thesis_id)
            
            # Check if the ancestor Thesis ID matches one of the IDs specified for this sequence ID in the map
            if ancestor_thesis_id in seq_to_thesis_map[seq_ref_id]:
                # Initialize summary entry if this sequence/thesis combo is targeted
                if summary_key_seq not in filter_summary_seq:
                    filter_summary_seq[summary_key_seq] = {"phases_removed_count": 0}
                    
                # This m_seq matches a filter rule (both sequence ID and thesis ID)
                
                # If this parent hasn't been queued for processing by this filter yet
                if parent_sequence not in processed_parent_sequences_seq_filter:
                    # Find siblings *before* queuing for removal
                    siblings = parent_sequence.xpath('./thesu:matchingPropositionSequence', namespaces=namespaces)
                    try:
                        removed_index = siblings.index(m_seq)
                        num_siblings = len(siblings)

                        if parent_sequence not in sequences_to_process_in_parent:
                            sequences_to_process_in_parent[parent_sequence] = []
                        # Store element and its original index
                        sequences_to_process_in_parent[parent_sequence].append((m_seq, removed_index, num_siblings))

                    except ValueError:
                         print(f"DEBUG (SeqFilter): Error finding index for {seq_ref_id}. Skipping.")
                         continue
            # else: This instance doesn't match the thesis ID requirement for this sequence ID.

    # Second pass: Process removals and phase adjustments per parent_sequence
    for parent_sequence, items_to_remove in sequences_to_process_in_parent.items():
        if parent_sequence in processed_parent_sequences_seq_filter:
             continue # Already processed by this filter run

        # Sort by original index descending for safe removal
        items_to_remove.sort(key=lambda x: x[1], reverse=True)

        # Need the thesis ID for logging, get it from the first item (they all share the same ancestor thesis)
        ancestor_thesis_id_log = "unknown_thesis"
        if items_to_remove:
             temp_thesis = find_parent_thesis(items_to_remove[0][0], namespaces)
             if temp_thesis is not None:
                 ancestor_thesis_id_log = temp_thesis.get(ET.QName(namespaces['xml'], 'id'), "unknown_thesis")

        # Handle corresponding matchingPropositionPhases 
        # Find the sibling <phase> elements containing the matchingPropositionPhases
        phase_elements = parent_sequence.xpath('.//thesu:newPhases/thesu:phase[thesu:matchingPropositionPhases]', namespaces=namespaces)
        phases_to_remove_map = {} # {phase_holder: [phase_element_to_remove, ...]}

        if phase_elements:
            phases_info = {} # {phase_element: [mpp_sibling1,...]}
            for phase_element in phase_elements:
                # Find direct MPP children of this phase
                mpp_siblings = phase_element.xpath('./thesu:matchingPropositionPhases', namespaces=namespaces)
                phases_info[phase_element] = mpp_siblings
        
            # Determine which phases need removal based on the indices of m_seq being removed
            for m_seq, removed_index, num_m_seq_siblings in items_to_remove: # Use sorted items
                seq_ref_id = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'), 'unknown') # Get ID for logging
                # Check within each relevant phase element
                for phase_element, mpp_siblings in phases_info.items():
                    num_mpp_siblings = len(mpp_siblings)
                    phase_to_remove = None

                    if num_m_seq_siblings == 1 and num_mpp_siblings == 1:
                        phase_to_remove = mpp_siblings[0]
                    elif num_mpp_siblings >= 1 and removed_index < num_mpp_siblings:
                        # Find the MPP sibling at the same index as the removed M_SEQ sibling
                        phase_to_remove = mpp_siblings[removed_index]
                    
                    if phase_to_remove is not None:
                        # Store the phase element (parent) and the MPP child to remove
                        if phase_element not in phases_to_remove_map:
                            phases_to_remove_map[phase_element] = []
                        if phase_to_remove not in phases_to_remove_map[phase_element]: 
                            phases_to_remove_map[phase_element].append(phase_to_remove)

        # Perform actual removals (m_seq first)
        for m_seq, _, _ in items_to_remove:
            seq_ref_id = m_seq.get(ET.QName(namespaces['thesu'], 'sequenceRef'), 'unknown')
            try:
                parent_sequence.remove(m_seq)
                # Suppressed: print(f"INFO (SeqFilter): Removed matchingPropositionSequence with seqRef {seq_ref_id} from Thesis {ancestor_thesis_id_log}")
            except ValueError:
                 print(f"DEBUG (SeqFilter): Could not remove m_seq {seq_ref_id} - already gone?")

        # Remove phase elements
        for phase_element, mpp_to_remove_list in phases_to_remove_map.items():
            for phase in mpp_to_remove_list:
                try:
                    phase_element.remove(phase)
                    # Increment phase count in summary for the specific seq/thesis combo
                    summary_key_seq = (seq_ref_id, ancestor_thesis_id_log) # Reconstruct key for logging
                    if summary_key_seq in filter_summary_seq:
                         filter_summary_seq[summary_key_seq]["phases_removed_count"] += 1
                    # Suppressed: print(f"INFO (SeqFilter): Removed matchingPropositionPhases from phase {phase_element.get(...)} in Thesis {ancestor_thesis_id_log}")
                except ValueError:
                    # MPP already removed
                    print(f"DEBUG (SeqFilter): Could not remove matchingPropositionPhases from phase {phase_element.get(ET.QName(namespaces['xml'], 'id'), '?')} - already gone?")

        # Mark parent as processed for this filter run
        processed_parent_sequences_seq_filter.add(parent_sequence)

    # Print summary logs
    for (seq_id, thesis_id), result in filter_summary_seq.items():
        # Only print if phases were actually removed for this combo
        if result["phases_removed_count"] > 0:
             print(f"INFO (SeqFilter): Processed filter for Sequence {seq_id} in Thesis {thesis_id}. PhasesRemovedCount={result['phases_removed_count']}.")
        else: # Optionally log even if no phases were removed but sequence was targeted
             print(f"INFO (SeqFilter): Processed filter for Sequence {seq_id} in Thesis {thesis_id}. No matching phases found/removed.")
             
    print(f"--- Custom Sequence/Phase Filtering Complete ---")

# Function to apply the Thesis Focus filter
def apply_thesis_focus_filter(xml_root, focus_thesis_ids, namespaces):
    """
    For each specified THESIS ID in focus_thesis_ids:
    1. Finds the THESIS element.
    2. Verifies it is a descendant of a 'thesu:source' element.
    3. If so, examines its immediate siblings.
    4. Removes any sibling UNLESS that sibling is itself a focused THESIS 
       or contains a descendant THESIS that is focused.
    """
    if not focus_thesis_ids:
        print("INFO (ThesisFocus): No focus IDs provided. Filter not active.")
        return

    focus_thesis_ids_set = set(focus_thesis_ids)
    
    print(f"--- Applying Thesis Focus Filter for IDs: {', '.join(sorted(list(focus_thesis_ids_set)))} ---")

    elements_to_remove = set()

    for focus_id in focus_thesis_ids: 
        if not focus_id: 
            continue

        xpath_query_target_thesis = f'.//thesu:THESIS[@xml:id="{focus_id}"]'
        target_thesis_elements = xml_root.xpath(xpath_query_target_thesis, namespaces=namespaces)

        if not target_thesis_elements:
            print(f"Warning (ThesisFocus): Target THESIS with xml:id='{focus_id}' not found. Skipping.")
            continue
        
        target_thesis_elem = target_thesis_elements[0]
        if len(target_thesis_elements) > 1:
            print(f"Warning (ThesisFocus): Multiple THESIS elements found for xml:id='{focus_id}'. Using the first one.")

        current_ancestor = target_thesis_elem.getparent()
        source_ancestor_found = False
        while current_ancestor is not None:
            if current_ancestor.tag == f"{{{namespaces['thesu']}}}source":
                source_ancestor_found = True
                break
            current_ancestor = current_ancestor.getparent()
        
        if not source_ancestor_found:
            print(f"Warning (ThesisFocus): Target THESIS '{focus_id}' is not a descendant of any 'thesu:source' element. Skipping sibling processing for it.")
            continue

        parent_of_target = target_thesis_elem.getparent()
        if parent_of_target is None: 
            print(f"Warning (ThesisFocus): Target THESIS '{focus_id}' has no parent, though reportedly under a source. Skipping sibling processing.")
            continue
        
        for potential_sibling in parent_of_target: 
            if potential_sibling is target_thesis_elem:
                continue 

            is_sibling_protected = False
            sibling_xml_id = potential_sibling.get(f"{{{namespaces['xml']}}}id")

            if potential_sibling.tag == f"{{{namespaces['thesu']}}}THESIS":
                if sibling_xml_id and sibling_xml_id in focus_thesis_ids_set:
                    is_sibling_protected = True

            if not is_sibling_protected:
                descendant_theses = potential_sibling.xpath('.//thesu:THESIS', namespaces=namespaces)
                for descendant_thesis in descendant_theses:
                    descendant_thesis_id = descendant_thesis.get(f"{{{namespaces['xml']}}}id")
                    if descendant_thesis_id and descendant_thesis_id in focus_thesis_ids_set:
                        is_sibling_protected = True
                        break 
            
            if not is_sibling_protected:
                elements_to_remove.add(potential_sibling)
    
    if not elements_to_remove:
        print("INFO (ThesisFocus): No elements marked for removal based on sibling logic.")
    else:
        print(f"INFO (ThesisFocus): Attempting to remove {len(elements_to_remove)} element(s)...")
        removed_count = 0
        for element in elements_to_remove:
            parent = element.getparent()
            if parent is not None: 
                try:
                    parent.remove(element)
                    removed_count += 1
                except ValueError: 
                    pass 
        print(f"INFO (ThesisFocus): Successfully removed {removed_count} element(s).")

    print(f"--- Thesis Focus Filtering Complete ---")


def apply_elements_to_exclude_filter(xml_root, exclude_ids, namespaces):
    """
    Remove THESIS and SUPPORT elements by xml:id before graph building.
    Used to exclude specific argument chains (e.g. the whetstones chain).
    """
    if not exclude_ids:
        return

    exclude_set = set(str(x).strip() for x in exclude_ids if x)
    if not exclude_set:
        return

    print(f"--- Applying Elements-to-Exclude Filter for {len(exclude_set)} ID(s) ---")

    removed_count = 0
    for elem_id in exclude_set:
        elem = xml_root.xpath(f'.//*[@xml:id="{elem_id}"]', namespaces=namespaces)
        if not elem:
            print(f"Warning (ElementsToExclude): Element with xml:id='{elem_id}' not found. Skipping.")
            continue
        target = elem[0]
        parent = target.getparent()
        if parent is not None:
            try:
                parent.remove(target)
                removed_count += 1
            except ValueError:
                print(f"DEBUG (ElementsToExclude): Could not remove {elem_id} - possibly already removed.")

    print(f"INFO (ElementsToExclude): Successfully removed {removed_count} element(s).")
    print(f"--- Elements-to-Exclude Filtering Complete ---")
