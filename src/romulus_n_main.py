import sys

from .basics import BasicFunctions
from .functions import *
from .rommulus import (
    SubCells,
    AddConstants,
    AddRoundTweakey,
    ShiftRows,
    MixColumns,
)

from pysat.solvers import Kissat404

from pysat.solvers import Kissat404

def lfsr56_step(x):
    mask56 = (1 << 56) - 1

    msb = (x >> 55) & 1

    x = (x << 1) & mask56

    if msb:
        x ^= 0x95

    return x


def lfsr56(D):
    state = 1

    for _ in range(D):
        state = lfsr56_step(state)

    return state

def make_tweakey(nonce, key, tweak, domain, D):
    lfsr_state = lfsr56(D)

    return (
        lfsr_state.to_bytes(7, "little")
        + bytes([domain])
        + bytes(8)
        + tweak
        + key
    )


def skinny_encrypt_state(S, tweakey_bytes):

    builder = BasicFunctions()

    state_vars = []

    for r in range(4):
        row = []

        for c in range(4):

            byte_vars = [
                builder.idp.id()
                for _ in range(8)
            ]

            row.append(byte_vars)

            value = S[4 * r + c]

            for b in range(8):

                if (value >> b) & 1:
                    builder.cnf.append(
                        [byte_vars[b]]
                    )
                else:
                    builder.cnf.append(
                        [-byte_vars[b]]
                    )

        state_vars.append(row)

    tk1_vars = []
    tk2_vars = []
    tk3_vars = []

    for arr, offset in (
        (tk1_vars, 0),
        (tk2_vars, 16),
        (tk3_vars, 32),
    ):

        for r in range(4):

            row = []

            for c in range(4):

                byte_vars = [
                    builder.idp.id()
                    for _ in range(8)
                ]

                row.append(byte_vars)

                value = tweakey_bytes[
                    offset + 4 * r + c
                ]

                for b in range(8):

                    if (value >> b) & 1:
                        builder.cnf.append(
                            [byte_vars[b]]
                        )
                    else:
                        builder.cnf.append(
                            [-byte_vars[b]]
                        )

            arr.append(row)

    for round_num in range(40):

        state_vars = SubCells(
            builder,
            state_vars
        )

        state_vars = AddConstants(
            builder,
            state_vars,
            round_num
        )

        (
            state_vars,
            tk1_vars,
            tk2_vars,
            tk3_vars,
        ) = AddRoundTweakey(
            builder,
            state_vars,
            tk1_vars,
            tk2_vars,
            tk3_vars,
        )

        state_vars = ShiftRows(
            builder,
            state_vars
        )

        state_vars = MixColumns(
            builder,
            state_vars
        )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve(), (
            "Romulus-N Skinny CNF is UNSAT"
        )

        model = solver.get_model()

    model_set = set(model)

    output = bytearray()

    for r in range(4):

        for c in range(4):

            value = 0

            for b in range(8):

                if state_vars[r][c][b] in model_set:
                    value |= 1 << b

            output.append(value)

    return bytes(output)


def pad_128(X):

    if len(X) == 16:
        return X

    if len(X) == 0:
        return bytes(16)

    return (
        X
        + bytes(15 - len(X))
        + bytes([len(X)])
    )


def rho(S, M):

    return bytes(
        x ^ y
        for x, y in zip(S, M)
    )

def process_associated_data(ad, key, nonce):

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

    blocks[-1] = pad_128(blocks[-1])

    if last_block_full:
        wA = 0x18
    else:
        wA = 0x1A

    S = bytes(16)

    for i in range(0, a - 1, 2):

        first = blocks[i]
        second = blocks[i + 1]

        S = rho(
            S,
            first
        )

        D = i + 1

        tweakey = make_tweakey(
            nonce=nonce,
            key=key,
            tweak=second,
            domain=0x08,
            D=D,
        )

        S = skinny_encrypt_state(
            S,
            tweakey
        )

    if a % 2 == 1:

        V = blocks[-1]

    else:

        V = bytes(16)

    S = rho(
        S,
        V
    )

    tweakey = make_tweakey(
        nonce=nonce,
        key=key,
        tweak=nonce,
        domain=wA,
        D=a,
    )

    S = skinny_encrypt_state(
        S,
        tweakey
    )

    return S

if __name__ == "__main__":

    key = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    nonce = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    if len(sys.argv) > 2:

        raise SystemExit(
            "Uzycie: "
            "python3 -m src.romulus_n_main [AD_HEX]"
        )

    try:

        ad = (
            bytes.fromhex(sys.argv[1])
            if len(sys.argv) == 2
            else b""
        )

    except ValueError as exc:

        raise SystemExit(
            f"Niepoprawne AD_HEX: {exc}"
        )

    if len(ad) > 259:

        raise SystemExit(
            "AD jest za dlugie dla limitu Romulus-N "
            "(259 bajtow)."
        )

    S = process_associated_data(
        ad=ad,
        key=key,
        nonce=nonce,
    )

    wM = 0x15

    D = 1

    tweakey_bytes = make_tweakey(
        nonce=nonce,
        key=key,
        tweak=nonce,
        domain=wM,
        D=D,
    )

    S = skinny_encrypt_state(
        S,
        tweakey_bytes
    )

    tag = bytes(
        (
            ((x >> 1) & 0x7F)
            |
            (
                (
                    ((x >> 7) & 1)
                    ^ (x & 1)
                )
                << 7
            )
        )
        for x in S
    )

    print(
        f"AD={ad.hex().upper()}"
        if ad
        else
        "AD="
    )

    print(
        f"CT={tag.hex().upper()}"
    )