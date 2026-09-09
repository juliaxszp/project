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
            tablica[y][x]
            #ustawianie na wkladanie w konwencji little endian
            for k in range(4):
                bajt = int(slowo[2 * k: 2 * k + 2], 16)
                tablica[y][x] += [(bajt >> i) & 1 for i in range(8)]
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

def absorb_ad(tablica, tablica_sat, AD):
    #pocięcie AD na kawalki o odpowiedniej długości
    kawalki = []
    for a in range((len(AD) // 88) + 1):
        inc = 88
        if a == len(AD) // 88: inc = (len(AD) - 88 * a)
        if inc > 0:
            kawalki.append(AD[88 * a:88 * a + inc])
    #obsługa przypadku dodania pustego AD:
    if len(AD) == 0:
        kawalki.append("")
    #teraz wkładamy tablicę z kawałków AD gotowych do dodania do stanu wewnętrznego
    bufory = []
    for b in range(len(kawalki)):
        bufor = kawalki[b]
        bufor += "01"
        zer_do_dodania = ((48 * 2)-len(bufor) -2)
        bufor += "0" * zer_do_dodania
        if b == 0:
            bufor += "03"
        else:
            bufor += "00"
        bufory.append(bufor)
    #teraz robimy faktyczne łączenie kawałków AD ze stanem wewnętrznym
    for c in range(len(bufory)):
        nowa_tablica_sat = {}
        tablica = xoodoo(tablica)
        tablica_sat = xoodoo_sat(tablica_sat)
        for y in range(3):
            nowa_tablica_sat[y] = {}
            for x in range(4):
                nowa_tablica_sat[y][x] = []
                idx = ((y * 4) + x) * 8
#                slowo_bufora_int = int(bufory[c][idx:idx + 8], 16)
                slowo = bufory[c][idx: idx + 8]
                slowo_bufora_bin = []
                for k in range(4):
                    bajt = int(slowo[2 * k:2 * k + 2], 16)
                    slowo_bufora_bin += [(bajt >> i) & 1 for i in range(8)]
#                slowo_bufora_bin = [(tablica[y][x] >> j) & 1 for j in range(32)]
#                slowo_tablicy = 0
                for i in range(32):
                    tablica[y][x][i] ^= slowo_bufora_bin[i]
                #dodanie zależności do SAT zależnej od bitów AD
                    stary = tablica_sat[y][x][i]
                    nowy = builder.var(f"state_ad_{c}_{y}_{x}_{i}")
                    if slowo_bufora_bin[i] == 0:
                        builder.equals(stary, nowy)
                    else:
                        builder.equals_not(stary, nowy)
                    nowa_tablica_sat[y][x][i].append(nowy)
        tablica_sat = nowa_tablica_sat
    return tablica, tablica_sat

def up_and_down(tablica, tablica_sat, plaintext_i, nr_bloku):
    #wykonanie xoodoo przed uzyskaniem pierwszego fragmentu z_i
    tablica = xoodoo(tablica)
    tablica_sat = xoodoo_sat(tablica_sat)
    #budowanie z_i jako ciag binarny
    z_i = []
    dlugosc = (len(plaintext_i) // 2) * 8
    for y in range(2):
        for x in range(4):
            if len(z_i) == dlugosc:
                break
            for i in range(32):
                z_i.append(tablica[y][x][i])
    bufor = plaintext_i
    bufor += "01"
    ilosc_zer = 96 - len(bufor)
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
                bajt = int(bufor[idx + 2 * j: idx + 2 * j + 2], 16)
                bufor_roboczy += [(bajt >> k) & 1 for k in range(8)]
            for i in range(32):
                tablica[y][x][i] ^= bufor_roboczy[i]
                stary = tablica_sat[y][x][i]
                nowy = builder.var(f"after_pt_state_{nr_bloku}_{y}_{x}_{i}")
                if bufor_roboczy[i] == 0:
                    builder.equals(stary, nowy)
                else:
                    builder.equals_not(stary, nowy)
                nowa_tablica_sat[y][x].append(nowy)
    return z_i, tablica, nowa_tablica_sat

