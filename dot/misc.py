"""Misc element DOT building functions.

Key function: process_misc_element
"""
from bootstrap.primary_imports import re
from xml_processing.extractors import extract_paraphrasis_text
from utils.text import pad_short_string

def process_misc_element(element, namespaces, dot_file, written_lines, retrieved_text, retrieved_text_snippet, locus, processed_propositions, source_id=None):
    """Process a MISC element: write its DOT node with speaker, locus, paraphrasis, and styling."""
    element_id = element.get('{http://alchemeast.eu/thesu/ns/1.0}id')
    if element_id is None:
        element_id = element.get('{http://www.w3.org/XML/1998/namespace}id')

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
    
    # Get paraphrasis text; if missing, default to "/"
    paraphrasis_elem = element.find("./thesu:paraphrasis", namespaces=namespaces)
    if paraphrasis_elem is not None:
        paraphrasis = extract_paraphrasis_text(paraphrasis_elem)
        if paraphrasis is not None: 
            paraphrasis = re.sub(r'\s+', ' ', paraphrasis)
            paraphrasis = re.sub(r'(.{1,50})(?:\s|$)', r'\1<br/>', paraphrasis)
            paraphrasis = paraphrasis.replace('"', r'\"')
        else:
            paraphrasis = "/"
    else:
        paraphrasis = "/"
    
    # Check extrinsic and implicit status
    extrinsic_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}extrinsic')
    implicit_att = element.get('{http://alchemeast.eu/thesu/ns/1.0}implicit')
    
    if extrinsic_att == "true":
        misc_fill = "#f6ede6"
        misc_border = "#b3a89a"
        misc_style = "dashed,filled"
        manifestation = "extrinsic"
        element_type_label = "extr. MISC"
    elif implicit_att == "true":
        misc_fill = "#f6ede6"
        misc_border = "#b3a89a"
        misc_style = "dashed,filled"
        manifestation = "implicit"
        element_type_label = "impl. MISC"
    else:
        misc_fill = "#ecd4bb"
        misc_border = "#b39c84"
        misc_style = "filled"
        manifestation = "explicit"
        element_type_label = "MISC"
    
    # Common styling for all MISC nodes
    misc_shape = "cylinder"
    
    # Add source_id attribute if available
    source_attr = f', source="{source_id}"' if source_id else ''
    
    # Build the DOT node label with improved formatting
    line_to_write = (
        f'"{element_id}" [label=<<br/><b>{element_type_label}</b><br/>'
        f'{pad_short_string(element_speaker, 30)}<br/>'
        f'{locus}<br/>'
        f'<i>{paraphrasis}</i><br/>'
        f'<font point-size="12">"{retrieved_text_snippet}"</font>>, '
        f'gephi_label="MISC", '
        f'text="{retrieved_text}", '
        f'locus="{locus.replace(" (of ", "_").replace(")", "").replace("<i>", "").replace("</i>", "")}", '
        f'speaker="{element_speaker.strip()}", '
        f'manifestation="{manifestation}"'
        f'{source_attr}, '
        f'fillcolor="{misc_fill}", '
        f'color="{misc_border}", '
        f'style="{misc_style}", '
        f'shape="{misc_shape}", '
        f'margin="0.30,0.1"];\n\n'
    )

    dot_file.write(line_to_write)
    written_lines.append(line_to_write)
    return written_lines, processed_propositions
