# OOMP Electronic Projects

**Explore a board, understand its components, and follow it through to manufacturing files.**

This repository brings electronic board projects into a consistent, browsable
collection. Each project keeps its source files, component records, drawings,
and review results together, with interactive explorers and production outputs
where available. Matched parts link back to the
[OOMP Electronics catalogue](https://github.com/oomlout/oomp_electronic_version_5).

**[Browse projects](navigation/README.md)** · **[Board explorer guide](kicad_agents/BOARD_EXPLORER_GUIDE.md)** · **[Add a project](ADDING_PROJECTS.md)** · **[Component catalogue](https://github.com/oomlout/oomp_electronic_version_5)**

[![Component-placement drawing of the Adafruit PWM Servo Shield][board-image]][example]

*Example: [Adafruit PWM Servo Shield][example]. Browse its saved project record
or [open the interactive board explorer][explorer].*

## Find what you need

| I want to… | Start here |
| --- | --- |
| Browse boards and saved versions | [Project catalogue](navigation/README.md) |
| Inspect components, pins, and routed nets | [Board explorer guide](kicad_agents/BOARD_EXPLORER_GUIDE.md) |
| Add another board | [Adding projects](ADDING_PROJECTS.md) and [definition format](project_data/README.md) |
| Understand the converted KiCad design | [Conversion and library guide](kicad_agents/KICAD_LIBRARY_GUIDE.md) |
| Review fabrication and assembly outputs | [Production guide](kicad_agents/PRODUCTION_JLC_GUIDE.md) |
| See where an OOMP component is used | [Component usage](https://oomlout.github.io/oomp_electronic_project_version_5/usage/index.html) |

## What a project contains

- **Saved source files and provenance**, including the upstream board and Git reference.
- **Component matching** against a local OOMP catalogue, with unresolved matches
  and review decisions kept visible.
- **Board drawings and interactive explorers**, plus InteractiveHtmlBom where generated.
- **A separate OOMP KiCad design**, conversion reports, and project-local libraries.
- **Manufacturing outputs where generated**, including Gerbers, assembly files,
  and validation reports for review.

Each project lives in `parts/<project-id>/`. Its page links to the available
files and reports. Custom or modified board items are preserved when they cannot
be replaced with verified library assets.

## Set up a local checkout

Use **Python 3.12 or later**. On Windows, enable Git's long-path support when cloning:

```powershell
git clone -c core.longpaths=true https://github.com/oomlout/oomp_electronic_project_version_5.git C:\gh\oomp_electronic_project_version_5
cd C:\gh\oomp_electronic_project_version_5
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
python action_doctor.py
```

Choose another destination if needed. For an existing checkout, run
`git config core.longpaths true` once. The doctor command reports prerequisites
without changing the checkout.

| Tool | Used for |
| --- | --- |
| KiCad CLI and libraries | Conversion and production output |
| KiCad's Python with `pcbnew` | InteractiveHtmlBom |
| Inkscape | PNG rendering |
| Git | Explicit upstream-source refreshes |

KiCad 10 supports Eagle PCB import, but its CLI does not import an Eagle
schematic/project pair. The existing paired-source refresh path requires a CLI
providing `kicad-cli import`; otherwise it fails explicitly. Use KiCad's
**File → Import Non-KiCad Project** for paired Eagle conversion, then save native
inputs. The migrated native KiCad inputs build without refreshing Eagle sources.

The committed `component_catalog` snapshot supplies component metadata and
assets. Ordinary builds do not access an electronics checkout.
Its compiled matching index contains the same IDs and explicit generic rules as
the saved component records, avoiding thousands of metadata reads per board.

## Build a selected project

Copy its ID from a project page. For example:

```powershell
$projectId = 'oomp_project_github_hanqaqa_easyduino_esp32_current'
python action_generate.py --filter $projectId
```

To explicitly fetch upstream changes and run the production, image, and
interactive BOM stages:

```powershell
python action_generate.py --filter $projectId --refresh-sources --production --images --ibom
```

Normal generation uses saved project inputs. Source refresh is explicit, so a
documentation rebuild cannot silently fetch a different upstream board.
`--regenerate-pngs` replaces preserved PNGs. Missing tools, missing inputs and
failed stages must be resolved before claiming a complete build.

| Task | Command |
| --- | --- |
| Populate definitions without building projects | `python action_generate.py --populate-only` |
| Refresh the component-usage pages | `python action_generate_usage.py` |
| Run the project test suite | `python -m pytest` |
| Check independence from sibling repositories | `python -S tools/run_isolated_tests.py -q` |

### Add a board

Edit `project_data/<owner>/working.yaml`; follow the
[worked example](ADDING_PROJECTS.md) and [definition guide](project_data/README.md).
Project IDs and existing
`parts/<project-id>` paths remain stable. Project records under `parts_source`
are derived from these definitions.
Historical records no longer present in the active definitions remain selectable
by their existing ID and are marked `definition_source: preserved_working_record`.
Their saved Git reference, inputs and review decisions are retained.

## Update the component snapshot

```powershell
python action_sync_component_catalog.py --source C:\gh\oomp_electronic_version_5
```

The default source is configured in [`project_config.json`](project_config.json)
and can point to a different location. It is used only by
the explicit sync command. Updates are copied and checksum-verified in staging,
then installed as a complete snapshot. A previous snapshot is retained at
`component_catalog.previous`; archive it before another update. Inspect the
snapshot manifest and matching changes before committing an update.

Snapshot hashes describe actual imported files. The source commit is recorded
for provenance; local source modifications are not represented by that commit.
Missing component assets are listed explicitly in the manifest.

## Links and publishing

Public repository and Pages addresses are configured in `project_config.json`.
Projects link to canonical component pages. `usage/index.html#<oomp-id>` shows
confirmed project usage and reports incomplete extraction coverage. It also
handles unknown component IDs without requiring a per-component page.

The Pages workflow publishes self-contained board explorers, interactive BOMs and usage pages.
CAD sources, drawings, manufacturing outputs and other downloads are linked from
GitHub. `tools/package_pages.py` checks the publication size before deployment.
Repository settings must use GitHub Actions as the Pages publishing source.

## IC naming

IC component IDs in the frozen catalogue use
`electronic_ic_<function>_<subtype>_<package>_<manufacturer>_<mpn>`.
Function, subtype, and package occupy taxonomy levels **3, 4, and 5**; levels
6–13 are empty and manufacturer/MPN remain at **14/15**. The package is the last
regular taxonomy field. Local `component_taxonomy.package_token` keeps matching
and display code independent of the electronics checkout.

See the [electronics intake guide](https://github.com/oomlout/oomp_electronic_version_5/blob/main/kicad_agents/JLC_PART_INTAKE_AGENT.md)
for adding components under this convention.

## Maintainer reference

[Project tooling](kicad_agents/README.md) · [Adding projects](ADDING_PROJECTS.md) · [Project definitions](project_data/README.md)

<details>
<summary>Repository split and migration history</summary>

### Repository split — 14 November 2026

The split preserved 915 saved projects and imported a dependency snapshot of
2,966 components. Existing drawings, explorers, manufacturing files and review
decisions were moved; no bulk documentation or board regeneration was performed.
Saved reverse usage was relocated without recomputing matches. Twelve projects
were marked as lacking extracted data.

At the split, the isolated project suite passed 92 tests, including native KiCad
conversion and fabrication checks. Four pre-existing assertions remained: the historical
Bus Pirate J302 rotation, IC1 being unmatched despite its saved confirmed match,
an old render zoom, and an old Bus Pirate version expectation. These failures
were checked against the original code/data and retained for separate repair;
the migration does not change board geometry to satisfy them.

### IC naming — 15 November 2026

The catalogue migration moved IC packages after their functional taxonomy and
recomputed MD5/base36/BIP39 codes from canonical IDs. The snapshot manifest
retains its original provenance and records the migration.

</details>

[example]: parts/oomp_project_github_adafruit_adafruit_16_channel_pwm_servo_shield_adafruit_pwm_servo_shield_current/README.md
[board-image]: parts/oomp_project_github_adafruit_adafruit_16_channel_pwm_servo_shield_adafruit_pwm_servo_shield_current/data/generated_data/src/board_300.png
[explorer]: https://oomlout.github.io/oomp_electronic_project_version_5/parts/oomp_project_github_adafruit_adafruit_16_channel_pwm_servo_shield_adafruit_pwm_servo_shield_current/board_explorer.html
