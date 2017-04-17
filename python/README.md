### How to start using `yupp` with Python 2

`1.` Install Python package:
  
    pip install --pre yupp

`2.` Start your code in Python with:

    # coding: yupp

for example:

    # coding: yupp
    # test.py

    ($set hola 'Hello world!')
    print ($hola)

`3.` Run the script in the usual way:

    python ./test.py

    Hello world!

`4.` The next run will be executed a bit fast because of the preprocessing phase is skipped.

### How to define source code encoding

    # coding: yupp.cp1252

### See also

[Configure Sublime Text](../sublime_text/)

[Further examples](../eg/)
