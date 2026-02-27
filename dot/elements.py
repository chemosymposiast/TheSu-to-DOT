"""Element processing for DOT building.

Coordinates the overall DOT building process and delegates to element-specific
modules (thesis, support, misc).

Key functions: initialize_elements_clusters, process_filtered_elements
"""
from bootstrap.primary_imports import os, urllib
from bootstrap.delayed_imports import ET
from config.runtime_settings import BASE_DIR
from xml_processing import retrieve_text_and_locus
from dot.propositions import process_referenced_propositions
from dot.thesis import process_thesis_element
from dot.support import process_support_element
from dot.misc import process_misc_element

def initialize_elements_clusters(xml_root, filtered_elements, namespaces, all_propositions, dot_file):
    """Process all source elements and referenced propositions, building DOT clusters and nodes."""
    written_lines = []
    stored_edges = []
    written_prop_phases = {}
    processed_elements = set()
    processed_propositions = set()
    
    # Process source elements
    source_elements = xml_root.findall('.//thesu:source', namespaces=namespaces)
    processed_sources = set()

    for source_element in source_elements:
        source_id = source_element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
        if source_id is None:
            source_id = source_element.get('{http://www.w3.org/XML/1998/namespace}id')
        source_path = source_element.get('{http://alchemeast.eu/thesu/ns/1.0}ref')
        
        if source_id in processed_sources:
            print(f"Warning: Skipping duplicate source with ID {source_id}")
            continue
            
        processed_sources.add(source_id)
        
        # Fix file:/ URLs in source paths
        if source_path.startswith('file:/'):
            # Remove the file:/ prefix and decode URL encoding
            source_path = urllib.parse.unquote(source_path[6:])
            # For file:/ URLs that include a leading slash before a drive or root,
            # normalise by dropping the extra slash.
            if source_path.startswith('/'):
                source_path = source_path[1:]  # Remove leading slash
        
        # Try multiple possible paths for the source file
        possible_paths = [
            os.path.abspath(source_path),  # Absolute path as is
            os.path.join(BASE_DIR, source_path),  # Join with BASE_DIR
            os.path.join(os.path.dirname(BASE_DIR), source_path),  # Join with parent of BASE_DIR
            os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), source_path),  # Join with grandparent of BASE_DIR
            os.path.join(BASE_DIR, "sources-refactored", os.path.basename(source_path)),  # Tests_1/sources-refactored
            os.path.join(BASE_DIR, "sources-segmented", os.path.basename(source_path)),  # Tests_1/sources-segmented
            os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "Tests_1", "sources-refactored", os.path.basename(source_path)),
            os.path.join("Tests_1", "sources-refactored", os.path.basename(source_path)),
            os.path.join("Tests_1", "sources-segmented", os.path.basename(source_path)),
        ]
        
        source_xml = None

        # Try each possible path
        for path in possible_paths:
            try:
                tree = ET.parse(path)
                source_xml = tree.getroot()
                break
            except (OSError, ET.ParseError):
                continue
        
        if source_xml is None:
            print(f"Warning: Could not parse source file '{source_path}' in any of the tried locations")
            print(f"Attempting to process the source element directly without loading the external file.")
            
            subgraph_id = f"source_{source_id.replace('.', '_').replace('-', '_')}"
            dot_file.write(f'subgraph {subgraph_id} {{\n')
            dot_file.write(f'label="{source_id}";\n\n')
            
            # Pass source_id to process_filtered_elements
            written_lines, stored_edges, processed_propositions = process_filtered_elements(
                source_element, filtered_elements, namespaces, all_propositions, 
                dot_file, written_lines, stored_edges, written_prop_phases, 
                processed_elements, processed_propositions, source_id  # Add source_id here
            )
            
            dot_file.write('}\n\n')
            continue

        subgraph_id = f"source_{source_id.replace('.', '_').replace('-', '_')}"
        dot_file.write(f'subgraph {subgraph_id} {{\n')
        dot_file.write(f'label="{source_id}";\n\n')
        
        # Pass source_id to process_filtered_elements
        written_lines, stored_edges, processed_propositions = process_filtered_elements(
            source_xml, filtered_elements, namespaces, all_propositions, 
            dot_file, written_lines, stored_edges, written_prop_phases, 
            processed_elements, processed_propositions, source_id  # Add source_id here
        )
        
        dot_file.write('}\n\n')
    
    # Process elements outside of any source with None as source_id
    written_lines, stored_edges, processed_propositions = process_filtered_elements(
        xml_root, filtered_elements, namespaces, all_propositions, 
        dot_file, written_lines, stored_edges, written_prop_phases, 
        processed_elements, processed_propositions, None
    )
    
    # Process referenced propositions
    written_lines, written_prop_phases, processed_propositions = process_referenced_propositions(
        filtered_elements, namespaces, all_propositions, dot_file, written_lines, 
        written_prop_phases, processed_propositions
    )
    
    return written_lines, stored_edges, written_prop_phases, processed_elements, processed_propositions

def process_filtered_elements(source_xml, filtered_elements, namespaces, all_propositions, dot_file, written_lines, stored_edges, written_prop_phases, processed_elements, processed_propositions, source_id=None):
    """Dispatch THESIS, SUPPORT, and MISC elements to their respective processors."""
    # If source_xml is a source element, get its children
    if source_xml.tag == '{http://alchemeast.eu/thesu/ns/1.0}source':
        elements_to_process = source_xml.findall('.//*')
        # Get source ID from the source element
        parent_source_id = source_xml.get('{http://alchemeast.eu/thesu/ns/1.0}id')
        if parent_source_id is None:
            parent_source_id = source_xml.get('{http://www.w3.org/XML/1998/namespace}id')
    else:
        # Otherwise, use the filtered_elements list
        elements_to_process = filtered_elements
        parent_source_id = source_id
    
    for element in elements_to_process:
        # Skip elements that aren't THESIS, SUPPORT, or MISC
        if element.tag not in [
            '{http://alchemeast.eu/thesu/ns/1.0}THESIS', 
            '{http://alchemeast.eu/thesu/ns/1.0}SUPPORT', 
            '{http://alchemeast.eu/thesu/ns/1.0}MISC'
        ]:
            continue
            
        # Get the element ID
        element_id = element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
        if element_id is None:
            element_id = element.get('{http://www.w3.org/XML/1998/namespace}id')
        
        # Skip if this element has already been processed
        if element_id in processed_elements:
            continue
            
        # Always check for the most specific source by looking at ancestors
        element_source_id = None
        source_ancestors = element.xpath('ancestor::thesu:source', namespaces=namespaces)
        if source_ancestors:
            # Get the closest source ancestor
            source_element = source_ancestors[0]
            element_source_id = source_element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
            if element_source_id is None:
                element_source_id = source_element.get('{http://www.w3.org/XML/1998/namespace}id')
        
        # Use the most specific source ID available (element-specific, then parent, then passed-in)
        actual_source_id = element_source_id or parent_source_id or source_id
        
        # Add to processed elements set
        processed_elements.add(element_id)
                    
        text_elements = element.xpath('.//thesu:text/thesu:textRef/thesu:segment', namespaces=namespaces)
        retrieved_text_snippet, retrieved_text, locus = retrieve_text_and_locus(text_elements, namespaces)
        
        if element.tag == '{http://alchemeast.eu/thesu/ns/1.0}THESIS':
            element_type = "THESIS"
            written_lines, processed_propositions = process_thesis_element(element, element_type, namespaces, all_propositions, dot_file, written_lines, stored_edges, written_prop_phases, retrieved_text, retrieved_text_snippet, locus, processed_propositions, actual_source_id)
        elif element.tag == '{http://alchemeast.eu/thesu/ns/1.0}SUPPORT':
            element_type = "SUPPORT"
            written_lines, processed_propositions = process_support_element(element, element_type, namespaces, dot_file, written_lines, retrieved_text, retrieved_text_snippet, locus, processed_propositions, actual_source_id)
        elif element.tag == '{http://alchemeast.eu/thesu/ns/1.0}MISC':
            element_type = "MISC"
            written_lines, processed_propositions = process_misc_element(element, element_type, namespaces, dot_file, written_lines, written_prop_phases, retrieved_text, retrieved_text_snippet, locus, processed_propositions, actual_source_id)
    
    return written_lines, stored_edges, processed_propositions
