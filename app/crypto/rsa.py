import random
from .utils import gen_prime, gcd_, mod_inv, mod_exp


class RSA:
    def __init__(self, public_key=None, private_key=None):
        if not (private_key or public_key):
            public_key, private_key = self.generate_keypair()

        self.public_key = public_key
        self.private_key = private_key

    def encrypt(self, message):
        return self.let_rsa(self.public_key, message)

    def decrypt(self, ciphertext, result_length=40):
        return self.let_rsa(self.private_key, ciphertext, result_length)

    def encrypt_signature(self, message):
        return self.let_rsa(self.private_key, message)

    def decrypt_signature(self, ciphertext, result_length=40):
        return self.let_rsa(self.public_key, ciphertext, result_length)

    @staticmethod
    def generate_keypair():
        p, q = gen_prime(), gen_prime()

        n = p * q
        phi = (p - 1) * (q - 1)
        e = random.randrange(1, phi)

        g = 0
        counter = 0
        while g != 1 and counter < 128:
            e = random.randrange(1, phi)
            g = gcd_(e, phi)

        d = mod_inv(e, phi)

        e, d, n = format(e, 'x'), format(d, 'x'), format(n, 'x')

        return (e, n), (d, n)

    @staticmethod
    def let_rsa(given_key, message, result_length=None):
        if not given_key:
            raise ValueError("Set key first.")

        key, n = (int(i, 16) for i in given_key)
        if result_length is None:
            cipher = format(mod_exp(int(message, 16), key, n), 'x')
        else:
            cipher = format(mod_exp(int(message, 16), key, n), f'0{result_length}x')
        return cipher
