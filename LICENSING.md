# OpenWASH — licensing analysis & recommendation

_Status: **APPLIED.** `LICENSE` (Apache-2.0) + `LICENSE-DATA` (CC-BY-4.0) + `NOTICE` are in the
repo. The EU database-right question is **resolved — LOW risk** (see Risks). This file records the
decision, the rationale, and the honest residual caveats._

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

## Risks / honest caveats

**EU sui generis database right — RESOLVED: LOW risk** (analysis 2026-07; legal *information*, not
legal advice). The right (Directive 96/9/EC, Art. 7/10/11) is held only by **EEA-domiciled makers**,
and the flagship sources are not: **WHO** is an international organisation, **EAWAG and Sphere are
Swiss** (Switzerland is outside the EEA and grants no such right), **EPA** is US public domain — so
there is **no enforceable EU database right in those sources to infringe**. Three independent
backstops reinforce this: *created-not-obtained* (**BHB v William Hill, C-203/02, 2004**) excludes
investment in *setting* guideline values; the harm-filter in **CV-Online Latvia, C-762/19, 2021**
defeats infringement for selective, cited, non-rehosting extraction; and a US maker/host/users sits
outside the right's territorial reach. **CC-BY-4.0 correctly *licenses* (not waives) our own
equivalent right** for EU re-users. Verdict: a paid legal review is **not warranted for the database
right alone**; commission one only if the project scales commercially or takes IP-contingent funding.

**Where the (still modest) residual risk actually is — copyright / NC-licence compatibility, NOT the
database right.** WHO's post-2016 **CC-BY-NC-SA** and EAWAG's **custom NC** terms attach *NonCommercial*
conditions to their *copyrightable expression* — which would conflict with our commercially-permissive
CC-BY-4.0 **only if we reproduced their text/tables/figures**. We don't (facts + our own words +
citations, nothing rehosted), so there is little to bite on. If a review is ever wanted, **scope it
narrowly to this copyright/NC question**, not the database right.

**Cheap defensive steps (keep doing these):**
1. **Keep the facts↔expression line bright** — re-express every value in our own words + YAML schema;
   never paste a source sentence, table layout, or figure caption verbatim.
2. **Cite precisely** (source, edition/year, section, exact value) — attribution also defeats the
   "market substitution/harm" narrative under CV-Online.
3. **Segregate any NC-encumbered *copyrightable* content** if it ever must appear — hold it under the
   source's NC terms, don't sweep it into the CC-BY-4.0 grant. Prefer paraphrase.
4. **Keep the `NOTICE`/provenance statement** (below) and the tight `.gitignore` (no rehosting).
5. **Honour any takedown/attribution request** promptly — cheap goodwill that forecloses escalation.
6. Do **not** imply WHO/EAWAG/Sphere endorsement (the NOTICE handles this).

> One unverified item: individual peer-reviewed papers' publisher domiciles/licences weren't checked
> one-by-one; the risk there is weak on substantial-part + harm, but it's the only residual EU-source
> exposure. This is a reasoned map of the law, not an opinion to rely on in litigation.

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
