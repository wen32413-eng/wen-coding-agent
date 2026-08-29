from app import process_order


def test_process_order_end_to_end():
    stock = {"KB100": 5}

    result = process_order(
        "sku=KB100;qty=2;price=60",
        stock,
        member=True,
    )

    assert result == {
        "sku": "KB100",
        "quantity": 2,
        "total": 108.0,
        "remaining_stock": 3,
    }


def test_process_order_can_consume_last_item():
    stock = {"MS200": 1}

    result = process_order(
        "sku=MS200;qty=1;price=100",
        stock,
        member=True,
    )

    assert result["total"] == 90.0
    assert result["remaining_stock"] == 0
