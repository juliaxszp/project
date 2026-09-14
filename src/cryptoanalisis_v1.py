#Adam Aftyka łamanie xoodyaka
import argparse
import json
import time
import resource
from pysat.formula import CNF
def wybierz_solver(solver_name):
    if solver_name == "Kissat404":
        from pysat.solvers import Kissat404
        return Kissat404
    elif solver_name == "CryptoMinisat":
        from pysat.solvers import CryptoMinisat
        return CryptoMinisat
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
    

def sprawdz_poprawnosc():
    bity_klucza = hex_na_bity(dane["values"]["key"])
    bity_nonce = hex_na_bity(dane["values"]["nonce"])
    bity_ad = hex_na_bity(dane["values"]["additional"])
    bity_plaintext = hex_na_bity(dane["values"]["plaintext"])
    assumptions = []
    assumptions += ustaw_wartosc(dane["variables"]["key"], bity_klucza)
    assumptions += ustaw_wartosc(dane["variables"]["nonce"], bity_nonce)
    assumptions += ustaw_wartosc(dane["variables"]["ad"], bity_ad)
    assumptions += ustaw_wartosc(dane["variables"]["plaintext"], bity_plaintext)
    with Glucose3(bootstrap_with=cnf.clauses) as solver:
        wynik = solver.solve(assumptions=assumptions)
        if wynik:
            model = solver.get_model()
            print("SAT")
        else:
            print("UnSAT")
            return
        odczytany_klucz = bity_na_hex_lsb(odczytaj_bity_z_sat(dane["variables"]["key"], model))
        odczytany_nonce = bity_na_hex_lsb(odczytaj_bity_z_sat(dane["variables"]["nonce"], model))
        odczytany_ad = bity_na_hex_lsb(odczytaj_bity_z_sat(dane["variables"]["ad"], model))
        odczytany_plaintext = bity_na_hex_lsb(odczytaj_bity_z_sat(dane["variables"]["plaintext"], model))
    print("klucz z modelu:", odczytany_klucz)
    print("Klucz z json:", dane["values"]["key"])
    print("nonce z modelu:", odczytany_nonce)
    print("Nonce z json:", dane["values"]["nonce"])
    print("AD z modelu:", odczytany_ad)
    print("AD z json:", dane["values"]["additional"])
    print("plaintext z modelu:", odczytany_plaintext)
    print("plaintext z json:", dane["values"]["plaintext"])
    bity_szyfrogramu = odczytaj_bity_z_sat(dane["variables"]["ciphertext"], model)
    bity_tagu = odczytaj_bity_z_sat(dane["variables"]["tag"], model)
    ciphertext = bity_na_hex_lsb(bity_szyfrogramu)
    tag = bity_na_hex_lsb(bity_tagu)
    print("Odnaleziony szyfrogram:", ciphertext)
    print("Odzyskany tag:", tag)
    if ciphertext == dane["values"]["ciphertext"]:
        print("Szyfrogram: sukces!")
    else:
        print("Szyfrogram: porażka")
    if tag == dane["values"]["tag"]:
        print("Tag: sukces!")
    else:
        print("tag: porażka")
    return
    
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
def kryptoanaliza(wybrany_solver, solver_name, liczba_nieznanych_bitow, instancja):
    cnf_test = CNF(from_file=f"{nazwa}.cnf")
    if instancja == 1:
        poczatek = 0
    elif instancja == 2:
        poczatek = 32
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

    with wybrany_solver(bootstrap_with=cnf_test.clauses) as solver:
        poczatek_czasu = time.perf_counter()
        wynik = solver.solve()
        koniec_czasu = time.perf_counter()
        statystyki = solver.accum_stats()
        konflikty = statystyki.get("conflicts")
        decyzje = statystyki.get("decisions")
        propagacje = statystyki.get("propagations")
        
        if wynik:
            model = solver.get_model()
            result = "SAT"
            odzyskane_bity_klucza = odczytaj_bity_z_sat(dane["variables"]["key"], model)
            odzyskany_klucz = bity_na_hex_lsb(odzyskane_bity_klucza)
            poprawny_klucz = odzyskany_klucz == dane["values"]["key"]
        else:
            model = None
            result = "UNSAT"
    pamiec = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    czas = koniec_czasu - poczatek_czasu
    zmienne = cnf_test.nv
    klauzule = len(cnf_test.clauses)
    return solver_name, liczba_nieznanych_bitow, result, poprawny_klucz, czas, konflikty, decyzje, propagacje, pamiec, zmienne, klauzule
def manager():
#    sterownik = int(input("1: sprawdzenie poprawności równań CNF. 2: kryptoanaliza"))
#    if sterownik == 1:
#        sprawdz_poprawnosc()
#    elif sterownik == 2:
#        kryptoanaliza()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", choices=["Kissat404", "CryptoMinisat"], required=True)
    parser.add_argument("--unknown-key-bits", type=int, required=True)
    parser.add_argument("--instance", type=int, required=True)
    args = parser.parse_args()
    solver_name = args.solver
    liczba_nieznanych_bitow = args.unknown_key_bits
    instancja = args.instance
    wybrany_solver = wybierz_solver(solver_name)
    solver_name, liczba_nieznanych_bitow, result, poprawny_klucz, czas, konflikty, decyzje, propagacje, pamiec, zmienne, klauzule = kryptoanaliza(wybrany_solver, solver_name, liczba_nieznanych_bitow, instancja)
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