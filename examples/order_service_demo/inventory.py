def reserve_stock(stock: dict[str, int], sku: str, quantity: int) -> int:
    """
    Reserve quantity units from stock and return the remaining amount.

    The caller owns the stock dictionary; successful reservations update it.
    """
    if sku not in stock:
        raise KeyError(f"unknown sku: {sku}")

    available = stock[sku]

    if quantity >= available:
        raise ValueError(
            f"insufficient stock for {sku}: requested={quantity}, available={available}"
        )

    stock[sku] = available - quantity
    return stock[sku]
