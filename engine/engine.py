import re
import unicodedata

from .text_estimator import TextEstimator
from .affective_state import AffectiveState


class Engine:

    ACTIONS = {
        "ANSWER",
        "ANSWER_EMPATHIC",
        "ASK_CLARIFICATION",
        "OFFER_HUMAN",
        "ESCALATE",
        "CLOSE_POSITIVE",
    }

    FRUSTRATION_STREAK_LIMIT = 3
    CONFIDENCE_THRESHOLD = 0.40

    LEGAL_PATTERNS = [
        r"\blawyer\b",
        r"\bsolicitor\b",
        r"\battorney\b",
        r"\blegal action\b",
        r"\btake legal action\b",
        r"\blegal advice\b",
        r"\blegal counsel\b",
        r"\blegal team\b",
        r"\bconsumer protection\b",
        r"\bconsumer authority\b",
        r"\bconsumer rights\b",
        r"\btrading standards\b",
        r"\bregulator(y)?\b",
        r"\bombudsman\b",
        r"\b(file|make|lodge|submit)\s+a\s+(formal\s+)?complaint\b",
        r"\bformal complaint\b",
        r"\bcomplaint to (the )?authorities\b",
        r"\breport (you|this|the company) to\b",
        r"\bsmall claims\b",
        r"\b(go to |take this to )?court\b",
        r"\bsue\b",
        r"\bautoridade de defesa do consumidor\b",
        r"\bdefesa do consumidor\b",
        r"\blivro de reclamacoes\b",
        r"\badvogado\b",
        r"\bacao judicial\b",
        r"\bqueixa formal\b",
    ]

    HUMAN_REQUEST_PATTERNS = [
        r"\b(speak|talk|chat)\s+(to|with)\s+(a\s+)?(human|person|real\s+person|live\s+agent|agent|representative|advisor|specialist|supervisor|manager|someone)\b",
        r"\b(connect|transfer|put|pass|hand|route|escalate)\s+(me|this|my\s+case)\s+(over\s+|through\s+)?(to|with)\s+(a\s+)?(human|person|real\s+person|agent|representative|advisor|supervisor|manager|someone)\b",
        r"\b(get|give|find)\s+(me\s+)?(a\s+)?(human|real\s+person|live\s+agent|representative|agent)\b",
        r"\bis there (a\s+)?(human|real\s+person|live\s+agent|someone)\b",
        r"\b(human|live)\s+(agent|support|assistance|representative|person|operator|staff)\b",
        r"\b(want|need|prefer|would like)\s+(to\s+(speak|talk|chat)\s+(to|with)\s+)?(a\s+)?(human|person|real\s+person|live\s+agent|representative|someone)\b",
        r"\b(anyone|someone)\s+(i\s+can\s+|to\s+)(speak|talk|chat)\s+(to|with)\b",
        r"\bnot\s+(a\s+)?(bot|robot|ai|machine|automated)\b",
        r"\bdo not want to talk to a bot\b",
        r"\bdont want to talk to a bot\b",
        r"\bsomeone from (your )?(team|support|staff|company|department)\b",
        r"\bcustomer (service|support) (agent|representative|person|team)\b",
        r"\bquero falar com (uma pessoa|um humano|um agente|alguem)\b",
        r"\bfalar com (uma pessoa|um humano|um agente|alguem)\b",
        r"\bassistente humano\b",
        r"\boperador humano\b",
        r"\btransfira me\b",
    ]

    REFUND_PATTERNS = [
        r"\brefund\b",
        r"\breimburse\b",
        r"\breimbursement\b",
        r"\bmoney back\b",
        r"\bmoney returned\b",
        r"\b(return|refund)\s+(all\s+|the\s+|my\s+)?(money|payment|amount|funds)\b",
        r"\b(get|give)\s+(me\s+)?my\s+money\s+back\b",
        r"\bcredit back\b",
        r"\bchargeback\b",
        r"\bcancel and refund\b",
        r"\breembolso\b",
        r"\bdevolucao do dinheiro\b",
        r"\bdevolver o dinheiro\b",
        r"\bquero o meu dinheiro\b",
    ]

    FRUSTRATION_PATTERNS = [
        r"\bfrustrat(ed|ing|ion)\b",
        r"\b(this is |that is |completely |totally |simply )?(unacceptable|ridiculous|absurd|pathetic|useless)\b",
        r"\b(terrible|horrible|awful|worst|poor|bad)\s+(service|experience|support|delivery)\b",
        r"\b(very|extremely|really|deeply|so)\s+disappointed\b",
        r"\bdisappointing\b",
        r"\b(no one|nobody)\s+(has\s+)?(helped|answered|replied|responded|got back)\b",
        r"\bno (response|reply|answer|update)\b",
        r"\bignored my (emails?|messages?|requests?|calls?|tickets?)\b",
        r"\b(supposed to be here|supposed to arrive|should have arrived|was due|expected|promised).{0,40}\b(\d+|a few|several|many|some|one|two|three|four|five|six|seven|last|yesterday|ago|days?|weeks?|hours?|months?)\b",
        r"\b(delayed|late|overdue|missing|lost|stuck)\s+(for\s+)?(\d+|a few|several|many|some|days?|weeks?|hours?)\b",
        r"\b(order|package|parcel|delivery|item|shipment)\s+(is|was)\s+(late|delayed|overdue|missing|lost)\b",
        r"\b(several|many|\d+)\s+(days|weeks|hours)\s+(late|overdue|ago)\b",
        r"\b(way|long)\s+overdue\b",
        r"\b(still|been)\s+waiting\b",
        r"\b(never|(still\s+)?(has|have|had)\s+not)\s+(arrived|received|delivered|come)\b",
        r"\bwaste of (time|money)\b",
        r"\bfed up\b",
        r"\bsick of\b",
        r"\btired of\b",
        r"\bnot acceptable\b",
        r"\bnao e aceitavel\b",
        r"\binaceitavel\b",
        r"\bestou frustrad[oa]\b",
        r"\bmuito desapontad[oa]\b",
        r"\bninguem (respondeu|ajudou)\b",
        r"\bcontinuo a espera\b",
    ]

    AMBIGUOUS_PHRASES = {
        "ok",
        "okay",
        "fine",
        "whatever",
        "sure",
        "hmm",
        "hm",
        "right",
        "yeah",
        "yes",
        "no",
        "maybe",
        "whatever you want",
        "do what you want",
        "whatever do what you want",
        "do whatever you want",
        "tanto faz",
        "pronto",
        "esta bem",
        "ta bem",
        "sim",
        "nao",
    }

    SHORT_ACKNOWLEDGEMENTS = {
        "thanks",
        "thank you",
        "thanks a lot",
        "many thanks",
        "appreciate it",
        "much appreciated",
        "understood",
        "understood thanks",
        "understood thank you",
        "thanks understood",
        "thank you understood",
        "got it",
        "got it thanks",
        "got it thank you",
        "ok got it",
        "okay got it",
        "ok thanks",
        "okay thanks",
        "ok thank you",
        "okay thank you",
        "alright thanks",
        "all good",
        "all good thanks",
        "sounds good",
        "makes sense",
        "fair enough",
        "will do",
        "noted",
        "noted thanks",
        "great thanks",
        "perfect thanks",
        "obrigado",
        "obrigada",
        "muito obrigado",
        "muito obrigada",
        "entendido",
        "entendido obrigado",
        "entendido obrigada",
        "ok obrigado",
        "ok obrigada",
    }

    CLOSURE_PATTERNS = [
        r"\bthat is all i needed\b",
        r"\bthat is all( for now)?\b",
        r"\bthat is everything\b",
        r"\bnothing else needed\b",
        r"\bthat answers (my question|everything|all my questions)\b",
        r"\bproblem (is )?solved\b",
        r"\bissue (is )?(solved|resolved)\b",
        r"\beverything is (solved|resolved)\b",
        r"\bthat (solved|fixed) it\b",
        r"\byou (solved|resolved|fixed) (my|the) (problem|issue)\b",
        r"\b(we are|i am) all set\b",
        r"\bno (more|further) questions\b",
        r"\bthank you,? that is all\b",
        r"\bthanks,? that is all\b",
        r"\bficou tudo resolvido\b",
        r"\besta tudo resolvido\b",
        r"\besta resolvido\b",
        r"\bficou resolvido\b",
        r"\bja esta resolvido\b",
        r"\bobrigad[oa],? ficou tudo resolvido\b",
    ]

    NEGATION_WORDS = {
        "not",
        "no",
        "never",
        "isnt",
        "wasnt",
        "arent",
        "werent",
        "hasnt",
        "havent",
        "hadnt",
        "doesnt",
        "dont",
        "didnt",
        "cannot",
        "cant",
        "couldnt",
        "wont",
        "wouldnt",
        "shouldnt",
        "aint",
        "nao",
        "nunca",
        "jamais",
    }

    CONTRACTIONS = {
        r"\bcan't\b": "cannot",
        r"\bcannot\b": "cannot",
        r"\bcouldn't\b": "could not",
        r"\bdon't\b": "do not",
        r"\bdoesn't\b": "does not",
        r"\bdidn't\b": "did not",
        r"\bwon't\b": "will not",
        r"\bwouldn't\b": "would not",
        r"\bshouldn't\b": "should not",
        r"\bisn't\b": "is not",
        r"\baren't\b": "are not",
        r"\bwasn't\b": "was not",
        r"\bweren't\b": "were not",
        r"\bhasn't\b": "has not",
        r"\bhaven't\b": "have not",
        r"\bhadn't\b": "had not",
        r"\bi'm\b": "i am",
        r"\bi've\b": "i have",
        r"\bi'll\b": "i will",
        r"\bi'd\b": "i would",
        r"\byou're\b": "you are",
        r"\byou've\b": "you have",
        r"\byou'll\b": "you will",
        r"\byou'd\b": "you would",
        r"\bwe're\b": "we are",
        r"\bwe've\b": "we have",
        r"\bwe'll\b": "we will",
        r"\bthey're\b": "they are",
        r"\bthey've\b": "they have",
        r"\bthey'll\b": "they will",
        r"\bit's\b": "it is",
        r"\bthat's\b": "that is",
        r"\bthere's\b": "there is",
        r"\bwhat's\b": "what is",
        r"\bwho's\b": "who is",
    }

    def __init__(self, engine_dir=None):
        self.text_estimator = TextEstimator(engine_dir=engine_dir)
        self.affective_state = AffectiveState()
        self.reset()

    def reset(self):
        self.affective_state.reset()
        self.frustration_streak = 0

    @staticmethod
    def _normalize_text(text):
        text = str(text).lower().strip()
        text = text.replace("’", "'").replace("‘", "'")

        for pattern, replacement in Engine.CONTRACTIONS.items():
            text = re.sub(pattern, replacement, text)

        text = unicodedata.normalize("NFKD", text)
        text = "".join(
            character
            for character in text
            if not unicodedata.combining(character)
        )
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _matches_any(text, patterns):
        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    def _has_negation_before(self, text, match_start):
        preceding_text = text[:match_start]
        clause_parts = re.split(r"[.!?;:,]", preceding_text)
        current_clause = clause_parts[-1]

        preceding_words = re.findall(
            r"\b[\w']+\b",
            current_clause,
        )
        recent_words = preceding_words[-5:]

        return any(
            word in self.NEGATION_WORDS
            for word in recent_words
        )

    def _is_unnegated_match(self, text, patterns):
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                if not self._has_negation_before(
                    text,
                    match.start(),
                ):
                    return True
        return False

    def _is_legal_signal(self, text):
        return self._is_unnegated_match(text, self.LEGAL_PATTERNS)

    def _is_human_request(self, text):
        return self._is_unnegated_match(text, self.HUMAN_REQUEST_PATTERNS)

    def _is_refund_request(self, text):
        return self._is_unnegated_match(text, self.REFUND_PATTERNS)

    def _is_frustration_signal(self, text):
        return self._is_unnegated_match(text, self.FRUSTRATION_PATTERNS)

    def _is_closure(self, text):
        return self._is_unnegated_match(text, self.CLOSURE_PATTERNS)

    @staticmethod
    def _has_unresolved_request(text):
        if "?" in text:
            return True

        request_patterns = [
            r"\bcan you\b",
            r"\bcould you\b",
            r"\bwould you\b",
            r"\bwill you\b",
            r"\bplease\b",
            r"\bi need you to\b",
            r"\bi still need\b",
            r"\bi also need\b",
            r"\bcan i\b",
            r"\bcould i\b",
            r"\bwhat about\b",
            r"\bhow about\b",
            r"\bmas pode\b",
            r"\bpode ajudar\b",
            r"\bpreciso de\b",
            r"\bquero saber\b",
        ]
        return Engine._matches_any(text, request_patterns)

    def _is_ambiguous(self, text, confidence):
        normalized = self._normalize_text(text)
        clean_text = re.sub(r"[^\w\s]", "", normalized)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        words = clean_text.split()

        if clean_text in self.AMBIGUOUS_PHRASES:
            return True

        if len(words) == 0:
            return True

        if clean_text in self.SHORT_ACKNOWLEDGEMENTS:
            return False

        if len(words) <= 2 and confidence < self.CONFIDENCE_THRESHOLD:
            return True

        return False

    @staticmethod
    def _is_sarcastic_or_uncertain(flags):
        return "possible_sarcasm" in flags

    @staticmethod
    def _is_portuguese(text):
        normalized = Engine._normalize_text(text)
        indicators = {
            "obrigado",
            "obrigada",
            "ficou",
            "resolvido",
            "nao",
            "estou",
            "quero",
            "preciso",
            "ninguem",
            "devolucao",
            "ajuda",
            "entendido",
            "entrega",
            "encomenda",
        }
        words = set(re.findall(r"\b\w+\b", normalized))
        return bool(words & indicators)

    def _update_frustration_streak(self, text, label, confidence):
        explicit_frustration = self._is_frustration_signal(text)
        affective_frustration = (
            label in {"frustration", "anger"}
            and confidence >= self.CONFIDENCE_THRESHOLD
        )

        if explicit_frustration or affective_frustration:
            self.frustration_streak += 1
        else:
            self.frustration_streak = 0

        return self.frustration_streak

    def _decide(
        self,
        state,
        frustration_streak,
        is_legal,
        is_human_request,
        is_refund_request,
        is_ambiguous,
        is_sarcastic,
        is_closure,
        has_unresolved_request,
        voice_only_label=None,
    ):
        label = state["label"]
        confidence = float(state["confidence"])

        # Priority 1: Explicit legal signals.
        if is_legal:
            return "ESCALATE"

        # Priority 2: Explicit human assistance requests.
        if is_human_request:
            return "OFFER_HUMAN"

        # Priority 3: Explicit refund requests.
        if is_refund_request:
            return "OFFER_HUMAN"

        # Priority 4: Sarcasm requires clarification.
        if is_sarcastic:
            return "ASK_CLARIFICATION"

        # Priority 5: Explicit positive closure only when no request remains open.
        if is_closure and not has_unresolved_request:
            return "CLOSE_POSITIVE"

        # Priority 6: Ambiguous or unreliable short input.
        if is_ambiguous:
            return "ASK_CLARIFICATION"

        # Priority 7: Anger escalation (low-confidence anger falls back safely to empathy).
        if label == "anger":
            if confidence < self.CONFIDENCE_THRESHOLD:
                return "ANSWER_EMPATHIC"
            return "ESCALATE"

        # Priority 8: Sustained frustration triggers human handoff.
        if frustration_streak >= self.FRUSTRATION_STREAK_LIMIT:
            return "OFFER_HUMAN"

        # Priority 9: Early frustration response.
        if frustration_streak > 0:
            return "ANSWER_EMPATHIC"

        # Priority 10: General negative emotional states or angry/frustrated voice tone.
        if label in {"frustration", "sadness"}:
            return "ANSWER_EMPATHIC"

        if label == "neutral" and voice_only_label in {"anger", "frustration"}:
            return "ANSWER_EMPATHIC"

        return "ANSWER"

    def _faq_reply(self, normalized_text, portuguese):
        if re.search(r"\b(shipping|delivery)\s+(cost|fee|fees|price|charge|free)\b", normalized_text):
            if portuguese:
                return (
                    "O envio padrão é gratuito em encomendas acima de 50 € "
                    "e custa 4,99 € nas restantes encomendas."
                )
            return (
                "Standard shipping is free on orders over €50, "
                "and €4.99 for smaller orders."
            )

        if re.search(r"\b(delivery|shipping|arrive|ship|deliver|entrega|envio|chegar)\b", normalized_text):
            if portuguese:
                return (
                    "As entregas padrão demoram normalmente entre 2 a 5 dias úteis. "
                    "Pode partilhar o número da sua encomenda se quiser verificar o estado atual?"
                )
            return (
                "Standard delivery typically takes 2 to 5 business days. "
                "Would you like to share your order number so I can check its status?"
            )

        if re.search(r"\b(track|tracking|status|where is my order|where is my package|rastreio|estado|encomenda)\b", normalized_text):
            if portuguese:
                return (
                    "Pode acompanhar a sua encomenda através do link de rastreio enviado por e-mail, "
                    "ou indicar o número da encomenda para eu verificar."
                )
            return (
                "You can track your package using the tracking link sent to your email, "
                "or share your order number here and I can check it for you."
            )

        if re.search(r"\b(cancel|cancellation|cancelar|cancelamento)\b", normalized_text):
            if portuguese:
                return (
                    "Pode cancelar a sua encomenda antes do envio através da sua conta "
                    "ou indicando o número da encomenda aqui."
                )
            return (
                "You can cancel your order anytime before it ships from your account page, "
                "or share your order number here so I can assist you."
            )

        if re.search(r"\b(return|exchange|policy|send back|devolucao|troca|politica)\b", normalized_text):
            if portuguese:
                return (
                    "Aceitamos devoluções e trocas no prazo de 30 dias após a entrega, "
                    "desde que o artigo esteja nas condições originais."
                )
            return (
                "We accept returns and exchanges within 30 days of delivery, "
                "provided the item is in its original condition."
            )

        if re.search(r"\b(payment|pay|invoice|receipt|billing|pagamento|fatura|recibo)\b", normalized_text):
            if portuguese:
                return (
                    "Aceitamos pagamentos por cartão de crédito/débito, PayPal e transferência bancária, "
                    "e a fatura é enviada automaticamente por e-mail."
                )
            return (
                "We accept credit/debit cards, PayPal, and bank transfers, "
                "and your invoice is sent automatically by email after purchase."
            )

        if re.search(r"\b(hours|open|contact|support|available|horario|contacto|suporte)\b", normalized_text):
            if portuguese:
                return (
                    "O nosso apoio ao cliente está disponível de segunda a sexta-feira, das 9h00 às 18h00."
                )
            return (
                "Our customer support team is available Monday through Friday, from 9:00 AM to 6:00 PM."
            )

        if re.fullmatch(r"(hello|hi|hey|good morning|good afternoon|good evening|ola|bom dia|boa tarde|boa noite)[!. ]*", normalized_text):
            if portuguese:
                return "Olá! Como posso ajudar hoje?"
            return "Hello! How can I help you today?"

        if portuguese:
            return (
                "Claro! Estou aqui para ajudar. "
                "Pode dizer-me mais sobre o que precisa?"
            )
        return (
            "Of course! I'm here to help. "
            "What would you like to know?"
        )

    def _reply(self, action, text, flags=None):
        portuguese = self._is_portuguese(text)
        flags = flags or []
        normalized_text = self._normalize_text(text)

        audio_notice = ""
        if "voice_processing_failed" in flags:
            if portuguese:
                audio_notice = (
                    "Não foi possível processar o áudio, por isso respondo com base na sua mensagem. "
                )
            else:
                audio_notice = (
                    "I couldn't process the audio, so I'm responding based on your message. "
                )

        if action == "ESCALATE":
            if portuguese:
                body = (
                    "Compreendo a gravidade da situação. "
                    "Vou encaminhar o caso para uma equipa "
                    "humana responsável por analisar e resolver "
                    "este problema."
                )
            else:
                body = (
                    "I understand the seriousness of this situation. "
                    "I will escalate your case to a human support team "
                    "so they can review and address it."
                )
            return audio_notice + body

        if action == "OFFER_HUMAN":
            if portuguese:
                body = (
                    "Compreendo. Vou encaminhar o seu pedido "
                    "para um agente humano que poderá ajudar "
                    "com esta situação."
                )
            else:
                body = (
                    "I understand. I can connect you with a human "
                    "support agent who can help resolve this issue."
                )
            return audio_notice + body

        if action == "ASK_CLARIFICATION":
            if portuguese:
                body = (
                    "Quero ter a certeza de que compreendi "
                    "corretamente. Pode explicar um pouco melhor "
                    "o que pretende?"
                )
            else:
                body = (
                    "I want to make sure I understand you correctly. "
                    "Could you clarify what you mean?"
                )
            return audio_notice + body

        if action == "CLOSE_POSITIVE":
            if portuguese:
                body = (
                    "Fico contente por saber que ficou tudo "
                    "resolvido. Obrigado pelo contacto!"
                )
            else:
                body = (
                    "I'm glad everything is resolved. "
                    "Thank you for contacting us!"
                )
            return audio_notice + body

        if action == "ANSWER_EMPATHIC":
            if portuguese:
                body = (
                    "Compreendo a sua frustração e lamento "
                    "o incómodo. Vou ajudar a encontrar uma "
                    "solução para esta situação."
                )
            else:
                body = (
                    "I understand your frustration, and I'm sorry "
                    "for the inconvenience. I'll help you find "
                    "a solution."
                )
            return audio_notice + body

        if action == "ANSWER":
            return audio_notice + self._faq_reply(normalized_text, portuguese)

        return audio_notice + "How can I help?"

    def process(self, text, audio_path=None, image_path=None):
        if not isinstance(text, str):
            text = "" if text is None else str(text)

        text = text.strip()

        if not text:
            return {
                "valence": 0.0,
                "activity": 0.0,
                "dominance": 0.0,
                "confidence": 0.1,
                "label": "neutral",
                "action": "ASK_CLARIFICATION",
                "reply": "Could you provide a message so I can help you?",
                "flags": [],
                "details": {
                    "message_count": self.affective_state.message_count,
                    "reason": "empty_input",
                    "frustration_streak": self.frustration_streak,
                },
            }

        raw_estimate = self.text_estimator.estimate(text)
        state = self.affective_state.update(
            text,
            raw_estimate,
            audio_path=audio_path,
        )

        flags = list(state.get("flags") or [])
        normalized_text = self._normalize_text(text)

        message_details = state.get("details") or {}
        voice_details = message_details.get("voice") or {}
        voice_only_info = voice_details.get("voice_only") or {}
        voice_only_label = voice_only_info.get("label")

        confidence = float(state["confidence"])

        is_legal = self._is_legal_signal(normalized_text)
        is_human_request = self._is_human_request(normalized_text)
        is_refund_request = self._is_refund_request(normalized_text)
        explicit_frustration = self._is_frustration_signal(normalized_text)
        is_sarcastic = self._is_sarcastic_or_uncertain(flags)
        is_closure = self._is_closure(normalized_text)
        has_unresolved_request = self._has_unresolved_request(normalized_text)

        is_ambiguous = self._is_ambiguous(
            text=text,
            confidence=confidence,
        )

        frustration_streak = self._update_frustration_streak(
            normalized_text,
            state["label"],
            confidence,
        )

        action = self._decide(
            state=state,
            frustration_streak=frustration_streak,
            is_legal=is_legal,
            is_human_request=is_human_request,
            is_refund_request=is_refund_request,
            is_ambiguous=is_ambiguous,
            is_sarcastic=is_sarcastic,
            is_closure=is_closure,
            has_unresolved_request=has_unresolved_request,
            voice_only_label=voice_only_label,
        )

        if action not in self.ACTIONS:
            action = "ANSWER"

        reply = self._reply(action, text, flags=flags)

        voice_empathy_override = (
            action == "ANSWER_EMPATHIC"
            and state["label"] == "neutral"
            and voice_only_label in {"anger", "frustration"}
        )

        details = dict(message_details)
        details.update({
            "frustration_streak": frustration_streak,
            "frustration_streak_limit": self.FRUSTRATION_STREAK_LIMIT,
            "legal_signal": is_legal,
            "human_request": is_human_request,
            "refund_request": is_refund_request,
            "explicit_frustration": explicit_frustration,
            "ambiguous_input": is_ambiguous,
            "possible_sarcasm": is_sarcastic,
            "positive_closure": is_closure,
            "unresolved_request": has_unresolved_request,
            "voice_empathy_override": voice_empathy_override,
            "decision_policy": "topic_3",
        })

        return {
            "valence": float(state["valence"]),
            "activity": float(state["activity"]),
            "dominance": float(state.get("dominance", 0.0)),
            "confidence": confidence,
            "label": state["label"],
            "action": action,
            "reply": reply,
            "flags": flags,
            "details": details,
        }