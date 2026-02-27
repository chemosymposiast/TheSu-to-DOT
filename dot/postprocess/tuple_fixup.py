"""
Tuple-like node ID fixup for DOT files.
Fixes node IDs that were mistakenly written as Python tuple structures.
"""
from bootstrap.primary_imports import re, shutil


def fix_tuple_node_ids(dot_filename, output_dot_filename=None):
    """
    Post-process a DOT file to fix any tuple-like node IDs that were mistakenly written.
    This is particularly targeting issues where complex Python data structures like
    tuples with function IDs and proposition sets are directly written to the DOT file.
    
    Args:
        dot_filename: The path to the DOT file to fix
        output_dot_filename: Optional, the path to save the fixed DOT file.
                            If None, overwrites the original file.
    """
    if output_dot_filename is None:
        output_dot_filename = dot_filename
        
    # Create a temporary file for the fixed content
    temp_filename = dot_filename + '.temp'
    
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add debugging to find all occurrences of tuple node IDs
    tuple_pattern = r'"(\([\'"]([^\'"]+)[\'"], \{[^\}]+\}\))"'
    matches = re.findall(tuple_pattern, content)
    
    # Print detailed information about each match
    if matches:
        for i, match in enumerate(matches):
            print(f"  Match {i+1}: Full pattern: '{match[0]}', Node ID: '{match[1]}'")
    else:
        print("DEBUG: No tuple node IDs found that need fixing")
    
    # Fix tuple-like node IDs using regex replacement
    # This specifically targets the pattern '(' + function_id + ', {' + proposition_ids + '})'
    fixed_content = re.sub(tuple_pattern, r'"\2"', content)
    
    with open(temp_filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Move the temp file to the output file
    shutil.move(temp_filename, output_dot_filename)
    print(f"Fixed tuple node IDs in {dot_filename} and saved to {output_dot_filename}")


def detect_and_fix_tuple_node_ids(dot_filename, output_dot_filename=None):
    """
    Examines a DOT file for tuple-like node IDs and provides warnings and fixes.
    
    This is particularly targeting issues where complex Python data structures like
    tuples with function IDs and proposition sets are directly written to the DOT file.
    When detected, it provides detailed warnings to help developers fix the root cause.
    
    Args:
        dot_filename: The path to the DOT file to examine
        output_dot_filename: Optional, the path to save the fixed DOT file.
                            If None, overwrites the original file.
    """
    if output_dot_filename is None:
        output_dot_filename = dot_filename
        
    # Create a temporary file for the fixed content
    temp_filename = dot_filename + '.temp'
    
    with open(dot_filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add detailed warning diagnostics for tuple node IDs
    tuple_pattern = r'"(\([\'"]([^\'"]+)[\'"], \{[^\}]+\}\))"'
    matches = re.findall(tuple_pattern, content)
    
    # Print detailed warnings when tuples are found
    if matches:
        print("\n" + "="*80)
        print("WARNING: Found tuple-structured node IDs in the DOT file!")
        print("These indicate a potential code issue where Python tuples are being used as node IDs.")
        print("="*80)
        
        for i, match in enumerate(matches):
            print(f"\nTuple {i+1}:")
            print(f"  Full tuple pattern: '{match[0]}'")
            print(f"  Function node ID component: '{match[1]}'")
            print(f"  Will be simplified to: '{match[1]}'")
            print("  --> This suggests a bug where a tuple is being passed instead of a string.")
            print("      Check any code that modifies or returns func_node_id values.")
        
        print("\nThe DOT file will be fixed automatically, but the code should be revised to prevent")
        print("this issue from recurring. Look for places where func_node_id values might be combined")
        print("with other data structures like sets or dicts in return values.")
        print("="*80 + "\n")
    
    # Fix tuple-like node IDs using regex replacement
    # This specifically targets the pattern '(' + function_id + ', {' + proposition_ids + '})'
    fixed_content = re.sub(tuple_pattern, r'"\2"', content)
    
    with open(temp_filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Move the temp file to the output file
    shutil.move(temp_filename, output_dot_filename)
    
    if matches:
        print(f"Fixed {len(matches)} tuple node IDs in {dot_filename} and saved to {output_dot_filename}")
