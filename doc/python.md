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

The following example demonstrates how to generate the source code in Python
using a dictionary. Data collected in this dictionary is used to create a set
of variables...

    #! /usr/bin/env python
    # coding: yupp

    ($__TITLE__ 0)

    ($import stdlib)

    ($dict VAR
        (` NAME        DEFVAL      FORMAT  )
        (`
        (  var_string  "montreal"  "%s"    )
        (  var_float   19.96       "%.2f"  )
        (  var_int     6           "%d"    )
        )
    )

    ($each-VAR \i.]
        ($i NAME) = ($i DEFVAL)

    [ )

    if __name__ == '__main__':
        ($each-VAR \i.]
            print ($q,,($i NAME) = ($unq ($i FORMAT))) % ( ($i NAME) )

        [ )

        var_int += 2

To be continued...

The macro processor gets various options from configuration files.
Options for all files of a directory should be specified in
[_".yuconfig"_](../eg/.yuconfig) file. Whereas individual options
for a particular file in [_"file.yuconfig"_](../eg/dict.yuconfig).

[yupp Wiki][wiki]

[pep-0263]: https://www.python.org/dev/peps/pep-0263/
[package]:  https://pypi.python.org/pypi/yupp/
[yupp]:     https://github.com/in4lio/yupp/
[wiki]:     https://github.com/in4lio/yupp/wiki/
