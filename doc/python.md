## Macros in Python _(still in the writing process)_

[**yupp**](https://github.com/in4lio/yupp/) is a lexical macro processor designed
primarily to compensate for the lack of metaprogramming facilities in the C language.
That macro processor allows us to program transformation of the source code in the
functional style.

In my experience, **yupp** not only able to replace weak C preprocessor but also
proposes an adequate alternative to a bit tricky templates. Equally well, **yupp**
can be used with Python, since [PEP 263](https://www.python.org/dev/peps/pep-0263/)
shows us the way to modify any source file before calling Python’s internal parser.

First of all, you need to install [yupp package](https://pypi.python.org/pypi/yupp/):

    pip install yupp

Start your source file with:

    # coding: yupp

[yupp Wiki](https://github.com/in4lio/yupp/wiki/)
