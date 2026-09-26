# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/coveragepy/coveragepy/blob/main/NOTICE.txt

"""Cover the PyPy line skip and the no-fall-through branch arc."""

from __future__ import annotations

from types import FrameType
from typing import cast

import pytest

try:
    from coverage.bytecode import NO_FALL_THROUGH, BranchArcResolver
except ImportError:  # pragma: no cover  # the seeded revert removes the no-fall-through set
    from coverage.bytecode import BranchArcResolver

    NO_FALL_THROUGH = set[int]()

try:
    from coverage.pytracer import PUSH_EXC_INFO, PyTracer
except ImportError:  # pragma: no cover  # the seeded revert removes the opcode name
    from coverage.pytracer import PyTracer

    PUSH_EXC_INFO = None


def test_push_exc_info_line_event_is_not_recorded() -> None:
    opcode = PUSH_EXC_INFO
    if not isinstance(opcode, int):
        pytest.skip("this interpreter has no PUSH_EXC_INFO opcode")
    code_bytes = bytes([opcode])

    class Code:
        """A tiny code object whose first opcode is PUSH_EXC_INFO."""

        co_filename = "sample.py"
        co_code = code_bytes
        co_name = "sample"
        co_firstlineno = 1

    class Frame:
        """Enough of a frame for the line-event branch."""

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
    result = tracer._trace(cast(FrameType, Frame()), "line", None)
    assert result is tracer._cached_bound_method_trace
    assert tracer.cur_file_data == set()


def test_reraise_branch_has_no_fall_through() -> None:
    if not NO_FALL_THROUGH:  # pragma: no cover
        pytest.skip("this build has no no-fall-through opcodes")

    def sample() -> None:
        try:
            raise ValueError("x")
        except ValueError:  # pylint: disable=try-except-raise
            raise

    with pytest.raises(ValueError, match="x"):
        sample()
    code = sample.__code__
    dest = next(index for index, op in enumerate(code.co_code) if op in NO_FALL_THROUGH)
    resolver = BranchArcResolver(code, {0: 1}, {})
    assert resolver.resolve(0, dest) is None
