#Adam Aftyka implementacja xoodyak
import random

from . import xoodyak_functions as xf
from .xoodyak_functions import *
import json


def reset_builder():
    global builder
    xf.builder = type(xf.builder)()
    builder = xf.builder


def xoodoo(tablica):
    for itterator in range(12):
        tablica = theta(tablica)
        tablica = rho_west(tablica)
        tablica = iota(tablica, itterator)
        tablica = chi(builder, tablica)
        tablica = rho_east(tablica)
    return tablica


def xoodoo_sat(tablica, nr_xoodoo):
    for iterrator in range(12):
        tablica = theta_sat(tablica, iterrator, nr_xoodoo)
        tablica = rho_west_sat(tablica)
        tablica = iota_sat(tablica, iterrator, nr_xoodoo)
        tablica = chi_sat(builder, tablica, iterrator, nr_xoodoo)
        tablica = rho_east_sat(tablica)
    return tablica


#funkcja pomocnicza do konwersji list na hex
def bits_to_hex(bity):
    wynik = ""
    for i in range(0, len(bity), 8):
        bajt = 0
        for j in range(8):
            bajt |= bity[i + j] << j
        wynik += f"{bajt:02x}"
    return wynik


def absorb_key(klucz, nonce, tablica):
    bufor = klucz
    bufor += nonce
    bufor += "10"
    bufor += "01"
    bufor += "0" * 26
    bufor += "02"

    #zamiana ciągu na listę
    tablica_sat = {}

    for y in range(3):
        tablica[y] = {}
        tablica_sat[y] = {}

        for x in range(4):
            tablica[y][x] = []

            tablica_sat[y][x] = [
                builder.var(f"initial_state_{y}_{x}_{i}")
                for i in range(32)
            ]

            #ustawianie konkretnych wartości słów
            idx = ((y * 4) + x) * 8
            slowo = bufor[idx:idx + 8]

            #ustawianie na wkladanie w konwencji little endian
            for k in range(4):
                bajt = int(slowo[2 * k: 2 * k + 2], 16)
                tablica[y][x] += [
                    (bajt >> i) & 1
                    for i in range(8)
                ]

    #teraz iteruję po tablicy i ustawiam konkretne zmienne SAT dla wartości jawnych.
    key_sat = []
    nonce_sat = []

    for yprim in range(3):
        for xprim in range(4):
            for iprim in range(32):

                if yprim == 0:
                    tablica_sat[yprim][xprim][iprim] = builder.var(
                        f"key_{xprim}_{iprim}"
                    )

                    key_sat.append(
                        tablica_sat[yprim][xprim][iprim]
                    )

                elif yprim == 1:
                    tablica_sat[yprim][xprim][iprim] = builder.var(
                        f"nonce_{xprim}_{iprim}"
                    )

                    nonce_sat.append(
                        tablica_sat[yprim][xprim][iprim]
                    )

                #wartości formatowe są stałymi, więc można zapisać konkretne wartości do CNF
                if yprim == 2:
                    v = tablica_sat[yprim][xprim][iprim]

                    if tablica[yprim][xprim][iprim] == 1:
                        builder.cnf.append([v])
                    else:
                        builder.cnf.append([-v])

    return tablica, tablica_sat, key_sat, nonce_sat


def absorb_ad(tablica, tablica_sat, AD, dlugosc_AD):

    #pocięcie AD na kawalki o odpowiedniej długości
    kawalki = []

    for a in range((len(AD) // 88) + 1):
        inc = 88

        if a == len(AD) // 88:
            inc = len(AD) - 88 * a

        if inc > 0:
            kawalki.append(
                AD[88 * a:88 * a + inc]
            )

    #obsługa przypadku dodania pustego AD:
    if len(AD) == 0:
        kawalki.append("")

    #teraz wkładamy tablicę z kawałków AD gotowych do dodania do stanu wewnętrznego
    bufory = []

    for b in range(len(kawalki)):
        bufor = kawalki[b]
        bufor += "01"

        zer_do_dodania = (
            (48 * 2) - len(bufor) - 2
        )

        bufor += "0" * zer_do_dodania

        if b == 0:
            bufor += "03"
        else:
            bufor += "00"

        bufory.append(bufor)

    #teraz robimy faktyczne łączenie kawałków AD ze stanem wewnętrznym
    ad_sat = []

    for c in range(len(bufory)):

        tablica = xoodoo(tablica)
        tablica_sat = xoodoo_sat(tablica_sat, c)

        nowa_tablica_sat = {}

        for y in range(3):
            nowa_tablica_sat[y] = {}

            for x in range(4):
                nowa_tablica_sat[y][x] = []

                liczba_bajtow_ad = (
                    len(kawalki[c]) // 2
                )

                idx = ((y * 4) + x) * 8

                slowo = bufory[c][
                    idx:idx + 8
                ]

                slowo_bufora_bin = []

                for k in range(4):
                    bajt = int(
                        slowo[2 * k:2 * k + 2],
                        16
                    )

                    slowo_bufora_bin += [
                        (bajt >> i) & 1
                        for i in range(8)
                    ]

                for i in range(32):

                    tablica[y][x][i] ^= (
                        slowo_bufora_bin[i]
                    )

                    #dodanie zależności do SAT zależnej od bitów AD
                    stary = tablica_sat[y][x][i]

                    nowy = builder.var(
                        f"state_ad_{c}_{y}_{x}_{i}"
                    )

                    nr_bajtu = (
                        (y * 16)
                        + (x * 4)
                        + (i // 8)
                    )

                    if nr_bajtu < liczba_bajtow_ad:

                        nr_bitu = i % 8

                        nr_bajtu_ad = (
                            c * 44
                            + nr_bajtu
                        )

                        ad_var = builder.var(
                            f"ad_{nr_bajtu_ad}_{nr_bitu}"
                        )

                        ad_sat.append(ad_var)

                        builder.xor([
                            stary,
                            ad_var,
                            nowy
                        ])

                    else:

                        if slowo_bufora_bin[i] == 0:
                            builder.equals(
                                stary,
                                nowy
                            )
                        else:
                            builder.equals_not(
                                stary,
                                nowy
                            )

                    nowa_tablica_sat[y][x].append(
                        nowy
                    )

                    #ustawianie wartości dla ad_sat

        tablica_sat = nowa_tablica_sat

    return tablica, tablica_sat, ad_sat


def up_and_down(
    tablica,
    tablica_sat,
    plaintext_i,
    nr_bloku,
    nr_xoodoo,
    plaintext_i_sat
):

    if nr_bloku == 0:

        tablica[2][3][31] ^= 1
        stan_przed_up_sat = {}

        for y in range(3):
            stan_przed_up_sat[y] = {}

            for x in range(4):
                stan_przed_up_sat[y][x] = []

                for i in range(32):

                    stary = tablica_sat[y][x][i]

                    nowy = builder.var(
                        f"before_up_{nr_bloku}_{y}_{x}_{i}"
                    )

                    if (
                        y == 2
                        and x == 3
                        and i == 31
                    ):
                        builder.equals_not(
                            stary,
                            nowy
                        )
                    else:
                        builder.equals(
                            stary,
                            nowy
                        )

                    stan_przed_up_sat[y][x].append(
                        nowy
                    )

        tablica_sat = stan_przed_up_sat

    #wykonanie xoodoo przed uzyskaniem pierwszego fragmentu z_i
    tablica = xoodoo(tablica)

    tablica_sat = xoodoo_sat(
        tablica_sat,
        nr_xoodoo
    )

    #budowanie z_i jako ciag binarny
    z_i = []
    z_i_sat = []

    dlugosc = (
        len(plaintext_i) // 2
    ) * 8

    for y in range(2):
        for x in range(4):
            for i in range(32):

                z_i.append(
                    tablica[y][x][i]
                )

                z_i_sat.append(
                    tablica_sat[y][x][i]
                )

                if len(z_i) == dlugosc:
                    break

            if len(z_i) == dlugosc:
                break

        if len(z_i) == dlugosc:
            break

    z_i = bits_to_hex(z_i)

    bufor = plaintext_i

    bity_tekstu_jawnego = (
        len(plaintext_i) * 4
    )

    bufor += "01"

    ilosc_zer = (
        96 - len(bufor)
    )

    bufor += "0" * ilosc_zer

    #dodanie pi
    nowa_tablica_sat = {}

    for y in range(3):
        nowa_tablica_sat[y] = {}

        for x in range(4):
            nowa_tablica_sat[y][x] = []

            idx = ((y * 4) + x) * 8

            bufor_roboczy = []

            for j in range(4):

                bajt = int(
                    bufor[
                        idx + 2 * j:
                        idx + 2 * j + 2
                    ],
                    16
                )

                bufor_roboczy += [
                    (bajt >> k) & 1
                    for k in range(8)
                ]

            for i in range(32):

                nr_bitu_bufora = (
                    ((y * 4) + x) * 32
                    + i
                )

                tablica[y][x][i] ^= (
                    bufor_roboczy[i]
                )

                stary = tablica_sat[y][x][i]

                nowy = builder.var(
                    f"after_pt_state_{nr_bloku}_{y}_{x}_{i}"
                )

                if (
                    nr_bitu_bufora
                    < bity_tekstu_jawnego
                ):

                    pt_var = (
                        plaintext_i_sat[
                            nr_bitu_bufora
                        ]
                    )

                    builder.xor([
                        stary,
                        pt_var,
                        nowy
                    ])

                else:

                    if bufor_roboczy[i] == 0:
                        builder.equals(
                            stary,
                            nowy
                        )
                    else:
                        builder.equals_not(
                            stary,
                            nowy
                        )

                nowa_tablica_sat[y][x].append(
                    nowy
                )

    return (
        z_i,
        z_i_sat,
        tablica,
        nowa_tablica_sat
    )


def squeeze_16(
    tablica,
    tablica_sat,
    nr_bloku,
    nr_xoodoo
):

    tablica[2][3][30] ^= 1 #dodanie 0x40 w ostatnim bajcie stanu
    stan_przed_tag_sat = {}

    for y in range(3):
        stan_przed_tag_sat[y] = {}

        for x in range(4):
            stan_przed_tag_sat[y][x] = []

            for i in range(32):

                stary = tablica_sat[y][x][i]

                nowy = builder.var(
                    f"before_tag_{y}_{x}_{i}"
                )

                if (
                    y == 2
                    and x == 3
                    and i == 30
                ):
                    builder.equals_not(
                        stary,
                        nowy
                    )

                else:
                    builder.equals(
                        stary,
                        nowy
                    )

                stan_przed_tag_sat[y][x].append(
                    nowy
                )

    #wykonanie xoodoo przed uzyskaniem tagu
    tablica = xoodoo(tablica)

    nowa_tablica_sat = xoodoo_sat(
        stan_przed_tag_sat,
        nr_xoodoo
    )

    #budowanie tagu jako ciag binarny
    tag = []
    tag_sat = []

    dlugosc = 128

    for y in range(2):
        for x in range(4):

            if len(tag) == dlugosc:
                break

            for i in range(32):

                tag.append(
                    tablica[y][x][i]
                )

                tag_sat.append(
                    nowa_tablica_sat[y][x][i]
                )

                if len(tag) == dlugosc:
                    break

        if len(tag) == dlugosc:
            break

    tag = bits_to_hex(tag)

    return (
        tag,
        tag_sat,
        tablica,
        nowa_tablica_sat
    )


def xoodyak(
    Key,
    Plaintext,
    Nonce,
    AD
):

    if len(Key) != 32:
        raise ValueError(
            "Klucz musi mieć dokładnie 16 bajtów."
        )

    if len(Nonce) != 32:
        raise ValueError(
            "Nonce musi mieć dokładnie 16 bajtów."
        )

    if len(Plaintext) != 48:
        raise ValueError(
            "Plaintext musi mieć dokładnie 24 bajty."
        )

    tablica = {}

    #policzenie ilości bloków AD, aby móc policzyć później nr_xoodoo
    dlugosc_AD = (
        len(AD) + 87
    ) // 88

    if len(AD) == 0:
        dlugosc_AD = 1

    nr_xoodoo_tag = (
        dlugosc_AD + 1
    )

    #zdefiniowanie zmiennych SAT od tekstu jawnego i szyfrogramu
    plaintext_sat = []
    ct_sat = []

    for p in range(
        len(Plaintext) * 4
    ):
        plaintext_sat.append(
            builder.var(
                f"plaintext_{p}"
            )
        )

        ct_sat.append(
            builder.var(
                f"ciphertext_{p}"
            )
        )

    #uruchomienie szyfrowania
    (
        tablica,
        tablica_sat,
        key_sat,
        nonce_sat
    ) = absorb_key(
        Key,
        Nonce,
        tablica
    )

    (
        tablica,
        tablica_sat,
        ad_sat
    ) = absorb_ad(
        tablica,
        tablica_sat,
        AD,
        dlugosc_AD
    )

    otrzymany_szyfrogram = ""

    (
        z_i,
        z_i_sat,
        tablica,
        tablica_sat
    ) = up_and_down(
        tablica,
        tablica_sat,
        Plaintext,
        0,
        dlugosc_AD,
        plaintext_sat
    )

    for i in range(
        len(z_i_sat)
    ):
        builder.xor([
            plaintext_sat[i],
            z_i_sat[i],
            ct_sat[i]
        ])

    blok_szyfrogramu = hex(
        int(z_i, 16)
        ^ int(Plaintext, 16)
    )[2:].zfill(
        len(z_i)
    )

    otrzymany_szyfrogram += (
        blok_szyfrogramu
    )

    (
        otrzymany_tag,
        tag_sat,
        tablica,
        tablica_sat
    ) = squeeze_16(
        tablica,
        tablica_sat,
        0,
        nr_xoodoo_tag
    )

    dane = {
        "key": Key,
        "nonce": Nonce,
        "additional": AD,
        "plaintext": Plaintext,
        "ciphertext": otrzymany_szyfrogram,
        "tag": otrzymany_tag
    }

    return (
        key_sat,
        nonce_sat,
        ad_sat,
        plaintext_sat,
        ct_sat,
        tag_sat,
        tablica_sat,
        dane
    )


def manager():

    Nonce = "74a9c38c241ac134b87dba198879d81a"

    AD = "ae4e344a85b5d767327e9fbaa16b58bffa2c3a8b0f4d30d14ed6aaf35e5ecb4f"

    key_sat_all = []
    nonce_sat_all = []
    ad_sat_all = []
    plaintext_sat_all = []
    ct_sat_all = []
    tag_sat_all = []
    tablica_sat_all = []
    dane_all = []

    #wylosowanie tekstów jawnych i kluczy
    for nr_zestawu in range(1, 11):

        reset_builder()

        Key = ''.join(
            random.choice(
                '0123456789abcdef'
            )
            for _ in range(32)
        )

        Plaintext = ''.join(
            random.choice(
                '0123456789abcdef'
            )
            for _ in range(48)
        )

        (
            key_sat,
            nonce_sat,
            ad_sat,
            plaintext_sat,
            ct_sat,
            tag_sat,
            tablica_sat,
            dane
        ) = xoodyak(
            Key,
            Plaintext,
            Nonce,
            AD
        )

        key_sat_all.append(
            key_sat
        )

        nonce_sat_all.append(
            nonce_sat
        )

        ad_sat_all.append(
            ad_sat
        )

        plaintext_sat_all.append(
            plaintext_sat
        )

        ct_sat_all.append(
            ct_sat
        )

        tag_sat_all.append(
            tag_sat
        )

        tablica_sat_all.append(
            tablica_sat
        )

        dane_all.append(
            dane
        )

        nazwa = (
            f"xoodyak_ptlen24B_set_{nr_zestawu}"
        )

        builder.cnf.to_file(
            f"{nazwa}.cnf"
        )

        #do pomocniczego Json:
        opis = {
            "Algorithm": "Xoodyak",
            "Mode": "keyed",
            "plaintext_length_in_bytes": 24,
            "values": dane,
            "variables": {
                "key": key_sat,
                "nonce": nonce_sat,
                "ad": ad_sat,
                "plaintext": plaintext_sat,
                "ciphertext": ct_sat,
                "tag": tag_sat
            },
            "encoding": {
                "values": "hex",
                "bit_order_inside_bytes": "LSB-first"
            }
        }

        with open(
            f"{nazwa}.json",
            "w",
            encoding="utf-8"
        ) as plik:

            json.dump(
                opis,
                plik,
                indent=4
            )

        print(
            f"Zapisano zestaw {nr_zestawu}/10"
        )

    print(
        "Zapis plików zakończony"
    )

    return (
        key_sat_all,
        nonce_sat_all,
        ad_sat_all,
        plaintext_sat_all,
        ct_sat_all,
        tag_sat_all,
        tablica_sat_all,
        dane_all
    )


manager()