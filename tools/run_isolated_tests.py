"""Run with `python -S tools/run_isolated_tests.py ...pytest arguments...`.

Bypass site .pth injections and reject filesystem access to the electronics
checkout. This catches hidden imports/reads even when both repositories exist.
"""
import os
from pathlib import Path
import sys
import sysconfig

root=Path(__file__).resolve().parents[1]
workspace=root.parent.resolve()
def external_checkout(path):
    return path.is_relative_to(workspace) and not path.is_relative_to(root)
sys.path[:]=[entry for entry in sys.path if not external_checkout(Path(entry or os.getcwd()).resolve())]
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
sys.path.insert(0,sysconfig.get_path('purelib'))
sys.path.insert(0,str(root))
def audit(event,args):
    if event in ('open','os.listdir','os.scandir') and args:
        name=args[0]
        if isinstance(name,(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(name)).resolve()
            if external_checkout(path):
                raise RuntimeError('Cross-repository access forbidden: '+str(path))
sys.addaudithook(audit)
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
