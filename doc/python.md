## Macros in Python _(still in the writing process)_

[**yupp**][yupp] is a lexical macro processor designed primarily to make up
for the poor metaprogramming facilities of the C language. The basic idea
behind **yupp** is programming of a source code transformation in the
functional style.

If a given task fits in well with the metaprogramming paradigm, **yupp** not
only able to replace the C preprocessor, offering us more options, but also
can serve as a fully viable alternative to the C++ templates. As well,
**yupp** can be used with Python, since [PEP 263][pep-0263] shows us the way
to modify any source file before calling Python’s internal parser.

You have to install [yupp package][package] to use the macro processor with
Python:

    pip install yupp

Then, in order to Python have called **yupp** before running your source code,
you must start your source file with the declaration of `yupp` encoding:

    # coding: yupp

or with the `yupp` encoding followed by a character encoding:

    # coding: yupp.<encoding name>

**yupp** performs a macro-expansion of a source code containing macros and
generates a source code in pure Python. It happens at the initial stage of
a source file run. Every next run if the original source code does not get
changed, the macro-expansion phase will be skipped and the previously
generated code will be executed directly.

The macro processor gets various options from configuration files.
Options for all files of a directory should be specified in
[_".yuconfig"_](../eg/.yuconfig) file. Whereas individual options
for a particular file in [_"file.yuconfig"_](../eg/dict.yuconfig).

Here is a small example of using macros in Python:

    # coding: yupp

    ($set greeting '!dlrow olleH')

    print ($reversed greeting)

To be continued...

[yupp Wiki][wiki]

[pep-0263]: https://www.python.org/dev/peps/pep-0263/
[package]:  https://pypi.python.org/pypi/yupp/
[yupp]:     https://github.com/in4lio/yupp/
[wiki]:     https://github.com/in4lio/yupp/wiki/
