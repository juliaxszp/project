#Adam Aftyka łamanie xoodyaka
import argparse
import json
import time
import multiprocessing
from itertools import combinations
from pysat.formula import CNF


def wybierz_solver(solver_name):
    if solver_name == "Kissat404":
        from pysat.solvers import Kissat404
        return Kissat404
    elif solver_name == "CryptoMinisat":
        from pysat.solvers import CryptoMinisat
        return CryptoMinisat
    else:
        raise ValueError(f"Nieznany solver: {solver_name}")


def hex_na_bity(hex):
    wynik = []
    for i in range(0, len(hex), 2):
        bajt = int(hex[i:i + 2], 16)
        for j in range(8):
            wynik.append((bajt >> j) & 1)
    return wynik


def ustaw_wartosc(zmienne, bity):
    if len(zmienne) != len(bity):
        raise ValueError(
            f"Niezgodne długości list: {len(zmienne)} i bitów: {len(bity)}"
        )

    wynik = []

    for zmienna, bit in zip(zmienne, bity):
        if bit == 1:
            wynik.append(zmienna)
        else:
            wynik.append(-zmienna)

    return wynik


def odczytaj_bity_z_sat(zmienne, model):
    model_set = set(model)
    wynik = []

    for zmienna in zmienne:
        if zmienna in model_set:
            wynik.append(1)
        else:
            wynik.append(0)

    return wynik


def bity_na_hex_lsb(bity):
    wynik = ""

    for i in range(0, len(bity), 8):
        bajt = 0

        for j in range(8):
            bajt |= bity[i + j] << j

        wynik += f"{bajt:02x}"

    return wynik


def znane_bity_klucza(zmienne, bity, bajt1, bajt2):
    wynik = []

    poczatek1 = bajt1 * 8
    koniec1 = poczatek1 + 8

    poczatek2 = bajt2 * 8
    koniec2 = poczatek2 + 8

    for i in range(len(zmienne)):
        if (
            poczatek1 <= i < koniec1
            or poczatek2 <= i < koniec2
        ):
            continue

        if bity[i] == 1:
            wynik.append(zmienne[i])
        else:
            wynik.append(-zmienne[i])

    return wynik


def uruchom_solver(
    solver_name,
    nazwa_cnf,
    ograniczenia,
    key_variables,
    poprawna_wartosc_klucza,
    kolejka
):
    try:
        wybrany_solver = wybierz_solver(solver_name)

        cnf_test = CNF(from_file=nazwa_cnf)

        for literal in ograniczenia:
            cnf_test.append([literal])

        with wybrany_solver(
            bootstrap_with=cnf_test.clauses
        ) as solver:

            poczatek_czasu = time.perf_counter()

            wynik = solver.solve()

            koniec_czasu = time.perf_counter()

            czas = koniec_czasu - poczatek_czasu

            if wynik:
                model = solver.get_model()

                odzyskane_bity_klucza = odczytaj_bity_z_sat(
                    key_variables,
                    model
                )

                odzyskany_klucz = bity_na_hex_lsb(
                    odzyskane_bity_klucza
                )

                poprawny_klucz = (
                    odzyskany_klucz
                    == poprawna_wartosc_klucza
                )

                kolejka.put({
                    "wynik": "SAT",
                    "czas": czas,
                    "poprawny_klucz": poprawny_klucz
                })

            else:
                kolejka.put({
                    "wynik": "UNSAT",
                    "czas": czas,
                    "poprawny_klucz": False
                })

    except Exception as blad:
        kolejka.put({
            "blad": str(blad)
        })


def kryptoanaliza(solver_name, nr_zestawu, part):
    nazwa = f"xoodyak_ptlen24B_set_{nr_zestawu}"

    with open(f"{nazwa}.json", "r", encoding="UTF-8") as plik:
        dane = json.load(plik)

    pary = list(combinations(range(16), 2))

    if part == 1:
        wybrane_pary = pary[:60]
    elif part == 2:
        wybrane_pary = pary[60:]
    else:
        raise ValueError("part musi mieć wartość 1 albo 2")

    bity_klucza = hex_na_bity(
        dane["values"]["key"]
    )

    bity_nonce = hex_na_bity(
        dane["values"]["nonce"]
    )

    bity_ad = hex_na_bity(
        dane["values"]["additional"]
    )

    bity_plaintext = hex_na_bity(
        dane["values"]["plaintext"]
    )

    bity_ciphertext = hex_na_bity(
        dane["values"]["ciphertext"]
    )

    bity_tag = hex_na_bity(
        dane["values"]["tag"]
    )

    stale_ograniczenia = []

    stale_ograniczenia += ustaw_wartosc(
        dane["variables"]["nonce"],
        bity_nonce
    )

    stale_ograniczenia += ustaw_wartosc(
        dane["variables"]["ad"],
        bity_ad
    )

    stale_ograniczenia += ustaw_wartosc(
        dane["variables"]["plaintext"],
        bity_plaintext
    )

    stale_ograniczenia += ustaw_wartosc(
        dane["variables"]["ciphertext"],
        bity_ciphertext
    )

    stale_ograniczenia += ustaw_wartosc(
        dane["variables"]["tag"],
        bity_tag
    )

    wyniki = {}

    for para in wybrane_pary:
        bajt1, bajt2 = para

        ograniczenia = list(stale_ograniczenia)

        ograniczenia += znane_bity_klucza(
            dane["variables"]["key"],
            bity_klucza,
            bajt1,
            bajt2
        )

        kolejka = multiprocessing.Queue()

        proces = multiprocessing.Process(
            target=uruchom_solver,
            args=(
                solver_name,
                f"{nazwa}.cnf",
                ograniczenia,
                dane["variables"]["key"],
                dane["values"]["key"],
                kolejka
            )
        )

        poczatek_limitu = time.perf_counter()

        proces.start()
        proces.join(720)

        if proces.is_alive():
            proces.terminate()
            proces.join()

            czas = (time.perf_counter() - poczatek_limitu)

            rezultat = {
                "para": [
                    bajt1,
                    bajt2
                ],
                "czas": czas,
                "wynik": "TIMEOUT"
            }

        else:
            if kolejka.empty():
                raise RuntimeError(f"Proces solvera zakończył się bez wyniku  dla pary {para}")

            wynik_solvera = kolejka.get()

            if "blad" in wynik_solvera:
                raise RuntimeError(f"Błąd solvera dla pary {para}:  {wynik_solvera['blad']}")

            rezultat = {
                "para": [
                    bajt1,
                    bajt2
                ],
                "czas": wynik_solvera["czas"],
                "wynik": wynik_solvera["wynik"]
            }

        klucz_wyniku = f"{bajt1}_{bajt2}"

        wyniki[klucz_wyniku] = rezultat

        print(f"Para {bajt1}, {bajt2}:  {rezultat['wynik']},  czas: {rezultat['czas']:.6f} s")

    return wyniki

def manager():
    parser = argparse.ArgumentParser()

    parser.add_argument("--solver", choices=["Kissat404", "CryptoMinisat"], required=True)

    parser.add_argument("--set", type=int, choices=range(1, 11), required=True)

    parser.add_argument("--part", type=int, choices=[1, 2], required=True)

    args = parser.parse_args()

    solver_name = args.solver
    nr_zestawu = args.set
    part = args.part

    wyniki = kryptoanaliza(solver_name, nr_zestawu, part)

    dane_wynikowe = {
        "solver": solver_name,
        "set": nr_zestawu,
        "part": part,
        "timeout_seconds": 720,
        "wyniki": wyniki
    }

    nazwa_wyniku = f"wyniki_{solver_name}_zestaw_{nr_zestawu}_{part}_z_2.json"

    with open(nazwa_wyniku, "w", encoding="UTF-8") as plik:
        json.dump(dane_wynikowe, plik, indent=4)

    print("Solver:", solver_name)

    print("Zestaw:", nr_zestawu)

    print("Część:", part)

    print("Liczba wykonanych par:", len(wyniki))
manager()