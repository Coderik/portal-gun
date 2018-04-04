import sys


class PrintIndent:
    """
    Context manager for implicit indentation of text printed to stdout and stderr.
    All output within the corresponding 'with' statement gets indented by a specified
    number of spaces.
    """

    _default_indent = 4

    @staticmethod
    def set_default_indent(value):
        assert type(value) == int
        assert value >= 0
        PrintIndent._default_indent = value

    def __init__(self, indent=None):
        if indent is None:
            indent = PrintIndent._default_indent
        else:
            assert type(indent) == int
            assert indent >= 0

        self._indent = indent

    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = PrintIndent.Wrapper(sys.stdout, self._indent)
        sys.stderr = PrintIndent.Wrapper(sys.stderr, self._indent)

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    class Wrapper:
        def __init__(self, writable, indent):
            self._writable = writable
            self._indent = indent

        def write(self, data):
            self._writable.write('\t{}'.format(data).expandtabs(self._indent))

        def flush(self):
            self._writable.flush()
