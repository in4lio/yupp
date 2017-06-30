A glance at the preprocessing
-----------------------------

Let's get acquainted with __yupp__ lexical preprocessor that allows metaprogramming in
the functional style. For that purpose, we will explore a small example from
[_"glance.yu-cpp"_](pic/glance.yu-cpp.md) file. The result of preprocessing is 
[_"glance.cpp"_](../eg/glance/glance.cpp) file. This example calculates the value of _Pi_
by the Leibniz formula increasing its accuracy at each run.

To begin with, embedding of preprocessor expressions into the source code occurs using
__an application form__ – `($<function> <arguments>)`. The first element of an application
is a function which can be called with arguments, for instance `($div 22 7)`.

__Comments__ that should not be saved in the generated text must be enclosed in the next
form – `($!<comment>)`.

Looking at preprocessor expressions of our example, we also are facing with the following
syntactic categories:
* __Simple lists__, like `(0 1 2 3)`.
* __Quotes__ – irreducible expressions or strings without quotation marks – ```(`<quote>)```.
* __Source code insertions__ using square brackets `[<text>]` or reverse square brackets
`]<EOL> <text> <EOL>[`. Source code insertions can also contain preprocessor expressions.
* __Lambda expressions__ – preprocessor expressions with parameters – `\<param>.\<param>.<expr>`.

__The set form__ – `($set <atom> <expr>)` allows to bound an atom (identifier) with a value,
for example a function of decrement could be defined as `($set dec \val.($sub val 1))`.

Our example begins with importing of [__yupp__ Standard Library](../lib/README.md) using
__the import form__ – `($import <file>)`.

![screenshot](pic/glance_01.png)

In particular, [_"stdlib.yu"_](../lib/stdlib.yu) contains __the dict macro__ which allows to
define a bunch of lists at once, that makes it easy to generate repeating code structures by
a dictionary. The foregoing application of __the dict macro__ is equal to:

```cpp
($set each-INI (  0                        1     2                         3       ))
($set TYPE     (  QDate                    int   QString                   double  ))
($set VAR      (  date                     step  greeting                  Pi      ))
($set DEFAULT  (  (`QDate::currentDate())  0     "Hello! Improving Pi..."  0.0     ))
```

The application of a list spawns __a cycle__, lambda expressions or functions passed as
arguments will be applied to each element of the list, e.g. `($(0 1 2) \i.($pow 10 i))`.

The application of a number retrieves an argument of that application by index, or if the only
argument is a list, retrieves an element of that list, e.g. `($2 (o o x o))`.

Unbound atoms (identifiers) from `INI` dictionary (`QString`, `Pi` etc.) will be processed
like quotes.

![screenshot](pic/glance_02.png)

The above snippet generates the following code:

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

You probably noticed a few weird using of square brackets. The construction
`]<EOL> ... <EOL>[`<br>
equals to ordinary `[ ... ]` but makes expressions, I dare say, more readable.

Another way to insert a short piece of code into the preprocessor expressions
is the double comma, e.g.<br>
`($count,,Wild Wild World,,W)`.

__Conditional expression__ contains: __condition__,
__alternative__ – an expression to be evaluated if the condition<br>
evaluates to zero (empty list `()`, empty code `[]` or empty quote ```(`)```)
and __consequent__ – an expression<br>
to be evaluated for other values of the condition –
```consequent ? condition | alternative```.

![screenshot](pic/glance_03.png)

The above functions after preprocessing:

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

The function `($q ... )` encloses an argument in quotation marks. For more
information, please goto<br>
[Built-in Functions](../doc/builtin.md).

__String formatting__ performs using the application of a string.
If the replacement field in the string contains<br>
a number, it refers to a positional argument, and if it contains an name,
it refers to a named argument, e.g.<br>
```($ "Lock, ($1) and ($p) Smoking ($0)" Barrels Stock \p 2)```.

![screenshot](pic/glance_04.png)

The foregoing snippet results in:

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
