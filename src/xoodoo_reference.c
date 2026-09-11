#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define VERBOSE_LEVEL 2

#define NLANES 12
#define NCOLUMS 4
#define NROWS 3
#define MAXROUNDS 12

typedef uint32_t tXoodooLane;

typedef struct {
    uint8_t A[48];
} Xoodoo_state;

#define ROTL32(a, offset) \
    (((uint32_t)(a) << (offset)) | ((uint32_t)(a) >> (32 - (offset))))

static unsigned int index_xy(int x, int y)
{
    x %= 4;
    if (x < 0)
        x += 4;

    y %= 3;
    if (y < 0)
        y += 3;

    return (unsigned int)(y * 4 + x);
}

static const uint32_t RC[MAXROUNDS] = {
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
};

static void Dump(const char *text, tXoodooLane *a, unsigned int level)
{
    if (level == VERBOSE_LEVEL) {
        printf("%s\n", text);

        printf(
            "a00 %08x, a01 %08x, a02 %08x, a03 %08x\n",
            a[0], a[1], a[2], a[3]
        );

        printf(
            "a10 %08x, a11 %08x, a12 %08x, a13 %08x\n",
            a[4], a[5], a[6], a[7]
        );

        printf(
            "a20 %08x, a21 %08x, a22 %08x, a23 %08x\n\n",
            a[8], a[9], a[10], a[11]
        );
    }
}

static void fromBytesToWords(
    tXoodooLane *stateAsWords,
    const uint8_t *state
)
{
    unsigned int i;
    unsigned int j;

    for (i = 0; i < NLANES; i++) {
        stateAsWords[i] = 0;

        for (j = 0; j < sizeof(tXoodooLane); j++) {
            stateAsWords[i] |=
                (tXoodooLane)(state[i * sizeof(tXoodooLane) + j])
                << (8 * j);
        }
    }
}

static void fromWordsToBytes(
    uint8_t *state,
    const tXoodooLane *stateAsWords
)
{
    unsigned int i;
    unsigned int j;

    for (i = 0; i < NLANES; i++) {
        for (j = 0; j < sizeof(tXoodooLane); j++) {
            state[i * sizeof(tXoodooLane) + j] =
                (stateAsWords[i] >> (8 * j)) & 0xFF;
        }
    }
}

static void Xoodoo_Round(
    tXoodooLane *a,
    tXoodooLane rc
)
{
    unsigned int x;
    unsigned int y;

    tXoodooLane b[NLANES];
    tXoodooLane p[NCOLUMS];
    tXoodooLane e[NCOLUMS];

    /*
     * Theta
     */

    for (x = 0; x < NCOLUMS; x++) {
        p[x] =
            a[index_xy(x, 0)] ^
            a[index_xy(x, 1)] ^
            a[index_xy(x, 2)];
    }

    for (x = 0; x < NCOLUMS; x++) {
        e[x] =
            ROTL32(p[index_xy((int)x - 1, 0)], 5) ^
            ROTL32(p[index_xy((int)x - 1, 0)], 14);
    }

    /*
     * UWAGA:
     * p[] ma tylko 4 elementy.
     * Dlatego poniżej poprawiamy indeksowanie ręcznie.
     */
    for (x = 0; x < NCOLUMS; x++) {
        unsigned int xm1 = (x + 3) % 4;

        e[x] =
            ROTL32(p[xm1], 5) ^
            ROTL32(p[xm1], 14);
    }

    for (x = 0; x < NCOLUMS; x++) {
        for (y = 0; y < NROWS; y++) {
            a[index_xy(x, y)] ^= e[x];
        }
    }

    Dump("Theta", a, 2);

    /*
     * Rho-west
     */

    for (x = 0; x < NCOLUMS; x++) {
        b[index_xy(x, 0)] =
            a[index_xy(x, 0)];

        b[index_xy(x, 1)] =
            a[index_xy((int)x - 1, 1)];

        b[index_xy(x, 2)] =
            ROTL32(a[index_xy(x, 2)], 11);
    }

    memcpy(a, b, sizeof(b));

    Dump("Rho-west", a, 2);

    /*
     * Iota
     */

    a[0] ^= rc;

    Dump("Iota", a, 2);

    /*
     * Chi
     */

    for (x = 0; x < NCOLUMS; x++) {
        for (y = 0; y < NROWS; y++) {
            b[index_xy(x, y)] =
                a[index_xy(x, y)] ^
                (
                    ~a[index_xy(x, (int)y + 1)] &
                    a[index_xy(x, (int)y + 2)]
                );
        }
    }

    memcpy(a, b, sizeof(b));

    Dump("Chi", a, 2);

    /*
     * Rho-east
     */

    for (x = 0; x < NCOLUMS; x++) {
        b[index_xy(x, 0)] =
            a[index_xy(x, 0)];

        b[index_xy(x, 1)] =
            ROTL32(
                a[index_xy(x, 1)],
                1
            );

        b[index_xy(x, 2)] =
            ROTL32(
                a[index_xy((int)x + 2, 2)],
                8
            );
    }

    memcpy(a, b, sizeof(b));

    Dump("Rho-east", a, 2);
}

static void Xoodoo_Permute_Nrounds(
    Xoodoo_state *state,
    unsigned int nr
)
{
    tXoodooLane a[NLANES];
    unsigned int i;

    fromBytesToWords(a, state->A);

    for (i = MAXROUNDS - nr; i < MAXROUNDS; i++) {
        printf(
            "========== RUNDA %u, RC = %08x ==========\n\n",
            i - (MAXROUNDS - nr) + 1,
            RC[i]
        );

        Xoodoo_Round(a, RC[i]);
    }

    fromWordsToBytes(state->A, a);
}

static void Xoodoo_Permute_12rounds(
    Xoodoo_state *state
)
{
    Xoodoo_Permute_Nrounds(state, 12);
}

static void print_state_bytes(
    const char *description,
    const Xoodoo_state *state
)
{
    unsigned int i;

    printf("%s\n", description);

    for (i = 0; i < 48; i++) {
        printf("%02x", state->A[i]);

        if ((i + 1) % 4 == 0)
            printf(" ");

        if ((i + 1) % 16 == 0)
            printf("\n");
    }

    printf("\n");
}

int main(void)
{
    Xoodoo_state state;

    /*
     * Przykładowy stan:
     *
     * 00 01 02 03
     * 04 05 06 07
     * ...
     * 2c 2d 2e 2f
     *
     * Łącznie 48 bajtów.
     */

    uint8_t input[48] = {
        0x00, 0x01, 0x02, 0x03,
        0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b,
        0x0c, 0x0d, 0x0e, 0x0f,

        0x10, 0x11, 0x12, 0x13,
        0x14, 0x15, 0x16, 0x17,
        0x18, 0x19, 0x1a, 0x1b,
        0x1c, 0x1d, 0x1e, 0x1f,

        0x20, 0x21, 0x22, 0x23,
        0x24, 0x25, 0x26, 0x27,
        0x28, 0x29, 0x2a, 0x2b,
        0x2c, 0x2d, 0x2e, 0x2f
    };

    memcpy(state.A, input, 48);

    print_state_bytes(
        "Stan wejściowy, 48 bajtów:",
        &state
    );

    printf(
        "Rozpoczynam Xoodoo[12]\n\n"
    );

    Xoodoo_Permute_12rounds(&state);

    print_state_bytes(
        "Stan końcowy po Xoodoo[12]:",
        &state
    );

    return 0;
}