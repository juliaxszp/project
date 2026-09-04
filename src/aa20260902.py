from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404


def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])


def sand(cnf: CNF, var_a: int, zmienne, liczba_zmiennych) -> None:
    for i in range(liczba_zmiennych):
        cnf.append([-var_a, zmienne[i]])
    dluga_klauzula = []
    for j in range(liczba_zmiennych):
        dluga_klauzula.append(-zmienne[j])
    cnf.append([var_a] + dluga_klauzula)


def sor(cnf: CNF, var_a: int, zmienne, liczba_zmiennych) -> None:
    for i in range(liczba_zmiennych):
        cnf.append([var_a, -zmienne[i]])
    dluga_klauzula = []
    for j in range(liczba_zmiennych):
        dluga_klauzula.append(zmienne[j])
    cnf.append([-var_a] + dluga_klauzula)

def sxor(cnf: CNF, var_a: int, zmienne, liczba_zmiennych) -> None:
    #tu można pomyśleć o a_var i reszta jako równanie a_var xor inne (z xorami między) = 0
    n = liczba_zmiennych + 1
    lista_roboczych_klauzul = []
    szablon = []
    szablon.append(var_a)
    for h in range(n - 1):
        szablon.append(zmienne[h])
    for i in range(2 ** n):
        szablonowa = szablon.copy()
        bini = [int(bit) for bit in f"{i:0{n}b}"]
        for j in range(n):
            if bini[j] == 1:
                szablonowa[j] = -szablonowa[j]
        lista_roboczych_klauzul.append(szablonowa)
    #tutaj usuwamy klauzule z parzystą ilością pozytywnych literałów
    lista_do_usuniecia = []
    for k in range(len(lista_roboczych_klauzul)):
        liczba = sum(1 for x in lista_roboczych_klauzul[k] if x > 0)
        if liczba % 2 == 0:
            lista_do_usuniecia.append(lista_roboczych_klauzul[k])
    for klauzula in lista_do_usuniecia:
        lista_roboczych_klauzul.remove(klauzula)
    #już mamy wszystkie klauzule które chcemy.
    for m in range(len(lista_roboczych_klauzul)):
        cnf.append(lista_roboczych_klauzul[m])



if __name__ == "__main__":
    cnf = CNF()
    idp = IDPool()

    print(idp)

    a_str = "a"
    liczba_zmiennych = 5
    zmienne = []

    a_var = idp.id(a_str)
    for i in range(liczba_zmiennych):
        nazwa = chr(98 + i)
        zmienne.append(idp.id(nazwa))

    #equals(cnf, a_var, b_var)
    sand(cnf, a_var, zmienne, liczba_zmiennych)
    sor(cnf, a_var, zmienne, liczba_zmiennych)
    sxor(cnf, a_var, zmienne, liczba_zmiennych)
    #cnf.append([-b_var])

    print(cnf.clauses)

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        solution = solver.solve()
        model = solver.get_model()

        print(solution)
        print(model)