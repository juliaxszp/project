import ctypes
lib = ctypes.CDLL( "/home/julia/Desktop/studies/Software/crypto_aead/photonbeetleaead128rate128v1/ref/libphotonbeetle.so")
encrypt = lib.crypto_aead_encrypt


U8_PTR = ctypes.POINTER(ctypes.c_ubyte)

encrypt.argtypes = [
    U8_PTR,                              
    ctypes.POINTER(ctypes.c_ulonglong),  
    U8_PTR,                              
    ctypes.c_ulonglong,                  
    U8_PTR,                              
    ctypes.c_ulonglong,                  
    U8_PTR,                              
    U8_PTR,                              
    U8_PTR                               
]

encrypt.restype = ctypes.c_int

def photon_encrypt(key_hex, nonce_hex, ad_hex, ptx_hex):
    key = bytes.fromhex(key_hex)
    nonce = bytes.fromhex(nonce_hex)
    ad = bytes.fromhex(ad_hex)
    ptx = bytes.fromhex(ptx_hex)

    key_array = (ctypes.c_ubyte * len(key))(*key)
    nonce_array = (ctypes.c_ubyte * len(nonce))(*nonce)
    ptx_array = (ctypes.c_ubyte * len(ptx))(*ptx)

    if len(ad) > 0:
        ad_array = (ctypes.c_ubyte * len(ad))(*ad)
    else:
        ad_array = None
    output = (ctypes.c_ubyte * (len(ptx) + 16))()

    output_len = ctypes.c_ulonglong(0)

    result = encrypt(
        output,                    
        ctypes.byref(output_len),  
        ptx_array,                 
        len(ptx),                  
        ad_array,                  
        len(ad),                   
        None,                      
        nonce_array,               
        key_array                 
    )

    if result != 0:
        raise RuntimeError("PHOTON-Beetle encryption failed")

    ciphertext_tag = bytes(output[:output_len.value])

    return ciphertext_tag.hex().upper()

"""key = "000102030405060708090A0B0C0D0E0F"
nonce = "000102030405060708090A0B0C0D0E0F"
ad = ""
ptx = "0001020304050607"

result = photon_encrypt(key, nonce, ad, ptx)

print(result)"""