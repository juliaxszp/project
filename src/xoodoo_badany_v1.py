from .functions import *

RC = [
    0x00000058,
    0x00000038,
    0x000003C0,
    0x000000D0,
    0x00000120,
    0x00000014,
    0x00000060,
    0x0000002C,
    0x00000380,
    0x000000F0,
    0x000001A0,
    0x00000012
]


def slowo_na_int(slowo):
    wynik = 0
    for i in range(32):
        wynik |= slowo[i] << i
    return wynik


def dump_state(nazwa, tablica):
    print(nazwa)

    print(
        f"a00 {slowo_na_int(tablica[0][0]):08x}, "
        f"a01 {slowo_na_int(tablica[0][1]):08x}, "
        f"a02 {slowo_na_int(tablica[0][2]):08x}, "
        f"a03 {slowo_na_int(tablica[0][3]):08x}"
    )

    print(
        f"a10 {slowo_na_int(tablica[1][0]):08x}, "
        f"a11 {slowo_na_int(tablica[1][1]):08x}, "
        f"a12 {slowo_na_int(tablica[1][2]):08x}, "
        f"a13 {slowo_na_int(tablica[1][3]):08x}"
    )

    print(
        f"a20 {slowo_na_int(tablica[2][0]):08x}, "
        f"a21 {slowo_na_int(tablica[2][1]):08x}, "
        f"a22 {slowo_na_int(tablica[2][2]):08x}, "
        f"a23 {slowo_na_int(tablica[2][3]):08x}"
    )

    print()


def xoodoo(tablica):
    for itterator in range(12):
        print(
            f"========== RUNDA {itterator + 1}, "
            f"RC = {RC[itterator]:08x} =========="
        )

        tablica = theta(tablica)
        dump_state("Theta", tablica)

        tablica = rho_west(tablica)
        dump_state("Rho-west", tablica)

        tablica = iota(tablica, itterator)
        dump_state("Iota", tablica)

        tablica = chi(builder, tablica)
        dump_state("Chi", tablica)

        tablica = rho_east(tablica)
        dump_state("Rho-east", tablica)

    return tablica


def utworz_stan_testowy():
    dane = bytes(range(48))

    tablica = {}

    for y in range(3):
        tablica[y] = {}

        for x in range(4):
            tablica[y][x] = []

            idx = ((y * 4) + x) * 4

            for k in range(4):
                bajt = dane[idx + k]

                tablica[y][x] += [
                    (bajt >> i) & 1
                    for i in range(8)
                ]

    return tablica


def main():
    tablica = utworz_stan_testowy()

    print("Stan wejściowy:")
    dump_state("Stan jako słowa 32-bitowe", tablica)

    print("Rozpoczynam Xoodoo[12]")
    print()

    tablica = xoodoo(tablica)

    print("Stan końcowy po Xoodoo[12]:")
    dump_state("Permutation", tablica)


if __name__ == "__main__":
    main()