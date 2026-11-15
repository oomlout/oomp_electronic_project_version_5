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
        'electronic_ic_amplifier_operational_dual_soic_8_example':{'taxonomy_2':'ic','taxonomy_3':'amplifier',
            'taxonomy_4':'operational_dual','taxonomy_5':'soic_8',
            'generic_match':{'values':['exampleamp'],'symbols':['Amplifier_Operational:Generic'],'footprints':['Package_SO:SOIC-8']}},
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
    assert next(row for row in compiled.generic_parts if row["kind"]=="ic")["package"]=="soic_8"
    evidence={'value':'example','library_id':'Device:D','footprint':'Diode_SMD:D_SOD-123'}
    assert original.generic_matches(evidence)==compiled.generic_matches(evidence)


def test_ic_display_uses_package_after_function():
    from working_oomp_metadata import readable_name
    from component_taxonomy import package_token
    data=dict(taxonomy_1='electronic',taxonomy_2='ic',taxonomy_3='amplifier',
              taxonomy_4='operational_dual',taxonomy_5='soic_8',part_number_manufacturer='EXAMPLE')
    assert package_token(data)=='soic_8'
    assert readable_name(data)=='IC EXAMPLE SOIC 8'
