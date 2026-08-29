import pytest

from inventory import reserve_stock


def test_reserve_partial_stock():
    stock = {"KB100": 5}

    remaining = reserve_stock(stock, "KB100", 2)

    assert remaining == 3
    assert stock["KB100"] == 3


def test_reserve_exact_available_stock():
    stock = {"KB100": 3}

    remaining = reserve_stock(stock, "KB100", 3)

    assert remaining == 0
    assert stock["KB100"] == 0


def test_reject_reservation_above_available_stock():
    stock = {"KB100": 2}

    with pytest.raises(ValueError):
        reserve_stock(stock, "KB100", 3)
