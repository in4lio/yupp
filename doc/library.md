_under construction..._


###Standard Library (stdlib.yu)

####dict

Dictionary to generate repeated structures of code.

```cpp
	($dict ID
		(` id_0       id_1       ... id_N )
		(`
		(  id_0_val_0 id_1_val_0 ... id_N_val_0 )
		(  id_0_val_1 id_1_val_1 ... id_N_val_1 )
		                         ...
		(  id_0_val_K id_1_val_K ... id_N_val_K )
		)
	)
	($each-ID \i.($i id_N))
```

####if, unless

```cpp
	($if cond [leg_T] [leg_F])
```

```cpp
	($unless cond [leg_F] [leg_T])
```

####unfold

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


###Coroutines (corolib.yu)

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


###Header Files Support (h.yu)

```cpp
	($h-begin-named)

	($h-extern-init,,int a[ 4 ],,{ 0, 1, 2, 3 })
	($h-extern) int b;

	($extern-c-begin)
	($h-extern) int f( void );
	($extern-c-end)

	($h-end)
```
