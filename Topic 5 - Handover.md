# Topic 5 — Evaluation, Data, Ethics, and Report Assembly

**Topic owner:** Tomás Silva (20451)

## 1. Responsibility and scope

Topic 5 documents **how the group evaluated** the NovaShop affective engine and assembles the **written project report**. It does **not** own:

- Text or voice model training (Topic 1 — Salim Houmaidan).
- Affective map, Kalman fusion, or voice integration logic (Topic 2 — Nuno Araújo).
- Decision policy or frustration streak rules (Topic 3 — Mina Faltos).
- Harness integration, checker, or Topic 4 tests (Topic 4 — Tomás Rêgo).

Tomás Silva’s work covers: evaluation methodology, interpretation of metrics and scenarios, SAM qualitative checklist, ethics and limitations, report structure and PDF delivery, and cross-checking claims against `engine/results/`, logs, and tests run on **18 November 2026**.

## 2. Evaluation methodology

Three layers are reported in `report/report.md` §7:

1. **EmoBank held-out regression** — text perception quality (`engine/results/text/metrics.json`).
2. **Mandatory scenario action acceptance** — M1–M4 against JSON expectations via `run_scenario.py` / session logs.
3. **Qualitative SAM quadrant checklist** — twelve sampled mandatory turns; not a new multi-rater SAM study.

Practice scenarios P1–P4 inform error analysis only; they are not part of the mandatory pass count.

## 3. Quantitative text results (EmoBank)

Test split after audit: **n = 981**. Metrics use targets in $[-1,1]$:

| Dimension | MAE | Pearson $r$ |
|-----------|-----|-------------|
| Valence | 0.093 | 0.686 |
| Activity | 0.083 | 0.486 |
| Dominance | 0.071 | 0.435 |

**Interpretation:** lower MAE is better; Pearson $r$ measures linear agreement with human EmoBank ratings. Valence is strongest; activity and dominance are noisier from short text. These metrics do not measure whether the correct **support action** was chosen.

## 4. Voice classifier metrics (CREMA-D)

From `engine/results/voice/` (actor-independent held-out test): accuracy **71.80%**, balanced accuracy **72.16%**, macro-F1 **≈ 0.7175**. These are **offline acted-speech** classifier scores, not end-to-end customer-support accuracy.

## 5. Mandatory scenario acceptance (actions)

**Date checked:** 18 November 2026. Logs: `logs/session_20261118_*.txt`. Demo copy: `logs/demo_session.txt` (M2).

| ID | Summary | Action-level result |
|----|---------|---------------------|
| M1 | Calm FAQ; positive close | Met |
| M2 | Escalation path | Met — OFFER_HUMAN, then ESCALATE |
| M3 | Human and authority requests | Met |
| M4 | Clarify; Portuguese close | Met on actions |

Narrative interpretation (strengths and weaknesses per scenario) is in `report/report.md` §7.3.

## 6. SAM checklist (12 mandatory turns)

Low arousal: $|a| < 0.25$; high arousal: $a \geq 0.25$.

**Summary:** 9 full quadrant matches, 2 partial (weak early M2 valence), 1 valence mismatch on sarcasm (policy still uses ASK_CLARIFICATION).

Full turn table: `report/report.md` Appendix C (values taken from the same 18 Nov scenario runs).

## 7. Error analysis (high level)

- Early **M2** turns can look emotionally neutral until explicit frustration wording; policy and streak compensate.
- **M4** sarcasm can yield positive valence while clarification fires.
- **P4** negation under-reacts in regression.
- **Portuguese** close can pass on actions while English-centric text encoders limit affect claims.

## 8. Ethics, privacy, and limitations

- **Local inference**; no cloud requirement for grading demos.
- **Voice WAVs** are sensitive; use kit or licensed CREMA-D clips.
- **Bias:** English EmoBank/DistilBERT; acted CREMA-D; cultural style risks on escalation heuristics.
- **Legal (high level):** OFFER_HUMAN and ESCALATE reflect transparency intent for automated support.
- **Limits:** estimates are not clinical diagnoses; CREMA-D metrics ≠ call-centre ground truth.

Expanded discussion: `report/report.md` §7.6–7.7 and `report/evaluation_compliance.md`.

## 9. Validated environment (group, 18 Nov 2026)

- Python **3.13**, venv `.venv313`
- Text and voice weights installed → `check_project.py` READY
- `python -m unittest discover tests -v` → **23/23 OK** (including voice integration when weights present)
- **Python 3.14:** FunASR Emotion2vec registration failure observed (document as limit)
- **No face channel** implemented

Tests were executed by the group on 18 Nov 2026; this handover was written afterward from logs and result files.

## 10. Report deliverables (Topic 5 assembly)

| File | Role |
|------|------|
| `report/report.md` | Editable academic source |
| `report/report.pdf` | Moodle PDF deliverable |
| `report/pandoc-template.tex` | A4 layout template |
| `report/README.md` | Build instructions |
| `report/evaluation_compliance.md` | Guide mapping |
| `report/revision_summary.md` | Revision log |

Build (from repo root):

```bash
pandoc report/report.md -o report/group_report.tex --standalone \
  --template=report/pandoc-template.tex -V fontsize=11pt
cd report && xelatex -interaction=nonstopmode group_report.tex && xelatex -interaction=nonstopmode group_report.tex
cp group_report.pdf report.pdf
```

## 11. AI assistance and verification

| Use | Verification |
|-----|----------------|
| Structure report vs Evaluation Guide | Compared to course materials and existing handovers |
| Draft/evaluate prose and tables | Cross-checked `metrics.json`, scenario logs, README test commands |
| LaTeX/PDF layout (Pandoc, A4) | Visual page check; page size 595.3×841.9 pt |
| Cursor AI (final report passes) | Co-authors review expert sections; Topic 3 AI log missing in repo — confirm with Mina Faltos |

Students remain responsible for explaining all content at presentation (Evaluation Guide §8).

## 12. What Tomás Silva contributed personally

- Designed and documented the **evaluation framework** (metrics + scenarios + SAM checklist).
- Ran and archived **18 Nov 2026** scenario logs; summarised **action-level** acceptance and **error analysis**.
- Authored **ethics/limitations** and **M1–M4 interpretation** in the group report.
- **Merged and formatted** the full report (all five expert sections attributed to their owners).
- Produced **evaluation_compliance.md**, **revision_summary.md**, and this handover.

Implementation code in `engine/` and expert-specific tests were **not** written solely by Tomás Silva; they are described for system completeness only.