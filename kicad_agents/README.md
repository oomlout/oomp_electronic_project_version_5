# Project processing tools

See [setup and commands](../README.md), [adding projects](../ADDING_PROJECTS.md),
[board explorer controls](BOARD_EXPLORER_GUIDE.md),
[guarded conversion](KICAD_LIBRARY_GUIDE.md) and
[fabrication output](PRODUCTION_JLC_GUIDE.md).

`action_generate.py` owns the project pipeline: populate definitions, optionally
refresh upstream inputs, extract KiCad data, match components from the committed
snapshot, generate documentation and explorers, optionally generate images,
InteractiveHtmlBom and production outputs, then publish navigation and usage.
Roboclick and the electronics Python framework are not required.

Each `parts/<project-id>` directory owns its inputs and outputs. Source refresh is
explicit. Conversion preserves originals and edits a separate `oomp_design` copy.
Library generation works on per-project copies, leaving `component_catalog`
unchanged. Missing matches remain unresolved; fabrication warnings require review.

Run `python -S tools/run_isolated_tests.py -q` to verify project tools with
filesystem access to the sibling electronics checkout blocked.
