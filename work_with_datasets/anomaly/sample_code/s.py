def func_1(x):
    z = [-1] * 7
    if x > 0:
        z[0] = 0
        if x > 1:
            z[1] = 1
            if x > 2:
                z[2] = 2
                if x > 3:
                    z[3] = 3
                    if x > 4:
                        z[4] = 4
                        if x > 5:
                            z[5] = 5
                            if x > 6:
                                z[6] = 6
    return z