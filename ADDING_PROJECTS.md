# Adding projects

This repository owns boards and their generated outputs. See [setup and commands](README.md).
Normal builds use saved sources and the committed component snapshot. Source fetching and
component synchronisation are explicit operations.

## 1. Add a board

Open the relevant user's `project_data/<user>/working.yaml`. Add the version to
the repository's `versions` list. This is the real Easyduino entry:

```yaml
github_user: Hanqaqa
projects:
  - github_repository: easyduino
    github_url: https://github.com/Hanqaqa/Easyduino
    repository_url: https://github.com/Hanqaqa/Easyduino.git
    versions:
      - board: atmega328p_arduino_uno
        board_name: ATmega328P Arduino Uno
        board_url: https://github.com/Hanqaqa/Easyduino/tree/master/Atmega328p%20Arduino%20Uno
        version: current
        git_ref: master
        sparse_checkout: true
        project_file_folder: Atmega328p Arduino Uno
        project_file_basename: Easyduino_Atmega
        project_file_path: Atmega328p Arduino Uno/Easyduino_Atmega
```

This is already present; do not add it twice. Copy the pattern for another
board and replace the values with that board's actual details.

| Field | What to type |
| --- | --- |
| `github_user`, `github_repository` | User-owned source identifiers. Taxonomy is normalized automatically; preserve real repository spelling. |
| `github_url`, `repository_url` | Actual upstream URLs. Preserve their real spelling, case and hyphens. |
| `board` | Optional extra taxonomy level for a repository containing several boards. Lowercase with underscores. Omit for a single-board repository. |
| `board_name` | Readable board title, including distinguishing model/revision details. |
| `board_url` | Link to this board's folder on GitHub; used by the generated project page. |
| `version` | `current` for the moving latest version; defaults to `current`. Use a stable name such as `rev_a` for a historical version. |
| `git_ref` | Actual upstream branch, tag or commit. `current` pulls that branch; historical versions check out the specified ref without pulling. Defaults to `main`, so specify `master` when appropriate. |
| `sparse_checkout` | `true` to check out only the selected board folder and root files. Useful for multi-board repositories. |
| `project_file_folder` | Directory inside the repository, with original case and spaces. Use `/`, and `""` if files are at repository root. |
| `project_file_basename` | Common filename stem, without an extension. |
| `project_file_path` | Folder plus filename stem; keep consistent with the previous two fields. |
| `source_format` | Omit (or use `kicad`) for native KiCad. Use `eagle` for paired `.brd` and `.sch` sources; the refresh action preserves both and runs `kicad-cli import` into the normal KiCad PCB, schematic, and project paths. This requires a KiCad CLI version that provides the top-level `import` command. |
| `production_exclude_references` | Optional plain list of references omitted from the JLCPCB BOM and CPL. |
| `production_lcsc_overrides` | Optional reference-to-LCSC-number dictionary for verified project-specific purchasing choices. |
| `production_rotation_offsets` | Optional reference-to-degree dictionary for JLC placement rotation corrections. |
| `production_position_offsets_mm` | Optional reference-to-`[x, y]` dictionary for placement-centre corrections in millimetres. |

A PCB is required; a schematic and project file may also be supplied. Paired Eagle sources use the explicit refresh/conversion path described above. Followed
hierarchical sheets are copied automatically; unrelated schematics elsewhere
in the repository are not imported as extra boards.

### Taxonomy and versions

Single-board repository:

```text
oomp / project / github / user / repo / current
```

Multi-board repository:

```text
oomp / project / github / user / repo / board / current
```

The Easyduino ID is:

```text
oomp_project_github_hanqaqa_easyduino_atmega328p_arduino_uno_current
```

For another board in the **same** repository, append another entry to `versions`
with a different `board`, source folder and file stem. For a previous version,
copy that board's entry, keep `board` unchanged, change `version` and `git_ref`,
and adjust the file path only if it differed in that revision. This produces
another part, rather than overwriting `current`.

### Generate and check the board

1. Run `action_generate.bat --filter <full-project-id> --refresh-sources --production --images --ibom`.
2. Open `parts/<id>/README.md` and `parts/<id>/board_explorer.html`. The prominent explorer link uses GitHub Pages to serve the HTML, not GitHub's source-file view.
3. Review `data/generated_data/unmatched_parts.yaml` (or JSON) and the browser
   research queue. Do not accept a near match just to remove a warning.
4. Add missing components in the separate electronics repository, build them,
   then explicitly run `action_sync_component_catalog.py` here. When an exact identity is verified, add a reusable matcher
   rule based on its value, footprint and symbol identity in
   `kicad_agents/oomp_matching_agent.py`, then rerun the same project command.

Matcher rules are declarations of an exact identity, not search hints. Never
force an IC, USB connector or crystal onto a similar-looking but electrically
different part. Unknown parts still appear in structured data and the explorer
with their actual PCB pads; they do not get an invented OOMP definition.

For conflicting source records, keep the reason in the same version dictionary:

```python
"match_blocked": {
    "U1": "The schematic says CP2102N, but the BOM orders CP2102-GMR. Confirm the intended chip.",
},
"review_notes": [
    "J1: distributor identity is verified; original footprint equivalence still needs checking.",
],
```

Blocked references stay unmatched even if an automatic rule would otherwise
match. Remove the block when the conflict is resolved. These notes persist in project JSON/YAML,
the project README and `data/generated_data/COMPONENT_REVIEW.md`; the reasons
also appear in each blocked component's OOMP data.

The action also generates InteractiveHtmlBom and a guarded OOMP KiCad design
copy. Read `data/oomp_design/conversion_report.yaml` and `validation.yaml`.
Only symbols/footprints that match official KiCad defaults are replaced.
Custom or changed items are retained and reported. Original files are preserved
in `data/original/`; the ignored checkout is under `data/git/`.

It also creates the JLCPCB upload bundle under
`data/production_auto_generate/`. Review `gerbers_jlc.zip`, `bom_jlc.csv`,
`cpl_jlc.csv`, `data/drc.json`, and especially `bom_missing_lcsc.csv` before an
order. Production details and simple correction dictionaries are documented in
[kicad_agents/PRODUCTION_JLC_GUIDE.md](kicad_agents/PRODUCTION_JLC_GUIDE.md).

