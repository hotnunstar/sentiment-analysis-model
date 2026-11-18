# Topic 4 Video Demo Script — maximum 5 minutes

## Before recording

1. Install the requirements and model weights.
2. Run `python check_project.py`; text mode must say `[READY]`.
3. Run `python -m unittest discover tests -v`; save the result.
4. Close unnecessary windows and remove personal information from the screen.
5. Start a fresh application session so the video creates a clean log.
6. After recording, copy that real log to `logs/demo_session.txt` for delivery.

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

Briefly point to the 2D map, 3D checkbox, metrics, scenario selector and log.

## 0:30–1:20 — M1 calm FAQ

Select and play `M1`.

Suggested narration:

> M1 contains calm delivery and address questions. The engine keeps the state
> close to neutral and chooses `ANSWER`. The final appreciative message is
> recognized as positive closure, so the action changes to `CLOSE_POSITIVE`.

Point to the numbered map points, confidence and final action.

## 1:20–2:20 — M2 growing frustration

Select and play `M2`.

Suggested narration:

> M2 shows why conversation state is necessary. Delays and unanswered emails
> build a frustration streak across turns. The system first answers with empathy,
> then offers a human when the frustration persists. The final legal threat has
> priority and produces `ESCALATE`.

Point out the movement toward negative valence/high activity and the action
changes. Do not claim that every emotional prediction is perfectly accurate.

## 2:20–3:10 — M3 explicit requests

Select and play `M3`.

Suggested narration:

> M3 tests explicit requests. A return question receives a normal answer. A
> direct request for a human produces `OFFER_HUMAN`, even if the affect estimate
> is uncertain. Mentioning the consumer-protection authority produces
> `ESCALATE`. Explicit safety and service signals therefore take priority over
> the emotion label.

## 3:10–4:00 — M4 robustness

Select and play `M4`.

Suggested narration:

> M4 tests uncertain input. Short or dismissive messages and the possible
> sarcasm example lead to `ASK_CLARIFICATION`, avoiding an overconfident
> interpretation. The negated phrase is handled without treating every negative
> word literally. The Portuguese resolved message is recognized as a positive
> closure.

Point to the sarcasm flag and lower confidence when visible.

## 4:00–4:35 — Log and software evidence

Expand **Session log**, then open the matching file in `logs/`.

Suggested narration:

> The same information is saved as readable UTF-8 text. Each entry contains the
> input, map coordinates, confidence, label, action, flags, latency, reply and
> diagnostic details. This makes the demonstration reproducible and lets us
> inspect why the policy selected an action.

## 4:35–4:55 — Optional voice

If the voice weight is installed, type `Here is my message.`, attach a sample
from `assets/audio/` and send it.

Suggested narration:

> Voice is an optional channel. The engine combines the wording with vocal
> evidence and records the voice-only reading and noise information in the log.
> If voice processing fails, the text result is preserved.

If voice is unavailable, use these seconds to show `python check_project.py`
and explain that it reports voice separately as optional.

## 4:55–5:00 — Finish

> The four standard scenarios, automated tests and exported log verify the
> complete path from input to affective state, action and response.

Stop the recording before five minutes.
