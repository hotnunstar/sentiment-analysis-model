# Topic 2 — Affective Model, Map and Channels (Voice)
## Group reference document — design, decisions, evidence and limitations

This document describes how Topic 2 turns a recording into a point on the affective map and integrates it with the text estimate. Every number comes from code in `engine/` and can be reproduced with the commands in section 12. The text side is described in `Topic 2 - Handover (Text).md`.

---

## 1. Goal and requirements

The Evaluation Guide (section 7) gives up to +2 points for a voice channel that is:

| Requirement | How it is met |
|---|---|
| Integrated with the text estimate | Voice is a second measurement of the same message in the Kalman state (section 9); one fused valence/activity/dominance, label and confidence per message |
| Shown working in the video | Attach a WAV in the interface; the fused point moves and the voice-only reading appears in the session log (section 10) |
| Tested | `tests/test_voice.py`, 12 tests (section 11) |
| Limits documented (speaker, noise) | Measured and handled (sections 7 and 8); remaining limits in section 13 |
| Must not break the text engine | A voice failure keeps the text result and adds a flag; text-only messages are unchanged (section 11) |

The Project Brief assigns the voice channel to Topic 2, including the concepts framing, windowing, spectrum, MFCC and pitch (section 4).

---

## 2. Files

| File | Content |
|---|---|
| `engine/acoustic_features.py` | Framing, windowing, power spectrum, mel filterbank, MFCC, pitch, loudness, spectral flatness — written from scratch with numpy |
| `engine/voice_affect.py` | Voice reading on the map: emotion probabilities → valence/dominance, prosody → activity; noise factors |
| `engine/affective_state.py` | Fusion: the voice measurement step, failure safety, confidence penalty for noise |
| `engine/train_voice_prosody.py` | Trains the prosodic activity estimator (and two comparison variants) |
| `engine/extract_acoustic_features.py` | Computes the acoustic features for every CREMA-D clip |
| `engine/calibrate_voice.py` | Measures the voice scale and error (dev actors) and evaluates on test actors |
| `engine/calibrate_voice_noise.py` | Noise experiment: adds noise at known SNRs and measures error growth |
| `engine/models/voice/prosody_activity.joblib` | Prosodic activity model |
| `engine/data/voice/acoustic_features.csv` | Cached acoustic features (7,442 clips) |
| `engine/results/voice/` | `prosody_metrics.json`, `noise_experiment.csv` and the classifier's dev/test predictions |
| `tests/test_voice.py` | Voice tests |

Input from Topic 1: the emotion classifier (`engine/voice_estimator.py`, frozen emotion2vec_base + logistic regression on CREMA-D), described in the Topic 1 documentation.

---

## 3. Pipeline

```
recording (WAV, any rate) -> 16 kHz mono
   |-- emotion2vec + classifier -> 6 emotion probabilities -> NRC VAD reference -> valence, dominance
   |-- acoustic features (sec. 4) -> prosodic model (sec. 7)                     -> activity
   |-- spectral flatness (sec. 8)                                                 -> noise factor
   -> rescale to the voice channel's range (sec. 6)
   -> Kalman update of the conversation state, after the text update of the same message (sec. 9)
```

Data: CREMA-D (7,442 acted English clips, 91 actors, 6 emotions; Open Database License). Actor-independent split from Topic 1: 63 train / 14 dev / 14 test actors (5,152 / 1,148 / 1,142 clips). All Topic 2 constants are measured on **dev** actors; **test** actors are only used for final evaluation.

---

## 4. Acoustic features (course concepts)

Implemented in `acoustic_features.py` following the course pipeline:

| Step | Implementation |
|---|---|
| Framing | 25 ms frames every 10 ms (400 samples, step 160 at 16 kHz); the signal is assumed stationary inside a frame |
| Windowing | Hamming window, so each frame goes to zero at its edges before the FFT |
| Spectrum | 512-point FFT → 257 bins; periodogram \|X(k)\|² / N |
| Mel filterbank | 26 triangular filters from 300 Hz to 8 kHz, equally spaced on the mel scale M(f) = 1125·ln(1 + f/700) |
| MFCC | log of the filter energies, DCT, keep coefficients 2–13 |
| Pitch (F0) | Autocorrelation peak per 40 ms frame, 60–400 Hz; a frame is voiced when the normalised peak ≥ 0.5 |
| Loudness | Frame energy in dB; utterance loudness = 95th percentile |
| Pitch movement | Spread of the voiced pitch in semitones (12·log2(f/median)), measured robustly (median absolute deviation) |
| Spectral flatness | Geometric / arithmetic mean of the spectrum: ≈ 0 for harmonic voice, high for noise |

**Validation against librosa:** MFCCs correlate 0.95–0.97 with librosa on real CREMA-D speech; pitch matches librosa's pYIN within 1–2%. The mel formula reproduces the course values (300 Hz → 401.25 mel, 4000 Hz → 2142.27 mel).

**Octave errors:** autocorrelation sometimes jumps an octave on single frames (17 of 43 voiced frames in one sad clip). A plain standard deviation gave 6.1 semitones of pitch movement for that clip; the robust spread gives 1.6, so pitch movement uses the robust measure.

---

## 5. From emotion probabilities to valence and dominance

The classifier outputs probabilities for anger, disgust, fear, happiness, neutral and sadness. Each emotion is given a reference point from the **NRC VAD Lexicon** (Mohammad, ACL 2018; ~20,000 English words rated by people), using the score of the **emotion's own name**, converted from 0..1 to −1..1:

| Emotion | Valence | Arousal | Dominance |
|---|---|---|---|
| anger | −0.67 | +0.73 | +0.31 |
| disgust | −0.90 | +0.55 | −0.37 |
| fear | −0.85 | +0.68 | −0.41 |
| happiness | +0.92 | +0.46 | +0.70 |
| neutral | −0.06 | −0.63 | −0.29 |
| sadness | −0.90 | −0.42 | −0.67 |

The voice reading is the **probability-weighted average** of these points.

- **Why a lexicon:** CREMA-D has only categorical labels; a published human-rated lexicon gives citable, checkable values instead of hand-picked numbers.
- **Why the emotion names only:** choosing synonyms would be a subjective selection.
- The lexicon file is not committed (redistribution terms unclear); only these six values are used, with the citation.

---

## 6. Voice scale and measured error

Same principle as the text map: each dimension is divided by the 99th percentile of the channel's own readings, so ±1 means "the top 1% of voice readings" (scale 0.895 for valence, 0.664 for dominance; 0.852 for prosodic activity).

"Truth" for a clip is the reference point of its intended emotion. Measured error on dev actors (RMSE, rescaled):

| Error σ (lower is better) | Valence | Activity | Dominance |
|---|---|---|---|
| Text (held-out EmoBank) | **0.42** | 0.54 | 0.66 |
| Voice (dev actors) | 0.57 | 0.56 (prosody) | **0.53** |

Voice errors are roughly Gaussian (74% within 1σ) with heavier tails (92–93% within 2σ instead of 95%): a misclassified emotion moves the point far.

On test actors, the emotion2vec readings correlate 0.75 (valence), 0.79 (activity), 0.79 (dominance) with the reference values. These are not directly comparable with text: the truth is a category reference, not human ratings, and the speech is acted.

---

## 7. Activity and the speaker problem

### Finding

emotion2vec's activity reading depends on the speaker's natural pitch. Across the 28 held-out actors, the correlation between an actor's median pitch and the mean error of their readings is:

| Speaker bias (0 = none) | Valence | Activity | Dominance |
|---|---|---|---|
| emotion2vec | −0.22 | **+0.59** | +0.26 |
| Prosodic estimator (below) | — | **+0.03** | — |

Higher-pitched speakers get their activity overestimated — the problem targeted by the course audio files `speaker_high` / `speaker_low` (same calm tone at 260 Hz and 90 Hz).

### Prosodic activity estimator

Ridge regression on speaker-invariant prosody: loudness, loudness variation, pitch movement (semitones), pitch range (semitones) and voiced share. **Absolute pitch is never an input.** Target: reference activity of the intended emotion; α chosen on dev actors (α = 100).

| Variant | Pearson dev / test | Speaker bias | Error overlap with emotion2vec |
|---|---|---|---|
| **Speaker-invariant (used)** | 0.44 / 0.50 | **+0.03** | +0.72 |
| + absolute pitch | 0.48 / 0.52 | +0.38 | +0.73 |
| + MFCCs | 0.45 / 0.52 | +0.29 | +0.73 |

Adding absolute pitch or MFCCs (which carry voice identity) gains at most 0.02 in correlation but introduces speaker bias.

### Decision

**Activity comes from prosody; valence and dominance from emotion2vec.** Each estimator is used for what it is good at, the activity estimate is fair across speakers and explainable with course concepts. Cost: lower activity accuracy on acted CREMA-D (0.50 vs 0.79). Combining both activity readings was rejected because their errors overlap strongly (+0.72): treating them as independent would count the same evidence twice, and an optimal correlated combination would keep about two thirds of the speaker bias.

---

## 8. Noise

### Experiment

300 dev clips (50 per emotion), white noise added at 20, 10, 5 and 0 dB SNR (fixed seed). Error variance relative to clean audio:

| SNR | Valence | Activity (prosody) | Dominance | Median spectral flatness |
|---|---|---|---|---|
| clean | 1.00 | 1.00 | 1.00 | 0.008 |
| 20 dB | 1.38 | 1.01 | 1.70 | 0.065 |
| 10 dB | 2.06 | 1.01 | 2.86 | 0.293 |
| 5 dB | 2.36 | 1.03 | 3.46 | 0.438 |
| 0 dB | 2.53 | 1.08 | 4.11 | 0.510 |

Noise strongly degrades emotion2vec; prosodic activity is almost unaffected (a further argument for section 7).

### Detecting noise at runtime

Spectral flatness rises steadily with noise and separates clean from noisy audio: 95% of clean clips stay below 0.018 while 95% of 20 dB clips are above 0.026. The usual energy-range SNR estimate (loud parts vs pauses) fails on continuous sounds such as the course's noisy files (≈ 3 dB everywhere), while flatness detects them (0.16–0.21 vs 0.00).

### Effect

1. **Weight:** the measured flatness is converted into the factors above by interpolation; they multiply the voice measurement noise, so noisy audio moves the state less (valence weight 0.28 → 0.18 on the course's noisy file).
2. **Confidence (rule-based):** confidence is multiplied by 1/√(mean noise factor). Without it, confidence rose on noisy audio, because the state stayed closer to the (neutral) text and "neutral" became more probable — mathematically consistent, but contrary to the expectation that noise lowers confidence. On the course files: 0.58 clean → 0.48–0.49 noisy.

---

## 9. Fusion with text (Kalman filter)

The conversation state is the same Kalman filter described in the text handover (section 9 there). For each message:

1. **Text update** — as before (the customer's affect may have changed since the previous message, so process noise is added).
2. **Voice update** (only when a recording is attached) — a second measurement of the **same moment**, so no process noise is added. Measurement noise = (voice σ)² × noise factor.

The weight of each channel follows from its measured error per dimension: text counts more for valence, voice for dominance, and both about equally for activity. Typical weights of a voice measurement on a first message: valence 0.28, activity 0.36, dominance 0.48.

Further rules:
- The short-text confidence caps (≤ 2 words → 0.35, ≤ 5 words → 0.65) apply only when no recording is attached, since the text is then not the only evidence. The interface requires typed text before a recording can be sent, so a voice message may come with a placeholder word.
- **Failure safety:** if the recording cannot be processed (missing file, invalid audio, missing weights), the text result is kept unchanged and `voice_processing_failed` is added to the flags.
- **When wording and tone disagree,** the fused label follows the channel that is more reliable for each dimension. Example: neutral text "Here is my message." with a furious recording gives fused label `neutral` with activity raised to +0.33, while the voice-only reading (`anger`) is logged. This is a deliberate, data-driven choice.

---

## 10. Output and log

Without a recording, the output is unchanged. With a recording, `details.voice` contains:

| Field | Content |
|---|---|
| `status` | `processed` or `failed` (with `error_type`, `error`) |
| `voice_only` | valence, activity, dominance and label of the recording alone |
| `predicted_emotion`, `emotion_probabilities` | classifier output |
| `noise_factor` | measurement-noise multipliers (valence, activity, dominance) |
| `message_weight` | how much the recording moved the state (Kalman gain per dimension) |
| `acoustics` | duration, loudness, median pitch, pitch movement, flatness |

The main `valence`, `activity`, `dominance`, `label` and `confidence` are the fused values.

---

## 11. Validation

### Course audio files (each in a new conversation, text "Here is my message.")

| File | Prosody activity | emotion2vec activity | Fused activity | Confidence |
|---|---|---|---|---|
| calm_clean | −0.36 | +0.18 | −0.17 | 0.58 |
| calm_noisy | −0.30 | −0.58 | −0.14 | 0.48 |
| agitated_clean | +0.33 | −0.58 | +0.08 | 0.58 |
| agitated_noisy | +0.35 | −0.58 | +0.09 | 0.49 |
| speaker_low | −0.33 | +0.69 | −0.15 | 0.58 |
| speaker_high | −0.26 | −0.58 | −0.13 | 0.58 |

All checks pass: agitated > calm, speaker_high ≈ speaker_low, noise lowers confidence. emotion2vec alone fails all three on these synthetic (non-speech) tones.

### Integration example
Same text "I am still waiting for my order.": without audio `neutral` (activity +0.08); with an angry test-actor recording `frustration` (valence −0.37, activity +0.44).

### Final held-out speech demo validation (21 November 2026)

The final demo assets use real acted speech from CREMA-D test actors rather than
the synthetic course tones. Each run started from a reset state and used the same
neutral text, `"Here is my message."`. All files matched the SHA-256 values in
the voice manifest.

| File | Classifier output | Voice-only VAD label | Voice V / A / D | Fused label | Confidence | Action |
|---|---|---|---|---|---:|---|
| `1013_WSI_ANG_XX.wav` | anger | anger | -0.744 / +0.884 / +0.472 | neutral | 0.605 | `ANSWER_EMPATHIC` |
| `1020_DFA_HAP_XX.wav` | happiness | calm | +1.000 / +0.430 / +1.000 | calm | 0.544 | `ANSWER` |
| `1020_WSI_SAD_XX.wav` | sadness | sadness | -0.994 / -0.019 / -1.000 | neutral | 0.582 | `ANSWER` |
| `1036_IWL_FEA_XX.wav` | fear | sadness | -0.954 / +0.690 / -0.624 | neutral | 0.577 | `ANSWER` |
| `1037_IOM_DIS_XX.wav` | disgust | sadness | -1.000 / -0.004 / -0.553 | neutral | 0.581 | `ANSWER` |
| `1065_ITS_NEU_XX.wav` | neutral | neutral | -0.070 / +0.247 / -0.430 | neutral | 0.678 | `ANSWER` |

Three outputs must not be confused in the report:

1. `details.voice.predicted_emotion` is the six-class emotion2vec + logistic
   regression category.
2. `details.voice.voice_only.label` is derived from the voice VAD coordinates;
   therefore happiness can map to `calm`, while fear or disgust can map to
   `sadness`.
3. The top-level `label` and `action` are produced after text/voice fusion and
   policy rules. For the anger example, the fused label remains `neutral`, but
   the voice-only anger safeguard correctly selects `ANSWER_EMPATHIC`.

These clips are clear demonstration examples, not a replacement for evaluation
on the complete 1,142-recording test split.

### Automated tests (`tests/test_voice.py`, 12 tests)
- Course pipeline: frame count, MFCC shape, mel values, pitch of a known tone, flatness of noise vs tone.
- Speaker rule and course files: absolute pitch never an input; speaker_high ≈ speaker_low; agitated > calm (clean and noisy); noise detected only in noisy files.
- Engine with voice (skipped if the voice weights are not downloaded): contract holds with audio; voice reading logged and moves the state; noise lowers confidence; broken audio keeps the text result.

Integration-stage suite, before the Topic 4 tests were added:
`python -m unittest discover tests` → 15 tests, OK. Text-only messages and the
four mandatory scenarios gave exactly the same results as before voice
integration. The final repository result is recorded below.

---

The earlier 15-test result above records the state immediately after voice
integration. The final integrated run on 21 November 2026 used both encoder
weights and produced **23 tests, OK, no skips**: 3 contract tests, 8 Topic 4
integration tests and 12 voice/acoustic tests.

## 12. How to reproduce

```bash
python engine/download_crema_d.py              # CREMA-D audio (hash-verified), only for the experiments
python engine/train_voice_classifier.py        # emotion classifier + dev/test probabilities
python engine/calibrate_voice.py               # voice scale and error (dev), test evaluation
python engine/extract_acoustic_features.py     # acoustic features for all clips
python engine/train_voice_prosody.py           # prosodic activity model and comparison variants
python engine/calibrate_voice_noise.py         # noise experiment (~30 min)
python tests/test_voice.py                     # voice tests
```

Constants in `voice_affect.py` (`VOICE_SCALE`, `VOICE_SIGMA`, noise table) come from these scripts.

---

## 13. Known limitations

1. **Acted speech.** CREMA-D actors perform emotions on fixed sentences; real customers are subtler. Classifier test accuracy is 71.8% (macro F1 0.72; per emotion F1: anger 0.83, neutral 0.82, happiness 0.71, fear 0.67, sadness 0.65, disgust 0.62).
2. **Category-based truth.** Voice error is measured against the reference point of the intended emotion, not human VAD ratings, and the reference values are word ratings, not ratings of voices.
3. **Loudness depends on the microphone.** Absolute loudness is the main activity cue; a different microphone or recording level shifts it.
4. **Residual speaker bias** in emotion2vec's valence (−0.22) and dominance (+0.26).
5. **Noise model.** Calibrated with white noise only; babble, music or reverberation were not tested.
6. **Rule-based parts.** The confidence penalty for noise is a rule, not a measured quantity.
7. **Independence assumption.** Text and voice errors are treated as independent in the fusion.
8. **Synthetic inputs.** The course audio files are tones, not speech: emotion2vec reads them all as sadness/disgust; only prosody behaves sensibly on them.
9. **Pitch octave errors** in the autocorrelation tracker, mitigated by the robust spread measure.
10. **Interface.** The GUI requires typed text to send a recording and cannot record from the microphone; it attaches existing WAV files.
11. **Language.** English acted speech only.
12. **Privacy.** Voice is biometric personal data; recordings must only be used with consent and are not stored by the engine.

---

## 14. AI log

Tool: Claude (Anthropic), used through Claude Code. The AI proposed options and drafted code and text; design decisions were taken by the Topic 2 member after discussing alternatives.

| Task | AI assistance | Verification |
|---|---|---|
| Requirements review | Read the Project Brief, Evaluation Guide and voice lecture; listed what the voice channel must satisfy | Checked against the documents |
| Voice → VAD mapping | Proposed lexicon vs literature values; extracted the six NRC scores | Values read from the lexicon file |
| Calibration | Drafted `calibrate_voice.py`; dev/test split use | Reproduced by the script |
| Acoustic features | Drafted `acoustic_features.py` from the lecture pipeline; robust pitch spread | Compared with librosa; unit tests |
| Speaker problem | Measured speaker bias; proposed and compared three activity variants | `train_voice_prosody.py` results |
| Noise | Designed and drafted the noise experiment; flatness as detector; confidence penalty option | `calibrate_voice_noise.py` results; tests |
| Fusion | Drafted the voice Kalman step, failure safety and short-text cap rule | Course files, real-voice checks, contract and scenario tests |
| Tests and documentation | Drafted `tests/test_voice.py` and this handover | Tests pass; numbers re-checked against the result files |
