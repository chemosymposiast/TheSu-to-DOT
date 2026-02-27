"""DOT file rendering and export to SVG, PDF, PNG.

Key functions: get_layout_params, display_dot, save_dot_as_svg, save_dot_as_pdf,
save_dot_as_png
"""
from bootstrap.primary_imports import os, re
from bootstrap.delayed_imports import Source, SVG, display

# Max characters per line in info box (matches width of boxes in outputs 1-8)
_INFO_BOX_MAX_CHARS = 55


def _wrap_text_for_label(text: str, max_chars: int = _INFO_BOX_MAX_CHARS) -> str:
    """Wrap long text at comma/space boundaries for GraphViz HTML labels."""
    if len(text) <= max_chars:
        return text
    parts = []
    current = ""
    for segment in text.split(", "):
        if not current:
            current = segment
        elif len(current) + len(segment) + 2 <= max_chars:
            current += ", " + segment
        else:
            parts.append(current)
            current = segment
    if current:
        parts.append(current)
    return "<BR/>".join(parts)


def _increase_node_margins(dot_content: str) -> str:
    """
    Slightly increase internal margins for box-shaped nodes to prevent
    long text from touching the right border, without changing the
    underlying DOT files saved by the core pipeline.
    """
    # Bump horizontal and vertical margins a little for box nodes
    return dot_content.replace('margin="0.30,0.1"', 'margin="0.35,0.12"')
from config.runtime_settings import (
    DEFAULT_ENGINE,
    LAYOUT_SETTINGS,
    PDF_OUTPUT_SETTINGS,
    PNG_OUTPUT_SETTINGS,
    thesis_focus_id as _default_thesis_focus_id,
)


def get_layout_params(engine=None, custom_settings=None, xml_name=None, sources_to_select=None,
                        filter_propositions=False, filter_matching_proposition_sequences=False,
                        filter_all_sequences=False, filter_extrinsic_elements=False,
                        custom_prop_filters=None,
                        custom_seq_phase_filters=None, thesis_focus_id=_default_thesis_focus_id,
                        elements_to_exclude=None):
    """
    Get layout parameters as a string for the specified engine, including an info box label.

    Parameters:
    - engine: GraphViz layout engine ('dot', 'fdp', 'neato')
    - custom_settings: Dictionary of custom settings to override defaults
    - xml_name: Name of the source XML file
    - sources_to_select: List of selected source IDs
    - filter_propositions, filter_matching_proposition_sequences, filter_all_sequences: Boolean filter states
    - custom_prop_filters, custom_seq_phase_filters: Dictionaries for custom filters
    - thesis_focus_id: ID of the THESIS to focus on, or None

    Returns: String with GraphViz layout parameters and info box label
    """
    # Use the default engine if none specified
    if engine is None:
        engine = DEFAULT_ENGINE

    # Get default settings for the specified engine
    if engine in LAYOUT_SETTINGS:
        settings = LAYOUT_SETTINGS[engine].copy()
    else:
        settings = LAYOUT_SETTINGS[DEFAULT_ENGINE].copy()

    # Override with custom settings if provided
    if custom_settings:
        settings.update(custom_settings)

    # Prepare info box content
    info_box_lines = []
    if xml_name:
        info_box_lines.append(f'<TR><TD ALIGN="LEFT">XML File:</TD><TD ALIGN="LEFT">{xml_name}.xml</TD></TR>')
    if sources_to_select:
        # Format sources for better readability in the box
        sources_str = '<BR/>'.join(s.replace("<", "&lt;").replace(">", "&gt;") for s in sources_to_select) # Escape IDs
        info_box_lines.append(f'<TR><TD ALIGN="LEFT" VALIGN="TOP">Sources:</TD><TD ALIGN="LEFT">{sources_str}</TD></TR>')

    info_box_lines.append(f'<TR><TD ALIGN="LEFT">Engine:</TD><TD ALIGN="LEFT">{engine}</TD></TR>')

    # --- Add Active Filter Information ---
    active_filter_lines = []
    # Check Toggles (respecting precedence a > b > c)
    if filter_propositions:
        active_filter_lines.append("(a) Remove All Propositions")
    elif filter_matching_proposition_sequences:
        active_filter_lines.append("(b) Remove Matching Prop Seq/Phases")
    # Only check C if A and B are false
    if filter_all_sequences:
        active_filter_lines.append("(c) Remove All Sequence Elements")

    # (d) Check Extrinsic Elements Filter
    if filter_extrinsic_elements:
        active_filter_lines.append("(d) Remove 'Extrinsic' Elements")

    # (e) Check Excluded Elements
    if elements_to_exclude:
        exclude_ids = [str(x).strip() for x in elements_to_exclude if x]
        if exclude_ids:
            active_filter_lines.append(f"(e) Exclude Elements ({len(exclude_ids)}):")
            safe_ids = [eid.replace("<", "&lt;").replace(">", "&gt;") for eid in exclude_ids]
            excluded_str = ", ".join(safe_ids)
            active_filter_lines.append(_wrap_text_for_label(excluded_str))

    # Check Custom Prop Filters
    if custom_prop_filters:
        # Normalize keys just in case they weren't before passing
        normalized_prop_filters = {pid.lstrip('#'): tids for pid, tids in custom_prop_filters.items()}
        if normalized_prop_filters: # Check if dict is non-empty after normalization
            active_filter_lines.append("")  # Visual separation from Excluded Elements
            active_filter_lines.append("(f) Exclude Propositions (by thesis):")
            prop_filter_details = []
            for prop_id, thesis_ids in normalized_prop_filters.items():
                # Escape potential HTML entities in IDs
                safe_prop_id = prop_id.replace("<", "&lt;").replace(">", "&gt;")
                safe_thesis_ids_str = ", ".join(t_id.replace("<", "&lt;").replace(">", "&gt;") for t_id in thesis_ids)
                line = f"&nbsp;&nbsp;&nbsp;&nbsp;&bull; Prop {safe_prop_id} &rarr; Theses: {safe_thesis_ids_str}"
                prop_filter_details.append(_wrap_text_for_label(line))
            active_filter_lines.append('<BR/>'.join(prop_filter_details))

    # Check Custom Seq/Phase Filters
    if custom_seq_phase_filters:
        normalized_seq_filters = {sid.lstrip('#'): tids for sid, tids in custom_seq_phase_filters.items()}
        if normalized_seq_filters:
            active_filter_lines.append("")  # Visual separation
            active_filter_lines.append("(g) Exclude Sequences (by thesis):")
            seq_filter_details = []
            for seq_id, thesis_ids in normalized_seq_filters.items():
                safe_seq_id = seq_id.replace("<", "&lt;").replace(">", "&gt;")
                safe_thesis_ids_str = ", ".join(t_id.replace("<", "&lt;").replace(">", "&gt;") for t_id in thesis_ids)
                line = f"&nbsp;&nbsp;&nbsp;&nbsp;&bull; Seq {safe_seq_id} &rarr; Theses: {safe_thesis_ids_str}"
                seq_filter_details.append(_wrap_text_for_label(line))
            active_filter_lines.append('<BR/>'.join(seq_filter_details))

    # Check Thesis Focus Filter
    if thesis_focus_id:
        safe_thesis_focus_id = ', '.join(t_id.replace("<", "&lt;").replace(">", "&gt;") for t_id in thesis_focus_id)
        active_filter_lines.append(_wrap_text_for_label(f"&bull; Thesis Focus: {safe_thesis_focus_id}"))

    # Add the filter info row if any filters are active
    if active_filter_lines:
        filters_str = '<BR/>'.join(active_filter_lines)
        info_box_lines.append(f'<TR><TD ALIGN="LEFT" VALIGN="TOP">Active Filters:</TD><TD ALIGN="LEFT">{filters_str}</TD></TR>')
    # --- End Filter Information ---

    # Format parameters for the box
    params_str = '<BR/>'.join([f'{k} = {v}' for k, v in settings.items()])
    info_box_lines.append(f'<TR><TD ALIGN="LEFT" VALIGN="TOP">Parameters:</TD><TD ALIGN="LEFT">{params_str}</TD></TR>')

    info_box_html = (
        '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" WIDTH="400">'
        + "".join(info_box_lines) +
        '</TABLE>'
    )

    # Build parameters string including the info box label
    params = ['graph [']
    # Add the info box label, positioned at the top-left
    params.append(f'label=<{info_box_html}>')
    params.append('labelloc=t') # Top location
    params.append('labeljust=l') # Left justification

    for key, value in settings.items():
        # Ensure string values are quoted correctly in the output
        if isinstance(value, str):
            # Escape backslashes and double quotes within the string value
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            params.append(f'{key}="{escaped_value}"')
        else:
            params.append(f'{key}={value}')
    params.append('];')
    params.append('node [layer="front"];')
    params.append('edge [layer="back", arrowsize=0.7];')

    return '\n'.join(params)


def display_dot(dot_filename, engine=None, custom_settings=None, xml_name=None, sources_to_select=None,
                    filter_propositions=False, filter_matching_proposition_sequences=False,
                    filter_all_sequences=False, filter_extrinsic_elements=False,
                    custom_prop_filters=None,
                    custom_seq_phase_filters=None, thesis_focus_id=_default_thesis_focus_id,
                    elements_to_exclude=None):
    """
    Display a DOT file with optimized layout parameters and info box.

    Parameters:
    - dot_filename: Path to DOT file
    - engine: GraphViz layout engine ('dot', 'fdp', 'neato', 'twopi', 'circo')
                If None, uses DEFAULT_ENGINE
    - custom_settings: Dictionary of custom settings to override defaults
    - xml_name: Name of the source XML file for the info box
    - sources_to_select: List of selected source IDs for the info box
    - filter_... , custom_... , thesis_focus_id : Filter states/configurations for the info box
    """
    try:
        with open(dot_filename, 'r', encoding='utf-8') as dot_file:
            dot_content = dot_file.read()
    except FileNotFoundError:
        print(f"Error: DOT file not found at {dot_filename}")
        return None

    # Increase node margins slightly to avoid text touching borders
    dot_content = _increase_node_margins(dot_content)

    # Use the default engine if none specified
    if engine is None:
        engine = DEFAULT_ENGINE

    # Get layout parameters for the specified engine, including the info box
    layout_params = get_layout_params(engine, custom_settings, xml_name, sources_to_select,
                                        filter_propositions=filter_propositions,
                                        filter_matching_proposition_sequences=filter_matching_proposition_sequences,
                                        filter_all_sequences=filter_all_sequences,
                                        filter_extrinsic_elements=filter_extrinsic_elements,
                                        custom_prop_filters=custom_prop_filters,
                                        custom_seq_phase_filters=custom_seq_phase_filters,
                                        thesis_focus_id=thesis_focus_id,
                                        elements_to_exclude=elements_to_exclude)

    # Robustly find where to insert the parameters
    match = re.search(r'digraph\s+\S*\s*\{', dot_content, re.IGNORECASE)
    if match:
        insert_pos = match.end()
        modified_content = dot_content[:insert_pos] + f'\n{layout_params}\n' + dot_content[insert_pos:]
    else:
            # If the standard pattern isn't found, maybe it's already modified or malformed?
            # For simplicity, we'll just prepend if the pattern fails.
            print("Warning: Could not find standard 'digraph G {' pattern. Prepending params.")
            modified_content = f'digraph G {{\n{layout_params}\n{dot_content}'

    try:
        src = Source(modified_content, engine=engine)
        display(SVG(src.pipe(format='svg')))
    except Exception as e: # Catch broader exceptions from graphviz/display
        print(f"Error occurred while rendering or displaying the SVG: {e}")
        print("Check Graphviz installation and DOT file syntax.")
    return src


def save_dot_as_svg(dot_filename, svg_filename, engine=None, custom_settings=None, xml_name=None, sources_to_select=None,
                        filter_propositions=False, filter_matching_proposition_sequences=False,
                        filter_all_sequences=False, filter_extrinsic_elements=False,
                        custom_prop_filters=None,
                        custom_seq_phase_filters=None, thesis_focus_id=_default_thesis_focus_id,
                        elements_to_exclude=None):
    """
    Save DOT file as SVG with optimized layout parameters and info box.
    """
    try:
        with open(dot_filename, 'r', encoding='utf-8') as dot_file:
            dot_content = dot_file.read()
    except FileNotFoundError:
        print(f"Error: DOT file not found at {dot_filename}")
        return None

    # Increase node margins slightly to avoid text touching borders
    dot_content = _increase_node_margins(dot_content)

    # Use the default engine if none specified
    if engine is None:
        engine = DEFAULT_ENGINE

    # Get layout parameters for the specified engine, including the info box
    layout_params = get_layout_params(engine, custom_settings, xml_name, sources_to_select,
                                        filter_propositions=filter_propositions,
                                        filter_matching_proposition_sequences=filter_matching_proposition_sequences,
                                        filter_all_sequences=filter_all_sequences,
                                        filter_extrinsic_elements=filter_extrinsic_elements,
                                        custom_prop_filters=custom_prop_filters,
                                        custom_seq_phase_filters=custom_seq_phase_filters,
                                        thesis_focus_id=thesis_focus_id,
                                        elements_to_exclude=elements_to_exclude)

    # Robustly find where to insert the parameters
    match = re.search(r'digraph\s+\S*\s*\{', dot_content, re.IGNORECASE)
    if match:
            insert_pos = match.end()
            modified_content = dot_content[:insert_pos] + f'\n{layout_params}\n' + dot_content[insert_pos:]
    else:
            print("Warning: Could not find standard 'digraph G {' pattern. Prepending params.")
            modified_content = f'digraph G {{\n{layout_params}\n{dot_content}'

    try:
        src = Source(modified_content, engine=engine)
        src.format = 'svg'
        src.render(filename=svg_filename, format='svg', cleanup=True, view=False)
    except Exception as e:
        print(f"An unexpected error occurred during SVG saving: {e}")
        print("Check Graphviz installation and DOT file syntax.")
        return None # Indicate failure
    return src


def save_dot_as_pdf(dot_filename, pdf_filename, engine=None, custom_settings=None, xml_name=None, sources_to_select=None,
                        filter_propositions=False, filter_matching_proposition_sequences=False,
                        filter_all_sequences=False, filter_extrinsic_elements=False,
                        custom_prop_filters=None,
                        custom_seq_phase_filters=None, thesis_focus_id=_default_thesis_focus_id,
                        elements_to_exclude=None):
    """
    Save DOT file as PDF. Attempts to fit within A3 (portrait) if larger,
    otherwise keeps original size. Uses high resolution (300 DPI).
    """
    try:
        with open(dot_filename, 'r', encoding='utf-8') as dot_file:
            dot_content = dot_file.read()
    except FileNotFoundError:
        print(f"Error: DOT file not found at {dot_filename}")
        return None

    # Increase node margins slightly to avoid text touching borders
    dot_content = _increase_node_margins(dot_content)

    # Use the default engine if none specified
    if engine is None:
        engine = DEFAULT_ENGINE

    # Get standard layout parameters
    layout_params = get_layout_params(engine, custom_settings, xml_name, sources_to_select,
                                        filter_propositions=filter_propositions,
                                        filter_matching_proposition_sequences=filter_matching_proposition_sequences,
                                        filter_all_sequences=filter_all_sequences,
                                        filter_extrinsic_elements=filter_extrinsic_elements,
                                        custom_prop_filters=custom_prop_filters,
                                        custom_seq_phase_filters=custom_seq_phase_filters,
                                        thesis_focus_id=thesis_focus_id,
                                        elements_to_exclude=elements_to_exclude)

    # Insert standard layout params into DOT content
    match = re.search(r'digraph\s+\S*\s*\{', dot_content, re.IGNORECASE)
    if match:
            insert_pos = match.end()
            modified_content = dot_content[:insert_pos] + f'\n{layout_params}\n' + dot_content[insert_pos:]
    else:
            print("Warning: Could not find standard 'digraph G {' pattern. Prepending standard params.")
            modified_content = f'digraph G {{\n{layout_params}\n{dot_content}'

    # --- Add PDF-specific attributes (Fit A3 using size, High Res) ---
    size_pdf = PDF_OUTPUT_SETTINGS["size"]
    dpi_pdf = PDF_OUTPUT_SETTINGS["dpi"]
    pdf_specific_attrs = f'graph [size="{size_pdf}", ratio=auto, dpi={dpi_pdf}];'

    # Find the end of the main graph attributes block to insert PDF specifics
    graph_attr_match = re.search(r'graph\s*\[[^]]*\]\s*;?', modified_content, re.IGNORECASE | re.DOTALL)
    if graph_attr_match:
        insert_pdf_pos = graph_attr_match.end()
        modified_content = modified_content[:insert_pdf_pos] + '\n' + pdf_specific_attrs + modified_content[insert_pdf_pos:]
    else:
        # Fallback logic
        print("Warning: Could not precisely locate graph attribute block. Inserting PDF attributes after standard layout params.")
        layout_params_pattern = re.escape(layout_params)
        match_layout = re.search(layout_params_pattern, modified_content)
        if match_layout:
             insert_pdf_pos = match_layout.end()
             modified_content = modified_content[:insert_pdf_pos] + '\n' + pdf_specific_attrs + modified_content[insert_pdf_pos:]
        else:
             print("Warning: Could not find layout params insertion point either. Prepending PDF attributes.")
             modified_content = pdf_specific_attrs + '\n' + modified_content
    # --- End PDF-specific attributes ---

    try:
        src = Source(modified_content, engine=engine)
        src.format = 'pdf'
        src.render(filename=pdf_filename, format='pdf', cleanup=True, view=False)
    except Exception as e:
        print(f"An unexpected error occurred during PDF saving: {e}")
        print("Check Graphviz installation and DOT file syntax.")
        return None # Indicate failure
    return src # Return src object on success


def save_dot_as_png(dot_filename, png_filename, engine=None, custom_settings=None, xml_name=None, sources_to_select=None,
                        filter_propositions=False, filter_matching_proposition_sequences=False,
                        filter_all_sequences=False, filter_extrinsic_elements=False,
                        custom_prop_filters=None,
                        custom_seq_phase_filters=None, thesis_focus_id=_default_thesis_focus_id,
                        elements_to_exclude=None):
    """
    Save DOT file as PNG. Attempts to fit within A3 (portrait) if larger,
    otherwise keeps original size. Uses high resolution (300 DPI).
    """
    try:
        with open(dot_filename, 'r', encoding='utf-8') as dot_file:
            dot_content = dot_file.read()
    except FileNotFoundError:
        print(f"Error: DOT file not found at {dot_filename}")
        return None

    # Increase node margins slightly to avoid text touching borders
    dot_content = _increase_node_margins(dot_content)

    # Use the default engine if none specified
    if engine is None:
        engine = DEFAULT_ENGINE

    # Get standard layout parameters
    layout_params = get_layout_params(engine, custom_settings, xml_name, sources_to_select,
                                        filter_propositions=filter_propositions,
                                        filter_matching_proposition_sequences=filter_matching_proposition_sequences,
                                        filter_all_sequences=filter_all_sequences,
                                        filter_extrinsic_elements=filter_extrinsic_elements,
                                        custom_prop_filters=custom_prop_filters,
                                        custom_seq_phase_filters=custom_seq_phase_filters,
                                        thesis_focus_id=thesis_focus_id,
                                        elements_to_exclude=elements_to_exclude)

    # Insert standard layout params into DOT content
    match = re.search(r'digraph\s+\S*\s*\{', dot_content, re.IGNORECASE)
    if match:
            insert_pos = match.end()
            modified_content = dot_content[:insert_pos] + f'\n{layout_params}\n' + dot_content[insert_pos:]
    else:
            print("Warning: Could not find standard 'digraph G {' pattern. Prepending standard params.")
            modified_content = f'digraph G {{\n{layout_params}\n{dot_content}'

    # --- Add PNG-specific attributes (Fit A3 using size, High Res) ---
    size_png = PNG_OUTPUT_SETTINGS["size"]
    dpi_png = PNG_OUTPUT_SETTINGS["dpi"]
    png_specific_attrs = f'graph [size="{size_png}", ratio=auto, dpi={dpi_png}];'

    # Find the end of the main graph attributes block to insert PNG specifics
    graph_attr_match = re.search(r'graph\s*\[[^]]*\]\s*;?', modified_content, re.IGNORECASE | re.DOTALL)
    if graph_attr_match:
        insert_png_pos = graph_attr_match.end()
        modified_content = modified_content[:insert_png_pos] + '\n' + png_specific_attrs + modified_content[insert_png_pos:]
    else:
        # Fallback logic
        print("Warning: Could not precisely locate graph attribute block. Inserting PNG attributes after standard layout params.")
        layout_params_pattern = re.escape(layout_params)
        match_layout = re.search(layout_params_pattern, modified_content)
        if match_layout:
             insert_png_pos = match_layout.end()
             modified_content = modified_content[:insert_png_pos] + '\n' + png_specific_attrs + modified_content[insert_png_pos:]
        else:
             print("Warning: Could not find layout params insertion point either. Prepending PNG attributes.")
             modified_content = png_specific_attrs + '\n' + modified_content
    # --- End PNG-specific attributes ---

    try:
        src = Source(modified_content, engine=engine)
        src.format = 'png'
        rendered_path = src.render(filename=png_filename, format='png', cleanup=True, view=False)

        # Check file size
        if os.path.exists(rendered_path):
             # Check if file is empty
             if os.path.getsize(rendered_path) == 0:
                 print(f"Warning: Generated PNG file '{rendered_path}' is empty.")
                 print("Check Graphviz installation and logs for errors.")
             else:
                 file_size_mb = os.path.getsize(rendered_path) / (1024 * 1024)
                 max_mb = PNG_OUTPUT_SETTINGS.get("max_warning_mb", 20.0)
                 if max_mb > 0 and file_size_mb > max_mb:
                     print(f"Warning: Generated PNG file '{rendered_path}' ({file_size_mb:.2f} MB) exceeds {max_mb}MB limit.")
                     print("Consider reducing output.png.dpi in settings_user.toml if size is consistently an issue.")
        else:
             print(f"Warning: PNG file '{rendered_path}' was not found after render call.")

    except Exception as e:
        print(f"An unexpected error occurred during PNG saving: {e}")
        print("Check Graphviz installation and DOT file syntax.")
        return None # Indicate failure
    return src # Return src object on success
