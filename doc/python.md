## Macros in Python _(still in the writing process)_

[**yupp**](https://github.com/in4lio/yupp/) is a lexical macro processor designed
primarily to compensate for the lack of metaprogramming facilities in the C language.
**yupp** allows to program transformation of the source code in the functional style.
For the tasks that fit into the metaprogramming paradigm well, **yupp** not only able
to replace the C preprocessor, but also can stand as an adequate alternative to
the C++ templates. Equally well, **yupp** can be used with Python, since
[PEP 263](https://www.python.org/dev/peps/pep-0263/)
shows us the way to modify any source file before calling Python’s internal parser.

First of all, you need to install [yupp package](https://pypi.python.org/pypi/yupp/):

    pip install yupp

Start your source file with:

    # coding: yupp

[yupp Wiki](https://github.com/in4lio/yupp/wiki/)
