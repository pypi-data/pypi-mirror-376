#ifndef __LIBILI2C_H
#define __LIBILI2C_H

#include <graal_isolate.h>


#if defined(__cplusplus)
extern "C" {
#endif

int createIlisMeta16(graal_isolatethread_t*, char*, char*);

int prettyPrint(graal_isolatethread_t*, char*);

int compileModel(graal_isolatethread_t*, char*, char*);

#if defined(__cplusplus)
}
#endif
#endif
