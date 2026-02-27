"""
DOT file post-processing and cleanup functions.

This module re-exports cleanup functions from specialized modules for convenience.
Individual functions are organized into:
- id_cleanup: ID replacement and cleanup
- reorganization: DOT file reorganization by source
- edge_validation: Edge validation and redirection
- excluded_filter: Remove excluded element node definitions (post-process)
- deduplication: Duplicate definition removal
- normalization: Line break normalization
- arrow_fixup: Arrow direction correction based on node positions
- tuple_fixup: Tuple-like node ID correction
"""
# Re-export functions from specialized modules
from .id_cleanup import replace_original_xml_ids
from .reorganization import reorganize_dot_file
from .edge_validation import redirect_or_remove_invalid_edges
from .excluded_filter import remove_excluded_node_definitions
from .filtered_pruning import prune_and_connect_filtered_nodes
from .deduplication import remove_duplicate_definitions
from .normalization import normalize_dot_file_line_breaks, collapse_excess_blank_lines
from .arrow_fixup import fix_arrow_directions
from .tuple_fixup import detect_and_fix_tuple_node_ids, fix_tuple_node_ids

__all__ = [
    'replace_original_xml_ids',
    'reorganize_dot_file',
    'redirect_or_remove_invalid_edges',
    'remove_excluded_node_definitions',
    'prune_and_connect_filtered_nodes',
    'remove_duplicate_definitions',
    'normalize_dot_file_line_breaks',
    'collapse_excess_blank_lines',
    'fix_arrow_directions',
    'detect_and_fix_tuple_node_ids',
    'fix_tuple_node_ids',
]
