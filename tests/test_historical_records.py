import yaml
import action_generate
import working_oomp_populate_project

def test_historical_project_remains_selectable_and_keeps_its_inputs(tmp_path,monkeypatch):
    identifier='oomp_project_github_example_board_rev_a'
    directory=tmp_path/'parts'/identifier
    directory.mkdir(parents=True)
    original={'taxonomy_1':'oomp','taxonomy_2':'project','project_version':'rev_a',
              'project_git_ref':'fixed-old-revision','project_match_blocked':{'U1':'Needs review'},
              'oomlout_ai_roboclick_1':{'actions':[{'command':'legacy'}]}}
    (directory/'working.yaml').write_text(yaml.safe_dump(original))
    (directory/'saved.png').write_bytes(b'preserved')
    monkeypatch.setattr(action_generate,'ROOT',tmp_path)
    monkeypatch.setattr(action_generate,'PROJECT_PARTS',tmp_path/'parts')
    monkeypatch.setattr(working_oomp_populate_project,'main',lambda **kwargs: None)
    assert action_generate.populate(identifier)==[directory]
    saved=yaml.safe_load((directory/'working.yaml').read_text())
    assert saved['project_git_ref']==original['project_git_ref']
    assert saved['project_match_blocked']==original['project_match_blocked']
    assert saved['definition_source']=='preserved_working_record'
    assert 'oomlout_ai_roboclick_1' not in saved
    assert (directory/'saved.png').read_bytes()==b'preserved'
