"""Text utility functions.

Key function: pad_short_string
"""


def pad_short_string(s, width, pad_char=' '):
    """Center-pad string s to width characters using pad_char. Returns s unchanged if len(s) >= width."""
    padding = width - len(s)
    left_padding = padding // 2
    right_padding = padding - left_padding
    return pad_char * left_padding + s + pad_char * right_padding
