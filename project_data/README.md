# Project definitions

The editable source of the project catalogue: boards, revisions, upstream
locations, and the review decisions that belong to each version.

**[Back to Electronic Projects](../README.md)** · **[Worked example](../ADDING_PROJECTS.md)** · **[Processing tools](../kicad_agents/README.md)**

## Where definitions live

Each GitHub user has exactly one file at
`project_data/<user>/working.yaml`; the loader discovers these files in folder
name order.

## Minimal definition

This is a schema example; replace the placeholders with a real board:

```yaml
github_user: example_user
projects:
  - github_repository: example_board
    versions:
      - project_file_path: hardware/example_board
```

## Defaults and optional fields

| Field | Default |
| --- | --- |
| `github_url` | `https://github.com/<github_user>/<github_repository>` |
| `repository_url` | The GitHub URL followed by `.git` |
| `version` | `current` |
| `git_ref` | `main` |
| `project_file_extensions` | `[.kicad_pcb, .kicad_sch, .kicad_pro]` |

Add `board`, `board_name`, `board_url`,
`sparse_checkout`, and the `project_file_*` fields when the repository needs
them. A repository may have multiple version records; `current` is selected in
preference to historical entries, otherwise the newest numeric version is used.
For PCB-only KiCad projects, set `project_file_extensions` on that version to
`[.kicad_pcb]`; the default is `[.kicad_pcb, .kicad_sch, .kicad_pro]`.

## Matching and review decisions

Keep `match_blocked`, `review_notes`, and production metadata alongside the
version that they describe. Do not add reference-level component matches here:
add a reusable, evidence-based rule in `kicad_agents/oomp_matching_agent.py`.

## Paired Eagle sources

Set `source_format: eagle` for paired Eagle `.brd` and `.sch` files with the
same basename. The refresh action retains them as `source_eagle.brd` and
`source_eagle.sch`, then uses `kicad-cli import` to create the matching
`kicad_file.kicad_pcb`, `.kicad_sch`, and `.kicad_pro` files before continuing
through the standard project pipeline. This needs a KiCad CLI version that
provides the top-level `import` command.
