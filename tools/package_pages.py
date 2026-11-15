"""Package only the self-contained browser pages, without CAD/build caches."""
from pathlib import Path
import sys
import shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from project_config import ROOT

def package(destination):
    destination=Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Use a new output directory: '+str(destination))
    files=[ROOT/'index.html',ROOT/'.nojekyll',ROOT/'usage/index.html',ROOT/'usage/index.json']
    explorers=sorted((ROOT/'parts').glob('oomp_project_*/board_explorer.html'))
    iboms=sorted((ROOT/'parts').glob('oomp_project_*/data/interactivehtmlbom/ibom.html'))
    files+=explorers+iboms
    total=sum(path.stat().st_size for path in files)
    if total>950_000_000:
        raise RuntimeError('Browser pages exceed the 950 MB publication budget; review hosting before adding more pages')
    for source in files:
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
            raise ValueError('Unexpected linked file: '+str(source))
        target=destination/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    print(f'Packaged {len(explorers)} explorers and {len(iboms)} interactive BOMs; {total:,} bytes')

if __name__=='__main__':
    package(ROOT/'build/pages')
