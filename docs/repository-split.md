# Standalone snapshot and ownership

Source: `btc4-fun/btc-envelope-maker`, commit
`e0e925c8d224a7595a15261e50e97b50d300a782`.

All 26 tracked generator files were exported using an explicit path allowlist
and `git show COMMIT:path`; no workspace directory was recursively copied.
The committed legacy requirements file was used. The original local source,
private artifacts and dirty legacy requirements remain untouched in the website
workspace. Index removal there is a separate publication-owner step.

`source-provenance.json` records each source path, Git blob ID and SHA-256,
including license, notice, preserved security reports and the metadata-schema
tests moved from the website. `source_sha256` fields describe original bytes. Destination adaptations are recorded
with final hashes and reasons in the same manifest.

The pure address validator is retained byte-for-byte in both owners with the
embedded Pieter Wuille MIT notice. There is no cross-repository runtime/import
or test dependency. Both own identical public_contract.json test vectors:
explicit Jalali timestamp serial stems, base36 suffixes and public BIP173/BIP84
addresses. Expected values are not calculated by the implementation under test.
Coordinate changes and provenance updates explicitly; never silently fetch code
from the other repository at runtime or during tests.

The generator owns PDF/QR/recovery, database schema and generator-branding tests.
The website owns HTTP admission and browser checks using its copy of the public
contract. Optional PostgreSQL helpers are operator tools, never website runtime
requirements. Run those CLI tools from this repository when separately authorized.

No deployment, live database access or migration is part of this extraction.

# New-output domain batch verification

The new printed brand and website part of contact defaults are b.tc4fun.ir. Contact email and mempool explorer are unchanged. Existing explicit configurations remain authoritative; no existing PDFs, wallets or ledgers were opened or rewritten.

Implementation and initial review used installed Codex 0.157.1 with catalog-discovered affordable gpt-reserve, selected explicitly. Isolated CLI workers could not see the host's dependency environment; their missing pytest report was not a product failure. Parent reran the full synthetic suite with the existing generator interpreter and private scratch basetemp:

```
/home/saeb/PycharmProjects/btc4fun/btc_envelope_maker/btc_envelope_maker/.venv/bin/python -B -m pytest -p no:cacheprovider --basetemp /home/saeb/.hermes/cache/scratch/btc4fun-generator-parent-accepted btc_envelope_maker/tests -q
153 passed, 1 skipped in 16.00s
```

Full testing exposed a stale extraction-provenance assertion. Updated only current destination digests and descriptions for the three adapted files, preserving historical source digests and blob IDs. The test continues enforcing unchanged validator and database sources and explicitly pins the original generator provenance while allowing the approved branding adaptation.

Pre-existing modified scripts/publication-allowlist.json and untracked AGENTS.md are excluded from this task's commit. No production database, real wallet, private assets or generated recovery material was accessed. Physical print inspection and offline-machine operational assurance are not proved by synthetic tests.

Publication correction: the separate verification document was rejected by hosted CI because it was outside the reviewed source allowlist. Its content is retained here instead; the pre-existing user allowlist edit remains untouched.
