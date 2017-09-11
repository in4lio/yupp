    yet another lexical preprocessor
     __    __    _____ _____
    /\ \  /\ \  /\  _  \  _  \
    \ \ \_\/  \_\/  \_\ \ \_\ \
     \ \__  /\____/\  __/\  __/
      \/_/\_\/___/\ \_\/\ \_\/
         \/_/      \/_/  \/_/

    ($($\y:u.\m.\...(m y($\C.\p.(r)e p)($\ro.(ce)s)))so r)

### VERSION

    yup.py      1.0c3
                2017-09-09
    python      2.7


### WHAT IS IT?

**yupp** is a lexical preprocessor for C/C++, Python and
<you name it> languages.

Read more: https://github.com/in4lio/yupp/tree/master/doc/


### HELLO WORLD

    #include <stdio.h>

    ($set greeting "Hello ($0)!\n")

    int main( void )
    {
        printf( ($greeting (`world)) );
        return ( 0 );
    }

### HELLO IN PYTHON

    # coding: yupp

    ($set greeting '!dlrow olleH')

    print ($reversed greeting)

### LICENSE

    Please see the file called "LICENSE".
