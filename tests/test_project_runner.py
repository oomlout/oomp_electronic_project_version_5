"""The new runner replaces legacy generated Roboclick action-layout tests."""
from pathlib import Path
from unittest.mock import patch
import yaml
import pytest
from action_generate import build

def project(tmp_path):
    root=tmp_path/'example'
    root.mkdir()
    (root/'working.yaml').write_text(yaml.safe_dump({'name':'example','project_source_format':'eagle'}))
    return root

def test_build_does_not_fetch_implicitly_and_preserves_png_default(tmp_path):
    root=project(tmp_path)
    with patch('kicad_agents.project_readme_action._project_sources_ready',return_value=True), \
         patch('kicad_agents.project_readme_action.compile_project_part') as compile, \
         patch('kicad_agents.web_manifest_action.build_web_manifest'), \
         patch('kicad_agents.project_git_action.refresh_project_files') as refresh:
        build(root)
    refresh.assert_not_called()
    assert compile.call_args.args[0]['regenerate_pngs'] is False

def test_explicit_fetch_receives_source_format(tmp_path):
    root=project(tmp_path)
    with patch('kicad_agents.project_readme_action._project_sources_ready',return_value=True), \
         patch('kicad_agents.project_readme_action.compile_project_part'), \
         patch('kicad_agents.web_manifest_action.build_web_manifest'), \
         patch('kicad_agents.project_git_action.refresh_project_files') as refresh:
        build(root,refresh=True)
    assert refresh.call_args.args[0]['project_source_format']=='eagle'

def test_missing_inputs_fail_the_build(tmp_path):
    root=project(tmp_path)
    with patch('kicad_agents.project_readme_action._project_sources_ready',return_value=False):
        with pytest.raises(RuntimeError,match='Missing project inputs'): build(root)

def test_failed_image_stage_cannot_report_success(tmp_path):
    root=project(tmp_path)
    with patch('kicad_agents.project_readme_action._project_sources_ready',return_value=True), \
         patch('kicad_agents.project_readme_action.compile_project_part'), \
         patch('kicad_agents.project_images_action.render_project_images',return_value=None):
        with pytest.raises(RuntimeError,match='image rendering'): build(root,images=True)

def test_vendored_ibom_and_project_templates_exist():
    from project_config import ROOT
    assert (ROOT/'tools/interactive_html_bom/InteractiveHtmlBom/generate_interactive_bom.py').is_file()
    assert (ROOT/'source_file/template_jinja/project_summary/working.md.j2').is_file()
