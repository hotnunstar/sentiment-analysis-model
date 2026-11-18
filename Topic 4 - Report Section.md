# Software Integration, Interface, Tests and Demonstration

The software contribution integrated the perception, affective-state and
decision components into the shared NovaShop application. The main objective was
to make the complete system reproducible and observable without changing the
shared interface supplied in the project kit. The application continues to use
`Engine.reset()` to begin a conversation and
`Engine.process(text, audio_path=None, image_path=None)` to process each turn.

The engine returns valence, activity and dominance in the interval `[-1, 1]`, a
confidence value in `[0, 1]`, an emotion label, one of the six permitted actions,
a reply, flags and diagnostic details. This dictionary is passed through the
shared contract normalizer before it reaches the interface. The normalizer checks
types and ranges, clips invalid numeric values, rejects unknown actions and
records any problems. This separation is useful because the graphical interface,
scenario runner and tests can all use the same public contract without depending
on the internal machine-learning implementation.

The shared `Session` class connects the engine to both the graphical and
command-line interfaces. It measures latency, numbers the messages, stores the
conversation history and catches unexpected exceptions. Therefore, an error in
one engine call is recorded instead of immediately terminating the interface.
Every turn is also sent to `SessionLogger`, which creates a UTF-8 plain-text file.
The log includes the input, optional audio or image path, affective coordinates,
confidence, label, action, flags, latency, reply and diagnostic details. These
logs provide evidence for the demonstration and make individual decisions easier
to inspect.

The graphical interface displays the conversation and the latest engine output.
It plots every message on a two-dimensional valence–activity map and can enable a
three-dimensional view when dominance is returned. It can play all mandatory and
practice scenarios and can attach a WAV file for the optional voice channel. The
same scenario files can be executed without the graphical interface through
`run_scenario.py`, which is helpful for reproducible checks.

To identify incomplete installations before a demonstration, a small read-only
checker was added in `check_project.py`. The checker uses only the Python standard
library. It verifies the Python version, required packages, essential project
files and model weights. Mandatory text requirements and optional voice
requirements are reported separately. It never installs packages or downloads
files, so its output describes the actual state of the delivered copy. A success
exit code indicates that text mode has the local requirements needed to start.

Eight Topic 4 tests were added. They deliberately use a small deterministic
`FakeEngine`, allowing the software integration to be checked without loading the
large neural-network weights. The tests cover valid and invalid contract results,
session history, log creation, engine-exception handling, the presence and
contents of the eight scenarios, the public engine method signature and the main
README commands. These tests complement the existing engine-contract and voice
tests rather than replacing them. The repository now contains 23 automated tests
in total. The full test suite must still be executed with the mandatory text
weight installed; tests that need the optional voice encoder are skipped when
that file is absent.

All eight Topic 4 tests passed in the integration environment. The end-to-end
suite could not complete there because the external machine-learning packages
and encoder weights had not yet been installed. This dependency state was
identified by the checker rather than hidden by the tests; the complete suite
must be repeated in the prepared offline demonstration environment.

Reproducibility instructions were consolidated in the README. They describe a
clean virtual-environment installation, the exact locations of the two large
encoder weights, the project checker, graphical and scenario commands, tests,
logs and common failure cases. Because the final code demonstration is performed
without connectivity, the mandatory text weight must be downloaded before the
demo and included in the delivered project copy. The optional voice weight is
also needed when voice is demonstrated.

The demonstration follows the same sequence on every machine: check the local
installation, run the automated tests, start the graphical application, play M1
to M4 and inspect the resulting session log. M1 demonstrates normal FAQ handling
and positive closure. M2 demonstrates accumulated frustration and escalation.
M3 demonstrates that explicit human and legal requests have priority. M4
demonstrates safe behavior for ambiguity, sarcasm, negation and Portuguese input.
The final part of the video opens the exported text log and, when the optional
model is available, shows one voice example.

The main limitation of the software packaging is the size of the model weights:
they cannot be stored in the GitHub repository and have to be transferred with
the final offline copy. The checker makes this condition explicit, but it cannot
repair a missing installation. In addition, passing contract tests shows that
the components communicate correctly; it does not by itself establish that the
emotion predictions are accurate. Prediction quality, dataset limitations and
ethical risks are evaluated separately in the evaluation section of the report.
