from src.basics import BasicFunctions
from src.gift_cofb import *
from pysat.solvers import Kissat404

def test_cofb_pad_full_block():
    builder = BasicFunctions()

    data = []

    for i in range(128):
        data.append(
            builder.var(f"data_{i}")
        )

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_full"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    assert blocks[0] == data

def test_cofb_pad_partial_block():
    builder = BasicFunctions()

    data = []

    for i in range(10):
        data.append(
            builder.var(f"data_{i}")
        )

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_partial"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    assert blocks[0][:10] == data

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    assert blocks[0][10] in model

    for i in range(11, 128):
        assert -blocks[0][i] in model

def test_cofb_pad_empty():
    builder = BasicFunctions()

    data = []

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_empty"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    assert blocks[0][0] in model

    for i in range(1, 128):
        assert -blocks[0][i] in model

def test_cofb_g():
    test_positions = [
        (0, 127),
        (1, 64),
        (63, 126),
        (64, 0),
        (65, 1),
        (127, 63)
    ]

    for source, expected_destination in test_positions:
        builder = BasicFunctions()

        y = []

        for i in range(128):
            var = builder.var(f"y_{source}_{i}")
            y.append(var)

            if i == source:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_g(
            builder,
            y,
            f"test_g_{source}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        for i in range(128):
            if i == expected_destination:
                assert output[i] in model
            else:
                assert -output[i] in model

def test_cofb_double():
    test_cases = [
        (
            0x0123456789ABCDEF,
            0x02468ACF13579BDE
        ),
        (
            0x8000000000000000,
            0x000000000000001B
        )
    ]

    for case_index, (
        input_value,
        expected_value
    ) in enumerate(test_cases):

        builder = BasicFunctions()

        l = []

        for i in range(64):
            var = builder.var(
                f"double_{case_index}_{i}"
            )

            l.append(var)

            bit = (
                input_value >> (63 - i)
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_double(
            builder,
            l,
            f"test_double_{case_index}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        output_value = 0

        for i in range(64):
            output_value <<= 1

            if output[i] in model:
                output_value |= 1

        assert output_value == expected_value

def test_cofb_triple():
    test_cases = [
        (
            0x0123456789ABCDEF,
            0x0365CFA89AFC5631
        ),
        (
            0x8000000000000000,
            0x800000000000001B
        )
    ]

    for case_index, (
        input_value,
        expected_value
    ) in enumerate(test_cases):

        builder = BasicFunctions()

        l = []

        for i in range(64):
            var = builder.var(
                f"triple_{case_index}_{i}"
            )

            l.append(var)

            bit = (
                input_value >> (63 - i)
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_triple(
            builder,
            l,
            f"test_triple_{case_index}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        output_value = 0

        for i in range(64):
            output_value <<= 1

            if output[i] in model:
                output_value |= 1

        assert output_value == expected_value

def test_cofb_gift_encrypt():
    builder = BasicFunctions()

    plaintext_bytes = [
        0x00, 0x01, 0x02, 0x03,
        0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B,
        0x0C, 0x0D, 0x0E, 0x0F
    ]

    key_bytes = [
        0x00, 0x01, 0x02, 0x03,
        0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B,
        0x0C, 0x0D, 0x0E, 0x0F
    ]

    expected_ciphertext = [
        0xA9, 0x4A, 0xF7, 0xF9,
        0xBA, 0x18, 0x1D, 0xF9,
        0xB2, 0xB0, 0x0E, 0xB7,
        0xDB, 0xFA, 0x93, 0xDF
    ]

    plaintext = []
    key = []

    for byte_index, byte in enumerate(
        plaintext_bytes
    ):
        for bit_index in range(7, -1, -1):
            var = builder.var(
                f"plaintext_{byte_index}_{bit_index}"
            )

            plaintext.append(var)

            bit = (
                byte >> bit_index
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    for byte_index, byte in enumerate(
        key_bytes
    ):
        for bit_index in range(7, -1, -1):
            var = builder.var(
                f"key_{byte_index}_{bit_index}"
            )

            key.append(var)

            bit = (
                byte >> bit_index
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    output = cofb_gift_encrypt(
        builder,
        plaintext,
        key,
        "test_cofb_gift"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    ciphertext = []

    for byte_index in range(16):
        value = 0

        for bit_index in range(8):
            value <<= 1

            var = output[
                byte_index * 8 + bit_index
            ]

            if var in model:
                value |= 1

        ciphertext.append(value)

    assert ciphertext == expected_ciphertext

def test_cofb_mask_block():
    builder = BasicFunctions()

    l = []

    for i in range(64):
        l.append(
            builder.var(f"l_{i}")
        )

    output = cofb_mask_block(
        builder,
        l,
        "test_mask"
    )

    assert len(output) == 128

    assert output[:64] == l

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    for i in range(64, 128):
        assert -output[i] in model

def test_cofb_xor_blocks():
    builder = BasicFunctions()

    a_bits = [1, 0, 1, 0]
    b_bits = [1, 1, 0, 0]
    c_bits = [0, 0, 1, 1]

    a = []
    b = []
    c = []

    for i in range(4):
        a_var = builder.var(
            f"a_{i}"
        )

        b_var = builder.var(
            f"b_{i}"
        )

        c_var = builder.var(
            f"c_{i}"
        )

        a.append(a_var)
        b.append(b_var)
        c.append(c_var)

        builder.cnf.append(
            [a_var]
            if a_bits[i] == 1
            else [-a_var]
        )

        builder.cnf.append(
            [b_var]
            if b_bits[i] == 1
            else [-b_var]
        )

        builder.cnf.append(
            [c_var]
            if c_bits[i] == 1
            else [-c_var]
        )

    output = cofb_xor_blocks(
        builder,
        [a, b, c],
        "test_xor"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    expected = [
        0,
        1,
        0,
        1
    ]

    for i in range(4):
        if expected[i] == 1:
            assert output[i] in model
        else:
            assert -output[i] in model

def test_cofb_triple_squared():
    builder = BasicFunctions()

    input_value = 0x8000000000000000
    expected_value = 0x8000000000000036

    l = []

    for i in range(64):
        var = builder.var(
            f"triple_squared_{i}"
        )

        l.append(var)

        bit = (
            input_value >> (63 - i)
        ) & 1

        if bit == 1:
            builder.cnf.append([var])
        else:
            builder.cnf.append([-var])

    output = cofb_triple_squared(
        builder,
        l,
        "test_triple_squared"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    output_value = 0

    for i in range(64):
        output_value <<= 1

        if output[i] in model:
            output_value |= 1

    assert output_value == expected_value

def test_cofb_process_associated_data():
    builder = BasicFunctions()

    associated_data = []
    y = []
    l = []
    key = []

    for i in range(128):
        ad_var = builder.var(
            f"process_ad_{i}"
        )

        y_var = builder.var(
            f"process_y_{i}"
        )

        key_var = builder.var(
            f"process_key_{i}"
        )

        associated_data.append(ad_var)
        y.append(y_var)
        key.append(key_var)

        builder.cnf.append([-ad_var])
        builder.cnf.append([-y_var])
        builder.cnf.append([-key_var])

    for i in range(64):
        l_var = builder.var(
            f"process_l_{i}"
        )

        l.append(l_var)

        builder.cnf.append([-l_var])

    output_y, output_l = (
        cofb_process_associated_data(
            builder,
            associated_data,
            y,
            l,
            key,
            message_is_empty=False,
            prefix="test_process_ad"
        )
    )

    assert len(output_y) == 128
    assert len(output_l) == 64

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    for var in output_l:
        assert -var in model

def test_cofb_process_message_partial():
    builder = BasicFunctions()

    message_bits = [
        1, 0, 1, 1, 0,
        0, 1, 0, 1, 0
    ]

    y_bits = [
        0, 1, 1, 0, 0,
        1, 0, 0, 1, 1
    ]

    message = []
    y = []
    l = []
    key = []

    for i in range(
        len(message_bits)
    ):
        var = builder.var(
            f"message_{i}"
        )

        message.append(var)

        if message_bits[i] == 1:
            builder.cnf.append([var])
        else:
            builder.cnf.append([-var])

    for i in range(128):
        var = builder.var(
            f"message_y_{i}"
        )

        y.append(var)

        if (
            i < len(y_bits)
            and
            y_bits[i] == 1
        ):
            builder.cnf.append([var])
        else:
            builder.cnf.append([-var])

    for i in range(64):
        var = builder.var(
            f"message_l_{i}"
        )

        l.append(var)

        builder.cnf.append([-var])

    for i in range(128):
        var = builder.var(
            f"message_key_{i}"
        )

        key.append(var)

        builder.cnf.append([-var])

    ciphertext, output_y, output_l = (
        cofb_process_message(
            builder,
            message,
            y,
            l,
            key,
            "test_message"
        )
    )

    assert len(ciphertext) == len(
        message_bits
    )

    assert len(output_y) == 128
    assert len(output_l) == 64

    expected_ciphertext = []

    for i in range(
        len(message_bits)
    ):
        expected_ciphertext.append(
            message_bits[i] ^ y_bits[i]
        )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    for i in range(
        len(expected_ciphertext)
    ):
        if expected_ciphertext[i] == 1:
            assert ciphertext[i] in model
        else:
            assert -ciphertext[i] in model

    for var in output_l:
        assert -var in model

def test_gift_cofb_encrypt_empty_message():
    builder = BasicFunctions()

    nonce = []
    key = []

    for i in range(128):
        nonce_var = builder.var(
            f"full_nonce_{i}"
        )

        key_var = builder.var(
            f"full_key_{i}"
        )

        nonce.append(nonce_var)
        key.append(key_var)

        builder.cnf.append(
            [-nonce_var]
        )

        builder.cnf.append(
            [-key_var]
        )

    associated_data = []
    message = []

    ciphertext, tag = gift_cofb_encrypt(
        builder,
        nonce,
        associated_data,
        message,
        key,
        "test_full_empty"
    )

    assert ciphertext == []
    assert len(tag) == 128

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()

def kat_bytes_to_sat_bits(
    builder,
    data,
    prefix
):
    bits = []

    for byte_index, byte in enumerate(data):
        for bit_index in range(7, -1, -1):
            var = builder.var(
                f"{prefix}_{byte_index}_{bit_index}"
            )

            bits.append(var)

            bit = (
                byte >> bit_index
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    return bits

def kat_sat_bits_to_bytes(
    bits,
    model
):
    result = []

    model_set = set(model)

    for start in range(
        0,
        len(bits),
        8
    ):
        value = 0

        for var in bits[
            start:start + 8
        ]:
            value <<= 1

            if var in model_set:
                value |= 1

        result.append(value)

    return bytes(result)

def run_gift_cofb_kat(
    key_hex,
    nonce_hex,
    plaintext_hex,
    associated_data_hex,
    expected_hex,
    prefix
):
    builder = BasicFunctions()

    key_bytes = bytes.fromhex(
        key_hex
    )

    nonce_bytes = bytes.fromhex(
        nonce_hex
    )

    plaintext_bytes = bytes.fromhex(
        plaintext_hex
    )

    associated_data_bytes = bytes.fromhex(
        associated_data_hex
    )

    expected_bytes = bytes.fromhex(
        expected_hex
    )

    key = kat_bytes_to_sat_bits(
        builder,
        key_bytes,
        f"{prefix}_key"
    )

    nonce = kat_bytes_to_sat_bits(
        builder,
        nonce_bytes,
        f"{prefix}_nonce"
    )

    plaintext = kat_bytes_to_sat_bits(
        builder,
        plaintext_bytes,
        f"{prefix}_plaintext"
    )

    associated_data = kat_bytes_to_sat_bits(
        builder,
        associated_data_bytes,
        f"{prefix}_ad"
    )

    ciphertext, tag = gift_cofb_encrypt(
        builder,
        nonce,
        associated_data,
        plaintext,
        key,
        prefix
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()

        model = solver.get_model()

    actual_ciphertext = (
        kat_sat_bits_to_bytes(
            ciphertext,
            model
        )
    )

    actual_tag = (
        kat_sat_bits_to_bytes(
            tag,
            model
        )
    )

    expected_ciphertext = (
        expected_bytes[
            :len(plaintext_bytes)
        ]
    )

    expected_tag = (
        expected_bytes[
            len(plaintext_bytes):
        ]
    )

    assert (
        len(expected_tag)
        == 16
    )

    assert (
        actual_ciphertext
        == expected_ciphertext
    )

    assert (
        actual_tag
        == expected_tag
    )

def test_gift_cofb_kat_count_1():
    run_gift_cofb_kat(
        key_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        nonce_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        plaintext_hex="",
        associated_data_hex="",
        expected_hex=(
            "368965836D36614DE2FC24D0F801B9AF"
        ),
        prefix="kat_1"
    )

def test_gift_cofb_kat_count_2():
    run_gift_cofb_kat(
        key_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        nonce_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        plaintext_hex="",
        associated_data_hex="00",
        expected_hex=(
            "AE5DCDD1285D5177FE251DEB99D727DC"
        ),
        prefix="kat_2"
    )

def test_gift_cofb_kat_count_34():
    run_gift_cofb_kat(
        key_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        nonce_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        plaintext_hex="00",
        associated_data_hex="",
        expected_hex=(
            "5DF96DB329E92688242EF4E06F94FE1BD9"
        ),
        prefix="kat_34"
    )

def test_gift_cofb_kat_count_545():
    run_gift_cofb_kat(
        key_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        nonce_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        plaintext_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        associated_data_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        expected_hex=(
            "3BFF715A56CBA49D1F7AC0691A966FDC"
            "BF77814044BF3FC9A9DEBBD393F545D4"
        ),
        prefix="kat_545"
    )

def test_gift_cofb_kat_count_1089():
    run_gift_cofb_kat(
        key_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        nonce_hex=(
            "000102030405060708090A0B0C0D0E0F"
        ),
        plaintext_hex=(
            "000102030405060708090A0B0C0D0E0F"
            "101112131415161718191A1B1C1D1E1F"
        ),
        associated_data_hex=(
            "000102030405060708090A0B0C0D0E0F"
            "101112131415161718191A1B1C1D1E1F"
        ),
        expected_hex=(
            "BAF563C60FBEDDC5662995F4C678BE80"
            "A7F7DE9B3AD8C97AA6CA17016D2AE65"
            "08E6FB3F79B412A1627AB7DFA755E0A22"
        ),
        prefix="kat_1089"
    )