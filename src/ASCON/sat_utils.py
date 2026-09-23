def force_bit(builder, var, bit_value):

    if bit_value == 1:
        builder.cnf.append([var])
    else:
        builder.cnf.append([-var])




def get_bit_value(model, var):
    return 1 if var in model else 0


def extract_bits(model, variables):
    return [get_bit_value(model, var) for var in variables]