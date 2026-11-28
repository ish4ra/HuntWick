# Platform logo coverage

The offline audit uses the same unified directory as Desktop. Each row retains its catalog name. The results grid, list, Platforms directory, history preview, reopened results and hosted platform selector use the same component. No search input, profile URL or image request leaves the application to load a logo. The Web Edition keeps its existing search allowlist.

| Catalog scope | Entries | Direct brand | Alias | Software family | Neutral globe | Actual logos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All eligible with both optional categories enabled | 4,613 | 166 | 37 | 4,164 | 246 | 4,367 |
| Default policy | 4,553 | 150 | 33 | 4,163 | 207 | 4,346 |
| Adult category enabled, experimental off | 4,570 | 150 | 33 | 4,163 | 224 | 4,346 |
| Informational unavailable entries | 6,606 | 124 | 24 | 54 | 6,404 | 202 |

Each scope counts a platform once. A direct brand matches the case-insensitive catalog name. An alias uses a normalized spelling, reviewed alternate name or equivalent provider identity. Family inheritance uses the pinned Maigret engine for each named instance. The registry includes 304 distinct brand assets and a second original colour variant for Laracasts. Logo availability is independent of whether a profile lookup is enabled or returns a match. [Complete per-platform CSV](catalog.csv) · [Generated counts](coverage.json)

RC.6 shipped 31 genuine SVGs, all byte-identical to their Simple Icons originals. Its exact-name table recognized 29 selectable rows. A number of those assets also have legitimate names outside that spelling list, including Replit, Twitter and Ko-fi. The new resolver handles those names in older saved results. The browser check decodes every bundled image at a 19-pixel display size and checks actual representative painted pixels on both themes. No corrupt RC.6 SVG was identified. [Light contact sheet](logos-light.png) · [Dark contact sheet](logos-dark.png)

## Instance identity

The generator checks the SHA-256 of the exact upstream Maigret database shipped in its locked wheel. It joins each bundled profile's provider names to that database's declared engine. This recognizes domains such as mstdn.party with no family name in their hostname. Explicit brand or reviewed instance overrides take precedence. Discourse and DiscourseJson share one logo. The Gitea detector can also be used on Forgejo installations. A small reviewed override list handles independently identified Forgejo services such as git.gay. Unclassified software migrations can leave an instance displaying the previously identified family. The UI never substitutes the software name for the actual instance name. [Maigret snapshot](../../engine/notices/Provenance.md) · [Reviewed public Forgejo instances](https://codeberg.org/forgejo-contrib/delightful-forgejo#public-instances)

The all-eligible rows inherit 2,772 Discourse, 499 GitLab, 458 Gitea, 229 Flarum, 142 Lemmy, 63 Mastodon and one independently identified Forgejo mark. Direct service overrides include Codeberg. The globe covers unrecognized services and ambiguous name collisions. The per-row CSV records missing permissions or an unconfirmed artwork identity where available. Examples include Sketchfab and Newgrounds, where the reviewed Simple Icons records lacked an individual license, and Shelf, where a same-name app glyph could not be authenticated as the correct service. Every remaining fallback has an explicit reason in the audit. [Per-file artwork credits](../../public/platforms/credits.csv) · [Redistribution notices](../../public/platforms/NOTICE.txt)

## Refresh and verify

Run from the repository root using its pinned engine environment.

```sh
uv run --project engine --frozen python scripts/platform_logos/registry.py
uv run --project engine --frozen python scripts/platform_logos/registry.py --check
npm test -- src/platformLogos.test.ts
```

The generator updates the runtime index and both audit files together. Engine CI regenerates them in memory and checks exact equality. Adding, removing or renaming a catalog platform therefore sends its coverage decision through review. The generator validates local SVG structure, strict local-only references, unique alias ownership, the asset hashes and the original-colour variant.

To find artwork for new fallback entries, run the candidate scanner with one or more downloaded upstream npm archives, for example `uv run --project engine --frozen python scripts/platform_logos/suggest.py simple-icons-16.38.1.tgz`. It prints the unresolved platform, archive and matching icon name. Inspect the original artwork, source rights, trademark guidelines and whether the service is genuinely the same brand. Only approved matches go into the ledger. Preserve a new collection's notice under `public/platforms/licenses`. Add its original file, hash, source and reviewed aliases in `public/platforms/credits.csv`. Record an unresolved review decision in `scripts/platform_logos/review.json`. For family changes, update the evidence and mapping in the generator.

For the visual regression, install the project frontend dependencies and use Python with Playwright, Pillow and Chromium. Run `python scripts/check_platform_logos.py`. This renders the real React component with the production CSS in a loopback browser. It checks every image decodes, 32 representative identifiers remain visible, both theme renders contain visible artwork, and all requests stay local. The only fixture with an invented name demonstrates the neutral fallback.

These are the reviewed source pins for reproduction.

| Source | Version or revision | SHA-256 of reviewed npm archive |
| --- | --- | --- |
| Simple Icons | 16.38.1 | 8ad81af0009aa0935df4411080feb4547b72e13458bbcf4d803b259b1f078804 |
| Font Awesome Free | 7.3.1 | ca4e32843bd81711894385c2466fb19c55cfd32ef3c58830b2d1df7bd42e6571 |
| CoreUI Icons | 3.1.0 | c46ae8d72ab9adedcd62503e9d6f077a9070516b82d0b2f98d0a0e45c96c45c1 |
| Tabler Icons | 3.53.0 | 207d929bb9337c22019073df4b997e20735a4a91fede8861af96d05ceed7b396 |
| Iconify Arcticons | 1.2.62 | ce979b788134186bf7fe6d32cc2eb707dc54a0bf6a53c63f3b749c683c74cc60 |

Flarum retains the original Foundation PNG and original colours. Laracasts uses the original colour variants distributed by Dashboard Icons. Their exact source revisions are in the ledger. Separate license texts and per-icon upstream links travel with the local assets.
