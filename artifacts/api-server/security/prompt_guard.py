import re
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Basic indicators of prompt injection attempts
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"system\s+override",
    r"you\s+are\s+now\s+a\s+helpful\s+assistant",
    r"disregard\s+instructions",
    r"dan\s+mode",
    r"jailbreak",
    r"forget\s+what\s+you\s+were\s+told",
    r"bypass\s+safety",
]


class PromptGuard:
    @staticmethod
    def detect_injection(text: str) -> bool:
        """
        Scan text for prompt injection patterns.
        Returns True if a suspicious pattern is found, False otherwise.
        """
        if not text:
            return False

        text_lower = text.lower()
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"Prompt injection detected using pattern: {pattern}")
                return True
        return False

    @classmethod
    def validate_input(cls, text: str):
        """Validates input text and raises HTTP exception if injection is detected."""
        if cls.detect_injection(text):
            raise HTTPException(
                status_code=400,
                detail="Security check failed: Suspicious input pattern detected.",
            )
