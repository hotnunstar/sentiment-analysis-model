# NovaShop Topic 1 Text Handover

**Topic owner:** Salim Houmaidan

**Revision:** 17 November 2026

**Scope:** Text perception in the integrated NovaShop engine, with the October prototype evaluation included as supporting evidence.

The original text estimator and scenario checks were developed by Salim Houmaidan. The integrated version includes the cross-platform fingerprint fix and dominance update reported by Nuno Araújo.

## 1. Purpose and method

Topic 1 converts an English customer message into three continuous scores: **valence** (negative to positive), **activity** (low to high activation) and **dominance** (feeling less to more in control). A saved, frozen DistilBERT encoder produces a pooled 768-dimensional embedding. Ridge regression maps that embedding to valence, activity and dominance in that order. Inference clips the three scores to `[-1, 1]`.

The frozen encoder provides contextual features while keeping training limited to the small regression model. Ridge regularisation penalises large coefficients, which is useful when fitting continuous targets from many potentially correlated embedding features. The retained setting is **alpha = 100**. The follow-up check found slightly higher development error at 300 and 1000, so 100 was best among the settings tested.

The only handwritten text rule is the `possible_sarcasm` flag. It looks for opening praise such as “Great” combined with selected problem expressions such as “another delay”. A repair word such as “fixed” can suppress the flag unless nearby negation is detected. The flag leaves the regression scores unchanged. The trained model handles the wording of negation, intensifiers, punctuation and short messages through the embedding. The flag alone cannot establish the intended meaning of sarcasm.

### Inference and interpretation

1. Load the saved encoder and the matching fitted regressor. Initialise the estimator once and reuse it across messages.
2. Encode each message as a pooled 768-dimensional vector using the saved encoder and pooling configuration.
3. Apply the fitted Ridge coefficients to estimate valence, activity and dominance. Clip each score to `[-1, 1]`.
4. Evaluate the sarcasm cue independently and include any matching flag in the result.

Activity describes emotional activation. Anger and tiredness can both have negative valence, with different activation levels. Dominance describes the degree of control expressed in the message.

The October prototype used mean pooling, a 128-token input limit and embeddings without unit normalisation. The saved encoder configuration is part of the model bundle and should travel with its weights. The learned estimator can respond to negation and emphasis, as the examples below show, with variable results across phrasings.

### Meaning of the sarcasm flag

`possible_sarcasm` signals that the wording matches a surface pattern. The detector can miss implicit sarcasm and misread mixed clauses. The flag has no calibrated probability, and the project did not measure its precision or recall. Topic 2 can use it when interpreting uncertainty.

## 2. Training and evaluation

The training script uses EmoBank’s `V`, `A` and `D` ratings in `engine/data/text/emobank.csv`. It converts the original 1–5 ratings to `[-1, 1]` using `(rating - 3) / 2`. The script uses EmoBank’s supplied train, development and test assignments. Exact duplicates across splits are removed after trimming text, giving priority to training, then development, then test.

| Split | Sentences used | Purpose |
|---|---:|---|
| Training | 8,062 | Fit Ridge coefficients |
| Development | 975 | Select alpha |
| Test | 981 | Evaluate the selected model |

The original data contained 1,000 development and 1,000 test rows. The split audit removed 25 development and 19 test rows with exact text overlap. The October run selected alpha by development MAE from 0.1, 1, 10 and 100. The fitted model used the training split, with development for model selection and test for final evaluation.

### Integrated test metrics

| Dimension | Ridge MAE | Training-mean baseline MAE | Pearson correlation |
|---|---:|---:|---:|
| Valence | 0.093 | 0.122 | 0.69 |
| Activity | 0.083 | 0.095 | 0.49 |
| Dominance | 0.071 | 0.078 | 0.43 |

MAE is mean absolute error on the normalised scale. The baseline predicts the training-set mean for each dimension. Pearson correlation measures association between predictions and reference ratings.

Nuno reported a maximum absolute change of **0.0** for valence and activity over the 981 test sentences after adding dominance. Ridge fits separate coefficients for each target at the same alpha, which remained 100. The new development mean MAE of **0.0807** averages V, A and D. The earlier **0.0859** averages V and A. Use the per-dimension test results in the group report.

### Original two-output benchmark

These figures come from the October training run, when Ridge predicted valence and activity. They provide the detailed development results and unrounded test values for the prototype.

| Measure | Development | Test |
|---|---:|---:|
| Valence MAE | 0.090463 | 0.093220 |
| Activity MAE | 0.081406 | 0.082965 |
| Mean MAE across valence and activity | 0.085935 | 0.088092 |
| Valence Pearson correlation | 0.690264 | 0.686094 |
| Activity Pearson correlation | 0.545392 | 0.486021 |

The original training-mean baseline had a test mean MAE of 0.108464. The prototype reduced that error by approximately 18.8%. Use the integrated per-dimension table above for the group report.

## 3. Cross-platform fingerprint fix

Previously, `model_fingerprint()` used operating-system-specific path separators and ordering when hashing the encoder files. As a result, an encoder and regressor that worked on Windows could fail the integrity check on macOS or vice versa. Finder could also introduce a `.DS_Store` file into `engine/models/text/encoder/` and change the fingerprint.

The new implementation uses relative paths with `/` separators, sorts those paths as text and excludes OS metadata entries `.DS_Store`, `._*`, `__MACOSX`, `Thumbs.db` and `desktop.ini`. The change applies to both `engine/train_regressor.py` and `engine/text_estimator.py` so training and inference use the same fingerprint algorithm. Nuno retrained the bundle to store the new fingerprint. Commit `4bfe7c3` also disables Git line-ending conversion for files under `engine/models/` and `engine/data/`, preserving the bytes of the model and dataset on checkout. Use the updated bundle with the matching encoder directory.

## 4. API and project files

`TextEstimator.estimate(text)` returns `raw_valence`, `raw_activity`, `raw_dominance` and `flags`. Topic 2 computes confidence and uses dominance as an additional cue when separating anger from sadness.

Example usage from the repository root.

```python
from engine.text_estimator import TextEstimator

estimator = TextEstimator()
result = estimator.estimate("Great, another delay. Really great.")
valence = result["raw_valence"]
activity = result["raw_activity"]
dominance = result["raw_dominance"]
flags = result["flags"]
```

The three raw scores are already on the `[-1, 1]` scale. Topic 2 receives the per-message outputs and computes conversation state, labels and confidence.

| Path | Contents |
|---|---|
| `engine/text_estimator.py` | Loads and checks the encoder and Ridge bundle, produces the three scores and applies the sarcasm flag |
| `engine/models/text/encoder/` | Saved DistilBERT encoder, tokenizer and pooling configuration |
| `engine/models/text/regressor.joblib` | Fitted three-output Ridge model with fingerprint metadata |
| `engine/train_regressor.py` | Training, model selection and evaluation |
| `engine/results/text/test_predictions.csv` | Per-sentence predictions, including `true_dominance` and `pred_dominance` |
| `engine/results/text/metrics.json` | Model settings, split audit and benchmark metrics |
| `tests/test_contract.py` | Group interface contract tests |

## 5. Running and verification

Nuno reported testing the change on Windows. The code and saved metrics here were checked against commit `4bfe7c3`. The repository README specifies Python 3.13 and provides a Google Drive link for `model.safetensors`. Before running the text contract tests, place that file at `engine/models/text/encoder/model.safetensors` and install the packages from `requirements.txt`. Run the tests from the repository root:

```bash
python tests/test_contract.py
```

On 14 November 2026, the text model loaded on Salim’s MacBook Air M3 and all three contract tests passed in 27.473 seconds. The terminal output did not display the Mac checkout’s commit hash. The contract tests verify interface behaviour. The EmoBank evaluation measures prediction error and correlation on labelled benchmark text.

The October prototype also passed three contract tests on 30 October 2026 after the sarcasm flag was integrated. The scenario observations below came from that prototype's GUI.

To use the shared GUI, run `python run_app.py` from the repository root after following the README setup. Once the local encoder files and matching regressor are in place, the estimator can load the saved bundle for inference. `engine/train_regressor.py` is the training entry point. Running it can regenerate the fitted regressor and evaluation outputs, so preserve the recorded results if reproducing training in a working copy.

## 6. October prototype checks

The following results come from the original two-output prototype and the logs dated 30 October 2026. They show how the estimator responded to individual messages before the group integrated the conversation state and policy.

### 6.1 Targeted text checks

| Check | Observed behaviour |
|---|---|
| “I am happy with my order.” vs “I am not happy with my order.” | Valence changes from approximately +0.154 to -0.135. |
| “The service is bad.” vs “The service is not bad.” | Valence shifts from approximately -0.245 to -0.014. |
| “I am disappointed with the delay.” vs “I am extremely disappointed with the delay.” | Activity rises from approximately +0.036 to +0.059; valence changes from -0.141 to -0.139, failing to become more negative. |
| “Great, another delay. Really great.” | Valence is approximately +0.019, activity +0.152, and `possible_sarcasm` appears. The likely negative meaning remains a prediction limitation. |
| “Great, you fixed the delay.” | Valence is approximately +0.063, activity +0.043, and `possible_sarcasm` is absent. |

These negation examples are encouraging but do not demonstrate general negation competence. Emotional strength is inconsistent. Sarcasm is not reliably interpreted. Predictions on several customer examples cluster near neutral; do not enlarge them simply to make points look more dramatic on the map.

### 6.2 Professor scenarios M1–M4 and P1–P4

The eight logs contain 28 messages. The preview logged `label="unmapped"`, `confidence=0.0` and `action="ANSWER"` as placeholders. Each table records the original per-message valence, activity and sarcasm cue. The scenarios were qualitative checks. The available logs contain no reference V/A ratings from which to compute scenario MAE or an accuracy rate.

#### M1 — Calm customer with simple questions

Source log: `BASELINE_M1_SESSION.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | Hi, how long does delivery usually take? | +0.012 | +0.030 | Absent |
| 2 | Thanks. And can I change my delivery address? | +0.008 | -0.034 | Absent |
| 3 | Perfect, that is all I needed. Thank you! | +0.282 | +0.288 | Absent |

The two factual questions receive near-neutral predictions. The final appreciative message has more positive valence (+0.282) and activity (+0.288). These are plausible observations for these examples, rather than evidence of a calibrated calm/joy label. No sarcasm cue is raised. Delivery advice, address changes and positive closure still require the response policy.

#### M2 — Frustration that grows over the conversation

Source log: `session_20261030_144736.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | Hi, my order 4821 has not arrived yet. | -0.014 | +0.034 | Absent |
| 2 | It was supposed to be here three days ago. | -0.008 | +0.028 | Absent |
| 3 | Nobody has answered my two emails. This is really frustrating. | -0.214 | +0.131 | Absent |
| 4 | This is unacceptable! I want my money back!! | -0.209 | +0.430 | Absent |
| 5 | I am furious. I will contact a lawyer if this is not solved today. | -0.229 | +0.141 | Absent |

The first two messages score near neutral; the final three have negative valence. Activity peaks at turn 4 (+0.430), then drops to +0.141 for the message containing “furious”. Activation does not follow a steadily increasing frustration trajectory. Individual-message predictions do not incorporate conversation history. The decision component must track state and recognise refund/escalation intent independently of emotional scores. No sarcasm cue is raised.

#### M3 — Explicit requests that must not be missed

Source log: `BASELINE_M3_SESSION.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | Can you tell me how to return a product? | +0.085 | +0.017 | Absent |
| 2 | I do not want to talk to a bot, please connect me with a human agent. | -0.203 | +0.042 | Absent |
| 3 | Thank you, but if this is not fixed I will go to the consumer protection authority. | -0.063 | +0.021 | Absent |

The human-agent request has negative valence (-0.203), while the consumer-protection statement is only slightly negative (-0.063). Both still receive the preview ANSWER action, without request-specific flags. In this prototype run, both turns used the placeholder action. The example shows why explicit human requests and escalation intent need their own signals even when the text affect is mild. No sarcasm cue is raised.

#### M4 — Ambiguous, sarcastic and non-English messages

Source log: `BASELINE_M4_SESSION.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | ok | +0.052 | +0.012 | Absent |
| 2 | whatever, do what you want | +0.055 | +0.085 | Absent |
| 3 | Great, another delay. Really great. | +0.019 | +0.152 | Present |
| 4 | It is not bad, thanks. | +0.048 | +0.009 | Absent |
| 5 | Obrigado, ficou tudo resolvido. | +0.079 | +0.018 | Absent |

The ambiguous expressions remain near neutral; “whatever, do what you want” does not clearly represent possible annoyance or resignation. The sarcastic delay message raises possible_sarcasm, but its valence remains slightly positive (+0.019). “It is not bad, thanks” scores slightly positive (+0.048), a plausible reading. The Portuguese message receives numbers (+0.079, +0.018), but these do not establish Portuguese support: the English-only component neither flags unsupported language nor abstains. These October results identify ambiguity and unsupported-language handling as areas to check in the integrated system.

#### P1 — Neutral refund request

Source log: `NEUTRAL_REFUND.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | Hello, I would like to know how refunds work. | +0.082 | +0.017 | Absent |
| 2 | I bought a keyboard last week, can I return it? | +0.048 | +0.020 | Absent |
| 3 | Understood, thanks. | +0.140 | +0.022 | Absent |

The two refund/return questions are close to neutral. The final acknowledgement is more positive (+0.140), with activity close to the midpoint (+0.022). No sarcasm cue is raised. These predictions are plausible for the examples; the preview does not actually explain refunds or returns.

#### P2 — Disappointed and tired customer

Source log: `P2_DIAPPOINTED_AND_TIRED_CUSTOMAR.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | I am really disappointed with my last order. | -0.181 | +0.080 | Absent |
| 2 | I am tired of waiting for the replacement. | -0.156 | +0.031 | Absent |
| 3 | I do not think it will ever arrive. | -0.113 | +0.032 | Absent |

All three messages have negative valence. Activity stays slightly above zero (+0.080, +0.031, +0.032), so low activation associated with tiredness is not clearly represented. “Tired of waiting” can also express frustration rather than physical tiredness; without reference ratings, the required activity value is not uniquely established. No sarcasm cue is raised.

#### P3 — Anxious about a payment

Source log: `P3_Anxious about a payment.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | I am worried my payment failed. | -0.137 | +0.055 | Absent |
| 2 | I am scared the money is gone and the order disappeared! | -0.176 | +0.248 | Absent |
| 3 | Please help me, I do not know what to do. | -0.315 | +0.142 | Absent |

All messages have negative valence. The scared/exclamatory message is more activated (+0.248) than the worried message (+0.055), while the final plea has the most negative valence (-0.315). These are plausible differences, but wording, length and punctuation also change, so this is not a controlled causal test of anxiety or intensity. No sarcasm cue is raised. The preview logged the affect scores alongside its placeholder action and label.

#### P4 — Negation and praise

Source log: `P4 - Negation and praise.txt`.

| Turn | Input | Valence | Activity | Sarcasm cue |
|---|---|---:|---:|---|
| 1 | The delivery was not bad. | -0.039 | -0.043 | Absent |
| 2 | I am not happy at all with the packaging. | -0.024 | +0.037 | Absent |
| 3 | Still, the support team was great, thank you. | +0.201 | +0.095 | Absent |

The praise receives positive valence (+0.201). “The delivery was not bad” is near neutral and slightly negative (-0.039); it does not clearly capture a mildly positive reading. More notably, “I am not happy at all with the packaging” receives only -0.024 valence, underrepresenting its likely dissatisfaction. This limits the encouraging results on other negation examples: negation handling does not generalise reliably across phrasing. No sarcasm cue is raised.

### 6.3 Findings and limitations

- **Negation and emphasis.** The paired examples show sensitivity to some changes in wording. In P4, “I am not happy at all with the packaging” received only −0.024 valence, which underrepresents the likely dissatisfaction.
- **Activity across turns.** In M2, activity peaked at +0.430 on the refund demand and fell to +0.141 on the “furious” message. These are estimates for individual turns and do not describe a tracked conversation trajectory.
- **Sarcasm and language.** M4 contained the only sarcasm cue across the 28 messages. Its valence still scored slightly positive. The Portuguese message received scores, which offers one observation from an English model and leaves Portuguese performance unverified.
- **Benchmark scope.** EmoBank measures performance against human ratings on general English text. The NovaShop scenarios show behaviour on individual customer-service examples. A representative, labelled customer-service evaluation would be needed to quantify performance in that domain.

## 7. Sources and evidence

- October Topic 1 documentation, original training metrics and the eight scenario log filenames recorded in section 6.
- Nuno Araújo’s update on the fingerprint fix, dominance and the integrated test metrics. The code and saved metrics were checked against commit `4bfe7c3` during the earlier verification recorded above.
- Buechel and Hahn (2017), [EmoBank](https://aclanthology.org/E17-2092/) and the [official dataset repository](https://github.com/JULIELab/EmoBank).
- [DistilBERT model card](https://huggingface.co/distilbert/distilbert-base-uncased).

## 8. AI log

I used ChatGPT to compare ways of estimating emotion from text, suggest test sentences and help me set up the project on macOS.

| What I asked ChatGPT | How I used the guidance | How I checked it |
|---|---|---|
| How can I estimate affect scores from customer messages? | I used the explanation to understand how a frozen DistilBERT encoder and Ridge regression work together. | I checked the held-out EmoBank results against the training-mean baseline. |
| How can I test negation, emphasis and sarcasm? | I used example sentences to compare wording such as “bad” and “not bad”, and to probe the `possible_sarcasm` flag. | I inspected the scores and flags produced by the estimator. |
| How do I run the project checks on my Mac? | I followed setup guidance and ran `python tests/test_contract.py`. | All three contract tests passed on my Mac. |
