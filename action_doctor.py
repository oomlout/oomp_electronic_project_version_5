"""Report independent project prerequisites without modifying either checkout."""
import importlib.util
import json
import shutil
from pathlib import Path
from project_config import ROOT

def diagnose():
    checks={}
    for module in ('yaml','jinja2','PIL'):
        checks[module]=bool(importlib.util.find_spec(module))
    checks['component_snapshot']=(ROOT/'component_catalog/manifest.json').is_file()
    checks['project_definitions']=(ROOT/'project_data').is_dir()
    from kicad_agents.kicad_library_agent import find_kicad_root
    try: checks['kicad']=str(find_kicad_root())
    except FileNotFoundError: checks['kicad']=False
    checks['git']=shutil.which('git') or False
    checks['inkscape']=shutil.which('inkscape') or (str(Path('C:/Program Files/Inkscape/bin/inkscape.exe')) if Path('C:/Program Files/Inkscape/bin/inkscape.exe').exists() else False)
    from kicad_agents.kicad_cli import supports_project_import
    checks['optional_capabilities']={'eagle_project_import':supports_project_import() if checks['kicad'] else False}
    return checks

if __name__=='__main__':
    result=diagnose()
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if all(result.values()) else 1)
