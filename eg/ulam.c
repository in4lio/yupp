/*  ulam.c was generated by yup.py (yupp) 0.9b6
    out of ulam.yu-c at 2016-09-10 01:29
 */

#include <stdio.h>

typedef void * co_t;
typedef unsigned int semaphore_t;

enum {
	CO_READY,
	CO_WAIT,
	CO_YIELD,
	CO_END,
	CO_SKIP,
};

#define SQ  19  /* odd, square side length */
static int spiral[ SQ * SQ ] = { 0 };

#define	PR_NONE  0
#define	PR_EOL  -1
#define	PR_DOT  -2
static int number = PR_NONE;  /* current state or prime number */

void init_spiral( void )
{
	const int dp[ 4 ] = { -SQ, -1, SQ, 1 };  /* step up, left, down and right */
	int p = SQ * SQ / 2;  /* position in spiral */
	int n = 2;  /* current number */
	int lch = 3;  /* chain length */
	int i, ii;

	spiral[ p ] = 1;
	spiral[ ++p ] = 2;
	while ( n < SQ * SQ ) {
		for ( i = 0; i < 4; i++ ) {  /* up-left-down-right cycle */
			for ( ii = 0; ii < lch >> 1; ii++ ) {  /* chain cycle */
				p += dp[ i ];
				spiral[ p ] = ++n;
			}
			++lch; /* chain grows up every second turn */
		}
	}
}

int isprime( int n )
{
	int i;

	if ( n == 2 ) return 1;
	if ( n == 1 || n % 2 == 0 ) return 0;
	for ( i = 3; i * i <= n; i += 2 ) if (( n % i ) == 0 ) return 0;
	return 1;
}

/* Define coroutines */

int coro_U( co_t *co_p )
{
	static int i;
	if ( *co_p ) goto **co_p;
	/* begin */
	for ( i = 0; i < SQ * SQ; i++ ) {
		number = spiral[ i ];

		if ( !isprime( number )) number = PR_DOT;
		do {
			/* yield */
			*co_p = &&L__0;
	
			return CO_YIELD;

			L__0:;
		} while ( 0 );

		/* check line breaking */
		if (( i % SQ ) == ( SQ - 1 )) number = PR_EOL;
		do {
			/* yield */
			*co_p = &&L__1;
	
			return CO_YIELD;

			L__1:;
		} while ( 0 );
	}
	/* end */
	*co_p = &&L__END_U;

	L__END_U:
	
	return CO_END;
}

int coro_L( co_t *co_p )
{
	
	if ( *co_p ) goto **co_p;
	/* begin */
	for ( ; ; ) {
		do {
			/* wait */
			*co_p = &&L__2;

			L__2:
			if (!( number > PR_NONE )) { /* cond */
		
				return CO_WAIT;
			}
		} while ( 0 );
		printf( "%03d ", number );
		number = PR_NONE;
	}
	/* end */
	*co_p = &&L__END_L;

	L__END_L:
	
	return CO_END;
}

int coro_A( co_t *co_p )
{
	
	if ( *co_p ) goto **co_p;
	/* begin */
	for ( ; ; ) {
		do {
			/* wait */
			*co_p = &&L__3;

			L__3:
			if (!( number == PR_DOT )) { /* cond */
		
				return CO_WAIT;
			}
		} while ( 0 );
		printf( " .  " );
		number = PR_NONE;
	}
	/* end */
	*co_p = &&L__END_A;

	L__END_A:
	
	return CO_END;
}

int coro_M( co_t *co_p )
{
	
	if ( *co_p ) goto **co_p;
	/* begin */
	for ( ; ; ) {
		do {
			/* wait */
			*co_p = &&L__4;

			L__4:
			if (!( number == PR_EOL )) { /* cond */
		
				return CO_WAIT;
			}
		} while ( 0 );
		printf( "\n" );
		number = PR_NONE;
	}
	/* end */
	*co_p = &&L__END_M;

	L__END_M:
	
	return CO_END;
}

/* Print ULAM spiral */

int main( void )
{
	co_t co_U = NULL;
	co_t co_L = NULL;
	co_t co_A = NULL;
	co_t co_M = NULL;

	init_spiral();
	while ( 1
		&& ((  coro_U( &co_U ) ) < CO_END )
		&& ((  coro_L( &co_L ) ) < CO_END )
		&& ((  coro_A( &co_A ) ) < CO_END )
		&& ((  coro_M( &co_M ) ) < CO_END )

	);
	return 0;
}
