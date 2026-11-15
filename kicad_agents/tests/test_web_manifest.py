import tempfile
import unittest
from pathlib import Path
import yaml
from kicad_agents.web_manifest_action import build_web_manifest

class WebManifestTests(unittest.TestCase):

    def test_manifest_has_metadata_inventory_stats_descriptions_and_urls(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            part_directory = Path(temporary_directory) / 'electronic_test_part'
            (part_directory / 'data').mkdir(parents=True)
            working = {'id': 'electronic_test_part', 'name_readable': 'Electronic test part', 'taxonomy_1': 'electronic', 'taxonomy_2': 'resistor', 'dimensions_mm': {'length': 1.6, 'width': 0.8}, 'pins': {'pin_1': {'name': 'one'}, 'pin_2': {'name': 'two'}}, 'oomlout_ai_roboclick_1': {'actions': [{'command': 'example', 'file_output': 'data/missing.svg'}], 'file_test': 'data/present.svg'}}
            (part_directory / 'working.yaml').write_text(yaml.safe_dump(working), encoding='utf-8')
            (part_directory / 'README.md').write_text('# Test\n', encoding='utf-8')
            (part_directory / 'data' / 'present.svg').write_text('<svg/>', encoding='utf-8')
            action_details = {'directory': str(part_directory), 'file_output': str(part_directory / 'web.yaml')}
            manifest = build_web_manifest(action_details)
            first_render = (part_directory / 'web.yaml').read_bytes()
            build_web_manifest(action_details)
            self.assertEqual((part_directory / 'web.yaml').read_bytes(), first_render)
            self.assertEqual(manifest['id'], 'electronic_test_part')
            self.assertEqual(manifest['highlights']['pin_count'], 2)
            self.assertEqual(manifest['file_stats']['file_count'], 3)
            self.assertNotIn('total_size', manifest['file_stats'])
            self.assertNotIn('total_size_bytes', manifest['file_stats'])
            self.assertNotIn('oomlout_ai_roboclick_1', manifest['metadata'])
            self.assertEqual([item['path'] for item in manifest['files']], ['data/present.svg', 'README.md', 'working.yaml'])
            readme = next((item for item in manifest['files'] if item['path'] == 'README.md'))
            self.assertIn('Human-readable overview', readme['description'])
            self.assertNotIn('size', readme)
            self.assertNotIn('size_bytes', readme)
            self.assertEqual(readme['media_type'], 'text/markdown')
            self.assertEqual(readme['github_url'], 'https://github.com/oomlout/oomp_electronic_project_version_5/blob/main/parts/electronic_test_part/README.md')
            self.assertTrue(manifest['links']['manifest_github'].endswith('/electronic_test_part/web.yaml'))
            declared = {item['path']: item for item in manifest['generation']['declared_outputs']}
            self.assertTrue(declared['data/present.svg']['available'])
            self.assertFalse(declared['data/missing.svg']['available'])
if __name__ == '__main__':
    unittest.main()
