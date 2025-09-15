from typing import Optional
import linecache
import inspect
import sys
import os

class CustomException(SystemExit):
    """Exception with the ability to customize its traceback message"""
    def __init__(
        self,
        error: Optional[str] = None,
        traceback: Optional[bool] = True,
        error_type: str = "CustomException",
        error_separator: str = ": ",
        traceback_kwd: str = "Traceback ",
        traceback_msg: str = "(most recent call last)",
        traceback_colon: str = ":",
        traceback_msg_end: str = "\n",
        traceback_data_end: str = "\n",
        traceback_data_start: str = "  ",
        traceback_code_end: str = "\n",
        traceback_code_start: str = "    ",
        traceback_underline_start: str = "    ",
        traceback_underline_end: str = "\n",
        traceback_underline_padding: int = 0,
        traceback_underline_repeat: int = None,
        traceback_file: Optional[str] = None,
        traceback_file_start: Optional[str] = None,
        traceback_file_left_quote: Optional[str] = None,
        traceback_file_right_quote: Optional[str] = None,
        traceback_file_to_line_separator: Optional[str] = None,
        traceback_line_data_start: Optional[str] = None,
        traceback_line_data: Optional[str] = None,
        traceback_line_to_scope_data_separator: Optional[str] = None,
        traceback_scope_data_start: Optional[str] = None,
        traceback_scope_data: Optional[str] = None,
        traceback_scope_prefix: Optional[str] = None,
        traceback_code: Optional[str] = None,
        traceback_underline_char: Optional[str] = None,
        traceback_underline_full: Optional[str] = None,
        traceback_end: Optional[str] = None
    ) -> None:

        """__init__ method"""

        # Collect runtime context
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        code_line = linecache.getline(filename, lineno).strip()
        scope = frame.f_code.co_name

        # Set defaults
        traceback_file = traceback_file or os.path.abspath(sys.argv[0])
        traceback_file_start = traceback_file_start or "File "
        traceback_data_start = traceback_data_start or "\t"
        traceback_file_left_quote = traceback_file_left_quote or "\""
        traceback_file_right_quote = traceback_file_right_quote or "\""
        traceback_file_to_line_separator = traceback_file_to_line_separator or ", "
        traceback_line_data_start = traceback_line_data_start or "line "
        traceback_line_data = traceback_line_data or str(lineno)
        traceback_line_to_scope_data_separator = traceback_line_to_scope_data_separator or ", "
        traceback_scope_data_start = traceback_scope_data_start or traceback_line_data_start
        traceback_scope_data = traceback_scope_data or scope
        traceback_scope_prefix = traceback_scope_prefix or "in "
        traceback_code = traceback_code or code_line
        traceback_end = traceback_end or ""
        traceback_underline_char = traceback_underline_char or "^"
        traceback_underline_repeat = len(traceback_code)
        traceback_underline_full = traceback_underline_full or None

        # Build formatted traceback message
        traceback_file_repr = (
                traceback_file_start + traceback_file_left_quote + traceback_file + traceback_file_right_quote
        )

        # Underline
        if traceback_underline_full:
            underline = (
                    traceback_underline_start + traceback_underline_full + traceback_underline_end
            )
        else:
            underline = (
                traceback_underline_start + (traceback_underline_padding * " ") + (traceback_underline_char *
                traceback_underline_repeat) + traceback_underline_end
            )

        self.msg = (
            traceback_kwd + traceback_msg + traceback_colon + traceback_msg_end +
            traceback_data_start + traceback_file_repr +
            traceback_file_to_line_separator + traceback_line_data_start + traceback_line_data +
            traceback_line_to_scope_data_separator + traceback_scope_prefix + traceback_scope_data + traceback_data_end +
            traceback_code_start + traceback_code + traceback_code_end + underline + traceback_end
        )

        # Add error type and separator
        error_prefix = error_type + error_separator
        if traceback:
            if not error:
                super().__init__(self.msg + error_prefix)
            else:
                error = self.msg + error_prefix + error
                super().__init__(error)
        elif error:
            super().__init__(error_prefix + error)


error = CustomException(error="hello world!", error_type="HelloWorldError", traceback_code="raise CustomException(...)", traceback_file="...")

raise error