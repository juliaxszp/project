#Adam Aftyka łamanie xoodyaka
import argparse
import json
import time
import resource
import subprocess
import re
import os
from pysat.formula import CNF

nazwa = f"xoodyak_ptlen64B"

with open(f"{nazwa}.json", "r", encoding="UTF-8") as plik:
    dane = json.load(plik)

def hex_na_bity(hex):
    wynik = []
    for i in range(0, len(hex), 2):
        bajt = int(hex[i:i+2], 16)
        for j in range(8):
            wynik.append((bajt >> j) & 1)
    return wynik

def ustaw_wartosc(zmienne, bity):
    if len(zmienne) != len(bity):
        raise ValueError(f"Niezgodne długości list: {len(zmienne)} i bitów: {len(bity)}")
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


def znane_bity_klucza(zmienne, bity, poczatek, liczba_nieznanych_bitow):
    wynik = []
    koniec = poczatek + liczba_nieznanych_bitow
    for i in range(len(zmienne)):
        if poczatek <= i < koniec:
            continue
        if bity[i] == 1:
            wynik.append(zmienne[i])
        else:
            wynik.append(-zmienne[i])
    return wynik

def uruchom_solver(solver_name, plik_cnf):
    if solver_name == "Kissat404":
        argumenty = [
            "kissat",
            plik_cnf
        ]
    elif solver_name == "CryptoMinisat":
        argumenty = [
            "cryptominisat5",
            "--verb", "1",
            "--verbstat", "2",
            "--printsol", "1",
            plik_cnf
        ]
    else:
        raise ValueError("Nieznany solver")

    return subprocess.run(
        argumenty,
        capture_output=True,
        text=True
    )

def odczytaj_wynik_solvera(output, returncode):
    if returncode == 10 or "s SATISFIABLE" in output:
        return "SAT"
    elif returncode == 20 or "s UNSATISFIABLE" in output:
        return "UNSAT"
    else:
        raise RuntimeError(
            f"Solver nie zwrócił SAT ani UNSAT. Kod wyjścia: {returncode}\n{output}"
        )

def odczytaj_model(output):
    model = []
    for linia in output.splitlines():
        if linia.startswith("v "):
            for wartosc in linia.split()[1:]:
                literal = int(wartosc)
                if literal != 0:
                    model.append(literal)
    return model

def parsuj_statystyki_kissat(output):
    konflikty = None
    decyzje = None
    propagacje = None

    for linia in output.splitlines():
        linia_mala = linia.lower()

        if "conflicts" in linia_mala:
            wynik = re.search(r"\bconflicts\b[^0-9]*([0-9]+)", linia_mala)
            if wynik:
                konflikty = int(wynik.group(1))

        if "decisions" in linia_mala:
            wynik = re.search(r"\bdecisions\b[^0-9]*([0-9]+)", linia_mala)
            if wynik:
                decyzje = int(wynik.group(1))

        if "propagations" in linia_mala:
            wynik = re.search(r"\bpropagations\b[^0-9]*([0-9]+)", linia_mala)
            if wynik:
                propagacje = int(wynik.group(1))

    return konflikty, decyzje, propagacje

def parsuj_statystyki_cryptominisat(output):
    konflikty = None
    decyzje = None
    propagacje = None

    for linia in output.splitlines():
        linia_mala = linia.lower()

        if "conflicts" in linia_mala:
            wynik = re.search(r"\bconflicts\b\s*:\s*([0-9]+)", linia_mala)
            if wynik:
                konflikty = int(wynik.group(1))

        if "decisions" in linia_mala:
            wynik = re.search(r"\bdecisions\b\s*:\s*([0-9]+)", linia_mala)
            if wynik:
                decyzje = int(wynik.group(1))

        if "propagations" in linia_mala:
            wynik = re.search(r"\bpropagations\b\s*:\s*([0-9]+)", linia_mala)
            if wynik:
                propagacje = int(wynik.group(1))

    return konflikty, decyzje, propagacje

def parsuj_statystyki(solver_name, output):
    if solver_name == "Kissat404":
        return parsuj_statystyki_kissat(output)
    elif solver_name == "CryptoMinisat":
        return parsuj_statystyki_cryptominisat(output)
    else:
        raise ValueError("Nieznany solver")

def kryptoanaliza(solver_name, liczba_nieznanych_bitow, instancja):
    cnf_test = CNF(from_file=f"{nazwa}.cnf")
    if instancja == 1:
        poczatek = 8
    elif instancja == 2:
        poczatek = 88
    elif instancja == 3:
        poczatek = 64
    elif instancja == 4:
        poczatek = 96
    else:
        raise ValueError("Niepoprawne ustawienie")
    poprawny_klucz = None
    bity_klucza = hex_na_bity(dane["values"]["key"])
    ograniczenia = []
    bity_nonce = hex_na_bity(dane["values"]["nonce"])
    bity_ad = hex_na_bity(dane["values"]["additional"])
    bity_plaintext = hex_na_bity(dane["values"]["plaintext"])
    bity_ciphertext = hex_na_bity(dane["values"]["ciphertext"])
    bity_tag = hex_na_bity(dane["values"]["tag"])
    ograniczenia += ustaw_wartosc(dane["variables"]["nonce"], bity_nonce)
    ograniczenia += ustaw_wartosc(dane["variables"]["ad"], bity_ad)
    ograniczenia += ustaw_wartosc(dane["variables"]["plaintext"], bity_plaintext)
    ograniczenia += ustaw_wartosc(dane["variables"]["ciphertext"], bity_ciphertext)
    ograniczenia += ustaw_wartosc(dane["variables"]["tag"], bity_tag)
    ograniczenia += znane_bity_klucza(dane["variables"]["key"], bity_klucza, poczatek, liczba_nieznanych_bitow)
    for literal in ograniczenia:
        cnf_test.append([literal])

    plik_cnf = f"temp_{solver_name}_{liczba_nieznanych_bitow}_{instancja}.cnf"
    cnf_test.to_file(plik_cnf)

    try:
        poczatek_czasu = time.perf_counter()
        proces = uruchom_solver(solver_name, plik_cnf)
        koniec_czasu = time.perf_counter()
    finally:
        if os.path.exists(plik_cnf):
            os.remove(plik_cnf)

    output = proces.stdout + "\n" + proces.stderr
    result = odczytaj_wynik_solvera(output, proces.returncode)
    konflikty, decyzje, propagacje = parsuj_statystyki(solver_name, output)

    if result == "SAT":
        model = odczytaj_model(output)
        if not model:
            raise RuntimeError("Solver zwrócił SAT, ale nie udało się odczytać modelu z linii v.")
        odzyskane_bity_klucza = odczytaj_bity_z_sat(dane["variables"]["key"], model)
        odzyskany_klucz = bity_na_hex_lsb(odzyskane_bity_klucza)
        poprawny_klucz = odzyskany_klucz == dane["values"]["key"]
    else:
        model = None
        poprawny_klucz = None

    pamiec = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    czas = koniec_czasu - poczatek_czasu
    zmienne = cnf_test.nv
    klauzule = len(cnf_test.clauses)
    return solver_name, liczba_nieznanych_bitow, result, poprawny_klucz, czas, konflikty, decyzje, propagacje, pamiec, zmienne, klauzule

def manager():

    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", choices=["Kissat404", "CryptoMinisat"], required=True)
    parser.add_argument("--unknown-key-bits", type=int, required=True)
    parser.add_argument("--instance", type=int, required=True)
    args = parser.parse_args()
    solver_name = args.solver
    liczba_nieznanych_bitow = args.unknown_key_bits
    instancja = args.instance
    solver_name, liczba_nieznanych_bitow, result, poprawny_klucz, czas, konflikty, decyzje, propagacje, pamiec, zmienne, klauzule = kryptoanaliza(solver_name, liczba_nieznanych_bitow, instancja)
    wyniki = {
        "instancja": instancja,
        "solver_name": solver_name,
        "liczba_nieznanych_bitow": liczba_nieznanych_bitow,
        "rezultat": result,
        "poprawny_klucz": poprawny_klucz,
        "czas": czas,
        "konflikty": konflikty,
        "decyzje": decyzje,
        "propagacje": propagacje,
        "pamiec": pamiec,
        "zmienne": zmienne,
        "klauzule": klauzule
    }
    nazwa_wyniku = f"wyniki_{solver_name}_{liczba_nieznanych_bitow}_{instancja}.json"
    with open(nazwa_wyniku, "w", encoding="UTF-8") as plik:
        json.dump(wyniki, plik, indent=4)
    print("Solver:", solver_name)
    print("Liczba nieznanych bitów:", liczba_nieznanych_bitow)

manager()
