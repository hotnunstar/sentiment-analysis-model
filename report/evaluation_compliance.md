# Evaluation Guide compliance summary

**Note:** `Evaluation_Guide.pdf` is **not** inside `sentiment-analysis-model`; criteria follow course materials cited in the report.

## Report criteria (weights from Guide)

| Criterion | Weight | Location | Final-pass status |
|-----------|--------|----------|-------------------|
| Content correctness and depth | 35% | §7.3 M1–M4 interpretation, metrics, errors | Added scenario-level analysis |
| One section per expert topic | 25% | §§3–7 | Unchanged |
| Difficulties and issues | 15% | §8, §7.4 | Unchanged |
| Structure, clarity, length | 15% | §1, §9, abstract | A4 PDF; see page note |
| Ethics and limitations | 10% | §7.6–7.7 | Unchanged |

## Verified PDF properties (18 Nov 2026 build)

| Property | Result |
|----------|--------|
| Paper size | **A4** — 595.3 × 841.9 pt (measured) |
| Total pages | **11** |
| References | **Page 11** only |
| Appendices | **Page 10** (contribution table + full 12-row SAM; Policy table removed as duplicate of §5 / Topic 3 handover) |
| Margin overflow (span bbox) | None flagged on automated pass |

## Body length (Guide: 7–12 pages)

The Guide does **not** state that the abstract is excluded from the count.

| Definition | Pages (this build) |
|------------|-------------------|
| From title/abstract through §10 AI usage (before appendices) | **1–9** → **9 pages** |
| Excluding only appendices and references | **9 pages** of main matter |
| If evaluator treats abstract+cover as non-body | **~8 pages** (pp. 2–9) |

Both interpretations sit **inside** the 7–12 range.

## AI usage (Topic 3)

`Topic 3 - Handover.md` contains **no AI log**. Report §10 records this and asks **Mina Faltos** to confirm; nothing was invented.

## Voice / tests (unchanged)

Python 3.13, 23/23 tests, voice weights, calm/agitated activity shift, Python 3.14 FunASR limit — §§4, 6.

## Human review still advised

- Topic 3 AI confirmation with Mina Faltos.
- Exact page-count rule your grader uses.
- Co-author sign-off on handover AI logs.