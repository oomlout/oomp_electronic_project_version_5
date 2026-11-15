"""Local paths and public links for the independent project application."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'project_config.json').read_text(encoding='utf-8'))
PROJECT_PARTS = ROOT / 'parts'
COMPONENT_PARTS = ROOT / 'component_catalog' / 'parts'
PROJECT_URL = CONFIG['project_repository_url']
COMPONENT_URL = CONFIG['component_repository_url']
PAGES_URL = CONFIG['project_pages_url']

def component_parts(value=None):
    # Older saved action records use "parts". They now refer to the local
    # dependency snapshot, never to the project-only output directory.
    if value is None or str(value).replace('\\', '/') in ('parts', str(ROOT / 'parts').replace('\\', '/')):
        return COMPONENT_PARTS
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()
