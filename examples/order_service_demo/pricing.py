def calculate_total(unit_price: float, quantity: int, member: bool = False) -> float:
    """
    Calculate an order total.

    Business rule:
    - Members receive a 10% discount when the subtotal is at least 100.
    - The returned amount is rounded to two decimal places.
    """
    subtotal = unit_price * quantity

    if member and subtotal > 100:
        subtotal *= 0.90

    return round(subtotal, 2)
