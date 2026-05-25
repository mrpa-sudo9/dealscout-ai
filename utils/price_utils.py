from decimal import Decimal


def calculate_discount(current_price: Decimal, avg_price: Decimal) -> float:
    if avg_price <= 0:
        return 0.0
    return float((1 - current_price / avg_price) * 100)


def is_significant_discount(current_price: Decimal, avg_price: Decimal, threshold: float = 15.0) -> bool:
    return calculate_discount(current_price, avg_price) >= threshold
