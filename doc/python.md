## Macros in Python _(still in the writing process)_

[**yupp**](https://github.com/in4lio/yupp/) is a lexical macro processor
designed primarily to make up for the poor metaprogramming facilities of
the C language. The basic idea behind **yupp** is programming of a source
code transformation in the functional style.

If a given task fits in well with the metaprogramming paradigm, **yupp** not
only able to replace the C preprocessor, offering us more options, but also
can serve as a fully viable alternative to the C++ templates. As well,
**yupp** can be used with Python, since 
[PEP 263](https://www.python.org/dev/peps/pep-0263/) shows us the way to
modify any source file before calling Python’s internal parser.

You have to install [yupp package](https://pypi.python.org/pypi/yupp/)
to use the macro processor with Python:

    pip install yupp

Now, in order to Python have called **yupp** before running your source code,
you must start the source file with the declaration of `yupp` encoding:

    # coding: yupp

or with `yupp` encoding followed by a character encoding:

    # coding: yupp.<encoding name>

**yupp** performs a macro-expansion of the source code and generates the
source code in pure Python, it happens at the initial stage of the source
file run. Every next run if the source code does not get changed, the
macro-expansion phase will be skipped and the previously generated code will
be executed directly.

The macro processor gets various options from configuration files. Options
for all files of a directory should be specified in
[_".yuconfig"_](../../../blob/master/eg/.yuconfig) file, whereas individual
options for a single file in
[_"file.yuconfig"_](../../../blob/master/eg/dict.yuconfig).

Here is a small example of using macros in Python code:

    # coding: yupp

    ($set greeting '!dlrow olleH')

    print ($reversed greeting)

To be continued...

[yupp Wiki](https://github.com/in4lio/yupp/wiki/)
