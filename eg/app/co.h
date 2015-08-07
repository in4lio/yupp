
/*  co.h was generated by yup.py (yupp) 0.8b8
    out of co.yu-h at 2015-08-07 20:23
 *//**
 *  \file  co.h (co.yu-h)
 *  \brief  Coroutines declarations.
 *  \author  Vitaly Kravtsov (in4lio@gmail.com)
 *  \copyright  See the LICENSE file.
 */

#ifndef CO_H
#define CO_H

#ifdef  CO_IMPLEMENT
#define CO_EXT
#define CO_EXT_INIT( dec, init ) \
	dec = init
#else
#define CO_EXT extern
#define CO_EXT_INIT( dec, init ) \
	extern dec
#endif

#ifndef COMMA
#define COMMA   ,
#endif

#ifdef __cplusplus
extern "C" {
#endif

#include "coroutine.h"

/** "A" coroutine local context. */
CO_EXT_INIT( CORO_CONTEXT( A ), NULL );
/** "A" coroutine alive flag. */
CO_EXT_INIT( int A_alive, CO_SKIP );
/** "A" coroutine. */
extern CORO_DEFINE( A );
/** Initialize "A" coroutine. */
extern int A_init( void );
/** Uninitialize "A" coroutine. */
extern void A_uninit( void );
/** "B" coroutine local context. */
CO_EXT_INIT( CORO_CONTEXT( B ), NULL );
/** "B" coroutine alive flag. */
CO_EXT_INIT( int B_alive, CO_SKIP );
/** "B" coroutine. */
extern CORO_DEFINE( B );
/** Initialize "B" coroutine. */
extern int B_init( void );
/** Uninitialize "B" coroutine. */
extern void B_uninit( void );
/** "C" coroutine local context. */
CO_EXT_INIT( CORO_CONTEXT( C ), NULL );
/** "C" coroutine alive flag. */
CO_EXT_INIT( int C_alive, CO_SKIP );
/** "C" coroutine. */
extern CORO_DEFINE( C );
/** Initialize "C" coroutine. */
extern int C_init( void );
/** Uninitialize "C" coroutine. */
extern void C_uninit( void );

#ifdef __cplusplus
}
#endif

#endif

