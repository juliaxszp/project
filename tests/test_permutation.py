from src.ascon import BasicFunctions
from src.ASCON.state import create_state
from src.ASCON.permutation import p12
from src.basics import BasicFunctions
from src.ASCON.permutation import p12
from pysat.solvers import Kissat404
from src.ASCON.round import round_function




def test_p12_structure():
    builder = BasicFunctions()
    state = create_state(builder)

    output = p12(builder, state)

    assert len(output) == 5

    for word in output:
        assert len(word) == 64




def test_p12_zero_state():
    builder = BasicFunctions()

    state = []

    for word in range(5):
        bits = []

        for bit in range(64):
            bits.append(builder.var(f"input_S{word}_{bit}"))

        state.append(bits)

    # Wymuszamy stan wejściowy = 0
    for word in range(5):
        for bit in range(64):
            builder.cnf.append([-state[word][bit]])

    output = p12(builder, state)

    expected_words = [
        0x78EA7AE5CFEBB108,
        0x9B9BFB8513B560F7,
        0x6937F83E03D11A50,
        0x3FE53F36F2C1178C,
        0x45D648E4DEF12C9,
    ]

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

        for word in range(5):
            output_value = 0

            for bit in range(64):
                variable = output[word][bit]

                if model[variable - 1] > 0:
                    output_value |= 1 << bit

            assert output_value == expected_words[word]





def test_p12_zero_state_debug():
    builder = BasicFunctions()

    state = []

    for word in range(5):
        bits = []

        for bit in range(64):
            bits.append(builder.var(f"debug_S{word}_{bit}"))

        state.append(bits)

    for word in range(5):
        for bit in range(64):
            builder.cnf.append([-state[word][bit]])

    # jedna runda
    output = round_function(
        builder,
        state,
        0xf0,
        round_number="debug_0"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:
        assert solver.solve()




def test_round_stages_debug():
    builder = BasicFunctions()

    state = []
    for word in range(5):
        bits = []
        for bit in range(64):
            bits.append(builder.var(f"stage_S{word}_{bit}"))
        state.append(bits)

    for word in range(5):
        for bit in range(64):
            builder.cnf.append([-state[word][bit]])

    # 1. add_constant
    from src.ascon import add_constant, S_box_64, Linear_Diffusion

    S0, S1, S2, S3, S4 = state

    S2 = add_constant(
        builder,
        S2,
        0xf0,
        prefix="debug_add_"
    )

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()

    # 2. S-box
    S0, S1, S2, S3, S4 = S_box_64(
        builder,
        S0, S1, S2, S3, S4,
        prefix="debug_sbox_"
    )

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()

    # 3. pierwsza dyfuzja
    S0 = Linear_Diffusion(
        builder,
        S0,
        19,
        28,
        prefix="debug_ld_0_"
    )

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()