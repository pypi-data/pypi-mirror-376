import sys
from io import TextIOWrapper, StringIO
from typing import Any, Callable, TextIO, Union

import kawaiitb.utils.fromtraceback as fromtraceback

sys_getframe = sys._getframe  # noqa

readables = (TextIO, TextIOWrapper, StringIO)
SupportsReading = Union[*readables]

__all__ = ["sys_getframe", "extract_caret_anchors_from_line_segment", "safe_string",
           "fromtraceback", "is_sysstdlib_name", *fromtraceback.__all__, ]


def safe_string(value: Any, what: str, func: Callable[[Any], str] = str):
    try:
        return func(value)
    except:
        return f'<{what} {func.__name__}() failed>'


def is_sysstdlib_name(name: str) -> bool:
    return name in sys.builtin_module_names or name in sys.stdlib_module_names


def extract_caret_anchors_from_line_segment(segment):
    import ast

    try:
        tree = ast.parse(segment)
    except SyntaxError:
        return None

    if len(tree.body) != 1:
        return None

    normalize = lambda offset: fromtraceback.byte_offset_to_character_offset(segment, offset)
    statement = tree.body[0]
    match statement:
        case ast.Expr(expr):
            match expr:
                case ast.BinOp():
                    operator_start = normalize(expr.left.end_col_offset)
                    operator_end = normalize(expr.right.col_offset)
                    operator_str = segment[operator_start:operator_end]
                    operator_offset = len(operator_str) - len(operator_str.lstrip())

                    left_anchor = expr.left.end_col_offset + operator_offset
                    right_anchor = left_anchor + 1
                    if operator_offset + 1 < len(operator_str) and not operator_str[operator_offset + 1].isspace():
                        right_anchor += 1

                    while left_anchor < len(segment) and ((ch := segment[left_anchor]).isspace() or ch in ")#"):
                        left_anchor += 1
                        right_anchor += 1
                    return normalize(left_anchor), normalize(right_anchor)
                case ast.Subscript():
                    left_anchor = normalize(expr.value.end_col_offset)
                    right_anchor = normalize(expr.slice.end_col_offset + 1)
                    while left_anchor < len(segment) and ((ch := segment[left_anchor]).isspace() or ch != "["):
                        left_anchor += 1
                    while right_anchor < len(segment) and ((ch := segment[right_anchor]).isspace() or ch != "]"):
                        right_anchor += 1
                    if right_anchor < len(segment):
                        right_anchor += 1
                    return left_anchor, right_anchor

    return None
