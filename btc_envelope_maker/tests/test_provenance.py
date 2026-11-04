"""Verify retained snapshot attribution and pinned runtime source locally."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_every_original_generator_path_has_valid_provenance_and_final_hash():
    manifest = json.loads((ROOT / 'docs/source-provenance.json').read_text())
    entries = manifest['files']
    generator = [item for item in entries if item['source_path'].startswith('btc_envelope_maker/')]
    assert len(generator) == manifest['original_generator_file_count'] == 26
    assert len({item['source_path'] for item in entries}) == len(entries)
    for item in entries:
        assert re.fullmatch('[0-9a-f]{64}', item['source_sha256'])
        assert re.fullmatch('[0-9a-f]{40}', item['source_git_blob'])
        actual = hashlib.sha256((ROOT / item['destination_path']).read_bytes()).hexdigest()
        assert actual == item['destination_sha256'], item['destination_path']
        if item['adaptation'] == 'unchanged':
            assert actual == item['source_sha256']
    # Domain branding changes the generator defaults, not the validator or DB layer.
    for name in ('address_validation.py', 'btc_db.py'):
        entry = next(item for item in generator if item['source_path'] == 'btc_envelope_maker/' + name)
        assert entry['adaptation'] == 'unchanged'
    entry = next(item for item in generator if item['source_path'] == 'btc_envelope_maker/btc_envelope_maker.py')
    assert 'b.tc4fun.ir' in entry['adaptation']
    assert entry['source_git_blob'] == '8bdfb78ad4655c1f8bfcdf98e28510a9c3d6b863'
    assert entry['source_sha256'] == 'ba28920c681daf903730c294ac510dde5deb111c7262a8534fe6bfde46bbb37e'
