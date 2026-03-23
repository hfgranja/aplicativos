"""
Domain-specific generators for property-based testing.
Covers primitives, monetary values, dates, documents, and invalid inputs.
"""
import random
import string
from decimal import Decimal
from datetime import date, timedelta
from typing import Any


def gen_integer(min_val=-2**31, max_val=2**31 - 1) -> int:
    return random.randint(min_val, max_val)


def gen_float(min_val=-1e10, max_val=1e10) -> float:
    return random.uniform(min_val, max_val)


def gen_string(min_len=0, max_len=256) -> str:
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.printable, k=length))


def gen_monetary_amount(min_cents=0, max_cents=10_000_000_00) -> Decimal:
    """Returns a Decimal with 2 decimal places."""
    cents = random.randint(min_cents, max_cents)
    return Decimal(cents) / 100


def gen_monetary_edge_cases() -> list:
    """Known edge cases for monetary arithmetic."""
    return [
        Decimal("0.00"),
        Decimal("0.01"),
        Decimal("0.10"),
        Decimal("1.00"),
        Decimal("99.99"),
        Decimal("1000000.00"),
        Decimal("-0.01"),
        Decimal("-99.99"),
        Decimal("9999999.99"),
    ]


def gen_date(start=date(2000, 1, 1), end=date(2030, 12, 31)) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def gen_date_edge_cases() -> list:
    return [
        date(2000, 2, 29),   # leap year
        date(2001, 2, 28),   # non-leap
        date(2100, 2, 28),   # century non-leap
        date(1970, 1, 1),    # Unix epoch
        date(9999, 12, 31),  # max date
        date(1, 1, 1),       # min date
    ]


def gen_cpf() -> str:
    """Generate a syntactically valid Brazilian CPF."""
    digits = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(digits) + 1 - i) * d for i, d in enumerate(digits))
        digits.append((11 - (s % 11)) % 10)
    return ''.join(map(str, digits))


def gen_email() -> str:
    domains = ["example.com", "test.org", "mail.net", "auditai.local"]
    user = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 12)))
    return f"{user}@{random.choice(domains)}"


def gen_invalid_inputs() -> list:
    """Adversarial inputs likely to break parsers or validation."""
    return [
        "",                          # empty
        " " * 1000,                  # whitespace
        "\x00\x01\x02",              # null bytes
        "a" * 10001,                 # too long
        "<script>alert(1)</script>", # XSS attempt
        "' OR '1'='1",               # SQL injection
        "../../../etc/passwd",       # path traversal
        "{{7*7}}",                   # template injection
        "\u0000",                    # unicode null
        "😀" * 100,                  # emoji flood
        "-1",                        # negative number
        "9" * 100,                   # huge number
        "NaN",                       # not a number
        "Infinity",                  # infinity
        "null", "undefined", "None", # null variants
        "true", "false",             # boolean strings
        "[]", "{}", "[[]]",          # JSON primitives
    ]
