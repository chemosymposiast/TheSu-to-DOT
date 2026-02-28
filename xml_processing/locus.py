"""Locus extraction and page ID handling for XML elements.

Key functions: get_first_non_empty_locus, check_for_standardized_page_id, retrieve_locus
"""
from bootstrap.primary_imports import re


def get_first_non_empty_locus(retrieved_texts_and_loci):
    """Return the first non-empty locus from a list of (text, locus) tuples, or empty string if none."""
    for _, locus in retrieved_texts_and_loci:
        if locus:
            return locus
    return ""

def check_for_standardized_page_id(element, namespaces):
    """
    Check for standardized page IDs in the element's ancestors.
    
    This function looks for ancestor div elements with standardized page IDs
    in the format 'page_X' which are used in both OCR and Poppler formats
    after processing.
    
    Args:
        element: The XML element to check
        xml: The XML document
        namespaces: Namespace mappings
        
    Returns:
        The page number as a string, or None if not found
    """
    try:
        # Try with different namespace combinations
        ancestor_divs = []
        
        # Try with no namespace
        try:
            ancestor_divs = element.xpath('ancestor::div', namespaces=namespaces)
        except Exception:
            pass
            
        # Try with HTML namespace
        try:
            ancestor_divs_html = element.xpath('ancestor::html:div', namespaces={'html': 'http://www.w3.org/1999/xhtml'})
            ancestor_divs.extend(ancestor_divs_html)
        except Exception:
            pass
            
        # Try with explicit XHTML namespace
        try:
            ancestor_divs_xhtml = element.xpath('ancestor::*[local-name()="div"]')
            ancestor_divs.extend(ancestor_divs_xhtml)
        except Exception:
            pass
        
        # Check for standardized page IDs (page_X format)
        page_divs = element.xpath('ancestor::*[local-name()="div" and starts-with(@id, "page_")]', namespaces=namespaces)
        if page_divs:
            page_id = page_divs[0].get('id').replace('page_', '')
            return page_id
            
        # Check for Poppler format divs with id="pageX" (common in Poppler HTML)
        poppler_divs = element.xpath('ancestor::*[local-name()="div" and starts-with(@id, "page")]', namespaces=namespaces)
        if poppler_divs:
            for div in poppler_divs:
                page_id = div.get('id')
                if page_id and page_id.startswith('page') and not page_id.endswith('-div'):
                    # Extract the page number from "pageX"
                    page_num = page_id.replace('page', '')
                    return page_num
        
        # Check for Poppler format divs with id="pageX-div" (common in Poppler HTML)
        poppler_div_divs = element.xpath('ancestor::*[local-name()="div" and contains(@id, "-div")]', namespaces=namespaces)
        if poppler_div_divs:
            for div in poppler_div_divs:
                page_id = div.get('id')
                if page_id and page_id.startswith('page') and page_id.endswith('-div'):
                    # Extract the page number from "pageX-div"
                    page_num = page_id.replace('page', '').replace('-div', '')
                    return page_num
            
        # Check for OCR format divs
        ocr_divs = element.xpath('ancestor::*[local-name()="div" and @class="ocr_page"]', namespaces=namespaces)
        if ocr_divs:
            ocr_div = ocr_divs[0]
            # Check if it has an ocr_page attribute (which would contain the mapped page number)
            if ocr_div.get('ocr_page'):
                page_num = ocr_div.get('ocr_page').replace('page_', '')
                return page_num
            # Otherwise use the original id
            elif ocr_div.get('id'):
                page_num = ocr_div.get('id').replace('page_', '')
                return page_num
                
        # Check for Poppler format divs with class="pdf-page"
        pdf_divs = element.xpath('ancestor::*[local-name()="div" and (@class="pdf-page" or @class="page" or contains(@class, "page"))]', namespaces=namespaces)
        if pdf_divs:
            pdf_div = pdf_divs[0]
            # Check if it has a pdf_page attribute (which would contain the mapped page number)
            if pdf_div.get('pdf_page'):
                page_num = pdf_div.get('pdf_page').replace('page_', '')
                return page_num
            # Otherwise use the original id
            elif pdf_div.get('id'):
                if pdf_div.get('id').startswith('page'):
                    page_num = pdf_div.get('id').replace('page', '')
                    return page_num
                
        # Additional check for any div with data-page-number attribute (common in Poppler HTML)
        page_number_divs = element.xpath('ancestor::*[local-name()="div" and @data-page-number]', namespaces=namespaces)
        if page_number_divs:
            page_num = page_number_divs[0].get('data-page-number')
            return page_num
        
        return None
    except Exception as e:
        print(f"Warning: Error checking for standardized page ID: {e}")
        return None

def retrieve_locus(element, xml, namespaces):
    """Extract locus (page/section reference) for an element from TEI or HTML/XHTML documents."""
    # Check if this is a TEI document or an HTML/XHTML document
    is_tei_document = False
    
    # Check if the root element is in the TEI namespace or has a TEI-related tag
    root = xml.getroot()
    if root.tag.startswith('{http://www.tei-c.org/ns/1.0}') or 'TEI' in root.tag:
        is_tei_document = True
    
    # For HTML/XHTML documents, use page ID approach
    if not is_tei_document:
        # First check for standardized page IDs from OCR/Poppler
        page_id = check_for_standardized_page_id(element, namespaces)
        if page_id:
            return f'p. {page_id}'
    
    # For TEI documents or if no page ID was found, use TEI-specific approach
    # Check for milestone elements
    preceding_milestone = element.xpath('preceding::milestone[not(@unit="tlnum")][1] | preceding::tei:milestone[not(@unit="tlnum")][1]', namespaces=namespaces)
    if preceding_milestone:
        preceding_milestone = preceding_milestone[0]
        attrs_with_numbers = [(k,v) for k,v in preceding_milestone.items() if re.search(r'\d', v)]
        if attrs_with_numbers:
            attrs_with_numbers.sort(key=lambda x: len(re.findall(r'\d', x[1]))/len(x[1]), reverse=True)
            return attrs_with_numbers[0][1]
    
    # Check for div elements
    div_parents = element.xpath('ancestor::div | ancestor::tei:div | ancestor::div1 | ancestor::tei:div1 | ancestor::div2 | ancestor::tei:div2 | ancestor::div3 | ancestor::tei:div3', namespaces=namespaces)
    if div_parents:
        div_parents = div_parents[1:]
        locus_parts = []
        for div in div_parents:
            attrs_with_numbers = [(k,v) for k,v in div.items() if re.search(r'\d', v)]
            if attrs_with_numbers:
                attrs_with_numbers.sort(key=lambda x: len(re.findall(r'\d', x[1]))/len(x[1]), reverse=True)
                locus_parts.append(attrs_with_numbers[0][1])
            else:
                index = div.getparent().index(div) + 1
                locus_parts.append(str(index))
        return f"{'.'.join(locus_parts)} (of <i>div</i>)"
    
    # Check for pb (page break) elements
    preceding_pb = element.xpath('preceding::pb[1] | preceding::tei:pb[1]', namespaces=namespaces)
    if preceding_pb:
        preceding_pb = preceding_pb[0]
        locus_start = preceding_pb.get('n')
        if locus_start:
            return f'p. {locus_start}'
    
    # Check for p elements
    p_parents = element.xpath('ancestor::p | ancestor::tei:p', namespaces=namespaces)
    if p_parents:
        locus_parts = []
        for p in p_parents:
            attrs_with_numbers = [(k,v) for k,v in p.items() if re.search(r'\d', v)]
            if attrs_with_numbers:
                attrs_with_numbers.sort(key=lambda x: len(re.findall(r'\d', x[1]))/len(x[1]), reverse=True)
                locus_parts.append(attrs_with_numbers[0][1])
            else:
                index = p.getparent().index(p) + 1
                locus_parts.append(str(index))
        return f"{'.'.join(locus_parts)} (of <i>p</i>)"
    
    # If we still haven't found a locus and this is not a TEI document, 
    # try the page ID approach as a fallback
    if not is_tei_document and not page_id:
        page_id = check_for_standardized_page_id(element, namespaces)
        if page_id:
            return f'p. {page_id}'
    
    return ''
