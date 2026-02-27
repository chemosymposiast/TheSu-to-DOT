"""DOT graph header writing.

Key function: write_dot_file_header
"""


def write_dot_file_header(dot_file):
    """Write the standard DOT graph header (digraph declaration and layout options) to the given file."""
    dot_file.write('digraph G {\n')
    dot_file.write('compound=true;\n\n')
    dot_file.write('newrank=true;\n\n')
    dot_file.write('rankdir="TB";\n\n')
    dot_file.write('splines=curved;\n\n')
