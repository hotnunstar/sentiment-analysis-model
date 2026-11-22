# Topic 3 — Decision Policy, State Over Time and Robustness

---

## 1. Responsibilities and Scope of Topic 3

Topic 3 sits between affective state estimation (Topic 2) and user-facing response formatting (Topic 4). Once Topic 1 extracts text and voice cues and Topic 2 filters them into a smoothed 3D affective state, `engine/engine.py` decides what the assistant should do next and produces the reply text.

Specifically, this module covers four jobs:

1. **Action selection:** Mapping the smoothed 3D state (`valence`, `activity`, `dominance`), discrete emotion `label`, calibrated `confidence`, vocal cues, and normalized text onto six standardized actions (`ANSWER`, `ANSWER_EMPATHIC`, `ASK_CLARIFICATION`, `OFFER_HUMAN`, `ESCALATE`, `CLOSE_POSITIVE`).
2. **Multi-turn state tracking:** Counting consecutive frustrated turns in `frustration_streak` so the assistant treats a single delayed-order remark differently from three turns of mounting dissatisfaction.
3. **Intent and risk precedence:** Enforcing explicit customer requests (human agent or refund) and legal or regulatory threats ahead of statistical emotion predictions.
4. **Input robustness:** Handling clause-level negation, contraction expansion, Unicode diacritic folding, single-word fillers, short polite acknowledgements, sarcasm flags, low-confidence anger fallbacks, voice-only anger or frustration overrides, broken-audio fallbacks, bilingual (English and Portuguese) FAQ routing, and guarded closure.

Topic 3 does not touch model weights, acoustic extractors, or Kalman filter parameters from Topics 1 and 2. It reads the structured dictionary returned by `AffectiveState.update()` and outputs an action, a localized reply, and diagnostic fields for logging and Topic 4.

---

## 2. Repository Files Owned, Modified, and Unchanged

| File | Status | Owner | Role in the System |
| :--- | :--- | :--- | :--- |
| `engine/engine.py` | **MODIFIED** | Topic 3 | Implements `Engine`, text normalization, clause-level negation, multi-turn `frustration_streak`, the 11-step priority policy, voice overrides and fallbacks, bilingual FAQ replies, and 3D `dominance` output |
| `engine/text_estimator.py` | **UNCHANGED** | Topic 1 (Text) | Predicts raw text `valence`, `activity`, `dominance`, and sets `possible_sarcasm` |
| `engine/voice_estimator.py` | **UNCHANGED** | Topic 1 (Voice) | Runs frozen `emotion2vec_base` + logistic regression to output six voice emotion probabilities |
| `engine/acoustic_features.py` | **UNCHANGED** | Topic 2 (Voice) | Computes framing, windowing, FFT power spectrum, Mel filterbank, MFCCs, pitch, loudness, and spectral flatness |
| `engine/voice_affect.py` | **UNCHANGED** | Topic 2 (Voice) | Maps voice probabilities to NRC VAD valence/dominance, estimates speaker-invariant prosodic activity, and computes noise factors |
| `engine/affective_state.py` | **UNCHANGED** | Topic 2 | Runs Kalman state filtering across `valence`, `activity`, and `dominance`, fuses text and audio, maps 3D V/A/D labels, and calibrates confidence |

---

## 3. Standardized Action Space (`Engine.ACTIONS`)

`Engine.ACTIONS` defines six mutually exclusive actions that govern how the assistant behaves on each turn:

| Action | Trigger Conditions | Conversational Objective | Downstream Guidance (Topic 4) |
| :--- | :--- | :--- | :--- |
| `ANSWER` | Neutral, mildly positive, or polite short acknowledgement messages when no higher-priority rule fires | Provide accurate, question-aware FAQ information or general help | Render direct, informative answer text without unnecessary apology framing |
| `ANSWER_EMPATHIC` | Early frustration (`streak` 1–2), fused `frustration` or `sadness`, low-confidence `anger` (`< 0.40`), or neutral text paired with angry/frustrated voice tone | Acknowledge customer frustration or distress empathetically while moving toward a fix | Use a supportive, de-escalating tone before presenting troubleshooting steps |
| `ASK_CLARIFICATION` | Empty input, ambiguous single-word or dismissive fillers (`"ok"`, `"whatever"`), unknown `<= 2`-word low-confidence turns, or `possible_sarcasm` | Avoid misreading vague, ironic, or underspecified messages | Ask the user politely to clarify their intent without assuming resolution |
| `OFFER_HUMAN` | Explicit request for a human agent, explicit refund/reimbursement request, or sustained frustration (`frustration_streak >= 3`) | Hand off smoothly from automated support to a live specialist | Trigger human handoff workflow or display agent-transfer confirmation |
| `ESCALATE` | Explicit legal/regulatory threat or high-confidence `anger` (`confidence >= 0.40`) | Flag high-risk or severely escalated cases immediately for senior human review | Route with a high-priority escalation flag and avoid further automated questioning |
| `CLOSE_POSITIVE` | Explicit unnegated resolution/closure phrase with zero question marks and zero unresolved request patterns | Confirm resolution warmly and close the support session | Display closing confirmation and mark the dialogue session as resolved |

---

## 4. Decision Policy and Priority Hierarchy (`Engine._decide`)

`Engine._decide()` runs top to bottom as a deterministic rule chain. Safety risks, explicit user requests, and ambiguity guards sit at the top so noisy classifier outputs cannot override clear customer intent.

### Step by Step Priority Order

1. **Priority 1 — Legal and Regulatory Concerns (`ESCALATE`):**
   `_is_legal_signal(normalized_text)` checks 27 unnegated English and Portuguese patterns covering lawyers, courts, lawsuits, regulators, ombudsmen, formal complaints, and consumer protection bodies (such as `"lawyer"`, `"solicitor"`, `"attorney"`, `"legal action"`, `"consumer protection"`, `"consumer authority"`, `"trading standards"`, `"regulator"`, `"ombudsman"`, `"formal complaint"`, `"small claims"`, `"court"`, `"sue"`, `"autoridade de defesa do consumidor"`, `"defesa do consumidor"`, `"livro de reclamacoes"`, `"advogado"`, `"acao judicial"`, and `"queixa formal"`). Any unnegated hit returns `ESCALATE` immediately.

2. **Priority 2 — Explicit Human Assistance Requests (`OFFER_HUMAN`):**
   `_is_human_request(normalized_text)` checks 17 unnegated patterns for requests to speak, chat, or transfer to a human agent, advisor, representative, supervisor, manager, or team member. It also catches bot refusals (`"do not want to talk to a bot"`, `"not a bot"`) and Portuguese equivalents (`"quero falar com um humano"`, `"assistente humano"`, `"operador humano"`), returning `OFFER_HUMAN`.

3. **Priority 3 — Refund and Financial Reimbursement Requests (`OFFER_HUMAN`):**
   `_is_refund_request(normalized_text)` matches 14 unnegated patterns (`"refund"`, `"reimburse"`, `"reimbursement"`, `"money back"`, `"money returned"`, `"return my money"`, `"credit back"`, `"chargeback"`, `"cancel and refund"`, `"reembolso"`, `"devolucao do dinheiro"`, `"quero o meu dinheiro"`). Automated replies cannot issue financial refunds, so these turns route straight to `OFFER_HUMAN`.

4. **Priority 4 — Possible Sarcasm Detection (`ASK_CLARIFICATION`):**
   `_is_sarcastic_or_uncertain(flags)` checks whether `"possible_sarcasm"` is in `state["flags"]`. Ironic remarks like `"Great, another delay. Really great."` carry positive surface words, so the engine asks for clarification instead of replying cheerfully.

5. **Priority 5 — Guarded Conversation Closure (`CLOSE_POSITIVE`):**
   Closure requires an unnegated match in `_is_closure(normalized_text)` (across 20 patterns such as `"that is all i needed"`, `"that is everything"`, `"issue is resolved"`, `"problem solved"`, `"we are all set"`, `"no more questions"`, `"ficou tudo resolvido"`, `"esta resolvido"`) **and** `not _has_unresolved_request(normalized_text)`. If a question mark or pending request remains, closure does not fire.

6. **Priority 6 — Input Ambiguity and Short-Utterance Guard (`ASK_CLARIFICATION`):**
   `_is_ambiguous(text, confidence)` returns `True` when the cleaned text has `0` words or matches `AMBIGUOUS_PHRASES` (`"ok"`, `"fine"`, `"whatever"`, `"do what you want"`, `"hmm"`, `"tanto faz"`, etc.). Polite confirmations in `SHORT_ACKNOWLEDGEMENTS` (`"thanks"`, `"understood, thanks"`, `"got it"`, `"ok thanks"`, `"obrigado"`, etc.) return `False` and proceed normally; any other utterance with `len(words) <= 2` and `confidence < 0.40` returns `True` and triggers `ASK_CLARIFICATION`.

7. **Priority 7 — Anger Escalation with Low-Confidence Safety Fallback (`ESCALATE` / `ANSWER_EMPATHIC`):**
   When `label == "anger"`, the policy compares `confidence` against `CONFIDENCE_THRESHOLD` (`0.40`). High-confidence anger (`confidence >= 0.40`) triggers `ESCALATE`, while low-confidence anger (`confidence < 0.40`) falls back to `ANSWER_EMPATHIC` so an angry customer on a short utterance receives immediate empathy rather than a clarification prompt or premature escalation.

8. **Priority 8 — Sustained Multi-Turn Frustration (`OFFER_HUMAN`):**
   Once `frustration_streak >= FRUSTRATION_STREAK_LIMIT` (`3` consecutive turns), the assistant proactively offers human handoff (`OFFER_HUMAN`).

9. **Priority 9 — Developing Frustration (`ANSWER_EMPATHIC`):**
   On turns `1` or `2` of a frustration sequence (`frustration_streak > 0`), the policy selects `ANSWER_EMPATHIC` to de-escalate early before frustration builds further.

10. **Priority 10 — Negative Affective State and Voice-Only Emotion Override (`ANSWER_EMPATHIC`):**
    If `label` is `"frustration"` or `"sadness"`, the assistant responds with `ANSWER_EMPATHIC`. The same action applies when multimodal fusion leaves `label == "neutral"` but the voice-only classifier (`voice_only_label`) detects `"anger"` or `"frustration"`.

11. **Priority 11 — Default Informative Response (`ANSWER`):**
    When none of Priorities 1–10 apply, the engine selects `ANSWER` and generates a bilingual, question-aware FAQ reply.

---

## 5. State Over Time — Multi-Turn Frustration Tracking

Evaluating each turn in isolation misses slow escalation when a customer starts out polite and loses patience across several messages. `Engine` solves this by maintaining `self.frustration_streak` across consecutive `Engine.process()` calls:

| Turn Condition | Formula / Rule | Effect on `frustration_streak` | Policy Impact |
| :--- | :--- | :--- | :--- |
| Explicit frustration or delay signal detected | `_is_frustration_signal(normalized_text) == True` | `frustration_streak += 1` | `ANSWER_EMPATHIC` on turns 1–2; `OFFER_HUMAN` at `>= 3` |
| Affective state predicts `frustration` or `anger` with sufficient confidence | `label in {"frustration", "anger"} and confidence >= 0.40` | `frustration_streak += 1` | `ANSWER_EMPATHIC` on turns 1–2; `OFFER_HUMAN` at `>= 3` |
| Neither explicit frustration nor confident negative emotion present | `explicit_frustration == False and affective_frustration == False` | `frustration_streak = 0` | Streak resets cleanly when tension subsides |
| New conversation started | `Engine.reset()` invoked | `frustration_streak = 0` | Resets both Topic 2 `AffectiveState` and Topic 3 streak |

### Integration with Topic 2's 3D Affective Model

- **3D Valence, Activity, and Dominance:** Topic 2 tracks three continuous dimensions (`valence`, `activity`, `dominance`), using high dominance to separate `anger` from low-dominance `sadness`. Topic 3 forwards `dominance` in its top-level return dictionary (`"dominance": float(state.get("dominance", 0.0))`)—enabling the 3D view in the interface—and routes `sadness` to `ANSWER_EMPATHIC` in Priority 10 without incrementing the anger/frustration escalation streak.
- **Calibrated Confidence Semantics:** In Topic 2, `confidence` represents the posterior probability of the chosen label, meaning a clearly neutral message routinely scores `0.50–0.65`. Accordingly, `CONFIDENCE_THRESHOLD = 0.40` is never applied as a blanket filter on neutral messages; it only gates low-confidence anger fallback (Priority 7), short utterance ambiguity (Priority 6), and affective frustration streak increments, while explicit delay or complaint phrases increment the streak immediately via `explicit_frustration`.

---

## 6. Linguistic Robustness and Safeguards

### Text Normalisation Pipeline (`Engine._normalize_text`)

Every incoming string goes through four normalization steps before regex matching:

1. **Case and whitespace normalisation:** Lowercases the text and strips leading and trailing whitespace.
2. **Apostrophe standardisation:** Replaces curly quotes (`’`, `‘`) with straight ASCII apostrophes (`'`).
3. **Contraction expansion (`Engine.CONTRACTIONS`):** Expands 35 common English contractions (`"can't"` -> `"cannot"`, `"couldn't"` -> `"could not"`, `"don't"` -> `"do not"`, `"doesn't"` -> `"does not"`, `"didn't"` -> `"did not"`, `"won't"` -> `"will not"`, `"wouldn't"` -> `"would not"`, `"isn't"` -> `"is not"`, `"haven't"` -> `"have not"`, `"i'm"` -> `"i am"`, `"it's"` -> `"it is"`, etc.) so negated auxiliaries are explicit tokens.
4. **Unicode diacritic folding (`NFKD`):** Decomposes accented characters and strips combining marks so Portuguese inputs match consistently regardless of accentuation (e.g., `"não"` -> `"nao"`, `"devolução"` -> `"devolucao"`, `"ação"` -> `"acao"`).

### Clause-Level Negation Guard (`Engine._has_negation_before`)

Every regex hit across `LEGAL_PATTERNS`, `HUMAN_REQUEST_PATTERNS`, `REFUND_PATTERNS`, `FRUSTRATION_PATTERNS`, and `CLOSURE_PATTERNS` passes through `_is_unnegated_match()`. The reason of why check only the local clause instead of the entire sentence is that a sentence-wide scan would suppress a valid request in a second clause after a comma. Instead, `_has_negation_before(text, match.start())` splits `text[:match_start]` at punctuation boundaries (`[.!?;:,]`), takes the active clause (`clause_parts[-1]`), and checks the **5 words immediately preceding the match** (`preceding_words[-5:]`) against `NEGATION_WORDS` (`"not"`, `"no"`, `"never"`, `"cannot"`, `"nao"`, `"nunca"`, `"jamais"`, etc.).

| Example Customer Message | Normalization & Clause Analysis | Policy Result |
| :--- | :--- | :--- |
| `"I want a refund"` | Unnegated match on `\brefund\b` | `OFFER_HUMAN` |
| `"I don't want a refund"` | Expands to `"i do not want a refund"`; `"not"` found within 5 words | Negated — suppressed |
| `"I don't want a refund, please connect me to an agent"` | Comma splits clause 1 (`"i do not want a refund"`) from clause 2 (`"please connect me to an agent"`) | Clause 2 triggers `OFFER_HUMAN` |
| `"It is not bad, thanks."` | No negative trigger; polite acknowledgement | `ANSWER` |

### Short Acknowledgements vs. Ambiguous Fillers

Topic 2 caps confidence at `0.35` on text-only messages of two words or fewer. Without an explicit whitelist, polite confirmations like `"Got it"` or `"Understood, thanks."` would be misclassified as ambiguous and trigger `"Could you clarify what you mean?"`. `_is_ambiguous()` separates them cleanly:

- **`SHORT_ACKNOWLEDGEMENTS` (41 English & Portuguese phrases -> `ANSWER`):** Includes `"thanks"`, `"thank you"`, `"thanks a lot"`, `"appreciate it"`, `"understood"`, `"understood thanks"`, `"understood thank you"`, `"got it"`, `"got it thanks"`, `"ok got it"`, `"ok thanks"`, `"okay thanks"`, `"alright thanks"`, `"all good"`, `"sounds good"`, `"makes sense"`, `"fair enough"`, `"will do"`, `"noted"`, `"great thanks"`, `"perfect thanks"`, `"obrigado"`, `"obrigada"`, `"muito obrigado"`, `"entendido"`, and `"ok obrigado"`.
- **`AMBIGUOUS_PHRASES` (22 English & Portuguese fillers -> `ASK_CLARIFICATION`):** Includes `"ok"`, `"okay"`, `"fine"`, `"whatever"`, `"sure"`, `"hmm"`, `"hm"`, `"right"`, `"yeah"`, `"yes"`, `"no"`, `"maybe"`, `"whatever you want"`, `"do what you want"`, `"whatever do what you want"`, `"tanto faz"`, `"pronto"`, `"esta bem"`, `"ta bem"`, `"sim"`, and `"nao"`.
- **Short low-confidence fallback:** Any unrecognized utterance of `<= 2` words with `confidence < 0.40` also routes to `ASK_CLARIFICATION`.

### Guarded Conversation Closure (`Engine._is_closure` & `Engine._has_unresolved_request`)

Positive affect (`joy` or `calm`) never triggers `CLOSE_POSITIVE` on its own. Closure requires an unnegated match in `CLOSURE_PATTERNS` (`"that is all i needed"`, `"that is all"`, `"that is everything"`, `"nothing else needed"`, `"problem solved"`, `"issue is resolved"`, `"we are all set"`, `"no more questions"`, `"ficou tudo resolvido"`, `"esta tudo resolvido"`) plus `not _has_unresolved_request(normalized_text)`, which checks that the message has no `?` and no pending request phrase (`"can you"`, `"could you"`, `"would you"`, `"will you"`, `"please"`, `"i need you to"`, `"i still need"`, `"i also need"`, `"can i"`, `"could i"`, `"what about"`, `"how about"`, `"mas pode"`, `"pode ajudar"`, `"preciso de"`, `"quero saber"`).

---

## 7. Multimodal Voice Integration and Fault Tolerance

`Engine.process()` forwards `audio_path` directly to Topic 2 on every turn:

```python
raw_estimate = self.text_estimator.estimate(text)
state = self.affective_state.update(
    text,
    raw_estimate,
    audio_path=audio_path,
)
```

### Voice-Only Empathy Override

When a recording sounds angry or frustrated while the typed text is neutral (for instance, `"Here is my message."` or `"Where is my package?"`), Topic 2's Kalman fusion can still report a fused `label` of `"neutral"` because text carries higher weight on valence. Topic 3 inspects `state["details"]["voice"]["voice_only"]["label"]`: if `state["label"] == "neutral"` and `voice_only_label in {"anger", "frustration"}`, Priority 10 switches the action from `ANSWER` to `ANSWER_EMPATHIC` and logs `details["voice_empathy_override"] = True`.

### Broken-Audio Fallback Notice

If audio decoding or `emotion2vec` fails on a missing or corrupted file, Topic 2 catches the exception, appends `"voice_processing_failed"` to `state["flags"]`, and keeps the text-based state intact. Topic 3 retains the text-driven action and prepends a localized notice in `Engine._reply()`:

- **English:** `"I couldn't process the audio, so I'm responding based on your message. "`
- **Portuguese:** `"Não foi possível processar o áudio, por isso respondo com base na sua mensagem. "`

---

## 8. Bilingual Question-Aware FAQ and Reply Generation

When `action == "ANSWER"`, `Engine._faq_reply(normalized_text, portuguese)` checks `_is_portuguese()` and matches eight customer support categories so routine inquiries receive concrete answers rather than generic filler:

| Category | Trigger Keywords (EN / PT) | English Response | Portuguese Response |
| :--- | :--- | :--- | :--- |
| **1. Shipping Fees** | `shipping/delivery` + `cost/fee/price/charge/free` | `"Standard shipping is free on orders over €50, and €4.99 for smaller orders."` | `"O envio padrão é gratuito em encomendas acima de 50 € e custa 4,99 € nas restantes encomendas."` |
| **2. Delivery Time** | `delivery`, `shipping`, `arrive`, `ship`, `deliver`, `entrega`, `envio`, `chegar` | `"Standard delivery typically takes 2 to 5 business days. Would you like to share your order number so I can check its status?"` | `"As entregas padrão demoram normalmente entre 2 a 5 dias úteis. Pode partilhar o número da sua encomenda se quiser verificar o estado atual?"` |
| **3. Order Tracking** | `track`, `tracking`, `status`, `where is my order`, `rastreio`, `estado`, `encomenda` | `"You can track your package using the tracking link sent to your email, or share your order number here and I can check it for you."` | `"Pode acompanhar a sua encomenda através do link de rastreio enviado por e-mail, ou indicar o número da encomenda para eu verificar."` |
| **4. Cancellations** | `cancel`, `cancellation`, `cancelar`, `cancelamento` | `"You can cancel your order anytime before it ships from your account page, or share your order number here so I can assist you."` | `"Pode cancelar a sua encomenda antes do envio através da sua conta ou indicando o número da encomenda aqui."` |
| **5. Returns & Exchanges** | `return`, `exchange`, `policy`, `send back`, `devolucao`, `troca`, `politica` | `"We accept returns and exchanges within 30 days of delivery, provided the item is in its original condition."` | `"Aceitamos devoluções e trocas no prazo de 30 dias após a entrega, desde que o artigo esteja nas condições originais."` |
| **6. Payments & Invoices** | `payment`, `pay`, `invoice`, `receipt`, `billing`, `pagamento`, `fatura`, `recibo` | `"We accept credit/debit cards, PayPal, and bank transfers, and your invoice is sent automatically by email after purchase."` | `"Aceitamos pagamentos por cartão de crédito/débito, PayPal e transferência bancária, e a fatura é enviada automaticamente por e-mail."` |
| **7. Support Hours** | `hours`, `open`, `contact`, `support`, `available`, `horario`, `contacto`, `suporte` | `"Our customer support team is available Monday through Friday, from 9:00 AM to 6:00 PM."` | `"O nosso apoio ao cliente está disponível de segunda a sexta-feira, das 9h00 às 18h00."` |
| **8. Greetings & General** | `hello`, `hi`, `hey`, `good morning`, `ola`, `bom dia`, or general statements | `"Hello! How can I help you today?"` / `"Of course! I'm here to help. What would you like to know?"` | `"Olá! Como posso ajudar hoje?"` / `"Claro! Estou aqui para ajudar. Pode dizer-me mais sobre o que precisa?"` |

For the remaining five actions (`ESCALATE`, `OFFER_HUMAN`, `ASK_CLARIFICATION`, `CLOSE_POSITIVE`, `ANSWER_EMPATHIC`), `Engine._reply()` generates dedicated responses matched to the detected language.

---

## 9. Engine Interface and Output Dictionary Contract

### Public Methods

```python
engine = Engine(engine_dir=None)
engine.reset()
result = engine.process(text, audio_path=None, image_path=None)
```

`Engine.reset()` clears `self.affective_state` and sets `self.frustration_streak = 0`. Passing an empty or whitespace-only string to `Engine.process()` returns a baseline neutral dictionary immediately without advancing the Kalman filter (`valence: 0.0`, `activity: 0.0`, `dominance: 0.0`, `confidence: 0.1`, `label: "neutral"`, `action: "ASK_CLARIFICATION"`, `details["reason"] = "empty_input"`).

### Top-Level Output Schema

| Key | Type | Range / Values | Description |
| :--- | :--- | :--- | :--- |
| `valence` | `float` | `[-1.0, 1.0]` | Smoothed pleasure/displeasure score from Topic 2 |
| `activity` | `float` | `[-1.0, 1.0]` | Smoothed emotional arousal score from Topic 2 |
| `dominance` | `float` | `[-1.0, 1.0]` | Smoothed sense of control/dominance from Topic 2 (enables 3D affective view) |
| `confidence` | `float` | `[0.0, 1.0]` | Calibrated probability that `label` is accurate |
| `label` | `str` | `neutral`, `joy`, `calm`, `frustration`, `anger`, `sadness` | Discrete emotion label derived from 3D V/A/D state |
| `action` | `str` | One of `Engine.ACTIONS` | Conversational action selected by Topic 3 |
| `reply` | `str` | Non-empty `str` | Generated response text (including audio-failure notice if applicable) |
| `flags` | `list[str]` | e.g., `possible_sarcasm`, `voice_processing_failed` | Active diagnostic flags from Topics 1 and 2 |
| `details` | `dict` | Nested metadata | Combined Topic 2 state details and Topic 3 policy diagnostics |

### Diagnostic Metadata Keys Added to `details` by this topic (Topic 3)

| Key | Type | Description |
| :--- | :--- | :--- |
| `frustration_streak` | `int` | Consecutive turns with explicit or confident affective frustration |
| `frustration_streak_limit` | `int` | Threshold (`3`) triggering `OFFER_HUMAN` for sustained frustration |
| `legal_signal` | `bool` | Whether an unnegated legal/regulatory pattern matched |
| `human_request` | `bool` | Whether an unnegated human-agent request matched |
| `refund_request` | `bool` | Whether an unnegated refund/reimbursement request matched |
| `explicit_frustration` | `bool` | Whether an unnegated frustration or delivery-delay pattern matched |
| `ambiguous_input` | `bool` | Whether the message was classified as ambiguous |
| `possible_sarcasm` | `bool` | Whether `"possible_sarcasm"` was flagged |
| `positive_closure` | `bool` | Whether an unnegated closure pattern matched |
| `unresolved_request` | `bool` | Whether a question mark or unresolved request remained |
| `voice_empathy_override` | `bool` | Whether neutral text was overridden to `ANSWER_EMPATHIC` due to angry/frustrated voice tone |
| `decision_policy` | `str` | Policy identifier (`"topic_3"`) |

---

## 10. Automated Tests and Mandatory Scenario Evaluation

All 15 automated unit and voice tests (`python -m unittest discover tests -v`) and all four mandatory scenarios (`python run_scenario.py`) were executed and verified.

### Automated Test Suite Summary

| Test Suite | Tests Run | Verified Capabilities | Result |
| :--- | :---: | :--- | :---: |
| `tests/test_contract.py` | 3 | `Engine.reset()` state clearing, `Engine.process()` schema/bounds/types (`valence`, `activity`, `dominance`, `confidence`, `label`, `action`, `reply`, `flags`, `details`), and scenario JSON validity | **PASS (3/3)** |
| `tests/test_voice.py` | 12 | Spectral flatness, MFCC framing, Mel scale, pitch invariance, agitation activity scaling, noise measurement variance, `emotion2vec` loading, broken-audio fallback (`test_broken_audio_keeps_the_text_result`), voice contract compliance (`test_contract_holds_with_audio`), and voice state updates | **PASS (12/12)** |

### Scenario M1 — `M1_calm_faq.json` (Calm Customer with Simple Questions)

| Turn | Customer Message | Valence | Activity | Confidence | Label | Selected Action |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `"Hi, how long does delivery usually take?"` | `+0.03` | `+0.09` | `0.61` | `neutral` | `ANSWER` |
| 2 | `"Thanks. And can I change my delivery address?"` | `+0.03` | `-0.06` | `0.64` | `neutral` | `ANSWER` |
| 3 | `"Perfect, that is all I needed. Thank you!"` | `+0.57` | `+0.84` | `0.40` | `calm` | `CLOSE_POSITIVE` |

### Scenario M2 — `M2_growing_frustration.json` (Escalating Frustration Across Turns)

| Turn | Customer Message | Valence | Activity | Confidence | Label | Selected Action |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `"Hi, my order 4821 has not arrived yet."` | `-0.03` | `+0.10` | `0.61` | `neutral` | `ANSWER_EMPATHIC` |
| 2 | `"It was supposed to be here three days ago."` | `-0.03` | `+0.12` | `0.62` | `neutral` | `ANSWER_EMPATHIC` |
| 3 | `"Nobody has answered my two emails. This is really..."` | `-0.44` | `+0.44` | `0.49` | `frustration` | `OFFER_HUMAN` |
| 4 | `"This is unacceptable! I want my money back!!"` | `-0.59` | `+1.00` | `0.76` | `anger` | `OFFER_HUMAN` |
| 5 | `"I am furious. I will contact a lawyer if this is..."` | `-0.70` | `+1.00` | `0.56` | `anger` | `ESCALATE` |

### Scenario M3 — `M3_explicit_requests.json` (Explicit Requests Taking Priority)

| Turn | Customer Message | Valence | Activity | Confidence | Label | Selected Action |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `"Can you tell me how to return a product?"` | `+0.18` | `+0.05` | `0.55` | `neutral` | `ANSWER` |
| 2 | `"I do not want to talk to a bot, please connect m..."` | `-0.36` | `+0.15` | `0.52` | `frustration` | `OFFER_HUMAN` |
| 3 | `"Thank you, but if this is not fixed I will go to..."` | `-0.27` | `+0.12` | `0.50` | `neutral` | `ESCALATE` |

### Scenario M4 — `M4_ambiguity_and_robustness.json` (Ambiguity, Sarcasm, Negation, and Portuguese)

| Turn | Customer Message | Valence | Activity | Confidence | Label | Selected Action |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `"ok"` | `+0.10` | `+0.03` | `0.35` | `neutral` | `ASK_CLARIFICATION` |
| 2 | `"whatever, do what you want"` | `+0.15` | `+0.26` | `0.53` | `neutral` | `ASK_CLARIFICATION` |
| 3 | `"Great, another delay. Really great."` | `+0.11` | `+0.47` | `0.21` | `neutral` | `ASK_CLARIFICATION` |
| 4 | `"It is not bad, thanks."` | `+0.14` | `+0.21` | `0.54` | `neutral` | `ANSWER` |
| 5 | `"Obrigado, ficou tudo resolvido."` | `+0.21` | `+0.14` | `0.52` | `neutral` | `CLOSE_POSITIVE` |

### Edge-Case Verification Matrix

| Test Case | Input / Condition | Verified Behaviour |
| :--- | :--- | :--- |
| **3D Dominance Output** | `e.process("")` and non-empty turns | `"dominance"` key present as `float` (`0.0` on empty input) |
| **Low-Confidence Anger** | `"I am furious with how I have been treated!"` (`anger`, `conf < 0.40`) | Routes safely to `ANSWER_EMPATHIC` |
| **Short Acknowledgement** | `"Understood, thanks."` | Bypasses ambiguity prompt and returns `ANSWER` |
| **Generalized Human Request** | `"Can I please speak to someone from your team?"` | Matches generalized pattern and returns `OFFER_HUMAN` |
| **Generalized Refund Request** | `"I would like my money returned, please."` | Matches generalized pattern and returns `OFFER_HUMAN` |
| **Question-Aware FAQ** | `"How long does delivery take?"` | Returns `ANSWER` containing `"2 to 5 business days"` |

---

## 11. Known Limitations and How to Run

### Known Limitations

1. **Rule based intent and negation matching:** Legal threats, human requests, refund demands, frustration phrases, FAQ routing, and closure rely on curated regular expressions and a 5-word clause-level negation window. Highly indirect phrasing outside those patterns falls back to general replies.
2. **Primary English orientation with targeted Portuguese support:** The text encoder and most regex rules target English. Portuguese coverage handles common greetings, FAQs, frustration expressions, refund or human requests, and closure phrases rather than full Portuguese morphological parsing.
3. **Consecutive-turn streak tracking:** `frustration_streak` counts consecutive frustrated turns and resets on a calm turn rather than maintaining a multi-topic dialogue graph across topic switches.
4. **Empirical confidence threshold:** `CONFIDENCE_THRESHOLD = 0.40` is calibrated to Topic 2's confidence scale and short-text caps rather than trained on a separate dialogue validation corpus.
5. **Image modality placeholder:** `image_path` remains in `Engine.process()` for interface compatibility, while text and voice (`audio_path`) are actively processed.

### Commands for Running and Verifying

1. **To run the complete 15-test unit, contract, and voice test suite:**

```bash
python -m unittest discover tests -v
```

2. **To run all four mandatory evaluation scenarios:**

```bash
python run_scenario.py scenarios/mandatory/M1_calm_faq.json
python run_scenario.py scenarios/mandatory/M2_growing_frustration.json
python run_scenario.py scenarios/mandatory/M3_explicit_requests.json
python run_scenario.py scenarios/mandatory/M4_ambiguity_and_robustness.json
```

3. **To run the automated edge-case verification check:**

```bash
python -c "from engine.engine import Engine; e = Engine(); r0 = e.process(''); assert 'dominance' in r0 and r0['dominance'] == 0.0; e.reset(); r1 = e.process('I am furious with how I have been treated!'); assert r1['action'] == 'ANSWER_EMPATHIC'; e.reset(); r2 = e.process('Understood, thanks.'); assert r2['action'] == 'ANSWER'; e.reset(); r3 = e.process('Can I please speak to someone from your team?'); assert r3['action'] == 'OFFER_HUMAN'; e.reset(); r4 = e.process('I would like my money returned, please.'); assert r4['action'] == 'OFFER_HUMAN'; e.reset(); r5 = e.process('How long does delivery take?'); assert 'business days' in r5['reply']; print('ALL CHECKS PASSED')"
```

---

## 12. AI Usage Log

Gemini / LLM assisted in reviewing Topic 3 decision policy edge cases, bilingual EN/PT regex coverage, and handover documentation structure draftm, all rules in `engine/engine.py` were manually reviewed, tested against mandatory scenarios M1–M4, and verified with the automated contract, voice, and edge-case test suites
