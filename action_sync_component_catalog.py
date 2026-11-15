"""Explicitly import a versioned component snapshot; normal builds never sync."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
import yaml
from project_config import ROOT, CONFIG

ASSETS = ('working.yaml', 'data/working_svg_assembly.svg',
          'data/working_svg_assembly_pins.svg', 'data/working_svg_square_pins.svg',
          'data/working_svg_outline.svg')

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def write_matching_index(catalog, files):
    """Compile the same ID and generic rules used by OompPartIndex once per sync."""
    records=[entry for entry in files if entry['path'].endswith('/working.yaml')]
    def metadata(entry):
        path=catalog/entry['path']
        if digest(path)!=entry['sha256']:
            raise RuntimeError('Snapshot metadata checksum mismatch: '+entry['path'])
        data=yaml.load(path.read_text(encoding='utf-8'),Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader)) or {}
        identifier=path.parent.name
        generic=None
        if identifier.startswith('electronic_') and data.get('generic_match'):
            generic={'oomp_id':identifier,'kind':data.get('taxonomy_2',''),
                     'package':data.get('taxonomy_3',''),'rules':data['generic_match']}
        return identifier,generic
    with ThreadPoolExecutor(max_workers=8) as workers:
        rows=sorted(workers.map(metadata,records))
    payload={'schema_version':1,'part_ids':[row[0] for row in rows],
             'generic_parts':[row[1] for row in rows if row[1]]}
    target=catalog/'matching_index.json'
    target.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    return {'path':target.name,'sha256':digest(target),'size':target.stat().st_size}

def sync(source):
    source = Path(source).resolve()
    if source == ROOT or not (source/'parts').is_dir():
        raise ValueError('Expected an electronics checkout containing parts/')
    stage = Path(tempfile.mkdtemp(prefix='component_catalog_stage_', dir=ROOT))
    try:
        paths=[]; availability={}
        for part in sorted((source/'parts').iterdir()):
            if not part.name.startswith(('electronic_', 'mechanical_')) or not (part/'working.yaml').is_file():
                continue
            availability[part.name]={'missing_assets':[]}
            for name in ASSETS:
                path=part/name
                if path.is_file(): paths.append(path)
                else: availability[part.name]['missing_assets'].append(name)
            library=part/'data/kicad'
            if library.is_dir(): paths.extend(p for p in library.rglob('*') if p.is_file())
        def copy(path):
            relative=path.relative_to(source)
            target=stage/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            before=digest(path)
            shutil.copy2(path,target)
            if before != digest(target) or before != digest(path):
                raise RuntimeError('Unstable or corrupt source: '+str(path))
            return {'path':relative.as_posix(),'sha256':before,'size':target.stat().st_size}
        with ThreadPoolExecutor(max_workers=6) as workers:
            files=list(workers.map(copy,paths))
        files.append(write_matching_index(stage,files))
        revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
        # Hashes describe the actual working snapshot, including local changes;
        # the commit is provenance and is not claimed to identify every byte.
        manifest={'schema_version':1,'source_repository':CONFIG['component_repository_url'],
                  'source_commit':revision,'source_state':'working-tree snapshot; file hashes are authoritative',
                  'files':files,'components':availability}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        destination=ROOT/'component_catalog'
        previous=ROOT/'component_catalog.previous'
        if previous.exists():
            raise RuntimeError('Previous snapshot already exists; archive it before another refresh')
        if destination.exists(): destination.rename(previous)
        try: stage.rename(destination)
        except Exception:
            if previous.exists(): previous.rename(destination)
            raise
        print(f'Snapshot: {len(availability)} components, {len(files)} verified files')
    except Exception:
        print('Incomplete staging directory retained:',stage)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/CONFIG['component_sync_source'])
    sync(parser.parse_args().source)
