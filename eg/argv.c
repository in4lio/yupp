/*  argv.c was generated by yup.py (yupp) 0.9b6
    out of argv.yu-c at 2016-09-10 01:28
 */

#include <stdarg.h>
#include <stdio.h>

int sumi( int argcnt, ... )
{
    int result = 0;
    va_list argptr;
    va_start( argptr, argcnt );
    while ( argcnt-- ) result += va_arg( argptr, int );
    va_end( argptr );
    return ( result );
}

double sumf( int argcnt, ... )
{
    double result = 0;
    va_list argptr;
    va_start( argptr, argcnt );
    while ( argcnt-- ) result += va_arg( argptr, double );
    va_end( argptr );
    return ( result );
}

int main( void )
{
    printf( "%d %.1f"
    , sumi( 4, 1, 3, 5, 7 )
    , sumf( 4, 2.0, 4.0, 6.0, 8.0 )
    );
    return 0;
}
