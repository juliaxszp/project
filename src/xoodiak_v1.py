#Adam Aftyka implementacja xoodyak
#stale ustalony klucz: a0bf9f4acef48231
#stale ustalony Nonce: 1234567890abcdee
#stale ustalone AD: aaabbbcccddd
from .functions import *
klucz = "a0bf9f4acef48231a0bf9f4acef48231"
nonce = "1234567890abcdee1234567890abcdee"
ad = "aabbccdd"

tablica = {}
def xoodoo(tablica):
    for itterator in range(12):
        tablica = theta(tablica)
        tablica = rho_west(tablica)
        tablica = iota(tablica, itterator)
        tablica = chi(builder, tablica)
        tablica = rho_east(tablica)
    return tablica
def xoodoo_sat(tablica):
    for itterator in range(12):
        tablica = theta_sat(tablica)
        tablica = rho_west_sat(tablica)
        tablica = iota_sat(tablica, itterator)
        tablica = chi_sat(builder, tablica)
        tablica = rho_east_sat(tablica)
    return tablica

def absorb_key(klucz, nonce, tablica):
    bufor = klucz
    bufor += nonce
    bufor += "10"
    bufor += "0" * 28
    bufor += "02"
    #zamiana ciągu na listę
    tablica_sat = {}
    for y in range(3):
        tablica[y] = {}
        tablica_sat[y] = {}
        for x in range(4):
            tablica_sat[y][x] = [builder.var(f"initial_state_{y}_{x}_{i}") for i in range(32)]
            #ustawianie konkretnych wartości słów
            idx = ((y * 4) + x) * 8
            slowo = bufor[idx:idx + 8]
            wartosc = int(slowo, 16)
            tablica[y][x] = [(wartosc >> i) & 1 for i in range(32)]
    #teraz iteruję po tablicy i ustawiam konkretne zmienne SAT dla wartości jawnych.
    for yprim in range(1, 3):
        for xprim in range(4):

            for iprim in range(32):
                v = tablica_sat[yprim][xprim][iprim]
                if tablica[yprim][xprim][iprim] == 1:
                    builder.cnf.append([v])
                else:
                    builder.cnf.append([-v])
    return tablica, tablica_sat