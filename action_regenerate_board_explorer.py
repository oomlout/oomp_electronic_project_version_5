"""Regenerate board_explorer.html for project parts without a full rebuild."""

import argparse
from pathlib import Path

from project_config import ROOT as REPOSITORY_ROOT
from kicad_agents.project_html_agent import generate_board_explorer


def _project_part_directories(filter_text=""):
    parts_directory = REPOSITORY_ROOT / "parts"
    directories = []
    for part_directory in sorted(parts_directory.iterdir(), key=lambda path: path.name.lower()):
        if not part_directory.is_dir() or (filter_text and filter_text not in part_directory.name):
            continue
        generated = part_directory / "data" / "generated_data"
        if (generated / "project.json").is_file() and (generated / "project_summary_data.json").is_file():
            directories.append(part_directory)
    return directories


def _load_json(path):
    import json

    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def regenerate(filter_text=""):
    directories = _project_part_directories(filter_text)
    if not directories:
        print("No project parts with extracted data matched; run the project README action first.")
        return
    regenerated = 0
    failed = []
    for part_directory in directories:
        output_directory = part_directory / "data" / "generated_data"
        try:
            project_data = _load_json(output_directory / "project.json")
            summary_data = _load_json(output_directory / "project_summary_data.json")
            explorer_path = generate_board_explorer(
                part_directory,
                project_data,
                summary_data,
                output_directory=output_directory,
            )
        except Exception as error:
            failed.append((part_directory.name, error))
            print(f"failed {part_directory.name}: {error}")
            continue
        print(f"regenerated {explorer_path}")
        regenerated += 1
    print(f"Board explorer regeneration complete: {regenerated} regenerated, {len(failed)} failed.")
    if failed:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filter", default="", help="OOMP project part ID or prefix; omit to regenerate every project part")
    arguments = parser.parse_args()
    regenerate(filter_text=arguments.filter)


if __name__ == "__main__":
    main()
