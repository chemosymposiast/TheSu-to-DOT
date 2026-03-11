### JOHD visualisation guide

This guide describes how to reproduce each legacy JOHD GraphViz visualisation using the refactored TheSu visualisation script and the XML file `ancient-lead-white_JOHD.xml`.  
For each recipe you temporarily edit `visualisation-script/settings_user.toml`, run the script, then adjust settings for the next view.

For a conceptual introduction to TheSu XML and the wider research project behind this dataset, including example visualisations of other sources, see `https://thesu.io`.

## 1. Global assumptions

- **Single XML source**
  - All visualisations are generated from the same XML file: `ancient-lead-white_JOHD.xml`.
  - In this project, that XML has been copied into the local `_thesu_inputs` folder next to the script, so you can configure `paths` like this:

```toml
[paths]
base_dir = "_thesu_inputs"
output_dir = "_thesu_outputs"
xml_name = "ancient-lead-white_JOHD"
```

- **How to run**
  - From `visualisation-script/`, run:

```bash
python TheSu-to-DOT.py
```

  - DOT, SVG, PDF, and PNG outputs will be written under the folder configured as `output_dir` (by default `_thesu_outputs`).

## 2. Configuration primer (legacy → `settings_user.toml`)

- **XML File**
  - **Legacy box**: `XML File: ancient-lead-white_JOHD.xml`
  - **TOML**: `paths.xml_name = "ancient-lead-white_JOHD"` and `paths.base_dir` points to the folder containing that XML.

- **Sources**
  - **Legacy box**: one or more lines under `Sources:`, e.g. `tlg0007_tlg112`, `caley_richards_1956`.
  - **TOML**: list under `filters.sources_to_select`, e.g.:

```toml
[filters]
sources_to_select = ["tlg0007_tlg112", "tlg0656_tlg001"]
```

- **Active Filters (a–d)**
  - **Legacy labels → TOML booleans in `[filters]`**:
    - `(a) Remove All Propositions` → `filter_propositions = true`
    - `(b) Remove Matching Prop Seq/Phases` → `filter_matching_proposition_sequences = true`
    - `(c) Remove All Sequence Elements` → `filter_all_sequences = true`
    - `(d) Remove 'Extrinsic' Elements` → `filter_extrinsic_elements = true`
  - If a letter is not listed in the SVG’s `Active Filters:` box, set that boolean to `false` for that recipe.

- **Thesis Focus**
  - **Legacy labels**: `• Thesis Focus: <THESIS_ID>[, <THESIS_ID>...]`
  - **TOML**: `filters.thesis_focus_id` is a list of thesis IDs:

```toml
[filters]
thesis_focus_id = [
  "tlg0656_tlg001.T213927",
  "tlg0093_tlg004.T151115",
]
```

- **Custom Filters (propositions)**
  - **Legacy labels**: lines under `Custom Filters:`, e.g.  
    `• Prop tlg0656_tlg001.P213927 → Theses: tlg0656_tlg001.T213927`
  - **TOML**: map proposition IDs to thesis IDs in `[filters.custom_propositions]`:

```toml
[filters.custom_propositions]
"tlg0656_tlg001.P213927" = ["tlg0656_tlg001.T213927"]
```

- **Layout engine**
  - **Legacy label**: `Engine: dot` or `Engine: neato`
  - **TOML**: `layout.default_engine`:

```toml
[layout]
default_engine = "dot"    # or "neato"
```

- **Layout parameters**
  - **Legacy labels**: lines under `Parameters:`, e.g. `nodesep = 0.25`, `mode = sgd`.
  - **TOML**:
    - For `Engine: dot`, set values in `[layout.dot]`.
    - For `Engine: neato`, set values in `[layout.neato]`.
  - The current defaults in `settings_user.toml` already match all DOT parameters in the JOHD SVGs, and also match the NEATO parameters for the Caley–Richards recipe (6c).  
    NEATO-based recipes 5, 6a, and 7 override `outputorder`, `maxiter`, `mode`, and/or `model` as shown below.

- **Output and colours**
  - JOHD GraphViz parameter boxes do not encode page size, DPI, or colour overrides; the defaults in `[output.pdf]`, `[output.png]`, and `[colors]` in `settings_user.toml` are suitable for reproducing the legacy layouts.

## 3. Visualisation recipes

For each recipe below:

1. Adjust `[filters]` and (when specified) `[filters.custom_propositions]`.
2. Set `[layout].default_engine` and any recipe-specific `[layout.neato]` overrides.
3. Run `python TheSu-to-DOT.py`.
4. Inspect the generated SVG/PDF/PNG in your `output_dir`.

### 3.1 Plutarch (`1.Plutarch/1.graphviz_Plutarch.svg`)

- **Summary**: Single-source Plutarch view, DOT engine, propositions/sequences and extrinsic elements removed.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `tlg0007_tlg112`
  - Engine: `dot`
  - Active Filters: `(a) Remove All Propositions`, `(c) Remove All Sequence Elements`, `(d) Remove 'Extrinsic' Elements`
  - Parameters: `overlap = scalexy`, `splines = ortho`, `nodesep = 0.25`, `ranksep = 0.3`, `outputorder = edgesfirst`, `concentrate = false`, `newrank = true`

- **TOML settings**:

```toml
[filters]
sources_to_select = ["tlg0007_tlg112"]
filter_propositions = true
filter_matching_proposition_sequences = false
filter_all_sequences = true
filter_extrinsic_elements = true
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

The `[layout.dot]` section can remain at its defaults (they already equal the parameters listed above).

### 3.2 Plato (`2.Plato/2.graphviz_Plato.svg`)

- **Summary**: Single-source Plato view with the same DOT layout and filters as Plutarch.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `tlg0059_tlg020`
  - Engine: `dot`
  - Active Filters: `(a) Remove All Propositions`, `(c) Remove All Sequence Elements`, `(d) Remove 'Extrinsic' Elements`
  - Parameters: identical to 3.1 (DOT defaults)

- **TOML settings**:

```toml
[filters]
sources_to_select = ["tlg0059_tlg020"]
filter_propositions = true
filter_matching_proposition_sequences = false
filter_all_sequences = true
filter_extrinsic_elements = true
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

DOT layout parameters remain at their defaults.

### 3.3 Plato–Plutarch–Dioscorides (`3.Plato-Plutarch-Dioscorides/3.graphviz_Plato-Plutarch-Dioscorides_BAD.svg`)

- **Summary**: Combined DOT view over Plato, Dioscorides, and Plutarch, focusing on matching proposition sequences and removing all sequence elements.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `tlg0059_tlg020`, `tlg0656_tlg001`, `tlg0007_tlg112`
  - Engine: `dot`
  - Active Filters: `(b) Remove Matching Prop Seq/Phases`, `(c) Remove All Sequence Elements`
  - Parameters: DOT defaults (`overlap = scalexy`, `splines = ortho`, `nodesep = 0.25`, `ranksep = 0.3`, `outputorder = edgesfirst`, `concentrate = false`, `newrank = true`)

- **TOML settings**:

```toml
[filters]
sources_to_select = ["tlg0059_tlg020", "tlg0656_tlg001", "tlg0007_tlg112"]
filter_propositions = false
filter_matching_proposition_sequences = true
filter_all_sequences = true
filter_extrinsic_elements = false
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

DOT layout parameters remain at their defaults.

### 3.4 Theophrastus (`4.Theophrastus/4.graphviz_Theophrastus.svg`)

- **Summary**: Single-source Theophrastus view, DOT engine, propositions and extrinsic elements removed.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `tlg0093_tlg004`
  - Engine: `dot`
  - Active Filters: `(a) Remove All Propositions`, `(d) Remove 'Extrinsic' Elements`
  - Parameters: DOT defaults (same as 3.1)

- **TOML settings**:

```toml
[filters]
sources_to_select = ["tlg0093_tlg004"]
filter_propositions = true
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = true
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

DOT layout parameters remain at their defaults.

### 3.5 Dioscorides–Theophrastus recipes (`5.Diosc.recipe-Thphr.recipe/5.graphviz_Diosc.recipe-Thphr.recipe.svg`)

- **Summary**: NEATO-based recipe view over Dioscorides, with a custom proposition filter and thesis focus, extrinsic elements removed.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `tlg0656_tlg001`
  - Engine: `neato`
  - Active Filters: `(d) Remove 'Extrinsic' Elements`
  - Custom Filters:
    - `Prop tlg0656_tlg001.P213927 → Theses: tlg0656_tlg001.T213927`
    - `Thesis Focus: tlg0656_tlg001.T213927`
  - Parameters (NEATO):
    - `overlap = prism`
    - `splines = spline`
    - `nodesep = 0.1`
    - `outputorder = edgesfirst`
    - `concentrate = true`
    - `K = 0.3`
    - `sep = 0.05`
    - `maxiter = 800`
    - `mode = major`
    - `model = subset`

- **TOML settings**:

```toml
[filters]
sources_to_select = ["tlg0656_tlg001"]
filter_propositions = false
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = true
thesis_focus_id = ["tlg0656_tlg001.T213927"]

[filters.custom_propositions]
"tlg0656_tlg001.P213927" = ["tlg0656_tlg001.T213927"]

[filters.custom_sequences]

[layout]
default_engine = "neato"

[layout.neato]
overlap = "prism"
splines = "spline"
nodesep = 0.1
outputorder = "edgesfirst"
concentrate = "true"
K = 0.3
sep = 0.05
maxiter = 800
mode = "major"
model = "subset"
```

### 3.6 KLL–Theophrastus–Dioscorides recipes (NEATO) (`6a.KLL.recipe-Thphr.recipe-Diosc.recipe/6a.graphviz_KLL.recipe-Thphr.recipe-Diosc.recipe.svg`)

- **Summary**: NEATO layout centred on the KLL 2010 thesis, with cross-links to Theophrastus and Dioscorides via the JOHD schema.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `katsaros_liritzis_laskaris_2010`
  - Engine: `neato`
  - Active Filters: `• Thesis Focus: katsaros_liritzis_laskaris_2010.T124253`
  - Parameters (NEATO):
    - `overlap = prism`
    - `splines = spline`
    - `nodesep = 0.1`
    - `outputorder = nodesfirst`
    - `concentrate = true`
    - `K = 0.3`
    - `sep = 0.05`
    - `maxiter = 1500`
    - `mode = sgd`
    - `model = shortpath`

- **TOML settings**:

```toml
[filters]
sources_to_select = ["katsaros_liritzis_laskaris_2010"]
filter_propositions = false
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = false
thesis_focus_id = ["katsaros_liritzis_laskaris_2010.T124253"]

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "neato"

[layout.neato]
overlap = "prism"
splines = "spline"
nodesep = 0.1
outputorder = "nodesfirst"
concentrate = "true"
K = 0.3
sep = 0.05
maxiter = 1500
mode = "sgd"
model = "shortpath"
```

### 3.7 KLL recipe (DOT) (`6b.KLL.recipe/6b.graphviz_KLL.recipe.svg`)

- **Summary**: DOT-based hierarchical view of the KLL 2010 recipe, hiding propositions and extrinsic elements without an explicit thesis focus filter.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `katsaros_liritzis_laskaris_2010`
  - Engine: `dot`
  - Active Filters:
    - `(a) Remove All Propositions`
    - `(d) Remove 'Extrinsic' Elements`
  - Parameters: DOT defaults (same as 3.1)

- **TOML settings**:

```toml
[filters]
sources_to_select = ["katsaros_liritzis_laskaris_2010"]
filter_propositions = true
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = true
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

DOT layout parameters remain at their defaults.

### 3.8 Caley–Richards–Theophrastus–Dioscorides recipes (`6c.Caley,Richards.recipe-Thphr.recipe-Diosc.recipe/6c.graphviz_Caley,Richards.recipe-Thphr.recipe-Diosc.recipe.svg`)

- **Summary**: NEATO-based recipe view centred on Caley–Richards 1956, with thesis focus only.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: `caley_richards_1956`
  - Engine: `neato`
  - Active Filters: `• Thesis Focus: caley_richards_1956.T212135`
  - Parameters (NEATO):
    - `overlap = prism`
    - `splines = spline`
    - `nodesep = 0.1`
    - `outputorder = nodesfirst`
    - `concentrate = true`
    - `K = 0.3`
    - `sep = 0.05`
    - `maxiter = 30000`
    - `mode = sgd`
    - `model = subset`

- **TOML settings**:

```toml
[filters]
sources_to_select = ["caley_richards_1956"]
filter_propositions = false
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = false
thesis_focus_id = ["caley_richards_1956.T212135"]

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "neato"
```

For this recipe, the default `[layout.neato]` values in `settings_user.toml` already match the legacy parameters, so you do not need to change them.

### 3.9 All recipes across sources (`7.all.recipes/7.graphviz_all.recipes_BAD.svg`)

- **Summary**: NEATO-based aggregate recipe view across all JOHD sources, with extrinsic elements removed and multiple thesis foci.
- **Legacy parameters**:
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources:
    - `tlg0093_tlg004`
    - `tlg0656_tlg001`
    - `tlg0007_tlg112`
    - `caley_richards_1956`
    - `katsaros_liritzis_laskaris_2010`
  - Engine: `neato`
  - Active Filters:
    - `(d) Remove 'Extrinsic' Elements`
    - `• Thesis Focus: tlg0093_tlg004.T151115, tlg0656_tlg001.T213927, tlg0007_tlg112.T141553, caley_richards_1956.T212135, katsaros_liritzis_laskaris_2010.T124253`
  - Parameters (NEATO):
    - `overlap = prism`
    - `splines = spline`
    - `nodesep = 0.1`
    - `outputorder = edgesfirst`
    - `concentrate = true`
    - `K = 0.3`
    - `sep = 0.05`
    - `maxiter = 1500`
    - `mode = major`
    - `model = circuit`

- **TOML settings**:

```toml
[filters]
sources_to_select = [
  "tlg0093_tlg004",
  "tlg0656_tlg001",
  "tlg0007_tlg112",
  "caley_richards_1956",
  "katsaros_liritzis_laskaris_2010",
]
filter_propositions = false
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = true
thesis_focus_id = [
  "tlg0093_tlg004.T151115",
  "tlg0656_tlg001.T213927",
  "tlg0007_tlg112.T141553",
  "caley_richards_1956.T212135",
  "katsaros_liritzis_laskaris_2010.T124253",
]

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "neato"

[layout.neato]
overlap = "prism"
splines = "spline"
nodesep = 0.1
outputorder = "edgesfirst"
concentrate = "true"
K = 0.3
sep = 0.05
maxiter = 1500
mode = "major"
model = "circuit"
```

### 3.10 Everything (`8.everything/8.graphviz_everything_BAD.dot` and `8.everything/8.gephi_everything.svg`)

- **Summary**: DOT-based global view over all JOHD sources, intended as an essentially unfiltered “everything” overview that corresponds to the Gephi layout in `8.gephi_everything.svg`.
- **Legacy parameters** (from the GraphViz DOT header and overall project conventions):
  - XML File: `ancient-lead-white_JOHD.xml`
  - Sources: all JOHD sources:
    - `tlg0059_tlg020`
    - `tlg0093_tlg004`
    - `tlg0656_tlg001`
    - `tlg0007_tlg112`
    - `caley_richards_1956`
    - `katsaros_liritzis_laskaris_2010`
  - Engine: `dot` (DOT file uses `rankdir="TB"`, `newrank=true`, and `splines=curved`)
  - Active Filters: none of (a)–(d), and no thesis focus
  - Parameters (DOT):
    - `splines = curved`
    - `newrank = true`
    - All other layout parameters are GraphViz defaults and can be approximated with the standard DOT settings used elsewhere in this guide.

- **TOML settings**:

```toml
[filters]
sources_to_select = []        # include all sources
filter_propositions = false
filter_matching_proposition_sequences = false
filter_all_sequences = false
filter_extrinsic_elements = false
thesis_focus_id = []

[filters.custom_propositions]

[filters.custom_sequences]

[layout]
default_engine = "dot"
```

For this “everything” view you can keep `[layout.dot]` at its defaults, or, to more closely mimic the legacy DOT file, temporarily set `splines = "curved"` while generating this visualisation.

## 4. Smoke-testing and practical tips

- **Minimal smoke tests**
  - Pick at least one DOT recipe (for example, 3.1 Plutarch) and one NEATO recipe (for example, 3.5 Dioscorides–Theophrastus recipes).
  - Apply the corresponding settings, run `python TheSu-to-DOT.py`, and visually compare the new SVGs in `_thesu_outputs` to the legacy SVGs in the JOHD `visualisations` folder.

- **Resetting between runs**
  - Because `settings_user.toml` is global, you will typically:
    1. Edit `[filters]` and `[layout]` to match a recipe.
    2. Run the script and archive the outputs.
    3. Adjust only the keys that change for the next recipe (usually `sources_to_select`, the four `filter_*` booleans, `thesis_focus_id`, `default_engine`, and — for some NEATO views — the few `layout.neato` parameters that differ).

- **On `_BAD` file names**
  - Legacy filenames suffixed with `_BAD` are treated here as canonical for parameter extraction; the suffix does not change how you configure the refactored script and can be ignored when following these recipes.

