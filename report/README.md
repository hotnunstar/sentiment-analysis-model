# Group report (deliverable)

All report sources live **inside this repository** (not in other folders on disk).

| File | Purpose |
|------|---------|
| `report.md` | Editable source (sections 1–9 + appendices) |
| `group_report.tex` | LaTeX generated from `report.md` (Pandoc) |
| `group_report.pdf` | Compiled group report for Moodle (`report.pdf` in the zip) |

## Rebuild PDF

From the repository root:

```bash
pandoc report/report.md -o report/group_report.tex --standalone \
  --template=report/pandoc-template.tex -V fontsize=11pt
# Output is A4 (see pandoc-template.tex geometry)
cd report && xelatex -interaction=nonstopmode group_report.tex && xelatex -interaction=nonstopmode group_report.tex
```

Copy for the delivery zip:

```bash
cp report/group_report.pdf report/report.pdf
```

## Expert sections

| § | Topic | Expert |
|---|-------|--------|
| 2 | Text perception | Salim Houmaidan (34387) |
| 3 | Affective model + voice | Nuno Araújo (20078) |
| 4 | Decision & robustness | Mina Faltos (34388) |
| 5 | Software & demo | Tomás Rêgo (34083) |
| 6–7 | Evaluation, data, ethics | Tomás Silva (20451); full report assembly |

Handover evidence: `Topic N - Handover*.md` at repository root.