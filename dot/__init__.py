"""DOT graph generation from TheSu XML.

Main entry: create_dot (from dot.orchestrator)
Element processing: initialize_elements_clusters, process_filtered_elements (from dot.elements)
"""
from .orchestrator import create_dot

__all__ = ['create_dot']
