"""Upgrade an existing checksummed snapshot without reading another checkout."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from action_sync_component_catalog import write_matching_index
from project_config import COMPONENT_PARTS

if __name__=='__main__':
    catalog=COMPONENT_PARTS.parent
    path=catalog/'manifest.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    files=[entry for entry in manifest['files'] if entry['path']!='matching_index.json']
    files.append(write_matching_index(catalog,files))
    manifest['files']=files
    temporary=path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
    print('Compiled matching index for',len(manifest['components']),'components',flush=True)
