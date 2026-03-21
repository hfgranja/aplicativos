"""
Generic property library — universal invariants applicable to most systems.
"""
from typing import Any, Callable, List


class PropertyViolation(Exception):
    def __init__(self, property_name: str, input_val: Any, actual: Any, expected: str):
        self.property_name = property_name
        self.input_val = input_val
        self.actual = actual
        self.expected = expected
        super().__init__(f"Property '{property_name}' violated: {expected} but got {actual!r}")


def check_idempotency(func: Callable, input_val: Any, times: int = 3) -> bool:
    """Running func(x) multiple times must return the same result."""
    results = [func(input_val) for _ in range(times)]
    return all(r == results[0] for r in results)


def check_roundtrip(encode: Callable, decode: Callable, value: Any) -> bool:
    """decode(encode(x)) == x"""
    return decode(encode(value)) == value


def check_commutativity(func: Callable, a: Any, b: Any) -> bool:
    """func(a, b) == func(b, a)"""
    return func(a, b) == func(b, a)


def check_associativity(func: Callable, a: Any, b: Any, c: Any) -> bool:
    """func(func(a,b), c) == func(a, func(b,c))"""
    return func(func(a, b), c) == func(a, func(b, c))


def check_monotonicity(func: Callable, inputs: List[Any]) -> bool:
    """For sorted inputs, outputs must be non-decreasing."""
    results = [func(x) for x in sorted(inputs)]
    return all(results[i] <= results[i + 1] for i in range(len(results) - 1))


def check_no_exception(func: Callable, input_val: Any) -> bool:
    """func must not raise for valid inputs."""
    try:
        func(input_val)
        return True
    except Exception:
        return False


def check_output_type(func: Callable, input_val: Any, expected_type: type) -> bool:
    """Output of func must be instance of expected_type."""
    return isinstance(func(input_val), expected_type)
