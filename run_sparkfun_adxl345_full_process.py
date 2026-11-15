"""Explicitly refresh and rebuild the existing SparkFun project selection."""
import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    root=Path(__file__).resolve().parent
    raise SystemExit(subprocess.call([
        sys.executable, str(root/'action_generate.py'), '--filter',
        'oomp_project_github_sparkfun_spark_fun_triple_axis_acclerometer_lis3_',
        '--refresh-sources', '--production', '--images', '--ibom'], cwd=root))
