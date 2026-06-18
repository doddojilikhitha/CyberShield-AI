import re
import html
from fastapi import HTTPException

# Suspicious payload structures (e.g. basic SQL injections or HTML script injects)
SUSPICIOUS_PAYLOAD_PATTERNS = [
    r"<\s*script[^>]*>",
    r"javascript\s*:",
    r"union\s+select",
    r"select\s+.*\s+from",
    r"drop\s+table",
    r"insert\s+into",
]


class SecurityValidator:
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitize text by stripping tags and escaping HTML characters."""
        if not text:
            return ""
        # Remove script tags
        cleaned = re.sub(
            r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE
        )
        # Escape remaining HTML
        return html.escape(cleaned).strip()

    @staticmethod
    def check_malicious_patterns(text: str):
        """Scans for general XSS or SQL injection attempts."""
        if not text:
            return

        text_lower = text.lower()
        for pattern in SUSPICIOUS_PAYLOAD_PATTERNS:
            if re.search(pattern, text_lower):
                raise HTTPException(
                    status_code=400,
                    detail="Security check failed: Input contains prohibited character patterns.",
                )

    @classmethod
    def validate_payload(cls, text: str) -> str:
        """Sanitize input and check for injection patterns in a single pass."""
        if not text:
            return ""
        cls.check_malicious_patterns(text)
        return cls.sanitize_string(text)
