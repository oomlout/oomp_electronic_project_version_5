# Guarded project conversion

Run `python action_generate.py --filter <project-id> --production`.
Components are read from the committed snapshot; derived library assets are built
in per-project working copies. Configure `OOMP_KICAD_ROOT` for nonstandard installs.

## Replacement safety

`kicad_project_action.py` is called by the project runner when production is requested. It re-extracts current inputs and uses current approved part matches. For each item it checks both the original source master and the selected OOMP master.

- KiCad normalises temporary footprint copies into the same coordinate frame, including underside mirroring. KiCad's symbol format upgrader normalises temporary symbol copies before comparison.
- Pin geometry, pin types, drawing geometry, pads, models and electrical overrides must agree. Unrecognised fields remain in the comparison: differences fail closed.
- Library names, UUIDs, nets, reference/value properties and other listed placement metadata are excluded from comparison. They are preserved in the design. The automatic reference/value text's 180-degree keep-upright convention is normalised, not treated as a physical modification.
- Replacement never changes soldering style. A design using a hand-solder master stays hand-solder. Its pads are not replaced by machine-solder pads.
- Only the verified library ID and added silkscreen annotation change in a PCB footprint. Pad trees, nets, placement and existing UUIDs are preserved. Schematic symbol instance fields/wires remain intact; footprint fields change only when the corresponding PCB instances were verified too.
- Custom imports, modified defaults, missing masters, incompatible canonical symbols and unmatched parts stay unchanged and receive a reason in `data/oomp_design/conversion_report.yaml` and `.json`.
- Original snapshots retain source checksums. New upstream revisions archive previous snapshots. Edited snapshots, generated designs or library tables are not silently overwritten. Copy `oomp_design` elsewhere before editing it.
- Every project conversion runs `kicad_validation_agent.py`: KiCad exports both netlists and verifies that component values/UUIDs and named-net pin memberships match. A structural PCB check allows only the approved library IDs and appended annotations to change. Results are saved in `validation.yaml` / `.json`; a failed check fails the action.
- Obsolete generated library entries are moved under `previous_generated/<sha256>/`, so removed entries aren't accidentally offered as active library items and their contents remain recoverable.

The generated copy is not a claim that the upstream design has passed ERC/DRC. Keep the existing design review and fabrication checks. Dense boards may need silkscreen label repositioning in an editable project copy.


Run `python -S tools/run_isolated_tests.py -q kicad_agents/tests/test_kicad_libraries.py` for native conversion regression tests.
