"""XML tree queries and element selection.

Key functions: get_all_proposition_ids, filter_elements, find_parent_thesis, find_common_ancestor
"""
from bootstrap.delayed_imports import ET


def get_all_proposition_ids(elements, namespaces):
    """Collect all proposition IDs referenced in matchingProposition elements within the given elements."""
    proposition_ids = set()
    for element in elements:
        matching_propositions_group = element.find('./thesu:matchingPropositionsGroup', namespaces=namespaces)
        if matching_propositions_group is not None:
            matching_propositions = matching_propositions_group.findall('.//thesu:matchingProposition', namespaces=namespaces)
            for matching_proposition in matching_propositions:
                prop_ref = matching_proposition.get('{http://alchemeast.eu/thesu/ns/1.0}propRef').split('#')[-1]
                proposition_ids.add(prop_ref)
    return proposition_ids

def filter_elements(elements, namespaces):
    """Return only THESIS, SUPPORT, and MISC elements from the given list."""
    return [element for element in elements if element.tag in ('{http://alchemeast.eu/thesu/ns/1.0}THESIS', '{http://alchemeast.eu/thesu/ns/1.0}SUPPORT', '{http://alchemeast.eu/thesu/ns/1.0}MISC')]

def find_parent_thesis(element, namespaces):
    """Traverses up the tree to find the first ancestor THESIS element."""
    ancestor = element.getparent()
    while ancestor is not None:
        # Using ET.QName for reliable namespace comparison
        if ancestor.tag == ET.QName(namespaces['thesu'], 'THESIS'):
            return ancestor
        ancestor = ancestor.getparent()
    return None

def find_common_ancestor(elem1, elem2):
    """Find the common ancestor of two elements."""
    ancestors1 = [elem1] + list(elem1.iterancestors())
    ancestors2 = [elem2] + list(elem2.iterancestors())
    
    for ancestor in ancestors1:
        if ancestor in ancestors2:
            return ancestor
    
    return None
