"""Resume prompt and generation (E5-2)."""

from medici.resume.prompt.generate import facts_to_resume_document, generate_resume
from medici.resume.prompt.prompt import (
    RESUME_JSON_SCHEMA,
    RESUME_SYSTEM_PROMPT,
    build_resume_prompt,
    posting_is_untrusted_block,
)

__all__ = [
    "RESUME_JSON_SCHEMA",
    "RESUME_SYSTEM_PROMPT",
    "build_resume_prompt",
    "facts_to_resume_document",
    "generate_resume",
    "posting_is_untrusted_block",
]