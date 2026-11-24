"""Install the prototype in a mod; optionally apply the reviewed state migration."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

FILES = ['painter.py', 'model.py', 'source_io.py', 'demographics.py', 'migrate_state_setup.py',
         'run_painter.bat', 'requirements.txt', '.gitignore', 'README.md', 'MODLOG.md', 'PLAN.md', 'test_painter.py']


def confined(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Migration path escaped its root')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(mod, migration=False, package=None):
    package = Path(package or Path(__file__).parent).resolve()
    root = Path(mod).resolve()
    destination = root / 'legacy_of_kattail_painter'
    if not (root / 'descriptor.mod').is_file():
        raise ValueError('Choose the mod root containing descriptor.mod')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('Painter folder is not empty; preserve or rename it before installing')
    for name in FILES:
        if not (package / name).is_file():
            raise ValueError('Missing package file: ' + name)
    entries = []
    stage = package / 'migration_patch/files'
    if migration:
        manifest = json.loads((package / 'migration_patch/manifest.json').read_text(encoding='utf-8'))
        entries = manifest['files']
        # Check every original/staged byte before creating the destination.
        for entry in entries:
            path, staged = confined(root, entry['path']), confined(stage, entry['path'])
            if sha(path) != entry['before_sha256'] or sha(staged) != entry['after_sha256']:
                raise ValueError('Source/stage changed; regenerate before installing: ' + entry['path'])
    destination.mkdir(exist_ok=True)
    for name in FILES:
        shutil.copy2(package / name, destination / name)
    if entries:
        backup = destination / ('migration_originals_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        for entry in entries:
            path = confined(backup, entry['path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(confined(root, entry['path']), path)
        try:
            for entry in entries:
                shutil.copy2(confined(stage, entry['path']), confined(root, entry['path']))
        except Exception:
            for entry in entries:
                shutil.copy2(confined(backup, entry['path']), confined(root, entry['path']))
            raise
        shutil.copy2(package / 'migration_patch/manifest.json', destination / 'migration_manifest.json')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, type=Path)
    parser.add_argument('--include-migration', action='store_true')
    args = parser.parse_args()
    print('Installed:', install(args.mod, args.include_migration))
    print('Run run_painter.bat. Use Save to write edited source files with backups.')
