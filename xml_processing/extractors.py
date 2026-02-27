"""Text extraction from XML elements.

Key functions: extract_paraphrasis_text, retrieve_text_and_locus, retrieve_segment_text,
preload_document_sources, preload_text_segments
"""
from bootstrap.primary_imports import os, re, urllib
from bootstrap.delayed_imports import ET
from config.runtime_settings import BASE_DIR
from state.caches import text_segment_cache
from xml_processing.readers import get_or_parse_document
from xml_processing.locus import get_first_non_empty_locus, retrieve_locus
from xml_processing.selectors import find_common_ancestor


def extract_paraphrasis_text(paraphrasis_elem, default_text="/"):
    """
    Extract all text content from a paraphrasis element, including text within child elements.
    
    Args:
        paraphrasis_elem: An Element object that might be a paraphrasis element
        default_text: Text to return if paraphrasis_elem is None or contains no text
        
    Returns:
        str: The extracted text content, or default_text if no text is found
    """
    if paraphrasis_elem is None:
        return default_text
        
    # Function to recursively extract text from an element and all its descendants
    def get_all_text(element):
        text = element.text or ""
        for child in element:
            text += get_all_text(child)
            if child.tail:
                text += child.tail
        return text
    
    # Get all text content and normalize whitespace
    text_content = get_all_text(paraphrasis_elem).strip()
    if not text_content:
        return default_text
    
    # Normalize whitespace
    return re.sub(r'\s+', ' ', text_content)


def retrieve_segment_text(segment, namespaces):
    """Retrieve text from a segment element (from/to refs) and return (text, locus). Uses cache."""
    from_attr = segment.get('{http://alchemeast.eu/thesu/ns/1.0}from')
    to_attr = segment.get('{http://alchemeast.eu/thesu/ns/1.0}to')

    locus_start = ''
    
    if from_attr is None or from_attr == 'None' or "#" not in from_attr:
        return '', locus_start
    
    file_path, element_id = from_attr.split("#")
    
    # Check if this segment is already in our cache
    cache_key = (file_path, element_id, to_attr)
    if cache_key in text_segment_cache:
        return text_segment_cache[cache_key]
    
    # Fix file:/ URLs in file paths
    if file_path.startswith('file:/'):
        # Remove the file:/ prefix and decode URL encoding
        file_path = urllib.parse.unquote(file_path[6:])
        # For file:/ URLs that include a leading slash before a drive or root,
        # normalise by dropping the extra slash.
        if file_path.startswith('/'):
            file_path = file_path[1:]  # Remove leading slash
    
    # Try different paths to find the file
    possible_paths = [
        os.path.abspath(file_path),  # Absolute path as is
        os.path.join(BASE_DIR, file_path),  # Join with BASE_DIR
        os.path.join(os.path.dirname(BASE_DIR), file_path),  # Join with parent of BASE_DIR
        os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), file_path),  # Join with grandparent of BASE_DIR
        os.path.join(BASE_DIR, "sources-refactored", os.path.basename(file_path)),  # _thesu_inputs/sources-refactored
        os.path.join(BASE_DIR, "sources-segmented", os.path.basename(file_path)),  # _thesu_inputs/sources-segmented
        os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "_thesu_inputs", "sources-refactored", os.path.basename(file_path)),
        os.path.join("_thesu_inputs", "sources-refactored", os.path.basename(file_path)),
        os.path.join("_thesu_inputs", "sources-segmented", os.path.basename(file_path)),
    ]
    
    # Get the document from cache or parse it
    xml, full_file_path = get_or_parse_document(file_path, possible_paths)
    
    if xml is None:
        print(f"Warning: Could not open or parse file '{file_path}' in any of the tried locations")
        # Cache the empty result
        text_segment_cache[cache_key] = ('', locus_start)
        return '', locus_start
    
    try:
        # Try to find the element by xml:id
        from_elements = xml.xpath(f"//*[@xml:id='{element_id}']", namespaces=namespaces)
        
        # If not found, try with just id attribute
        if not from_elements:
            from_elements = xml.xpath(f"//*[@id='{element_id}']", namespaces=namespaces)
            
        # If still not found, try with thesu:id
        if not from_elements:
            from_elements = xml.xpath(f"//*[@thesu:id='{element_id}']", namespaces=namespaces)
        
        # If still not found, try with XHTML namespace
        if not from_elements:
            # Add XHTML namespace to the namespaces dictionary
            xhtml_namespaces = {**namespaces, 'xhtml': 'http://www.w3.org/1999/xhtml'}
            from_elements = xml.xpath(f"//xhtml:*[@id='{element_id}']", namespaces=xhtml_namespaces)
        
        if not from_elements:
            print(f"Warning: Could not find element with id '{element_id}' in file '{full_file_path}'")
            # Cache the empty result
            text_segment_cache[cache_key] = ('', locus_start)
            return '', locus_start
            
        from_element = from_elements[0]
        
        # Check if this is an XHTML document
        is_xhtml = False
        root = xml.getroot()
        if root.tag.endswith('html') or '{http://www.w3.org/1999/xhtml}' in root.tag:
            is_xhtml = True
            
        # Get the locus information
        locus_start = retrieve_locus(from_element, xml, namespaces)
        
        # CRITICAL FIX: Extract text properly considering both text and tail properties
        def extract_element_text(element):
            # Start with the element's text
            text_parts = []
            if element.text:
                text_parts.append(element.text)
            
            # Get text from processing instructions and element tails
            for child in element:
                # For processing instructions like oxy_custom_*
                if isinstance(child, ET._ProcessingInstruction):
                    # Check for oxy_custom_start
                    if 'oxy_custom_start' in child.target:
                        # Find the text that should be between oxy_custom_start and oxy_custom_end
                        for sibling in child.itersiblings():
                            if isinstance(sibling, ET._ProcessingInstruction) and 'oxy_custom_end' in sibling.target:
                                # Found the end tag, stop here
                                break
                            elif not isinstance(sibling, ET._ProcessingInstruction) and sibling.text:
                                # Regular element with text
                                text_parts.append(sibling.text)
                
                # Add tail text from any child element
                if child.tail:
                    text_parts.append(child.tail)
            
            # Combine all text parts
            return ''.join(text_parts).strip()
        
        # Get the first element's text
        first_element_text = extract_element_text(from_element)
        text = first_element_text
        
        # If there's a to_attr, get all text between from_element and to_element
        if to_attr is not None and to_attr != 'None':
            to_file_path, to_element_id = to_attr.split("#")
            
            # If from and to are in the same file
            if to_file_path == file_path or to_file_path.endswith(os.path.basename(file_path)):
                # Try to find the to_element
                to_elements = xml.xpath(f"//*[@xml:id='{to_element_id}']", namespaces=namespaces)
                
                # If not found, try with just id attribute
                if not to_elements:
                    to_elements = xml.xpath(f"//*[@id='{to_element_id}']", namespaces=namespaces)
                    
                # If still not found, try with thesu:id
                if not to_elements:
                    to_elements = xml.xpath(f"//*[@thesu:id='{to_element_id}']", namespaces=namespaces)
                
                # If still not found, try with XHTML namespace
                if not to_elements:
                    # Add XHTML namespace to the namespaces dictionary
                    xhtml_namespaces = {**namespaces, 'xhtml': 'http://www.w3.org/1999/xhtml'}
                    to_elements = xml.xpath(f"//xhtml:*[@id='{to_element_id}']", namespaces=xhtml_namespaces)
                
                if to_elements:
                    to_element = to_elements[0]
                    
                    # Special handling for XHTML documents
                    if is_xhtml:
                        # For XHTML, we need a different approach to get all elements between from and to
                        # First, find the common ancestor
                        common_ancestor = find_common_ancestor(from_element, to_element)
                        if common_ancestor is not None:
                            # Get all text-containing elements under the common ancestor
                            xhtml_namespaces = {**namespaces, 'xhtml': 'http://www.w3.org/1999/xhtml'}
                            all_text_elements = common_ancestor.xpath('.//xhtml:span[@class="w" or @class="pc" or @class="num" or @class="space"]', 
                                                                                namespaces=xhtml_namespaces)
                            
                            # Find the indices of our target elements
                            start_idx = -1
                            end_idx = -1
                            for i, elem in enumerate(all_text_elements):
                                if elem is from_element:
                                    start_idx = i
                                if elem is to_element:
                                    end_idx = i
                            
                            if start_idx >= 0 and end_idx >= 0:
                                # Get all elements between start and end (inclusive)
                                text_elements = all_text_elements[start_idx:end_idx+1]
                                
                                processed_text = ""
                                for i, elem in enumerate(text_elements):
                                    # Skip the first element as we already have its text
                                    if i == 0:
                                        continue
                                        
                                    # Extract text properly from each element
                                    elem_text = extract_element_text(elem)
                                    if elem_text:
                                        # Check if this is punctuation
                                        is_punctuation = (elem.get('class') == 'pc') or (elem_text.strip() in [',', '.', ';', ':', '!', '?', ')', ']', '}', '"', "'"])
                                        
                                        # No space before punctuation
                                        if is_punctuation:
                                            processed_text = processed_text.rstrip() + elem_text
                                        else:
                                            if processed_text and not processed_text.endswith(' '):
                                                processed_text += " "
                                            processed_text += elem_text
                                        
                                        # Add space after words and after punctuation (except certain characters)
                                        if elem.get('class') in ['w', 'num'] or (is_punctuation and elem_text.strip() not in ['(', '[', '{', '"', "'"]):
                                            processed_text += ' '
                                
                                # Combine the first element's text with the processed text
                                if processed_text:
                                    if first_element_text and not first_element_text.endswith(' '):
                                        text = first_element_text + ' ' + processed_text.strip()
                                    else:
                                        text = first_element_text + processed_text.strip()
                                else:
                                    text = first_element_text
                            else:
                                # Fallback: just use first element's text + to_element's text
                                to_element_text = extract_element_text(to_element)
                                text = first_element_text + " ... " + to_element_text
                        else:
                            # Fallback: just use first element's text + to_element's text
                            to_element_text = extract_element_text(to_element)
                            text = first_element_text + " ... " + to_element_text
                    else:
                        # Original approach for non-XHTML documents
                        # But we need to modify to use our text extraction function
                        seg_elements = xml.xpath('//span[@class="w" or @class="pc" or @class="num" or @class="space"] | //w | //pc | //num | //space | //tei:w | //tei:pc | //tei:num | //tei:space | //seg | //tei:seg | //xhtml:span[@class="w" or @class="pc" or @class="num" or @class="space"]', 
                                             namespaces={**namespaces, 'xhtml': 'http://www.w3.org/1999/xhtml'})
                        
                        try:
                            from_index = seg_elements.index(from_element)
                            to_index = seg_elements.index(to_element) if to_element in seg_elements else len(seg_elements)
                            
                            # Process elements between from_element and to_element
                            following_elements = seg_elements[from_index+1 : to_index+1]  # Skip the first element
                            
                            processed_text = ""
                            for elem in following_elements:
                                elem_text = extract_element_text(elem)
                                if elem_text:
                                    # Check if this is punctuation
                                    class_attr = elem.get('class') if hasattr(elem, 'get') else None
                                    is_punctuation = (class_attr == 'pc') or (elem_text.strip() in [',', '.', ';', ':', '!', '?', ')', ']', '}', '"', "'"])
                                    
                                    # No space before punctuation
                                    if is_punctuation:
                                        processed_text = processed_text.rstrip() + elem_text
                                    else:
                                        if processed_text and not processed_text.endswith(' '):
                                            processed_text += " "
                                        processed_text += elem_text
                                    
                                    # Add space after words/numbers and after punctuation
                                    if (class_attr in ['w', 'num']) or (is_punctuation and elem_text.strip() not in ['(', '[', '{', '"', "'"]):
                                        processed_text += ' '
                            
                            # Combine the first element's text with the processed text
                            if processed_text:
                                if first_element_text and not first_element_text.endswith(' '):
                                    text = first_element_text + ' ' + processed_text.strip()
                                else:
                                    text = first_element_text + processed_text.strip()
                            else:
                                text = first_element_text
                            
                        except ValueError:
                            # Fallback: just use first element's text + to_element's text
                            to_element_text = extract_element_text(to_element)
                            text = first_element_text + " ... " + to_element_text
                else:
                    # If to-element not found, just use first element's text
                    text = first_element_text
            else:
                # If from and to are in different files, just use the first element's text
                text = first_element_text
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix any remaining spacing issues with punctuation
        text = re.sub(r'\s+([,.;:!?)\]}])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([,.;:!?)\]}])', r'\1 ', text)     # Add space after punctuation
        text = re.sub(r'\s+$', '', text)                   # Remove trailing spaces
        text = re.sub(r'([(\[{])\s+', r'\1', text)         # Remove space after opening brackets
        text = re.sub(r'\s+(["\'])', r'\1', text)          # Remove space before quotes
        text = re.sub(r'(["\'])\s+', r'\1', text)          # Remove space after quotes at the beginning of words
        text = re.sub(r'\s\s+', ' ', text)                 # Remove multiple spaces
        
        # Cache the result before returning
        text_segment_cache[cache_key] = (text, locus_start)
        return text, locus_start
    except Exception as e:
        print(f"Error retrieving segment text: {e}")
        # Cache the empty result
        text_segment_cache[cache_key] = ('', locus_start)
        return '', locus_start


def retrieve_text_and_locus(text_elements, namespaces):
    """Aggregate text and locus from multiple segment elements. Returns (snippet, full_text, locus)."""
    # Get all text segments and their loci
    retrieved_texts_and_loci = [retrieve_segment_text(text_element, namespaces) for text_element in text_elements]
    
    # Extract all text segments
    all_texts = [text for text, locus in retrieved_texts_and_loci if text]
    
    # Join all texts into a single string
    if len(all_texts) > 1:
        retrieved_text = ' ... '.join(all_texts)
    else:
        retrieved_text = ''.join(all_texts)
    
    # Clean up the text
    retrieved_text = re.sub(r'\s+', ' ', retrieved_text).strip()
    
    # Create a snippet version
    retrieved_text_snippet = retrieved_text
    
    # For snippet creation, we need to preserve original ellipses
    # First, tokenize the text into words and ellipses
    tokens = re.findall(r'\.{3}|…|\S+', retrieved_text_snippet)
    
    # Identify which tokens are actual words (not ellipses)
    actual_words = [(i, token) for i, token in enumerate(tokens) if token not in ['...', '…']]
    
    # If we have more than 5 actual words, create a shortened version for snippet
    if len(actual_words) > 5:
        # Get indices of the first 3 and last 2 actual words
        first_three_indices = [i for i, _ in actual_words[:3]]
        last_two_indices = [i for i, _ in actual_words[-2:]]
        
        # Get all tokens between the first and last groups, including any ellipses
        middle_tokens = []
        
        # Check if there's a gap that needs an ellipsis
        if first_three_indices[-1] + 1 < last_two_indices[0]:
            # Add our own ellipsis to mark the truncation
            middle_tokens = ["..."]
        
        # Reconstruct the snippet with original ellipses preserved
        first_part = tokens[:first_three_indices[-1] + 1]
        last_part = tokens[last_two_indices[0]:]
        
        retrieved_text_snippet = ' '.join(first_part) + " " + ' '.join(middle_tokens) + " " + ' '.join(last_part)
        retrieved_text_snippet = retrieved_text_snippet.strip()
        
        # Clean up only duplicate ellipses created by our truncation
        retrieved_text_snippet = re.sub(r'\s+\.{3}\s+\.{3}\s+', ' ... ', retrieved_text_snippet)
    
    # Remove any extra spaces that might have been introduced
    retrieved_text_snippet = re.sub(r'\s+', ' ', retrieved_text_snippet).strip()
    
    # Trim the retrieved_text if it's longer than 100 words
    full_words = [w for w in retrieved_text.split() if w not in ['...', '…']]
    if len(full_words) > 100:
        if len(all_texts) > 1:
            # For discontinuous text with multiple segments, preserve the start and end of each segment
            trimmed_segments = []
            remaining_words = 100
            segments_to_process = len(all_texts)
            
            # Calculate words to allocate per segment (minimum 5 words per segment)
            min_words_per_segment = 5
            base_words_per_segment = max(min_words_per_segment, remaining_words // segments_to_process)
            
            for segment in all_texts:
                segment_words = [w for w in segment.split() if w not in ['...', '…']]
                segment_length = len(segment_words)
                
                if segment_length <= base_words_per_segment or remaining_words <= base_words_per_segment:
                    # If segment is short enough or we're running out of words, keep it all
                    trimmed_segments.append(segment)
                    remaining_words -= segment_length
                else:
                    # Always keep at least first 3 and last 2 words of each segment
                    words_to_keep = min(base_words_per_segment, remaining_words)
                    
                    # Ensure we keep at least 3 words from start and 2 from end if possible
                    words_from_start = min(3, segment_length // 2)
                    words_from_end = min(2, segment_length - words_from_start)
                    
                    # If we have more words to keep, distribute between middle
                    middle_words = words_to_keep - words_from_start - words_from_end
                    
                    if middle_words > 0:
                        trimmed_segment = ' '.join(segment_words[:words_from_start]) + ' ... ' + ' '.join(segment_words[-words_from_end:])
                    else:
                        # Not enough room for ellipsis, just take from start and end
                        trimmed_segment = ' '.join(segment_words[:words_from_start]) + ' ' + ' '.join(segment_words[-words_from_end:])
                    
                    trimmed_segments.append(trimmed_segment)
                    remaining_words -= (words_from_start + words_from_end + (1 if middle_words > 0 else 0))  # Count ellipsis as one word
                
                segments_to_process -= 1
                
                # If we've used all our word allocation, stop processing segments
                if remaining_words <= 0:
                    break
            
            # Join the trimmed segments
            retrieved_text = ' ... '.join(trimmed_segments)
        else:
            # For a single continuous text, keep first 50 and last 50 words if possible
            first_part = ' '.join(full_words[:50])
            last_part = ' '.join(full_words[-50:])
            retrieved_text = first_part + " ... " + last_part
    
    # Get the first non-empty locus
    locus_start = get_first_non_empty_locus(retrieved_texts_and_loci)
    locus = locus_start
    
    return retrieved_text_snippet, retrieved_text, locus


def preload_document_sources(xml_root, namespaces):
    """Preload all source documents and text segments referenced in the XML into caches."""
    # Collect all the source elements
    source_elements = xml_root.findall('.//thesu:source', namespaces=namespaces)
    
    # Track source documents specifically for accurate counting
    source_docs_loaded = 0
    
    # Process each source element to preload the document
    for source_element in source_elements:
        source_path = source_element.get('{http://alchemeast.eu/thesu/ns/1.0}ref')
        
        if not source_path:
            continue
            
        # Fix file:/ URLs in source paths
        if source_path.startswith('file:/'):
            # Remove the file:/ prefix and decode URL encoding
            source_path = urllib.parse.unquote(source_path[6:])
            # For Windows paths, ensure they're absolute
            if source_path.startswith('/'):
                source_path = source_path[1:]  # Remove leading slash for Windows absolute paths
        
        # Try multiple possible paths for the source file
        possible_paths = [
            os.path.abspath(source_path),  # Absolute path as is
            os.path.join(BASE_DIR, source_path),  # Join with BASE_DIR
            os.path.join(os.path.dirname(BASE_DIR), source_path),  # Join with parent of BASE_DIR
            os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), source_path),  # Join with grandparent of BASE_DIR
            os.path.join(BASE_DIR, "sources-refactored", os.path.basename(source_path)),  # _thesu_inputs/sources-refactored
            os.path.join(BASE_DIR, "sources-segmented", os.path.basename(source_path)),  # _thesu_inputs/sources-segmented
            os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "_thesu_inputs", "sources-refactored", os.path.basename(source_path)),
            os.path.join("_thesu_inputs", "sources-refactored", os.path.basename(source_path)),
            os.path.join("_thesu_inputs", "sources-segmented", os.path.basename(source_path)),
        ]
        
        # Try to preload the document
        xml, full_path = get_or_parse_document(source_path, possible_paths)
        if full_path:
            source_docs_loaded += 1
    
    # Also preload all text references to build the text segment cache
    preload_text_segments(xml_root, namespaces)
    
    print(f"Preloading complete. {source_docs_loaded} documents cached.")


def preload_text_segments(xml_root, namespaces):
    """Preload all text segments referenced in the XML into the text segment cache."""
    # Find all text segment references in the document
    text_refs = []
    
    # All elements with text references
    elements_with_text = xml_root.findall('.//thesu:text/thesu:textRef/thesu:segment', namespaces=namespaces)
    for segment in elements_with_text:
        text_refs.append(segment)
    
    # Process each segment to cache its text
    for segment in text_refs:
        retrieve_segment_text(segment, namespaces)
