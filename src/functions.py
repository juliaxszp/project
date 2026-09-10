from .basics import *

builder = BasicFunctions()

def xor_bits(builder, x, y, b):   #b = y xor x, gdzie y to nowy bit
    if b == 0:  # b = 0, czyli y = x
        builder.equals(x, y)
    else:  # b = 1, czyli y = not x
        builder.equals_not(x, y)

def xor_const(builder, var_1, var_2, var_3):
    for i in range(len(var_1)):                              #zmiana z 4 bitów na dlugosc jednej zmiennej na potrzeby innych szyfrow
        xor_bits(builder, var_1[i], var_2[i], var_3[i])

def rotl(var, idx):
    y = var[idx:] + var[:idx]
    return y
#funkcje do SAT:
def vector_xor_sat(builder, vectors, output):
    for i in range(len(output)):
        builder.xor([vector[i] for vector in vectors] + [output[i]])

def vector_and_sat(builder, vectors, output):
    for i in range(len(output)):
        builder.equal_and(output[i], [vector[i] for vector in vectors])

#czesci do xoodoo
def theta_sat(tablica):
    p = {}
    for i in range(4):
        p[i] = [builder.var(f"p{i}_{j}") for j in range(32)]
        vector_xor_sat(builder, [tablica[0][i], tablica[1][i], tablica[2][i]], p[i])

    #dodajemy te p do kolumny x-1

    e = {}
    for k in range(4):
        e[k] = [builder.var(f"e{k}_{j}") for j in range(32)]
        vector_xor_sat(builder, [rotl(p[(k-1) % 4], 5), rotl(p[(k-1) % 4], 14)], e[k])

    #xorujemy wartości e do kolumn tablicy
    wynik = {}
    for y in range(3):
        wynik[y] = {}
        for x in range(4):
            wynik[y][x] = [builder.var(f"theta{y}_{x}_{j}") for j in range(32)]
            vector_xor_sat(builder, [tablica[y][x], e[x]], wynik[y][x])

    return wynik

def rho_west_sat(tablica):
    
    #pierwszy wiersz zostawiamy
    lista = [tablica[1][i] for i in range(4)]
    lista = rotl(lista, 3)
    for i in range(4):
        tablica[1][i] = lista[i]

    for i in range(4):
        tablica[2][i] = rotl(tablica[2][i], 11)

    return tablica

def iota_sat(tablica, nr_rundy):
    round_constants = [
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

    constant = [int(bit) for bit in f"{round_constants[nr_rundy]:032b}"]
    wynik = [builder.var(f"iota_{nr_rundy}_{j}") for j in range(32)]
    xor_const(builder, tablica[0][0], wynik, constant)
    tablica[0][0] = wynik

    return tablica

def chi_sat(builder, tablica):
    wynik = {}

    for y in range(3):
        wynik[y] = {}
        for x in range(4):
            temp = [builder.var(f"chi_temp_{x}_{y}_{m}") for m in range(32)]
            wynik[y][x] = [builder.var(f"chi_{x}{y}{j}") for j in range(32)]

            vector_and_sat(
                builder,
                [[-var for var in tablica[(y + 1) % 3][x]],
                 tablica[(y + 2) % 3][x]],
                temp
            )

            vector_xor_sat(
                builder,
                [tablica[y][x], temp],
                wynik[y][x]
            )

    return wynik
def rho_east_sat(tablica):
    #płaszczyzna zerowa bez zmian
    #pł 1:
    for i in range(4):
        tablica[1][i] = rotl(tablica[1][i], 1)
        #pł 2:
    lista = [tablica[2][i] for i in range(4)]
    lista = rotl(lista, 2)
    for j in range(4):
        tablica[1][j] = lista[j]
    for k in range(4):
        tablica[2][k] = rotl(tablica[2][k], 8)

    return tablica

#funkcje do prostej implementacji xoodoo
def vector_xor(builder, vectors):
    output = []
    for i in range(len(vectors[0])):
        output.append(builder.xorn([vector[i] for vector in vectors]))
    return output

def vector_and(builder, vectors):
    output = []
    for i in range(len(vectors[0])):
        output.append(builder.equal_andn([vector[i] for vector in vectors]))
    return output

#czesci do xoodoo
def theta(tablica):
    p = {}
    for i in range(4):
        p[i] = vector_xor(builder, [tablica[0][i], tablica[1][i], tablica[2][i]])

    #dodajemy te p do kolumny x-1

    e = {}
    for k in range(4):
        e[k] = vector_xor(builder, [rotl(p[(k-1) % 4], 5), rotl(p[(k-1) % 4], 14)])

    #xorujemy wartości e do kolumn tablicy
    wynik = {}
    for y in range(3):
        wynik[y] = {}
        for x in range(4):
            wynik[y][x] = vector_xor(builder, [tablica[y][x], e[x]])

    return wynik

def rho_west(tablica):
    
    #pierwszy wiersz zostawiamy
    lista = [tablica[1][i] for i in range(4)]
    lista = rotl(lista, 3)
    for i in range(4):
        tablica[1][i] = lista[i]

    for i in range(4):
        tablica[2][i] = rotl(tablica[2][i], 11)

    return tablica
def iota(tablica, nr_rundy):
    round_constants = [
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

    constant = [(round_constants[nr_rundy] >> i) & 1 for i in range(32)]
    tablica[0][0] = vector_xor(builder, [tablica[0][0], constant])

    return tablica
def chi(builder, tablica):
    wynik = {}

    for y in range(3):
        wynik[y] = {}
        for x in range(4):
            temp = vector_and(
                builder,
                [[1 - var for var in tablica[(y + 1) % 3][x]],
                 tablica[(y + 2) % 3][x]]
            )

            wynik[y][x] = vector_xor(
                builder,
                [tablica[y][x], temp]
            )

    return wynik

def rho_east(tablica):
    #płaszczyzna zerowa bez zmian
    #pł 1:
    for i in range(4):
        tablica[1][i] = rotl(tablica[1][i], 1)
        #pł 2:
    lista = [tablica[2][i] for i in range(4)]
    lista = rotl(lista, 2)
    for j in range(4):
        tablica[1][j] = lista[j]
    for k in range(4):
        tablica[2][k] = rotl(tablica[2][k], 8)

    return tablica
