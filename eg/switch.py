#! /usr/bin/env python
# coding: yupp

($__TITLE__ 0)

from zlib import crc32

($! switch construction for strings based on CRC-32 )
($set crc32-switch \cond.\crc32-case..\crc32-default..\body.]
    _crc32 = crc32( ($cond) ) & 0xffffffff
    if False:
        pass
    ($body \crc32-case \val.]
    elif _crc32 == ($hex ($crc32 ($unq ($val)))):
    [ \crc32-default ]
    else:
    [ )
[ )

($! pattern matching )
($set pattern-switch \cond.\p-case..\body.]
    ($set p-val (`_pattern_value))
    while True:
        _pattern_value = ($cond)
        ($body \p-case \exp.]
            if ($exp):
        [ )
        break
[ )

def main():
    # -- CRC-32 switch for strings
    for val in ( 'Zero', 'One', 'Two', 'Three', 'Four', 'Five' ):
        print val,

        ($crc32-switch (`val) ]
            ($crc32-case 'One')
                print 1
            ($crc32-case 'Two')
                print 2
            ($crc32-case 'Three')
                print 3
            ($crc32-case 'Four')
                print 4
            ($crc32-case 'Five')
                print 5
            ($crc32-case 'Zero')
                print 0
            ($crc32-default)
                print '?'
        [ )

    # -- pattern matching
    for val in range( -2, 4 ):
        print val,

        ($pattern-switch (`val) ]
            ($p-case,,($p-val) < 0)
                print '< 0'
                # -- check the next condition

            ($p-case,,0 <= ($p-val) <= 2)
                print 'in [0..2]'
                # -- do not check the next condition
                break

            ($p-case,,($p-val) > 2)
                print '> 2'
        [ )

if __name__ == '__main__':
    main()
