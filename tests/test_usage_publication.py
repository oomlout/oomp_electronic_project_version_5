import json
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml
import action_generate_usage as usage

def fixture(tmp_path):
    parts=tmp_path/'parts'
    project=parts/'oomp_project_example'
    (project/'data/generated_data').mkdir(parents=True)
    (project/'working.yaml').write_text(yaml.safe_dump({'name_readable':'Example','project_github_url':'https://github.com/example/board'}))
    component=lambda ref,id,hole=False: {'reference':ref,'pcb':{'is_mounting_hole':hole},'oomp':{'status':'matched','oomp_id':id}}
    data=project/'data/generated_data/project.json'
    data.write_text(json.dumps({'components':[component('R10','resistor'),component('R2','resistor'),component('R2','resistor'),component('H1','hole',True)],'mounting_hole_items':[component('MH1','hole',True)]}))
    electronics=parts/'resistor/working.yaml'
    electronics.parent.mkdir()
    electronics.write_text('custom_note: keep me\n')
    return parts,project,data,electronics

def test_usage_counts_and_links_without_component_writes(tmp_path):
    parts,project,data,electronics=fixture(tmp_path)
    before=electronics.read_bytes()
    with patch.object(usage,'ROOT',tmp_path),patch.object(usage,'PROJECT_PARTS',parts):
        first=usage.generate_usage()
        second=usage.generate_usage()
    assert first==second
    assert electronics.read_bytes()==before
    assert first['usage']['resistor'][0]['references']==['R2','R10']
    assert first['usage']['resistor'][0]['quantity']==2
    assert first['usage']['hole'][0]['references']==['MH1']
    assert 'oomp_electronic_project_version_5' in first['usage']['resistor'][0]['oomp_url']

def test_missing_extraction_retains_explicitly_stale_usage_and_invalid_data_aborts(tmp_path):
    parts,project,data,electronics=fixture(tmp_path)
    with patch.object(usage,'ROOT',tmp_path),patch.object(usage,'PROJECT_PARTS',parts):
        usage.generate_usage()
        data.unlink()
        result=usage.generate_usage()
        assert result['unavailable_projects']==[project.name]
        assert result['usage']['resistor'][0]['extraction_available'] is False
        previous=(tmp_path/'usage/index.json').read_bytes()
        data.write_text('not json')
        with pytest.raises(json.JSONDecodeError): usage.generate_usage()
        assert (tmp_path/'usage/index.json').read_bytes()==previous

def test_successful_empty_extraction_removes_old_usage(tmp_path):
    parts,project,data,electronics=fixture(tmp_path)
    with patch.object(usage,'ROOT',tmp_path),patch.object(usage,'PROJECT_PARTS',parts):
        usage.generate_usage()
        data.write_text('{"components": []}')
        assert usage.generate_usage()['usage']=={}
