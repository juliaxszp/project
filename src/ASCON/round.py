from src.ascon import (
    add_constant,
    S_box_64,
    Linear_Diffusion
)


def round_function(Builder, state, constant, round_number=0):
    prefix = f"R{round_number}_"

    S0, S1, S2, S3, S4 = state

    # Add constant
    S2 = add_constant(
        Builder,
        S2,
        constant,
        prefix=prefix
    )

    # S-box
    S0, S1, S2, S3, S4 = S_box_64(
        Builder,
        S0,
        S1,
        S2,
        S3,
        S4,
        prefix=prefix
    )

    # Linear diffusion
    S0 = Linear_Diffusion(Builder, S0, 19, 28, prefix=f"{prefix}S0_")
    S1 = Linear_Diffusion(Builder, S1, 61, 39, prefix=f"{prefix}S1_")
    S2 = Linear_Diffusion(Builder, S2, 1, 6, prefix=f"{prefix}S2_")
    S3 = Linear_Diffusion(Builder, S3, 10, 17, prefix=f"{prefix}S3_")
    S4 = Linear_Diffusion(Builder, S4, 7, 41, prefix=f"{prefix}S4_")

    return [S0, S1, S2, S3, S4]