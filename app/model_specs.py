# Data models for various message formats.

from dataclasses import dataclass


@dataclass
class _SystemRequirementsConfig:
    """Model for additional system requirements."""
    sound_card: bool
    additional_notes: bool

@dataclass
class DescriptionConfig:
    """Model for main description configuration."""
    num_paragraphs: int
    num_features: int
    num_subsections: int
    tagline: bool
    system_requirements: _SystemRequirementsConfig

@dataclass
class GameDescription:
    """Model for a generated game description."""
    description: str
    features: list[str]
    tagline: str
    tags: dict
    developer: str
    system_requirements: list[dict]
