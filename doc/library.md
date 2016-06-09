_Sorry, still in the process..._

Standard Library (stdlib.yu)
----------------------------
```
($import stdlib)
```
####dict

This macro allows to define a series of lists that make it easy to generate
repeating code structures by a dictionary.

```cpp
	($dict NAME
		(` col_1_name   col_2_name     col_N_name  )
		(`
		(  col_1_val_1  col_2_val_1    col_N_val_1 )
		(  col_1_val_2  col_2_val_2    col_N_val_2 )

		(  col_1_val_M  col_2_val_M    col_N_val_M )
		)
	)
```

For example:

![screenshot](pic/library_01.png)

The foregoing application of `dict` macro corresponds to:

```cpp
($set each-INI (  0                        1     2                         3       ))
($set TYPE     (  QDate                    int   QString                   double  ))
($set VAR      (  date                     step  greeting                  Pi      ))
($set DEFAULT  (  (`QDate::currentDate())  0     "Hello! Improving Pi..."  0.0     ))
```

The application of `each-INI` spawns cycle from 0 to 3.

![screenshot](pic/library_02.png)

This snippet generates the following code:

```cpp
QDate ini_date = QDate::currentDate();
int ini_step = 0;
QString ini_greeting = "Hello! Improving Pi...";
double ini_Pi = 0.0;
```

####if, unless

Another way to write a conditional expression.

```cpp
($if ($eq 4 ($add 2 2)) [ALL RIGHT] [SMOKE DETECTED])

ALL RIGHT
```

```cpp
($unless ($eq 4 ($add 2 2)) "It's impossible!" "OK")

"OK"
```

####unfold

This macro allows to unfold a sequence of specified number of elements (the first argument).
If the number of arguments is greater than two, the second argument is the first element
of the sequence, and so on. The last argument is a lambda function with the sequence number
as a parameter, to calculate missing members of the sequence.

```cpp
($unfold 7 A B C \n.($add n 1))

ABC4567
```

####do
The macro places an argument into the single-pass `do-while` statement. It's usually used together with `define` macro.

```cpp
($do ]
	foo(); bar();
[ )

do {
	foo(); bar();
} while ( 0 )
```

####foo
It does the same thing as `do` macro but using Statements in Expressions GNU Extension `({ })`.

####define
Define C macro `($define signature body)`.

```cpp
($define,,CLEAR_VAR( var, mask ),,($do ]
	var &= ~( mask );
[ ))

#define CLEAR_VAR( var, mask ) do { \
	var &= ~( mask ); \
} while ( 0 )
```

####def
```cpp
($def NAME)
```
Define empty C macro `NAME` and bind the same *yupp* atom with `1`.

```cpp
($def LINK_MODULE)

#define LINK_MODULE
```

####undef
```cpp
($undef NAME)
```
Undefine C macro `NAME` and bind the same *yupp* atom with `0`.

```cpp
($undef LINK_MODULE)

#undef  LINK_MODULE
```

####def-if
```cpp
(def-if COND NAME)
```
Define empty C macro `NAME` and bind the same *yupp* atom with `1` only if `cond` is true.

```cpp
($def-if LINK_MODULE LINK_MODULE_TEST)
```

####skip-if-not

```cpp
	($skip-if-not LINK_MODULE)
```

####BIN, BB

```cpp
	($BIN,,11001010110010100000)
```

```cpp
	($BB,,10110011,,10110010,,10110001,,10110000)
```

####def-fn-argv

```cpp
	($def-fn-argv int sum ]
		int result = 0;
		($ &arg-begin)
		while ( ($ &arg-count)-- ) result += ($ &arg-value &type);
		($ &arg-end)
		return ( result );
	[ )
```

#### INT_MAX, INT_MIN

Minimal and maximal values of `int32_t`.


Coroutines (corolib.yu)
-----------------------
```
($import corolib)
```
```cpp
	($coro-context A);
	($coro-context B);

	($coro-define A ]
		for ( ; ; ) {
			/* ... */
			($coro-yield);
		}
	[ )

	($coro-define B ]
		for ( ; ; ) {
			/* ... */
			($coro-wait cond);
		}
	[ \enter ]
		($coro-local) int b;
	[ )

	int main( void )
	{
		for ( ; ; ) {
			($coro-call A);
			($coro-call B);
		}
		return 0;
	}
```


Header Files Helper (h.yu)
--------------------------
```
($import h)
```
```cpp
	($h-begin-named)

	($h-extern-init,,int a[ 4 ],,{ 0, 1, 2, 3 })
	($h-extern) int b;

	($extern-c-begin)
	($h-extern) int f( void );
	($extern-c-end)

	($h-end)
```
