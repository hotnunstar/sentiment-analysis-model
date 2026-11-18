# Topic 4 — Software, Interface, Tests and Demo

**Topic owner:** Tomás

## 1. Responsibility

Topic 4 integrates the work of Topics 1–3 with the shared project kit. It does
not change the emotion models or the decision thresholds. Its responsibilities
are:

1. make the repository understandable and reproducible;
2. verify the public `Engine` contract;
3. test the interface/session/logging path;
4. verify the mandatory scenarios;
5. document installation, execution and troubleshooting;
6. prepare the five-minute demonstration.

The shared `harness/`, `run_app.py`, `run_scenario.py` and scenario files were
not modified as part of this topic.

## 2. System integration

The complete path is:

```text
run_app.py or run_scenario.py
    -> harness.loader.load_engine()
    -> Engine.reset()
    -> Engine.process(text, audio_path, image_path)
    -> harness.contract.normalize()
    -> Session history and SessionLogger
    -> GUI/map or command-line output
```

`Engine.process()` returns a dictionary containing `valence`, `activity`,
`dominance`, `confidence`, `label`, `action`, `reply`, `flags` and `details`.
The interface and the teacher's tests use this dictionary rather than calling
the internal estimators directly.

The contract normalizer protects the interface from malformed output. It clips
numeric values to their accepted ranges, checks the action, gives safe defaults
and records problems. The `Session` also catches engine exceptions, so one bad
message does not close the graphical application.

## 3. Files created or updated by Topic 4

| File | Purpose |
|---|---|
| `check_project.py` | Checks Python, packages, required files and optional voice files without changing the computer |
| `tests/test_topic4.py` | Eight small tests for the contract, session, logs, scenarios, public API and README |
| `README.md` | Clean installation, model placement, checker, run commands, tests and troubleshooting |
| `Topic 4 - Handover.md` | Technical explanation and handover for this topic |
| `Topic 4 - Report Section.md` | Report-ready description of the Topic 4 work |
| `TOPIC_4_VIDEO_SCRIPT.md` | Timed recording and narration plan for the demo |

## 4. Project checker

Run:

```bash
python check_project.py
```

The checker is intentionally simple and uses only the Python standard library.
Its small functions each have one responsibility:

- `package_is_installed()` checks whether Python can find one package;
- `file_exists()` checks one path relative to the project;
- `check_python()` verifies Python 3.9 or later;
- `check_packages()` checks a group of imports;
- `check_files()` checks a group of project files;
- `main()` prints the summary and returns exit code 0 or 1.

The mandatory text channel and optional voice channel are reported separately.
A missing voice weight therefore does not pretend that the mandatory text
channel is broken.

## 5. Automated tests

Run only the Topic 4 tests:

```bash
python -m unittest tests.test_topic4 -v
```

These tests use `FakeEngine`, a predictable engine with the same public methods
as the real one. It avoids loading machine-learning models and makes integration
failures easy to understand.

The eight tests verify:

1. a valid result passes the shared contract;
2. an invalid result is reported and receives a safe action;
3. a session sends a message and writes a readable log;
4. a session survives an engine exception;
5. all eight project scenarios exist;
6. M1–M4 contain non-empty messages;
7. `Engine` exposes `reset()` and the correct `process()` signature;
8. the README contains the main verification and execution commands.

Run all repository tests with:

```bash
python -m unittest discover tests -v
```

The full suite requires the installed dependencies and the mandatory text model
weight. Voice integration tests are skipped when the optional voice encoder is
not available.

**Verification on 18 November 2026:** all eight Topic 4 tests passed. The full
suite could not complete in this checkout because the machine-learning packages
and large encoder weights were not installed; `check_project.py` reports those
missing items explicitly. The full suite must be repeated in the prepared demo
environment before delivery.

## 6. Interface and logs

The shared graphical interface shows:

- the customer and assistant messages;
- valence, activity and dominance;
- confidence, label, action and flags;
- a 2D or 3D affective map;
- scenario selection;
- optional WAV selection;
- an expandable session log.

`SessionLogger` writes the same information to `logs/session_*.txt`, including
latency and diagnostic details. A new session receives a new filename and does
not overwrite a previous log.

## 7. Mandatory demo scenarios

- **M1 — calm FAQ:** normal questions should be answered and a positive ending
  should close positively.
- **M2 — growing frustration:** the state becomes more negative/active, repeated
  frustration offers a human, and a legal threat escalates.
- **M3 — explicit requests:** return information is answered, a human request
  offers a human, and a consumer-protection threat escalates.
- **M4 — ambiguity and robustness:** short or sarcastic messages ask for
  clarification, negation is not treated as simple negativity, and a resolved
  Portuguese message closes positively.

## 8. Current limitations and delivery check

The large encoder weights are intentionally ignored by Git. Before an offline
demonstration, copy `model.safetensors` and, if voice is shown,
`emotion2vec_base.pt` to the paths documented in the README.

Before delivery:

1. replace the owner placeholder at the top of this file;
2. prepare a clean virtual environment and install `requirements.txt`;
3. add the model weights;
4. run `check_project.py` and the complete test suite;
5. run M1–M4 and inspect their output;
6. record the video using `TOPIC_4_VIDEO_SCRIPT.md`;
7. copy the real video log to `logs/demo_session.txt` and include it in the zip.

## 9. AI-use record

AI assistance was used to review the brief and repository, draft the project
checker, draft Topic 4 tests, reorganize the README and prepare documentation.
The changes were verified with the automated Topic 4 test suite and manual code
review. The student must review every function, run the final end-to-end checks
with the model files and be able to explain or modify the code during the
presentation.
