Class 2 audio pack (synthetic, voice-like signals, 16 kHz, 16-bit mono, 2 s each). For teaching only.
calm_clean.wav / agitated_clean.wav   - low pitch quiet vs high pitch loud (about 120 Hz vs 230 Hz)
calm_noisy.wav / agitated_noisy.wav   - the same signals with white noise added at about 5 dB SNR
speaker_low.wav / speaker_high.wav    - the same calm tone at about 90 Hz and 260 Hz
With the reference prototype: the fixed baseline gives speaker_high a higher arousal than speaker_low
(wrong: both are calm), and the noisy files keep the same confidence as the clean ones. These are the
problems students must solve in variants C and A.

1009_DFA_ANG_XX.wav - real acted angry speech from actor 1009 in the held-out
CREMA-D test split. Included for the integrated voice demo. The file hash is
verified by engine/data/voice/manifest.json. Source: CREMA-D
(https://github.com/CheyneyComputerScience/CREMA-D), Open Database License.

demo_emotions/ - seven hash-verified held-out CREMA-D speech recordings covering
all six classifier categories, with two anger examples. See
demo_emotions/README.txt for expected results and the distinction between
predicted emotion, voice-only VAD label and fused label.
