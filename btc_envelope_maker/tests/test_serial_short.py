"""Short serial format: Y(1,base36) + M(1) + D(1) + H(1) + X(1,base36) + index.

The variable char X is an incrementing counter derived from existing batch_*
folders for the same hour prefix (no DB, no persistent state). Old 9-char
stems remain accepted by the site/app shape regex; this file only pins the
new generator output.
"""
import datetime as dt
import importlib.util
from pathlib import Path
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'btc_envelope_maker.py'
spec = importlib.util.spec_from_file_location('generator_short_serial', SOURCE)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def test_short_stem_is_five_chars():
    # 2026-11-06 14:37:52 -> Jalali 1405/08/15 14:37:52 (year 05 -> base36 '5')
    now = dt.datetime(2026, 11, 6, 14, 37, 52)
    stem, human = gen.serial_stem_short(now, counter=0)
    assert len(stem) == 5, stem
    # Y(1) + M(1) + D(1) + H(1) + X(1)
    assert stem[0] == gen.to_b36(gen.gregorian_to_jalali(now.year, now.month, now.day)[0] % 100, 1)
    assert stem[4] == gen.to_b36(0, 1)


def test_short_stem_year_is_base36_single_char():
    # Jalali year 1406 -> 06 -> base36 '6'
    now = dt.datetime(2027, 3, 21, 0, 0, 0)  # 1406/01/01
    jy, _, _ = gen.gregorian_to_jalali(now.year, now.month, now.day)
    assert jy == 1406
    stem, _ = gen.serial_stem_short(now, counter=0)
    assert stem[0] == '6'


def test_short_stem_counter_advances_x():
    now = dt.datetime(2026, 11, 6, 14, 0, 0)
    stems = [gen.serial_stem_short(now, counter=i)[0] for i in range(3)]
    assert stems[0][4] == '0'
    assert stems[1][4] == '1'
    assert stems[2][4] == '2'
    assert len({s[:4] for s in stems}) == 1  # same hour prefix


def test_short_stem_counter_overflow_rejected():
    now = dt.datetime(2026, 11, 6, 14, 0, 0)
    with pytest.raises(ValueError):
        gen.serial_stem_short(now, counter=36)


def test_next_free_counter_scans_existing_batch_folders(tmp_path):
    now = dt.datetime(2026, 11, 6, 14, 0, 0)
    prefix = gen.serial_stem_short(now, counter=0)[0][:4]  # Y M D H
    # Simulate two batches already made this hour: X=0 and X=1
    (tmp_path / f'batch_{prefix}0').mkdir()
    (tmp_path / f'batch_{prefix}1').mkdir()
    # Unrelated folder from another hour must be ignored
    (tmp_path / 'batch_zzzz0').mkdir()
    assert gen.next_free_counter(tmp_path, now) == 2


def test_next_free_counter_ignores_non_batch_entries(tmp_path):
    now = dt.datetime(2026, 11, 6, 14, 0, 0)
    (tmp_path / 'preview_whatever').mkdir()
    (tmp_path / 'notes.txt').write_text('x')
    assert gen.next_free_counter(tmp_path, now) == 0
