A glance at the yupp
--------------------

The source file of this example is [glance.yu-cpp](../eg/glance/glance.yu-cpp),
the result file - [glance.cpp](../eg/glance/glance.cpp).

Embedding of the preprocessor expressions into the source code (text) occurs
using an __application form__ `($ ... )`.
The first element of an application is a function, that can be called with
arguments, e.g. `($add 40 2)`.<br>
The application `($! ... )` is used for __comments__.

Looking at the preprocessor expressions of this example, you will also meet
other syntactic forms:
* __simple lists__, e.g. `(0 1 2 3)`;
* __quotes__ - irreducible expressions or strings without quotation marks -
```(` ... )```;
* __source code insertions__ using square brackets `[ ... ]` or reverse square
brackets `]<EOL> ... <EOL>[`
(the insertions also can contain the preprocessor expressions);
* __lambda expressions__ - expressions with parameters - `\a.\b.\c.( ... )`.

__Set form__ `($set ... )` allows to bound an atom with a value, for example
the decrement function definition is `($set dec \p.($sub p 1))`.

The following code snippet begins with `($import ... )` of the standard library.
The [stdlib.yu](../lib/stdlib.yu) in particular contains __dict__ macro
intended to define a series of lists that make it easy to generate
repeating code structures by a dictionary.

![screenshot](pic/glance_01.png)

The foregoing application of __dict__ macro corresponds to:

```cpp
($set each-INI (  0                        1     2                         3       ))
($set TYPE     (  QDate                    int   QString                   double  ))
($set VAR      (  date                     step  greeting                  Pi      ))
($set DEFAULT  (  (`QDate::currentDate())  0     "Hello! Improving Pi..."  0.0     ))
```

![screenshot](pic/glance_02.png)

```cpp
#include <math.h>
#include <QDate>
#include <QSettings>
#include <QDebug>

QDate ini_date = QDate::currentDate();
int ini_step = 0;
QString ini_greeting = "Hello! Improving Pi...";
double ini_Pi = 0.0;
```

![screenshot](pic/glance_03.png)

```cpp
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
```

![screenshot](pic/glance_04.png)

```cpp
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
```
