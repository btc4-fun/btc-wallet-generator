# Regency Method-3 envelopes

Select with `--regency` (no changes to private `config.toml` are required), or set
`layout = "regency"`. The existing pairs/separate layouts remain available.

Preview from the repository root:

```sh
.venv/bin/python btc_envelope_maker/btc_envelope_maker.py --regency --preview --config btc_envelope_maker/config.example.toml --out out
```

For real offline generation use your operator config and replace `--preview` with
`--count 1 --acknowledge-offline`. Disconnect networking first; never fund preview
addresses. One count means FOUR independent wallets, FOUR A4 envelope leaves,
and ONE A4 public companion leaf, not one physical leaf. Output retains restrictive
permissions, rollback cleanup, and the public-only ledger. Recovery words are
printed directly on each envelope's inward face, never on a separate insert.

For one group, `sheets.pdf` contains nine A4 portrait pages:

- 1/2: inside/back of envelope 1
- 3/4: inside/back of envelope 2
- 5/6: inside/back of envelope 3
- 7/8: inside/back of envelope 4
- 9: four public companion cards; each has address QR, serial lookup QR and explanation

For N groups, pages 1 through 8N are duplex envelope pairs. Pages 8N+1 through 9N
are public companions, printed separately. Never send the whole SECRET PDF to an
online print service, even if only requesting its public pages.

Print envelope pages at ACTUAL SIZE / 100%, A4 portrait, duplex, FLIP ON LONG EDGE.
Do not use fit-to-page or booklet mode. Print companion pages separately, simplex.
First print a PUBLIC PREVIEW and physically fold it to check printer registration,
orientation, QR scanning, paper opacity and complete secret concealment. Software
checks cannot certify your printer, physical folds or resistance to opening.

With the secret face toward you, fold the left and right edges to the centre
(crease x=52.5 and 157.5 mm). Fold the bottom upward along the line 80 mm from the
bottom. Fold the top down along the line 189 mm from the bottom; its edge lands
at 81 mm, leaving 1 mm clearance. Tuck the flaps together, then seal their joint
on the flap side, opposite the address QR. The uncreased central panel is about
105 x 109 mm. Use opaque paper: wax is evidence of disturbance, not protection
against reading through thin paper or a guarantee of exclusive custody.

The back bears the address QR and this notice, with the URL on its own line:

هشدار: قبل از باز کردن سایت

https://b.tc4fun.ir

مطالعه شود

Public companions link to `https://b.tc4fun.ir/s/<serial>`. These are public
Bitcoin receiving addresses, not raw public keys. The secret is the BIP39 recovery
phrase (12 or 24 words), retaining the existing BIP84 derivation.

Folding reference: Method 3 in
https://noteandwish.com/blogs/journal-lab/regency-era-letter-folding-tutorial-jane-austen-style

Automated tests extract PDF text, rasterize and decode the private/address/lookup
QRs using public test vectors, and check page pairing and absence of recovery
words on backs and companion pages. Physical print/fold acceptance remains an
operator step before using any real wallet.

## Card-sized envelopes (`--regency-card`)

The sealed packet is exactly credit-card size, 85.6 x 54 mm, so it drops into a
gift box. Select with `--regency-card` (or `layout = "regency_card"`); the private
`config.toml` is untouched.

```sh
.venv/bin/python btc_envelope_maker/btc_envelope_maker.py --regency-card --preview --config btc_envelope_maker/config.example.toml --out out
```

Each leaf is 171.2 x 148 mm and two leaves stack on one A4 (2 x 148 = 296 mm).
Leaves are centred horizontally (19.4 mm margins) so long-edge duplex mirrors the
back onto the same leaf. One group is still four wallets, so `sheets.pdf` has five
A4 pages:

- 1: inside of envelopes 1 and 2 (top leaf, bottom leaf)
- 2: backs of envelopes 1 and 2
- 3: inside of envelopes 3 and 4
- 4: backs of envelopes 3 and 4
- 5: four public companion cards

For N groups, pages 1 through 2N are duplex envelope pairs and pages 2N+1 through
3N are public companions.

Leaf geometry, measured from the bottom edge of the leaf:

- panel: x 42.8 to 128.4 mm, y 28 to 82 mm (85.6 x 54 mm)
- bottom flap: y 0 to 28 mm, folds up
- top flap: y 82 to 148 mm, folds down; its outer 12 mm (y 136 to 148) is the
  wax-seal tab and lands at y 16 to 28 mm, i.e. 12 mm past the bottom fold
- side flaps: x 0 to 42.8 and x 128.4 to 171.2, fold to the centre line

Fold with the secret face toward you: sides to the centre, bottom up, top down.
The seal tab then overhangs the back by 12 mm; put the wax seal there, never on
the address QR. Cut the two leaves apart on the solid border before folding.

Print at ACTUAL SIZE / 100%, A4 portrait, duplex, FLIP ON LONG EDGE, then the
companion page simplex.

The inside face carries the recovery words twice: printed as a numbered list and
encoded as a 20 mm QR beside it, so the holder can restore by scanning instead of
retyping. Both are the same secret and both stay inside the sealed panel. The back
carries only the public address QR.

The top flap carries cold-storage guidance and the link
`https://b.tc4fun.ir/security` instead of fold instructions — the crease lines are
self-explanatory once the cut border is solid and the folds are hatched.

Line convention on the leaf: the outer border is a SOLID line (cut here), the
fold creases are a fine hatched/dashed grey line (crease here), and the seal-tab
boundary is the only red dashed line. Never cut a hatched line.
