"""
Gephi transformation pipeline.

This module re-exports Gephi transformation functions from specialized modules.
Individual functions are organized into:
- phases: Phase processing
- nodes: Node finding
- edges: Edge processing and creation
- content: DOT content processing
- io: File I/O
- file_cleanup: File cleanup functions (duplicate edges, attributes, invisible elements)
- sources: Source handling
- colors: Color utilities
- postprocess: Post-processing
"""
from .phases import process_phases_only
from .nodes import (
    find_gephi_matching_proposition_nodes,
    find_gephi_employed_nodes,
    find_gephi_function_nodes,
    find_gephi_entailment_nodes,
    find_gephi_etiology_nodes,
    find_gephi_analogy_nodes,
    find_gephi_reference_nodes,
)
from .edges import (
    process_gephi_edges_for_entailment_nodes,
    process_gephi_edges_for_etiology_nodes,
    process_gephi_edges_for_analogy_nodes,
    process_gephi_edges_for_reference_nodes,
    process_gephi_edges_for_pseudonodes,
    create_gephi_direct_entailment_edges,
    create_gephi_direct_etiology_edges,
    create_gephi_direct_analogy_edges,
    create_gephi_direct_matching_edges,
    create_gephi_direct_employed_edges,
    create_gephi_direct_reference_edges,
    create_gephi_direct_function_edges,
)
from .content import process_gephi_dot_content
from .io import write_gephi_dot_file
from .file_cleanup import remove_duplicate_gephi_edges, clean_edge_attributes
from .sources import (
    find_gephi_source_subgraphs,
    create_gephi_source_nodes,
    create_gephi_source_edges,
)
from .postprocess import post_process_gephi_dot, write_source_nodes_after_processing

def create_gephi_dot(dot_filename, gephi_dot_filename):
    """Create a DOT file optimized for Gephi by removing invisible elements and simplifying the graph."""
    print(f"Creating Gephi-optimized DOT file: {gephi_dot_filename}")
    
    # Phase 1: Process only phase nodes and their connections
    temp_phase_processed_file = f"{dot_filename}.phase_processed.dot"
    process_phases_only(dot_filename, temp_phase_processed_file)
    
    # Phase 2: Process all other elements using the phase-processed file as input
    with open(temp_phase_processed_file, 'r', encoding='utf-8') as f:
        dot_content = f.read()
    
    # Find different types of pseudo-nodes
    matching_nodes = find_gephi_matching_proposition_nodes(dot_content)
    employed_nodes = find_gephi_employed_nodes(dot_content)
    function_nodes = find_gephi_function_nodes(dot_content)
    entailment_nodes = find_gephi_entailment_nodes(dot_content)
    analogy_nodes = find_gephi_analogy_nodes(dot_content)
    reference_nodes = find_gephi_reference_nodes(dot_content)
    etiology_nodes = find_gephi_etiology_nodes(dot_content)

    # Find source subgraphs and their associated nodes
    source_subgraphs = find_gephi_source_subgraphs(dot_content)
    
    # Create source nodes and their connections
    source_nodes = create_gephi_source_nodes(source_subgraphs)
    source_edges = create_gephi_source_edges(source_subgraphs, dot_content)
    
    # Process edges connected to pseudo-nodes
    process_gephi_edges_for_pseudonodes(dot_content, matching_nodes, employed_nodes, function_nodes)
    process_gephi_edges_for_entailment_nodes(dot_content, entailment_nodes)
    process_gephi_edges_for_analogy_nodes(dot_content, analogy_nodes)
    process_gephi_edges_for_reference_nodes(dot_content, reference_nodes)
    process_gephi_edges_for_etiology_nodes(dot_content, etiology_nodes)

    # Create direct edges that replace pseudo-nodes
    direct_matching_edges = create_gephi_direct_matching_edges(matching_nodes)
    direct_employed_edges = create_gephi_direct_employed_edges(employed_nodes)
    direct_function_edges = create_gephi_direct_function_edges(function_nodes)
    direct_entailment_edges = create_gephi_direct_entailment_edges(entailment_nodes)
    direct_analogy_edges = create_gephi_direct_analogy_edges(analogy_nodes)
    direct_reference_edges = create_gephi_direct_reference_edges(reference_nodes)
    direct_etiology_edges = create_gephi_direct_etiology_edges(etiology_nodes)

    # Combine all direct edges
    direct_edges = (direct_matching_edges + direct_employed_edges + 
                   direct_function_edges + direct_entailment_edges + 
                   direct_analogy_edges + direct_reference_edges +
                   direct_etiology_edges)
    
    # Add source connections to direct edges (only once)
    direct_edges.extend(source_edges)

    # Process the DOT content to simplify and optimize - phases are already processed
    # We pass empty phase_to_cluster and cluster_parents since phases are already handled
    processed_lines, _ = process_gephi_dot_content(
        dot_content,
        matching_nodes, employed_nodes, function_nodes, 
        entailment_nodes, analogy_nodes, reference_nodes, etiology_nodes
    )

    # Add source nodes to processed lines BEFORE writing the file
    processed_lines.extend(source_nodes)

    # Write the processed DOT content to the Gephi DOT file
    # No need to pass new_phase_edges since they're already in the dot_content
    write_gephi_dot_file(gephi_dot_filename, processed_lines, direct_edges)
    
    # Clean up temporary file
    import os
    os.remove(temp_phase_processed_file)
        
    # Remove duplicate edge definitions before final cleanup
    remove_duplicate_gephi_edges(gephi_dot_filename)
    
    # Additional post-processing
    clean_edge_attributes(gephi_dot_filename)
    post_process_gephi_dot(gephi_dot_filename)
    
    # Write back source nodes after post-processing to ensure they appear in the final file
    write_source_nodes_after_processing(gephi_dot_filename, source_nodes)

