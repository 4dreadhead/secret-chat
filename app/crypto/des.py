import des


class Des:
    def __init__(self, key_bytes=None):
        if key_bytes:
            self.key = self.KeyGen(key_bytes)

    def set_key(self, key_bytes):
        self.key = self.KeyGen(key_bytes)

    @staticmethod
    def decompose_message(message, f="utf-8"):
        match f:
            case "utf-8":
                msg_bin = "".join([format(int(byte), "08b")
                                   for byte in bytearray(message, "utf-8")])
            case "hex":
                msg_bin = "".join([format(int(byte, 16), "08b")
                                   for byte in [message[i:i+2] for i in range(0, len(message), 2)]])
            case _:
                raise ValueError("Incorrect data format.")

        return (msg_bin[i:i + 64].ljust(64, "0") for i in range(0, len(msg_bin), 64))

    @staticmethod
    def compose_message(blocks, f="utf-8"):
        result_bytes = bytearray()
        for i, block in enumerate(blocks):
            res = bytearray([int(block[i:i + 8], 2) for i in range(0, len(block), 8)])

            if blocks[i] is blocks[-1]:
                for j in range(len(res) - 1, -1, -1):
                    if res[j] != 0:
                        res = res[0:j+1]
                        break

            result_bytes += res

        match f:
            case "hex":
                result = "".join([format(byte, "02x") for byte in result_bytes if byte != 0x00])

            case "utf-8":
                try:
                    result = result_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    result = "".join([format(byte, "02x") for byte in result_bytes if byte != 0x00])

            case _:
                raise ValueError("Incorrect data format.")
        return result

    def encrypt(self, message):
        message_blocks = self.decompose_message(message, "utf-8")
        blocks = self.let_des_algorithm(message_blocks, "encrypt")
        return self.compose_message(blocks, "hex")

    def decrypt(self, message):
        message_blocks = self.decompose_message(message, "hex")
        blocks = self.let_des_algorithm(message_blocks, "decrypt")
        return self.compose_message(blocks, "utf-8")

    def let_des_algorithm(self, message_blocks, action="encrypt"):
        processed_data = []
        try:
            for counter, incoming_block in enumerate(message_blocks):
                result = self.process_block(incoming_block, action)
                processed_data.append(result)

        finally:
            return processed_data

    def process_block(self, incoming_block, action):
        block = self.message_shuffle(incoming_block, "START")

        match action:
            case "encrypt":
                for round_ in range(1, 17):
                    block = self.one_round(block, self.key.round_keys[round_], action)
                block = block[32:64] + block[:32]

            case "decrypt":
                block = block[32:64] + block[:32]
                for round_ in range(16, 0, -1):
                    block = self.one_round(block, self.key.round_keys[round_], action)

            case _:
                raise ValueError(f"Неизвестное действие: {action}.")

        result = self.message_shuffle(block, "END")
        return result

    @staticmethod
    def message_shuffle(bit_message, action):
        return "".join([bit_message[i - 1] for i in Des.IP_TABLES[action]])

    @staticmethod
    def widen_block(block):
        return "".join([block[i - 1] for i in Des.E_TABLE])

    @staticmethod
    def block_p_shuffle(block):
        return "".join([block[i - 1] for i in Des.P_TABLE])

    @staticmethod
    def xor(x, y, length):
        return format(int(x, 2) ^ int(y, 2), f"0{length}b")

    def process_message_block(self, block, key):
        wide_block = self.widen_block(block)
        wide_block = self.xor(wide_block, key, 48)

        _6bit_groups = [wide_block[6*i:6*(i+1)] for i in range(8)]
        result_block = "".join(
            [self.process_6bit_group(group, s_table) for group, s_table in zip(_6bit_groups, Des.S_TABLES)]
        )
        return self.block_p_shuffle(result_block)

    @staticmethod
    def process_6bit_group(_6bit_group, s_table):
        row = int(_6bit_group[0] + _6bit_group[-1], 2)
        column = int(_6bit_group[1:-1], 2)
        return format(s_table[row][column], "b").zfill(4)

    def one_round(self, block, round_key, action):
        first_block = block[:32]
        second_block = block[32:64]

        match action:
            case "encrypt":
                processed_block = self.process_message_block(second_block, round_key)
                return "".join([second_block, self.xor(first_block, processed_block, 32)])
            case "decrypt":
                processed_block = self.process_message_block(first_block, round_key)
                return "".join([self.xor(processed_block, second_block, 32), first_block])
            case _:
                raise ValueError(f"Неизвестное действие: {action}")

    # KeyGen class to generate round keys
    class KeyGen:
        def __init__(self, key):
            self.key_bytes = key
            self.key_bin = "".join([bin(byte)[2:].rjust(8, "0") for byte in self.key_bytes])
            self.add_control_bits()
            self.prepared_key = self.key_pc_shuffle(self.key_bin, "START")
            self.round_keys = self.generate_round_keys()

        def generate_round_keys(self):
            round_key = self.prepared_key
            round_keys = {}

            for round_ in range(1, 17):
                round_key = self.key_round_shuffle(round_key, round_)
                shuffled_round_key = self.key_pc_shuffle(round_key, "END")
                round_keys[round_] = shuffled_round_key

            return round_keys

        def add_control_bits(self):
            key_64bit = ""
            control_bits = []
            key_7bit_blocks = [self.key_bin[7 * i:7 * (i + 1)] for i in range(8)]

            for bits in key_7bit_blocks:
                control_bits.append(str(1 - sum(map(int, list(bits))) % 2))

            for block_7bit, control_bit in zip(key_7bit_blocks, control_bits):
                key_64bit += block_7bit + control_bit

            self.key_bin = key_64bit

        @staticmethod
        def key_pc_shuffle(key_64bit, action):
            return "".join([key_64bit[i - 1] for i in Des.PC_TABLES[action]])

        @staticmethod
        def key_round_shuffle(key_56bit, round_):
            first_block, second_block = key_56bit[:28], key_56bit[28:]
            result_blocks = []

            for block in (first_block, second_block):
                result_blocks.append(
                    "".join([block[(i + Des.ROUND_SHUFFLE_TABLE[round_]) % 28] for i in range(28)]))

            return "".join(result_blocks)

    # For debugging incorrect des results
    @staticmethod
    def debug_test_des(key, message):
        key_hex = bytearray([int(key[i:i+8], 2) for i in range(0, len(key), 8)])
        key_des = des.DesKey(key_hex)
        encrypted = key_des.encrypt(message.encode("utf-8"), padding=True)
        decrypted = key_des.decrypt(encrypted)

        def from_bytes_to_hex(b):
            return "".join([format(i, 'x') for i in b])

        print("[ DEBUG INFO ]")
        print(f"message: {message}")
        print(f"key hex: {from_bytes_to_hex(key_hex)}")
        print(f"encrypted message: {from_bytes_to_hex(encrypted)}")
        print(f"decrypted message: {from_bytes_to_hex(decrypted)}")

    # All required des constants

    ROUND_SHUFFLE_TABLE = {
        1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2,
        9: 1, 10: 2, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2, 16: 1
    }

    PC_TABLES = {
        "START": (
            57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18,
            10, 2, 59, 51, 43, 35, 27, 19, 11, 3, 60, 52, 44, 36,
            63, 55, 47, 39, 31, 23, 15, 7, 62, 54, 46, 38, 30, 22,
            14, 6, 61, 53, 45, 37, 29, 21, 13, 5, 28, 20, 12, 4
        ),
        "END": (
            14, 17, 11, 24, 1, 5, 3, 28, 15, 6, 21, 10, 23, 19, 12, 4,
            26, 8, 16, 7, 27, 20, 13, 2, 41, 52, 31, 37, 47, 55, 30, 40,
            51, 45, 33, 48, 44, 49, 39, 56, 34, 53, 46, 42, 50, 36, 29, 32
        )
    }

    IP_TABLES = {
        "START": (
            58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
            62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
            57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
            61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7
        ),
        "END": (
            40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31,
            38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29,
            36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27,
            34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25
        )
    }

    S_TABLES = (
        # S1
        ((14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7),
         (0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8),
         (4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0),
         (15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13)),

        # S2
        ((15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10),
         (3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5),
         (0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15),
         (13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9)),

        # S3
        ((10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8),
         (13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1),
         (13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7),
         (1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12)),

        # S4
        ((7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15),
         (13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9),
         (10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4),
         (3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14)),

        # S5
        ((2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9),
         (14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6),
         (4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14),
         (11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3)),

        # S6
        ((12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11),
         (10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8),
         (9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6),
         (4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13)),

        # S7
        ((4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1),
         (13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6),
         (1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2),
         (6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12)),

        # S8
        ((13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7),
         (1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2),
         (7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8),
         (2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11))
    )

    E_TABLE = (
        32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9, 8, 9,
        10, 11, 12, 13, 12, 13, 14, 15, 16, 17, 16,
        17, 18, 19, 20, 21, 20, 21, 22, 23, 24, 25,
        24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1
    )

    P_TABLE = (
        16, 7, 20, 21, 29, 12, 28, 17,
        1, 15, 23, 26, 5, 18, 31, 10,
        2, 8, 24, 14, 32, 27, 3, 9,
        19, 13, 30, 6, 22, 11, 4, 25
    )
