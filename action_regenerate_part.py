"""Rebuild a selected project with the independent project runner."""
from action_regenerate_all import _normal_gate_is_complete

def _check_files_complete(part_directory, mode_details):
    if mode_details.get('always_run_on_regeneration',False): return False
    return _normal_gate_is_complete(part_directory,mode_details)

if __name__=='__main__':
    from action_generate import main
    main()
