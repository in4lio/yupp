![screenshot](doc/pic/logo.png)

### VERSION

```
yupp        1.0c3
            2017-09-09
python      2.7
```

### WHAT IS IT?

**yupp** is a lexical preprocessor for C/C++, Python and
`<you name it>` languages.

[Read more...](doc/README.md)

### HELLO WORLD

```
#include <stdio.h>

($set greeting "Hello ($0)!\n")

int main( void )
{
    printf( ($greeting (`world)) );
    return ( 0 );
}
```

### HELLO IN PYTHON

```
# coding: yupp

($set greeting '!dlrow olleH')

if __name__ == '__main__':
    print ($reversed greeting)
```

### LICENSE

Please see the file called [_"LICENSE"_](LICENSE).
