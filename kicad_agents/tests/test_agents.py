import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path
import yaml
from kicad_agents.kicad_processing_agent import process_project
from kicad_agents.project_summary_agent import _orientation_rotation
from kicad_agents.browser_research_agent import build_browser_research_queue, import_browser_datasheet
import kicad_agents.kicad_processing_agent as kicad_processing_agent
from kicad_agents import interactive_html_bom_action
from kicad_agents.project_images_action import render_project_images
from kicad_agents.project_git_action import _convert_eagle_board, _convert_eagle_project, refresh_project_files
import kicad_agents.project_git_action as project_git_action
from kicad_agents.kicad_cli import find_kicad_cli
from kicad_agents.sexpr import children, load, tag, value
import working_oomp_populate_project
import working_oomp_metadata
from kicad_agents.pcb_copper import add_copper_svg, copper_svg
from kicad_agents.project_html_agent import _lcsc_search_value
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
from project_config import COMPONENT_PARTS, PROJECT_PARTS
PARTS_DIRECTORY = COMPONENT_PARTS
PROJECT_PART = PROJECT_PARTS / 'oomp_project_github_electrolama_pt1_current'
BUS_PIRATE_PART = PROJECT_PARTS / 'oomp_project_github_dangerousprototypes_buspirate5_hardware_5_rev10a'
SAMPLE_PROJECT = PROJECT_PART
SAMPLE_SCHEMATIC = SAMPLE_PROJECT / 'data' / 'kicad_file.kicad_sch'

class LcscSearchTests(unittest.TestCase):

    def test_passive_search_values_use_package_and_compact_value(self):
        resistor = {'taxonomy_1': 'electronic', 'taxonomy_2': 'resistor', 'taxonomy_3': '0402', 'taxonomy_4': '10000_ohm'}
        working_oomp_metadata.add_lcsc_search(resistor)
        self.assertEqual(resistor['lcsc_search'], '0402 10kΩ')
        through_hole = {'taxonomy_1': 'electronic', 'taxonomy_2': 'resistor', 'taxonomy_3': 'quarter_watt_through_hole', 'taxonomy_4': '10000_ohm'}
        working_oomp_metadata.add_lcsc_search(through_hole)
        self.assertEqual(through_hole['lcsc_search'], '10kΩ through hole')
        capacitor = {'taxonomy_1': 'electronic', 'taxonomy_2': 'capacitor', 'taxonomy_3': '1206', 'taxonomy_4': '47_micro_farad'}
        working_oomp_metadata.add_lcsc_search(capacitor)
        self.assertEqual(capacitor['lcsc_search'], '1206 47uF')
        electrolytic = {'taxonomy_1': 'electronic', 'taxonomy_2': 'capacitor', 'taxonomy_3': '6_3_mm_diameter_5_4_mm_tall', 'taxonomy_4': 'electrolytic', 'taxonomy_5': '220_micro_farad', 'taxonomy_6': '10_volt'}
        working_oomp_metadata.add_lcsc_search(electrolytic)
        self.assertEqual(electrolytic['lcsc_search'], '220uF 10V electrolytic')
        header = {'taxonomy_1': 'electronic', 'taxonomy_2': 'connector', 'taxonomy_3': 'header', 'taxonomy_4': '2_54_mm_pitch', 'taxonomy_5': 'through_hole', 'taxonomy_6': '10_pin'}
        working_oomp_metadata.add_lcsc_search(header)
        self.assertEqual(header['lcsc_search'], '2.54mm header 10 pin through hole')

    def test_part_numbers_and_explicit_values_win(self):
        ic = {'taxonomy_1': 'electronic', 'taxonomy_2': 'ic', 'taxonomy_3': 'tsot_23_5', 'taxonomy_4': 'power_management', 'part_number_manufacturer': 'RT9742CGJ5'}
        working_oomp_metadata.add_lcsc_search(ic)
        self.assertEqual(ic['lcsc_search'], 'RT9742CGJ5')
        explicit = {'taxonomy_1': 'electronic', 'taxonomy_2': 'resistor', 'taxonomy_3': '0402', 'taxonomy_4': '10000_ohm', 'lcsc_search': '0402 10k 1%'}
        working_oomp_metadata.add_lcsc_search(explicit)
        self.assertEqual(explicit['lcsc_search'], '0402 10k 1%')

    def test_unmatched_components_fall_back_to_footprint_size_and_value(self):
        capacitor = {'pcb': {'value': '100n', 'library_id': 'Capacitor_SMD:C_0402_1005Metric'}}
        self.assertEqual(_lcsc_search_value(capacitor, {}), '0402 100nF')
        resistor = {'pcb': {'value': '10k', 'library_id': 'Resistor_SMD:R_0603_1608Metric'}}
        self.assertEqual(_lcsc_search_value(resistor, {}), '0603 10kΩ')
        part_number = {'pcb': {'value': 'RT9742CGJ5', 'library_id': 'Package_TO_SOT_SMD:SOT-23-5'}}
        self.assertEqual(_lcsc_search_value(part_number, {}), 'RT9742CGJ5')
        declared = {'lcsc_search': 'custom query'}
        self.assertEqual(_lcsc_search_value({'pcb': {'value': '10k'}}, declared), 'custom query')

class CopperPadLayeringTests(unittest.TestCase):

    def test_board_copper_renders_below_component_artwork(self):
        features = [{'kind': 'segment', 'start': [0, 0], 'end': [1, 0], 'width': 0.2, 'layers': ['F.Cu'], 'net': 'GND', 'net_id': 'net_0_0', 'reference': '', 'number': ''}, {'kind': 'pad', 'position': [1, 1], 'rotation': 0, 'size': [1, 0.6], 'shape': 'rect', 'layers': ['F.Cu'], 'net': 'GND', 'net_id': 'net_0_0', 'reference': 'R1', 'number': '1', 'roundrect_rratio': 0, 'anchor': 'rect', 'primitives': []}]
        drawing = copper_svg(features)
        self.assertIn('copper-segment', drawing)
        self.assertIn('copper-pad', drawing)
        board = '<svg viewBox="0 0 10 10"><g class="board-component" data-reference="R1"><rect class="component" x="1" y="1" width="2" height="1"/></g><g class="indicator"><rect/></g></svg>'
        composed = add_copper_svg(board, drawing)
        copper_index = composed.find('class="copper-base"')
        self.assertLess(copper_index, composed.find('class="board-component"'))
        self.assertNotIn('class="copper-pads"', composed)
        mirrored = add_copper_svg(board, drawing, mirror=True)
        self.assertIn('class="copper-base" transform="translate(', mirrored)

class SExpressionTests(unittest.TestCase):

    def test_reads_modern_sample_schematic(self):
        root = load(SAMPLE_SCHEMATIC)
        self.assertEqual(tag(root), 'kicad_sch')
        self.assertEqual(value(root, 'version'), '20260306')
        self.assertEqual(len(children(root, 'symbol')), 64)
        self.assertEqual(len(children(root, 'wire')), 177)

class ProcessingAgentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.output_directory = Path(cls.temporary_directory.name) / 'generated_data'
        cls.project_data, _ = process_project(SAMPLE_PROJECT, PARTS_DIRECTORY, output_directory=cls.output_directory)
        cls.components = {component['reference']: component for component in cls.project_data['components']}

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def test_project_counts_and_formats(self):
        summary = self.project_data['summary']
        self.assertEqual(summary['schematic_symbol_count'], 64)
        self.assertEqual(summary['pcb_footprint_count'], 37)
        self.assertEqual(summary['component_count'], 67)
        self.assertEqual(summary['mounting_hole_count'], 9)
        self.assertEqual(summary['dedicated_mounting_hole_count'], 3)
        json.loads((self.output_directory / 'project.json').read_text(encoding='utf-8'))
        yaml.safe_load((self.output_directory / 'project.yaml').read_text(encoding='utf-8'))

    def test_c1_positions_connectivity_size_and_match(self):
        component = self.components['C1']
        self.assertEqual(component['category'], 'capacitor')
        self.assertEqual(component['category_name'], 'Capacitor')
        self.assertEqual(component['category_source'], 'oomp_populate')
        schematic_unit = component['schematic']['units'][0]
        self.assertEqual(schematic_unit['position']['x'], 73.66)
        self.assertEqual(schematic_unit['position']['y'], 40.64)
        self.assertEqual(schematic_unit['position']['rotation'], 90.0)
        self.assertEqual(schematic_unit['pins'][0]['number'], '1')
        self.assertEqual(schematic_unit['pins'][0]['position'], {'x': 73.66, 'y': 43.18})
        self.assertEqual(schematic_unit['pins'][0]['net'], 'GND')
        self.assertEqual(schematic_unit['pins'][1]['number'], '2')
        self.assertEqual(schematic_unit['pins'][1]['position'], {'x': 73.66, 'y': 38.1})
        self.assertEqual(schematic_unit['pins'][1]['net'], 'VUSB_IN')
        self.assertEqual(schematic_unit['size']['local_graphics']['width'], 5.2324)
        self.assertEqual(component['pcb']['position']['x'], 149.7511)
        self.assertEqual(component['pcb']['position']['y'], 119.1286)
        self.assertEqual(component['oomp']['oomp_id'], 'electronic_capacitor_0402_10_nano_farad')

    def test_pcb_rotation_is_converted_from_kicad_to_svg_coordinates(self):
        j1_position = self.components['J1']['pcb']['position']
        con2_position = self.components['CON2']['pcb']['position']
        self.assertEqual(j1_position['rotation_kicad'], -90.0)
        self.assertEqual(j1_position['rotation'], 90.0)
        self.assertEqual(con2_position['rotation_kicad'], -90.0)
        self.assertEqual(con2_position['rotation'], 90.0)
        con2_pads = self.components['CON2']['pcb']['pads']
        con2_ground = next((pad for pad in con2_pads if pad['number'] == 'GND@1'))
        self.assertEqual(con2_ground['position'], {'x': 145.7561, 'y': 96.7536})

    def test_mounting_holes_retain_drill_plating_and_positions(self):
        holes = self.project_data['mounting_holes']
        self.assertEqual(len(holes), 9)
        standalone_hole = self.components['UNK_HOLE_0']
        self.assertTrue(standalone_hole['pcb']['is_mounting_hole'])
        self.assertEqual(standalone_hole['oomp']['oomp_id'], 'mechanical_mounting_hole_2_mm_round_unplated')
        standalone_record = standalone_hole['pcb']['mounting_holes'][0]
        self.assertEqual(standalone_record['drill_size']['diameter'], 2.0)
        self.assertEqual(standalone_record['plating'], 'unplated')
        self.assertEqual(standalone_record['position'], {'x': 141.7511, 'y': 93.3786})
        usb_a_holes = self.components['CON3']['pcb']['mounting_holes']
        self.assertEqual(len(usb_a_holes), 2)
        self.assertTrue(all((hole['plating'] == 'plated' for hole in usb_a_holes)))
        self.assertTrue(all((hole['drill_size']['diameter'] == 0.8 for hole in usb_a_holes)))
        header_holes = self.components['J1']['pcb']['mounting_holes']
        self.assertEqual(header_holes, [])
        mounting_hole_items = self.project_data['mounting_hole_items']
        self.assertEqual(len(mounting_hole_items), 9)
        self.assertEqual([item['reference'] for item in mounting_hole_items], [f'MH{number}' for number in range(1, 10)])
        self.assertTrue(all((item['classification']['taxonomy_path'][0:2] == ['mechanical', 'mounting_hole'] for item in mounting_hole_items)))
        self.assertTrue((self.output_directory / 'components' / 'MH1' / 'oomp' / 'working.yaml').is_file())
        self.assertTrue((self.output_directory / 'mounting_holes.json').is_file())
        self.assertTrue((self.output_directory / 'mounting_holes.yaml').is_file())

    def test_component_folder_contract_and_oomp_copy(self):
        component_directory = self.output_directory / 'components' / 'C1'
        expected_files = [component_directory / 'component.json', component_directory / 'component.yaml', component_directory / 'schematic' / 'working.yaml', component_directory / 'schematic' / 'size.yaml', component_directory / 'pcb' / 'working.yaml', component_directory / 'pcb' / 'size.yaml', component_directory / 'oomp' / 'match.yaml', component_directory / 'oomp' / 'working.yaml']
        for expected_file in expected_files:
            self.assertTrue(expected_file.is_file(), expected_file)
        copied = component_directory / 'oomp' / 'working.yaml'
        source = PARTS_DIRECTORY / 'electronic_capacitor_0402_10_nano_farad' / 'working.yaml'
        self.assertEqual(copied.read_bytes(), source.read_bytes())

    def test_unmatched_and_non_physical_are_separate(self):
        unmatched = json.loads((self.output_directory / 'unmatched_parts.json').read_text(encoding='utf-8'))
        unmatched_references = {component['reference'] for component in unmatched['components']}
        self.assertIn('IC1', unmatched_references)
        self.assertNotIn('#GND1', unmatched_references)
        self.assertEqual(self.components['#GND1']['oomp']['status'], 'not_applicable')

class ProjectPartTests(unittest.TestCase):

    def test_browser_research_queue_is_explicit_and_browser_only(self):
        project_data = {'components': [{'reference': 'U1', 'pcb': {'value': 'example123', 'library_id': 'Package_SO:SOIC-8', 'exclude_from_bom': False}, 'oomp': {'status': 'unmatched', 'inferred': {'mpn': 'EXAMPLE123'}, 'candidates': []}}, {'reference': 'C1', 'pcb': {'value': 'DNF', 'library_id': 'Capacitor_SMD:C_0402_1005Metric', 'exclude_from_bom': False}, 'oomp': {'status': 'unmatched'}}]}
        queue = build_browser_research_queue(project_data)
        self.assertEqual(queue['task_count'], 1)
        self.assertEqual(queue['tasks'][0]['references'], ['U1'])
        self.assertIn('https://www.lcsc.com/search?q=', queue['tasks'][0]['browser_urls']['lcsc_search'])
        self.assertIs(queue['network_policy']['python_http_clients_allowed'], False)

    def test_browser_datasheet_import_validates_pdf_and_writes_provenance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            downloaded_file = temporary_path / 'download.pdf'
            downloaded_file.write_bytes(b'%PDF-1.7\nexample')
            parts_source_directory = temporary_path / 'parts_source'
            destination = import_browser_datasheet('electronic_ic_test', downloaded_file, 'https://example.com/datasheet.pdf', parts_source_directory)
            self.assertTrue(destination.is_file())
            provenance = yaml.safe_load((destination.parent / 'datasheet_source.yaml').read_text(encoding='utf-8'))
            self.assertEqual(provenance['acquisition_method'], 'interactive_browser')
            self.assertEqual(provenance['file_size_bytes'], len(b'%PDF-1.7\nexample'))
            self.assertEqual(len(provenance['sha256']), 64)
            second_destination = import_browser_datasheet('electronic_ic_test', downloaded_file, 'https://example.com/datasheet.pdf', parts_source_directory)
            self.assertEqual(second_destination, destination)

    def test_process_project_logs_missing_modern_source_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            project_directory = temporary_path / 'part'
            output_directory = project_directory / 'data' / 'generated_data'
            output_directory.mkdir(parents=True)
            with mock.patch.object(kicad_processing_agent, 'REPOSITORY_ROOT', temporary_path):
                project_data, returned_output_directory = process_project(project_directory, PARTS_DIRECTORY, output_directory=output_directory)
            self.assertIsNone(project_data)
            self.assertEqual(returned_output_directory, output_directory.resolve())
            log_path = temporary_path / 'report' / 'errors_during_run.txt'
            self.assertTrue(log_path.is_file())
            self.assertIn('No modern .kicad_sch files found', log_path.read_text(encoding='utf-8'))

    def test_process_project_accepts_a_pcb_only_project(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_directory = Path(temporary_directory) / 'part'
            data_directory = project_directory / 'data'
            data_directory.mkdir(parents=True)
            (data_directory / 'kicad_file.kicad_pcb').write_text('(kicad_pcb (version 20221018) (generator pcbnew) (general (thickness 1.6)) (paper "A4") (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user) (37 "F.SilkS" user) (44 "Edge.Cuts" user)))', encoding='utf-8')
            project_data, _ = process_project(project_directory, PARTS_DIRECTORY)
        self.assertIsNotNone(project_data)
        self.assertEqual(project_data['summary']['schematic_symbol_count'], 0)
        self.assertEqual(project_data['summary']['pcb_footprint_count'], 0)

    def test_kicad_10_eagle_transform_preserves_footprint_placement(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_directory = Path(temporary_directory) / 'part'
            data_directory = project_directory / 'data'
            data_directory.mkdir(parents=True)
            board_path = data_directory / 'kicad_file.kicad_pcb'
            board_path.write_text('(kicad_pcb (version 20260101) (generator pcbnew) (footprint "imported:C_0603" (layer "F.Cu") (transform (translate 6.1976 -11.938) (rotate 90) (scale 1 1)) (property "Reference" "C1") (property "Value" "100nF") (pad "1" smd rect (at -0.85 0 90) (size 1.1 1) (layers "F.Cu"))))', encoding='utf-8')
            parsed = kicad_processing_agent._parse_pcb(board_path, project_directory)
        footprint = parsed['footprints'][0]
        self.assertEqual(footprint['position'], {'x': 6.1976, 'y': -11.938, 'rotation': -90.0, 'rotation_kicad': 90.0, 'units': 'mm'})
        self.assertEqual(footprint['pads'][0]['position'], {'x': 6.1976, 'y': -11.088})

    def test_project_populator_defaults_to_current_and_allows_version_records(self):
        options = []
        working_oomp_populate_project.main(options=options)
        self.assertGreater(len(options), 8)
        project = next((option for option in options if option['project_github_repository'] == 'pt1'))
        taxonomy = [project[f'taxonomy_{number}'] for number in range(1, 7)]
        self.assertEqual(taxonomy, ['oomp', 'project', 'github', 'electrolama', 'pt1', 'current'])
        self.assertEqual(project['project_file_folder'], 'pcba/Rev A2')
        self.assertEqual(project['project_file_basename'], 'pt1-RevA2')
        bus_pirate = next((option for option in options if option['project_github_repository'] == 'buspirate5_hardware'))
        bus_taxonomy = [bus_pirate[f'taxonomy_{number}'] for number in range(1, 7)]
        self.assertEqual(bus_taxonomy, ['oomp', 'project', 'github', 'dangerousprototypes', 'buspirate5_hardware', '5_rev10a'])
        self.assertIs(bus_pirate['project_sparse_checkout'], True)
        self.assertEqual(bus_pirate['project_file_folder'], 'bus_pirate_pcb/5-REV10A')
        easyduino_nano = next((option for option in options if option['project_github_repository'] == 'easyduino' and option['project_board'] == 'atmega328p_arduino_nano'))
        self.assertEqual([easyduino_nano[f'taxonomy_{n}'] for n in range(1, 8)], ['oomp', 'project', 'github', 'hanqaqa', 'easyduino', 'atmega328p_arduino_nano', 'current'])
        self.assertEqual(easyduino_nano['project_git_ref'], 'master')
        self.assertEqual(easyduino_nano['project_file_basename'], 'Easyduino_Atmega_Nano')
        easyduino = next((option for option in options if option['project_github_repository'] == 'easyduino' and option['project_board'] == 'atmega328p_arduino_uno'))
        self.assertEqual([easyduino[f'taxonomy_{n}'] for n in range(1, 8)], ['oomp', 'project', 'github', 'hanqaqa', 'easyduino', 'atmega328p_arduino_uno', 'current'])
        self.assertEqual(easyduino['project_git_ref'], 'master')
        self.assertEqual(easyduino['project_file_basename'], 'Easyduino_Atmega')
        easyduino_esp32s3 = next((option for option in options if option['project_github_repository'] == 'easyduino' and option['project_board'] == 'esp32s3'))
        self.assertEqual(easyduino_esp32s3['project_file_basename'], 'Easyduino_ESP32S3')
        easyduino_pico = next((option for option in options if option['project_github_repository'] == 'easyduino' and option['project_board'] == 'raspberry_pi_pico_2040'))
        self.assertEqual(easyduino_pico['project_file_basename'], 'Easyduino_RP2040')
        easyduino_bluepill = next((option for option in options if option['project_github_repository'] == 'easyduino' and option['project_board'] == 'stm32f103_bluepill'))
        self.assertEqual(easyduino_bluepill['project_file_basename'], 'Easyduino_STM32F103')
        thermocouple = next((option for option in options if option['project_github_repository'] == 'Thermocouple-sensor-AD8495-breakout-hardware-design'))
        self.assertEqual(thermocouple['project_file_folder'], 'CAD/V1.0.0')
        self.assertEqual(thermocouple['project_file_basename'], 'K-pair-adapter')
        capacitive_soil = next((option for option in options if option['project_github_repository'] == 'Capacitive-soil-sensor-hardware-design'))
        self.assertEqual(capacitive_soil['project_file_folder'], 'CAD/V2.0.0')
        self.assertEqual(capacitive_soil['project_file_basename'], 'Capacitive soil sensor')
        ltr507als = next((option for option in options if option['project_github_repository'] == 'Digital-light---proximity-sensor-LTR-507ALS-breakout-hardware-design'))
        self.assertEqual(ltr507als['project_file_basename'], 'Light_sensor_LTR-507ALS-01')
        ina219 = next((option for option in options if option['project_github_repository'] == 'Voltage---current-sensor-INA219-breakout-hardware-design'))
        self.assertEqual(ina219['project_file_folder'], 'CAD/V1.0.0')
        self.assertEqual(ina219['project_file_basename'], 'INA219_breakout')
        acs712 = next((option for option in options if option['project_github_repository'] == 'Current-sensor-30A-ACS712-breakout-hardware-design'))
        self.assertEqual(acs712['project_file_folder'], 'CAD/V2.0.0')
        self.assertEqual(acs712['project_file_basename'], 'Current_sensor_ACS712')
        gnss_easyc = next((option for option in options if option['project_github_repository'] == 'GNSS-GPS-L86-M33-breakout-with-easyC-hardware-design'))
        self.assertEqual(gnss_easyc['project_file_folder'], 'CAD/V1.1.0')
        self.assertEqual(gnss_easyc['project_file_basename'], 'GNSS GPS L86-M33 breakout with easyC')
        pms7003 = next((option for option in options if option['project_github_repository'] == 'PMS7003-sensor-adapter-hardware-design'))
        self.assertEqual(pms7003['project_file_basename'], 'PMS7003_sensor_adapter')

    def test_project_yaml_accepts_the_minimal_project_path_definition(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_directory = Path(temporary_directory)
            user_directory = data_directory / 'example_user'
            user_directory.mkdir()
            (user_directory / 'working.yaml').write_text('github_user: example_user\nprojects:\n  - github_repository: example_board\n    versions:\n      - project_file_path: hardware/example_board\n', encoding='utf-8')
            projects = working_oomp_populate_project._load_project_files(data_directory)
        project = projects[0]
        version = project['versions'][0]
        self.assertEqual(project['github_url'], 'https://github.com/example_user/example_board')
        self.assertEqual(project['repository_url'], 'https://github.com/example_user/example_board.git')
        self.assertEqual(version['project_file_folder'], 'hardware')
        self.assertEqual(version['project_file_basename'], 'example_board')

    def test_project_populator_normalizes_taxonomy_and_github_user_ids(self):
        options = []
        working_oomp_populate_project.main(options=options)
        project = next((option for option in options if option['project_github_user'] == 'soldered_electronics' and option['project_github_repository'] == 'Butane--LPG---Smoke-sensor-MQ2-breakout-hardware-design'))
        self.assertEqual(project['taxonomy_4'], 'soldered_electronics')
        self.assertEqual(project['taxonomy_5'], 'butane_lpg_smoke_sensor_mq2_breakout_hardware_design')
        self.assertEqual(project['project_github_user'], 'soldered_electronics')

    def test_project_git_action_writes_error_file_when_fetch_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            part_directory = Path(temporary_directory) / 'test_project'
            part_directory.mkdir()
            details = {'directory': str(part_directory), 'project_git_url': 'https://example.invalid/not_real_repo.git', 'project_github_repository': 'not_real_repo', 'project_file_basename': 'BrokenBoard', 'project_file_folder': 'CAD/V1', 'project_file_extensions': ['.kicad_pcb', '.kicad_sch', '.kicad_pro'], 'project_sparse_checkout': True, 'project_git_ref': 'main'}
            with self.assertRaises((RuntimeError, OSError, ValueError)):
                refresh_project_files(details)
            error_file = part_directory / 'data' / 'error.txt'
            self.assertTrue(error_file.is_file())
            error_text = error_file.read_text(encoding='utf-8')
            self.assertIn('Project data fetch failed.', error_text)
            self.assertIn('Repository URL', error_text)
            self.assertIn('BrokenBoard', error_text)

    def test_project_git_action_uses_short_temp_workspace(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            part_directory = Path(temporary_directory) / 'a' / 'very' / 'long' / 'part' / 'path'
            details = {'directory': str(part_directory), 'project_git_url': 'https://github.com/sparkfun/SparkFun_Qwiic_Current_Sensor_ADE7953.git', 'project_github_repository': 'SparkFun_Qwiic_Current_Sensor_ADE7953', 'project_file_basename': 'CurrentSensor', 'project_file_folder': 'CAD/V1', 'project_file_extensions': ['.kicad_pcb'], 'project_sparse_checkout': False, 'project_git_ref': 'main'}
            repository_directory = project_git_action._repository_workspace_directory(details)
            self.assertTrue(str(repository_directory).startswith(str(Path(tempfile.gettempdir()))))
            self.assertIn('oomp_git_cache', str(repository_directory))
            self.assertNotIn(str(part_directory), str(repository_directory))

    def test_eagle_board_conversion_uses_the_kicad_cli_import_command(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source = temporary_path / 'source.brd'
            destination = temporary_path / 'converted.kicad_pcb'
            source.write_text('<eagle/>', encoding='utf-8')
            destination.write_text('(kicad_pcb)', encoding='utf-8')
            completed = mock.Mock(returncode=0, stdout='', stderr='')
            with mock.patch('kicad_agents.project_git_action.subprocess.run', return_value=completed) as run:
                _convert_eagle_board(source, destination, 'test-kicad-cli')
        run.assert_called_once_with(['test-kicad-cli', 'pcb', 'import', '--format', 'eagle', '--output', str(destination), str(source)], capture_output=True, text=True)

    def test_blank_kicad_cli_configuration_is_treated_as_unset(self):
        with mock.patch.dict('os.environ', {'KICAD_CLI': 'configured-kicad-cli'}):
            self.assertEqual(find_kicad_cli(''), 'configured-kicad-cli')

    def test_eagle_project_conversion_uses_the_combined_kicad_cli_import_command(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            board = temporary_path / 'source.brd'
            schematic = temporary_path / 'source.sch'
            destination_board = temporary_path / 'kicad_file.kicad_pcb'
            destination_schematic = temporary_path / 'kicad_file.kicad_sch'
            destination_project = temporary_path / 'kicad_file.kicad_pro'
            board.write_text('<eagle/>', encoding='utf-8')
            schematic.write_text('<eagle/>', encoding='utf-8')
            for destination in [destination_board, destination_schematic, destination_project]:
                destination.write_text('converted', encoding='utf-8')
            completed = mock.Mock(returncode=0, stdout='', stderr='')
            with mock.patch('kicad_agents.project_git_action.subprocess.run', return_value=completed) as run:
                _convert_eagle_project(board, schematic, destination_board, destination_schematic, destination_project, 'test-kicad-cli')
        run.assert_called_once_with(['test-kicad-cli', 'import', '--output', str(temporary_path / 'kicad_file'), str(board), str(schematic)], capture_output=True, text=True)

    def test_project_images_action_creates_part_level_artwork_and_3d_renders(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            part_directory = Path(temporary_directory) / 'part'
            source_directory = part_directory / 'data' / 'generated_data' / 'src'
            source_directory.mkdir(parents=True)
            (part_directory / 'data' / 'kicad_file.kicad_pcb').write_text('(kicad_pcb)', encoding='utf-8')
            (source_directory / 'board.png').write_bytes(b'front')
            (source_directory / 'board_bottom.png').write_bytes(b'back')

            def render(command, **_kwargs):
                Path(command[command.index('--output') + 1]).write_bytes(b'render')
                return mock.Mock(returncode=0, stdout='', stderr='')
            with mock.patch('kicad_agents.project_images_action.subprocess.run', side_effect=render) as run:
                result = render_project_images({'directory': str(part_directory), 'project_kicad_cli': 'test-kicad-cli'})
            images_directory = part_directory / 'images'
            self.assertEqual((images_directory / 'pcb_front.png').read_bytes(), b'front')
            self.assertEqual((images_directory / 'pcb_back.png').read_bytes(), b'back')
            self.assertTrue((images_directory / 'pcb_isometric.png').is_file())
            self.assertTrue((images_directory / 'pcb_3d_populated.png').is_file())
            self.assertEqual(run.call_count, 2)
            self.assertIn('315,0,45', result['commands'][0])
            self.assertIn('0.75', result['commands'][1])
            self.assertIn('--perspective', result['commands'][1])

    def test_refresh_project_files_routes_eagle_boards_through_conversion(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            repository_directory = temporary_path / 'repo'
            (repository_directory / '.git').mkdir(parents=True)
            source = repository_directory / 'Hardware' / 'ADXL345_Breakout.brd'
            source_schematic = repository_directory / 'Hardware' / 'ADXL345_Breakout.sch'
            source.parent.mkdir()
            source.write_text('<eagle/>', encoding='utf-8')
            source_schematic.write_text('<eagle/>', encoding='utf-8')
            details = {'directory': str(temporary_path / 'part'), 'project_git_url': 'https://github.com/sparkfun/ADXL345_Breakout.git', 'project_github_repository': 'ADXL345_Breakout', 'project_file_folder': 'Hardware', 'project_file_basename': 'ADXL345_Breakout', 'project_file_extensions': ['.kicad_pcb'], 'project_source_format': 'eagle', 'project_sparse_checkout': False, 'project_git_ref': 'master'}

            def convert(board_path, schematic_path, board_destination, schematic_destination, project_destination, _cli):
                for destination in [board_destination, schematic_destination, project_destination]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text('converted', encoding='utf-8')
            with mock.patch.object(project_git_action, '_repository_workspace_directory', return_value=repository_directory), mock.patch.object(project_git_action, '_git_repository_is_usable', return_value=True), mock.patch.object(project_git_action, '_run_git'), mock.patch.object(project_git_action, '_convert_eagle_project', side_effect=convert) as converter:
                copied = refresh_project_files(details)
            data_directory = temporary_path / 'part' / 'data'
            self.assertTrue((data_directory / 'source_eagle.brd').is_file())
            self.assertTrue((data_directory / 'source_eagle.sch').is_file())
            self.assertTrue((data_directory / 'kicad_file.kicad_pcb').is_file())
            self.assertTrue((data_directory / 'kicad_file.kicad_sch').is_file())
            self.assertTrue((data_directory / 'kicad_file.kicad_pro').is_file())
            self.assertTrue((data_directory / 'original' / 'source_eagle.brd').is_file())
            self.assertTrue((data_directory / 'original' / 'source_eagle.sch').is_file())
            converter.assert_called_once()
            self.assertEqual(len(copied), 5)

    def test_project_populator_keeps_only_current_version_records(self):
        options = []
        working_oomp_populate_project.main(options=options)
        current_sensor = [option for option in options if option['project_github_repository'] == 'SparkFun_Qwiic_Current_Sensor_ADE7953']
        self.assertEqual(len(current_sensor), 1)
        self.assertEqual(current_sensor[0]['project_version'], 'current')
        self.assertNotIn('v1.0.0', [option['project_version'] for option in current_sensor])

    def test_project_data_declares_one_current_version_per_board(self):
        project_data_directory = Path(__file__).resolve().parents[2] / 'project_data'
        for definition_file in project_data_directory.glob('*/working.yaml'):
            definition = yaml.safe_load(definition_file.read_text(encoding='utf-8'))
            for project in definition['projects']:
                versions_by_board = {}
                for version in project['versions']:
                    board = version.get('board', project['github_repository'])
                    versions_by_board.setdefault(board, []).append(version)
                for board, versions in versions_by_board.items():
                    self.assertEqual(len(versions), 1, f'{definition_file}: {project['github_repository']}/{board}')
                    self.assertEqual(versions[0].get('version', 'current'), 'current')

    def test_bus_pirate_explorer_is_self_contained_and_linked_to_oomp_parts(self):
        generated_data = BUS_PIRATE_PART / 'data' / 'generated_data'
        explorer_path = BUS_PIRATE_PART / 'board_explorer.html'
        review_path = generated_data / 'lcsc_review.yaml'
        self.assertTrue(explorer_path.is_file())
        self.assertFalse((generated_data / 'board_explorer.html').exists())
        self.assertIn(f'https://oomlout.github.io/oomp_electronic_project_version_5/parts/{BUS_PIRATE_PART.name}/board_explorer.html', (BUS_PIRATE_PART / 'README.md').read_text(encoding='utf-8'))
        self.assertTrue(review_path.is_file())
        explorer = explorer_path.read_text(encoding='utf-8')
        self.assertIn('<style id="oomp-board-style">', explorer)
        self.assertIn('<script id="component-data" type="application/json">', explorer)
        self.assertIn('data-reference="U103"', explorer)
        self.assertIn('class="board-view" data-side="front"', explorer)
        self.assertIn('class="board-view" data-side="back"', explorer)
        self.assertIn('class="side-button" type="button" data-side="back"', explorer)
        self.assertIn('id="zoom-out"', explorer)
        self.assertIn('id="zoom-in"', explorer)
        self.assertIn('id="zoom-reset"', explorer)
        self.assertIn("stage.addEventListener('wheel'", explorer)
        self.assertIn("stage.addEventListener('pointerdown'", explorer)
        self.assertIn("window.addEventListener('pointermove'", explorer)
        self.assertIn("window.addEventListener('pointerup'", explorer)
        self.assertIn('activePointers.size === 2', explorer)
        self.assertIn('touch-action: none', explorer)
        self.assertIn('{passive: false}', explorer)
        self.assertIn('class="oomp-id"', explorer)
        self.assertIn("link.className = 'part-link'", explorer)
        self.assertIn("box.setAttribute('class', selected ? 'selection-box' : 'hover-box')", explorer)
        self.assertIn('class="component-highlights"', explorer)
        gradient_free = explorer.split('data-theme="rainbow"')[0]
        self.assertNotIn('linear-gradient', gradient_free)
        self.assertIn('working_svg_square_pins', (generated_data / 'src' / 'components' / 'manifest.yaml').read_text(encoding='utf-8'))
        self.assertIn('https://github.com/oomlout/oomp_electronic_version_5/tree/main/parts/electronic_ic_qfn_56_7_mm_x_7_mm_microcontroller_dual_core_arm_cortex_m0_plus_raspberry_pi_rp2040', explorer)
        self.assertNotRegex(explorer, '<script[^>]+src=')
        self.assertNotRegex(explorer, '<link[^>]+stylesheet')
        bus_project = json.loads((generated_data / 'project.json').read_text(encoding='utf-8'))
        self.assertEqual(len(bus_project['mounting_hole_items']), 6)
        self.assertTrue(all((item['oomp']['status'] == 'matched' for item in bus_project['mounting_hole_items'])))
        self.assertEqual(bus_project['mounting_hole_items'][0]['reference'], 'MH1')
        self.assertTrue((PARTS_DIRECTORY / 'mechanical_mounting_hole_0_7_mm_round_unplated' / 'working.yaml').is_file())
        board_top = (generated_data / 'src' / 'board.svg').read_text(encoding='utf-8')
        board_bottom = (generated_data / 'src' / 'board_bottom.svg').read_text(encoding='utf-8')
        self.assertNotIn('data-reference="J301"', board_top)
        self.assertIn('data-reference="J301"', board_bottom)
        self.assertNotIn('data-reference="U103"', board_bottom)
        self.assertIn('mirrored horizontally', (BUS_PIRATE_PART / 'README.md').read_text(encoding='utf-8'))

    def test_j1_orientation_uses_footprint_pad_one(self):
        local_bounds = {'min_x': -1.3716, 'min_y': -1.2446, 'max_x': 14.0716, 'max_y': 1.4986}
        pads = [{'number': '1', 'local_position': {'x': 0.0, 'y': 0.0}}]
        pin_one_svg = {'x': 1.24, 'y': 1.27}
        rotation = _orientation_rotation(2.48, 15.24, local_bounds, pads, pin_one_svg)
        self.assertEqual(rotation, -90)

    def test_nearly_square_ic_orientation_is_not_forced_by_pad_extents(self):
        local_bounds = {'min_x': -2.125, 'min_y': -1.8, 'max_x': 2.125, 'max_y': 1.8}
        pads = [{'number': '1', 'local_position': {'x': -1.25, 'y': -0.95}}]
        pin_one_svg = {'x': 0.3759, 'y': 0.5657}
        rotation = _orientation_rotation(2.8, 2.9, local_bounds, pads, pin_one_svg)
        self.assertEqual(rotation, 0)

class RepositoryOrganizationTests(unittest.TestCase):

    def test_interactive_html_bom_logs_missing_python_to_run_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            part_directory = root / 'parts' / 'demo_part'
            data_directory = part_directory / 'data'
            data_directory.mkdir(parents=True)
            (data_directory / 'kicad_file.kicad_pcb').write_text('(kicad_pcb)', encoding='utf-8')
            script_directory = root / 'tools' / 'interactive_html_bom' / 'InteractiveHtmlBom'
            script_directory.mkdir(parents=True)
            (script_directory / 'generate_interactive_bom.py').write_text('# stub', encoding='utf-8')
            with mock.patch.object(interactive_html_bom_action, 'REPOSITORY_ROOT', root), mock.patch.object(interactive_html_bom_action, 'INTERACTIVE_HTML_BOM_SCRIPT', script_directory / 'generate_interactive_bom.py'), mock.patch.object(interactive_html_bom_action, '_candidate_python_executables', return_value=[]):
                result = interactive_html_bom_action.generate_interactive_html_bom({'directory': str(part_directory)})
            self.assertIsNone(result)
            log_path = root / 'report' / 'errors_during_run.txt'
            self.assertTrue(log_path.is_file())
            self.assertIn("InteractiveHtmlBom requires KiCad's bundled Python", log_path.read_text(encoding='utf-8'))
