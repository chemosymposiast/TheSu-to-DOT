# TheSu-to-DOT

Converts TheSu XML documents into DOT graphs for visualisation with GraphViz and Gephi.

The script operates on documents encoded in the **TheSu XML** stand-off annotation schema, which models ideas, arguments, and their discursive contexts in historical texts. For an overview of the schema, examples of annotated sources, and further documentation, see the project website at `https://thesu.io`.

## Requirements

- Python 3.x
- GraphViz (dot, neato, fdp executables on PATH)
- Dependencies: `lxml`, `graphviz` (Python package). For Python &lt; 3.11, also `tomli` (for `settings_user.toml`).

## Running

From the `visualisation-script` directory:

```bash
python TheSu-to-DOT.py
```

## Configuration

- **Input data**: `_thesu_inputs/` – XML documents, XSD schema, and source files (`sources-refactored/`, `sources-segmented/`)
- **Output**: `_thesu_outputs/` – DOT, SVG, PDF, PNG files
- **Settings**: Edit `settings_user.toml` for paths, filters, layout engine, XML target, PDF/PNG resolution, GraphViz path, and color theming (all changeable settings are there)

## Structure

- `TheSu-to-DOT.py` – Entry script
- `bootstrap/` – Dependency checks and imports
- `config/` – Runtime settings and filters
- `state/` – Document and text-segment caches
- `xml_processing/` – XML loading, selectors, locus, extractors
- `dot/` – DOT graph build and post-processing
- `gephi/` – Gephi DOT conversion
- `render/` – SVG/PDF/PNG export

See `TheSu-to-DOT_outline.md` for a more detailed module map.
