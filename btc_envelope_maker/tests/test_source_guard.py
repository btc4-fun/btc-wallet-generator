"""Guard must inspect all publishable bytes, not merely an empty staged diff."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def guard():
    source = ROOT / 'scripts/check_publication.py'
    assert source.exists(), 'Standalone source publication guard is missing'
    spec = importlib.util.spec_from_file_location('generator_source_guard', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expected_public_source_is_accepted():
    assert guard().violations('btc_envelope_maker/config.example.toml', b'db_url = ""', {'btc_envelope_maker/config.example.toml'}) == []


def test_even_allowlisted_private_paths_and_credentials_are_rejected():
    module = guard()
    for path in ('config.toml', '.env', 'x.pdf', 'wallet.sqlite3', 'wallet.db-wal', 'privatekey.png', 'out/public.txt', 'secrets/token', 'ledger.csv'):
        assert module.violations(path, b'synthetic', {path})
    for payload in (b'postgresql://' + b'operator:synthetic-secret@invalid.example/db', b'-----BEGIN ' + b'PRIVATE KEY-----'):
        assert module.violations('README.md', payload, {'README.md'})


def test_unreviewed_files_are_rejected():
    assert guard().violations('unexpected.txt', b'public', {'README.md'})
