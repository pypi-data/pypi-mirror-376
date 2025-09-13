"""A collection of common constants for the logging system."""

from collections.abc import Callable
from io import StringIO
from typing import IO, Literal, TextIO

from bear_dereth.constants.enums.log_level import LogLevel
from bear_dereth.tools.general.textio_utility import DEVNULL, stderr, stdout

METHOD_NAMES: dict[str, dict[str, LogLevel]] = {
    "debug": {"level": LogLevel.DEBUG},
    "info": {"level": LogLevel.INFO},
    "warning": {"level": LogLevel.WARNING},
    "error": {"level": LogLevel.ERROR},
    "exception": {"level": LogLevel.EXCEPTION},
    "verbose": {"level": LogLevel.VERBOSE},
    "success": {"level": LogLevel.SUCCESS},
    "failure": {"level": LogLevel.FAILURE},
}

BaseOutput = Literal["stdout", "stderr", "devnull", "string_io"]
CallableOrFile = Callable[[], TextIO | IO[str] | StringIO] | TextIO | IO[str] | StringIO
ExtraStyle = Literal["flatten", "no_flatten"]
WITHOUT_EXCEPTION_NAMES: dict[str, dict[str, LogLevel]] = METHOD_NAMES.copy()
WITHOUT_EXCEPTION_NAMES.pop("exception")

FILE_MODE: dict[BaseOutput, Callable[[], TextIO | IO[str] | StringIO]] = {
    "stdout": stdout,
    "stderr": stderr,
    "devnull": DEVNULL,
    "string_io": StringIO,
}
