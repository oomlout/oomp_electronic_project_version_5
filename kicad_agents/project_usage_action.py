"""Collect confirmed matches and publish usage within the project repository.

Uses only saved, confirmed project matches. No browser, LLM or image generation.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from project_config import PROJECT_URL, PAGES_URL
REPOSITORY_PARTS_URL = PROJECT_URL + "/tree/main/parts"
PAGES_PARTS_URL = PAGES_URL + "/parts"


def reference_sort_key(reference):
    return [int(piece) if piece.isdigit() else piece.lower() for piece in re.split(r"(\d+)", reference)]


def build_usage_index(parts_directory="parts"):
    """Return one entry per part/project, plus projects not extracted yet."""
    parts_directory = Path(parts_directory).resolve()
    index = {}
    unavailable = []
    for working_file in sorted(parts_directory.glob("oomp_project_*/working.yaml")):
        project_directory = working_file.parent
        metadata = yaml.safe_load(working_file.read_text(encoding="utf-8")) or {}
        project_file = project_directory / "data" / "generated_data" / "project.json"
        if not project_file.is_file():
            unavailable.append(project_directory.name)
            continue
        # Parse every project before changing any part; invalid JSON must not
        # silently erase previously known usage.
        project = json.loads(project_file.read_text(encoding="utf-8"))
        if not isinstance(project.get("components"), list):
            raise ValueError(f"Missing component list in {project_file}")
        project_id = project_directory.name
        github_url = metadata.get("project_github_url", "")
        entry = {
            "project_id": project_id,
            "name": metadata.get("name_readable") or project_id,
            "version": metadata.get("project_version", "current"),
            "github_url": github_url,
            "board_url": metadata.get("project_board_url") or github_url,
            "oomp_url": f"{REPOSITORY_PARTS_URL}/{quote(project_id)}",
            "board_explorer_url": f"{PAGES_PARTS_URL}/{quote(project_id)}/board_explorer.html",
        }
        placements = {}
        for collection in ["components", "mounting_hole_items"]:
            for component in project.get(collection, []):
                match = component.get("oomp") or {}
                part_id = match.get("oomp_id")
                if match.get("status") != "matched" or match.get("accepted") is False or not part_id:
                    continue
                pcb = component.get("pcb") or {}
                if pcb.get("exclude_from_bom") or str(pcb.get("value", "")).strip().upper() == "DNF":
                    continue
                # Dedicated holes also appear as raw footprints. Count only
                # their classified MH items, not both representations.
                if collection == "components" and pcb.get("is_mounting_hole"):
                    continue
                reference = str(component.get("reference") or "")
                if not reference:
                    continue
                placement = [str(pcb.get("source_file") or ""), reference]
                if part_id not in placements:
                    placements[part_id] = []
                if placement not in placements[part_id]:
                    placements[part_id].append(placement)
        for part_id in sorted(placements):
            usage = copy.deepcopy(entry)
            usage["quantity"] = len(placements[part_id])
            usage["references"] = sorted([item[1] for item in placements[part_id]], key=reference_sort_key)
            index.setdefault(part_id, []).append(usage)
    return index, unavailable


def refresh_project_usage(parts_directory="parts", render_readmes=True):
    """Publish project-owned usage; never rewrite component records."""
    from project_config import PROJECT_PARTS
    requested = Path(parts_directory)
    if str(requested) != "parts" and requested.resolve() != PROJECT_PARTS:
        raise ValueError("Usage publishing only supports this repository's project parts")
    from action_generate_usage import generate_usage
    return generate_usage()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts-dir", default="parts")
    parser.add_argument("--no-readmes", action="store_true")
    parser.add_argument("--kwargs", help="JSON supplied by the Roboclick run_python action")
    arguments = parser.parse_args()
    details = json.loads(arguments.kwargs) if arguments.kwargs else {}
    result = refresh_project_usage(
        details.get("parts_directory", arguments.parts_dir),
        render_readmes=not arguments.no_readmes,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
