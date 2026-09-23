from src.ASCON.iv import ASCON128_IV


def test_ascon128_iv():
    assert ASCON128_IV == 0x80400c0600000000