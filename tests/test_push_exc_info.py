# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/coveragepy/coveragepy/blob/main/NOTICE.txt

"""Cover the PyPy line skip and the no-fall-through branch arc."""

from __future__ import annotations

import pytest

from coverage.bytecode import BranchArcResolver, NO_FALL_THROUGH
from coverage.pytracer import PUSH_EXC_INFO, PyTracer


def test_push_exc_info_line_event_is_not_recorded() -> None:
    if PUSH_EXC_INFO is None:
        pytest.skip("this interpreter has no PUSH_EXC_INFO opcode")

    class Code:
        co_filename = "sample.py"
        co_code = bytes([PUSH_EXC_INFO])
        co_name = "sample"
        co_firstlineno = 1

    class Frame:
        def __init__(self) -> None:
            self.f_code = Code()
            self.f_lasti = 0
            self.f_lineno = 10
            self.f_back = None

    tracer = PyTracer()
    tracer.stopped = False
    tracer.cur_file_data = set()
    tracer.trace_arcs = False
    tracer.last_line = 1
    result = tracer._trace(Frame(), "line", None)
    assert result == tracer._cached_bound_method_trace
    assert tracer.cur_file_data == set()


def test_reraise_branch_has_no_fall_through() -> None:
    def sample() -> None:
        try:
            raise ValueError("x")
        except ValueError:
            raise

    code = sample.__code__
    dest = next(index for index, op in enumerate(code.co_code) if op in NO_FALL_THROUGH)
    resolver = BranchArcResolver(code, {0: 1}, {})
    assert resolver.resolve(0, dest) is None
