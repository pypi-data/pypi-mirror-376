"""
AgentSpec - Specification-driven development toolkit.

A modular toolkit for generating comprehensive development specifications
with smart context detection and template-based generation.
"""

__version__ = "1.0.2"
__author__ = "Keyur Golani"

from .core.context_detector import ContextDetector

# from .core.spec_generator import SpecGenerator  # Not implemented yet
from .core.instruction_database import InstructionDatabase
from .core.template_manager import TemplateManager

__all__ = [
    # "SpecGenerator",
    "InstructionDatabase",
    "TemplateManager",
    "ContextDetector",
]
