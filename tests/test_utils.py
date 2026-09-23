from src.ASCON.utils import int_to_bits


def test_int_to_bits():
    assert int_to_bits(5, 4) == [1, 0, 1, 0]