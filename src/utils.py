def clip(low, val, high):
    '''
    >>> clip(5, 3, 10)
    5
    >>> clip(5, 5, 10)
    5
    >>> clip(5, 12, 10)
    10
    '''
    return min(max(low, val), high)


def format_mm_ss(ss):
    '''
    >>> format_mm_ss(0)
    '00:00'
    >>> format_mm_ss(1)
    '00:01'
    >>> format_mm_ss(10)
    '00:10'
    >>> format_mm_ss(60)
    '01:00'
    >>> format_mm_ss(61)
    '01:01'
    >>> format_mm_ss(70)
    '01:10'
    >>> format_mm_ss(119)
    '01:59'
    >>> format_mm_ss(181)
    '03:01'
    '''
    mm = ss / 60.
    ss = ss - int(mm) * 60
    return '%02u:%02u' % (mm, ss)


def parse_duration(duration_str: str):
    '''
    >>> parse_duration('2s')
    2
    >>> parse_duration('90s')
    90
    >>> parse_duration('1m')
    60
    >>> parse_duration('10m 5s')
    605
    >>> parse_duration('1h')
    3600
    >>> parse_duration('2h3m')
    7380
    >>> parse_duration('3h2m  1s')
    10921
    >>> parse_duration('4h 05s')
    14405
    '''
    orig_duration_str = duration_str

    def strip_leading_fragment(duration_str: str):
        index = 0
        while duration_str[index].isdigit():
            index += 1
        return int(duration_str[:index]), duration_str[index], duration_str[index + 1:].strip()
    duration = 0
    while duration_str:
        nr, unit, duration_str = strip_leading_fragment(duration_str)
        if unit == 'h':
            duration += nr * 60 * 60
        elif unit == 'm':
            duration += nr * 60
        elif unit == 's':
            duration += nr
        else:
            raise ValueError("Invalid duration %s" % orig_duration_str)
    return duration
