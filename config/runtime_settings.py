"""Runtime settings: paths, filter toggles, layout options, and constants.

All user-editable settings are loaded from settings_user.toml in the script root.
Key globals: BASE_DIR, OUTPUT_DIR, xml_name, sources_to_select, filter_*,
DEFAULT_ENGINE, LAYOUT_SETTINGS, XML_NAMESPACE, xml_filename, dot_filename, etc.
"""
from bootstrap.primary_imports import os

# Resolved relative to this config module so it works regardless of cwd.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)  # config -> project root

# TOML parser: use built-in tomllib (Python 3.11+) or tomli for older Python
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _normalize_id(s):
    """Strip leading # from IDs; return string."""
    if not isinstance(s, str):
        return str(s)
    return s.lstrip("#")


def _normalize_id_list(lst):
    """Ensure list contains strings, normalized."""
    if lst is None:
        return []
    return [_normalize_id(x) for x in lst if x]


def _normalize_prop_filters(d):
    """Convert dict to {prop_id: [thesis_ids]} with normalized IDs."""
    if not d or not isinstance(d, dict):
        return {}
    out = {}
    for k, v in d.items():
        key = _normalize_id(str(k))
        out[key] = _normalize_id_list(v) if isinstance(v, (list, tuple)) else []
    return out


def _resolve_path(path_str, base):
    """Resolve path: if relative, join with base; if absolute, use as-is."""
    if not path_str or not isinstance(path_str, str):
        return None
    path_str = path_str.strip()
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(base, path_str)


def _load_user_settings():
    """Load and validate settings from settings_user.toml. Returns merged config dict."""
    defaults = _get_default_settings()

    settings_path = os.path.join(_PROJECT_ROOT, "settings_user.toml")
    if not os.path.isfile(settings_path):
        return defaults

    if tomllib is None:
        raise ImportError(
            "Cannot load settings_user.toml: no TOML parser available. "
            "Use Python 3.11+ or install: pip install tomli"
        )

    try:
        with open(settings_path, "rb") as f:
            raw = tomllib.load(f)
    except Exception as e:
        raise ValueError(
            f"Error reading settings_user.toml: {e}\n"
            f"Check the file for syntax errors (e.g. missing quotes, wrong brackets)."
        ) from e

    # Merge paths
    paths = raw.get("paths") or {}
    if isinstance(paths, dict):
        for k, v in paths.items():
            if v is not None:
                defaults["paths"][k] = v

    # Merge filters
    filters = raw.get("filters") or {}
    if isinstance(filters, dict):
        for k in ("sources_to_select", "thesis_focus_id", "elements_to_exclude",
                  "filter_propositions", "filter_matching_proposition_sequences",
                  "filter_all_sequences", "filter_extrinsic_elements"):
            if k in filters and filters[k] is not None:
                v = filters[k]
                if k in ("filter_propositions", "filter_matching_proposition_sequences",
                         "filter_all_sequences", "filter_extrinsic_elements"):
                    defaults["filters"][k] = bool(v)
                else:
                    defaults["filters"][k] = [str(x) for x in v] if isinstance(v, (list, tuple)) else []

    # Custom proposition filters: [filters.custom_propositions]
    fp = raw.get("filters")
    custom_props = fp.get("custom_propositions") if isinstance(fp, dict) else {}
    defaults["custom_prop_filters"] = _normalize_prop_filters(custom_props)

    # Custom sequence filters: [filters.custom_sequences]
    custom_seqs = fp.get("custom_sequences") if isinstance(fp, dict) else {}
    defaults["custom_seq_filters"] = _normalize_prop_filters(custom_seqs)

    # Layout
    layout = raw.get("layout") or {}
    if isinstance(layout, dict):
        if "default_engine" in layout and layout["default_engine"]:
            eng = str(layout["default_engine"]).strip().lower()
            if eng not in ("dot", "fdp", "neato"):
                raise ValueError(
                    f"Invalid layout.default_engine: '{layout['default_engine']}'. "
                    f"Must be one of: dot, fdp, neato"
                )
            defaults["default_engine"] = eng

        for engine in ("dot", "fdp", "neato"):
            eng_table = layout.get(engine)
            if isinstance(eng_table, dict):
                for k, v in eng_table.items():
                    if v is not None:
                        defaults["layout"][engine][k] = v

    # Merge output settings
    output = raw.get("output") or {}
    if isinstance(output, dict):
        # Top-level output flags (booleans)
        for flag_key in ("output_svg", "output_pdf", "output_png", "open_in_browser"):
            if flag_key in output and output[flag_key] is not None:
                defaults["output"][flag_key] = bool(output[flag_key])

        # Nested per-format tables
        for fmt in ("pdf", "png"):
            fmt_table = output.get(fmt)
            if isinstance(fmt_table, dict):
                for k, v in fmt_table.items():
                    if v is not None:
                        defaults["output"][fmt][k] = v

    # Merge system settings
    system = raw.get("system") or {}
    if isinstance(system, dict) and "graphviz_path" in system and system["graphviz_path"] is not None:
        p = system["graphviz_path"]
        defaults["system"]["graphviz_path"] = str(p).strip() if p else ""

    # Merge colors (user overrides for theming)
    colors = raw.get("colors") or {}
    if isinstance(colors, dict):
        for k, v in colors.items():
            if v is not None and isinstance(v, str):
                defaults["colors"][k] = str(v).strip()

    return defaults


def _get_default_settings():
    """Return default settings (mirrors original hard-coded values)."""
    return {
        "paths": {
            "base_dir": "_thesu_inputs",
            "output_dir": "_thesu_outputs",
            "xml_name": "ancient_lead_white_Plut.",
            # Optional: separate base name for output files (DOT/SVG/PDF/PNG).
            # If not set, xml_name is used for outputs as well.
            "output_basename": None,
        },
        "filters": {
            "sources_to_select": [],
            "filter_propositions": False,
            "filter_matching_proposition_sequences": True,
            "filter_all_sequences": False,
            "filter_extrinsic_elements": False,
            "thesis_focus_id": [],
            "elements_to_exclude": [],
        },
        "custom_prop_filters": {},
        "custom_seq_filters": {},
        "default_engine": "dot",
        "layout": {
            "dot": {
                "overlap": "scalexy",
                "splines": "ortho",
                "nodesep": 0.25,
                "ranksep": 0.30,
                "outputorder": "edgesfirst",
                "concentrate": "false",
                "newrank": "true",
            },
            "fdp": {
                "overlap": "prism",
                "splines": "spline",
                "nodesep": 0.10,
                "outputorder": "edgesfirst",
                "concentrate": "true",
                "K": 0.5,
                "sep": 0.2,
                "maxiter": 2000,
                "start": "regular",
            },
            "neato": {
                "overlap": "prism",
                "splines": "spline",
                "nodesep": 0.1,
                "outputorder": "nodesfirst",
                "concentrate": "true",
                "K": 0.3,
                "sep": 0.05,
                "maxiter": 30000,
                "mode": "sgd",
                "model": "subset",
            },
        },
        "output": {
            # Per-format export toggles and viewer behaviour
            "output_svg": True,
            "output_pdf": True,
            "output_png": True,
            "open_in_browser": True,
            # Format-specific rendering settings
            "pdf": {"size": "11.7,16.5", "dpi": 300},
            "png": {"size": "11.7,16.5", "dpi": 1400, "max_warning_mb": 20.0},
        },
        "system": {"graphviz_path": ""},
        "colors": {
            "darkgray": "tan",
            "silver": "darkseagreen",
            "lightslategray": "darkolivegreen",
            "cornflowerblue": "steelblue",
            "lavender": "lightsteelblue",
            "gainsboro": "mediumaquamarine",
            "lightgray": "mediumaquamarine",
            "lightgrey": "mediumaquamarine",
            "honeydew": "palegreen",
        },
    }


def _apply_settings(cfg):
    """Apply merged config to module globals."""
    paths = cfg["paths"]
    base_dir = _resolve_path(paths.get("base_dir"), _PROJECT_ROOT)
    output_dir = _resolve_path(paths.get("output_dir"), _PROJECT_ROOT)
    if not base_dir:
        base_dir = os.path.join(_PROJECT_ROOT, "_thesu_inputs")
    if not output_dir:
        output_dir = os.path.join(_PROJECT_ROOT, "_thesu_outputs")

    xml_name_val = paths.get("xml_name") or "ancient_lead_white_Plut."
    if not isinstance(xml_name_val, str):
        xml_name_val = str(xml_name_val)

    # Optional separate base name for output files; falls back to xml_name.
    output_basename_val = paths.get("output_basename") or xml_name_val
    if not isinstance(output_basename_val, str):
        output_basename_val = str(output_basename_val)

    # Set globals
    glob = globals()
    glob["BASE_DIR"] = base_dir
    glob["OUTPUT_DIR"] = output_dir
    glob["xml_name"] = xml_name_val
    glob["OUTPUT_BASENAME"] = output_basename_val
    glob["sources_to_select"] = cfg["filters"].get("sources_to_select") or []
    glob["filter_propositions"] = cfg["filters"].get("filter_propositions", False)
    glob["filter_matching_proposition_sequences"] = cfg["filters"].get("filter_matching_proposition_sequences", True)
    glob["filter_all_sequences"] = cfg["filters"].get("filter_all_sequences", False)
    glob["filter_extrinsic_elements"] = cfg["filters"].get("filter_extrinsic_elements", False)
    glob["custom_prop_filters_to_apply"] = cfg.get("custom_prop_filters") or {}
    glob["custom_seq_phase_filters_to_apply"] = cfg.get("custom_seq_filters") or {}
    glob["thesis_focus_id"] = cfg["filters"].get("thesis_focus_id") or []
    glob["elements_to_exclude"] = cfg["filters"].get("elements_to_exclude") or []
    glob["DEFAULT_ENGINE"] = cfg.get("default_engine") or "dot"

    # Layout: GraphViz expects "true"/"false" for booleans; keep numbers as-is
    layout_cfg = cfg.get("layout") or {}
    defs = _get_default_settings()["layout"]
    LAYOUT = {}
    for engine in ("dot", "fdp", "neato"):
        eng = layout_cfg.get(engine) or {}
        merged = dict(defs.get(engine, {}))
        for k, v in eng.items():
            if v is not None:
                merged[k] = "true" if v is True else ("false" if v is False else v)
        LAYOUT[engine] = merged
    glob["LAYOUT_SETTINGS"] = LAYOUT

    # Output settings for export formats and viewer behaviour
    output_cfg = cfg.get("output") or {}
    defs_out = _get_default_settings().get("output", {})
    pdf_out = dict(defs_out.get("pdf", {}))
    pdf_out.update(output_cfg.get("pdf") or {})
    png_out = dict(defs_out.get("png", {}))
    png_out.update(output_cfg.get("png") or {})
    glob["PDF_OUTPUT_SETTINGS"] = {"size": str(pdf_out.get("size", "11.7,16.5")), "dpi": int(pdf_out.get("dpi", 300))}
    glob["PNG_OUTPUT_SETTINGS"] = {
        "size": str(png_out.get("size", "11.7,16.5")),
        "dpi": int(png_out.get("dpi", 1400)),
        "max_warning_mb": float(png_out.get("max_warning_mb", 20.0)),
    }
    glob["OUTPUT_SVG"] = bool(output_cfg.get("output_svg", defs_out.get("output_svg", True)))
    glob["OUTPUT_PDF"] = bool(output_cfg.get("output_pdf", defs_out.get("output_pdf", True)))
    glob["OUTPUT_PNG"] = bool(output_cfg.get("output_png", defs_out.get("output_png", True)))
    glob["OPEN_IN_BROWSER"] = bool(output_cfg.get("open_in_browser", defs_out.get("open_in_browser", True)))

    # System settings
    system_cfg = cfg.get("system") or {}
    glob["GRAPHVIZ_PATH"] = (system_cfg.get("graphviz_path") or "").strip()

    # Color mapping (for theming)
    colors_cfg = cfg.get("colors") or {}
    defs_colors = _get_default_settings().get("colors", {})
    color_mapping = dict(defs_colors)
    color_mapping.update({k: str(v) for k, v in colors_cfg.items() if v})
    glob["color_mapping"] = color_mapping

    # Derived paths
    glob["xml_filename"] = os.path.join(BASE_DIR, xml_name_val + ".xml")
    glob["xml_schema"] = os.path.join(BASE_DIR, "TheSu.xsd")
    glob["dot_filename"] = os.path.join(OUTPUT_DIR, output_basename_val + ".dot")
    glob["svg_filename"] = os.path.join(OUTPUT_DIR, output_basename_val)
    glob["pdf_filename"] = os.path.join(OUTPUT_DIR, output_basename_val)
    glob["png_filename"] = os.path.join(OUTPUT_DIR, output_basename_val)

    os.makedirs(OUTPUT_DIR, exist_ok=True)


# Load settings on import
_cfg = _load_user_settings()
_apply_settings(_cfg)

# Constants (not user-editable)
XML_NAMESPACE = "http://alchemeast.eu/thesu/ns/1.0"

# color_mapping is set by _apply_settings from [colors] in settings_user.toml


if __name__ == "__main__":
    """Quick self-check: print effective settings."""
    print("Effective settings:")
    print("  BASE_DIR:", BASE_DIR)
    print("  OUTPUT_DIR:", OUTPUT_DIR)
    print("  xml_name:", xml_name)
    print("  sources_to_select:", sources_to_select)
    print("  DEFAULT_ENGINE:", DEFAULT_ENGINE)
    print("  filter_propositions:", filter_propositions)
    print("  filter_matching_proposition_sequences:", filter_matching_proposition_sequences)
