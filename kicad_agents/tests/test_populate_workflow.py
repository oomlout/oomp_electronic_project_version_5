import unittest
from kicad_agents.kicad_processing_agent import _footprint_record, _symbol_record, _add_connectivity_cross_checks
from kicad_agents.sexpr import loads
from pathlib import Path
'The documented source-only workflow keeps defaults and overrides editable.'

class PopulateWorkflowTests(unittest.TestCase):

    def test_module_with_mounting_holes_does_not_classify_signal_pins_as_holes(self):
        root = loads('(footprint "Module:Arduino_UNO_R3_WithMountingHoles"\n          (property "Reference" "A1") (layer "F.Cu") (at 10 20)\n          (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu"))\n          (pad "1" thru_hole circle (at 2 0) (size 2 2) (drill 1) (layers "*.Cu") (net "GND")))')
        directory = Path.cwd()
        record = _footprint_record(root, directory / 'board.kicad_pcb', directory)
        self.assertFalse(record['is_mounting_hole'])
        self.assertEqual(len(record['mounting_holes']), 1)
        self.assertEqual(record['mounting_holes'][0]['role'], 'mounting')
        self.assertFalse(record['pads'][1]['is_mounting_hole'])

    def test_schematic_y_up_library_becomes_y_down_sheet(self):
        library = loads('(symbol "Device:C" (symbol "C_1_1"\n          (pin passive line (at 0 3.81 270) (length 2) (name "") (number "1"))\n          (pin passive line (at 0 -3.81 90) (length 2) (name "") (number "2"))))')
        directory = Path.cwd()
        for angle, expected in [[0, (10, 16.19)], [90, (6.19, 20)], [180, (10, 23.81)], [270, (13.81, 20)]]:
            symbol = loads(f'(symbol (lib_id "Device:C") (property "Reference" "C1") (at 10 20 {angle}) (unit 1))')
            record = _symbol_record(symbol, {'Device:C': library}, directory / 'root.kicad_sch', directory)
            pin = record['pins'][0]['position']
            self.assertAlmostEqual(pin['x'], expected[0])
            self.assertAlmostEqual(pin['y'], expected[1])

    def test_root_local_net_prefix_does_not_flatten_child_sheet_names(self):
        components = [{'schematic': {'units': [{'source_file': source, 'pins': [{'number': '1', 'net': 'DATA'}]}]}, 'pcb': {'pads': [{'number': '1', 'net': net}]}} for source, net in [('root.kicad_sch', '/DATA'), ('child.kicad_sch', '/other/DATA')]]
        _add_connectivity_cross_checks(components, root_schematic='root.kicad_sch')
        self.assertEqual(components[0]['connectivity_cross_check']['agree_count'], 1)
        self.assertEqual(components[1]['connectivity_cross_check']['disagree_count'], 1)
if __name__ == '__main__':
    unittest.main()
