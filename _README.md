![screenshot](doc/pic/logo.png)

### VERSION

    yupp        1.0c3
                2017-09-09
    python      2.7

### WHAT IS IT?

**yupp** is a lexical preprocessor for C/C++, Python and
&lt;you name it&gt; languages.

[FULL README](doc/README.md)

### HELLO WORLD

```cpp
    #include <stdio.h>

    ($set greeting "Hello ($0)!\n")

    int main( void )
    {
        printf( ($greeting (`world)) );
        return ( 0 );
    }
```

### HELLO IN PYTHON

```cpp
    # coding: yupp

    ($set greeting '!dlrow olleH')

    print ($reversed greeting)
```

### LICENSE

Please see the file called [_"LICENSE"_](LICENSE).
