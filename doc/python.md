## Macros in Python _(still in the writing process)_

[**yupp**](https://github.com/in4lio/yupp/) is a lexical macro processor
designed primarily to compensate for the lack of metaprogramming facilities
in the C language. The idea behind **yupp** is programming of a source code
transformation in the functional style.

If our task fits well into the metaprogramming paradigm, **yupp** able to
replace the C preprocessor, giving us more options, or even can act as a
viable alternative to the C++ templates. As well, **yupp** can be used with
Python, since [PEP 263](https://www.python.org/dev/peps/pep-0263/) shows us
the way to modify any source file before calling Python’s internal parser.

You have to install [yupp package](https://pypi.python.org/pypi/yupp/)
to use the macro processor with Python:

    pip install yupp

Now, in order to Python have called **yupp** before running your source code,
you must start the source file with the declaration of `yupp` encoding:

    # coding: yupp

or with `yupp` encoding followed by a character encoding:

    # coding: yupp.<encoding name>

**yupp** performs a macro-expansion of our source code and generates the
source code in pure Python, it happens at the initial stage of our source
file run. Every next run if our source code does not get changed, the
macro-expansion phase will be skipped and the previously generated code will
be executed directly.

Macro processor options for all files in a directory can be specified into
[_".yuconfig"_](../../../blob/master/eg/.yuconfig) file, individual options
for a single file in [_"file.yuconfig"_](../../../blob/master/eg/dict.yuconfig).

[yupp Wiki](https://github.com/in4lio/yupp/wiki/)
