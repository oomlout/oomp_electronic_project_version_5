# Project processing tools

Turn saved board sources into structured component data, interactive explorers,
KiCad design copies, and reviewable manufacturing outputs.

**[Back to Electronic Projects](../README.md)** · **[Add a board](../ADDING_PROJECTS.md)** · **[Project definitions](../project_data/README.md)**

## Choose a starting point

| Task | Guide |
| --- | --- |
| Set up tools and build a selected board | [Setup and commands](../README.md#build-a-selected-project) |
| Register a board or another revision | [Adding projects](../ADDING_PROJECTS.md) |
| Explore components, pins, and routed nets | [Board explorer controls](BOARD_EXPLORER_GUIDE.md) |
| Understand converted designs and local libraries | [Conversion guide](KICAD_LIBRARY_GUIDE.md) |
| Prepare and review fabrication files | [Production guide](PRODUCTION_JLC_GUIDE.md) |

## How the pipeline fits together

`action_generate.py` coordinates these stages:

1. Populate project definitions and select the requested boards.
2. Refresh upstream inputs when `--refresh-sources` is supplied.
3. Extract KiCad data and match components against the committed catalogue.
4. Build project documentation and board explorers.
5. Run requested image, InteractiveHtmlBom, and production stages.
6. Update navigation and component usage.

The project tools run using their own code and committed component snapshot.
Roboclick and the electronics Python framework are not required.

## Files and review boundaries

Each `parts/<project-id>` directory owns its inputs and outputs. Source refresh is
explicit. Conversion preserves originals and edits a separate `oomp_design` copy.
Library generation works on per-project copies, leaving `component_catalog`
unchanged. Missing matches remain unresolved; fabrication warnings require review.

## Check changes

Run from the repository root:

```powershell
python action_doctor.py
python -S tools/run_isolated_tests.py -q
```

The doctor reports installed prerequisites. The isolated suite blocks filesystem
access to sibling checkouts, so it also checks the project's independence.
Historical test findings from the split are retained in the
[migration notes](../README.md#maintainer-reference).
