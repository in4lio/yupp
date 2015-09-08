/*  coro.c was generated by yup.py (yupp) 0.8b8
    out of coro.yu-c at 2015-08-07 20:18
 */

#include <stdio.h>

void *lc_A = 0;
void *lc_B = 0;

int coro_A( void **ip )
{
	static int i;
	if ( *ip ) goto **ip;
	/* begin */
	for ( i = 0; i < 10; i++ ) {
		printf( "A%d ", i );
		/* yield */
		do {
			*ip = &&LC__0;
			return ( 1 );

			LC__0:;
		} while ( 0 );
	}
	/* end */
	*ip = &&LC__END_A;

	LC__END_A:
	return ( 0 );
}

int coro_B( void **ip )
{
	static int i;
	if ( *ip ) goto **ip;
	/* begin */
	for ( i = 0; i < 8; i++ ) {
		printf( "B%d ", i );
		/* yield */
		do {
			*ip = &&LC__1;
			return ( 1 );

			LC__1:;
		} while ( 0 );
	}
	/* end */
	*ip = &&LC__END_B;

	LC__END_B:
	return ( 0 );
}

int main( void )
{
	int alive_A, alive_B;
	do {
		alive_A = coro_A( &lc_A );
		alive_B = coro_B( &lc_B );
	} while ( alive_A || alive_B );
	printf( "\n" );

	return 0;
}