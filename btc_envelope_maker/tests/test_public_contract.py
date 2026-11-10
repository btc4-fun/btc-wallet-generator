"""Fixed public expectations; no sibling repository or production configuration."""
import ast
import datetime as dt
import json
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((Path(__file__).parent / 'fixtures/public_contract.json').read_text())


class GeneratorBrandingContract(unittest.TestCase):
    def test_generator_defaults_and_sanitized_example_have_public_brand(self):
        tree = ast.parse((ROOT / 'btc_envelope_maker/btc_envelope_maker.py').read_text())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'DEFAULTS' for target in node.targets))
        defaults = ast.literal_eval(assignment.value)
        example = tomllib.loads((ROOT / 'btc_envelope_maker/config.example.toml').read_text())
        for config in (defaults, example):
            self.assertEqual(config['brand_name'], 'b.tc4fun.ir')
            self.assertEqual(config['contact'], 'b.tc4fun.ir   |   09113458375@b.tc4fun.ir')
            self.assertEqual(config['db_url'], '')
            self.assertEqual(config['explorer_url'], 'https://mempool.space/address/')



def test_existing_configured_brand_is_not_rewritten(tmp_path):
    """The new default affects new runs only; old config/output identity survives."""
    config = tmp_path / 'existing-config.toml'
    config.write_text(
        'brand_name = "btc4.fun"\n'
        'contact = "btc4.fun   |   09113458375@btc4.fun"\n'
        'explorer_url = "https://mempool.space/address/"\n',
        encoding='utf-8',
    )
    from test_generator_security import gen

    loaded = gen.load_config(config)
    assert loaded['brand_name'] == 'btc4.fun'
    assert loaded['contact'] == 'btc4.fun   |   09113458375@btc4.fun'
    assert loaded['explorer_url'] == 'https://mempool.space/address/'



def test_serial_encoder_matches_independently_specified_public_contract():
    from test_generator_security import gen
    for vector in CONTRACT['serial_stems']:
        stem, _ = gen.serial_stem(dt.datetime.fromisoformat(vector['moment']), vector['mode'])
        assert stem == vector['expected']
    for vector in CONTRACT['suffixes']:
        assert gen.to_b36(vector['index'], vector['width']) == vector['expected']


def test_address_public_contract():
    from test_address_validation import validator
    for vector in CONTRACT['addresses']:
        assert validator.valid_address(vector['value']) == vector['valid']
        assert validator.valid_inventory_address(vector['value']) == vector['inventory']
