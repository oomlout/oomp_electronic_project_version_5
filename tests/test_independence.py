import importlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def test_imports_owned_by_project_checkout():
    for name in ['project_config','working_oomp_populate_project', 'action_generate',
                 'action_regenerate_all', 'action_regenerate_part', 'action_regenerate_board_explorer',
                 'action_unmatched_component_check', 'action_generate_usage',
                 'kicad_agents.kicad_processing_agent','kicad_agents.project_readme_action',
                 'kicad_agents.kicad_project_action','kicad_agents.production_jlc_agent']:
        module=importlib.import_module(name)
        assert Path(module.__file__).resolve().is_relative_to(ROOT)

def test_catalog_is_complete_and_checksummed():
    import hashlib
    from concurrent.futures import ThreadPoolExecutor
    manifest=json.loads((ROOT/'component_catalog/manifest.json').read_text())
    assert manifest['components']
    def verify(entry):
        path=ROOT/'component_catalog'/entry['path']
        assert path.stat().st_size==entry['size']
        with path.open('rb') as source:
            assert hashlib.file_digest(source,'sha256').hexdigest()==entry['sha256']
    with ThreadPoolExecutor(max_workers=8) as workers:
        for count,_ in enumerate(workers.map(verify,manifest['files']),1):
            if count%10000==0: print(f'Verified {count}/{len(manifest["files"])} snapshot files',flush=True)

def test_saved_parts_argument_resolves_to_snapshot():
    from project_config import component_parts, COMPONENT_PARTS
    assert component_parts()==COMPONENT_PARTS
    assert component_parts('parts')==COMPONENT_PARTS
    assert component_parts(ROOT/'parts')==COMPONENT_PARTS

def test_project_population_has_no_external_framework_import():
    import ast
    tree=ast.parse((ROOT/'action_generate.py').read_text())
    forbidden={'oomp','oomp_helper','oomp_populate_helper','oomlout_roboclick'}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            assert not any(alias.name in forbidden for alias in node.names)
        if isinstance(node,ast.ImportFrom): assert node.module not in forbidden
