---
title: "Affective Computing Project — NovaShop Assistant"
author:
  - "Salim Houmaidan (34387)"
  - "Nuno Araújo (20078)"
  - "Mina Faltos (34388)"
  - "Tomás Rêgo (34083)"
  - "Tomás Silva (20451)"
date: "MIAA 2025/2026 · Project AC — November 2026"
numbersections: true
abstract: |
  Customer-support assistants that answer only keywords miss frustration building over several messages, sarcastic or ambiguous wording, and explicit legal or human-agent requests. We built an offline NovaShop affective engine that estimates valence, activity, dominance, confidence, and a discrete label from text, optionally fuses a voice reading, maintains conversation state, and selects one of six support actions. Text perception uses frozen DistilBERT embeddings and Ridge regression trained on EmoBank; an optional CREMA-D voice channel supplies class probabilities and speaker-invariant prosody. Affective estimates are rescaled and combined with a per-dimension Kalman filter; a deterministic policy maps state and phrase patterns to actions and template replies. On held-out EmoBank text, mean MAE is 0.083 with valence Pearson $r = 0.686$ on $n = 981$ test sentences. With Python 3.13, all 23 automated tests pass, including voice integration; the voice channel is demonstrated with held-out CREMA-D speech clips; mandatory scenarios M1–M4 meet action-level acceptance criteria, while qualitative SAM checks reveal partial weaknesses on early frustration and sarcastic valence. Processing is local; limitations include English-centric training, acted voice data, and emotion estimates that are not ground truth.
---

# Introduction

## Background and motivation

Affective computing studies how machines can infer and respond to human emotional state. In customer support, tone and trajectory matter: a calm FAQ differs from a conversation that escalates from a late delivery to a legal threat. The course couples this idea with the Self-Assessment Manikin (SAM): valence (pleasantness), activity (arousal), and optionally dominance (control), displayed on a shared affective map.

## Problem statement

Keyword-only bots cannot track worsening frustration across turns, hesitate on short replies such as “ok”, or prioritise explicit requests to speak to a human or mention consumer protection. A practical engine must estimate affect per message, smooth estimates over time, expose calibrated confidence, and choose among six contract actions while remaining reproducible for grading.

## Project objectives

The NovaShop engine shall: (1) perceive emotion from text (mandatory); (2) optionally integrate voice; (3) maintain state across turns; (4) return valence, activity, dominance, confidence, label, action, and reply; (5) behave robustly on ambiguous, sarcastic, and Portuguese input. No face channel is implemented.

## Scope and limitations of claims

Affect labels are **computational estimates** for adaptive support, not clinical or legal diagnoses. Reported correlations are against EmoBank human ratings, not new SAM studies on NovaShop wording.

## Report organisation

Section 2 presents architecture and scenarios. Sections 3–7 follow expert topics 1–5. Section 8 discusses challenges; Section 9 concludes. Section 10 documents AI use. Appendices hold extended tables and contribution detail.

## Expert responsibilities

| Topic | Expert | Focus |
|:-----:|--------|--------|
| 1 | Salim Houmaidan (34387) | Text and voice classifiers |
| 2 | Nuno Araújo (20078) | Map, Kalman state, voice fusion |
| 3 | Mina Faltos (34388) | Decision policy and robustness |
| 4 | Tomás Rêgo (34083) | Harness integration, tests, demo |
| 5 | Tomás Silva (20451) | Evaluation, data, ethics, report |

Handover notes in the repository root (`Topic N - Handover*.md`) support each section.

# System architecture and methodology

## NovaShop scenarios

All groups use mandatory scenarios **M1–M4**: calm FAQ (M1), escalating frustration (M2), explicit human/legal requests (M3), and ambiguity, sarcasm, negation, and Portuguese close (M4). Practice scenarios P1–P4 extend testing. The harness and JSON files are unchanged; only `engine/` is group code.

## Processing pipeline

The following sequence links components without repeating per-expert implementation lists:

1. **Customer input:** text and optional WAV.
2. **Text perception (Topic 1):** DistilBERT embedding and Ridge regression produce raw valence, activity, dominance; a surface sarcasm flag may be set.
3. **Optional voice (Topics 1–2):** emotion2vec features and a CREMA-D classifier yield class probabilities; prosody estimates activity; noise reduces voice weight.
4. **Affective state (Topic 2):** rescaling to the map, label, confidence, and a **Kalman filter** per dimension over the conversation.
5. **Decision policy (Topic 3):** deterministic rules select one of six actions and a template reply.
6. **Interface:** contract normalisation, GUI or scenario runner, session log.

Stateful filtering matters for M2: early turns can look emotionally weak while explicit frustration language later triggers `OFFER_HUMAN` via both affect and a **frustration streak** counter.

## Integration contract

The public `Engine` returns one dictionary per turn. Numeric fields are clipped to kit ranges; the harness records contract violations instead of crashing the GUI. Optional `image_path` is accepted for compatibility but unused; there is no implemented face channel. This separation lets Topics 1–3 evolve internal models while Topic 4 and the scenario runner depend only on stable field names.

## Actions and contract

The kit defines six support actions. The harness validates names and numeric ranges before display or logging.

| Action | Typical use |
|--------|-------------|
| ANSWER | Neutral FAQ or factual reply |
| ANSWER_EMPATHIC | Mild negative affect without escalation trigger |
| ASK_CLARIFICATION | Sarcasm flag, ambiguity, or low confidence |
| OFFER_HUMAN | Explicit human or refund request; frustration streak |
| ESCALATE | Legal or regulatory wording (EN/PT) |
| CLOSE_POSITIVE | Resolved conversation without open questions |

# Text perception — Expert Topic 1 (Salim Houmaidan, 34387)

## Method

Short customer messages need contextual representations, not hand-tuned lexicons alone. We freeze **DistilBERT** (`distilbert-base-uncased`), pool embeddings to 768 dimensions, and train **Ridge regression** on **EmoBank** sentences. Human valence, activity, and dominance scores on the 1–5 EmoBank scale are mapped to the interval $[-1, 1]$ using $(\mathrm{score} - 3) / 2$. Ridge regularisation with $\alpha = 100$ was selected on the development split by minimising mean MAE across the three targets.

EmoBank splits after removing 44 cross-split duplicate strings: 8062 train, 975 dev, and 981 test (`engine/results/text/data_audit.json`). Freezing the encoder limits overfitting on modest-sized emotion corpora while keeping sentence context.

## Sarcasm and negation

Negation and emphasis are learned from embeddings. The only hand-written text rule is **`possible_sarcasm`**: praise plus complaint cues (e.g. “Great” and “delay”) without changing regression scores; Topic 3 may request clarification.

## Results and interpretation

| Dimension | MAE | Pearson $r$ |
|-----------|-----|-------------|
| Valence | 0.093 | 0.686 |
| Activity | 0.083 | 0.486 |
| Dominance | 0.071 | 0.435 |

MAE measures average absolute error on the normalised scale; smaller is better. Pearson $r$ measures linear association with human EmoBank ratings. Valence is predicted most reliably; activity and dominance are noisier from text alone, which matches intuition about short support messages. These metrics do not directly measure whether the correct **support action** was chosen.

## Optional voice classifier (Topic 1, integrated by Topic 2)

For bonus voice points, Salim trained a **CREMA-D** emotion classifier: frozen **emotion2vec** utterance embeddings and logistic regression (actor-independent split). Held-out test metrics: accuracy **71.80%**, balanced accuracy **72.16%**, macro-F1 **0.7175**, on acted speech, not live call-centre audio.

# Affective model and multimodal integration — Expert Topic 2 (Nuno Araújo, 20078)

## Map, labels, and SAM

Raw Ridge outputs occupy a narrow band. Each axis is divided by the 99th percentile of held-out predictions (scale factors $\approx 0.30$, $0.20$, and $0.14$ for valence, activity, and dominance), then clipped for display. This aligns sparse model outputs with the SAM-style interface without tuning thresholds on NovaShop text.

Six labels (`neutral`, `calm`, `joy`, `anger`, `frustration`, `sadness`) use thresholds expressed as multiples of measured error. **Confidence** is a calibrated label probability (not distance from origin), so clear neutral messages can exceed the policy threshold $0.40$ when appropriate.

## Conversation state

A one-dimensional **Kalman filter** runs per dimension: process noise allows affect to change; measurement noise grows for short or flagged sarcastic text. **Unclipped** internal state prevents a single extreme complaint from being forgotten on the next turn; this matters when raw valence on M2’s opening lines stays near neutral until explicit frustration phrases appear.

Consider M2 turn by turn: a polite delay question may measure $v \approx -0.03$, which looks almost neutral in isolation. After “three days late” the measurement remains weak, but the filter retains negative momentum. Once the customer writes “really frustrating,” $v$ drops sharply and activity rises; the policy then offers a human agent. Without temporal smoothing, a support system might treat each message as a fresh FAQ and miss escalation risk.

## Voice fusion

With voice weights installed under the encoder directory (`engine/models/voice/encoder/`), voice adds a second measurement: classifier-derived valence and dominance (via NRC VAD emotion anchors), prosodic activity without absolute pitch (mitigating speaker bias), and spectral-flatness noise penalties. When audio cannot be processed, the engine sets a failure flag, keeps the text-only estimate, and does not crash the session.

On Python **3.13** (README-recommended), voice processing status is **processed** when weights are installed. Two kinds of audio are used:

- **Synthetic teaching tones** (`assets/audio/calm_clean.wav`, `agitated_clean.wav`, noise and speaker variants) support automated tests of prosody, noise penalties, and speaker invariance. They are **not** human speech: the voice stack (emotion2vec and the CREMA-D classifier) was trained on **acted human utterances**, so synthetic sine-like or tone-burst WAVs are **out-of-domain**. Attaching `calm_clean.wav` to neutral text can still place the map in a negative, low-activity quadrant (e.g. valence $\approx -0.18$, activity $\approx -0.16$) even though the filename says “calm”. **Reset session** clears Kalman state and frustration counters but **does not** correct this acoustic domain mismatch; only a new turn with different audio or text changes the measurement. Under identical neutral text, clean calm versus agitated kit tones can still shift fused **activity** (about $-0.13$ to $+0.11$, 18 Nov 2026), which is useful for engineering checks, but quadrant labels must not be read as validated human emotions. For that reason these files are **not** used as categorical emotion demos in the video.
- **Held-out CREMA-D speech** in `assets/audio/demo_emotions/` supplies real acted categories for the **video demonstration** (Topic 4, 21 Nov 2026). Files are hash-verified against `engine/data/voice/manifest.json`.

On Python 3.14 we observed FunASR failing to register Emotion2vec. Document this as an environment limitation, not a missing weight.

# Decision-making and robustness — Expert Topic 3 (Mina Faltos, 34388)

## Rationale

Learned affect is noisy; **deterministic policy rules** encode business priorities: legal escalation and human/refund requests precede affect scores. An 11-step priority chain in `engine/engine.py` implements this (documented in the Topic 3 handover).

## Illustrative behaviour

**M2 (18 Nov 2026):** turns 1–2 show weak negative valence but empathic replies; turn 3 (“really frustrating”) yields `OFFER_HUMAN`; lawyer threat ends with `ESCALATE`. **M3:** return FAQ answered; human-agent phrase triggers `OFFER_HUMAN`; consumer authority triggers `ESCALATE` despite mild valence.

**Frustration streak:** explicit delay or frustration language, or confident frustration/anger labels, increment a counter; from three consecutive qualifying turns, `OFFER_HUMAN` fires even when perception lags.

Replies use keyword FAQ templates in English and Portuguese; no large language model.

Policy design is intentionally **explainable**: graders and customers can trace why `ESCALATE` fired from phrase lists and priority order, unlike a black-box ranker. That transparency trades some nuance for reproducibility on the fixed M1–M4 scripts.

# Software integration, testing, and demonstration — Expert Topic 4 (Tomás Rêgo, 34083)

Tomás Rêgo integrated Topics 1–3 with the official kit without changing model weights or policy thresholds. Integration follows the shared path: scenario runner or GUI loads the public `Engine`, calls `reset()` and `process(text, audio_path, image_path)`, then normalises output through the harness contract and session logger.

`check_project.py` reports Python version, dependencies, and whether text and voice weight files are present; text and voice readiness are listed separately so a missing voice checkpoint does not falsely mark the mandatory text channel as broken. `tests/test_topic4.py` uses a lightweight **FakeEngine** with the same public API to verify contract clipping, session logs, scenario file presence, and README instructions: eight tests that run quickly without loading neural models.

With dependencies and weights installed, the full suite (`python -m unittest discover tests -v`) exercises engine contract tests, Topic 4 harness tests, voice preprocessing tests, and voice integration tests that call the real encoder. Splitting **FakeEngine** harness tests from heavyweight model tests is deliberate: integration and logging failures surface in seconds, while perception tests run only when weights are present.

**Validated environments:** on 18 Nov 2026 (Python **3.13**, `.venv313`) the suite reached **23/23** with voice weights installed. On **21 Nov 2026**, Tomás Rêgo re-ran `check_project.py` with text and voice **[READY]** and reported **23 tests passed, 0 skipped** (3 contract, 8 Topic 4, 12 voice/acoustic), with both large encoder weights present (`Topic 4 - Handover.md`).

The demonstration order follows `TOPIC_4_VIDEO_SCRIPT.md`: checker → full tests → GUI with **reset between each** mandatory scenario (M1–M4, so Kalman state and frustration streak do not leak) → exported session log → optional **voice with sound files**. Large weights ship in the offline zip, not Git.

## Voice demonstration with sound (Topic 4)

The optional channel is demonstrated in the five-minute video with **neutral text** and a user-selected WAV:

> Here is my message.

Held-out CREMA-D clips live in `assets/audio/demo_emotions/` (seven files, six emotion classes; ODbL). Example outcomes documented in the repository README:

```{=latex}
\medskip
\begingroup\footnotesize
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\linewidth}{@{}>{\RaggedRight\arraybackslash\hsize=0.95\hsize}X >{\RaggedRight\arraybackslash\hsize=0.55\hsize}X >{\RaggedRight\arraybackslash\hsize=1.25\hsize}X >{\RaggedRight\arraybackslash\hsize=0.75\hsize}X@{}}
\toprule
\textbf{Audio file} & \textbf{Classifier} & \textbf{Fused label (illustrative)} & \textbf{Action} \\
\midrule
\nolinkurl{1013_WSI_ANG_XX.wav} & anger & neutral (text dominates); voice reads anger & \textbf{ANSWER\_EMPATHIC} \\
\nolinkurl{1020_DFA_HAP_XX.wav} & happiness & calm & ANSWER \\
\nolinkurl{1065_ITS_NEU_XX.wav} & neutral & neutral & ANSWER \\
\bottomrule
\end{tabularx}
\endgroup
```

These runs show why the report separates **classifier category**, **voice-only VAD label** (`details.voice.voice_only.label`), **fused top-level label**, and **final action**: anger in the voice can raise activity and change policy even when the typed words are neutral. Happiness may map to a calm fused quadrant while the classifier still reports happiness. Failed audio processing leaves the text-only result unchanged (`voice` failure flag).

The GUI and session logs record audio paths, voice diagnostics, and latency so evaluators can reproduce the demonstration offline. Synthetic kit WAVs remain for **engineering tests** only; **CREMA-D demo_emotions** clips are the **presented speech evidence** for integrated voice. If a demonstration accidentally uses kit synthetic audio, the group should explain that the map can look “wrong” relative to everyday calm/angry speech because the models expect human acting, not classroom tones.

## Reproducibility checklist

For grading, the group documented a fixed order: create Python 3.13 virtual environment, install `requirements.txt`, place text and voice weights at README paths, run `check_project.py`, run the full unit-test suite, execute M1–M4 with `run_scenario.py`, and archive `logs/session_*.txt`. The same sequence appears in the README and Topic 4 handover; deviations (e.g. Python 3.14 without voice registration) are recorded as environment limits rather than hidden failures.

# Experimental evaluation, ethics, and limitations — Expert Topic 5 (Tomás Silva, 20451)

## Methodology

Evaluation combines three layers: (1) **EmoBank benchmark metrics** for text regression quality; (2) **mandatory scenario action acceptance** against JSON expectations on turns M1–M4; (3) a **qualitative SAM quadrant checklist** on twelve sampled mandatory turns (not a multi-rater SAM laboratory study on kit text). Low arousal is $|a| < 0.25$; high arousal is $a \geq 0.25$. Practice scenarios P1–P4 add refund, disappointment, anxiety, and negation cases; they inform error analysis but are not part of the mandatory pass/fail count.

## Scenario acceptance (actions)

| ID | Expected (summary) | Outcome (18 Nov 2026) |
|----|-------------------|------------------------|
| M1 | Calm FAQ; positive close | Met: CLOSE_POSITIVE on thanks |
| M2 | Escalation path | Met: OFFER_HUMAN, then ESCALATE |
| M3 | Human and authority | Met: OFFER_HUMAN, ESCALATE |
| M4 | Clarify; PT close | Met on actions: ASK_CLARIFICATION; PT CLOSE_POSITIVE |

Logs: `logs/session_20261118_*.txt` (mandatory scenarios, 18 Nov 2026). The delivery video exports a fresh session log to `logs/demo_session.txt` per Topic 4 instructions. Passing here means each turn’s **action** matched the scenario file; it does not require perfect valence on every turn.

## Interpretation of mandatory scenarios (M1–M4)

Read together, the four mandatory scripts show what the integrated engine is good at and where perception alone would fail grading criteria.

**M1 (calm FAQ)** exercises the baseline path: neutral or mildly positive text should receive informative `ANSWER` replies, and a polite closing thanks should end with `CLOSE_POSITIVE`. The run confirms that low-arousal FAQ language does not spuriously escalate. SAM samples on the opening FAQ and final thanks align with expected quadrants (Appendix C), so M1 supports both **action correctness** and reasonable affect display for straightforward service.

**M2 (escalating frustration)** is the critical stress test for **state and policy**. Text regression often leaves valence near neutral on the first delay complaints; Kalman state and the frustration streak nonetheless allow `ANSWER_EMPATHIC` early and `OFFER_HUMAN` once frustration language accumulates. The legal threat at the end correctly yields `ESCALATE` even though the scenario is scripted. M2 therefore demonstrates the design intent of Topic 3: business rules and multi-turn counters compensate when early affect estimates under-react. The partial SAM matches on turns 1–2 are weaknesses in **displayed emotion**, not in required actions.

**M3 (explicit human and authority requests)** shows **intent precedence** over classifiers. Return-policy FAQ text is answered factually; phrases requesting a human agent trigger `OFFER_HUMAN` without requiring extreme negative valence, and consumer-authority wording triggers `ESCALATE`. This behaviour matches customer-protection expectations better than a pure emotion classifier would. It also explains why action-level pass rates can be high while EmoBank MAE remains imperfect on short administrative sentences.

**M4 (ambiguity, sarcasm, negation, Portuguese)** tests **robustness** rather than benchmark accuracy. The single-word `ok` turn appropriately asks for clarification rather than guessing intent. Sarcastic praise about a delay is misread in valence (positive $v$) but still receives `ASK_CLARIFICATION` via the sarcasm flag, an example where policy mitigates a perception error. The Portuguese closing turn achieves the expected positive close action, but text encoders trained mainly on English should not be interpreted as strong evidence of multilingual affect understanding.

Across M1–M4, the system’s strength is **reliable routing** under the kit contract; its weakness is **fine-grained emotional truth** on sarcasm, weak opening frustration, and some negation patterns (see practice scenario P4).

## SAM checklist (qualitative)

Of twelve sampled mandatory turns: **9** full quadrant agreement, **2** partial (weak valence on early M2 opening lines), **1** valence mismatch on sarcasm (policy still selects clarification). Full turn-by-turn values are in Appendix C.

## Error analysis

Early M2 valence stays near neutral until explicit frustration wording; policy and streak compensate. M4 sarcasm can show positive valence while `ASK_CLARIFICATION` fires. P4 negation (“not happy at all”) under-reacts in regression. English DistilBERT limits Portuguese affect claims despite successful **actions** on the Portuguese close.

## Ethics, bias, and legal context

**Privacy and data handling.** Inference runs locally; training artefacts are offline. Runtime logs should contain fictional scenario text only, not real customer transcripts. Voice WAVs are biometric-sensitive; course demos should use kit audio or CREMA-D clips under ODbL.

**Bias and fairness.** DistilBERT and EmoBank are predominantly English; Portuguese in M4 is only lightly supported at the text level. Anger and escalation heuristics may misread direct or informal cultural styles. CREMA-D voice is acted, gendered, and accent-biased; prosody design deliberately avoids absolute pitch for that reason.

**Transparency and law (high level).** EU consumer-facing automation increasingly expects clarity about bots and human escalation. `OFFER_HUMAN` and `ESCALATE` implement that design intent in the policy layer. The system must not be presented as a clinical or legal emotion diagnostic.

## Limitations

The engine cannot guarantee correct behaviour on hidden examiner messages, reliably detect irony on every phrasing, or replace humans in safety-critical contexts. CREMA-D metrics do not certify end-to-end call-centre accuracy. Scenario success, benchmark MAE, and SAM quadrant checks measure different things and should be reported together honestly.

## Practice scenarios (P1–P4)

| ID | Focus | Representative outcome |
|----|-------|-------------------------|
| P1 | Neutral refund FAQ | ANSWER; mild positive $v$ |
| P2 | Disappointment | Empathic reply; may offer human on sustained negativity |
| P3 | Anxiety | Empathic support; higher activity on fear-like wording |
| P4 | Explicit negation | ANSWER but weak negative valence on “not happy” |

These runs informed the error-analysis notes above; only M1–M4 determine mandatory action acceptance.

## Optional voice channel (evaluation summary)

Offline CREMA-D classifier metrics (§3.4) measure acted speech in isolation. The **integrated** channel is evidenced by: (1) **23/23** tests including voice fusion and failure safety; (2) **processed** voice status with weights on Python 3.13; (3) **demo_emotions** runs under fixed neutral text, showing classifier output, fused state, and policy change (e.g. anger → empathic reply); (4) limitations: acted actors, English-centric text, **synthetic kit WAVs misaligned with human-speech training** (misleading map even after reset), and cases where fused label stays neutral while voice-only sub-fields show emotion. This satisfies the Evaluation Guide expectation that optional voice be integrated, demonstrated, tested, documented with limits, and explainable to the group.

# Challenges and lessons learned

Compressed regression outputs required map rescaling and Kalman tracking instead of trusting raw scores alone. Calibrated confidence was necessary so Topic 3 could use a $0.40$ threshold meaningfully. Integrating voice demanded large checkpoints, Python 3.13 for FunASR registration, and honest separation of **processed audio** from improved customer outcomes. Sarcasm and negation remain the dominant text failure modes; the policy’s clarification and streak rules are deliberate compensations, not fixes to perception. Coordinating five topics relied on handover documents and fixed scenario checklists. Cross-platform model fingerprints were needed so the same bundle runs on Windows and macOS.

# Conclusion and future work

We set out to build a reproducible affect-aware NovaShop engine that respects the kit contract, tracks conversation state, and selects among six actions using text and optional voice. The implemented pipeline (DistilBERT and Ridge text estimation, optional CREMA-D voice fusion, Kalman affective state, and a transparent policy) meets **action-level** acceptance on M1–M4 and passes **23/23** automated tests under Python 3.13 with voice weights installed. EmoBank correlations show moderate agreement for valence and weaker agreement for activity and dominance, which explains remaining perceptual weaknesses on sarcasm, negation, and weak opening frustration.

The decision layer deliberately compensates for perception: explicit legal and human-agent phrases, frustration streaks, and clarification on sarcasm flags stabilise behaviour even when valence is imperfect. This is appropriate for a support assistant but must not be mistaken for accurate emotion reading.

Future work could include stronger sarcasm and negation modelling, multilingual text encoders, customer-service domain evaluation, SAM studies on kit messages with ethics approval, and broader deployment testing across Python versions. The project demonstrates that **affect-aware routing** is feasible offline when estimation, state, and policy are engineered together, and that honest evaluation must separate **scenario success**, **benchmark metrics**, and **emotional ground truth**.

# AI usage and contributions

Per Evaluation Guide §8, AI tools were permitted when work was verified and explainable. The table below summarises documented use; expert-specific prompts appear in Topic handover files.

| Area | AI assistance | Student verification |
|------|---------------|----------------------|
| Topic 1 (text/voice) | ChatGPT for setup, classifier comparison, and test phrasing | Held-out metrics in `engine/results/`; manual WAV checks (see Topic 1 handovers) |
| Topic 2 (affective model) | Claude via Claude Code for design options and drafts | Reproducibility commands and tests in Topic 2 handovers |
| Topic 3 (decision policy) | Gemini / LLM assisted in reviewing Topic 3 decision policy edge cases, bilingual EN/PT regex coverage, and handover documentation structure draft | All rules in `engine/engine.py` were manually reviewed, tested against mandatory scenarios M1–M4, and verified with the automated contract, voice, and edge-case test suites |
| Topic 4 (integration, voice demo assets) | AI review of brief, checker, Topic 4 tests, demo script; CREMA-D clip packaging | `tests/test_topic4.py`; 21 Nov 2026 full suite; `assets/audio/demo_emotions/` README |
| Topic 5 / report | Editor assistance for structure, tables, and LaTeX/PDF build | Cross-check against `metrics.json`, 18 Nov scenario logs, 23/23 tests on Python 3.13 |
| Report merge (Tomás Silva) | Cursor AI for academic rewrite and layout fixes | Visual PDF review; figures unchanged from result files |

**Needs human confirmation:** exact Cursor prompt history for the final report pass is not archived in the repository; each co-author should confirm their handover AI log before presentation (especially Topic 3).

\appendix

```{=latex}
\begingroup\footnotesize
```

# Contribution statement

| Member | No. | Topic | Report sections |
|--------|-----|-------|-----------------|
| Salim Houmaidan | 34387 | 1 | §3 |
| Nuno Araújo | 20078 | 2 | §4 |
| Mina Faltos | 34388 | 3 | §5 |
| Tomás Rêgo | 34083 | 4 | §6 |
| Tomás Silva | 20451 | 5 | §7–10, assembly |

# SAM checklist (12 mandatory turns)

Low arousal: $|a| < 0.25$; high arousal: $a \geq 0.25$. †Sarcasm valence mismatch; policy clarifies.

```{=latex}
\enlargethispage{10\baselineskip}
```

| Sc. | Turn | Expected SAM | $v$ / $a$ | Match |
|-----|------|--------------|-----------|-------|
| M1 | Delivery FAQ | Neutral+, low arousal | $+0.03$ / $+0.09$ | Yes |
| M1 | Final thanks | Positive, higher arousal | $+0.57$ / $+0.84$ | Yes |
| M2 | Order late | Negative, moderate | $-0.03$ / $+0.10$ | Partial |
| M2 | Three days late | More negative | $-0.03$ / $+0.12$ | Partial |
| M2 | “Really frustrating” | Negative, higher arousal | $-0.44$ / $+0.44$ | Yes |
| M2 | Money back | Very negative, high arousal | $-0.59$ / $+1.00$ | Yes |
| M2 | Lawyer threat | Very negative, high arousal | $-0.70$ / $+1.00$ | Yes |
| M3 | Return FAQ | Neutral | $+0.18$ / $+0.05$ | Yes |
| M4 | `ok` | Uncertain | $+0.10$ / $+0.03$ | Yes |
| M4 | Sarcastic delay | Negative valence | $+0.11$ / $+0.47$ | No† |
| M4 | Not bad, thanks | Mildly positive | $+0.14$ / $+0.21$ | Yes |
| M4 | Portuguese close | Positive, calm | $+0.21$ / $+0.14$ | Yes |

```{=latex}
\endgroup
\clearpage
\section*{References}
```

1. Project Brief and Evaluation Guide, MIAA Affective Computing, 2026 (course materials).  
2. Buechel, S., & Hahn, U. (2017). EmoBank. *ACL Workshop on Subjectivity, Sentiment and Social Media Analysis*.  
3. Bradley, M. M., & Lang, P. J. (1994). Self-Assessment Manikin. *J. Behavior Therapy and Experimental Psychiatry*.  
4. Russell, J. A. (1980). Circumplex model of affect. *JPSP*.  
5. Sanh, V., et al. (2019). DistilBERT, a distilled version of BERT. *arXiv:1910.01108*.  
6. CREMA-D (ODbL): CheyneyComputerScience/CREMA-D.
