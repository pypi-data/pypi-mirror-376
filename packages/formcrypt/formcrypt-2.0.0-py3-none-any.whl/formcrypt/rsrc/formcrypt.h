#pragma once
#define SHADOW_SPACE_SIZE 0x20
#define KEY_SIZE 8

#ifndef ARCH_X86
#define PROLOGUE_SIZE 8

/*
	push rbp
	mov rbp, rsp
	sub rsp, SHADOW_SPACE_SIZE
*/
#define FUNCTION_PROLOG 0x55, 0x48, 0x89, 0xE5, 0x48, 0x83, 0xEC, SHADOW_SPACE_SIZE

/*
	add rsp, SHADOW_SPAPCE_SIZE
	pop rbp
	ret
*/
#define FUNCTION_EPILOG 0xCC, 0xCC, 0xCC, 0x48, 0x83, 0xC4, SHADOW_SPACE_SIZE, 0x5D, 0xC3
#endif

#ifdef ARCH_X86
#define PROLOGUE_SIZE 6
/*
	push ebp
	mov ebp, esp
*/
#define FUNCTION_PROLOG 0xCC, 0xCC, 0xCC, 0x55, 0x8B, 0xEC

/*
	mov esp, ebp
	pop ebp
	ret
*/
#define FUNCTION_EPILOG 0xCC, 0xCC, 0xCC, 0x89, 0xEC, 0x5D, 0xC3
#endif

typedef struct _ENCRYPTED_BUFFER {
	char Key[PROLOGUE_SIZE + KEY_SIZE];
	char Buffer[];
} ENCRYPTED_BUFFER, *PENCRYPTED_BUFFER;

void DecryptRc4Buffer(PENCRYPTED_BUFFER pEncryptedBuffer);

#define NEW_BUFFER(VariableName, Ciphertext, Cipherkey)	\
	ENCRYPTED_BUFFER VariableName = {					\
		.Key	= { FUNCTION_PROLOG, Cipherkey },		\
		.Buffer = { Ciphertext, 0x00, FUNCTION_EPILOG }	\
	}													\

