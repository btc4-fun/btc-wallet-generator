"""Optional public metadata: migration, NULL semantics, CSV columns, config validation.

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

import pytest
from bech32 import encode

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import btc_db

# The module and its package share a name, so load the script by path like
# the other generator tests do.
_spec = importlib.util.spec_from_file_location(
    "generator_under_test", PACKAGE / "btc_envelope_maker.py")
assert _spec is not None and _spec.loader is not None
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)

SYNTHETIC_ADDRESS = encode("bc", 0, list(range(20)))
SYNTHETIC_ADDRESS_2 = encode("bc", 0, list(range(1, 21)))
OPTIONAL = ("public_notes", "site_key", "site_url", "image_url")
PRIVATE = ("contact_type", "contact_value", "notes")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="public-metadata-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "disposable.sqlite3"
        self.url = str(self.path)

    @contextlib.contextmanager
    def database(self):
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:
            yield conn

    def columns(self):
        with self.database() as conn:
            return [row[1] for row in conn.execute('PRAGMA table_info("wallets")')]

    def create_old_table(self):
        with self.database() as conn:
            conn.execute("CREATE TABLE wallets (serial TEXT PRIMARY KEY, address TEXT NOT NULL UNIQUE, "
                         "jalali_datetime TEXT, created_utc TEXT)")
            conn.execute("INSERT INTO wallets VALUES ('fixture-1', ?, 'kept text', NULL)", (SYNTHETIC_ADDRESS,))

    def test_migration_adds_only_the_four_public_columns_and_is_idempotent(self):
        self.create_old_table()
        self.assertNotIn("public_notes", self.columns())
        btc_db.migrate_public_columns(self.url)
        after_first = self.columns()
        self.assertEqual(after_first,
                         ["serial", "address", "jalali_datetime", "created_utc", *OPTIONAL])
        # Private columns are not created by this migration.
        self.assertFalse(set(PRIVATE) & set(after_first))
        btc_db.migrate_public_columns(self.url)              # idempotent no-op
        self.assertEqual(self.columns(), after_first)
        with self.database() as conn:
            self.assertEqual(conn.execute("SELECT serial, jalali_datetime FROM wallets").fetchall(),
                             [("fixture-1", "kept text")])

    def test_migration_refuses_missing_table(self):
        with self.assertRaises(btc_db.DbError):
            btc_db.migrate_public_columns(self.url)
        self.assertEqual(self.columns(), [])

    def test_migration_leaves_existing_private_columns_untouched(self):
        self.create_old_table()
        btc_db.migrate_contact_columns(self.url)
        with self.database() as conn:
            conn.execute("UPDATE wallets SET contact_type='phone', contact_value='x', notes='private'")
        btc_db.migrate_public_columns(self.url)
        self.assertTrue(set(PRIVATE).issubset(self.columns()))
        with self.database() as conn:
            self.assertEqual(conn.execute("SELECT contact_type, contact_value, notes FROM wallets").fetchone(),
                             ("phone", "x", "private"))

    def test_cli_migrate_public_exists_and_runs(self):
        self.create_old_table()
        self.assertEqual(btc_db.main(["migrate-public", "--db", self.url]), 0)
        self.assertTrue(set(OPTIONAL).issubset(self.columns()))


class NullSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="public-null-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "disposable.sqlite3"
        self.url = str(self.path)

    @contextlib.contextmanager
    def database(self):
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:
            yield conn

    def stored(self, serial):
        with self.database() as conn:
            return conn.execute(
                f"SELECT {', '.join(OPTIONAL)} FROM wallets WHERE serial = ?", (serial,)).fetchone()

    def test_empty_strings_are_written_as_null_not_empty(self):
        btc_db.check(self.url)
        btc_db.save_rows(self.url, "wallets", [
            btc_db.Row("fixture-1", SYNTHETIC_ADDRESS, "", "", "", "   ", "", ""),
            btc_db.Row("fixture-2", SYNTHETIC_ADDRESS_2, public_notes="note", site_key="btc4.fun",
                       site_url="https://btc4.fun/", image_url="https://btc4.fun/x.png"),
        ])
        self.assertEqual(self.stored("fixture-1"), (None, None, None, None))
        self.assertEqual(self.stored("fixture-2"),
                         ("note", "btc4.fun", "https://btc4.fun/", "https://btc4.fun/x.png"))

    def test_plain_ledger_insert_stays_backwards_compatible(self):
        # No public values -> the historical 4-column INSERT, so a pre-migration
        # existing table still accepts plain ledger rows (save_rows never migrates).
        with self.database() as conn:
            conn.execute("CREATE TABLE wallets (serial TEXT PRIMARY KEY, address TEXT NOT NULL UNIQUE, "
                         "jalali_datetime TEXT, created_utc TEXT)")
        self.assertEqual(btc_db.save_rows(self.url, "wallets", [btc_db.Row("fixture-1", SYNTHETIC_ADDRESS)]),
                         (1, 0))
        btc_db.migrate_public_columns(self.url)
        self.assertEqual(self.stored("fixture-1"), (None, None, None, None))

    def test_csv_optional_columns_are_read_and_private_columns_are_ignored(self):
        ledger = Path(self.directory.name) / "ledger.csv"
        ledger.write_text(
            "serial,address,jalali_datetime,created_utc,contact_type,contact_value,notes,"
            "public_notes,site_key,site_url,image_url\n"
            f"fixture-1,{SYNTHETIC_ADDRESS},,,phone,PRIVATE,PRIVATE,public note,btc4.fun,"
            "https://btc4.fun/,https://btc4.fun/x.png\n"
            f"fixture-2,{SYNTHETIC_ADDRESS_2},,,,,,,,,,\n", encoding="utf-8")
        rows = btc_db.read_ledger(ledger)
        self.assertEqual(rows[0].public_notes, "public note")
        self.assertEqual(rows[0].site_key, "btc4.fun")
        self.assertEqual(rows[0].site_url, "https://btc4.fun/")
        self.assertEqual(rows[0].image_url, "https://btc4.fun/x.png")
        self.assertEqual(rows[1].public_notes, None)
        self.assertNotIn("PRIVATE", repr(rows))
        # List never selects or prints the optional columns either.
        btc_db.save_rows(self.url, "wallets", rows, skip_existing=True)
        self.assertTrue(all(len(row) == 4 for row in btc_db.list_rows(self.url)))


class ConfigValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="public-config-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)

    def config(self, **values):
        path = Path(self.directory.name) / "config.toml"
        # json.dumps gives a basic TOML string (double quotes, real escapes).
        body = "".join(f"{k} = {json.dumps(v, ensure_ascii=False)}\n" for k, v in values.items())
        path.write_text(body, encoding="utf-8")
        return path

    def assert_rejected(self, **values):
        with self.assertRaises(SystemExit) as raised, patch("builtins.print"):
            generator.load_config(self.config(**values))
        self.assertTrue(raised.exception.code and str(raised.exception.code).startswith("config: "))

    def test_empty_defaults_are_accepted(self):
        cfg = generator.load_config(self.config())
        for name in OPTIONAL:
            self.assertEqual(cfg[name], "")

    def test_valid_values_are_accepted(self):
        cfg = generator.load_config(self.config(
            public_notes="یادداشت\nبا خط دوم", site_key="b.tc4fun.ir",
            site_url="https://b.tc4fun.ir/p", image_url="https://btc4.fun/static/logo.png"))
        self.assertEqual(cfg["public_notes"], "یادداشت\nبا خط دوم")
        self.assertEqual(cfg["site_url"], "https://b.tc4fun.ir/p")

    def test_http_url_is_rejected(self):
        self.assert_rejected(site_key="btc4.fun", site_url="http://btc4.fun/")

    def test_wrong_host_is_rejected_for_site_and_image(self):
        self.assert_rejected(site_key="x", site_url="https://evil.invalid/")
        self.assert_rejected(image_url="https://evil.invalid/x.png")

    def test_port_userinfo_and_query_are_rejected(self):
        for url in ("https://btc4.fun:8443/", "https://user@btc4.fun/", "https://btc4.fun/?a=1"):
            with self.subTest(url=url):
                self.assert_rejected(image_url=url)

    def test_overlong_values_are_rejected(self):
        self.assert_rejected(public_notes="x" * 501)
        self.assert_rejected(site_key="k" * 65)
        self.assert_rejected(image_url="https://btc4.fun/" + "x" * 600)

    def test_control_and_bidi_characters_are_rejected_in_notes(self):
        for text in ("a\u0000b", "a\u202eb", "a\ufeffb"):
            with self.subTest(text=ascii(text)):
                self.assert_rejected(public_notes=text)

    def test_site_key_and_url_must_appear_together(self):
        self.assert_rejected(site_key="btc4.fun")
        self.assert_rejected(site_url="https://btc4.fun/")

    def test_bad_site_key_is_rejected(self):
        self.assert_rejected(site_key="bad key!", site_url="https://btc4.fun/")

    def test_owner_configured_extra_host_is_allowed(self):
        cfg = generator.load_config(self.config(
            site_key="shop", site_url="https://shop.example.invalid/",
            public_url_hosts="shop.example.invalid"))
        self.assertEqual(cfg["site_url"], "https://shop.example.invalid/")

    def test_site_url_must_match_its_key(self):
        # site_key is the site's name and site_url its address: the address must
        # belong to the named site, so a mismatched pair is a config error.
        self.assert_rejected(site_key="btc4.fun", site_url="https://b.tc4fun.ir/")
        self.assert_rejected(site_key="shop", site_url="https://btc4.fun/")
        cfg = generator.load_config(self.config(
            site_key="b.tc4fun.ir", site_url="https://b.tc4fun.ir/path"))
        self.assertEqual(cfg["site_key"], "b.tc4fun.ir")
        self.assertEqual(cfg["site_url"], "https://b.tc4fun.ir/path")

    def test_site_key_may_be_a_short_name_for_its_host(self):
        # A short label is allowed as long as the address host starts with it.
        cfg = generator.load_config(self.config(
            site_key="btc4", site_url="https://btc4.fun/"))
        self.assertEqual(cfg["site_key"], "btc4")

    def test_shipped_example_config_keeps_public_metadata_empty(self):
        # The example is committed and public: it must never carry a real
        # note, site or image, and it must still load without errors.
        example = PACKAGE / "config.example.toml"
        cfg = generator.load_config(example)
        for name in OPTIONAL:
            with self.subTest(name=name):
                self.assertEqual(cfg[name], "")
        self.assertEqual(cfg["public_url_hosts"], "")


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
