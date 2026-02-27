"""XML processing: document loading and text extraction.

Readers: get_or_parse_document, parse_included_files
Extractors: extract_paraphrasis_text, retrieve_text_and_locus, retrieve_segment_text,
preload_document_sources, preload_text_segments
Selectors: find_parent_thesis, get_all_proposition_ids, filter_elements, find_common_ancestor
Locus: get_first_non_empty_locus, check_for_standardized_page_id, retrieve_locus
"""
from .readers import get_or_parse_document, parse_included_files
from .extractors import (
    extract_paraphrasis_text,
    retrieve_text_and_locus,
    retrieve_segment_text,
    preload_document_sources,
    preload_text_segments,
)

__all__ = [
    'get_or_parse_document',
    'parse_included_files',
    'extract_paraphrasis_text',
    'retrieve_text_and_locus',
    'retrieve_segment_text',
    'preload_document_sources',
    'preload_text_segments',
]
