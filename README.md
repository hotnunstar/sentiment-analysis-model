# NovaShop Affective Assistant

NovaShop is an offline customer-support assistant that estimates the customer's
emotional state and chooses an appropriate response action. It accepts text and
an optional WAV recording.

## What the engine returns

For every message, `Engine.process()` returns:

- `valence`, `activity`, `dominance`: affective map coordinates from `-1` to `1`;
- `confidence`: confidence in the emotion label from `0` to `1`;
- `label`: `neutral`, `joy`, `calm`, `frustration`, `anger` or `sadness`;
- `action`: one of the six actions required by the project brief;
- `reply`, `flags` and `details`: the response and diagnostic information.

The six actions are `ANSWER`, `ANSWER_EMPATHIC`, `ASK_CLARIFICATION`,
`OFFER_HUMAN`, `ESCALATE` and `CLOSE_POSITIVE`.

## Project structure

| Path | Purpose |
|---|---|
| `engine/` | Text/voice perception, affective state and decision policy |
| `harness/` | Shared interface, contract, session and logging code |
| `scenarios/` | Four mandatory and four practice conversations |
| `tests/` | Contract, voice and Topic 4 integration tests |
| `assets/audio/` | Held-out CREMA-D demo speech and synthetic engineering signals |
| `logs/` | Plain-text session logs created while the program runs |
| `check_project.py` | Read-only installation and model-file check |

## Requirements

- Python 3.9 or later. The project was tested by the group with **Python 3.13** (recommended for the optional **voice** channel; emotion2vec via FunASR may not load on Python 3.14).
- Packages listed in `requirements.txt`.
- Tkinter for the graphical interface.
- The text model weight described below.
- The voice model weight only when using the optional voice channel.

## Clean installation

From the project root, create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Linux, install Tkinter separately if necessary:

```bash
sudo apt install python3-tk
```

## Model weights

The two encoder weights are too large for GitHub. Download them from the
[group Google Drive folder](https://drive.google.com/drive/folders/1mXXYlbqNvOcEIQl74V8zCEJdlOqwpjTS?usp=sharing)
and keep the filenames unchanged.

Required for text mode:

```text
engine/models/text/encoder/model.safetensors          (about 253 MB)
```

Required only for the optional voice mode:

```text
engine/models/voice/encoder/emotion2vec_base.pt       (about 1.07 GB)
```

For an offline demonstration, download the required weights before disconnecting
from the internet and include them in the delivered project copy.

## Check the installation

Run the read-only checker:

```bash
python check_project.py
```

`[READY] Text mode is ready` means the mandatory text system has its packages
and model files. Missing voice items are reported as optional.

## Run the application

Open the graphical interface:

```bash
python run_app.py
```

The interface shows the conversation, affective map, confidence, label, action,
flags and session log. Select **3D view** to include dominance.

To attach voice, type a message, choose **Audio (optional)...**, select a WAV
file such as one from `assets/audio/`, and press **Send**.

## Optional voice channel

The voice path runs locally and has three stages:

1. A frozen [`emotion2vec_base`](https://huggingface.co/emotion2vec/emotion2vec_base)
   encoder converts the complete utterance into a 768-dimensional emotional
   speech embedding. The original model was self-supervised on 262 hours of
   open-source emotional speech; it extracts vocal patterns rather than
   determining a speaker's true internal emotional state.
2. A logistic-regression classifier trained on acted human speech from
   [CREMA-D](https://github.com/CheyneyComputerScience/CREMA-D) predicts one of
   six categories: anger, disgust, fear, happiness, neutral or sadness. Actors
   are separated between the train, development and test splits.
3. Speaker-normalised prosody supplies an activity estimate. The engine maps
   the voice result onto valence, activity and dominance and fuses it with the
   text estimate. Consequently, the voice-only category, voice-only VAD label
   and final fused label can differ.

The encoder weight and trained classifiers are loaded from
`engine/models/voice/`; prediction does not download a model or send the audio
to an external service. CREMA-D contains acted English speech, not spontaneous
customer-support calls, so its predictions should be treated as estimates and
not as ground-truth emotions.

### Voice demonstration audio

The categorical voice demonstration uses the seven WAV files in
`assets/audio/demo_emotions/`. They are real acted-speech recordings from the
official CREMA-D `AudioWAV` collection, distributed under the Open Database
License. All seven belong to held-out test actors, were absent from classifier
training, and are checked against the SHA-256 values in
`engine/data/voice/manifest.json`. The set covers all six classifier categories
and includes a second anger example.

For a reproducible comparison, start a new conversation before every file and
use the same neutral text:

```text
Here is my message.
```

Recommended examples are:

| File | Intended CREMA-D category | Demonstration purpose |
|---|---|---|
| `1013_WSI_ANG_XX.wav` | Anger | Clearest example of voice changing the policy to an empathic answer |
| `1020_DFA_HAP_XX.wav` | Happiness | Positive contrast; may map to the project's calm VAD region |
| `1065_ITS_NEU_XX.wav` | Neutral | Neutral comparison |

See `assets/audio/demo_emotions/README.txt` for all seven files and their
expected outputs. The other WAV files directly under `assets/audio/`—such as
`calm_clean.wav`, `agitated_clean.wav` and the speaker variants—are synthetic
teaching signals. They test noise handling, prosody and speaker invariance, but
they are not human speech and must not be presented as validated emotion
examples.

## Run the mandatory scenarios

```bash
python run_scenario.py scenarios/mandatory/M1_calm_faq.json
python run_scenario.py scenarios/mandatory/M2_growing_frustration.json
python run_scenario.py scenarios/mandatory/M3_explicit_requests.json
python run_scenario.py scenarios/mandatory/M4_ambiguity_and_robustness.json
```

Each command prints the decisions and creates a plain-text log in `logs/`.

## Tests

Topic 4 integration tests do not load the large models:

```bash
python -m unittest tests.test_topic4 -v
```

Run the complete suite after installing the requirements and adding the text
model weight:

```bash
python -m unittest discover tests -v
```

The repository currently contains 23 tests: 3 engine-contract tests, 12 voice
tests and 8 Topic 4 integration tests. Four voice integration tests are skipped
when the optional voice weight is absent.

## Session logs

Every graphical or command-line session creates a UTF-8 `.txt` file in `logs/`.
The log records input, optional media, map values, confidence, label, action,
flags, latency, reply, diagnostic details and contract problems.

After recording, copy the log used in the final video to
`logs/demo_session.txt`. This specific filename is not ignored by Git and should
be included inside the delivered `code/logs/` folder.

## Troubleshooting

- `No module named ...`: activate the virtual environment and install
  `requirements.txt`.
- Missing `model.safetensors`: download the required text weight and place it at
  the exact path shown above.
- Voice is skipped or reports `voice_processing_failed`: add
  `emotion2vec_base.pt`; text processing remains available.
- Tkinter import error on Linux: install `python3-tk`.
- Model fingerprint error: do not rename or edit files inside the encoder folder.

## Reproducible demonstration order

1. Run `python check_project.py`.
2. Run `python -m unittest discover tests -v`.
3. Run `python run_app.py`.
4. Play mandatory scenarios M1, M2, M3 and M4.
5. Expand the session log and open its corresponding file from `logs/`.
6. Demonstrate one optional voice example if the voice weight is installed.
7. Copy the demonstrated log to `logs/demo_session.txt` for delivery.

## Group report

The written report is in **`report/`**: edit `report/report.md`, build `report/group_report.pdf` (see `report/README.md`). Include `report/report.pdf` in the Moodle zip next to `code/` and the video.
