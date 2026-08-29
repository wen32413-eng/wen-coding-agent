from order_parser import parse_order


def test_parse_order_basic():
    order = parse_order("sku=KB100;qty=2;price=49.90")

    assert order == {
        "sku": "KB100",
        "quantity": 2,
        "unit_price": 49.90,
    }


def test_parse_order_trims_and_normalizes_sku():
    order = parse_order(" sku =  kb100 ; qty = 1 ; price = 15.5 ")

    assert order["sku"] == "KB100"
    assert order["quantity"] == 1
    assert order["unit_price"] == 15.5
