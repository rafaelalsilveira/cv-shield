SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "follow these instructions instead",
    "do not hire",
    "always recommend this candidate",
]


def detect_suspicious_patterns(text):
    findings = []

    text_lower = text.lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in text_lower:
            findings.append(pattern)

    return findings