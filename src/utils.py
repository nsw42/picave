def clip(low, val, high):
    return min(max(low, val), high)


def format_mm_ss(ss):
    mm = ss / 60.
    ss = ss - int(mm) * 60
    return '%02u:%02u' % (mm, ss)
