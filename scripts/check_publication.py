"""Explicit source allowlist; scan working source or the complete Git index.

Never prints matched secret bytes. This is not a secret/image safety audit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {'.venv', 'venv', 'out', 'secrets', '__pycache__', 'backups', 'data', 'state', 'wheelhouse'}
FORBIDDEN_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.pdf', '.pem', '.key', '.kdbx', '.csv', '.p12', '.pfx'}


def violations(name, data, allowed):
    path = Path(name)
    errors = []
    if name not in allowed:
        errors.append('not in reviewed source allowlist')
    if (set(path.parts) & FORBIDDEN_PARTS or path.suffix.lower() in FORBIDDEN_SUFFIXES
            or re.search(r'\.(?:db|sqlite|sqlite3)-(?:wal|shm|journal)$', path.name, re.I)
            or path.name.lower() in {'config.toml', 'todo', 'todo.txt', 'privatekey.png', 'publickey.png'}
            or path.name.startswith('.env')):
        errors.append('forbidden publication path')
    if re.search(rb'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----', data):
        errors.append('private-key material')
    for match in re.finditer(rb'postgres(?:ql)?://([^:@\s\x22\x27]+):([^*@\s\x22\x27]+)@', data, re.I):
        if not (match.group(1) == b'user' and match.group(2) in {b'password', b'pass'}):
            errors.append('credential-bearing database URI')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', action='store_true', help='Scan every indexed file, not just staged changes')
    args = parser.parse_args()
    allowed = set(json.loads((ROOT / 'scripts/publication-allowlist.json').read_text()))
    if args.index:
        names = set(filter(None, subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')))
    else:
        # Git metadata alone is excluded. Runtime/output trees are errors, never silently skipped.
        names = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(ROOT).parts}
    failures = []
    for missing in sorted(allowed - names):
        failures.append((missing, 'required public source missing'))
    for name in sorted(names):
        path = ROOT / name
        if not args.index and path.is_symlink():
            failures.append((name, 'source symlink forbidden'))
            continue
        data = (subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
                if args.index else path.read_bytes())
        failures.extend((name, reason) for reason in violations(name, data, allowed))
    for name, reason in failures:
        print(f'BLOCKED {name}: {reason}')
    print(f'Publication source guard: {len(names)} files; {len(failures)} violations')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
