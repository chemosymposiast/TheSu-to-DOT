"""Delayed imports: modules requiring runtime dependency checks.

Loaded after run_runtime_checks() and setup_graphviz_path_and_check().
Includes: graphviz, lxml, IPython.display. Stdlib (re, math, etc.) come from primary_imports.
"""
# ruff: noqa: F401 - re-exports for other modules
from graphviz import Source
from lxml import etree as ET
from IPython.display import SVG, display
