"""Exercise the installed KiCad CLI on fresh fabrication inputs."""
import json
import subprocess
import zipfile
from pathlib import Path
import pytest
from kicad_agents.kicad_library_agent import Masters
from kicad_agents.production_jlc_agent import generate_jlc_production_files, PUBLIC_OUTPUT_FILENAMES

def test_native_fabrication_preserves_inputs_and_reports_missing_purchasing(tmp_path):
    try:
        masters=Masters()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    data=tmp_path/'board/data'; data.mkdir(parents=True)
    board=data/'kicad_file.kicad_pcb'
    script='''import pcbnew,sys
b=pcbnew.BOARD()
edge=pcbnew.PCB_SHAPE()
edge.SetShape(pcbnew.SHAPE_T_RECT)
edge.SetLayer(pcbnew.Edge_Cuts)
edge.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(10),pcbnew.FromMM(10)))
edge.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(30),pcbnew.FromMM(30)))
edge.SetWidth(pcbnew.FromMM(0.05))
b.Add(edge)
fp=pcbnew.FootprintLoad(sys.argv[1],'R_0603_1608Metric')
b.Add(fp)
fp.SetReference('R1'); fp.SetValue('2k2')
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(20),pcbnew.FromMM(20)))
pcbnew.SaveBoard(sys.argv[2],b)
'''
    subprocess.run([str(masters.root/'bin/python.exe'),'-c',script,
                    str(masters.library_root/'footprints/Resistor_SMD.pretty'),str(board)],
                   check=True,capture_output=True,text=True,timeout=120)
    original=board.read_bytes()
    empty_parts=tmp_path/'empty_catalog'; empty_parts.mkdir()
    output=generate_jlc_production_files({'directory':str(data.parent),'parts_directory':str(empty_parts)})
    assert output is not None
    assert {path.name for path in output.iterdir()}==set(PUBLIC_OUTPUT_FILENAMES)|{'data'}
    manifest=json.loads((output/'data/manifest.json').read_text())
    assert manifest['summary']['components_missing_lcsc']==1
    assert 'review' in manifest['status']
    with zipfile.ZipFile(output/'gerbers_jlc.zip') as archive:
        assert archive.testzip() is None
        assert archive.namelist()
    assert board.read_bytes()==original
