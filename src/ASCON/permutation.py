from src.ASCON.round import round_function


def p12(Builder, state, prefix="p12_"):

    constants = [
        0xf0,
        0xe1,
        0xd2,
        0xc3,
        0xb4,
        0xa5,
        0x96,
        0x87,
        0x78,
        0x69,
        0x5a,
        0x4b,
    ]

    for round_number, constant in enumerate(constants):
        state = round_function(
            Builder,
            state,
            constant,
            round_number=f"{prefix}{round_number}"
    )

    return state



def p8(Builder, state, prefix="p8_"):
    constants = [
        0xb4, 
        0xa5, 
        0x96, 
        0x87,
        0x78, 
        0x69, 
        0x5a, 
        0x4b,
    ]

    for round_number, constant in enumerate(constants):
        state = round_function(
            Builder,
            state,
            constant,
            round_number=f"{prefix}{round_number}"
        )

    return state



def p6(Builder, state, prefix="p6_"):
    constants = [
        0x96, 
        0x87, 
        0x78,
        0x69, 
        0x5a, 
        0x4b,
    ]

    for round_number, constant in enumerate(constants):
        state = round_function(
            Builder,
            state,
            constant,
            round_number=f"{prefix}{round_number}"
        )

    return state