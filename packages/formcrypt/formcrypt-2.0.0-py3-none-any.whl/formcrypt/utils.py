def rc4(key, data):
        """
        RC4 encryption/decryption function.
        :param key: The key used for encryption/decryption (bytes)
        :param data: The plaintext/ciphertext data (bytes)
        :return: The processed data (bytes)
        """
        # Key Scheduling Algorithm (KSA)
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        
        # Pseudo-Random Generation Algorithm (PRGA)
        i = j = 0
        output = bytearray()
        for byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % 256]
            enc_byte = byte ^ K
            if (enc_byte == 0x00):
                return rc4(key, data)
            output.append(enc_byte)
        return bytes(output)

def to_c_byte_array_string( data ) -> str:
    byte_array_string = ""
    c = 0
    for i in data:
        format_string = "0x%02X," if c != (len(data) - 1) else "0x%02X"
        byte_array_string += format_string % ( i & 0xFF)
        c += 1
    return byte_array_string