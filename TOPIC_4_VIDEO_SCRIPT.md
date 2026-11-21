# Topic 4 Video Demo Script — maximum 5 minutes

## Before recording

1. Install the requirements and the text and voice model weights.
2. Run `python check_project.py`; both text and optional voice mode must say
   `[READY]` because this demo includes both implemented channels.
3. Run `python -m unittest discover tests -v`; confirm `Ran 23 tests` and `OK`
   with no skipped voice tests.
4. Close unnecessary windows and remove personal information from the screen.
5. Test `assets/audio/demo_emotions/1013_WSI_ANG_XX.wav` once before recording.
   It is real acted speech from the held-out CREMA-D test split. The first voice
   request loads the large model and can take a few seconds.
6. Start a fresh application session so the video creates a clean log.
7. After recording, copy that real log to `logs/demo_session.txt` for delivery.

## 0:00–0:30 — Start and interface

Screen:

```bash
python run_app.py
```

Suggested narration:

> This is the NovaShop affective customer-support assistant. The shared
> interface communicates with our engine through `reset` and `process`. It shows
> the conversation, valence, activity, dominance, confidence, emotion label,
> selected action and the affective map. Every turn is also written to a
> plain-text session log.

Briefly point to the 2D map, 3D checkbox, metrics, scenario selector, optional
audio selector and log. The project demonstrates text and voice only; do not
select or discuss the image input as an implemented channel.

## 0:30–1:15 — M1 calm FAQ

Select and play `M1`.

Suggested narration:

> M1 contains calm delivery and address questions. The engine keeps the state
> close to neutral and chooses `ANSWER`. The final appreciative message is
> recognized as positive closure, so the action changes to `CLOSE_POSITIVE`.

Point to the numbered map points, confidence and final action.

## 1:15–2:10 — M2 growing frustration

Select and play `M2`.

Suggested narration:

> M2 shows why conversation state is necessary. Delays and unanswered emails
> build a frustration streak across turns. The system first answers with empathy,
> then offers a human when the frustration persists. The final legal threat has
> priority and produces `ESCALATE`.

Point out the movement toward negative valence/high activity and the action
changes. Do not claim that every emotional prediction is perfectly accurate.

## 2:10–2:55 — M3 explicit requests

Select and play `M3`.

Suggested narration:

> M3 tests explicit requests. A return question receives a normal answer. A
> direct request for a human produces `OFFER_HUMAN`, even if the affect estimate
> is uncertain. Mentioning the consumer-protection authority produces
> `ESCALATE`. Explicit safety and service signals therefore take priority over
> the emotion label.

## 2:55–3:40 — M4 robustness

Select and play `M4`.

Suggested narration:

> M4 tests uncertain input. Short or dismissive messages and the possible
> sarcasm example lead to `ASK_CLARIFICATION`, avoiding an overconfident
> interpretation. The negated phrase is handled without treating every negative
> word literally. The Portuguese resolved message is recognized as a positive
> closure.

Point to the sarcasm flag and lower confidence when visible.

## 3:40–4:15 — Log and software evidence

Expand **Session log**, then open the matching file in `logs/`.

Suggested narration:

> The same information is saved as readable UTF-8 text. Each entry contains the
> input, map coordinates, confidence, label, action, flags, latency, reply and
> diagnostic details. This makes the demonstration reproducible and lets us
> inspect why the policy selected an action.

## 4:15–4:55 — Voice channel

Start a new conversation with **New conversation** so the previous scenarios do
not influence the voice result. Type `Here is my message.`, select
**Audio (optional)...**, attach
`assets/audio/demo_emotions/1013_WSI_ANG_XX.wav` and send it. This held-out
acted-speech sample is labelled and predicted as anger. In the verified demo
run, the voice-only label was `anger`, fused activity increased, and the action
changed from `ANSWER` to `ANSWER_EMPATHIC`.

Suggested narration:

> Audio is an optional active channel. When a recording is attached, the engine
> uses emotion2vec for emotion probabilities and speaker-invariant prosodic
> features for activity. It fuses this evidence with the text state and records
> the voice-only reading, acoustic information and noise factors in the log. If
> audio processing fails, the text result is preserved instead of failing the
> complete request.

Point to the increased activity, the voice information in `details`, and the
confidence value. Do not claim that the voice classifier alone determines the
final state: text and voice are fused by the affective-state component.

If time permits, start another new conversation with the same text and attach
`assets/audio/demo_emotions/1020_DFA_HAP_XX.wav`. Point out that the classifier
predicts `happiness`, while the VAD-derived and fused label is `calm`. This shows
variation without claiming that classifier categories and final labels are the
same thing.

Do not use `agitated_clean.wav` to demonstrate emotion classification. The
`calm_*`, `agitated_*` and `speaker_*` files are synthetic teaching tones used to
test prosody, noise and speaker invariance; they are not recordings of emotional
speech.

## 4:55–5:00 — Finish

> The four standard scenarios, automated tests and exported log verify the
> complete path from text and optional voice input to affective state, action
> and response.

Stop the recording before five minutes.
