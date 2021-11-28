def a(z, v):
    for i in range(2):
        for i1 in range(2):
            for j in range(2):
                for k in range(2):
                    for l in range(2):
                        for m in range(2):
                            if v != z:
                                try:
                                    if v / 2:
                                        try:
                                            v += z
                                        except ValueError:
                                            print(z)
                                        v = z ** 2 + z
                                        u = v + 2
                                except ZeroDivisionError:
                                    print(z)

    return z + v