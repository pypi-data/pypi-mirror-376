"""Get the source code string of an expression and optionally evalute it."""

import sys

if sys.version_info < (3, 14):
    raise RuntimeError(
        f'Python version 3.14+ required for the {__name__} module, '
        'because it makes use of t-strings'
    )

from string.templatelib import Template
from typing import Any, Callable, Literal, overload

_LAMBDA_NAME = (lambda: None).__name__

@overload
def expr(e: Template[Callable[[], Any]], /) -> str:
    pass

@overload
def expr(e: Template[Callable[[], Any]], /, eval: Literal[False]) -> str:
    pass

@overload
def expr[T](e: Template[Callable[[], T]], /, eval: Literal[True]) -> tuple[str, T]:
    pass

def expr[T](e: Template[Callable[[], T]], /, eval: bool = False) -> str | tuple[str, T]:
    """Turn an expression into its source code string, without executing the
    expression, except when explicitly desired.
    
    Args:
        e: 
            A template with exactly one interpolation, of which the value is a
            literal lambda with no arguments and returning the expression the
            source code string is desired from.
            ```
            # PEP 8 standard
            t'{(lambda: ...)}

            # Surrounding whitespace is allowed though
            t'  {  (  lambda  :  ...  )  }  '
            ```
        eval:
            False by default.
            A bool that specifies whether only the source code string or a 
            tuple of both the source code string and the expression evaluted
            is returned. If False, the expression is not evaluated.

    >>> # Basic behaviour
    >>> x = 100
    >>> expr(t'{(lambda: x)}')
    'x'
    >>> expr(t'{(lambda: x)}', False)
    'x'
    >>> expr(t'{(lambda: x)}', True)
    ('x', 100)
    >>> 
    >>> # Laziness
    >>> y = [1, 2, 3] 
    >>> _ = expr(t'{(lambda: y.append(4))}')
    >>> y
    [1, 2, 3]
    >>> _ = expr(t'{(lambda: y.append(4))}', True)
    >>> y
    [1, 2, 3, 4]
    """
    
    if len(e.interpolations) != 1:
        raise ValueError('not exactly one interpolation')
    
    if (
        (e.strings[0] and not e.strings[0].isspace())
        or (e.strings[1] and not e.strings[1].isspace())
    ):
        raise ValueError('illegal characters around the interpolation')
    
    interp = e.interpolations[0]
    
    ex = (
        interp.expression   #  "   (  lambda  :  ...  )  "
        .lstrip()           #     "(  lambda  :  ...  )  "
        .removeprefix('(')  #      "  lambda  :  ...  )  "
        .lstrip()           #        "lambda  :  ...  )  "
    )

    LAMBDA = 'lambda'

    # verifying every possible workaround would be overkill, this is easily enough
    if (
        not ex.startswith(LAMBDA) 
        or not callable(interp.value) 
        or interp.value.__name__ != _LAMBDA_NAME
    ):
        raise ValueError('expected a lambda without any args as the value of the interpolation')
    
    ex = (
        ex                     #  "lambda  :  ...  )  "
        .removeprefix(LAMBDA)  #        "  :  ...  )  " 
        .strip()               #          ":  ...  )" 
        .removeprefix(':')     #           "  ...  )"
        .removesuffix(')')     #           "  ...  "
        .strip()               #             "..."
    )
    
    if eval:
        return (ex, interp.value())  # type: ignore
    
    return ex

    
__all__ = [
    'expr'
]