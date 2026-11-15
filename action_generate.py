"""Populate and build projects using only this repository and its snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import yaml
from project_config import ROOT, PROJECT_PARTS, COMPONENT_PARTS, PROJECT_URL

def project_identifier(option):
    return '_'.join(str(option.get(f'taxonomy_{i}', '')).strip().replace(' ', '_').replace('.', '_')
                    for i in range(1,16) if option.get(f'taxonomy_{i}'))

def finalize_record(data, identifier):
    data.update(name=identifier,id=identifier,name_space=identifier.replace('_',' '))
    for key in list(data):
        if key.startswith('oomlout_') and 'roboclick' in key: data.pop(key)
    for key in ['link_github','link_main','link_redirect']:
        data[key]=PROJECT_URL+'/tree/main/parts/'+identifier
    data['generation_command']='python action_generate.py --filter '+identifier
    return data

def populate(filter_text=''):
    import working_oomp_populate_project
    import working_oomp_metadata
    options=[]
    working_oomp_populate_project.main(options=options)
    working_oomp_metadata.add_readable_metadata(options)
    seen=set(); selected=[]
    for option in options:
        identifier=project_identifier(option)
        if identifier in seen: raise ValueError('Duplicate project ID: '+identifier)
        seen.add(identifier)
        if filter_text and filter_text not in identifier: continue
        directory=PROJECT_PARTS/identifier
        directory.mkdir(parents=True,exist_ok=True)
        source=ROOT/'parts_source'/identifier/'working.yaml'
        source.parent.mkdir(parents=True,exist_ok=True)
        source.write_text(yaml.safe_dump(option,sort_keys=True,allow_unicode=True),encoding='utf-8')
        existing=directory/'working.yaml'
        data=yaml.safe_load(existing.read_text(encoding='utf-8')) if existing.exists() else {}
        data=data or {}
        data.update(option)
        data.pop('definition_source',None)
        finalize_record(data,identifier)
        existing.write_text(yaml.safe_dump(data,sort_keys=True,allow_unicode=True),encoding='utf-8')
        selected.append(directory)
    # Historical records remain valid saved build inputs even when the active
    # definitions have collapsed to a single current version.
    for directory in sorted(PROJECT_PARTS.glob('oomp_project_*')):
        identifier=directory.name
        if identifier in seen or (filter_text and filter_text not in identifier): continue
        working=directory/'working.yaml'
        if not working.is_file(): continue
        data=yaml.safe_load(working.read_text(encoding='utf-8')) or {}
        if data.get('taxonomy_1')!='oomp' or data.get('taxonomy_2')!='project':
            raise ValueError('Invalid preserved project record: '+identifier)
        finalize_record(data,identifier)
        data['definition_source']='preserved_working_record'
        working.write_text(yaml.safe_dump(data,sort_keys=True,allow_unicode=True),encoding='utf-8')
        selected.append(directory)
    return selected

def build(directory, *, refresh=False, production=False, images=False, ibom=False, regenerate_pngs=False):
    from kicad_agents.project_readme_action import compile_project_part, _project_sources_ready
    from kicad_agents.web_manifest_action import build_web_manifest
    metadata=yaml.safe_load((directory/'working.yaml').read_text(encoding='utf-8'))
    details={**metadata,'directory':str(directory),'parts_directory':str(COMPONENT_PARTS),
             'regenerate_pngs':regenerate_pngs}
    if refresh:
        from kicad_agents.project_git_action import refresh_project_files
        refresh_project_files(details)
    if not _project_sources_ready(directory):
        raise RuntimeError('Missing project inputs or upstream error: '+directory.name)
    compile_project_part(details)
    if ibom:
        from kicad_agents.interactive_html_bom_action import generate_interactive_html_bom
        generate_interactive_html_bom(details)
        status=yaml.safe_load((directory/'data/interactivehtmlbom/generation_status.yaml').read_text())
        if status.get('status') not in ('complete','success','generated'):
            raise RuntimeError('InteractiveHtmlBom did not succeed: '+str(status))
    if images:
        from kicad_agents.project_images_action import render_project_images
        if render_project_images(details) is None:
            raise RuntimeError('Project image rendering did not complete')
    if production:
        from kicad_agents.kicad_project_action import convert_project
        from kicad_agents.production_jlc_agent import generate_jlc_production_files
        if convert_project(details) is None:
            raise RuntimeError('Project conversion did not complete')
        result=generate_jlc_production_files(details)
        if result is None:
            raise RuntimeError('Production generation did not complete')
    build_web_manifest(details)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--filter',default='')
    p.add_argument('--populate-only',action='store_true')
    p.add_argument('--refresh-sources',action='store_true')
    p.add_argument('--production',action='store_true')
    p.add_argument('--images',action='store_true')
    p.add_argument('--ibom',action='store_true')
    p.add_argument('--regenerate-pngs',action='store_true')
    args=p.parse_args()
    os.chdir(ROOT)
    selected=populate(args.filter)
    if not selected: raise SystemExit('No matching project definitions')
    failures=[]
    if not args.populate_only:
        if not (COMPONENT_PARTS.parent/'manifest.json').is_file():
            raise SystemExit('Missing committed component snapshot; run action_sync_component_catalog.py explicitly')
        for directory in selected:
            try:
                build(directory,refresh=args.refresh_sources,production=args.production,
                      images=args.images,ibom=args.ibom,regenerate_pngs=args.regenerate_pngs)
            except Exception as error:
                failures.append({'project':directory.name,'error':str(error)})
                print(directory.name,error,flush=True)
    from action_generate_navigation import generate
    generate()
    from action_generate_usage import generate_usage
    generate_usage()
    report=ROOT/'report/build_result.json'
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps({'projects':len(selected),'failures':failures},indent=2),encoding='utf-8')
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
