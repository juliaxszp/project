import matplotlib.pyplot as plt

unknown_bits = [1, 2, 4, 8, 10, 12, 14, 16, 20]
last = [0.12, 0.12, 0.15, 312, 174, 587, 1034, 3045, 4006]
first = [0.13, 0.17, 0.14, 0.18, 196, 398, 1793, 6015, 19368]
random = [0.06, 0.06, 0.07, 14, 57, 15, 1455, 1623, 8000]
plt.plot(unknown_bits, first, marker = "o", label = "Pierwsze bity")
plt.plot(unknown_bits, last, marker = "o", label = "Ostatnie bity")
plt.plot(unknown_bits, random, marker = "o", label = "Losowe bity")
plt.xlabel("Liczba nieznanych bitów")
plt.ylabel("Czas rozwiązania [s]")
plt.xticks(unknown_bits)
plt.legend()
plt.show()
