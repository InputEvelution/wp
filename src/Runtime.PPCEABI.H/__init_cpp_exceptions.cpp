#include "Runtime.PPCEABI.H/NMWException.h"
#include "Runtime.PPCEABI.H/__ppc_eabi_linker.h"

extern "C"{
	extern void __init_cpp_exceptions(void);
	extern void __fini_cpp_exceptions(void);
}

static int fragmentID = -2;

static inline void __exception_info_constants(void** info, char** R2) {
	register char* temp;
	asm {	mr temp, r2; }
	*R2 = temp;
	*info = (void*)_eti_init_info;
}

extern void __init_cpp_exceptions(void) {
	char* R2;
	void* info;
	if (fragmentID == -2) {
		__exception_info_constants(&info, &R2);
		fragmentID = __register_fragment((struct __eti_init_info*)info, R2);
	}
}

extern void __fini_cpp_exceptions(void) {
	if (fragmentID != -2) {
		__unregister_fragment(fragmentID);
		fragmentID = -2;
	}
}

#pragma push
// HACK: When DTK sets all objects to force_active, the linker decides to strip
// these, for some reason. Set them to force_active as well.
#pragma force_active on

#pragma section ".ctors$10"
__declspec(section ".ctors$10") 
	extern void * const __init_cpp_exceptions_reference = __init_cpp_exceptions;
#pragma section ".dtors$10"
__declspec(section ".dtors$10") 
	extern void * const __destroy_global_chain_reference = __destroy_global_chain;
#pragma section ".dtors$15"
__declspec(section ".dtors$15") 
	extern void * const __fini_cpp_exceptions_reference = __fini_cpp_exceptions;

#pragma pop
