"""
Banking domain properties — financial invariants to test.
"""
from decimal import Decimal
from typing import Any, Callable


def check_balance_preservation(
    initial_balance: Decimal, debit: Decimal, credit: Decimal, final_balance: Decimal
) -> bool:
    """initial + credit - debit == final (conservation of value)."""
    return initial_balance + credit - debit == final_balance


def check_non_negative_after_debit(balance: Decimal, amount: Decimal) -> bool:
    """A debit must not produce a negative balance (without overdraft)."""
    return (balance - amount) >= Decimal("0.00")


def check_rounding_two_decimals(amount: Decimal) -> bool:
    """Monetary amounts must never have more than 2 decimal places."""
    return amount == amount.quantize(Decimal("0.01"))


def check_no_money_created(transfers: list) -> bool:
    """Sum of all debits must equal sum of all credits (no money created)."""
    total_debit = sum(t["amount"] for t in transfers if t["type"] == "debit")
    total_credit = sum(t["amount"] for t in transfers if t["type"] == "credit")
    return total_debit == total_credit


def check_transaction_idempotency(process_fn: Callable, tx_id: str, payload: Any) -> bool:
    """Processing the same transaction twice must produce the same result."""
    r1 = process_fn(tx_id, payload)
    r2 = process_fn(tx_id, payload)
    return r1 == r2


def check_reversal_cancels_original(amount: Decimal, apply_fn: Callable, reverse_fn: Callable,
                                     initial_balance: Decimal) -> bool:
    """apply then reverse must restore original balance."""
    after_apply = apply_fn(initial_balance, amount)
    after_reverse = reverse_fn(after_apply, amount)
    return after_reverse == initial_balance
