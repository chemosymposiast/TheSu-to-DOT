"""
Post-processing filter for elements_to_exclude.

Removes node definitions for excluded elements from the DOT file.
This runs after the full DOT is generated, so that redirect_or_remove_invalid_edges
can then substitute edges to those nodes with filtered pseudo-nodes.
"""
from bootstrap.primary_imports import re


def remove_excluded_node_definitions(dot_filename, elements_to_exclude):
    """
    Remove node definition lines for excluded element IDs from the DOT file.

    Only removes lines that define nodes (not edges). Edges referencing excluded
    nodes remain; redirect_or_remove_invalid_edges will substitute them with
    filtered pseudo-nodes.

    Only runs when elements_to_exclude is non-empty.
    """
    if not elements_to_exclude:
        return

    exclude_set = set(str(x).strip() for x in elements_to_exclude if x)
    if not exclude_set:
        return

    with open(dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Same node pattern as edge_validation.py
    node_def_pattern = re.compile(r'^\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$')

    removed_count = 0
    output_lines = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith(('//', '#')):
            output_lines.append(line)
            continue
        if line_stripped.startswith(('digraph', 'graph', 'subgraph', '{', '}')):
            output_lines.append(line)
            continue
        if '->' in line_stripped:
            output_lines.append(line)
            continue

        node_match = node_def_pattern.match(line_stripped)
        if node_match and '->' not in line_stripped:
            node_id = node_match.group(1)
            if node_id in exclude_set:
                removed_count += 1
                continue  # Skip this line (remove the node definition)

        output_lines.append(line)

    if removed_count > 0:
        print(f"--- Elements-to-Exclude (post-process): Removed {removed_count} node definition(s) ---")
        with open(dot_filename, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)
