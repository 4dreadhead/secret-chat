from math import gcd
from Crypto.Math.Primality import generate_probable_safe_prime, generate_probable_prime


def mod_exp(base=0, exp=0, mod=1, use_builtin_function=True):
    if use_builtin_function:
        return pow(base, exp, mod)

    result = 1
    while exp:
        if exp & 1:
            result = result * base % mod
        exp >>= 1
        base = base ** 2 % mod

    return result


def gcd_(a=1, b=1, use_builtin_function=True):
    if use_builtin_function:
        return gcd(a, b)

    while b:
        a, b = b, a % b
    return a


def mod_inv(base=0, mod=1, use_builtin_function=True):
    if use_builtin_function:
        return pow(base, -1, mod)

    if gcd(base, mod) != 1:
        raise ValueError("base is not invertible for the given modulus")

    for num in range(1, mod+1):
        if (num * base) % mod == 1:
            return num

    return None


def gen_prime(safe_prime=False):
    # Function generate_probably_safe_prime evaluates too long (> 10 sec)
    return int(generate_probable_safe_prime(exact_bits=512) if safe_prime else generate_probable_prime(exact_bits=512))
