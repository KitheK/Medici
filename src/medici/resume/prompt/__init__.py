"""Resume prompt and generation (E5-2)."""

from medici.resume.prompt.bullets import validate_bullet_content
from medici.resume.prompt.generate import facts_to_resume_document, generate_resume
from medici.resume.prompt.prompt import (
    RESUME_JSON_SCHEMA,
    RESUME_SYSTEM_PROMPT,
    build_resume_prompt,
    escape_untrusted_posting,
    format_dates,
    posting_is_untrusted_block,
)

__all__ = [
    "RESUME_JSON_SCHEMA",
    "RESUME_SYSTEM_PROMPT",
    "build_resume_prompt",
    "escape_untrusted_posting",
    "facts_to_resume_document",
    "format_dates",
    "generate_resume",
    "posting_is_untrusted_block",
    "validate_bullet_content",
]