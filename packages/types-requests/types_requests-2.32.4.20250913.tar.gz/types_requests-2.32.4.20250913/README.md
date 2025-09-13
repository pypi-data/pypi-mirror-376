## Typing stubs for requests

This is a [type stub package](https://typing.python.org/en/latest/tutorials/external_libraries.html)
for the [`requests`](https://github.com/psf/requests) package. It can be used by type checkers
to check code that uses `requests`. This version of
`types-requests` aims to provide accurate annotations for
`requests~=2.32.4`.

Note: `types-requests` has required `urllib3>=2` since v2.31.0.7. If you need to install `types-requests` into an environment that must also have `urllib3<2` installed into it, you will have to use `types-requests<2.31.0.7`.

This package is part of the [typeshed project](https://github.com/python/typeshed).
All fixes for types and metadata should be contributed there.
See [the README](https://github.com/python/typeshed/blob/main/README.md)
for more details. The source for this package can be found in the
[`stubs/requests`](https://github.com/python/typeshed/tree/main/stubs/requests)
directory.

This package was tested with the following type checkers:
* [mypy](https://github.com/python/mypy/) 1.17.1
* [pyright](https://github.com/microsoft/pyright) 1.1.405

It was generated from typeshed commit
[`59c36c8bf960b1b7609af5eee3b17ecde6c48864`](https://github.com/python/typeshed/commit/59c36c8bf960b1b7609af5eee3b17ecde6c48864).