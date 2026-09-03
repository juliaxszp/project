import random

def OTP(tekst,klucz):
    szyfrogram = []
    for i in range(0,len(tekst)):
        szyfrogram.append(ord(tekst[i]) ^ klucz[i])
    return szyfrogram

def deszyfracjaOTP(szyfrogram,klucz):
    tekst = []
    for i in range(0,len(szyfrogram)):
        tekst.append(chr(szyfrogram[i] ^ klucz[i]))
    return tekst


tekst = "Ala ma kota"
klucz=[]
for i in range(0,len(tekst)):
    klucz.append(random.randint(0,25))

szyfrogram=OTP(tekst,klucz)
print(szyfrogram)
print(deszyfracjaOTP(szyfrogram,klucz))
