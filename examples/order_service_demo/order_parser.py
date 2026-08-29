def parse_order(text: str) -> dict:
    """
    Parse an order string such as:
        "sku=KB100;qty=2;price=49.90"

    Returns a normalized order dictionary.
    """
    parts = {}

    for item in text.split(";"):
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()

    return {
        "sku": parts["sku"].strip(),
        "quantity": int(parts["qty"]),
        "unit_price": float(parts["price"]),
    }
