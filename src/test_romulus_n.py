# Testy KAT dla Romulus-N.
#
# Na tym etapie testujemy przypadki:
#   - PT = epsilon
#   - AD o coraz większej dlugosci
#
# Wartosci pochodza z oficjalnego:
# LWC_AEAD_KAT_128_128.txt
#
# Kolejne grupy:
#   1. podstawowe - juz masz
#   2. lekko trudniejsze
#   3. trudniejsze
#
# Oficjalny KAT:
# https://github.com/romulusae/romulus/blob/master/Implementations/software/ref/Romulus-N/LWC_AEAD_KAT_128_128.txt

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


KATS = [

    # ============================================================
    # 1. TESTY, KTORE JUZ MASZ
    # AD = 0..9 bajtow
    # ============================================================

    ("", "4F42AED219ECC79F4DAF3E3BAD52AEE7"),
    ("00", "AB8FE298CF6A3261F1F6C89B2B5E3367"),
    ("0001", "0AD6EE5DE5280CC51CBCAFBFCE5E99DF"),
    ("000102", "6CD9F20267266610D4F769EB602BFF17"),
    ("00010203", "19733DA1D8C16E0BD5F516A15BAA5908"),
    ("0001020304", "3A6D0641C711CF5B941364035663C7E7"),
    ("000102030405", "B48A50D9E16DA2D0BCC784DB7C126536"),
    ("00010203040506", "A3D9197875E4F92DA35A48B1E07483B7"),
    ("0001020304050607", "B96653DC95ED31D43A9E19DA42A71ABA"),
    ("000102030405060708", "ACA17AF4073855420675302764B5DC89"),

    # ============================================================
    # 2. LEKKO TRUDNIEJSZE
    # AD = 10..16 bajtow
    #
    # Tutaj dochodzimy do granicy 16-bajtowego bloku.
    # Szczegolnie wazne sa 15 i 16 bajtow.
    # ============================================================

    ("00010203040506070809",
     "7D79DF409392AA600A0D11CBFD906E80"),

    ("000102030405060708090A",
     "092E181F40BE039D2E3E487E7077E445"),

    ("000102030405060708090A0B",
     "DC663A1D1901CE72BE4A7F3E4C3EB0BF"),

    ("000102030405060708090A0B0C",
     "B50DD4A972DB1D311AFC204E29515C9B"),

    ("000102030405060708090A0B0C0D",
     "0F51E7B2AF267F0F22ABCD57F9A0D8C7"),

    # 16 bajtow - bardzo wazny przypadek graniczny
    ("000102030405060708090A0B0C0D0E",
     "39C467A055B702ABA9857E2C9A7DB716"),

    # 17 bajtow - przejscie ponad jeden blok
    ("000102030405060708090A0B0C0D0E0F",
     "413D3F77845E976AC72596E765B26B6A"),

    # ============================================================
    # 3. TRUDNIEJSZE
    # AD > 16 bajtow
    # ============================================================

    ("000102030405060708090A0B0C0D0E0F10",
     "D17F367D07F02A0F93E1DE5385529556"),

    ("000102030405060708090A0B0C0D0E0F1011",
     "5E8F2FC2BB627A819950B081BD9046A2"),

    ("000102030405060708090A0B0C0D0E0F101112",
     "099377EB20CE32F6C2741C0271D420BF"),

    ("000102030405060708090A0B0C0D0E0F10111213",
     "67EDE73262D0E89E8563F79B2C81183F"),

    ("000102030405060708090A0B0C0D0E0F1011121314",
     "0A02D202AC556A7C5D63BBCB48BD7C08"),

    ("000102030405060708090A0B0C0D0E0F101112131415",
     "26767C17A6F2827F555B8D821B087776"),

    ("000102030405060708090A0B0C0D0E0F10111213141516",
     "2FC4C0CD30343AD78C94300201C02CCC"),

    # ============================================================
    # 4. JESZCZE TRUDNIEJSZE
    # coraz dluzsze AD
    # ============================================================

    ("000102030405060708090A0B0C0D0E0F1011121314151617",
     "65374F9820E14134A09BDD2736D35374"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718",
     "DD7653B181923EE9618FEE4167C4329F"),

    ("000102030405060708090A0B0C0D0E0F10111213141516171819",
     "CF0F7BBBC999218F8965B0C95734F76A"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A",
     "C4C21C764765BE3CD6AD1D4B8B7C3156"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A1B",
     "E364473014F0B6E717B31D068FFEDE07"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C",
     "DC61BD30632AFA362E341B65243E10F0"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D",
     "64795075A3EFFD16C578234D83263384"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E",
     "7BAF89F08686EE2266C2A648795011A9"),

    ("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F",
     "77B3BBEA06D2F03827E928080703A571"),
]


for count, (ad, expected) in enumerate(KATS, 1):

    env = os.environ.copy()

    src_dir = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = (
        src_dir
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )

    cmd = [
        sys.executable,
        "-m",
        "src.romulus_n_main",
    ]

    if ad:
        cmd.append(ad)

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(f"Count {count}: ERROR")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)

    got = None

    for line in result.stdout.splitlines():
        if line.startswith("CT="):
            got = line[3:].strip().upper()
            break

    if got is None:
        print(f"Count {count}: ERROR - brak CT w wyjsciu")
        print(result.stdout)
        raise SystemExit(1)

    status = "OK" if got == expected else "FAIL"

    print(
        f"Count = {count:2d}  "
        f"AD_len={len(ad) // 2:2d}  "
        f"AD={ad:<64}  "
        f"got={got}  "
        f"expected={expected}  "
        f"{status}"
    )

    if got != expected:
        print("\nTEST KAT NIE PRZESZEDL.")
        print(f"AD       = {ad}")
        print(f"Got      = {got}")
        print(f"Expected = {expected}")
        raise SystemExit(1)


print()
print(f"Wszystkie {len(KATS)} testow KAT Romulus-N przeszly.")