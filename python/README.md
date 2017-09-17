## **yupp** Python Package

### How to start using **yupp** with Python 2

`1.` Install Python package:

    pip install yupp

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

### Examples

Source code                          | Generated code                       | Description
:---                                 | :---                                 | :---
[.yuconfig](../eg/.yuconfig)         | –                                    | Preprocessor options for the entire directory
[coding.yu-py](../eg/coding.yu-py)   | [coding.py](../eg/coding.py)         | Source code encoding
[coro.py](../eg/coro.py)             | [coro.yugen.py](../eg/coro.yugen.py) | Coroutines
[dict.yu-py](../eg/dict.yu-py)       | [dict.py](../eg/dict.py)             | Using a dictionary to generate code
[dict.yuconfig](../eg/dict.yuconfig) | –                                    | Preprocessor options for the single file

[Further examples...](../eg/)

### See also

[Configure Sublime Text](../sublime_text/)
