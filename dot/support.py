"""Support-related DOT building functions.

Key functions: process_support_element, get_function_and_aim, process_support_targets,
process_explicit_targets, process_omitted_targets, process_employed_elements
"""
from bootstrap.primary_imports import re
from xml_processing.extractors import extract_paraphrasis_text
from utils.text import pad_short_string
from config.runtime_settings import XML_NAMESPACE
from dot.pseudo_nodes import generate_unique_pseudo_node_id_targets

def get_function_and_aim(support_element, namespaces):
    """Extract the primary support function (JUSTIFIES, EXPLAINS, etc.) and aim from a SUPPORT element."""
    support_functions_group = support_element.find('.//thesu:supportFunctionsGroup', namespaces=namespaces)
    
    functions = list(support_functions_group)
    functions_with_rank = [(function, int(function.get(f'{{{XML_NAMESPACE}}}rank')) if function.get(f'{{{XML_NAMESPACE}}}rank') is not None and function.get(f'{{{XML_NAMESPACE}}}rank').isdigit() else float('inf')) for function in functions]
    top_function = min(functions_with_rank, key=lambda x: x[1])

    element, rank = top_function
    function = None
    aim = None

    if element.tag == f'{{{XML_NAMESPACE}}}argumentation':
        function = "argumentation"
        aim = element.get(f'{{{XML_NAMESPACE}}}for')
        if aim is None or aim == "acc":
            function = "JUSTIFIES"
        elif aim == "rej":
            function = "REFUTES"
        elif aim == "mix":
            function = "DISCUSSES"
    elif element.tag == f'{{{XML_NAMESPACE}}}exposition':
        function = "EXPLAINS"
    elif element.tag == f'{{{XML_NAMESPACE}}}expansion':
        function = "EXPANDS ON"
    elif element.tag == f'{{{XML_NAMESPACE}}}contextualization':
        function = "CONTEXTUALIZES"

    return function, aim

def process_support_targets(element, function, implicit_att, implicit_style, function_attributes,
                           t_gephi_label, support_fill, support_border, support_style,
                           t_fill, t_border, t_shape,
                           namespaces, dot_file, written_lines, element_id, processed_propositions, source_id=None):
    """
    Process all the targets referred to by a SUPPORT.
    
    This includes explicit targets, omitted targets and employed elements.
    """
    
    # Initialize the function node ID
    func_node_id = None

    
    # Initialize employed node ID - will be created only if needed
    employed_node_id = None
    
    # === PROCESS TARGETS (things the SUPPORT refers to) ===
    
    # 1. Process explicit targets
    func_node_id, processed_propositions = process_explicit_targets(
        element, element_id, function, t_gephi_label, support_fill, support_border, 
        support_style, t_border, implicit_style, namespaces, dot_file, 
        written_lines, func_node_id, processed_propositions
    )
    
    # 2. Process omitted targets
    func_node_id, processed_propositions = process_omitted_targets(
        element, element_id, function, t_gephi_label, support_fill, support_border, 
        support_style, t_fill, t_border, t_shape, implicit_att, implicit_style, 
        function_attributes, namespaces, dot_file, written_lines, func_node_id, processed_propositions, source_id
    )
    
    # === PROCESS EMPLOYED ELEMENTS (things used within the SUPPORT) ===
    
    # 3. Process employed elements (both explicit and omitted)
    employed_node_id, processed_propositions = process_employed_elements(
        element, element_id, function_attributes, namespaces, 
        dot_file, written_lines, employed_node_id, processed_propositions, source_id
    )

    return func_node_id, written_lines, processed_propositions

def process_explicit_targets(element, element_id, function, t_gephi_label, 
                            support_fill, support_border, support_style, 
                            t_border, implicit_style, namespaces, 
                            dot_file, written_lines, func_node_id, processed_propositions):
    """
    Process explicit targets (things the SUPPORT refers to).
    
    This creates the function node (if needed) and connects it to explicit targets.
    """
    # Find all explicit targets
    explicit_targets = element.findall('.//thesu:targetsGroup/thesu:target', namespaces=namespaces)
    
    # Only process if we have explicit targets
    if explicit_targets:
        for target_element in explicit_targets:
            target_ref = target_element.get('{http://alchemeast.eu/thesu/ns/1.0}ref').split('#')[-1]           
            
            # Create the function node if it doesn't exist yet
            if func_node_id is None:
                func_node_id = f"{element_id}_func"
                line_to_write = (f'"{func_node_id}" [label="{function}", gephi_label="{t_gephi_label}", '
                                 f'gephi_omitted="false", fontsize="11", fillcolor="{support_fill}", '
                                 f'color="{support_border}", style="{support_style}", shape="ellipse"];\n\n')
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
                
                # Connect SUPPORT to function node
                line_to_write = f'"{element_id}" -> "{func_node_id}" [dir=none, color="{support_border}", style="{support_style}"];\n\n'
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
            
            # Connect function node to target
            line_to_write = f'"{func_node_id}" -> "{target_ref}" [color="{t_border}", style="{implicit_style}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
    
    return func_node_id, processed_propositions

def process_omitted_targets(element, element_id, function, t_gephi_label, 
                           support_fill, support_border, support_style, 
                           t_fill, t_border, t_shape, implicit_att, implicit_style,
                           function_attributes, namespaces, dot_file, 
                           written_lines, func_node_id, processed_propositions, source_id=None):
    """
    Process omitted targets (things the SUPPORT refers to that are not explicit).
    
    This creates omitted target nodes and connects them to the function node.
    """
    # Find all omitted targets elements
    omitted_targets_elements = element.findall('.//thesu:targetsGroup/thesu:omittedTargets', namespaces=namespaces)
    
    # Process each omitted targets element
    for omitted_targets_elem in omitted_targets_elements:
        # Case 1: Empty omittedTargets tag (completely unspecified)
        if len(list(omitted_targets_elem)) == 0:
            # Create a unique ID for this omitted element
            pseudo_node_id = generate_unique_pseudo_node_id_targets(
                written_lines, element_id, "omitted_ELEMENTS", "unspecified"
            )
            
            # Style for unspecified omitted elements
            o_fill = "#f5f5f5"  # Very light gray
            o_border = "#a0a0a0"  # Medium gray for border
            o_shape = "box"
            o_style = "dotted,filled,rounded"
            
            # Create the node
            label = f"<b>ELEMENTS</b><br/><i>(unspecified,<br/>omitted,<br/>one or more)</i>"
            source_attr = f', source="{source_id}"' if source_id else ''
            node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="ELEM", '
                         f'gephi_omitted="true", gephi_unspecified="true", fontsize="11", '
                         f'fillcolor="{o_fill}", color="{o_border}", style="{o_style}", '
                         f'shape="{o_shape}"{source_attr}];\n\n')
            dot_file.write(node_line)
            written_lines.append(node_line)
            
            # Ensure function node exists
            if func_node_id is None:
                func_node_id = f"{element_id}_func"
                line_to_write = (f'"{func_node_id}" [label="{function}", gephi_label="{t_gephi_label}", '
                                f'gephi_omitted="false", fontsize="11", fillcolor="{support_fill}", '
                                f'color="{support_border}", style="{support_style}", shape="ellipse"];\n\n')
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
                
                # Connect SUPPORT to function node
                line_to_write = f'"{element_id}" -> "{func_node_id}" [dir=none, color="{support_border}", style="{support_style}"];\n\n'
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
            
            # Connect function node to omitted element with proper color
            line_to_write = f'"{func_node_id}" -> "{pseudo_node_id}" [color="{t_border}", style="{implicit_style}"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
            continue
        
        # Case 2: Specified omitted targets
        for child in omitted_targets_elem:
            local_name = child.tag.split('}')[-1]  # e.g. omittedTHESES, omittedMISCS, omittedSUPPORTS
            
            # Determine the type of omitted element and its styling
            if local_name == "omittedTHESES":
                display_type = "THESIS"
                o_fill = "#f0faf0"       # THESIS fill
                o_border = "#82b366"     # THESIS border
                o_shape = "box"          # THESIS shape
                o_style = "rounded,filled"
            elif local_name == "omittedMISCS":
                display_type = "MISC"
                o_fill = "#ecd4bb"       # MISC fill
                o_border = "#b39c84"     # MISC border
                o_shape = "cylinder"     # MISC shape
                o_style = "filled"
            elif local_name == "omittedSUPPORTS":
                display_type = "SUPPORT"
                # For omitted SUPPORTS, determine styling based on functions
                func_elem = child.find('.//thesu:omittedSupportsFunctions', namespaces=namespaces)
                # Default all functions to rank 4
                ranks = {"JUSTIFIES": 4, "EXPLAINS": 4, "EXPANDS ON": 4, "CONTEXTUALIZES": 4}
                if func_elem is not None:
                    arg_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedArgumentationRank')
                    exp_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedExpositionRank')
                    expa_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedExpansionRank')
                    cont_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedContextualisationRank')
                    if arg_rank and arg_rank.isdigit():
                        ranks["JUSTIFIES"] = int(arg_rank)
                    if exp_rank and exp_rank.isdigit():
                        ranks["EXPLAINS"] = int(exp_rank)
                    if expa_rank and expa_rank.isdigit():
                        ranks["EXPANDS ON"] = int(expa_rank)
                    if cont_rank and cont_rank.isdigit():
                        ranks["CONTEXTUALIZES"] = int(cont_rank)
                dominant_function = min(ranks, key=ranks.get)
                explicit_mapping = function_attributes.get(dominant_function)
                if explicit_mapping is not None:
                    o_fill = explicit_mapping['false']['fill']
                    o_border = explicit_mapping['false']['peripheries']
                    o_style = "rounded,filled"
                    o_shape = "ellipse"  # Omitted SUPPORT nodes are ellipses.
                else:
                    o_fill = "#dae8fc"
                    o_border = "#7c9ac7"
                    o_shape = "ellipse"
                    o_style = "rounded,filled"
            else:
                continue  # Skip unrecognized element types

            # Handle based on whether count is specified
            count_attr = child.get('{http://alchemeast.eu/thesu/ns/1.0}number')
            if count_attr and count_attr.isdigit():
                # Case 2a: Specified number of omitted elements
                count = int(count_attr)
                for i in range(count):
                    # Create node ID
                    pseudo_node_id = generate_unique_pseudo_node_id_targets(
                        written_lines, element_id, f"omitted_TARGET_{display_type}", i+1
                    )
                    
                    # Create the node
                    label = f"<b>{display_type}</b><br/><i>(omitted)</i>"
                    source_attr = f', source="{source_id}"' if source_id else ''
                    node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="{display_type[:4]}", '
                                 f'gephi_omitted="true", fontsize="11", fillcolor="{o_fill}", '
                                 f'color="{o_border}", style="{o_style}", shape="{o_shape}"{source_attr}];\n\n')
                    dot_file.write(node_line)
                    written_lines.append(node_line)
                    
                    # Ensure function node exists
                    if func_node_id is None:
                        func_node_id = f"{element_id}_func"
                        line_to_write = (f'"{func_node_id}" [label="{function}", gephi_label="{t_gephi_label}", '
                                        f'gephi_omitted="false", fontsize="11", fillcolor="{support_fill}", '
                                        f'color="{support_border}", style="{support_style}", shape="ellipse"];\n\n')
                        dot_file.write(line_to_write)
                        written_lines.append(line_to_write)
                        # Connect SUPPORT to function node
                        line_to_write = f'"{element_id}" -> "{func_node_id}" [dir=none, color="{support_border}", style="{support_style}"];\n\n'
                        dot_file.write(line_to_write)
                        written_lines.append(line_to_write)
                    
                    # Connect function node to omitted element with proper color
                    line_to_write = f'"{func_node_id}" -> "{pseudo_node_id}" [color="{t_border}", style="{implicit_style}"];\n\n'
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
            else:
                # Case 2b: Unspecified number of omitted elements
                # Create node ID
                pseudo_node_id = generate_unique_pseudo_node_id_targets(
                    written_lines, element_id, f"omitted_TARGET_{display_type}", "unspecified"
                )
                
                # Create the node
                label = f"<b>{display_type}</b><br/><i>(omitted,<br/>one or more)</i>"
                o_style = "dotted,filled"  # Dotted for unspecified quantity
                source_attr = f', source="{source_id}"' if source_id else ''
                node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="{display_type[:4]}", '
                             f'gephi_omitted="true", gephi_unspecified="true", fontsize="11", '
                             f'fillcolor="{o_fill}", color="{o_border}", style="{o_style}", '
                             f'shape="{o_shape}"{source_attr}];\n\n')
                dot_file.write(node_line)
                written_lines.append(node_line)
                
                # Ensure function node exists
                if func_node_id is None:
                    func_node_id = f"{element_id}_func"
                    line_to_write = (f'"{func_node_id}" [label="{function}", gephi_label="{t_gephi_label}", '
                                    f'gephi_omitted="false", fontsize="11", fillcolor="{support_fill}", '
                                    f'color="{support_border}", style="{support_style}", shape="ellipse"];\n\n')
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
                    # Connect SUPPORT to function node
                    line_to_write = f'"{element_id}" -> "{func_node_id}" [dir=none, color="{support_border}", style="{support_style}"];\n\n'
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
                
                # Connect function node to omitted element with proper color
                line_to_write = f'"{func_node_id}" -> "{pseudo_node_id}" [color="{t_border}", style="{implicit_style}"];\n\n'
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
    
    return func_node_id, processed_propositions

def process_employed_elements(element, element_id, function_attributes, 
                             namespaces, dot_file, written_lines, employed_node_id, processed_propositions, source_id=None):
    """
    Process employed elements (things used within the SUPPORT).
    
    This creates employed nodes and connects them to the SUPPORT.
    This is completely separate from the target processing.
    """
    
    # Process employed elements - This section needs to be preserved to maintain employed elements functionality
    for employed_element in element.findall('.//thesu:employedElements/thesu:elementRef', namespaces=namespaces):
        employed_element_ref = employed_element.get('{http://alchemeast.eu/thesu/ns/1.0}ref').split('#')[-1]
        if employed_node_id is None:
            employed_node_id = f"{element_id}_employed"
            # Create the common employed pseudo-node with fixed styling:
            line_to_write = (f'"{employed_node_id}" [label="EMPLOYED IN", gephi_label="in", fontsize="11", '
                             f'fillcolor="#ffe6cc", color="#d79c02", gephi_omitted="false", shape="ellipse", style="filled"];\n\n')
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
            # Instead of connecting SUPPORT -> employed node, we now connect employed node -> SUPPORT
            # (to force vertical ordering)
            line_to_write = f'"{employed_node_id}" -> "{element_id}" [color="#d79c02", style="solid"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
        # Connect explicit employed element to the common employed node:
        line_to_write = f'"{employed_element_ref}" -> "{employed_node_id}" [dir=none, color="#d79c02", style="solid"];\n\n'
        dot_file.write(line_to_write)
        written_lines.append(line_to_write)
    
    # Process omitted employed elements
    for omitted_employed_elem in element.findall('.//thesu:employedElements/thesu:omittedEmployedElements', namespaces=namespaces):
        # Check if this is an empty omittedEmployedElements tag (no children)
        if len(list(omitted_employed_elem)) == 0:
            # Handle completely unspecified omitted employed elements
            pseudo_node_id = generate_unique_pseudo_node_id_targets(written_lines, element_id, "omitted_ELEMENTS", "unspecified")
            
            # Light gray color for unspecified elements
            o_fill = "#f5f5f5"  # Very light gray
            o_border = "#a0a0a0"  # Medium gray for border
            o_shape = "box"     # Match thesis shape but with rounded corners
            o_style = "dotted,filled,rounded"  # Dotted for vagueness
            
            label = f"<b>ELEMENTS</b><br/><i>(unspecified,<br/>omitted,<br/>one or more)</i>"
            
            source_attr = f', source="{source_id}"' if source_id else ''
            node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="ELEM", '
                         f'gephi_omitted="true", gephi_unspecified="true", fontsize="11", fillcolor="{o_fill}", '
                         f'color="{o_border}", style="{o_style}", shape="{o_shape}"{source_attr}];\n\n')
            dot_file.write(node_line)
            written_lines.append(node_line)
            
            # Create employed node if needed
            if employed_node_id is None:
                employed_node_id = f"{element_id}_employed"
                # Create the common employed pseudo-node with fixed styling:
                line_to_write = (f'"{employed_node_id}" [label="EMPLOYED IN", gephi_label="in", fontsize="11", '
                                f'fillcolor="#ffe6cc", color="#d79c02", gephi_omitted="false", shape="ellipse", style="filled"];\n\n')
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
                # Connect employed node to SUPPORT
                line_to_write = f'"{employed_node_id}" -> "{element_id}" [color="#d79c02", style="solid"];\n\n'
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
            # Edge from omitted node to the common employed node:
            line_to_write = f'"{pseudo_node_id}" -> "{employed_node_id}" [dir=none, color="#d79c02", style="solid"];\n\n'
            dot_file.write(line_to_write)
            written_lines.append(line_to_write)
            continue
        
        # Handle specified omitted employed elements 
        for child in omitted_employed_elem:
            local_name = child.tag.split('}')[-1]  # e.g. omittedTHESES, omittedMISCS, omittedSUPPORTS
            if local_name == "omittedTHESES":
                display_type = "THESIS"
                # Use explicit THESIS styling:
                o_fill = "#f0faf0"       # Explicit THESIS fill color
                o_border = "#82b366"     # Explicit THESIS border
                o_shape = "box"          # THESIS shape (assumed box)
                o_style = "rounded,filled"
            elif local_name == "omittedMISCS":
                display_type = "MISC"
                # MISCs styled like explicit CONTEXTUALIZES:
                o_fill = "#ecd4bb"       # Explicit CONTEXTUALIZES fill
                o_border = "#b39c84"     # Explicit CONTEXTUALIZES border
                o_shape = "cylinder"     # CONTEXTUALIZES shape
                o_style = "filled"
            elif local_name == "omittedSUPPORTS":
                display_type = "SUPPORT"
                # For omitted SUPPORTS, use omittedSupportsFunctions if available:
                func_elem = child.find('.//thesu:omittedSupportsFunctions', namespaces=namespaces)
                # Default: all functions rank 4
                ranks = {"JUSTIFIES": 4, "EXPLAINS": 4, "EXPANDS ON": 4, "CONTEXTUALIZES": 4}
                if func_elem is not None:
                    arg_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedArgumentationRank')
                    exp_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedExpositionRank')
                    expa_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedExpansionRank')
                    cont_rank = func_elem.get('{http://alchemeast.eu/thesu/ns/1.0}omittedContextualisationRank')
                    if arg_rank and arg_rank.isdigit():
                        ranks["JUSTIFIES"] = int(arg_rank)
                    if exp_rank and exp_rank.isdigit():
                        ranks["EXPLAINS"] = int(exp_rank)
                    if expa_rank and expa_rank.isdigit():
                        ranks["EXPANDS ON"] = int(expa_rank)
                    if cont_rank and cont_rank.isdigit():
                        ranks["CONTEXTUALIZES"] = int(cont_rank)
                dominant_function = min(ranks, key=ranks.get)
                explicit_mapping = function_attributes.get(dominant_function)
                if explicit_mapping is not None:
                    o_fill = explicit_mapping['false']['fill']
                    o_border = explicit_mapping['false']['peripheries']
                    o_style = "rounded,filled"
                    o_shape = "ellipse"  # For omitted SUPPORT nodes, force elliptical shape:
                else:
                    o_fill = "#dae8fc"
                    o_border = "#7c9ac7"
                    o_shape = "ellipse"
                    o_style = "rounded,filled"
            else:
                continue

            count_attr = child.get('{http://alchemeast.eu/thesu/ns/1.0}number')
            if count_attr and count_attr.isdigit():
                # Specified number of omitted elements
                count = int(count_attr)
                for i in range(count):
                    pseudo_node_id = generate_unique_pseudo_node_id_targets(written_lines, element_id, f"omitted_{display_type}", i+1)
                    label = f"<b>{display_type}</b><br/><i>(omitted)</i>"
                    source_attr = f', source="{source_id}"' if source_id else ''
                    node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="{display_type[:4]}", '
                                 f'gephi_omitted="true", fontsize="11", fillcolor="{o_fill}", '
                                 f'color="{o_border}", style="{o_style}", shape="{o_shape}"{source_attr}];\n\n')
                    dot_file.write(node_line)
                    written_lines.append(node_line)
                    
                    # Ensure employed node exists
                    if employed_node_id is None:
                        employed_node_id = f"{element_id}_employed"
                        # Create the common employed pseudo-node with fixed styling:
                        line_to_write = (f'"{employed_node_id}" [label="EMPLOYED IN", gephi_label="in", fontsize="11", '
                                        f'fillcolor="#ffe6cc", color="#d79c02", gephi_omitted="false", shape="ellipse", style="filled"];\n\n')
                        dot_file.write(line_to_write)
                        written_lines.append(line_to_write)
                        # Connect employed node to SUPPORT
                        line_to_write = f'"{employed_node_id}" -> "{element_id}" [color="#d79c02", style="solid"];\n\n'
                        dot_file.write(line_to_write)
                        written_lines.append(line_to_write)
                    
                    # Connect omitted element to employed node
                    line_to_write = f'"{pseudo_node_id}" -> "{employed_node_id}" [dir=none, color="#d79c02", style="solid"];\n\n'
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
            else:
                # Unspecified number of omitted elements
                pseudo_node_id = generate_unique_pseudo_node_id_targets(written_lines, element_id, f"omitted_{display_type}", "unspecified")
                label = f"<b>{display_type}</b><br/><i>(omitted,<br/>one or more)</i>"
                # Use dotted style to indicate unspecified quantity (communicates vagueness)
                o_style = "dotted,filled"
                source_attr = f', source="{source_id}"' if source_id else ''
                node_line = (f'"{pseudo_node_id}" [label=<{label}>, gephi_label="{display_type[:4]}", '
                             f'gephi_omitted="true", gephi_unspecified="true", fontsize="11", fillcolor="{o_fill}", '
                             f'color="{o_border}", style="{o_style}", shape="{o_shape}"{source_attr}];\n\n')
                dot_file.write(node_line)
                written_lines.append(node_line)
                
                # Ensure employed node exists
                if employed_node_id is None:
                    employed_node_id = f"{element_id}_employed"
                    # Create the common employed pseudo-node with fixed styling:
                    line_to_write = (f'"{employed_node_id}" [label="EMPLOYED IN", gephi_label="in", fontsize="11", '
                                    f'fillcolor="#ffe6cc", color="#d79c02", gephi_omitted="false", shape="ellipse", style="filled"];\n\n')
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
                    # Connect employed node to SUPPORT
                    line_to_write = f'"{employed_node_id}" -> "{element_id}" [color="#d79c02", style="solid"];\n\n'
                    dot_file.write(line_to_write)
                    written_lines.append(line_to_write)
                
                # Connect omitted element to employed node
                line_to_write = f'"{pseudo_node_id}" -> "{employed_node_id}" [dir=none, color="#d79c02", style="solid"];\n\n'
                dot_file.write(line_to_write)
                written_lines.append(line_to_write)
    
    return employed_node_id, processed_propositions

def process_support_element(element, element_type, namespaces, dot_file, written_lines, retrieved_text, retrieved_text_snippet, locus, processed_propositions, source_id=None):
    """
    Process a SUPPORT element, handling its targets and employed elements.
    
    This function:
    1. Extracts styling info based on the SUPPORT's function
    2. Delegates target and employed element processing to specialized functions
    3. Creates the SUPPORT node itself
    """
    
    element_id = element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
    if element_id is None:
        element_id = element.get('{http://www.w3.org/XML/1998/namespace}id')
    
    # --- Initialize node IDs and styling variables ---
    func_node_id = None

    # Default values for target styling (to be updated based on function)
    t_gephi_label = "tar"  # Default value
    t_fill = "#ffffff"     # Default value
    t_border = "#000000"   # Default value
    t_shape = "ellipse"    # Default value
    
    # Default values for support styling (to be updated based on function)
    support_fill = "#dae8fc"  # Default value
    support_border = "#7c9ac7"  # Default value
    support_style = "filled"   # Default value
    support_shape = "ellipse"  # Default value
    
    # --- Process basic element info ---
    
    # Get all speakers from speakersGroup
    speaker_elements = element.findall('.//thesu:speakersGroup/thesu:speaker', namespaces=namespaces)
    
    # Process speakers according to rank
    element_speaker = ""
    if speaker_elements:
        # Get rank for each speaker (default is 1 if not specified)
        speakers_with_rank = []
        for spk in speaker_elements:
            name_val = spk.get('{http://alchemeast.eu/thesu/ns/1.0}name')
            if name_val:
                speaker_name = name_val.split('#')[-1]
                rank_val = spk.get('{http://alchemeast.eu/thesu/ns/1.0}rank')
                rank = int(rank_val) if rank_val and rank_val.isdigit() else 1
                speakers_with_rank.append((speaker_name, rank))
        
        if speakers_with_rank:
            # Find minimum rank (highest priority)
            min_rank = min(rank for _, rank in speakers_with_rank)
            
            # Get all speakers with this highest priority rank
            top_speakers = [name for name, rank in speakers_with_rank if rank == min_rank]
            
            # Join speaker names with commas
            element_speaker = ", ".join(top_speakers)
    
    # Get paraphrasis
    paraphrasis_elem = element.find("./thesu:paraphrasis", namespaces=namespaces)
    if paraphrasis_elem is not None:
        paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
        paraphrasis = re.sub(r'\s+', ' ', paraphrasis)
        paraphrasis = re.sub(r'(.{1,50})(?:\s|$)', r'\1<br/>', paraphrasis)
        paraphrasis = paraphrasis.replace('"', r'\"')
    else:
        paraphrasis = "/"
    
    # Get support function and form
    function, aim = get_function_and_aim(element, namespaces)
    form_elem = element.find('.//thesu:supportType/thesu:supportForm[1]', namespaces=namespaces)
    if form_elem is not None:
        formTag = form_elem.get('{http://alchemeast.eu/thesu/ns/1.0}formTag')
        form = formTag.split('#')[-1] if formTag else None
    else:
        form = None
    
    # --- Determine styling based on function ---
    
    # Check implicit and extrinsic status
    extrinsic_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}extrinsic')
    implicit_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}implicit')
    
    if extrinsic_att == "true":
        implicit_style = "dashed,filled"
        element_type_label = f"extr. {element_type}"
        manifestation = "extrinsic"
        implicit_att = "true"
    elif implicit_att == "true":
        implicit_style = "dashed,filled"
        element_type_label = f"impl. {element_type}"
        manifestation = "implicit"
    else:
        implicit_style = "filled"
        element_type_label = f"{element_type}"
        manifestation = "explicit"
        implicit_att = "false"
    
    # Function attribute mappings for styling
    function_attributes = {
        'JUSTIFIES': {'false': {'gephi_label':'jus','fill': '#dae8fc', 'peripheries': '#7c9ac7', 'shape': 'diamond'},
                      'true':  {'gephi_label':'(jus)','fill': '#f5f8fd', 'peripheries': '#949ebf', 'shape': 'diamond'}},
        'REFUTES': {'false': {'gephi_label':'ref','fill': '#f8cecc', 'peripheries': '#b95753', 'shape': 'diamond'},
                    'true':  {'gephi_label':'(ref)','fill': '#fdf6f6', 'peripheries': '#a89794', 'shape': 'diamond'}},
        'DISCUSSES': {'false': {'gephi_label':'dis','fill': '#ffff99', 'peripheries': '#b3b300', 'shape': 'diamond'},
                      'true':  {'gephi_label':'(dis)','fill': '#ffffe6', 'peripheries': '#999966', 'shape': 'diamond'}},
        'EXPLAINS': {'false': {'gephi_label':'exp','fill': '#edffc4', 'peripheries': '#927b89', 'shape': 'parallelogram'},
                     'true':  {'gephi_label':'(exp)','fill': '#f9facb', 'peripheries': '#a59ba1', 'shape': 'parallelogram'}},
        'EXPANDS ON': {'false': {'gephi_label':'exc','fill': '#999999', 'peripheries': '#4d4d4d', 'shape': 'invhouse'},
                       'true':  {'gephi_label':'(exc)','fill': '#cccccc', 'peripheries': '#828282', 'shape': 'invhouse'}},
        'CONTEXTUALIZES': {'false': {'gephi_label':'con','fill': '#ecd4bb', 'peripheries': '#b39c84', 'shape': 'cylinder'},
                           'true':  {'gephi_label':'(con)','fill': '#f6ede6', 'peripheries': '#b3a89a', 'shape': 'cylinder'}}
    }
    
    # --- Compute styling for the SUPPORT node ---
    support_attr = function_attributes.get(function)
    if support_attr is not None:
        support_fill = support_attr[implicit_att]['fill']
        support_border = support_attr[implicit_att]['peripheries']
        support_shape = "ellipse"  # For the SUPPORT node itself
        support_style = implicit_style
    else:
        support_fill = "#f0faf0"
        support_border = "#82b366"
        support_shape = "ellipse"
        support_style = implicit_style

    # --- CRITICAL: Compute target styling BEFORE processing targets ---
    # This ensures the proper blue color (t_border) is used for connections
    function_attribute = function_attributes.get(function)
    if function_attribute is not None:
        t_gephi_label = function_attribute[implicit_att]['gephi_label']
        t_fill = function_attribute[implicit_att]['fill']
        t_border = function_attribute[implicit_att]['peripheries']  # Blue color for target edges comes from here!
        t_shape = function_attribute[implicit_att]['shape']
    else:
        t_gephi_label = "tar"
        t_fill = "#ffffff"
        t_border = "#000000"
        t_shape = "ellipse"
    
    # --- Process targets and employed elements using the specialized functions ---
    
    result = process_support_targets(
        element, function, implicit_att, implicit_style, function_attributes,
        t_gephi_label, support_fill, support_border, support_style,
        t_fill, t_border, t_shape,  # <-- Pass explicit target styling with correct t_border
        namespaces, dot_file, written_lines, element_id, processed_propositions, source_id
    )

    
    # Unpack the result
    func_node_id, written_lines, processed_propositions = result

    # Add source_id attribute if available
    source_attr = f', source="{source_id}"' if source_id else ''

    # Write the SUPPORT node itself with its styling
    support_node_str = (
        f'"{element_id}" [label=<<b>{element_type_label}</b><br/>{pad_short_string(element_speaker, 30)}'
        f'<br/>{locus}<br/><i>form: {"unspecified" if form is None else form}</i>'
        f'<br/><font point-size="12">"{retrieved_text_snippet}"</font>>, '
        f'gephi_label="{element_type[:4]}", '
        f'text="{retrieved_text}", '
        f'locus="{locus.replace(" (of ", "_").replace(")", "").replace("<i>", "").replace("</i>", "")}", '
        f'speaker="{element_speaker.strip()}", '
        f'form="{form}", '
        f'paraphrasis="{paraphrasis.replace("<br/>", " ")}", '
        f'manifestation="{manifestation}", '
        f'fillcolor="{support_fill}", '
        f'color="{support_border}", '
        f'style="{support_style}", '
        f'shape="{support_shape}", '
        f'margin="0.05,0.02"'
        f'{source_attr}];\n\n'
    )

    dot_file.write(support_node_str)
    
    return written_lines, processed_propositions
