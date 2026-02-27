# Reproducing the JOHD dataset visualisations

Each visualisation has a matching ready-to-use preset. The simplest way to reproduce it is to swap in the preset (delete the current `settings_user.toml`, copy the preset into the script root, rename it `settings_user.toml`), then run the script. The TOML settings listed under each visualisation below are what the preset already contains — you only need to set them manually if you prefer to edit `settings_user.toml` directly or want to customise beyond the preset.

## Context and provenance

### Dataset and paper

The dataset referenced in this guide is the one attached to the paper **Lead White in Context Across Greco-Roman Sources: The First *TheSu* XML Annotation Dataset of Arguments and Recipes, with Graph Visualisations and Discussion of their Design** (Daniele Morrone). Full submission June 2025; under peer review.

- **Visualisations production dates:** 11–13 June 2025  
- ***TheSu* XML source:** last edited 9 June 2025  
- ***TheSu* XML XSD:** last edited 11 June 2025

The visualisations included in the referenced dataset were generated with an earlier legacy version of the script, which is not shared. **This script** (the one in this repository) is a refactored, better modularised, and upgraded version of that legacy script. It produces almost exactly the same output from the same input file, with no changes in the design and semantic content of the graphs.

## 1. Before you begin

**XML file.** All visualisations are generated from the same XML file: `ancient-lead-white_JOHD.xml`. Make sure it is in the `_thesu_inputs/` folder next to the script. The relevant section of `settings_user.toml` should read:

```toml
[paths]
base_dir = "_thesu_inputs"
output_dir = "_thesu_outputs"
xml_name = "ancient-lead-white_JOHD"
```

**How to run.** From the project root directory:

```bash
python TheSu-to-DOT.py
```

DOT, SVG, PDF, and PNG outputs will be written to `_thesu_outputs/`. On the first successful run, the script writes a small internal state file at `bootstrap/.thesu_runtime_state.json` to remember that GraphViz is correctly installed; you can ignore this file and do not need to edit it.

## 2. About the dataset SVG files

Each SVG file in the dataset contains a small parameter box listing the exact settings used to generate that figure — the source(s), active filters, layout engine, and layout parameters. Section 3 already translates all of these into the corresponding `settings_user.toml` entries, so you do not need to decode the parameter boxes yourself to reproduce the figures.

## 3. How to replicate the JOHD dataset visualisations

**To use a preset** (simplest):

```bash
del settings_user.toml
copy _config_presets\<preset-folder>\<preset-file>.toml settings_user.toml
python TheSu-to-DOT.py
```

**To apply settings manually**: edit the `[filters]` and `[layout]` sections of `settings_user.toml` as shown for each visualisation below, then run the script.

### 3.1 Plutarch (`1.Plutarch/`)

**Preset**: `_config_presets/1.Plutarch/settings_1.Plutarch.toml`

Argumentation map for Plutarch's *Quaestiones convivales* 6.5, 690f-691c. The graph represents an interpretation that both the cooling and "thinning" effects Plutarch attributes to lead are explained through its essential coldness, and shows how different types of relationships between statements — including entailment — are encoded in *TheSu* XML. To focus on the argumentative structure and strip away everything else, propositions, sequence elements, and extrinsic elements are all removed, leaving only the core theses and their logical and rhetorical relations.

- Sources: `tlg0007_tlg112`
- Engine: `dot`
- Active Filters: `(a)`, `(c)`, `(d)`
- Parameters: DOT defaults

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

The `[layout.dot]` section can remain at its defaults.

### 3.2 Plato (`2.Plato/`)

**Preset**: `_config_presets/2.Plato/settings_2.Plato.toml`

Argumentation map for Plato's *Lysis*, 217b-e, where Socrates reflects on the nature of qualities and their presence in objects. The passage has a more complex discourse structure than the Plutarch example: the lead white examples applied to Menexenus's blond hair first serve to clarify Socrates's point for Menexenus, then become premises for his moral argument. Many statements are presented as contrasting with each other, and Menexenus occasionally responds with confirmations — all of which add relational complexity that makes the DOT hierarchical tree difficult to read. The same filters as 3.1 are applied for the same reason — to isolate the argumentative structure — but this is one of the views where the Gephi version (included in the dataset and used in the paper) is the more readable one (see section 4).

- Sources: `tlg0059_tlg020`
- Engine: `dot`
- Active Filters: `(a)`, `(c)`, `(d)`
- Parameters: DOT defaults

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

### 3.3 Plato–Plutarch–Dioscorides (`3.Plato-Plutarch-Dioscorides/`)

**Preset**: `_config_presets/3.Plato-Plutarch-Dioscorides/settings_3.Plato-Plutarch-Dioscorides.toml`

Cross-source comparison connecting Plutarch *Quaestiones convivales* 6.5, 690f-691c; Plato *Lysis*, 217b-e; and Dioscorides *De materia medica* 5.81, 5.82, 5.88 through shared proposition nodes. Despite Plutarch's Platonism, his discussion shares no common propositions with Plato's passage — both independently connect with Dioscorides's treatment instead. To make these cross-source links visible, propositions are kept in the graph (unlike in 3.1 and 3.2), while matching proposition sequences and all sequence elements are filtered out to reduce clutter. This is one of the views where GraphViz produces a cluttered layout — the Gephi version is recommended (see section 4).

- Sources: `tlg0059_tlg020`, `tlg0656_tlg001`, `tlg0007_tlg112`
- Engine: `dot`
- Active Filters: `(b)`, `(c)`
- Parameters: DOT defaults

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

### 3.4 Theophrastus (`4.Theophrastus/`)

**Preset**: `_config_presets/4.Theophrastus/settings_4.Theophrastus.toml`

Argumentation and recipe map for Theophrastus's *De lapidibus* 55-56, which contains the earliest attested production process for lead white. Unlike the Plato and Plutarch views, sequence elements are kept here: this is what allows the individual steps of the recipe to appear in the graph, broken down into numbered phases and shown alongside their discursive context. Propositions and extrinsic elements are still removed to keep the view readable.

- Sources: `tlg0093_tlg004`
- Engine: `dot`
- Active Filters: `(a)`, `(d)`
- Parameters: DOT defaults

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

### 3.5 Dioscorides–Theophrastus recipes (`5.Diosc.recipe-Thphr.recipe/`)

**Preset**: `_config_presets/5.Diosc.recipe-Thphr.recipe/settings_5.Diosc.recipe-Thphr.recipe.toml`

Step-by-step comparison between Dioscorides's first recipe (*De materia medica* 5.88.1) and a proposition modelling Theophrastus's procedure (*De lapidibus* 55). Corresponding steps are connected by arrows with labels characterising their relationship (e.g., "extends", "alters"), making similarities and divergences immediately visible. The view is centred on the Dioscorides recipe thesis node, with a custom exclusion to keep the graph focused. A NEATO spring layout is used rather than DOT: instead of imposing a hierarchy, it positions nodes by simulated physical force, which works better for this type of side-by-side comparison.

- Sources: `tlg0656_tlg001`
- Engine: `neato`
- Active Filters: `(d)`, `(f)`
- Thesis Focus: `tlg0656_tlg001.T213927`
- Custom exclusion: proposition `tlg0656_tlg001.P213927` excluded from thesis `tlg0656_tlg001.T213927`

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

### 3.6 KLL–Theophrastus–Dioscorides recipes, NEATO (`6a.KLL.recipe-Thphr.recipe-Diosc.recipe/`)

**Preset**: `_config_presets/6a.KLL.recipe-Thphr.recipe-Diosc.recipe/settings_6a.KLL.recipe-Thphr.recipe-Diosc.recipe.toml`

Three-way comparison mapping the modern replication by Katsaros, Liritzis, and Laskaris (2010) to both ancient recipes simultaneously. Spatial distancing and colour coding make immediately clear which steps derive from which source and how they correspond across time. The view is centred on the KLL thesis node, with cross-links radiating out to Theophrastus and Dioscorides. NEATO is used for the same reason as in 3.5: a force-directed layout suits this kind of network comparison better than a strict hierarchy.

- Sources: `katsaros_liritzis_laskaris_2010`
- Engine: `neato`
- Thesis Focus: `katsaros_liritzis_laskaris_2010.T124253`

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

### 3.7 KLL recipe, DOT (`6b.KLL.recipe/`)

**Preset**: `_config_presets/6b.KLL.recipe/settings_6b.KLL.recipe.toml`

The same Katsaros et al. (2010) recipe as in 3.6, but rendered with DOT and shown in the context of its full surrounding discourse structure, without a thesis focus filter. Showing the recipe within its mapped discourse reveals contextual information that a recipe-only view would hide: the authors explicitly state they combined Dioscorides's recipe with Theophrastus's "incomplete" description to achieve "a complete method". Propositions and extrinsic elements are removed to keep the view readable, but sequence elements (recipe steps) are kept.

- Sources: `katsaros_liritzis_laskaris_2010`
- Engine: `dot`
- Active Filters: `(a)`, `(d)`
- Parameters: DOT defaults

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

### 3.8 Caley–Richards–Theophrastus–Dioscorides recipes (`6c.Caley,Richards.recipe-Thphr.recipe-Diosc.recipe/`)

**Preset**: `_config_presets/6c.Caley,Richards.recipe-Thphr.recipe-Diosc.recipe/settings_6c.Caley,Richards.recipe-Thphr.recipe-Diosc.recipe.toml`

NEATO recipe view centred on the Caley & Richards (1956, p. 188) replication and its mapped connections to the ancient recipes. The view highlights significant departures from Theophrastus's recipe in the final part, which stem primarily from Caley and Richards's interpretation that Theophrastus's step 6 involves water. Only the thesis focus filter is applied — no element types are removed — so the full recipe and propositional structure is visible.

- Sources: `caley_richards_1956`
- Engine: `neato`
- Thesis Focus: `caley_richards_1956.T212135`

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

The default `[layout.neato]` values in `settings_user.toml` already match the dataset parameters, so no further changes are needed.

### 3.9 All recipes across sources (`7.all.recipes/`)

**Preset**: `_config_presets/7.all.recipes/settings_7.all.recipes.toml`

Overview of all recipes across the dataset: Dioscorides *De materia medica* 5.88.1, Theophrastus *De lapidibus* 55, Plutarch *Quaestiones convivales* 6.5, 691b, plus the replications by Caley & Richards (1956) and Katsaros et al. (2010). All five sources are included at once; one thesis node per source is used as a focus anchor to keep each source's recipe steps grouped together, while extrinsic elements are removed to reduce noise. Spatial proximity gives a rough indication of shared steps. NEATO is used because DOT's strict hierarchy would not make sense for this kind of multi-source comparison. This is one of the views where GraphViz produces a cluttered layout — the Gephi version is recommended (see section 4).

- Sources: `tlg0093_tlg004`, `tlg0656_tlg001`, `tlg0007_tlg112`, `caley_richards_1956`, `katsaros_liritzis_laskaris_2010`
- Engine: `neato`
- Active Filters: `(d)`
- Thesis Focus: one per source (see below)

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

### 3.10 Everything (`8.everything/`)

**Preset**: `_config_presets/8.everything/settings_8.everything.toml`

The most comprehensive view: all six sources at once, with no filters applied — all propositions, sequences, extrinsic elements, and theses are shown together. This includes Plato *Lysis* 217b-e, Dioscorides *De materia medica* 5.81, 5.82, 5.88, Plutarch *Quaestiones convivales* 6.5, 690f-691c, Theophrastus *De lapidibus* 55-56, Caley & Richards (1956), and Katsaros et al. (2010). In this view, sources naturally cluster around the proposition nodes they share, and it becomes visible which recipe steps in modern replications correspond to propositional steps in the ancient model recipes. Because nothing is removed, this is the hardest view to read in GraphViz — the Gephi version is the recommended one (see section 4).

- Sources: all (`tlg0059_tlg020`, `tlg0093_tlg004`, `tlg0656_tlg001`, `tlg0007_tlg112`, `caley_richards_1956`, `katsaros_liritzis_laskaris_2010`)
- Engine: `dot`
- Active Filters: none

```toml
[filters]
sources_to_select = []        # empty = include all sources
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

You can keep `[layout.dot]` at its defaults, or temporarily set `splines = "curved"` to more closely match the original dataset DOT file.

## 4. Practical note (GraphViz vs Gephi)

Some visualisations work better in one tool than the other:

- **GraphViz preferred** for: 1.Plutarch, 4.Theophrastus, 5.Diosc.recipe-Thphr.recipe, 6a, 6b, 6c — hierarchical or spring layouts render well.
- **Gephi preferred** for: 2.Plato, 3.Plato-Plutarch-Dioscorides, 7.all.recipes, 8.everything — the Plato passage has a complex discourse structure that produces a difficult-to-read DOT tree; cross-source and large-scale views also produce cluttered GraphViz output.

The script generates a `*_gephi.dot` file alongside each GraphViz output. For views 2, 3, 7, and 8, import that file into Gephi as the basis for a network graph.

> **The Gephi visualisations in the JOHD dataset cannot be reproduced directly by this script.** After importing the `*_gephi.dot` file, you need to apply a force-directed layout algorithm in Gephi, then manually adjust the appearance of nodes, edges, and labels before exporting. The final dataset figures were produced this way. The paper presenting the dataset documents which layout algorithms were used for each Gephi visualisation.

