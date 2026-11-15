from kicad_agents.project_summary_agent import _orientation_rotation

def test_usb_a_pad_one_orientation():
    local_bounds = {'min_x': -7.15, 'min_y': -4.575, 'max_x': 7.15, 'max_y': 6.025}
    pads = [{'number': 'VBUS', 'local_position': {'x': 3.5, 'y': 5.3}}]
    assert _orientation_rotation(14.3, 10.6, local_bounds, pads,
                                 {'x': 2.696, 'y': 2.12, 'identifiers': ['VBUS', '1']}) == 180
