import matplotlib.pyplot as plt

unknown_bits = [1, 2, 4, 8, 10, 12, 14, 16, 20]
last = [0.06, 0.06, 0.06, 15, 83, 99, 203, 674, 3056]
first = [ 0.07, 0.07, 0.07, 0.07, 25, 147, 613, 1501, 12168]
random = [0.08, 0.07, 0.07, 7, 10, 27, 605, 1840, 2672]
plt.plot(unknown_bits, first, marker = "o", label = "Pierwsze bity")
plt.plot(unknown_bits, last, marker = "o", label = "Ostatnie bity")
plt.plot(unknown_bits, random, marker = "o", label = "Losowe bity")
plt.xlabel("Liczba nieznanych bitów")
plt.ylabel("Czas rozwiązania [s]")
plt.xticks(unknown_bits)
plt.legend()
plt.show()