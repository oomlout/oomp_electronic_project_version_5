from action_generate import project_identifier
import working_oomp_populate_project
from kicad_agents.oomp_matching_agent import match_component

def test_easyduino_project_and_explicit_conflicts():
    projects=[]
    working_oomp_populate_project.main(options=projects)
    project=next(p for p in projects if p.get('project_board')=='esp32')
    assert project_identifier(project)=='oomp_project_github_hanqaqa_easyduino_esp32_current'
    assert project['project_file_path']=='ESP32/Easyduino_ESP32'
    assert set(project['project_match_blocked'])=={'U1','U4'}
    assert project['project_match_overrides']=={}
    component={'reference':'U1','pcb':{'value':'CP2102N','library_id':'Interface_USB:CP2102N'}}
    result=match_component(None,component,blocked=project['project_match_blocked'])
    assert not result['accepted']
    assert 'CP2102-GMR' in result['reasons'][0]
