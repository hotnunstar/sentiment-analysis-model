# Report revision summary (final targeted pass)

**Date:** 18 November 2026  
**Files:** `report/report.md`, `report/report.pdf`, `report/pandoc-template.tex`, `evaluation_compliance.md`.

## Changes in this pass

1. **A4 format** — `a4paper` on `article` and `[a4paper,margin=2.4cm]{geometry}` in `pandoc-template.tex`; verified **595.3 × 841.9 pt**.
2. **M1–M4 interpretation** — New §7.3 (~500 words) on strengths/weaknesses per mandatory scenario.
3. **Integration/testing** — One paragraph on FakeEngine vs full suite (Topic 4).
4. **AI table** — Topic 3 row: no AI log in repository; flagged for Mina Faltos; no invented use.
5. **Pagination** — References after appendices; `\footnotesize` on appendices; removed duplicate Policy appendix; SAM fits on page 10; page 11 = references only.
6. **Preserved** — Expert sections, voice/Python 3.13/23 tests, metrics, conclusion, structure.

## Validation (regenerated PDF)

| Check | Outcome |
|-------|---------|
| Total pages | **11** |
| A4 | Yes (595.3 × 841.9 pt) |
| References | Page **11** |
| Appendices + SAM | Page **10** (12 SAM rows; no orphan page) |
| Body (pp. 1–9 before appendices) | **9 pages** (abstract on page 1 included if grader counts it) |
| `waschosen` math glitch | Absent |
| Engine/tests | Not modified |

## Visual inspection

PNGs: regenerate with `report/page_checks/` after each build if needed.

## Deliverable status

Suitable for final human read-through. **Not** claiming automatic full marks—Topic 3 AI log and grader page rules remain for the group to confirm.