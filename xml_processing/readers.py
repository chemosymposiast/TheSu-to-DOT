"""Document loading and parsing for XML files.

Key functions: get_or_parse_document, parse_included_files
"""
from bootstrap.primary_imports import os
from bootstrap.delayed_imports import ET
from config.runtime_settings import BASE_DIR
from state.caches import document_cache


def get_or_parse_document(file_path, possible_paths=None):
    """
    Get a parsed XML document from cache or parse it if not cached.
    Tries multiple possible paths if specified.
    
    Args:
        file_path: Primary path to the file
        possible_paths: List of alternative paths to try if primary path fails
        
    Returns:
        tuple: (parsed_document, full_file_path) or (None, None) if not found
    """
    # First check if the exact path is in our cache
    if file_path in document_cache:
        return document_cache[file_path], file_path
    
    # If no possible paths provided, use just the file_path
    if possible_paths is None:
        possible_paths = [file_path]
    else:
        # Ensure the primary path is first in the list
        if file_path not in possible_paths:
            possible_paths = [file_path] + possible_paths
    
    # Try each possible path
    for path in possible_paths:
        # Check if this path is already in our cache
        if path in document_cache:
            return document_cache[path], path
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                xml = ET.parse(file)
                document_cache[path] = xml  # Cache the parsed document
                return xml, path
        except (OSError, ET.ParseError):
            continue
    
    return None, None


def parse_included_files(included_files, namespaces):
    """Parse xi:include elements and collect all PROPOSITION elements into a dict keyed by id."""
    all_propositions = {}
    for included_file in included_files:
        # Use os.path.join to combine BASE_DIR with the href attribute
        included_filepath = os.path.join(BASE_DIR, included_file.get('href'))
        
        # Use document cache if available
        if included_filepath in document_cache:
            included_tree = document_cache[included_filepath]
            included_root = included_tree.getroot()
        else:
            included_tree = ET.parse(included_filepath)
            included_root = included_tree.getroot()
            # Cache the parsed document
            document_cache[included_filepath] = included_tree

        # Differentiate based on filename
        if "included-propositions" in included_filepath or "new-propositions" in included_filepath:
            propositions = included_root.findall('.//thesu:PROPOSITION', namespaces=namespaces)
            for proposition in propositions:
                prop_id = proposition.get('{http://alchemeast.eu/thesu/ns/1.0}id')
                if prop_id is None:
                    prop_id = proposition.get('{http://www.w3.org/XML/1998/namespace}id')
                all_propositions[prop_id] = proposition
    return all_propositions
