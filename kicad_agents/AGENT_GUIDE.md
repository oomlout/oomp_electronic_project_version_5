# Project workflow

Edit project definitions in `project_data/<owner>/working.yaml`; follow
[Adding projects](../ADDING_PROJECTS.md). Generate using the commands in the
[repository README](../README.md).

Normal generation uses saved sources and a committed component snapshot.
`--refresh-sources` explicitly refreshes upstream Git sources. Only
`action_sync_component_catalog.py` reads an electronics checkout; its source path
is configurable in `project_config.json` or with `--source`.

Use exact identity evidence for component matches. Preserve blocked references,
ambiguities and review notes. Unknown parts must remain unmatched. Add new
components in the [electronics repository](https://github.com/oomlout/oomp_electronic_version_5),
then explicitly update the snapshot and inspect matching changes.

Component facts and datasheet research use the interactive browser. Python tools
extract and generate from saved evidence; they do not fetch supplier facts or
invent identities. `browser_research_agent.py` creates research queues and
validates browser-downloaded PDFs.

Inspect unmatched lists, review queues, both board sides, explorer interaction,
conversion reports and production reports. A generated fabrication bundle does
not mean purchasing, DRC or placement issues have been resolved. Follow
[production checks](PRODUCTION_JLC_GUIDE.md).

Existing PNGs are retained unless `--regenerate-pngs` is passed. Each failed stage
must produce a failed command result. Publish usage only in this repository;
never write component usage back into the electronics checkout.
