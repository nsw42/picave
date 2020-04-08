
def ColourNames(filename) -> dict:
    rtn = {}
    with open(filename) as handle:
        for line in handle:
            line = line.strip()
            r, g, b, name = line.split(maxsplit=3)
            rtn[name] = [int(r), int(g), int(b)]
    return rtn
