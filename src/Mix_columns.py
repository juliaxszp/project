MIX_M = [
    [1,0,1,1],
    [1,0,0,0],
    [0,1,1,0],
    [1,0,1,0]
    ]

def Mix_columns(state):
    for i in range(4):
        a=state[0][i]
        b=state[1][i]
        c=state[2][i]
        d=state[3][i]

        state[0][i]=(a*MIX_M[0][0])^(b*MIX_M[0][1])^(c*MIX_M[0][2])^(d*MIX_M[0][3])
        state[1][i]=(a*MIX_M[1][0])^(b*MIX_M[1][1])^(c*MIX_M[1][2])^(d*MIX_M[1][3])
        state[2][i]=(a*MIX_M[2][0])^(b*MIX_M[2][1])^(c*MIX_M[2][2])^(d*MIX_M[2][3])
        state[3][i]=(a*MIX_M[3][0])^(b*MIX_M[3][1])^(c*MIX_M[3][2])^(d*MIX_M[3][3])


test_Mix = [
    [0x01, 0x01, 0x01, 0x01],
    [0x01, 0x01, 0x01, 0x01],
    [0x01, 0x01, 0x01, 0x01],
    [0x01, 0x01, 0x01, 0x01]
]   

print(Mix_columns(test_Mix))

for i in range(4):
    for j in range(4):
        print(hex(test_Mix[i][j]), end=' ')
    print()