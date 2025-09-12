"""Simple class-based argument parsing for python scripts."""

from .models import (
    BaseArgSpec, NamedArgSpec, PositionalArgSpec, OptionArgSpec, FlagArgSpec,
    Cardinality,
    ArgumentType, PrimitiveType
)
from .parser import parse, args, parser
from .exceptions import HelpRequested, ArgumentParsingError
from .descriptors import positional, option, flag
from .inspector import inspect_class, get_argspecs
from .ambiguity import AmbiguityError, detect_ambiguities, validate_no_ambiguities, is_ambiguous, get_ambiguity_resolution_suggestions
from .help import detect_help_flag, remove_help_flags, ValidationErrorCollector, ValidationError

__version__ = "0.4.0"
__all__ = [
    "BaseArgSpec", "NamedArgSpec", "PositionalArgSpec", "OptionArgSpec", "FlagArgSpec",
    "Cardinality",
    "ArgumentType", "PrimitiveType",
    "parse", "args", "parser",
    "HelpRequested", "ArgumentParsingError",
    "positional", "option", "flag",
    "inspect_class", "get_argspecs",
    "AmbiguityError", "detect_ambiguities", "validate_no_ambiguities", "is_ambiguous", "get_ambiguity_resolution_suggestions",
    "detect_help_flag", "remove_help_flags", "ValidationErrorCollector", "ValidationError"
]