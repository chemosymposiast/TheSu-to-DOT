"""
TheSu-to-DOT — Convert TheSu XML documents to DOT graphs for GraphViz/Gephi.

Pipeline: XML (_thesu_inputs) → DOT → Gephi DOT → SVG/PDF/PNG (_thesu_outputs).
Configuration and paths live in settings_user.toml (edit that file to change settings).

Copyright (c) 2025

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
https://creativecommons.org/licenses/by-sa/4.0/ or see the LICENSE file
included with this distribution.
"""
from bootstrap.primary_imports import os
import webbrowser
import pathlib
from bootstrap.dependencies import run_runtime_checks, setup_graphviz_path_and_check

# --- Bootstrap: fail fast if dependencies or GraphViz are missing ---
run_runtime_checks()
setup_graphviz_path_and_check()

# --- Configuration: paths, filters, layout (edit settings_user.toml) ---
from config.runtime_settings import (
    xml_name,
    sources_to_select,
    filter_propositions,
    filter_matching_proposition_sequences,
    filter_all_sequences,
    filter_extrinsic_elements,
    custom_prop_filters_to_apply,
    custom_seq_phase_filters_to_apply,
    thesis_focus_id,
    elements_to_exclude,
    xml_filename,
    dot_filename,
    svg_filename,
    pdf_filename,
    png_filename,
    OUTPUT_SVG,
    OUTPUT_PDF,
    OUTPUT_PNG,
    OPEN_IN_BROWSER,
)

# --- Core pipeline: DOT build, postprocess, Gephi, render ---
from dot import create_dot
from dot.postprocess import fix_arrow_directions
from gephi import create_gephi_dot
from render import save_dot_as_svg, save_dot_as_pdf, save_dot_as_png

# %%  --- Main execution ---

def _open_svg_in_browser(svg_path: str) -> None:
    """Open the given SVG file in the default web browser, cross-platform."""
    svg_file = pathlib.Path(svg_path)
    if not svg_file.is_file():
        print(f"SVG file not found at {svg_file}")
        return

    try:
        webbrowser.open(svg_file.resolve().as_uri())
    except Exception as e:
        print(f"Could not automatically open SVG file in browser: {e}")


if __name__ == "__main__":
    # --- Step 1: Build DOT from XML (with full filter config) ---
    create_dot(xml_filename, dot_filename, sources_to_select=sources_to_select,
               filter_propositions=filter_propositions,
               filter_matching_proposition_sequences=filter_matching_proposition_sequences,
               filter_all_sequences=filter_all_sequences,
               filter_extrinsic_elements=filter_extrinsic_elements,
               custom_prop_filters=custom_prop_filters_to_apply,
               custom_seq_phase_filters=custom_seq_phase_filters_to_apply,
               thesis_focus_id=thesis_focus_id,
               elements_to_exclude=elements_to_exclude)

    # --- Step 2: Rebuild DOT (simplified filters) and generate Gephi DOT ---
    create_dot(xml_filename, dot_filename, sources_to_select)
    gephi_dot_path = dot_filename[:-4] + "_gephi.dot"
    create_gephi_dot(dot_filename, gephi_dot_path)

    # --- Step 3: Fix arrow directions for correct edge layout ---
    try:
        fixed_dot_filename = fix_arrow_directions(dot_filename)
    except Exception as e:
        print(f"Error during arrow direction fixing: {e}")
        fixed_dot_filename = dot_filename  # fallback to unfixed DOT

    # --- Step 4: Export to SVG, PDF, PNG (conditionally) ---
    svg_src = None
    if OUTPUT_SVG:
        svg_src = save_dot_as_svg(
            fixed_dot_filename,
            svg_filename,
            xml_name=xml_name,
            sources_to_select=sources_to_select,
            filter_propositions=filter_propositions,
            filter_matching_proposition_sequences=filter_matching_proposition_sequences,
            filter_all_sequences=filter_all_sequences,
            filter_extrinsic_elements=filter_extrinsic_elements,
            custom_prop_filters=custom_prop_filters_to_apply,
            custom_seq_phase_filters=custom_seq_phase_filters_to_apply,
            thesis_focus_id=thesis_focus_id,
            elements_to_exclude=elements_to_exclude,
        )

    if OUTPUT_PDF:
        pdf_src = save_dot_as_pdf(
            fixed_dot_filename,
            pdf_filename,
            xml_name=xml_name,
            sources_to_select=sources_to_select,
            filter_propositions=filter_propositions,
            filter_matching_proposition_sequences=filter_matching_proposition_sequences,
            filter_all_sequences=filter_all_sequences,
            filter_extrinsic_elements=filter_extrinsic_elements,
            custom_prop_filters=custom_prop_filters_to_apply,
            custom_seq_phase_filters=custom_seq_phase_filters_to_apply,
            thesis_focus_id=thesis_focus_id,
            elements_to_exclude=elements_to_exclude,
        )
    else:
        pdf_src = None

    if OUTPUT_PNG:
        png_src = save_dot_as_png(
            fixed_dot_filename,
            png_filename,
            xml_name=xml_name,
            sources_to_select=sources_to_select,
            filter_propositions=filter_propositions,
            filter_matching_proposition_sequences=filter_matching_proposition_sequences,
            filter_all_sequences=filter_all_sequences,
            filter_extrinsic_elements=filter_extrinsic_elements,
            custom_prop_filters=custom_prop_filters_to_apply,
            custom_seq_phase_filters=custom_seq_phase_filters_to_apply,
            thesis_focus_id=thesis_focus_id,
            elements_to_exclude=elements_to_exclude,
        )
    else:
        png_src = None

    # Open SVG in default browser (cross-platform) if enabled
    svg_file_path = svg_filename + ".svg"
    if OPEN_IN_BROWSER and OUTPUT_SVG and svg_src and os.path.exists(svg_file_path):
        _open_svg_in_browser(svg_file_path)

    print("\nScript finished.")

