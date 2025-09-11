# rexpr
A small library that uses Python 3.14's new templates (t-strings) to smoothly implement a way to turn an expression into its source code string dynamically.

## Advantages
This solution brings multiple advantages:
- Laziness:
    If the expression should does not need to be evaluated (only the source code string is desired), it won't be.
- Fast:
    Only very few basic string checks and modifications are performed.
- Builtin support by type checkers and linters:
    As long as a type checker / linter supports templates, the correct return value (if evaluated), the correctness of the expression and the correct type of the interpolation can be verified.
    As of writing this (Python 3.14rc2), generic support for templates and interpolations has been [added](https://github.com/python/cpython/issues/133970), but is not yet supported by typeshed and type checkers.
- Single point of truth:
    By having the possibility to also evaluate an expression in the same function call, there is no need to duplicate an expression to get both its evaluated value and its source code string.

## References
This module is an implementation of the ideas and solutions proposed by my [topic](https://discuss.python.org/t/proposal-implement-builtin-way-to-stringify-expression-nicely-2/101589).