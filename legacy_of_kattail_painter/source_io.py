"""Guarded text writes with byte-for-byte backups and rollback on failure."""
from __future__ import annotations

from datetime import datetime
import os
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
    """Apply {relative: (expected original bytes, new bytes)} after full preflight."""
    root = Path(root).resolve()
    paths = {relative: confined(root, relative) for relative in changes}
    if len(set(paths.values())) != len(paths):
        raise ValueError('Duplicate destination in save')
    for relative, (original, _) in changes.items():
        if paths[relative].read_bytes() != original:
            raise ValueError('File changed outside the painter; reload before saving: ' + relative)
    if not changes:
        return None
    backup = root / 'legacy_of_kattail_painter' / 'backups' / (
        label + '_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for relative, (original, _) in changes.items():
        target = confined(backup, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original)
    written = []
    try:
        for relative, (original, updated) in changes.items():
            if paths[relative].read_bytes() != original:
                raise ValueError('File changed during save: ' + relative)
            atomic_bytes(paths[relative], updated)
            written.append(relative)
    except Exception:
        for relative in reversed(written):
            atomic_bytes(paths[relative], changes[relative][0])
        raise
    return backup
