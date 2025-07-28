import sys

WIDTH = 80
HEIGHT = 24
MAX_ITER = 30

# Determine region in complex plane
RE_START, RE_END = -2.0, 1.0
IM_START, IM_END = -1.0, 1.0

for y in range(HEIGHT):
    imag = IM_START + (y / HEIGHT) * (IM_END - IM_START)
    for x in range(WIDTH):
        real = RE_START + (x / WIDTH) * (RE_END - RE_START)
        c = complex(real, imag)
        z = 0j
        iter = 0
        while abs(z) <= 2 and iter < MAX_ITER:
            z = z*z + c
            iter += 1
        # Choose character based on escape time
        if iter == MAX_ITER:
            char = '*'
        elif iter > MAX_ITER / 2:
            char = '+'
        elif iter > MAX_ITER / 4:
            char = '-'
        else:
            char = ' '
        sys.stdout.write(char)
    sys.stdout.write('\n')

