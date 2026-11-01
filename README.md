# btc-wallet-generator

Standalone offline Bitcoin paper-wallet generator for btc4.fun. Source-available
under [PolyForm Noncommercial 1.0.0](LICENSE.md); see [NOTICE](NOTICE).
This repository does not run the website or either Android application.

## Start here

- [Printing and operating instructions](btc_envelope_maker/README.md)
- [Pinned dependencies and offline preparation](btc_envelope_maker/DEPENDENCIES.md)
- [Security boundaries and historical findings](SECURITY.md)
- [Snapshot provenance](docs/source-provenance.json)
- [Extraction and shared public contracts](docs/repository-split.md)

The nested directory is intentional: existing CLI/import/font/configuration
paths have been preserved. From the repository root:

```sh
cd btc_envelope_maker
python3.13 -m venv .venv
.venv/bin/pip install --require-hashes --only-binary=:all: -r requirements-runtime.txt
cp config.example.toml config.toml
.venv/bin/python btc_envelope_maker.py --preview
```

Preview uses a public recovery phrase. **Never fund preview/test addresses.**
Keep real config, wallets, PDFs, ledgers and databases outside Git; disconnect
networking and use a trusted offline machine/printer before real generation.
The legacy requirements.txt was exported from the committed snapshot, not from
an operator's locally modified dependency file. Use the hash-locked files.

## Independent verification

On a disposable Linux x86_64 CPython 3.13 test environment, install
`poppler-utils`, `libzbar0` (or the distro's `libzbar0t64`) and
`fonts-dejavu-core`, then from the repository root:

```sh
python -m pip install --require-hashes --only-binary=:all: -r btc_envelope_maker/requirements-runtime.txt -r btc_envelope_maker/requirements-test.txt
python -B scripts/check_publication.py
python -B scripts/check_publication.py --index
python -B -m pytest -p no:cacheprovider --basetemp "$TMPDIR/generator-tests" btc_envelope_maker/tests -q
```

Set TMPDIR to a private disposable directory before running tests. Tests use
public vectors, synthetic configuration and disposable SQLite, not real keys,
wallet records or a PostgreSQL service. PDF tests render real PDFs, extract text,
rasterize/decode QR pixels and independently recover addresses from printed
words. Native dependencies must exist: those checks do not silently skip.
The index guard scans the entire index; it is meaningful after source is staged
or checked out, not on an empty new index. The source guard also supports this
initial unstaged snapshot and rejects any unreviewed file.

## Separate owners

- Website/backend: https://github.com/btc4-fun/btc-envelope-maker
- Generator publication target: https://github.com/btc4-fun/btc-wallet-generator
- Customer app: https://github.com/btc4-fun/btc-tag-checker
- Seller app: https://github.com/btc4-fun/btc-tag-mapper

Repository publication is separate from website deployment. A split alone does
not resolve historical security findings or authorize migrations/deployment.
