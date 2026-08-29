from inventory import reserve_stock
from order_parser import parse_order
from pricing import calculate_total
from validator import validate_order


def process_order(order_text: str, stock: dict[str, int], member: bool = False) -> dict:
    """Parse, validate, price, and reserve one order."""
    order = parse_order(order_text)
    validate_order(order)

    total = calculate_total(
        unit_price=order["unit_price"],
        quantity=order["quantity"],
        member=member,
    )

    remaining = reserve_stock(
        stock=stock,
        sku=order["sku"],
        quantity=order["quantity"],
    )

    return {
        "sku": order["sku"],
        "quantity": order["quantity"],
        "total": total,
        "remaining_stock": remaining,
    }
