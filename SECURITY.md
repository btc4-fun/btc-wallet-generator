# Generator security policy

Report privately to 09113458375@btc4.fun. Never send recovery words, private
keys, confidential PDFs, credentials or customer ledgers in issues or messages.

This standalone repository preserves the generator behavior and limitations
from the source snapshot; extraction is not a new security certification.
Use trusted offline hardware and printing, review dependencies, and perform an
independent recovery check before handling funds. Failed network probes are not
proof of isolation. Public preview phrases must never receive funds.

## Preserved historical evidence

The following are byte-preserved reports from the pre-split combined repository.
Website paths and deployment descriptions inside them are historical, not
instructions to copy website code here or proof about today's live service:

- [Original security policy and unresolved limitations](docs/history/SECURITY.md)
- [Generator security follow-up](docs/history/SECURITY-FOLLOWUP.md)
- [Second review](docs/history/SECURITY-ROUND2.md)

The generator still requires explicit offline acknowledgment for real generation,
uses restrictive creation permissions and excludes public previews from inventory.
Catchable-error cleanup cannot prove secure deletion, protect against hostile
parent directories, or recover from all process/power failures. Locked hashes
identify package bytes, not publisher authenticity or independently audited code.

Source publication must pass `scripts/check_publication.py` and its complete-index
mode. This allowlist/credential check cannot establish safety of arbitrary image
content or catch every secret. Only the original tracked public font/logo assets
are included, with source hashes in the provenance manifest; no operator images,
configuration, PDFs, databases or wallet outputs were exported.
