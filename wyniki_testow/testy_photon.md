# Analiza dla Photon-Beetle
1. Test KAT265, brak AD, 64 bitowy PTX

Ilość literałów: 455427
Ilość klauzul: 3270342 - n
gdzie n - liczba nieznanych bitów

### Test dla nieznanych ostatnich bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | 0.06 s |
| 2 | 0.06 s |
| 4 | 0.06 s |
| 8 | 15 s |
| 10 | 83 s |
| 12 | 99 s |
| 14 | 203 s |
| 16 | 674 s |
| 20 | 3056 s |
| 24 | > 15 h |

### Test dla nieznanych pierwszych bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | 0.07 s |
| 2 | 0.07 s |
| 4 | 0.07 s |
| 8 | 0.07 s |
| 10 | 25 s | 
| 12 | 147 s |
| 14 | 613 s |
| 16 | 1501 s | 
| 20 | ???? |


### Test dla nieznanych losowych bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | 0.08 s|
| 2 | 0.07 |
| 4 | 0.07 |
| 8 | 7 s |
| 10 | 10 s |
| 12 | 27 s |
| 14 | 605 s |
| 16 | 1840 s |
| 20 | ?? |

2. Test KAT454, z AD, 104 bitowy PTX

Ilość literałów: 910678
Ilość klauzul: 6540516 - n
gdzie n - liczba nieznanych bitów

### Test dla nieznanych ostatnich bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | 0.12 s |
| 2 | 0.12 s |
| 4 | 0.15 s |
| 8 | 312 s |
| 10 | 174 s |
| 12 | 587 s |
| 14 | 1034 s |
| 16 | 3045 s |
| 20 |  |
| 24 | |

### Test dla nieznanych pierwszych bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | 0.13 s |
| 2 | 0.17 s |
| 4 | 0.14 s |
| 8 | 0.18 s |
| 10 | 196 s | 
| 12 | 398 s|
| 14 | 1793 s |
| 16 | | 
| 20 | |


### Test dla nieznanych losowych bitów

| Ilość nieznanych bitów | Czas rozwiązania |
| -----------------------| ---------------- |
| 1 | |
| 2 | |
| 4 | |
| 8 | |
| 10 | |
| 12 | |
| 14 | |
| 16 | |
| 20 | |
