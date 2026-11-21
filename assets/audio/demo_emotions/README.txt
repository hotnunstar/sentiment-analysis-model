CREMA-D held-out speech examples for the NovaShop voice demo
=============================================================

These are real acted-speech recordings, not the synthetic teaching tones in the
parent folder. Every file belongs to the test split, was absent from classifier
training, and matches the SHA-256 stored in engine/data/voice/manifest.json. The
folder contains all six categories plus a second anger example.

Use the same neutral text for comparisons:

    Here is my message.

Start a new conversation before each file so that the previous emotional state
does not affect the next result.

File                     Intended/predicted  Voice-only VAD label  Fused label  Action
1009_DFA_ANG_XX.wav      anger               anger                 neutral      ANSWER_EMPATHIC
1013_WSI_ANG_XX.wav      anger               anger                 neutral      ANSWER_EMPATHIC
1020_DFA_HAP_XX.wav      happiness           calm                  calm         ANSWER
1020_WSI_SAD_XX.wav      sadness             sadness               neutral      ANSWER
1036_IWL_FEA_XX.wav      fear                sadness               neutral      ANSWER
1037_IOM_DIS_XX.wav      disgust             sadness               neutral      ANSWER
1065_ITS_NEU_XX.wav      neutral             neutral               neutral      ANSWER

Why some names differ
---------------------

details.voice.predicted_emotion is the six-class voice classifier result:
anger, disgust, fear, happiness, neutral or sadness.

details.voice.voice_only.label is derived afterwards from the voice VAD point.
For example, happiness can fall in the project's "calm" VAD region, while fear
and disgust can fall in the "sadness" region. The main top-level label is the
final fusion of the typed text and voice, so it can remain neutral even when the
voice-only reading is emotional.

Recommended video examples
--------------------------

1. 1013_WSI_ANG_XX.wav: clearest policy change; neutral text becomes
   ANSWER_EMPATHIC because the voice-only label is anger.
2. 1020_DFA_HAP_XX.wav: positive contrast; the fused label becomes calm.
3. 1065_ITS_NEU_XX.wav: neutral comparison if there is enough time.

Source and licence
------------------

CREMA-D: https://github.com/CheyneyComputerScience/CREMA-D
Licence: Open Database License.
