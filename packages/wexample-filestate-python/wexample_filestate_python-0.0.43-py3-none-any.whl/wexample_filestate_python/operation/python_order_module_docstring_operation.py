from __future__ import annotations

from typing import TYPE_CHECKING

from .abstract_python_file_operation import AbstractPythonFileOperation

if TYPE_CHECKING:
    from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType


class PythonOrderModuleDocstringOperation(AbstractPythonFileOperation):
    """Ensure module docstring is positioned at the very top of Python files.

    Moves the module docstring (if present) to be the first element in the file,
    before any imports or other code elements.

    Triggered by config: { "python": ["order_module_docstring"] }
    """

    @classmethod
    def get_option_name(cls) -> str:
        from wexample_filestate_python.config_option.python_config_option import (
            PythonConfigOption,
        )

        return PythonConfigOption.OPTION_NAME_ORDER_MODULE_DOCSTRING

    @classmethod
    def preview_source_change(cls, target: TargetFileOrDirectoryType) -> str | None:
        import libcst as cst
        from wexample_filestate_python.operation.utils.python_docstring_utils import (
            find_module_docstring,
            is_module_docstring_at_top,
            move_docstring_to_top,
        )

        src = cls._read_current_str_or_fail(target)
        module = cst.parse_module(src)

        # Check if there's a docstring and if it needs to be moved
        docstring_node, position = find_module_docstring(module)

        if docstring_node is None:
            # No docstring found, nothing to do
            return None

        if is_module_docstring_at_top(module):
            # Check if quotes need normalization
            if len(docstring_node.body) > 0 and isinstance(
                docstring_node.body[0], cst.Expr
            ):
                expr = docstring_node.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    quote = expr.value.quote
                    if quote.startswith("'''") or (
                        quote.startswith("'") and not quote.startswith('"')
                    ):
                        # Need to normalize quotes
                        from wexample_filestate_python.operation.utils.python_docstring_utils import (
                            normalize_docstring_quotes,
                        )

                        normalized_docstring = normalize_docstring_quotes(
                            docstring_node
                        )
                        # Ensure no leading whitespace for the docstring at top
                        clean_docstring = normalized_docstring.with_changes(
                            leading_lines=[]
                        )
                        new_body = [clean_docstring] + list(module.body[1:])
                        modified_module = module.with_changes(body=new_body)
                        return modified_module.code
            # Already at top and quotes are fine
            return None

        # Move docstring to top (this also normalizes quotes)
        modified_module = move_docstring_to_top(module)
        return modified_module.code

    def describe_after(self) -> str:
        return "Module docstring has been moved to the top of the file."

    def describe_before(self) -> str:
        return "Module docstring is not positioned at the top of the file."

    def description(self) -> str:
        return "Move module docstring to the top of Python files. Ensures the module docstring appears as the first element before any imports or code."
