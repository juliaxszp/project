def int_to_bits(value, size):
    bits = []

    for i in range(size):
        bits.append((value >> i) & 1)

    return bits

def bits_to_int(bits):
    value = 0

    for i, bit in enumerate(bits):
        if bit:
            value |= 1 << i

    return value