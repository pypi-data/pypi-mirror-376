#ifndef __LIBILI2C_H
#define __LIBILI2C_H

#include <graal_isolate_dynamic.h>


#if defined(__cplusplus)
extern "C" {
#endif

typedef int (*createIlisMeta16_fn_t)(graal_isolatethread_t*, char*, char*);

typedef int (*prettyPrint_fn_t)(graal_isolatethread_t*, char*);

typedef int (*compileModel_fn_t)(graal_isolatethread_t*, char*, char*);

#if defined(__cplusplus)
}
#endif
#endif
