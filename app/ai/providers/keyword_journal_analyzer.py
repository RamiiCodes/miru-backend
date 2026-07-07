from app.ai.journal_analyzer import DetectedJournalSignal, JournalAnalysisResult


JOURNAL_SIGNAL_KEYWORDS = {
    "rumination_tendency": [
        "overthinking",
        "can't stop thinking",
        "cannot stop thinking",
        "thinking again and again",
        "loop",
        "ruminating",
        "obsessed",
        "stuck in my head",
        "je pense trop",
        "je n'arrête pas de penser",
        "boucle",
    ],
    "self_criticism": [
        "i am stupid",
        "i'm stupid",
        "i am useless",
        "i'm useless",
        "i hate myself",
        "my fault",
        "i'm not good enough",
        "i am not good enough",
        "not good enough",
        "je suis nul",
        "je suis inutile",
        "c'est ma faute",
    ],
    "fear_of_failure": [
        "failed",
        "failure",
        "i will fail",
        "afraid to fail",
        "scared to fail",
        "not capable",
        "i can't do it",
        "je vais échouer",
        "peur d'échouer",
        "échec",
    ],
    "work_sensitivity": [
        "work",
        "job",
        "manager",
        "colleague",
        "meeting",
        "deadline",
        "project",
        "travail",
        "boulot",
        "chef",
        "collègue",
        "réunion",
        "deadline",
        "projet",
    ],
}


SAFETY_KEYWORDS = {
    "self_harm_risk": [
        "kill myself",
        "end my life",
        "hurt myself",
        "suicide",
        "suicidal",
    ],
    "harm_to_others_risk": [
        "hurt someone",
        "kill someone",
        "harm someone",
        "attack someone",
    ],
    "abuse_or_coercion_context": [
        "abused",
        "coerced",
        "forced me",
        "threatened me",
        "controlled me",
    ],
    "severe_distress": [
        "severe distress",
        "cannot cope",
        "can't cope",
        "can't take it anymore",
        "panic attack",
        "overwhelmed and unsafe",
    ],
}


SIGNAL_REASONS = {
    "rumination_tendency": "The journal contains language suggesting repetitive or looping thoughts.",
    "self_criticism": "The journal contains language suggesting self-critical thoughts.",
    "fear_of_failure": "The journal contains language suggesting fear of failure or perceived failure.",
    "work_sensitivity": "The journal contains work-related context that may influence the user's state.",
}


class KeywordJournalAnalyzer:
    provider = "keyword"
    model_name = "keyword_rules_v0_1"
    prompt_version = "journal_signal_extraction_v0_1"

    def analyze(self, content: str) -> JournalAnalysisResult:
        detected_signals: list[DetectedJournalSignal] = []

        for signal_code, keywords in JOURNAL_SIGNAL_KEYWORDS.items():
            matched_keywords = self._find_matched_keywords(
                content=content,
                keywords=keywords,
            )

            value = self._calculate_signal_value(
                match_count=len(matched_keywords),
            )

            if value == 0.0:
                continue

            detected_signals.append(
                DetectedJournalSignal(
                    signal_code=signal_code,
                    value=value,
                    confidence=0.55,
                    evidence=", ".join(matched_keywords[:3]),
                    reason=SIGNAL_REASONS.get(signal_code),
                )
            )

        return JournalAnalysisResult(
            detected_signals=detected_signals,
            safety_flags=self._detect_safety_flags(content),
            language=None,
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
        )

    def _detect_safety_flags(self, content: str) -> list[str]:
        normalized_content = content.lower()
        detected_flags: list[str] = []

        for flag_type, keywords in SAFETY_KEYWORDS.items():
            if any(keyword in normalized_content for keyword in keywords):
                detected_flags.append(flag_type)

        return detected_flags

    def _find_matched_keywords(
        self,
        content: str,
        keywords: list[str],
    ) -> list[str]:
        normalized_content = content.lower()

        matched_keywords: list[str] = []
        occupied_spans: list[tuple[int, int]] = []

        # Longer keywords first prevents double-counting nested phrases like:
        # "i am not good enough" and "not good enough".
        sorted_keywords = sorted(
            set(keywords),
            key=len,
            reverse=True,
        )

        for keyword in sorted_keywords:
            normalized_keyword = keyword.lower()
            search_start = 0

            while True:
                match_start = normalized_content.find(
                    normalized_keyword,
                    search_start,
                )

                if match_start == -1:
                    break

                match_end = match_start + len(normalized_keyword)

                overlaps_existing_match = any(
                    match_start < existing_end and match_end > existing_start
                    for existing_start, existing_end in occupied_spans
                )

                if not overlaps_existing_match:
                    matched_keywords.append(keyword)
                    occupied_spans.append((match_start, match_end))
                    break

                search_start = match_end

        return matched_keywords

    def _calculate_signal_value(
        self,
        match_count: int,
    ) -> float:
        if match_count == 0:
            return 0.0

        if match_count == 1:
            return 0.4

        if match_count == 2:
            return 0.7

        return 0.9
