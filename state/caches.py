"""Runtime caches for parsed documents and text segments.

Key globals: document_cache, text_segment_cache
"""
# Document cache to avoid repeatedly parsing the same files
# Keys: file paths, Values: parsed ET documents
document_cache = {}

# Source text lookup cache
# Keys: (file_path, element_id), Values: (text, locus)
text_segment_cache = {}
