from tools import package_pages

def test_publication_copies_saved_explorers_and_boms_without_changing_inputs(tmp_path,monkeypatch):
    source=tmp_path/'source'; source.mkdir()
    files={
        'index.html':b'<h1>Saved index</h1>',
        '.nojekyll':b'',
        'usage/index.html':b'<h1>Saved usage</h1>',
        'usage/index.json':b'{}',
        'parts/oomp_project_demo/board_explorer.html':b'<h1>Saved explorer</h1>',
        'parts/oomp_project_demo/data/interactivehtmlbom/ibom.html':b'<h1>Saved BOM</h1>',
    }
    for name,data in files.items():
        path=source/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    cad=source/'parts/oomp_project_demo/data/kicad_file.kicad_pcb'
    cad.write_bytes(b'preserved CAD')
    monkeypatch.setattr(package_pages,'ROOT',source)
    output=tmp_path/'published'
    package_pages.package(output)
    assert {path.relative_to(output).as_posix() for path in output.rglob('*') if path.is_file()}==set(files)
    for name,data in files.items():
        assert (source/name).read_bytes()==data
        assert (output/name).read_bytes()==data
    assert cad.read_bytes()==b'preserved CAD'
