"""
Post-processing for filtered pseudo-nodes.

Phase 1: Prune filtered nodes not connected (through mediators) to any unfiltered node.
         Then iteratively remove dangling mediator nodes.
Phase 2: Add dashed edges between kept filtered nodes that were indirectly connected
         through chains of other filtered nodes, with xlabel showing chain length.
"""
from bootstrap.primary_imports import re
from collections import deque
from .normalization import collapse_excess_blank_lines


def is_mediator_node(node_id):
    """Return True if node_id is a mediator pseudo-node (func, employed, entailment, etc.)."""
    if node_id.endswith('_func') or node_id.endswith('_employed'):
        return True
    if '_to_' in node_id:
        return True
    if '_in_etiology_in_' in node_id:
        return True
    if '_analogy_to_' in node_id:
        return True
    if '_referenced-in_' in node_id:
        return True
    return False


def _parse_dot_graph(lines):
    """Parse DOT lines into defined nodes, edges, and adjacency.

    Returns (defined_nodes: set, edges: list[(src,tgt,line_idx)], adjacency: dict)
    """
    node_def_pattern = re.compile(r'^\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$')
    edge_def_pattern = re.compile(r'^\s*"([^"]+)"\s*->\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$')

    defined_nodes = set()
    edges = []
    adjacency = {}  # undirected: node -> set of neighbours

    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith(('//','#','digraph','graph','subgraph','{','}')):
            continue
        if '=' in s and '->' not in s and not s.startswith('"'):
            continue

        edge_m = edge_def_pattern.match(s)
        if edge_m:
            src, tgt = edge_m.group(1), edge_m.group(2)
            edges.append((src, tgt, i))
            adjacency.setdefault(src, set()).add(tgt)
            adjacency.setdefault(tgt, set()).add(src)
            continue

        node_m = node_def_pattern.match(s)
        if node_m and '->' not in s:
            defined_nodes.add(node_m.group(1))

    return defined_nodes, edges, adjacency


def prune_and_connect_filtered_nodes(dot_filename, elements_to_exclude):
    """Phase 1+2 combined: prune filtered nodes without a direct unfiltered
    connection, remove dangling mediators, then add dashed edges between kept
    filtered nodes that were indirectly connected through chains of other
    (now-removed) filtered nodes.

    Direct connection = path from filtered node to an unfiltered node through
    mediators only (other filtered nodes do not count as a bridge).

    Indirect connection = two kept filtered nodes that were in the same
    connected component of the full pre-pruning filtered+mediator subgraph.
    """
    if not elements_to_exclude:
        return

    with open(dot_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    defined_nodes, edges, adjacency = _parse_dot_graph(lines)

    # --- Classify nodes ---
    filtered_nodes = {n for n in defined_nodes if n.endswith('_filtered')}
    mediator_nodes = {n for n in defined_nodes if is_mediator_node(n)}
    unfiltered_nodes = defined_nodes - filtered_nodes - mediator_nodes

    if not filtered_nodes:
        return

    # --- Phase 1a: determine which filtered nodes to keep ---
    keep_filtered = set()
    for f_node in filtered_nodes:
        visited = {f_node}
        queue = deque([f_node])
        found_unfiltered = False
        while queue and not found_unfiltered:
            curr = queue.popleft()
            for nb in adjacency.get(curr, []):
                if nb in visited:
                    continue
                visited.add(nb)
                if nb in unfiltered_nodes:
                    found_unfiltered = True
                    break
                if nb in mediator_nodes:
                    queue.append(nb)
        if found_unfiltered:
            keep_filtered.add(f_node)

    to_remove = filtered_nodes - keep_filtered

    # --- Phase 2: find indirect connections + chain lengths BEFORE pruning ---
    # (src, dst, pruned_count) tuples — src->dst follows original edge direction
    indirect_edges = []
    if len(keep_filtered) >= 2:
        restricted = filtered_nodes | mediator_nodes
        r_adj = {}
        directed_pairs = set()
        for src, tgt, _ in edges:
            if src in restricted and tgt in restricted:
                r_adj.setdefault(src, set()).add(tgt)
                r_adj.setdefault(tgt, set()).add(src)
                directed_pairs.add((src, tgt))

        # Find connected components among ALL filtered + mediator nodes
        comp_visited = set()
        components_kept = []
        for start in filtered_nodes:
            if start in comp_visited:
                continue
            comp_filtered = set()
            q = deque([start])
            comp_visited.add(start)
            while q:
                node = q.popleft()
                if node in filtered_nodes:
                    comp_filtered.add(node)
                for nb in r_adj.get(node, []):
                    if nb not in comp_visited:
                        comp_visited.add(nb)
                        q.append(nb)
            kept_in_comp = comp_filtered & keep_filtered
            if len(kept_in_comp) >= 2:
                components_kept.append((kept_in_comp, comp_filtered, r_adj))

        # For each component, BFS spanning tree over kept filtered nodes.
        # Count pruned filtered nodes on the path between each pair.
        # Track forward/backward hops to preserve original edge direction.
        for kept_set, all_filtered_in_comp, adj_map in components_kept:
            tree_visited = set()
            root = next(iter(kept_set))
            tree_visited.add(root)
            tree_queue = deque([root])

            while tree_queue:
                f_node = tree_queue.popleft()
                inner_visited = {f_node}
                # queue entries: (current_node, pruned_count, fwd_hops, bwd_hops)
                inner_queue = deque([(f_node, 0, 0, 0)])
                while inner_queue:
                    curr, pruned_count, fwd, bwd = inner_queue.popleft()
                    for neighbour in adj_map.get(curr, []):
                        if neighbour in inner_visited:
                            continue
                        inner_visited.add(neighbour)
                        is_fwd = (curr, neighbour) in directed_pairs
                        new_fwd = fwd + (1 if is_fwd else 0)
                        new_bwd = bwd + (0 if is_fwd else 1)
                        if neighbour in kept_set:
                            if neighbour not in tree_visited:
                                tree_visited.add(neighbour)
                                tree_queue.append(neighbour)
                                if new_fwd >= new_bwd:
                                    indirect_edges.append((f_node, neighbour, pruned_count))
                                else:
                                    indirect_edges.append((neighbour, f_node, pruned_count))
                        elif neighbour in mediator_nodes:
                            inner_queue.append((neighbour, pruned_count, new_fwd, new_bwd))
                        elif neighbour in filtered_nodes:
                            inner_queue.append((neighbour, pruned_count + 1, new_fwd, new_bwd))

    # --- Phase 1b: apply pruning of filtered nodes ---
    removed_edge_indices = set()
    if to_remove:
        for src, tgt, idx in edges:
            if src in to_remove or tgt in to_remove:
                removed_edge_indices.add(idx)

    # --- Phase 1c: iteratively remove dangling mediators ---
    # Build surviving-edge adjacency, then repeatedly remove mediator nodes
    # that have only 0 or 1 real neighbour (i.e. they don't bridge between two
    # real nodes). "Real" = unfiltered or kept-filtered.
    surviving_edges = [(s, t, i) for s, t, i in edges if i not in removed_edge_indices]

    real_nodes = unfiltered_nodes | keep_filtered
    dangling_mediators = set()
    changed = True
    removed_mediator_set = set()

    while changed:
        changed = False
        # Build adjacency from surviving edges (excluding already-removed mediators)
        post_adj = {}
        for src, tgt, idx in surviving_edges:
            if src in removed_mediator_set or tgt in removed_mediator_set:
                continue
            post_adj.setdefault(src, set()).add(tgt)
            post_adj.setdefault(tgt, set()).add(src)

        for med in mediator_nodes - removed_mediator_set:
            neighbours = post_adj.get(med, set())
            # Count how many distinct real nodes this mediator connects to
            real_neighbours = neighbours & real_nodes
            mediator_neighbours = neighbours & (mediator_nodes - removed_mediator_set)

            # A useful mediator bridges between real nodes (possibly through
            # other mediators). A dangling mediator only reaches 0 or 1 real
            # node through its direct connections.
            if len(real_neighbours) >= 2:
                continue  # Bridges two real nodes — keep

            if len(real_neighbours) == 1 and mediator_neighbours:
                # Check if ANY of its mediator-neighbours leads to a different
                # real node (i.e. the mediator is part of a chain)
                # Quick check: BFS through mediator neighbours only
                chain_visited = {med}
                chain_queue = deque([med])
                other_real = set()
                while chain_queue:
                    cn = chain_queue.popleft()
                    for nb in post_adj.get(cn, set()):
                        if nb in chain_visited or nb in removed_mediator_set:
                            continue
                        chain_visited.add(nb)
                        if nb in real_nodes:
                            other_real.add(nb)
                        elif nb in mediator_nodes:
                            chain_queue.append(nb)
                if len(other_real) >= 2:
                    continue  # Part of a useful chain — keep

            # Dangling: remove
            removed_mediator_set.add(med)
            changed = True

    # Collect all edge indices to remove (pruned filtered + dangling mediators)
    all_nodes_to_purge = to_remove | removed_mediator_set
    final_removed_edges = set()
    for src, tgt, idx in edges:
        if src in all_nodes_to_purge or tgt in all_nodes_to_purge:
            final_removed_edges.add(idx)

    # Rewrite file
    node_def_pattern = re.compile(r'^\s*"([^"]+)"\s*(\[.*?\])?\s*;?\s*$')
    output = []
    for i, line in enumerate(lines):
        if i in final_removed_edges:
            continue
        s = line.strip()
        m = node_def_pattern.match(s)
        if m and '->' not in s and m.group(1) in all_nodes_to_purge:
            continue
        output.append(line)
    lines = output

    print(f"--- Filtered-pruning: removed {len(to_remove)} filtered node(s), "
          f"{len(removed_mediator_set)} dangling mediator(s), "
          f"{len(final_removed_edges)} edge(s) ---")

    # --- Insert indirect-connection dashed edges ---
    if indirect_edges:
        new_edge_lines = []
        for src, dst, pruned_count in indirect_edges:
            if pruned_count > 0:
                xlabel = f'via {pruned_count} filtered'
            else:
                xlabel = 'indirectly connected'
            new_edge_lines.append(
                f'"{src}" -> "{dst}" [style="dashed", color="#999999", '
                f'xlabel="{xlabel}", fontsize="9", fontcolor="#999999"];\n\n'
            )

        closing_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                closing_idx = i
                break

        if closing_idx >= 0:
            lines = lines[:closing_idx] + ['\n'] + new_edge_lines + lines[closing_idx:]

        print(f"--- Filtered-indirect: added {len(indirect_edges)} dashed edge(s) ---")

    with open(dot_filename, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    collapse_excess_blank_lines(dot_filename)
