import time

from pysat.solvers import Kissat404

from .basics import BasicFunctions
from .rommulus import (
    SubCells,
    AddConstants,
    AddRoundTweakey,
    ShiftRows,
    MixColumns,
)

KEY_HEX = "000102030405060708090A0B0C0D0E0F"
NONCE_HEX = "000102030405060708090A0B0C0D0E0F"

PT_HEX = ""
AD_HEX = "000102030405060708090A0B0C0D0E0F101112"

EXPECTED_TAG = "099377EB20CE32F6C2741C0271D420BF"

UNKNOWN_BITS = [2, 4, 6, 8, 10, 12, 14, 16]

PATTERNS = ["start", "end", "middle", "every_2"]

def fixed_byte(builder, value):
    out = []

    for b in range(8):
        v = builder.idp.id()

        if (value >> b) & 1:
            builder.cnf.append([v])
        else:
            builder.cnf.append([-v])

        out.append(v)

    return out


def xor_byte(builder, byte_vars, value):
    out = []

    for b in range(8):
        v = builder.idp.id()

        if (value >> b) & 1:
            builder.equals_not(v, byte_vars[b])
        else:
            builder.equals(v, byte_vars[b])

        out.append(v)

    return out


def xor_block(builder, state, block):
    out = []

    for i in range(16):
        out.append(
            xor_byte(
                builder,
                state[i],
                block[i]
            )
        )

    return out


def pad_128(data):
    if len(data) == 16:
        return data

    if len(data) == 0:
        return bytes(16)

    return (
        data
        + bytes(15 - len(data))
        + bytes([len(data)])
    )


def lfsr56(D):
    x = 1

    for _ in range(D):
        msb = (x >> 55) & 1
        x = (x << 1) & ((1 << 56) - 1)

        if msb:
            x ^= 0x95

    return x


def make_tk(builder, key, nonce, tweak, domain, D):
    tk = []

    for x in lfsr56(D).to_bytes(7, "little"):
        tk.append(
            fixed_byte(builder, x)
        )

    tk.append(
        fixed_byte(builder, domain)
    )

    for _ in range(8):
        tk.append(
            fixed_byte(builder, 0)
        )

    for x in tweak:
        tk.append(
            fixed_byte(builder, x)
        )

    for i in range(16):
        tk.append(
            key[i * 8:(i + 1) * 8]
        )

    return tk


def skinny(builder, state, tk):

    state = [
        state[i * 4:(i + 1) * 4]
        for i in range(4)
    ]

    tk1 = [
        tk[i * 4:(i + 1) * 4]
        for i in range(4)
    ]

    tk2 = [
        tk[16 + i * 4:16 + (i + 1) * 4]
        for i in range(4)
    ]

    tk3 = [
        tk[32 + i * 4:32 + (i + 1) * 4]
        for i in range(4)
    ]

    for r in range(40):

        state = SubCells(
            builder,
            state
        )

        state = AddConstants(
            builder,
            state,
            r
        )

        state, tk1, tk2, tk3 = AddRoundTweakey(
            builder,
            state,
            tk1,
            tk2,
            tk3
        )

        state = ShiftRows(
            builder,
            state
        )

        state = MixColumns(
            builder,
            state
        )

    return [
        state[r][c]
        for r in range(4)
        for c in range(4)
    ]

def process_ad(builder, ad, key, nonce):

    if len(ad) == 0:
        blocks = [b""]
    else:
        blocks = [
            ad[i:i + 16]
            for i in range(0, len(ad), 16)
        ]

    a = len(blocks)

    last_block_full = (
        len(ad) != 0
        and len(ad) % 16 == 0
    )

    blocks[-1] = pad_128(
        blocks[-1]
    )

    if last_block_full:
        domain = 0x18
    else:
        domain = 0x1A

    state = [
        fixed_byte(builder, 0)
        for _ in range(16)
    ]

    for i in range(0, a - 1, 2):

        first = blocks[i]
        second = blocks[i + 1]

        state = xor_block(
            builder,
            state,
            first
        )

        tk = make_tk(
            builder,
            key,
            nonce,
            second,
            0x08,
            i + 1
        )

        state = skinny(
            builder,
            state,
            tk
        )

    if a % 2 == 1:
        last = blocks[-1]
    else:
        last = bytes(16)

    state = xor_block(
        builder,
        state,
        last
    )

    tk = make_tk(
        builder,
        key,
        nonce,
        nonce,
        domain,
        a
    )

    state = skinny(
        builder,
        state,
        tk
    )

    return state

def unknown_positions(unknown_bits, pattern):

    if pattern == "start":
        return list(
            range(unknown_bits)
        )

    if pattern == "end":
        return list(
            range(
                128 - unknown_bits,
                128
            )
        )

    if pattern == "middle":
        start = (
            128 - unknown_bits
        ) // 2

        return list(
            range(
                start,
                start + unknown_bits
            )
        )

    if pattern == "every_2":
        return list(
            range(
                0,
                2 * unknown_bits,
                2
            )
        )

    raise ValueError(
        "Nieznany pattern"
    )

def build_test(
    unknown_bits,
    pattern
):

    builder = BasicFunctions()

    real_key = bytes.fromhex(
        KEY_HEX
    )

    nonce = bytes.fromhex(
        NONCE_HEX
    )

    ad = bytes.fromhex(
        AD_HEX
    )

    key = [
        builder.idp.id()
        for _ in range(128)
    ]

    key_bits = []

    for x in real_key:
        for b in range(8):
            key_bits.append(
                (x >> b) & 1
            )

    unknown = set(
        unknown_positions(
            unknown_bits,
            pattern
        )
    )

    for i in range(128):

        if i in unknown:
            continue

        if key_bits[i]:
            builder.cnf.append(
                [key[i]]
            )
        else:
            builder.cnf.append(
                [-key[i]]
            )

    state = process_ad(
        builder,
        ad,
        key,
        nonce
    )

    tk = make_tk(
        builder,
        key,
        nonce,
        nonce,
        0x15,
        1
    )

    state = skinny(
        builder,
        state,
        tk
    )

    tag = []

    for x in state:

        y = []

        for b in range(1, 8):
            y.append(
                x[b]
            )

        v = builder.idp.id()

        builder.xor([
            v,
            x[7],
            x[0]
        ])

        y.append(v)

        tag.append(y)

    expected = bytes.fromhex(
        EXPECTED_TAG
    )

    for i in range(16):

        for b in range(8):

            bit = (
                expected[i] >> b
            ) & 1

            if bit:
                builder.cnf.append(
                    [tag[i][b]]
                )
            else:
                builder.cnf.append(
                    [-tag[i][b]]
                )

    return (
        builder,
        key,
        key_bits
    )

for unknown_bits in UNKNOWN_BITS:

    for pattern in PATTERNS:

        print()
        print("=" * 60)

        print(
            f"Nieznane bity: {unknown_bits}"
        )

        print(
            f"Rozmieszczenie: {pattern}"
        )

        builder, key, real_bits = build_test(
            unknown_bits,
            pattern
        )

        unknown = unknown_positions(
            unknown_bits,
            pattern
        )

        print(
            f"Pozycje nieznane: {unknown}"
        )

        print(
            f"Zmienne: {builder.idp.top}"
        )

        print(
            f"Klauzule: "
            f"{len(builder.cnf.clauses)}"
        )

        with Kissat404(
            bootstrap_with=
            builder.cnf.clauses
        ) as solver:

            start = time.perf_counter()

            result = solver.solve()

            elapsed = (
                time.perf_counter()
                - start
            )

            print(
                f"SAT: {result}"
            )

            print(
                f"Czas: "
                f"{elapsed:.6f} s"
            )

            if not result:
                continue

            model = set(
                solver.get_model()
            )

            recovered = []

            for v in key:

                if v in model:
                    recovered.append(1)
                else:
                    recovered.append(0)

            recovered_hex = ""

            for i in range(
                0,
                128,
                8
            ):

                value = 0

                for b in range(8):
                    value |= (
                        recovered[i + b]
                        << b
                    )

                recovered_hex += (
                    f"{value:02X}"
                )

            print(
                f"Odzyskany klucz: "
                f"{recovered_hex}"
            )

            print(
                f"Poprawny klucz:   "
                f"{KEY_HEX}"
            )

            print(
                f"OK: "
                f"{recovered_hex == KEY_HEX}"
            )