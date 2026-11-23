"""Model clients for structured JSON completions."""

from medici.model.client import (
    InvalidModelOutputError,
    ModelClient,
    ModelError,
    SchemaDefinitionError,
    SchemaValidationError,
    TransportError,
)
from medici.model.fake import FakeModelClient

__all__ = [
    "FakeModelClient",
    "InvalidModelOutputError",
    "ModelClient",
    "ModelError",
    "SchemaDefinitionError",
    "SchemaValidationError",
    "TransportError",
]