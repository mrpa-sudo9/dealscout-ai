import pytest
from decimal import Decimal

from utils.price_utils import calculate_discount, is_significant_discount


@pytest.mark.parametrize("current,avg,expected", [
    (Decimal("80"), Decimal("100"), 20.0),
    (Decimal("50"), Decimal("100"), 50.0),
    (Decimal("100"), Decimal("100"), 0.0),
    (Decimal("120"), Decimal("100"), -20.0),
])
def test_calculate_discount(current, avg, expected):
    assert calculate_discount(current, avg) == expected


@pytest.mark.parametrize("current,avg,threshold,expected", [
    (Decimal("80"), Decimal("100"), 20.0, True),
    (Decimal("85"), Decimal("100"), 20.0, False),
    (Decimal("50"), Decimal("100"), 15.0, True),
])
def test_is_significant_discount(current, avg, threshold, expected):
    assert is_significant_discount(current, avg, threshold) == expected
