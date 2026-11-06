"""Optional public links: a key/value list (instagram, telegram, youtube, ...).

Disposable SQLite only; PostgreSQL is not contacted.
"""
from __future__ import annotations

import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from bech32 import encode

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import btc_db

_spec = importlib.util.spec_from_file_location(
    "generator_under_test_links", PACKAGE / "btc_envelope_maker.py")
assert _spec is not None and _spec.loader is not None
generator = importlib.util.module_from_spec(_spec)
sys.modules["generator_under_test_links"] = generator
_spec.loader.exec_module(generator)

SYNTHETIC_ADDRESS = encode("bc", 0, list(range(20)))
SYNTHETIC_ADDRESS_2 = encode("bc", 0, list(range(1, 21)))

LINKS = {
    "instagram": "https://instagram.com/btc4fun",
    "telegram": "https://t.me/btc4fun",
    "youtube": "https://youtube.com/@btc4fun",
}


class PublicLinksUnit(unittest.TestCase):
    def test_links_are_normalized_to_a_sorted_key_value_map(self):
        self.assertEqual(generator.normalize_public_links(LINKS), LINKS)
        self.assertEqual(generator.normalize_public_links({}), {})
        self.assertEqual(generator.normalize_public_links(None), {})

    def test_keys_are_lowercased_and_trimmed(self):
        self.assertEqual(generator.normalize_public_links({" Instagram ": "https://instagram.com/x"}),
                         {"instagram": "https://instagram.com/x"})

    def test_bad_keys_are_rejected(self):
        for key in ("bad key", "k" * 33, "", "  ", "a/b", "کلید"):
            with self.subTest(key=key):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({key: "https://instagram.com/x"})

    def test_values_must_be_https_urls(self):
        for value in ("http://instagram.com/x", "javascript:alert(1)", "instagram.com/x",
                      "https://", "https://x" + "y" * 600):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({"instagram": value})

    def test_control_and_bidi_characters_are_rejected(self):
        for value in ("https://instagram.com/a\u202eb", "https://instagram.com/a\u0000b"):
            with self.subTest(value=ascii(value)):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({"instagram": value})

    def test_too_many_links_are_rejected(self):
        many = {f"k{i}": "https://instagram.com/x" for i in range(21)}
        with self.assertRaises(SystemExit):
            generator.normalize_public_links(many)


class PublicLinksConfig(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="public-links-config-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)

    def config(self, **values):
        path = Path(self.directory.name) / "config.toml"
        lines = []
        for k, v in values.items():
            if isinstance(v, dict):
                # A TOML table: [public_links] then one key = "value" per line.
                lines.append(f"[{k}]")
                lines.extend(f"{ik} = {json.dumps(iv, ensure_ascii=False)}" for ik, iv in v.items())
            else:
                lines.append(f"{k} = {json.dumps(v, ensure_ascii=False)}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_empty_default_is_an_empty_map(self):
        cfg = generator.load_config(self.config())
        self.assertEqual(cfg["public_links"], {})

    def test_valid_links_are_accepted(self):
        cfg = generator.load_config(self.config(public_links=LINKS))
        self.assertEqual(cfg["public_links"], LINKS)

    def test_bad_link_is_a_config_error(self):
        with self.assertRaises(SystemExit) as raised, patch("builtins.print"):
            generator.load_config(self.config(public_links={"instagram": "http://instagram.com/x"}))
        self.assertTrue(str(raised.exception.code).startswith("config: "))

    def test_shipped_example_config_keeps_links_empty(self):
        cfg = generator.load_config(PACKAGE / "config.example.toml")
        self.assertEqual(cfg["public_links"], {})


class PublicLinksDatabase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="public-links-db-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "disposable.sqlite3"
        self.url = str(self.path)

    @contextlib.contextmanager
    def database(self):
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:
            yield conn

    def stored(self, serial):
        with self.database() as conn:
            return conn.execute("SELECT public_links FROM wallets WHERE serial = ?", (serial,)).fetchone()

    def test_fresh_table_has_a_nullable_public_links_column(self):
        btc_db.check(self.url)
        with self.database() as conn:
            columns = {row[1]: row for row in conn.execute('PRAGMA table_info("wallets")')}
        self.assertIn("public_links", columns)
        self.assertEqual(columns["public_links"][3], 0)          # not null = 0
        self.assertIn(columns["public_links"][4], (None, "NULL"))

    def test_links_are_stored_as_json_and_empty_becomes_null(self):
        btc_db.check(self.url)
        btc_db.save_rows(self.url, "wallets", [
            btc_db.Row("fixture-1", SYNTHETIC_ADDRESS, public_links=LINKS),
            btc_db.Row("fixture-2", SYNTHETIC_ADDRESS_2),
        ])
        self.assertEqual(json.loads(self.stored("fixture-1")[0]), LINKS)
        self.assertIsNone(self.stored("fixture-2")[0])

    def test_plain_ledger_insert_stays_backwards_compatible(self):
        with self.database() as conn:
            conn.execute("CREATE TABLE wallets (serial TEXT PRIMARY KEY, address TEXT NOT NULL UNIQUE, "
                         "jalali_datetime TEXT, created_utc TEXT)")
        self.assertEqual(btc_db.save_rows(self.url, "wallets", [btc_db.Row("fixture-1", SYNTHETIC_ADDRESS)]),
                         (1, 0))

    def test_migration_adds_the_column_and_is_repeatable(self):
        with self.database() as conn:
            conn.execute("CREATE TABLE wallets (serial TEXT PRIMARY KEY, address TEXT NOT NULL UNIQUE, "
                         "jalali_datetime TEXT, created_utc TEXT)")
            conn.execute("INSERT INTO wallets VALUES ('fixture-1', ?, 'kept', NULL)", (SYNTHETIC_ADDRESS,))
        self.assertIsNone(btc_db.migrate_public_columns(self.url))
        self.assertIsNone(btc_db.migrate_public_columns(self.url))
        with self.database() as conn:
            columns = {row[1] for row in conn.execute('PRAGMA table_info("wallets")')}
            kept = conn.execute("SELECT jalali_datetime FROM wallets").fetchone()
        self.assertIn("public_links", columns)
        self.assertEqual(kept, ("kept",))

    def test_csv_public_links_column_is_read(self):
        ledger = Path(self.directory.name) / "ledger.csv"
        ledger.write_text(
            "serial,address,jalali_datetime,created_utc,public_links\n"
            f'fixture-1,{SYNTHETIC_ADDRESS},,,"{json.dumps(LINKS).replace(chr(34), chr(34) * 2)}"\n',
            encoding="utf-8")
        rows = btc_db.read_ledger(ledger)
        # read_ledger keeps the normalized JSON text; compare the decoded map.
        self.assertEqual(json.loads(rows[0].public_links), LINKS)

    def test_export_writes_links_as_key_value_pairs(self):
        btc_db.check(self.url)
        btc_db.save_rows(self.url, "wallets", [btc_db.Row("fixture-1", SYNTHETIC_ADDRESS, public_links=LINKS)])
        out = Path(self.directory.name) / "export.csv"
        self.assertEqual(btc_db.export_rows(self.url, "wallets", out), 1)
        text = out.read_text(encoding="utf-8-sig")
        self.assertIn("public_links", text.splitlines()[0])
        self.assertIn("instagram=https://instagram.com/btc4fun", text)
        self.assertIn("telegram=https://t.me/btc4fun", text)


if __name__ == "__main__":
    unittest.main()
