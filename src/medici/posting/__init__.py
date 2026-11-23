"""Job posting parser."""

from medici.posting.models import Posting
from medici.posting.parser import parse_posting

__all__ = ["Posting", "parse_posting"]