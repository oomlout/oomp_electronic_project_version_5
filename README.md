# OOMP electronic projects

Project definitions, KiCad processing, board drawings, explorers and production
outputs. [Component catalogue](https://github.com/oomlout/oomp_electronic_version_5)
is maintained separately.

## Setup

On Windows, clone with `git clone -c core.longpaths=true` followed by this
repository's URL and your destination directory. Existing checkouts should use
`git config core.longpaths true` because saved board assets have long paths.

Use Python 3.12 or later. Install `requirements.txt` in a local virtual
environment. KiCad CLI and its libraries are needed for conversion and production;
KiCad's Python with `pcbnew` is needed for InteractiveHtmlBom. Inkscape is used for
PNG rendering. Git is needed when refreshing upstream sources.

KiCad 10 supports Eagle PCB import, but its CLI does not import an Eagle
schematic/project pair. The existing paired-source refresh path requires a CLI
providing `kicad-cli import`; otherwise it fails explicitly. Use KiCad's
**File → Import Non-KiCad Project** for paired Eagle conversion, then save native
inputs. The migrated native KiCad inputs build without refreshing Eagle sources.

The committed `component_catalog` snapshot supplies component metadata and
assets. Ordinary builds do not access an electronics checkout.
Its compiled matching index contains the same IDs and explicit generic rules as
the saved component records, avoiding thousands of metadata reads per board.

## Commands

```powershell
python action_generate.py --populate-only
python action_generate.py --filter <project-id>
python action_generate.py --filter <project-id> --refresh-sources --production --images --ibom
python action_generate_usage.py
python -m pytest
```

Normal generation uses saved project inputs. Source refresh is explicit, so a
documentation rebuild cannot silently fetch a different upstream board.
`--regenerate-pngs` replaces preserved PNGs. Missing tools, missing inputs and
failed stages must be resolved before claiming a complete build.

Edit `project_data/<owner>/working.yaml` to add boards. Project IDs and existing
`parts/<project-id>` paths remain stable. Project records under `parts_source`
are derived from these definitions.
Historical records no longer present in the active definitions remain selectable
by their existing ID and are marked `definition_source: preserved_working_record`.
Their saved Git reference, inputs and review decisions are retained.

## Component snapshot updates

```powershell
python action_sync_component_catalog.py --source C:\gh\oomp_electronic_version_5
```

The default source is configured in `project_config.json`. It is used only by
the explicit sync command. Updates are copied and checksum-verified in staging,
then installed as a complete snapshot. A previous snapshot is retained at
`component_catalog.previous`; archive it before another update. Inspect the
snapshot manifest and matching changes before committing an update.

Snapshot hashes describe actual imported files. The source commit is recorded
for provenance; local source modifications are not represented by that commit.
Missing component assets are listed explicitly in the manifest.

## Links and usage

Public repository and Pages addresses are configured in `project_config.json`.
Projects link to canonical component pages. `usage/index.html#<oomp-id>` shows
confirmed project usage and reports incomplete extraction coverage. It also
handles unknown component IDs without requiring a per-component page.

The Pages workflow publishes self-contained board explorers, interactive BOMs and usage pages.
CAD sources, drawings, manufacturing outputs and other downloads are linked from
GitHub. `tools/package_pages.py` checks the publication size before deployment.
Repository settings must use GitHub Actions as the Pages publishing source.

## Migration record — 2026-11-14

The split preserved 915 saved projects and imported a dependency snapshot of
2,966 components. Existing drawings, explorers, manufacturing files and review
decisions were moved; no bulk documentation or board regeneration was performed.
Saved reverse usage was relocated without recomputing matches. Twelve projects
were marked as lacking extracted data.

The isolated project suite passed 92 tests, including native KiCad conversion
and fabrication checks. Four existing assertions still fail: the historical
Bus Pirate J302 rotation, IC1 being unmatched despite its saved confirmed match,
an old render zoom, and an old Bus Pirate version expectation. These failures
were checked against the original code/data and retained for separate repair;
the migration does not change board geometry to satisfy them.
