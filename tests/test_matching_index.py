import json
import hashlib
from pathlib import Path
import yaml
from action_sync_component_catalog import write_matching_index
from kicad_agents.oomp_matching_agent import OompPartIndex

def test_compiled_index_preserves_live_metadata_matching(tmp_path):
    rows={
        'electronic_resistor_0603_2200_ohm':{'taxonomy_2':'resistor','taxonomy_3':'0603'},
        'electronic_diode_sod_123_example':{'taxonomy_2':'diode','taxonomy_3':'sod_123',
            'generic_match':{'values':['example'],'symbols':['Device:D'],'footprints':['Diode_SMD:D_SOD-123']}},
        'mechanical_mounting_hole_3_mm':{'taxonomy_2':'mounting_hole'},
    }
    files=[]
    for identifier,data in rows.items():
        path=tmp_path/'parts'/identifier/'working.yaml'
        path.parent.mkdir(parents=True)
        path.write_text(yaml.safe_dump(data))
        files.append({'path':path.relative_to(tmp_path).as_posix(),
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size})
    original=OompPartIndex(tmp_path/'parts')
    write_matching_index(tmp_path,files)
    compiled=OompPartIndex(tmp_path/'parts')
    assert original.parts==compiled.parts
    assert original.by_id==compiled.by_id
    assert original.generic_parts==compiled.generic_parts
    evidence={'value':'example','library_id':'Device:D','footprint':'Diode_SMD:D_SOD-123'}
    assert original.generic_matches(evidence)==compiled.generic_matches(evidence)
