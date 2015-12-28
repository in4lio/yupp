_in progress..._


###Standard Library (stdlib.yu)

####__dict__ (macro)

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
