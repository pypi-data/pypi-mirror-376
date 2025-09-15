from __future__ import annotations

from typing import TYPE_CHECKING

from .abstract_python_file_operation import AbstractPythonFileOperation

if TYPE_CHECKING:
    from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType


class PythonModernizeTypingOperation(AbstractPythonFileOperation):
    """Modernize typing syntax (PEP 585/604) to Python 3.12 style.

    Triggered by: {"python": ["modernize_typing"]}
    """

    @classmethod
    def get_option_name(cls) -> str:
        from wexample_filestate_python.config_option.python_config_option import (
            PythonConfigOption,
        )

        return PythonConfigOption.OPTION_NAME_MODERNIZE_TYPING

    @classmethod
    def preview_source_change(cls, target: TargetFileOrDirectoryType) -> str | None:
        from pyupgrade._main import Settings, _fix_plugins

        src = cls._read_current_str_or_fail(target)
        settings = Settings(min_version=(3, 12))
        updated = _fix_plugins(src, settings=settings)
        # _fix_plugins returns a string; return as-is
        return updated

    def describe_after(self) -> str:
        return "Typing syntax has been modernized to Python 3.12 style (PEP 585/604)."

    def describe_before(self) -> str:
        return (
            "The file uses legacy typing syntax that can be modernized for Python 3.12."
        )

    def description(self) -> str:
        return "Modernize typing syntax (PEP 585/604) using pyupgrade for Python 3.12."
