def validate_order(order: dict) -> None:
    """Validate fields required by the order-processing pipeline."""
    sku = order.get("sku")
    quantity = order.get("quantity")
    unit_price = order.get("unit_price")

    if not isinstance(sku, str) or not sku.strip():
        raise ValueError("sku must be a non-empty string")

    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")

    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        raise ValueError("unit_price must be non-negative")
