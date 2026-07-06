# OpenWASH — licensing analysis & recommendation

_Status: recommendation for approval. Not yet applied (no LICENSE files dropped). Get a real
legal eyeball before a formal public launch — see Risks._

## TL;DR recommendation

| Bucket | What | License |
|---|---|---|
| **Code** | `engine/`, `tests/`, `research/*.py` | **Apache-2.0** |
| **Data** | `data/*.yaml` — the curated safety facts + schema + annotations | **CC-BY-4.0** |
| **Docs** | `README.md`, `data/README.md`, `research/reading/*.md` | **CC-BY-4.0** |

Plus a **NOTICE / provenance statement** (below) making explicit that the safety numbers are
cited facts, that OpenWASH claims copyright only in its selection/arrangement/schema/annotations,
that source documents are NOT redistributed, and that this is unaffiliated with WHO/EAWAG/etc.

This slightly revises the README's earlier "intended: Apache-2.0 + CDLA-Permissive-2.0": keep
Apache-2.0 for code, but prefer **CC-BY-4.0 over CDLA-Permissive-2.0** for the data (reasoning below).

## Why these, specifically

**Strategic goal = maximal embedding.** The mission is for the guardrail/substrate to be the
verification layer *everywhere* — including in **commercial** tools (CBS operators, funders'
outcome-verification systems) and **proprietary** software. That rules OUT anything
non-commercial (NC) or share-alike/copyleft (SA, ODbL, CC-BY-SA): those block exactly the
adoption the project exists to achieve.

**Permissive, but WITH attribution** (not CC0/public-domain), because:
- The project's soul is **provenance** — waiving attribution (CC0) undercuts the "cite the
  substrate" norm that builds its authority and trust, which IS the moat.
- **CC-BY-4.0** is the most universally recognized open license, it **explicitly covers sui
  generis database rights** (mitigating EU risk by being clear what we grant), and attribution is
  a light burden any tool can meet. Funders, NGOs, and academics know how to comply instantly.
- **CDLA-Permissive-2.0** (the earlier intended pick) is fully defensible and more "data-native,"
  but it's less recognized outside data/ML and its 2.0 revision dropped even the attribution
  requirement — so CC-BY-4.0 is a small upgrade for *this* project's citation-first ethos.

**Apache-2.0 for code** (not MIT): permissive + trusted + an explicit **patent grant**, which
matters if any method (e.g. a future viability-verification approach) touches patentable ground.

## Why the NC/SA upstreams do NOT force our hand

- **Facts aren't copyrightable** (US *Feist v. Rural*). "≤1 viable helminth egg/g", "6-log
  reduction for unrestricted irrigation", the die-off constants — these are facts. WHO's
  CC-BY-NC-SA and EAWAG's NC-custom terms govern reproducing their **text/tables/expression**, not
  extracting a number and citing it.
- **We don't rehost.** The committed dataset holds facts + citations + *our* schema and prose; the
  `.gitignore` excludes every source PDF/derived-text file. There is no WHO/EAWAG/Sphere/CAWST
  *expression* in the repo to which their terms could attach.
- **Our compilation is our own work** — original selection, arrangement, corroboration schema,
  lineage analysis, and notes — copyrightable by us and lawfully licensed by us.
- Upstream terms recorded per-source in `data/sources.yaml`: WHO © (×3, cite & extract), Sphere ©
  (redistribute unmodified w/ attribution), EAWAG (open access, NC, w/ attribution), CAWST (NC WASH
  use), EPA 40 CFR (US federal, public domain), peer-reviewed papers (OA + non-OA). The CC-BY-SA
  copyleft sources (Akvopedia/SSWM) were **considered but NOT used** — confirmed absent from `data/`.

## Risks / honest caveats (why "get a legal eyeball before launch")

1. **EU sui generis database right.** Unlike US law, the EU protects *substantial extraction* from
   a database even of non-copyrightable facts. Our extraction is **selective and transformative
   across 24 sources** (not a bulk copy of any one WHO/EAWAG table), which is the defensible
   posture — but a formal public release would benefit from confirming no single source was
   "substantially extracted."
2. **Keep the no-rehost discipline forever.** The whole facts-not-expression argument depends on
   never committing reproduced source tables/prose. Keep `.gitignore` tight; keep extractions to
   facts + our words.
3. **NC terms bind *their* works, not our facts** — but to leave zero room for argument, never
   paste a WHO/EAWAG table verbatim; always re-express + cite.
4. **Attribution/trademark:** cite sources; do **not** imply WHO/EAWAG/Sphere endorsement (the
   NOTICE handles this).

## Proposed NOTICE / provenance statement (ship in the repo)

> OpenWASH curates **safety facts** — thresholds, die-off constants, and reduction targets —
> extracted from and **cited to** their original sources (WHO, EAWAG/Sandec, Sphere, US EPA, and
> peer-reviewed literature; see `data/sources.yaml`). Those facts are not owned by OpenWASH.
> OpenWASH claims copyright only in its **original selection, arrangement, schema, corroboration
> logic, and annotations**, released under CC-BY-4.0 (data/docs) and Apache-2.0 (code). Source
> documents remain under their own terms and are **NOT redistributed** here. OpenWASH is
> independent and **not affiliated with or endorsed by** any cited organization.

## To apply (on approval)
- `LICENSE` (Apache-2.0, code) + `LICENSE-DATA` (CC-BY-4.0, data/docs) + `NOTICE` (the statement).
- Update README license line + `data/README.md`; add a one-line SPDX header option to engine files.
- Add `requirements.txt` (pyyaml, pytest) while touching hygiene.
