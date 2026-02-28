# *TheSu*-to-DOT

Converts *TheSu* XML documents into graph visualisations (DOT, SVG, PDF, PNG, and a Gephi import version). Configurable filters by source, proposition, sequence, thesis focus, etc.

The `_config_presets/` folder contains ready-to-use configurations that reproduce each figure from the JOHD lead-white dataset. For dataset context, provenance, and step-by-step reproduction instructions, see [JOHD_dataset_reproduction.md](JOHD_dataset_reproduction.md).

## Requirements

- **Python 3.x** (developed with 3.13.3)
- **GraphViz 14.1.2** — `dot`, `neato`, `fdp` must be on your PATH
- **Python packages:** `lxml` 6.0.2, `graphviz` 0.20.3, `webcolors` 24.11.1, `ipython` 9.2.0 (plus `tomli` on Python < 3.11)

```bash
pip install -r requirements.txt
```

## How to run

```bash
python TheSu-to-DOT.py
```

The script reads all settings from `settings_user.toml`. The default configuration runs a Plutarch lead-white example immediately — useful to verify the installation.

Output appears in `_thesu_outputs/`.

| Folder / file        | Purpose                                                                    |
| -------------------- | -------------------------------------------------------------------------- |
| `_thesu_inputs/`     | Put your *TheSu* XML file here, along with the XSD schema and source files |
| `_thesu_outputs/`    | Generated files (DOT, SVG, PDF, PNG, `*_gephi.dot`)                        |
| `settings_user.toml` | Configure paths, filters, layout, and output options                       |

## Using presets

To switch to a preset: delete `settings_user.toml`, copy the preset file into the script root, rename it `settings_user.toml`, and run the script.

```bash
del settings_user.toml
copy _config_presets\1.Plutarch\settings_1.Plutarch.toml settings_user.toml
python TheSu-to-DOT.py
```

To start fresh with a different *TheSu* document, use `_config_presets/settings_clean_slate.toml` and set `paths.xml_name` to your XML file name.

See [JOHD_dataset_reproduction.md](JOHD_dataset_reproduction.md) for the full list of presets and reproduction steps.

## GraphViz vs Gephi

Every run produces both a GraphViz DOT file (for SVG/PDF/PNG) and a `*_gephi.dot` file. GraphViz works well for smaller, focused views. For larger or denser graphs, import `*_gephi.dot` into Gephi and apply a force-directed layout there.

> **Note:** the Gephi figures in the JOHD dataset are not directly reproducible by this script — they require manual layout and styling in Gephi after import. See [JOHD_dataset_reproduction.md](JOHD_dataset_reproduction.md).

**Planned:** future versions will generate Gephi output independently and in parallel with the GraphViz pipeline — not by post-processing the DOT file, and not in DOT format, but as GEXF. Support for additional graph visualisation and analysis tools may follow.

## Code structure

- `TheSu-to-DOT.py` — entry point
- `bootstrap/` — dependency checks and runtime state
- `config/` — runtime settings and filters
- `state/` — document and text-segment caches
- `xml_processing/` — XML loading, selectors, extractors
- `dot/` — DOT graph construction
- `gephi/` — Gephi DOT conversion
- `render/` — SVG/PDF/PNG export

## License

[Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) — see [LICENSE](LICENSE).
