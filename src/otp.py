from .basics import BasicFunctions

def otp(builder, plaintext_vars, key_vars):
    ciphertext_vars = []
    for i in range(len(plaintext_vars)):
        ciphertext_bit = builder.var(f"ciphertext_{i}")

        builder.xor([
            plaintext_vars[i],
            key_vars[i],
            ciphertext_bit
        ])

        ciphertext_vars.append(ciphertext_bit)

    return ciphertext_vars