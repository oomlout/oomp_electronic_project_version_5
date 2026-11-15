import shutil
import subprocess
from pathlib import Path
import pytest
from kicad_agents.kicad_library_agent import Masters
from kicad_agents.project_git_action import _convert_eagle_project, _convert_eagle_board
from kicad_agents.kicad_cli import supports_project_import

def test_eagle_pair_import_or_explicit_unsupported_error(tmp_path):
    try:
        masters=Masters()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    root=Path(__file__).resolve().parents[1]
    fixture=root/'parts/oomp_project_github_adafruit_adafruit_learning_system_guides_joy_button_pcb_current/data'
    inputs=[]
    for suffix in ('brd','sch'):
        source=fixture/f'source_eagle.{suffix}'
        target=tmp_path/source.name
        shutil.copyfile(source,target)
        inputs.append(target)
    original=[path.read_bytes() for path in inputs]
    output=tmp_path/'fresh'; output.mkdir()
    targets=[output/f'kicad_file.{suffix}' for suffix in ('kicad_pcb','kicad_sch','kicad_pro')]
    cli=masters.root/'bin/kicad-cli.exe'
    if not supports_project_import(cli):
        with pytest.raises(RuntimeError,match='Eagle schematic conversion requires'):
            _convert_eagle_project(*inputs,*targets,kicad_cli=cli)
        assert not any(path.exists() for path in targets)
        assert [path.read_bytes() for path in inputs]==original
        return
    _convert_eagle_project(*inputs,*targets,kicad_cli=cli)
    assert all(path.is_file() and path.stat().st_size>0 for path in targets)
    assert [path.read_bytes() for path in inputs]==original
    assert '(kicad_pcb' in targets[0].read_text(encoding='utf-8')
    assert '(kicad_sch' in targets[1].read_text(encoding='utf-8')

def test_actual_eagle_pcb_import(tmp_path):
    try:
        masters=Masters()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    root=Path(__file__).resolve().parents[1]
    fixture=root/'parts/oomp_project_github_adafruit_adafruit_learning_system_guides_joy_button_pcb_current/data/source_eagle.brd'
    source=tmp_path/'board.brd'; shutil.copyfile(fixture,source)
    original=source.read_bytes()
    output=tmp_path/'converted.kicad_pcb'
    _convert_eagle_board(source,output,masters.root/'bin/kicad-cli.exe')
    assert '(kicad_pcb' in output.read_text(encoding='utf-8')
    assert source.read_bytes()==original
