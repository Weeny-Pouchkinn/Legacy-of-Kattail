"""Guarded text writes with byte-for-byte backups and rollback on failure."""
from __future__ import annotations

from datetime import datetime
import os
import json
import hashlib
from pathlib import Path
import tempfile


def confined(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Source path escapes mod root: ' + str(relative))
    return path


def encode_source(text, original):
    encoding = 'utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8'
    try:
        original.decode(encoding)
    except UnicodeDecodeError:
        encoding = 'cp1252'
    newline = '\r\n' if b'\r\n' in original else '\n'
    return text.replace('\r\n', '\n').replace('\n', newline).encode(encoding)


def atomic_bytes(path, data):
    handle, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_changes(root, changes, label='save'):
    """Apply guarded writes/creates/deletes; None denotes an absent file."""
    root = Path(root).resolve()
    paths = {relative: confined(root, relative) for relative in changes}
    if len(set(paths.values())) != len(paths):
        raise ValueError('Duplicate destination in save')
    for relative, (original, _) in changes.items():
        actual = paths[relative].read_bytes() if paths[relative].is_file() else None
        if actual != original:
            raise ValueError('File changed outside the painter; reload before saving: ' + relative)
    if not changes:
        return None
    backup = root / 'legacy_of_kattail_painter' / 'backups' / (
        label + '_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for relative, (original, _) in changes.items():
        if original is not None:
            target = confined(backup, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
    backup.mkdir(parents=True, exist_ok=True)
    manifest = {relative: {'before': hashlib.sha256(old).hexdigest() if old is not None else None,
                           'after': hashlib.sha256(new).hexdigest() if new is not None else None}
                for relative, (old, new) in changes.items()}
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (backup / 'created_files.txt').write_text(''.join(p + '\n' for p, (old, _) in changes.items() if old is None), encoding='utf-8')
    written = []
    try:
        for relative, (original, updated) in changes.items():
            actual = paths[relative].read_bytes() if paths[relative].is_file() else None
            if actual != original:
                raise ValueError('File changed during save: ' + relative)
            if updated is None:
                paths[relative].unlink()
            else:
                paths[relative].parent.mkdir(parents=True, exist_ok=True)
                atomic_bytes(paths[relative], updated)
            written.append(relative)
    except Exception:
        for relative in reversed(written):
            original = changes[relative][0]
            if original is None:
                paths[relative].unlink(missing_ok=True)
            else:
                atomic_bytes(paths[relative], original)
        raise
    return backup
