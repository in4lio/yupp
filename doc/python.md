## Macros in Python _(still in the writing process)_

[**yupp**][yupp] is a lexical macro processor designed primarily to make up
for the poor metaprogramming facilities of the C language. The basic idea
behind **yupp** is programming of source code transformation in the functional
style.

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

**yupp** performs a macro-expansion of source code containing macros and
generates source code in pure Python. It happens at the initial stage of
a source file run. Every next run if the original source code does not get
changed, the macro-expansion phase will be skipped and the previously
generated code will be executed directly.

The following example demonstrates how to generate source code in Python
using a dictionary. Data collected in this dictionary is used to create,
initialize and print a set of variables.

    #! /usr/bin/env python
    # coding: yupp

    ($__TITLE__ 0)

    ($import stdlib)

    ($dict INI
        (` TYPE     VAR       DEFAULT                   )
        (`
        (  int      step      0                         )
        (  string   greeting  'Hello! Improving Pi...'  )
        (  float    Pi        0.0                       )
        (  boolean  flag      True                      )
        (  string   date      (`time.strftime( '%c' ))  )
        )
    )

    import time
    from ConfigParser import ConfigParser

    FILE = ($'($0).ini' ($lower ($__MODULE_NAME__)))
    SEC = 'General'

    ($each-INI \i.]
        ini_($i VAR) = ($i DEFAULT)

    [ )

    def ini_load( fn ):
        ($each-INI \i.]
            global ini_($i VAR)

        [ )
        ini = ConfigParser()

        ini.read( fn )
        if ini.has_section( SEC ):
            ($each-INI \i.]
                ($set OPT ($qs ($i VAR)))
                ($set T (`) ? ($eq ($i TYPE),,string) | ($i TYPE))
                if ini.has_option( SEC, ($OPT) ):
                    ini_($i VAR) = ini.get($T)( SEC, ($OPT) )

            [ )

    def ini_save( fn ):
        ($each-INI \i.]
            global ini_($i VAR)

        [ )

        ini = ConfigParser()

        if not ini.has_section( SEC ):
            ini.add_section( SEC )

        ($each-INI \i.]
            ($set VR,,ini_($i VAR))
            ($set VAL VR ? ($eq ($i TYPE),,string) | [str( ($VR) )])
            ini.set( SEC, ($qs ($i VAR)), ($VAL) )

        [ )
        with open( fn, 'wb' ) as f:
            ini.write( f )

    if __name__ == '__main__':
        ini_load( FILE )

        # Calc Pi using Leibniz formula, add one term of the series
        ini_Pi += pow( -1, ini_step ) * 4.0 / ( ini_step * 2 + 1 )
        ini_step += 1

        ($each-INI \i.]
            print ($'($0) =',,ini_($i VAR)), ini_($i VAR)

        [ )
        ini_save( FILE )

The generated source code in Python:


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
