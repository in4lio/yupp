
#include <math.h>
#include <QDate>
#include <QSettings>
#include <QDebug>

QDate ini_date = QDate::currentDate();
int ini_step = 0;
QString ini_greeting = "Hello! Improving Pi...";
double ini_Pi = 0.0;

void ini_load( const QString &fn )
{
	QSettings ini( fn, QSettings::IniFormat );

	ini_date = ini.value( "date", ini_date ).toDate();
	ini_step = ini.value( "step", ini_step ).toInt();
	ini_greeting = ini.value( "greeting", ini_greeting ).toString();
	ini_Pi = ini.value( "Pi", ini_Pi ).toDouble();

}

void ini_save( const QString &fn )
{
	QSettings ini( fn, QSettings::IniFormat );

	ini.setValue( "date", ini_date );
	ini.setValue( "step", ini_step );
	ini.setValue( "greeting", ini_greeting );
	ini.setValue( "Pi", ini_Pi );

}

#define ini_file  "glance.ini"

int main( void )
{
	ini_load( ini_file );

	// Calc Pi using Leibniz formula, add one term of the series
	ini_Pi += pow( -1, ini_step ) * 4.0 / ( ini_step * 2 + 1 );
	++ini_step;

	qDebug() << ini_date;
	qDebug() << ini_step;
	qDebug() << ini_greeting;
	qDebug() << ini_Pi;

	ini_save( ini_file );

	return ( 0 );
}
