class SHA1:
    INIT_H = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0)
    M2DEG32 = 0xFFFFFFFF

    def __init__(self, data):
        self.h = list(self.INIT_H)
        self.blocks = []
        self.update(data)

    def update(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not isinstance(data, bytes):
            raise ValueError(f"Unexpected data type: {data.__class__}")

        padded_data = self.padding(data)
        blocks = self.split_blocks(padded_data)

        self.blocks.extend(blocks)
        self.hashing_current_blocks()

    @classmethod
    def rotate(cls, n, b):
        return ((n << b) | (n >> (32 - b))) & cls.M2DEG32

    @staticmethod
    def padding(data):
        padding = b"\x80" + b"\x00" * (63 - (len(data) + 8) % 64)
        size = int.to_bytes(8 * len(data), 8, "big")
        padded_data = data + padding + size
        return padded_data

    @staticmethod
    def split_blocks(blocks):
        return [blocks[i:i+64] for i in range(0, len(blocks), 64)]

    def expand_block(self, block):
        w = [int.from_bytes(block[i:i+4], "big") for i in range(0, 128, 4)] + [0] * 64
        for i in range(16, 80):
            w[i] = self.rotate((w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16]), 1)
        return w

    def hashing_current_blocks(self):
        for block in self.blocks:
            expanded_block = self.expand_block(block)
            self.blocks.remove(block)
            a, b, c, d, e = self.INIT_H
            for i in range(0, 80):
                if 0 <= i < 20:
                    f = (b & c) | ((~b) & d)
                    k = 0x5A827999
                elif 20 <= i < 40:
                    f = b ^ c ^ d
                    k = 0x6ED9EBA1
                elif 40 <= i < 60:
                    f = (b & c) | (b & d) | (c & d)
                    k = 0x8F1BBCDC
                else:
                    f = b ^ c ^ d
                    k = 0xCA62C1D6
                a, b, c, d, e = (
                    self.rotate(a, 5) + f + e + k + expanded_block[i] & self.M2DEG32,
                    a,
                    self.rotate(b, 30),
                    c,
                    d,
                )
            self.h = (
                self.h[0] + a & self.M2DEG32,
                self.h[1] + b & self.M2DEG32,
                self.h[2] + c & self.M2DEG32,
                self.h[3] + d & self.M2DEG32,
                self.h[4] + e & self.M2DEG32,
            )

    def to_hash(self):
        return "%08x%08x%08x%08x%08x" % tuple(self.h)
