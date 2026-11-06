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

    def test_slug_labels_are_lowercased_and_trimmed(self):
        self.assertEqual(generator.normalize_public_links({" Instagram ": "https://instagram.com/x"}),
                         {"instagram": "https://instagram.com/x"})

    def test_human_labels_are_kept_as_written(self):
        # The owner writes contact labels in Persian; they are shown verbatim.
        for label in ("اینستاگرام", "تلگرام", "ایمیل", "سایت", "Instagram Profile"):
            with self.subTest(label=label):
                self.assertEqual(
                    generator.normalize_public_links({label: "https://instagram.com/x"}),
                    {label: "https://instagram.com/x"})

    def test_bad_labels_are_rejected(self):
        for key in ("k" * 33, "", "  ", "بد\u202eسط", "a\u0000b"):
            with self.subTest(key=key):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({key: "https://instagram.com/x"})

    def test_mailto_and_tel_contact_routes_are_accepted(self):
        routes = {"ایمیل": "mailto:09113458375@btc4.fun", "تلفن": "tel:+989113458375"}
        self.assertEqual(generator.normalize_public_links(routes), routes)

    def test_bare_email_and_phone_become_contact_routes(self):
        # A seller writes contact details as plain text; they must work as-is.
        got = generator.normalize_public_links({"ایمیل": "09113458375@btc.fun",
                                                "موبایل": "0911 345 8375",
                                                "تلفن": "+98 (911) 345-8375"})
        self.assertEqual(got, {"ایمیل": "mailto:09113458375@btc.fun",
                               "موبایل": "tel:09113458375",
                               "تلفن": "tel:+989113458375"})

    def test_any_https_host_is_allowed_for_a_link(self):
        # A seller's own profiles live on other hosts; only the shape is checked.
        links = {"instagram": "https://instagram.com/b.tc4fun.ir",
                 "telegram": "https://b_tc4fun_ir.t.me",
                 "youtube": "https://youtube.com/@btc4fun"}
        self.assertEqual(generator.normalize_public_links(links), links)

    def test_unsafe_link_schemes_and_shapes_are_still_rejected(self):
        for value in ("http://instagram.com/x", "javascript:alert(1)", "data:text/html,x",
                      "https://user:pw@instagram.com/x", "https://instagram.com:8443/x",
                      "https://instagram.com/a b", "tel:12", "mailto:not-an-email"):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({"x": value})

    def test_mailto_still_requires_a_clean_target(self):
        for value in ("mailto:", "mailto: ", "mailto:a b@x.ir", "mailto:a\u202eb@x.ir"):
            with self.subTest(value=ascii(value)):
                with self.assertRaises(SystemExit):
                    generator.normalize_public_links({"ایمیل": value})

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
        # Values are percent-escaped so `;` and `=` inside them cannot break the flat form.
        self.assertIn("instagram=https%3A%2F%2Finstagram.com%2Fbtc4fun", text)
        self.assertIn("telegram=https%3A%2F%2Ft.me%2Fbtc4fun", text)

    def test_csv_links_round_trip_through_the_flat_form(self):
        # A mailto value contains both `@` and `=`-free separators; the round trip must keep it exact.
        links = {"ایمیل": "mailto:09113458375@btc4.fun", "سایت": "https://btc.saeb.id.ir"}
        flat = btc_db._links_text(json.dumps(links, ensure_ascii=False))
        self.assertNotIn(" ", flat)
        self.assertEqual(btc_db._links_from_text(flat), links)


if __name__ == "__main__":
    unittest.main()
