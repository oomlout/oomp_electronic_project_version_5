"""Full local rebuild; fetching upstream sources remains explicitly opt-in."""
from pathlib import Path
import sys
import yaml

def _normal_gate_is_complete(part_directory, mode_details):
    """Read legacy output gates without treating failed status files as success."""
    value=mode_details.get('file_test','')
    if value in (None,''): return False
    tests=value if isinstance(value,(list,tuple)) else [value]
    results=[]
    for name in tests:
        path=Path(str(name))
        if not path.is_absolute(): path=part_directory/path
        success=path.exists()
        if success and path.suffix.lower() in ('.yaml','.yml'):
            try:
                status=yaml.safe_load(path.read_text(encoding='utf-8')) or {}
                if isinstance(status,dict):
                    success=str(status.get('status','')).lower() not in ('failed','error','skipped','incomplete')
            except (OSError,UnicodeError,yaml.YAMLError): success=False
        results.append(success)
    return all(results) if mode_details.get('file_test_mode','exists')=='exists' else any(results)

if __name__=='__main__':
    from action_generate import main
    sys.argv.extend(['--regenerate-pngs','--production','--images','--ibom'])
    main()
