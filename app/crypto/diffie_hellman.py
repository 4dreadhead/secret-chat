from random import randint
from .utils import mod_exp, mod_inv, gen_prime


class DiffieHellman:
    def __init__(self, g=None, p=None):
        if g is None or p is None:
            self.generate_gp_params()
        else:
            self.g = int(g, 16)
            self.p = int(p, 16)

        self.k = self.generate_private_key()

        self.partial_key = self.generate_partial_key()
        self.partial_key_from_remote = None
        self.full_key = None
        self.session_key = None

    def get_g(self):
        return format(self.g, 'x')

    def get_p(self):
        return format(self.p, 'x')

    def get_partial_key(self):
        return format(self.partial_key, 'x')

    def generate_gp_params(self):
        self.p = gen_prime()

        while 1:
            self.g = mod_exp(randint(2, self.p), 2, self.p)

            if self.check_g_is_valid():
                break

    def check_g_is_valid(self):
        g = int(self.g)
        p = int(self.p)

        if g in (1, 2):
            return False

        if (p - 1) % g == 0:
            return False

        if (p - 1) % mod_inv(g, p) == 0:
            return False

        return True

    def generate_private_key(self):
        return randint(1, self.p)

    def generate_partial_key(self):
        return mod_exp(self.g, self.k, self.p)

    def generate_full_key(self):
        if not self.partial_key_from_remote:
            raise ValueError("Partial key from remote must be set first.")

        return mod_exp(self.partial_key_from_remote, self.k, self.p)

    def generate_session_key(self):
        parts = [self.full_key.to_bytes(64, "big")[i:i+8] for i in range(0, 56, 8)]
        return bytes([part[i] for i, part in enumerate(parts)])

    def set_partial_key_from_remote(self, partial_key_from_remote):
        self.partial_key_from_remote = int(partial_key_from_remote, 16)
        self.full_key = self.generate_full_key()
        self.session_key = self.generate_session_key()
