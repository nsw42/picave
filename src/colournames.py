
def colour_names(filename) -> dict:
    rtn = {}
    with open(filename, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            r, g, b, name = line.split(maxsplit=3)
            rtn[name] = [int(r), int(g), int(b)]
    return rtn
