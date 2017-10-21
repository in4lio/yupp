#include <math.h>
#include <stdio.h>

int main( void )
{
	float Co = 3.14159265359;
	double F = acos( -1 );
	float Zu = 3.14159292035;

	printf( "Hello world!\n" );

	printf( "Co = %.2f\n", Co );
	printf( "F = %.10f\n", F );
	printf( "Zu = %.6f\n", Zu );

	return 0;
}
