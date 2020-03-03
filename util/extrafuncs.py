import math

ABBREVIATIONS = ['', 'k', 'mil', 'bil', 'tril']
ABBREVIATION_DICT = {
    '' : 1,
    'k' : 1000,
    'm' : 1000000,
    'mil' : 1000000,
    'b' : 1000000000,
    'bil' : 1000000000,
    't' : 1000000000000,
    'tril' : 1000000000000
}

def roundSig(n):
    power = int(math.floor(math.log10(abs(n))))
    if power < 1:
        power = 0
        return round(n, 2), power
    return round(n, 4 - int(math.floor(math.log10(abs(n)))) - 1), power

def shortenPrice(price):
    price, power = roundSig(price)
    if power // 3 == 0:
        return str(price)
    if power > 14:
        return "{:.3e}".format(price)
    return str(price / (10 ** (power // 3 * 3))) + ABBREVIATIONS[power // 3]