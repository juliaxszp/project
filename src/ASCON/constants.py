def get_const_zero(Builder):
    if not hasattr(Builder, "_const_zero"):
        Builder._const_zero = Builder.var("__CONST_ZERO__")
        Builder.cnf.append([-Builder._const_zero])

    return Builder._const_zero


def get_const_one(Builder):
    if not hasattr(Builder, "_const_one"):
        Builder._const_one = Builder.var("__CONST_ONE__")
        Builder.cnf.append([Builder._const_one])

    return Builder._const_one