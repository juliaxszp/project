plik xoodyak_v1.py jest odpowiedzialny za generowanie relacji później wykorzystywanych do SATSolvera jak i generacji prawidłowych wartości na podstawie określonych wejść.

Założenia nieobecne w ogólnej implementacji xoodyaka:
- nonce wynosi 128 bitów
- AD jest niezerową wartością
w wersji v1 tekst jawny i AD są stałymi i nie da się zmienić ich długości.
