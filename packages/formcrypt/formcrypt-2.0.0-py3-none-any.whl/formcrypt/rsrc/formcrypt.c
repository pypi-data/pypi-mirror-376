#include "formcrypt.h"

void DecryptRc4Buffer(PENCRYPTED_BUFFER pEncryptedBuffer) {
    unsigned char   S[256], TrueKey[KEY_SIZE], temp;
    const char      *String1, *String2;
    unsigned int    i, j = 0, k, StringLength;

    // Retrieve the string length
    String1 = pEncryptedBuffer->Buffer;
    for (String2 = String1; *String2; ++String2);
    StringLength = String2 - String1;

    // Seperate key from fake function prologue
    for (int x = 0; x < KEY_SIZE; x++) {
        TrueKey[x] = pEncryptedBuffer->Key[PROLOGUE_SIZE + x];
    }

    // Key Scheduling Algorithm (KSA)
    for (i = 0; i < 256; i++) {
        S[i] = i;
    }
    for (i = 0; i < 256; i++) {
        j = (j + S[i] + TrueKey[i % KEY_SIZE]) % 256;
        temp = S[i];
        S[i] = S[j];
        S[j] = temp;
    }

    // Pseudo-Random Generation Algorithm (PRGA)
    i = j = 0;
    for (k = 0; k < StringLength; k++) {
        i = (i + 1) % 256;
        j = (j + S[i]) % 256;
        temp = S[i];
        S[i] = S[j];
        S[j] = temp;
        pEncryptedBuffer->Buffer[k] ^= S[(S[i] + S[j]) % 256];
    }
}