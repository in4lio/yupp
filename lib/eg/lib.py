def reversed_string( val ):
    return str( val )[ ::-1 ]

def define_upper_reversed( fn ):
    return r'($set %s \a.($upper ($reversed_string a)))' % ( fn )
