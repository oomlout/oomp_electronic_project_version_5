import unittest
import working_oomp_populate_project

class PreservedProjectPaths(unittest.TestCase):
    def test_saved_soldered_board_paths(self):
        options=[]
        working_oomp_populate_project.main(options=options)
        simple_light = next((option for option in options if option['project_github_repository'] == 'Simple-light-sensor-board-hardware-design'))
        self.assertEqual(simple_light['project_file_folder'], 'CAD/V1.1.1')
        self.assertEqual(simple_light['project_file_basename'], 'Simple_sensor')
        simple_light_easyc = next((option for option in options if option['project_github_repository'] == 'Simple-light-sensor-board-with-easyC-hardware-design'))
        self.assertEqual(simple_light_easyc['project_file_folder'], 'CAD/V1.1.2')
        self.assertEqual(simple_light_easyc['project_file_basename'], 'Simple_sensor_easyC')
        simple_light_qwiic = next((option for option in options if option['project_github_repository'] == 'Simple-light-sensor-board-qwiic-hardware-design'))
        self.assertEqual(simple_light_qwiic['project_file_folder'], 'CAD/V1.1.2')
        self.assertEqual(simple_light_qwiic['project_file_basename'], 'Simple_sensor_easyC')
        simple_fire = next((option for option in options if option['project_github_repository'] == 'Simple-fire-sensor-board-hardware-design'))
        self.assertEqual(simple_fire['project_file_folder'], 'CAD/V1.1.1')
        self.assertEqual(simple_fire['project_file_basename'], 'Simple_sensor')
        simple_fire_easyc = next((option for option in options if option['project_github_repository'] == 'Simple-fire-sensor-board-with-easyC-hardware-design'))
        self.assertEqual(simple_fire_easyc['project_file_folder'], 'CAD/V1.1.2')
        self.assertEqual(simple_fire_easyc['project_file_basename'], 'Simple_sensor_easyC')
        hx711 = next((option for option in options if option['project_github_repository'] == 'Load-cell-ampfilier-HX711-board-hardware-design'))
        self.assertEqual(hx711['project_file_folder'], 'CAD/V1.1.1')
        self.assertEqual(hx711['project_file_basename'], 'HX711')
        hx711_easyc = next((option for option in options if option['project_github_repository'] == 'Load-cell-ampfilier-HX711-board-with-easy-C-hardware-design'))
        self.assertEqual(hx711_easyc['project_file_folder'], 'CAD/V1.1.1')
        self.assertEqual(hx711_easyc['project_file_basename'], 'HX711_breakout_easyC')

