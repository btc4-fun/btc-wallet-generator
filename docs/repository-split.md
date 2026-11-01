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
