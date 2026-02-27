"""
Color conversion utilities for Gephi.
"""
import webcolors

from config.runtime_settings import color_mapping


def hex_to_closest_color(match):
    """Converts a HEX color code to the closest HTML color name."""
    hex_code = match.group(1)
    try:
        # Convert hex to RGB
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        
        closest_color = closest_web_color((r, g, b))
        # Apply custom mapping if the color is problematic
        return color_mapping.get(closest_color, closest_color)
    except Exception as e:
        print(f"Warning: Error converting color {hex_code}: {e}")
        return "black"  # Safe fallback


def closest_web_color(rgb_color):
    """Find the closest web color name to the given RGB values."""
    try:
        # Try newer webcolors API first
        try:
            color_names = webcolors.names("css3")
            min_colors = {}
            for name in color_names:
                r_c, g_c, b_c = webcolors.name_to_rgb(name)
                rd = (r_c - rgb_color[0]) ** 2
                gd = (g_c - rgb_color[1]) ** 2
                bd = (b_c - rgb_color[2]) ** 2
                min_colors[(rd + gd + bd)] = name
            return min_colors[min(min_colors.keys())]
        except AttributeError:
            # Fall back to older API
            color_dict = webcolors.names("css3")
            min_colors = {}
            for hex_val, name in color_dict.items():
                r_c, g_c, b_c = webcolors.hex_to_rgb(hex_val)
                rd = (r_c - rgb_color[0]) ** 2
                gd = (g_c - rgb_color[1]) ** 2
                bd = (b_c - rgb_color[2]) ** 2
                min_colors[(rd + gd + bd)] = name
            return min_colors[min(min_colors.keys())]
    except Exception as e:
        print(f"Warning: Error finding closest web color: {e}")
        return "black"  # Safe fallback

