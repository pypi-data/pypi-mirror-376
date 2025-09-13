pytest-skip
=============

This is a [pytest](https://pytest.org) plugin which allows to (de-)select or skip tests by name from a list loaded from a file.

pytest-skip expands upon the capabilities of the original [pytest-select](https://github.com/ulope/pytest-select) plugin
by adding
- `--skip-from-file` option to skip tests instead of deselecting
- support to (de-)select or skip parametrized tests without needing to specify test instance qualifiers
- support for blank and comment lines in the selection files
- better integration with the `pytest-xdist`, plugin warning and error messages are passed to the master node with proper stdout or stderr outputs
- sharding functionality to distribute tests across several nodes
- an ability to select/skip parameters combinations matching a certain regular expression.
Put your regexp in the square brackets as a raw string and end the line with `@regexp` suffix:
`file.py::test[r"REGEXP"]@regexp`


Usage
-----

This plugin adds new command line options to pytest:

- ``--select-from-file``
- ``--deselect-from-file``
- ``--skip-from-file``
- ``--select-test``
- ``--deselect-test``
- ``--skip-from-test``
- ``--select-fail-on-missing``
- ``--num-shards``, ``--shard-id`` and ``--sharding-mode``

The first three expect an argument that resolves to one or multiple, semicolon-separated, UTF-8 encoded text file(s)
containing one test name per line. Text file may contain blank and comment lines (starts from `#`). All three
(select, deselect, skip) options can be used simultaneously.

The next three expect one or multiple, semicolon-separated, test names to be selected, deselected or skipped.

The next one changes the behaviour in case (de-)selected or skipped test names are missing from the to-be executed tests.
By default a warning is emitted and the remaining selected tests are executed as normal.
By using the ``--select-fail-on-missing`` flag this behaviour can be changed to instead abort execution in that case.

The sharding parameters allow users to split the test sets into even portions across multiple shards for parallel execution.
The tests that are filtered out for a shard will be deselected.

Test names are expected in the same format as seen in the output of
``pytest --collect-only --quiet`` for example.

Both plain test names or complete node ids (e.g. ``test_file.py::test_name``) are accepted.

Example::

    $~ cat select.txt
    test_something
    test_parametrized[1]
    test_parametrized
    tests/test_foo.py::test_other
    test_parametrized_complex[r"[8|16]-.*-.*"]@regexp
    tests/test_foo.py::test_params[r"int32-.*-.*"]@regexp

    $~ cat deselect.txt
    tests/test_foo.py::test_params[r"bf32-.*-.*"]@regexp

    $~ cat skip1.txt
    test_parametrized[1]
    test_parametrized[2]

    $~ cat skip2.txt
    test_parametrized[r"[579]"]@regexp

    $~ pytest --select-from-file select.txt
    $~ pytest --deselect-from-file deselect.txt
    $~ pytest --select-from-file select.txt --deselect-from-file deselect.txt --skip-from-file skip1.txt:skip2.txt
    $~ pytest --skip-from-file skip1.txt:skip2.txt --num-shards=4 --shard-id=0 --sharding-mode=round-robin
    $~ pytest --skip-from-file skip1.txt:skip2.txt --num-shards=4 --shard-id=0 --sharding-mode=contiguous-split


Install from source
-------------------

```bash
git clone --recursive https://github.com/vlad-penkin/pytest-skip
# Run this command from the pytest-skip directory after cloning the source code using the command above
pip install .
```

Install in development mode
---------------------------

To install plugin in development mode run::

```bash
pip install -e .
```

Questions
---------

Why not use pytest's builtin ``-k`` option
******************************************

The ``-k`` selection mechanism is (currently) unable to deal with selecting multiple parametrized
tests and is also a bit fragile since it matches more than just the test name.
Additionally, depending on the number of tests, giving test names on the command line can overflow
the maximum command length.

Version History
---------------
- ``v0.2.0`` - 9/12/2025:
    - Added sharding functionality (`--num-shards`, `--shard-id`, `--sharding-mode`) to distribute tests across multiple nodes
    - Added ability to (de-)select or skip tests directly by name (`--select-test`, `--deselect-test`, `--skip-test`)
    - Extended `--*-from-file` options to accept multiple, semicolon-separated files simultaneously
    - Introduced support for selecting/skipping parameter combinations with regular expressions using the `@regexp` syntax
    - Improved integration of simultaneous use of `--select-from-file`, `--deselect-from-file`, and `--skip-from-file`

- ``v0.1.0`` - 4/4/2025:
    - Initial release
