"""
DOT file generation orchestrator.

This module contains the main high-level function that orchestrates the creation
of DOT files from XML input. It coordinates XML parsing, filtering, preprocessing,
DOT building, and cleanup.
"""
from bootstrap.delayed_imports import ET
from config.runtime_settings import (
    sources_to_select, filter_propositions,
    filter_matching_proposition_sequences, filter_all_sequences,
    filter_extrinsic_elements, custom_prop_filters_to_apply,
    custom_seq_phase_filters_to_apply, thesis_focus_id,
    elements_to_exclude
)
from xml_processing import parse_included_files
from xml_processing.selectors import filter_elements
from config.filters import (
    apply_custom_prop_filters,
    apply_custom_seq_phase_filters,
    apply_thesis_focus_filter,
)
from dot.header import write_dot_file_header
from dot.elements import initialize_elements_clusters
from xml_processing import preload_document_sources
from dot.postprocess import (
    replace_original_xml_ids,
    reorganize_dot_file,
    redirect_or_remove_invalid_edges,
    remove_duplicate_definitions,
    normalize_dot_file_line_breaks,
    detect_and_fix_tuple_node_ids,
    remove_excluded_node_definitions,
    prune_and_connect_filtered_nodes,
)


def create_dot(xml_filename, dot_filename, sources_to_select=sources_to_select,
                   filter_propositions=filter_propositions,
                   filter_matching_proposition_sequences=filter_matching_proposition_sequences,
                   filter_all_sequences=filter_all_sequences,
                   filter_extrinsic_elements=filter_extrinsic_elements,
                   custom_prop_filters=custom_prop_filters_to_apply,
                   custom_seq_phase_filters=custom_seq_phase_filters_to_apply,
                   thesis_focus_id=thesis_focus_id,
                   elements_to_exclude=elements_to_exclude):
    """
    Main orchestrator function that creates a DOT file from XML input.
    
    This function handles:
    - XML parsing and validation
    - Source filtering
    - Custom filter application
    - DOT file generation (via dot.elements)
    - Post-processing cleanup (via dot.postprocess)
    """
    try:
        # Use lxml's parser
        parser = ET.XMLParser(remove_blank_text=True) 
        xml_tree = ET.parse(xml_filename, parser)
        xml_root = xml_tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file {xml_filename}: {e}")
        return
    except FileNotFoundError:
        print(f"Error: XML file not found at {xml_filename}")
        return
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred during XML loading: {e}")
        return


    namespaces = {'thesu': 'http://alchemeast.eu/thesu/ns/1.0', 'xi': 'http://www.w3.org/2001/XInclude', 'xml': 'http://www.w3.org/XML/1998/namespace', 'tei': 'http://www.tei-c.org/ns/1.0'}

    # Filter sources to keep only those in the sources_to_select list
    filtered_source_ids = []
    if sources_to_select:
        sources = xml_root.xpath('.//thesu:source', namespaces=namespaces)
        sources_to_remove = []
        for source in sources:
            source_id = source.get(ET.QName(namespaces['xml'], 'id'))            
            if source_id not in sources_to_select:
                filtered_source_ids.append(source_id)
                sources_to_remove.append(source)
                
        # Remove sources after iteration
        for source in sources_to_remove:
            parent = source.getparent()
            if parent is not None:
                try:
                    parent.remove(source)
                    print(f"Removed source: {source.get(ET.QName(namespaces['xml'], 'id'))}")
                except ValueError:
                    print(f"WARNING: Could not remove source {source.get(ET.QName(namespaces['xml'], 'id'))} - already gone?")


    # Parse the included XML files (assuming parse_included_files exists and uses lxml)
    all_propositions = {}
    try:
        included_files = xml_root.xpath('.//thesu:propositions/xi:include', namespaces=namespaces)
        all_propositions = parse_included_files(included_files, namespaces) 
    except NameError:
         print("Error: `parse_included_files` function is not defined.")
    except Exception as e:
        print(f"Error parsing included proposition files: {e}")


    # Preload all source documents and text segments (assuming function exists)
    try:
        preload_document_sources(xml_root, namespaces) 
    except NameError:
        print("Warning: `preload_document_sources` function is not defined.")
    except Exception as e:
        print(f"Error preloading document sources: {e}")


    # --- Apply Custom Proposition Filters --- 
    if custom_prop_filters:
        # Normalize keys in the input map (remove leading #)
        normalized_prop_filters_map = {pid.lstrip('#'): tids for pid, tids in custom_prop_filters.items()}
        if normalized_prop_filters_map:
            try:
                # Pass the normalized map directly
                apply_custom_prop_filters(xml_root, all_propositions, normalized_prop_filters_map, namespaces)
            except Exception as e:
                print(f"Error during custom proposition filtering: {e}")
        # else: No valid custom filters parsed

    # --- Apply Custom Sequence/Phase Filters --- 
    if custom_seq_phase_filters:
        # Normalize keys in the input map (remove leading #)
        normalized_seq_filters_map = {sid.lstrip('#'): tids for sid, tids in custom_seq_phase_filters.items()}
        if normalized_seq_filters_map:
            try:
                # Pass the normalized map directly
                apply_custom_seq_phase_filters(xml_root, normalized_seq_filters_map, namespaces)
            except Exception as e:
                print(f"Error during custom sequence/phase filtering: {e}")
            # Completion message is inside the function

    # (a) Filter out all PROPOSITION elements (if enabled)
    # This should happen AFTER custom filters
    if filter_propositions:
        all_propositions.clear() 
        matching_props = xml_root.xpath('.//thesu:matchingProposition', namespaces=namespaces)
        for match_prop in matching_props:
            parent = match_prop.getparent()
            if parent is not None:
                try:
                    parent.remove(match_prop)
                except ValueError: pass 

    # (b) Filter out matchingPropositionSequence, matchingPropositionPhases, 
    #     and sequence elements in PROPOSITIONs (if enabled and (a) is not)
    elif filter_matching_proposition_sequences:
        elements_to_remove = []
        elements_to_remove.extend(xml_root.xpath('.//thesu:matchingPropositionSequence', namespaces=namespaces))
        elements_to_remove.extend(xml_root.xpath('.//thesu:matchingPropositionPhases', namespaces=namespaces))
        
        for elem in elements_to_remove:
             parent = elem.getparent()
             if parent is not None:
                 try:
                      parent.remove(elem)
                 except ValueError: pass
        
        # Remove sequence elements from all_propositions (if they still exist)
        for prop_id, prop_elem in list(all_propositions.items()):
            prop_sequences_to_remove = prop_elem.xpath('.//thesu:sequence', namespaces=namespaces)
            for seq in prop_sequences_to_remove:
                parent = seq.getparent()
                if parent is not None:
                    try:
                        parent.remove(seq)
                    except ValueError: pass


    # (c) Filter out any sequence elements (if enabled and not overridden by b)
    if filter_all_sequences:
        sequences_to_remove = []
        sequences_to_remove.extend(xml_root.xpath('.//thesu:sequence', namespaces=namespaces))
        
        if not filter_propositions:
            for prop_id, prop_elem in list(all_propositions.items()):
                 sequences_to_remove.extend(prop_elem.xpath('.//thesu:sequence', namespaces=namespaces))
        
        unique_sequences_to_remove = list(set(sequences_to_remove)) 
        for seq in unique_sequences_to_remove:
            parent = seq.getparent()
            if parent is not None:
                try:
                    parent.remove(seq)
                except ValueError: pass

    # (d) Filter out any element with @extrinsic = true
    if filter_extrinsic_elements:
        extrinsic_elements_to_remove = []
        extrinsic_elements_to_remove.extend(xml_root.xpath('.//*[@thesu:extrinsic="true"]', namespaces=namespaces))
        
        for elem in extrinsic_elements_to_remove:
            parent = elem.getparent()
            if parent is not None:
                try:
                    parent.remove(elem)
                except ValueError: pass

    # --- Apply Thesis Focus Filter ---
    if thesis_focus_id:
        try:
            apply_thesis_focus_filter(xml_root, thesis_focus_id, namespaces)
        except Exception as e:
            print(f"Error during Thesis Focus filtering: {e}")

    # --- Apply Elements-to-Exclude Filter ---
    # Deferred to post-processing: we build the full DOT first, then remove excluded
    # node definitions so edge_validation can substitute with filtered pseudo-nodes
    # for any connection type (entailments, etiologies, analogies, references, etc.),
    # not just SUPPORT-related edges.

    # Ensure the rest of the DOT generation functions exist and are called correctly
    try:
        with open(dot_filename, 'w', encoding='utf-8') as dot_file:
            write_dot_file_header(dot_file) 

            elements = xml_root.xpath('.//thesu:AEsystem/*', namespaces=namespaces)
            filtered_elements = filter_elements(elements, namespaces) 

            written_lines, stored_edges, written_prop_phases, processed_elements, processed_propositions = initialize_elements_clusters(xml_root, filtered_elements, namespaces, all_propositions, dot_file)
            
            for edge in stored_edges:
                if "_to_" in edge:
                    dot_file.write(edge)

            dot_file.write('}\n\n\n')

        replace_original_xml_ids(dot_filename)
        detect_and_fix_tuple_node_ids(dot_filename)  
        
        #debug_dot_filename = dot_filename.replace('.dot', '_debug_after_filter.dot')
        #shutil.copy(dot_filename, debug_dot_filename)

        reorganize_dot_file(dot_filename)
        # Elements-to-exclude: post-process only when filter is active
        if elements_to_exclude:
            remove_excluded_node_definitions(dot_filename, elements_to_exclude)
        redirect_or_remove_invalid_edges(dot_filename, xml_filename, namespaces,
                                        elements_to_exclude=elements_to_exclude)
        if elements_to_exclude:
            prune_and_connect_filtered_nodes(dot_filename, elements_to_exclude)
        remove_duplicate_definitions(dot_filename)
        normalize_dot_file_line_breaks(dot_filename)

    except NameError as ne:
         print(f"Error: A required DOT generation function is missing: {ne}")
    except Exception as e:
        print(f"Error generating DOT file: {e}")
        return None 

    return dot_filename # Return the path to the generated file
