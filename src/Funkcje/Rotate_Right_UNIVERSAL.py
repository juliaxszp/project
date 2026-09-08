print('Rotacja jest dla 64bitowego slowa, jeśli chcesz zmienić to zmień 64 na dowolną liczbę bitów')
n = int(input('Podaj rotacje "n":'))


def rotate_right(S, n):
    output = []

    for i in range(64):
        output.append(S[(i - n) % 64])

    return output