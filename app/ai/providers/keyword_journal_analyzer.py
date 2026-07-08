from app.ai.journal_analyzer import (
    DetectedJournalSignal,
    JournalAnalysisResult,
    LifeEventCandidate,
)


class KeywordJournalAnalyzer:
    provider = "keyword"
    model_name = "keyword_rules_v0_2"
    prompt_version = "journal_signal_extraction_v0_2"

    SIGNAL_KEYWORDS = {
        "rumination_tendency": [
            "can't stop thinking",
            "cannot stop thinking",
            "stuck in my head",
            "overthinking",
            "replaying",
            "looping thought",
            "thinking again and again",
        ],
        "self_criticism": [
            "i am not good enough",
            "i'm not good enough",
            "not good enough",
            "i hate myself",
            "i am useless",
            "i'm useless",
            "i failed again",
        ],
        "fear_of_failure": [
            "afraid to fail",
            "fear of failure",
            "i failed again",
            "i will fail",
            "what if i fail",
        ],
        "work_sensitivity": [
            "work",
            "manager",
            "colleague",
            "meeting",
            "deadline",
            "office",
            "project",
        ],
        "grief_loss": [
            "my parents just died",
            "parents just died",
            "died",
            "passed away",
            "lost my",
            "death of",
            "funeral",
            "bereavement",
        ],
        "emotional_numbness": [
            "feel nothing",
            "nothing inside",
            "numb",
            "empty inside",
            "i feel empty",
            "can't feel",
            "cannot feel",
        ],
        "disorientation": [
            "i am lost",
            "i'm lost",
            "lost",
            "don't know what to do",
            "do not know what to do",
            "no direction",
        ],
        "loneliness": [
            "alone",
            "lonely",
            "no one understands",
            "nobody understands",
            "isolated",
        ],
        "overwhelm": [
            "overwhelmed",
            "too much",
            "can't handle",
            "cannot handle",
            "can't cope",
            "cannot cope",
        ],
    }

    SIGNAL_THEME_MAP = {
        "rumination_tendency": "rumination",
        "self_criticism": "self_criticism",
        "fear_of_failure": "fear_of_failure",
        "work_sensitivity": "work_stress",
        "grief_loss": "grief",
        "emotional_numbness": "emotional_numbness",
        "disorientation": "disorientation",
        "loneliness": "loneliness",
        "overwhelm": "overwhelm",
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

    def analyze(self, content: str) -> JournalAnalysisResult:
        detected_signals = self._detect_signals(content=content)

        signal_codes = [
            signal.signal_code
            for signal in detected_signals
        ]

        themes = self._build_themes(signal_codes=signal_codes)

        life_event_candidates = self._detect_life_event_candidates(
            content=content,
        )

        safety_flags = self._detect_safety_flags(content=content)

        return JournalAnalysisResult(
            detected_signals=detected_signals,
            safety_flags=safety_flags,
            themes=themes,
            life_event_candidates=life_event_candidates,
            emotional_tone=", ".join(themes) if themes else None,
            summary=self._build_summary(
                themes=themes,
                life_event_candidates=life_event_candidates,
            ),
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output={
                "analyzer_type": "keyword_fallback",
                "detected_signal_codes": signal_codes,
                "themes": themes,
                "safety_flags": safety_flags,
                "life_event_candidates": [
                    candidate.model_dump(mode="json")
                    for candidate in life_event_candidates
                ],
            },
        )

    def _detect_signals(self, content: str) -> list[DetectedJournalSignal]:
        detected_signals: list[DetectedJournalSignal] = []

        for signal_code, keywords in self.SIGNAL_KEYWORDS.items():
            matched_keywords = self._find_matched_keywords(
                content=content,
                keywords=keywords,
            )

            if not matched_keywords:
                continue

            detected_signals.append(
                DetectedJournalSignal(
                    signal_code=signal_code,
                    value=self._calculate_signal_value(
                        matched_count=len(matched_keywords),
                    ),
                    confidence=0.55,
                    evidence=", ".join(matched_keywords),
                    reason=(
                        "Keyword fallback detected: "
                        + ", ".join(matched_keywords)
                    ),
                )
            )

        return detected_signals

    def _find_matched_keywords(
        self,
        content: str,
        keywords: list[str],
    ) -> list[str]:
        normalized_content = content.lower()
        matched_keywords: list[str] = []
        occupied_spans: list[tuple[int, int]] = []

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
                    match_start < existing_end
                    and match_end > existing_start
                    for existing_start, existing_end in occupied_spans
                )

                if not overlaps_existing_match:
                    matched_keywords.append(keyword)
                    occupied_spans.append((match_start, match_end))
                    break

                search_start = match_end

        return matched_keywords

    def _calculate_signal_value(self, matched_count: int) -> float:
        if matched_count <= 0:
            return 0.0

        if matched_count == 1:
            return 0.4

        if matched_count == 2:
            return 0.7

        return 0.9

    def _detect_safety_flags(self, content: str) -> list[str]:
        normalized_content = content.lower()
        detected_flags: list[str] = []

        for flag_type, keywords in self.SAFETY_KEYWORDS.items():
            if any(keyword in normalized_content for keyword in keywords):
                detected_flags.append(flag_type)

        return detected_flags

    def _detect_life_event_candidates(
        self,
        content: str,
    ) -> list[LifeEventCandidate]:
        normalized_content = content.lower()

        bereavement_keywords = [
            "my parents just died",
            "parents just died",
            "died",
            "passed away",
            "lost my",
            "death of",
            "funeral",
            "bereavement",
        ]

        if any(keyword in normalized_content for keyword in bereavement_keywords):
            return [
                LifeEventCandidate(
                    event_type="bereavement",
                    description=(
                        "The user describes the death or loss of someone close."
                    ),
                    severity="high",
                    confidence=0.8,
                    evidence=None,
                )
            ]

        return []

    def _build_themes(self, signal_codes: list[str]) -> list[str]:
        return sorted(
            {
                self.SIGNAL_THEME_MAP[signal_code]
                for signal_code in signal_codes
                if signal_code in self.SIGNAL_THEME_MAP
            }
        )

    def _build_summary(
        self,
        themes: list[str],
        life_event_candidates: list[LifeEventCandidate],
    ) -> str | None:
        if not themes and not life_event_candidates:
            return None

        summary_parts: list[str] = []

        if themes:
            summary_parts.append(
                "Detected themes: " + ", ".join(themes) + "."
            )

        if life_event_candidates:
            event_types = [
                candidate.event_type
                for candidate in life_event_candidates
            ]

            summary_parts.append(
                "Possible life event candidate(s): "
                + ", ".join(event_types)
                + "."
            )

        return " ".join(summary_parts)