"""Regency envelopes: only public test vectors, never fresh entropy."""
import subprocess
from PIL import Image

from test_generator_security import gen, deny_random_generation, cli
from test_generator_crypto import decode_qrs


def leaf_crop(image, index):
    """Crop one 171.2 x 148 mm leaf out of a 600 dpi A4 render (index 0 = top)."""
    w, h = image.size
    top = index * h * gen.CARD_LEAF_H / 297.0
    return image.crop((0, int(top), w, int(top + h * gen.CARD_LEAF_H / 297.0)))


def test_regency_cli_selects_four_wallet_group_without_changing_config(cli):
    cli.run('--regency', '--preview')
    assert cli.cfg['layout'] == 'regency'
    assert ('render', 4) in cli.calls


def test_regency_multigroup_public_pages_follow_all_duplex_pairs(tmp_path):
    cfg = dict(gen.DEFAULTS, _logo=None, layout='regency', words=24)
    gen.register_fonts(cfg)
    wallets = [gen.Wallet(f'0587k4530{i}', gen.TEST_ADDRESS, gen.TEST_MNEMONIC_24) for i in range(8)]
    pdf = tmp_path / 'multi.pdf'
    with gen.private_creation():
        assert gen.render_sheets(cfg, gen.make_plan(cfg), wallets, {'sheet': pdf}, True) == 2
    pages = subprocess.run(['pdftotext', '-raw', str(pdf), '-'], check=True,
                           capture_output=True, text=True).stdout.split('\f')[:-1]
    assert len(pages) == 18
    for i, wallet in enumerate(wallets):
        assert wallet.serial in pages[2 * i] and wallet.serial in pages[2 * i + 1]
        assert 'art' in pages[2 * i] and 'abandon' not in pages[2 * i + 1]
    assert all('abandon' not in page for page in pages[16:])


def test_regency_card_geometry_is_credit_card_sized_with_a_seal_tab():
    assert (gen.CARD_ENV_W, gen.CARD_ENV_H) == (85.6, 54.0)
    assert gen.CARD_LEAF_W == 2 * gen.CARD_ENV_W
    assert gen.CARD_LEAF_H * 2 <= 297, 'two leaves must fit one A4'
    assert gen.CARD_LEAF_X * 2 + gen.CARD_LEAF_W == 210, 'leaf must be centred for long-edge duplex'
    assert gen.CARD_BOTTOM_FLAP + gen.CARD_ENV_H + gen.CARD_TOP_FLAP == gen.CARD_LEAF_H
    assert gen.CARD_TOP_FLAP == gen.CARD_ENV_H + gen.CARD_SEAL_TAB
    # the top flap edge lands CARD_SEAL_TAB below the bottom fold: that is the seal tab
    landing = gen.CARD_TOP_FOLD - gen.CARD_TOP_FLAP
    assert landing == gen.CARD_BOTTOM_FLAP - gen.CARD_SEAL_TAB


def test_regency_card_two_envelopes_per_a4_and_one_public_sheet(tmp_path):
    cfg = dict(gen.DEFAULTS, _logo=None, layout='regency_card')
    gen.register_fonts(cfg)
    plan = gen.make_plan(cfg)
    assert (plan.page_w, plan.page_h, plan.per_sheet) == (210, 297, 4)
    wallets = [gen.Wallet(f'0587k4530{i}', gen.TEST_ADDRESS, gen.TEST_MNEMONIC) for i in range(4)]
    pdf = tmp_path / 'card.pdf'
    with gen.private_creation():
        assert gen.render_sheets(cfg, plan, wallets, {'sheet': pdf}, True) == 1
    text = subprocess.run(['pdftotext', '-raw', str(pdf), '-'], check=True,
                          capture_output=True, text=True).stdout.split('\f')
    assert len(text[:-1]) == 5
    # page 1: inside of wallets 0 and 1; page 2: their backs
    assert wallets[0].serial in text[0] and wallets[1].serial in text[0]
    assert 'abandon' in text[0]
    assert 'abandon' not in text[1]
    assert wallets[0].serial in text[1] and wallets[1].serial in text[1]
    assert 'https://b.tc4fun.ir' in text[1]
    # page 3/4: wallets 2 and 3
    assert wallets[2].serial in text[2] and wallets[3].serial in text[2]
    assert 'abandon' not in text[3]
    # page 5: public companions only
    assert 'abandon' not in text[4]
    for wallet in wallets:
        assert 'https://b.tc4fun.ir/s/' + wallet.serial in text[4]
    # The fold instructions are gone; the flap now carries cold-storage guidance.
    assert 'روش سوم' not in text[0]
    assert 'https://b.tc4fun.ir/security' in text[0]
    # The seal-tab caption is gone: the tab is marked by the red dashed line and
    # the Bitcoin mark, not by a Persian label.
    assert 'زبانه' not in text[0] and 'زبانه' not in text[1]
    # No btc4.fun reference survives anywhere on the leaf, mailbox included.
    assert 'btc4.fun' not in text[0] and 'btc4.fun' not in text[1]
    # The inside face carries the recovery words as a QR, one per leaf. The QR is
    # 20 mm on a 171 mm leaf, so decode a per-leaf crop at 600 dpi, not the page.
    for page in (1, 3):
        out = tmp_path / f'card-{page}'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-r', '600',
                        '-singlefile', '-png', str(pdf), str(out)], check=True, capture_output=True)
        with Image.open(str(out) + '.png') as image:
            assert set(decode_qrs(leaf_crop(image, 0))) == {gen.TEST_MNEMONIC}
            assert set(decode_qrs(leaf_crop(image, 1))) == {gen.TEST_MNEMONIC}
    # Backs carry the public address QR, one per leaf.
    for page in (2, 4):
        out = tmp_path / f'card-{page}'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-scale-to', '3500',
                        '-singlefile', '-png', str(pdf), str(out)], check=True, capture_output=True)
        with Image.open(str(out) + '.png') as image:
            assert set(decode_qrs(image)) == {gen.TEST_ADDRESS}
    out = tmp_path / 'card-5'
    subprocess.run(['pdftoppm', '-f', '5', '-l', '5', '-scale-to', '3500',
                    '-singlefile', '-png', str(pdf), str(out)], check=True, capture_output=True)
    with Image.open(str(out) + '.png') as image:
        assert set(decode_qrs(image)) == {gen.TEST_ADDRESS} | {
            'https://b.tc4fun.ir/s/' + w.serial for w in wallets}
    assert pdf.stat().st_mode & 0o777 == 0o600


def test_regency_card_cli_selects_the_card_layout(cli):
    cli.run('--regency-card', '--preview')
    assert cli.cfg['layout'] == 'regency_card'
    assert ('render', 4) in cli.calls


def test_regency_four_envelopes_have_paired_backs_and_one_public_sheet(tmp_path, monkeypatch):
    cfg = dict(gen.DEFAULTS, _logo=None, layout='regency')
    gen.register_fonts(cfg)
    plan = gen.make_plan(cfg)
    assert (plan.page_w, plan.page_h, plan.per_sheet) == (210, 297, 4)
    wallets = [gen.Wallet(f'0587k4530{i}', gen.TEST_ADDRESS, gen.TEST_MNEMONIC) for i in range(4)]
    pdf = tmp_path / 'sheets.pdf'
    with gen.private_creation():
        assert gen.render_sheets(cfg, plan, wallets, {'sheet': pdf}, True) == 1
    text = subprocess.run(['pdftotext', '-raw', str(pdf), '-'], check=True,
                          capture_output=True, text=True).stdout.split('\f')
    assert len(text[:-1]) == 9
    for i, wallet in enumerate(wallets):
        assert wallet.serial in text[2 * i]
        assert wallet.serial in text[2 * i + 1]
        assert '1.' in text[2 * i] and 'abandon' in text[2 * i]
        assert 'abandon' not in text[2 * i + 1]
        assert 'https://b.tc4fun.ir' in text[2 * i + 1]
    assert 'abandon' not in text[8]
    for wallet in wallets:
        assert 'https://b.tc4fun.ir/s/' + wallet.serial in text[8]
    for page, expected in [(1, {gen.TEST_MNEMONIC}), (2, {gen.TEST_ADDRESS}),
                           (9, {gen.TEST_ADDRESS} | {'https://b.tc4fun.ir/s/' + w.serial for w in wallets})]:
        out = tmp_path / f'page-{page}'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-scale-to', '3500',
                        '-singlefile', '-png', str(pdf), str(out)], check=True, capture_output=True)
        with Image.open(str(out) + '.png') as image:
            assert set(decode_qrs(image)) == expected
    assert pdf.stat().st_mode & 0o777 == 0o600
