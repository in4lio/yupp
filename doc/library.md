_still in the process..._

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
	($if cond [leg_T] [leg_F])
```

```cpp
	($unless cond [leg_F] [leg_T])
```

####unfold

This macro allows to unfold a sequence of specified number of elements (the first argument).<br>
If the number of arguments is greater than two, the second argument is the first element
of the sequence, and so on.
The last argument is a lambda function with the sequence number as a parameter,
to calculate missing members of the sequence. 

```cpp
	($unfold N [val_0] [val_1] [...] \n.(val_($n)))
```

####do

```cpp
	($do,,foo(); bar(); )
```

####define

```cpp
	($define,,array_length( x ),,( sizeof( x ) / sizeof(( x )[ 0 ])))
```

####def, undef

```cpp
	($def LINK_MODULE)
```

```cpp
	($undef LINK_MODULE)
```

####def-if

```cpp
	($def-if LINK_MODULE)
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
