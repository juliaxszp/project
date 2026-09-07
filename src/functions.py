from .basics import *


def xor_bits(Builder, x, y, b):   #b = y xor x, gdzie y to nowy bit
    if b == 0:  # b = 0, czyli y = x
        Builder.equals(x, y)
    else:  # b = 1, czyli y = not x
        Builder.equals_not(x, y)

def xor_const(Builder, var_1, var_2, var_3):
    for i in range(len(var_1)):                              #zmiana z 4 bitów na dlugosc jednej zmiennej na potrzeby innych szyfrow
        xor_bits(Builder, var_1[i], var_2[i], var_3[i])
def rotl(var, idx):
    y = var[idx:] + var[:idx]
    return y

def vector_xor(Builder, vectors, output):
    for i in range(len(output)):
        Builder.xor([vector[i] for vector in vectors] + [output[i]])
#czesci do xoodoo
def theta(tablica):
    p = {}
    for i in range(4):
        p[i] = [Builder.var(f"p{i}_{j}") for j in range(32)]
        vector_xor(Builder, [tablica[0, i], tablica[1, i], tablica[2, i]], p[i])

    #dodajemy te p do kolumny x-1

    e = {}
    for k in range(4):
        e[k] = [Builder.var(f"e{k}_{j}") for j in range(32)]
        vector_xor(Builder, [rotl(p[(k-1) % 4], 5), rotl(p[(k-1) % 4], 14)], e[k])
    #xorujemy wartości e do kolumn tablicy
    wynik = {}
    for y in range(3):
        wynik[y] = {}
        for x in range(4):
            wynik[y][x] = [Builder.var(f"theta{y}_{x}_{j}") for j in range(32)]
            vector_xor(Builder, [tablica[y, x], e[x]], wynik[y][x])

    return wynik
def rhowest(tablica):
    
    #pierwszy wiersz zostawiamy
    lista = tablica[1]
    tablica[1] = rotl(lista, 1)
    for i in range(4):
        tablica[2, i] = rotl(tablica[i][2], 11)
    return tablica
def iota(tablica):
    