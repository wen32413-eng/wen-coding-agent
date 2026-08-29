from pricing import calculate_total


def test_non_member_has_no_discount():
    assert calculate_total(25.0, 4, member=False) == 100.0


def test_member_discount_above_threshold():
    assert calculate_total(60.0, 2, member=True) == 108.0


def test_member_discount_at_exact_threshold():
    assert calculate_total(25.0, 4, member=True) == 90.0
