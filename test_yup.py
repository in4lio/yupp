r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

test_yup.py -- testkit for yupp preprocessor
"""

from __future__ import division
import traceback
from yugen import *                                                                                                    #pylint: disable=wildcard-import,unused-wildcard-import

_TRACEBACK = True
_TRACE = TRACE_STAGE_NONE


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *          T E S T K I T          *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *
#   Structure of record:
#   -- trace storing (0 - none, 1 - yuparse, 2 - yueval, 3 - both)
#   -- source text of test
#   -- expected AST or exception
#   -- expected result text or exception

#   -----------------------------------
#   yuparse() testkit
#   -----------------------------------

t_parse_title = 'yuparse() testkit'
t_parse_kit = [(
                                                                                                                       #pylint: disable=line-too-long
#   ---- 01 -- PLAIN, APPLY, VAR, REMARK
TRACE_STAGE_NONE,

r"""
while( ($m::app) > 10 ) {
    /* cycle ($app) */
}
""",

TEXT([PLAIN('\nwhile( '), APPLY(VAR([ATOM('m')], ATOM('app')), [], []), PLAIN(' > 10 ) {\n    /* cycle '), APPLY(VAR([], ATOM('app')), [], []), PLAIN(' */\n}\n')], 0, 0),

""
),(
#   ---- 02 -- APPLY, SET, REMARK, COMMENT
TRACE_STAGE_NONE,

r"""
($set (a b c) (($e) 'hi!' ($q u)))($_123)/**/($set a 10 \set) // q...
($! Comment into the TEXT(). )
""",

TEXT([PLAIN('\n'), SET([ATOM('a'), ATOM('b'), ATOM('c')], LIST([APPLY(VAR([], ATOM('e')), [], []), STR("'hi!'"), APPLY(VAR([], ATOM('q')), [VAR([], ATOM('u'))], [])])), APPLY(VAR([], ATOM('_123')), [], []), PLAIN('/**/'), SET(ATOM('a'), INT(10L)), PLAIN(' // q...\n'), COMMENT(), PLAIN('\n')], 0, 0),

""
),(
#   ---- 03 -- region, named, LATE_BOUNDED
TRACE_STAGE_NONE,

r"""
// fn()!
($u1::u2::u3::fn \p1 par1 &par2 \p3 par3 \fn)
($fn2 \p1 a \b.(c) \p3 \d.\e.($d e) \fn2)
""",

TEXT([PLAIN('\n// fn()!\n'), APPLY(VAR([ATOM('u1'), ATOM('u2'), ATOM('u3')], ATOM('fn')), [VAR(LATE_BOUNDED(), ATOM('par2'))], [(ATOM('p1'), VAR([], ATOM('par1'))), (ATOM('p3'), VAR([], ATOM('par3')))]), PLAIN('\n'), APPLY(VAR([], ATOM('fn2')), [LAMBDA([([], ATOM('b'), None)], LIST([VAR([], ATOM('c'))]))], [(ATOM('p1'), VAR([], ATOM('a'))), (ATOM('p3'), LAMBDA([([], ATOM('d'), None), ([], ATOM('e'), None)], APPLY(VAR([], ATOM('d')), [VAR([], ATOM('e'))], [])))]), PLAIN('\n')], 0, 0),

""
),(
#   ---- 04 -- code, EMIT
TRACE_STAGE_NONE,

r"""
do {($fn \code ]
    abc( d ) + ($ee f) * 10
[[(gh[i[j]] == k)"]"]
($code l(m(n(o(')'))))) ]p["]]]"]\[\fn)} while( 1 )
($fn ]
// eol:)
\[)
($emit l)($emit l\n.(n)\emit)
""",

TEXT([PLAIN('\ndo {'), APPLY(VAR([], ATOM('fn')), [TEXT([PLAIN('(gh[i[j]] == k)'), STR('"]"')], 0, 0), TEXT([PLAIN(' l(m(n(o('), STR("')'"), PLAIN('))))')], 0, 0), TEXT([PLAIN('p['), STR('"]]]"'), PLAIN(']')], 0, 0)], [(ATOM('code'), TEXT([PLAIN('    abc( d ) + '), APPLY(VAR([], ATOM('ee')), [VAR([], ATOM('f'))], []), PLAIN(' * 10')], 0, 0))]), PLAIN('} while( 1 )\n'), APPLY(VAR([], ATOM('fn')), [TEXT([REMARK('// eol:)')], 0, 0)], []), PLAIN('\n'), EMIT(VAR([], ATOM('l')), None), EMIT(VAR([], ATOM('l')), LAMBDA([([], ATOM('n'), None)], LIST([VAR([], ATOM('n'))]))), PLAIN('\n')], 0, 0),

""
),(
#   ---- 05 -- LAMBDA
TRACE_STAGE_NONE,

r"""
($ \p.\pp1..\pp2..\pp:abc.\...\ppp1..\ppp.\pppp.($f p1) *(1 a b))
($set lst (pa pb pc))
($ \(lst).($f2))
""",

TEXT([PLAIN('\n'), APPLY(LAMBDA([([], ATOM('p'), None), ([ATOM('pp1'), ATOM('pp2')], ATOM('pp'), VAR([], ATOM('abc'))), ([], ATOM('...'), None), ([ATOM('ppp1')], ATOM('ppp'), None), ([], ATOM('pppp'), None)], APPLY(VAR([], ATOM('f')), [VAR([], ATOM('p1'))], [])), [EMBED(LIST([INT(1L), VAR([], ATOM('a')), VAR([], ATOM('b'))]))], []), PLAIN('\n'), SET(ATOM('lst'), LIST([VAR([], ATOM('pa')), VAR([], ATOM('pb')), VAR([], ATOM('pc'))])), PLAIN('\n'), APPLY(LAMBDA(VAR([], ATOM('lst')), APPLY(VAR([], ATOM('f2')), [], [])), [], []), PLAIN('\n')], 0, 0),

""
),(
#   ---- 06 -- LIST, INT, FLOAT, STR
TRACE_STAGE_NONE,

r"""
($l (-0.123 -48 077 "\\Hello \"world\"!\n" 3.14e-29 0xFF1 *a *() ($b) '\x000' '\'' '\n' \c.(d)))
""",

TEXT([PLAIN('\n'), APPLY(VAR([], ATOM('l')), [LIST([FLOAT(-0.123), INT(-48L), INT(63L), STR('"\\\\Hello \\"world\\"!\\n"'), FLOAT(3.14e-29), INT(4081L), EMBED(VAR([], ATOM('a'))), EMBED(LIST([])), APPLY(VAR([], ATOM('b')), [], []), STR("'\\x000'"), STR("'\\''"), STR("'\\n'"), LAMBDA([([], ATOM('c'), None)], LIST([VAR([], ATOM('d'))]))])], []), PLAIN('\n')], 0, 0),

""
),(
#   ---- 07 -- INFIX, STR, MACRO, EVAL ($$)
TRACE_STAGE_NONE,

r"""
($z {pi + e/2 - ($w) + len("hi{!}")} ($quoteHello()))
($macro m1 (a b) ($add a b))
($macro m2 () ]printf("Hello %s!", "Nike");[/*HACK:]*/)
($$ "(${f} {0} {1})" 2 3 \f sub)
($$ a "yes" "no")
""",

TEXT([PLAIN('\n'), APPLY(VAR([], ATOM('z')), [INFIX(TEXT([PLAIN('pi + e/2 - '), APPLY(VAR([], ATOM('w')), [], []), PLAIN(' + len('), STR('"hi{!}"'), PLAIN(')')], 0, 0)), STR('Hello()')], []), PLAIN('\n'), MACRO(ATOM('m1'), [ATOM('a'), ATOM('b')], ' ($add a b)'), PLAIN('\n'), MACRO(ATOM('m2'), [], ' ]printf("Hello %s!", "Nike");[/*HACK:]*/'), PLAIN('\n'), EVAL(APPLY(STR('"(${f} {0} {1})"'), [INT(2L), INT(3L)], [(ATOM('f'), VAR([], ATOM('sub')))])), PLAIN('\n'), EVAL(APPLY(VAR([], ATOM('a')), [STR('"yes"'), STR('"no"')], [])), PLAIN('\n')], 0, 0),

""
),(
#   ---- 08 -- COND
TRACE_STAGE_NONE,

r"""
($f 1L ? c | 2 ($e) ?(2) d ?($f) | dd?1 | ddd ?'2' | dddd)
""",

TEXT([PLAIN('\n'), APPLY(VAR([], ATOM('f')), [COND(VAR([], ATOM('c')), INT(1L), INT(2L)), COND(LIST([INT(2L)]), APPLY(VAR([], ATOM('e')), [], []), None), COND(APPLY(VAR([], ATOM('f')), [], []), VAR([], ATOM('d')), COND(INT(1L), VAR([], ATOM('dd')), COND(STR("'2'"), VAR([], ATOM('ddd')), VAR([], ATOM('dddd')))))], []), PLAIN('\n')], 0, 0),

""
)]

#   -----------------------------------
#   yueval() testkit
#   -----------------------------------

t_eval_title = 'yueval() testkit'
t_eval_kit = [(
                                                                                                                       #pylint: disable=line-too-long
#   ---- 01 -- PLAIN
TRACE_STAGE_NONE,

r"""
/*  Hello world! */
int main()
{
    // Entry point...
    printf( "Hello world!" );

    return 1;
}
""",

TEXT([PLAIN('\n/*  Hello world! */\nint main()\n{\n    // Entry point...\n    printf( '), STR('"Hello world!"'), PLAIN(' );\n\n    return 1;\n}\n')], 0, 0),

r"""
/*  Hello world! */
int main()
{
    // Entry point...
    printf( "Hello world!" );

    return 1;
}
"""
),(
#   ---- 02 -- APPLY, BUILTIN, code, __va_args__
TRACE_STAGE_NONE,

r"""
($print ]($e) 100.0 ($len "We all live in a yellow submarine,")
\[)
($print ($add 2 2) '*' ($mul 2 2) '=' ($mul ($add 2 2) ($mul 2 2)) '\n' yellow submarine '\n')
($q ($reversed ($unq "\n!dlrow olleH")))
($ \p1.\p2.\p3.($add ($add p1 p2) p3) 1L 2 *( 3 4 5 ) 6 7l *(8 9 10 11 12 13 14 15))
($ \f.\a.($f a) exp ($e))
($ \a.($ \p1.\p2.\p3.($add ($add p1 p2) p3) *a) ( 100 10 1 ))
($ \a.\...($($lazy __va_args__) \f.($f a)) 9 \n.($sqrt n) \n.[ ($n) ] \n.($pow n 2))
($join (,,(1),2,,3,(4),,5,6;;($zfill,,7;;3)) ,,,)
($macro m (c) ($replace,,($c),,2,,_))
($m,,1234256722)
// '12345'[ ::-1 ]
($getslice (`12345) (`) (`) -1)
""",

TEXT([PLAIN('\n'), APPLY(VAR([], ATOM('print')), [TEXT([APPLY(VAR([], ATOM('e')), [], []), PLAIN(' 100.0 '), APPLY(VAR([], ATOM('len')), [STR('"We all live in a yellow submarine,"')], []), PLAIN('\n')], 0, 0)], []), PLAIN('\n'), APPLY(VAR([], ATOM('print')), [APPLY(VAR([], ATOM('add')), [INT(2L), INT(2L)], []), STR("'*'"), APPLY(VAR([], ATOM('mul')), [INT(2L), INT(2L)], []), STR("'='"), APPLY(VAR([], ATOM('mul')), [APPLY(VAR([], ATOM('add')), [INT(2L), INT(2L)], []), APPLY(VAR([], ATOM('mul')), [INT(2L), INT(2L)], [])], []), STR("'\\n'"), VAR([], ATOM('yellow')), VAR([], ATOM('submarine')), STR("'\\n'")], []), PLAIN('\n'), APPLY(VAR([], ATOM('q')), [APPLY(VAR([], ATOM('reversed')), [APPLY(VAR([], ATOM('unq')), [STR('"\\n!dlrow olleH"')], [])], [])], []), PLAIN('\n'), APPLY(LAMBDA([([], ATOM('p1'), None), ([], ATOM('p2'), None), ([], ATOM('p3'), None)], APPLY(VAR([], ATOM('add')), [APPLY(VAR([], ATOM('add')), [VAR([], ATOM('p1')), VAR([], ATOM('p2'))], []), VAR([], ATOM('p3'))], [])), [INT(1L), INT(2L), EMBED(LIST([INT(3L), INT(4L), INT(5L)])), INT(6L), INT(7L), EMBED(LIST([INT(8L), INT(9L), INT(10L), INT(11L), INT(12L), INT(13L), INT(14L), INT(15L)]))], []), PLAIN('\n'), APPLY(LAMBDA([([], ATOM('f'), None), ([], ATOM('a'), None)], APPLY(VAR([], ATOM('f')), [VAR([], ATOM('a'))], [])), [VAR([], ATOM('exp')), APPLY(VAR([], ATOM('e')), [], [])], []), PLAIN('\n'), APPLY(LAMBDA([([], ATOM('a'), None)], APPLY(LAMBDA([([], ATOM('p1'), None), ([], ATOM('p2'), None), ([], ATOM('p3'), None)], APPLY(VAR([], ATOM('add')), [APPLY(VAR([], ATOM('add')), [VAR([], ATOM('p1')), VAR([], ATOM('p2'))], []), VAR([], ATOM('p3'))], [])), [EMBED(VAR([], ATOM('a')))], [])), [LIST([INT(100L), INT(10L), INT(1L)])], []), PLAIN('\n'), APPLY(LAMBDA([([], ATOM('a'), None), ([], ATOM('...'), None)], APPLY(APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], []), [LAMBDA([([], ATOM('f'), None)], APPLY(VAR([], ATOM('f')), [VAR([], ATOM('a'))], []))], [])), [INT(9L), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('sqrt')), [VAR([], ATOM('n'))], [])), LAMBDA([([], ATOM('n'), None)], TEXT([PLAIN(' '), APPLY(VAR([], ATOM('n')), [], []), PLAIN(' ')], 0, 0)), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('pow')), [VAR([], ATOM('n')), INT(2L)], []))], []), PLAIN('\n'), APPLY(VAR([], ATOM('join')), [LIST([TEXT([PLAIN('(1),2')], 0, 0), TEXT([PLAIN('3,(4)')], 0, 0), TEXT([PLAIN('5,6')], 0, 0), APPLY(VAR([], ATOM('zfill')), [TEXT([PLAIN('7')], 0, 0), INT(3L)], [])]), TEXT([PLAIN(',')], 0, 0)], []), PLAIN('\n'), MACRO(ATOM('m'), [ATOM('c')], ' ($replace,,($c),,2,,_)'), PLAIN('\n'), APPLY(VAR([], ATOM('m')), [TEXT([PLAIN('1234256722')], 0, 0)], []), PLAIN('\n// '), STR("'12345'"), PLAIN('[ ::-1 ]\n'), APPLY(VAR([], ATOM('getslice')), [STR('12345'), STR(''), STR(''), INT(-1L)], []), PLAIN('\n')], 0, 0),

r"""
"Hello world!\n"
10
15.1542622415
111
3.0 9 81.0
(1),2,3,(4),5,6,007
1_34_567__
// '12345'[ ::-1 ]
54321
"""
),(
#   ---- 03 -- SET, indent
TRACE_STAGE_NONE,

r"""
($set greeting (`\n!dlrow olleH))
($q ($reversed ($unq greeting)))
($set a 222)
($set (b c d) ($e))
($set (e f g h i j) (1 2 3 4 5L))
($a) ($b) ($c) ($d) ($e) ($f) ($g) ($h) ($i)($j)
($set k 10)($set mult \i.($mul k i))($set l 3)
($list k ($mult 2) ($mult l ))
0
($!)($!)($!)
1
($set a 1)($set b 2)
2
($!) ($!)   ($!)
3
($set a 1)  ($set b 2)
4
5($!)
6($set a 1)
7($!)($!) ($!)
8($set a 1)($set b 2) ($set c 3)
($!)9 ($!)
($set a 1) ($set b 2)A($set c 3)
""",

TEXT([PLAIN('\n'), SET(ATOM('greeting'), STR('\\n!dlrow olleH')), PLAIN('\n'), APPLY(VAR([], ATOM('q')), [APPLY(VAR([], ATOM('reversed')), [APPLY(VAR([], ATOM('unq')), [VAR([], ATOM('greeting'))], [])], [])], []), PLAIN('\n'), SET(ATOM('a'), INT(222L)), PLAIN('\n'), SET([ATOM('b'), ATOM('c'), ATOM('d')], APPLY(VAR([], ATOM('e')), [], [])), PLAIN('\n'), SET([ATOM('e'), ATOM('f'), ATOM('g'), ATOM('h'), ATOM('i'), ATOM('j')], LIST([INT(1L), INT(2L), INT(3L), INT(4L), INT(5L)])), PLAIN('\n'), APPLY(VAR([], ATOM('a')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('b')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('c')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('d')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('e')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('f')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('g')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('h')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('i')), [], []), APPLY(VAR([], ATOM('j')), [], []), PLAIN('\n'), SET(ATOM('k'), INT(10L)), SET(ATOM('mult'), LAMBDA([([], ATOM('i'), None)], APPLY(VAR([], ATOM('mul')), [VAR([], ATOM('k')), VAR([], ATOM('i'))], []))), SET(ATOM('l'), INT(3L)), PLAIN('\n'), APPLY(VAR([], ATOM('list')), [VAR([], ATOM('k')), APPLY(VAR([], ATOM('mult')), [INT(2L)], []), APPLY(VAR([], ATOM('mult')), [VAR([], ATOM('l'))], [])], []), PLAIN('\n0\n'), COMMENT(), COMMENT(), COMMENT(), PLAIN('\n1\n'), SET(ATOM('a'), INT(1L)), SET(ATOM('b'), INT(2L)), PLAIN('\n2\n'), COMMENT(), PLAIN(' '), COMMENT(), PLAIN('   '), COMMENT(), PLAIN('\n3\n'), SET(ATOM('a'), INT(1L)), PLAIN('  '), SET(ATOM('b'), INT(2L)), PLAIN('\n4\n5'), COMMENT(), PLAIN('\n6'), SET(ATOM('a'), INT(1L)), PLAIN('\n7'), COMMENT(), COMMENT(), PLAIN(' '), COMMENT(), PLAIN('\n8'), SET(ATOM('a'), INT(1L)), SET(ATOM('b'), INT(2L)), PLAIN(' '), SET(ATOM('c'), INT(3L)), PLAIN('\n'), COMMENT(), PLAIN('9 '), COMMENT(), PLAIN('\n'), SET(ATOM('a'), INT(1L)), PLAIN(' '), SET(ATOM('b'), INT(2L)), PLAIN('A'), SET(ATOM('c'), INT(3L)), PLAIN('\n')], 0, 0),

r"""
"Hello world!\n"
222 2.71828182846 2.71828182846 2.71828182846 1 2 3 4 5
102030
0
1
2
3
4
5
6
7
8
9
A
"""
),(
#   ---- 04 -- LATE_BOUNDED, EMIT, parameters from list
TRACE_STAGE_NONE,

r"""
($set k 10)($set app \p1..\p2..\f.\i.($f k i))($set l 3)
($list k ($app \f ($mul &p1 &p2) 2) ($app \f ($mul &p1 &p2) l ))
($set l ("A" "B" "C"))
($set a 5)
($emit l), ($emit l \r.($r \s.($lower s))), ($emit l), ($emit l)
($emit a \n.{ n + 1 }), ($emit a \n.($q n)), ($emit a)
($set q 3)
($set add2 \n.($add n 2))
(${}($emit q add2)+($emit q add2)+($emit q add2)+($emit q add2))
($set p (c d))
($ \(p).{c - d} 100 500)
($set p (d c))
($ \(p).{c - d} 100 500)
""",

TEXT([PLAIN('\n'), SET(ATOM('k'), INT(10L)), SET(ATOM('app'), LAMBDA([([ATOM('p1'), ATOM('p2')], ATOM('f'), None), ([], ATOM('i'), None)], APPLY(VAR([], ATOM('f')), [VAR([], ATOM('k')), VAR([], ATOM('i'))], []))), SET(ATOM('l'), INT(3L)), PLAIN('\n'), APPLY(VAR([], ATOM('list')), [VAR([], ATOM('k')), APPLY(VAR([], ATOM('app')), [INT(2L)], [(ATOM('f'), APPLY(VAR([], ATOM('mul')), [VAR(LATE_BOUNDED(), ATOM('p1')), VAR(LATE_BOUNDED(), ATOM('p2'))], []))]), APPLY(VAR([], ATOM('app')), [VAR([], ATOM('l'))], [(ATOM('f'), APPLY(VAR([], ATOM('mul')), [VAR(LATE_BOUNDED(), ATOM('p1')), VAR(LATE_BOUNDED(), ATOM('p2'))], []))])], []), PLAIN('\n'), SET(ATOM('l'), LIST([STR('"A"'), STR('"B"'), STR('"C"')])), PLAIN('\n'), SET(ATOM('a'), INT(5L)), PLAIN('\n'), EMIT(VAR([], ATOM('l')), None), PLAIN(', '), EMIT(VAR([], ATOM('l')), LAMBDA([([], ATOM('r'), None)], APPLY(VAR([], ATOM('r')), [LAMBDA([([], ATOM('s'), None)], APPLY(VAR([], ATOM('lower')), [VAR([], ATOM('s'))], []))], []))), PLAIN(', '), EMIT(VAR([], ATOM('l')), None), PLAIN(', '), EMIT(VAR([], ATOM('l')), None), PLAIN('\n'), EMIT(VAR([], ATOM('a')), LAMBDA([([], ATOM('n'), None)], INFIX(TEXT([PLAIN(' n + 1 ')], 0, 0)))), PLAIN(', '), EMIT(VAR([], ATOM('a')), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('q')), [VAR([], ATOM('n'))], []))), PLAIN(', '), EMIT(VAR([], ATOM('a')), None), PLAIN('\n'), SET(ATOM('q'), INT(3L)), PLAIN('\n'), SET(ATOM('add2'), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('add')), [VAR([], ATOM('n')), INT(2L)], []))), PLAIN('\n'), INFIX(TEXT([EMIT(VAR([], ATOM('q')), VAR([], ATOM('add2'))), PLAIN('+'), EMIT(VAR([], ATOM('q')), VAR([], ATOM('add2'))), PLAIN('+'), EMIT(VAR([], ATOM('q')), VAR([], ATOM('add2'))), PLAIN('+'), EMIT(VAR([], ATOM('q')), VAR([], ATOM('add2')))], 0, 0)), PLAIN('\n'), SET(ATOM('p'), LIST([VAR([], ATOM('c')), VAR([], ATOM('d'))])), PLAIN('\n'), APPLY(LAMBDA(VAR([], ATOM('p')), INFIX(TEXT([PLAIN('c - d')], 0, 0))), [INT(100L), INT(500L)], []), PLAIN('\n'), SET(ATOM('p'), LIST([VAR([], ATOM('d')), VAR([], ATOM('c'))])), PLAIN('\n'), APPLY(LAMBDA(VAR([], ATOM('p')), INFIX(TEXT([PLAIN('c - d')], 0, 0))), [INT(100L), INT(500L)], []), PLAIN('\n')], 0, 0),

r"""
102030
"A", "B", "c",
5, 6, "6"
24
-400
400
"""
),(
#   ---- 05 -- LATE_BOUNDED (variable argument list)
TRACE_STAGE_NONE,

r"""
($set def-fn-argv \type.\name.\type..\arg-begin..\arg-count..\arg-value..\arg-end..\body.]
($type) ($name)( int argcnt, ... )
{
    ($body \type type \arg-begin ]
        va_list argptr;
        va_start( argptr, argcnt );
    [\arg-count ]
        argcnt
    [\arg-value \type.]
        va_arg( argptr, ($type) )
    [\arg-end ]
        va_end( argptr );
    \[\body )
}
[\set )

($def-fn-argv \type int \name sumi ]
    int result = 0;
    ($ &arg-begin)
    while ( ($ &arg-count)-- ) result += ($ &arg-value &type);
    ($ &arg-end)
    return ( result );
\[\def-fn-argv )
""",

TEXT([PLAIN('\n'), SET(ATOM('def-fn-argv'), LAMBDA([([], ATOM('type'), None), ([], ATOM('name'), None), ([ATOM('type'), ATOM('arg-begin'), ATOM('arg-count'), ATOM('arg-value'), ATOM('arg-end')], ATOM('body'), None)], TEXT([APPLY(VAR([], ATOM('type')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('name')), [], []), PLAIN('( int argcnt, ... )\n{\n    '), APPLY(VAR([], ATOM('body')), [], [(ATOM('type'), VAR([], ATOM('type'))), (ATOM('arg-begin'), TEXT([PLAIN('        va_list argptr;\n        va_start( argptr, argcnt );')], 0, 0)), (ATOM('arg-count'), TEXT([PLAIN('        argcnt')], 0, 0)), (ATOM('arg-value'), LAMBDA([([], ATOM('type'), None)], TEXT([PLAIN('        va_arg( argptr, '), APPLY(VAR([], ATOM('type')), [], []), PLAIN(' )')], 0, 0))), (ATOM('arg-end'), TEXT([PLAIN('        va_end( argptr );')], 0, 0))]), PLAIN('\n}')], 0, 0))), PLAIN('\n\n'), APPLY(VAR([], ATOM('def-fn-argv')), [TEXT([PLAIN('    int result = 0;\n    '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-begin')), [], []), PLAIN('\n    while ( '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-count')), [], []), PLAIN('-- ) result += '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-value')), [VAR(LATE_BOUNDED(), ATOM('type'))], []), PLAIN(';\n    '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-end')), [], []), PLAIN('\n    return ( result );')], 0, 0)], [(ATOM('type'), VAR([], ATOM('int'))), (ATOM('name'), VAR([], ATOM('sumi')))]), PLAIN('\n')], 0, 0),

r"""
int sumi( int argcnt, ... )
{
    int result = 0;
    va_list argptr;
    va_start( argptr, argcnt );
    while ( argcnt-- ) result += va_arg( argptr, int );
    va_end( argptr );
    return ( result );
}
"""
),(
#   ---- 06 -- MACRO, indent
TRACE_STAGE_NONE,

r"""
($macro m (a b)($add ($a) ($b)))
($set a \b.($m 1 b))
($a 2)
($macro m1 ()"C, forever!")
($m1)
($macro m2 (m a)($($m) ($a) (b)($($m) ($b) (c)($($m) ($c) ()Yes!))))
($m2 macro new_m2)
($new_m2 new_new_m2)
($new_new_m2 new_new_new_m2)
($new_new_new_m2)
($set n 22)
($"($p1)+($0)+($1)+($2)=($p0)" +1 +2 +4 \p1 15 \p0 n)
($set s '($sub ($n1) ($n2))')
($$s \n1 10 \n2 2)
($$"($add 2 2)")
($macro a (){
    ($set b 5)
    ($b),
})
{
    {
        ($a)
    }
}
""",

TEXT([PLAIN('\n'), MACRO(ATOM('m'), [ATOM('a'), ATOM('b')], '($add ($a) ($b))'), PLAIN('\n'), SET(ATOM('a'), LAMBDA([([], ATOM('b'), None)], APPLY(VAR([], ATOM('m')), [INT(1L), VAR([], ATOM('b'))], []))), PLAIN('\n'), APPLY(VAR([], ATOM('a')), [INT(2L)], []), PLAIN('\n'), MACRO(ATOM('m1'), [], '"C, forever!"'), PLAIN('\n'), APPLY(VAR([], ATOM('m1')), [], []), PLAIN('\n'), MACRO(ATOM('m2'), [ATOM('m'), ATOM('a')], '($($m) ($a) (b)($($m) ($b) (c)($($m) ($c) ()Yes!)))'), PLAIN('\n'), APPLY(VAR([], ATOM('m2')), [VAR([], ATOM('macro')), VAR([], ATOM('new_m2'))], []), PLAIN('\n'), APPLY(VAR([], ATOM('new_m2')), [VAR([], ATOM('new_new_m2'))], []), PLAIN('\n'), APPLY(VAR([], ATOM('new_new_m2')), [VAR([], ATOM('new_new_new_m2'))], []), PLAIN('\n'), APPLY(VAR([], ATOM('new_new_new_m2')), [], []), PLAIN('\n'), SET(ATOM('n'), INT(22L)), PLAIN('\n'), APPLY(STR('"($p1)+($0)+($1)+($2)=($p0)"'), [INT(1L), INT(2L), INT(4L)], [(ATOM('p1'), INT(15L)), (ATOM('p0'), VAR([], ATOM('n')))]), PLAIN('\n'), SET(ATOM('s'), STR("'($sub ($n1) ($n2))'")), PLAIN('\n'), EVAL(APPLY(VAR([], ATOM('s')), [], [(ATOM('n1'), INT(10L)), (ATOM('n2'), INT(2L))])), PLAIN('\n'), EVAL(APPLY(STR('"($add 2 2)"'), [], [])), PLAIN('\n'), MACRO(ATOM('a'), [], '{\n    ($set b 5)\n    ($b),\n}'), PLAIN('\n{\n    {\n        '), APPLY(VAR([], ATOM('a')), [], []), PLAIN('\n    }\n}\n')], 0, 0),

r"""
3
"C, forever!"
Yes!
"15+1+2+4=22"
8
4
{
    {
        {
            5,
        }
    }
}
"""
),(
#   ---- 07 -- yummy C preprocessor)))
TRACE_STAGE_NONE,

r"""
($($\y:u.\m.\...(m y($\C.\p.(r)e p)($\ro.(ce)s)))so r)
""",

TEXT([PLAIN('\n'), APPLY(APPLY(LAMBDA([([], ATOM('y'), VAR([], ATOM('u'))), ([], ATOM('m'), None), ([], ATOM('...'), None)], LIST([VAR([], ATOM('m')), VAR([], ATOM('y')), APPLY(LAMBDA([([], ATOM('C'), None), ([], ATOM('p'), None)], LIST([VAR([], ATOM('r'))])), [VAR([], ATOM('e')), VAR([], ATOM('p'))], []), APPLY(LAMBDA([([], ATOM('ro'), None)], LIST([VAR([], ATOM('ce'))])), [VAR([], ATOM('s'))], [])])), [], []), [VAR([], ATOM('so')), VAR([], ATOM('r'))], []), PLAIN('\n')], 0, 0),

r"""
source
"""
),(
#   ---- 08 -- IMPORT (equals to test 5)
TRACE_STAGE_NONE,

r"""
($import "eg/lib.py")
($import { define_upper_reversed( 'uprevst' ) })
#define ($uprevst hello)
($import "stdlib.yu")
($def-fn-argv \type int \name sumi ]
    int result = 0;
    ($ &arg-begin)
    while ( ($ &arg-count)-- ) result += ($ &arg-value &type);
    ($ &arg-end)
    return ( result );
\[\def-fn-argv )
""",

TEXT([PLAIN('\n'), PLAIN('\n'), SET(ATOM('uprevst'), LAMBDA([([], ATOM('a'), None)], APPLY(VAR([], ATOM('upper')), [APPLY(VAR([], ATOM('reversed_string')), [VAR([], ATOM('a'))], [])], []))), PLAIN('\n#define '), APPLY(VAR([], ATOM('uprevst')), [VAR([], ATOM('hello'))], []), PLAIN('\n'), IMPORT_BEGIN(), COMMENT(), PLAIN('\n'), MACRO(ATOM('dict'), [ATOM('id'), ATOM('cols'), ATOM('body')], '\n\t($set cols-($id) ($range ($len (($cols)) )))\n\t($set each-($id) ($range ($len (($body)) )))\n\t($set (($cols))\n\t\t($cols-($id) \\__i.($ (($body)) \\__var.($__i __var)))\n\t)\n'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('if'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('then')), VAR([], ATOM('else'))), [], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('unless'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('else')), VAR([], ATOM('then'))), [], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('unfold'), LAMBDA([([], ATOM('count'), None), ([], ATOM('...'), None)], LET([ATOM('__last'), ATOM('__func')], LIST([APPLY(VAR([], ATOM('sub')), [APPLY(VAR([], ATOM('len')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], []), INT(1L)], []), APPLY(VAR([], ATOM('__last')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], [])]), APPLY(APPLY(VAR([], ATOM('range')), [VAR([], ATOM('count'))], []), [LAMBDA([([], ATOM('__i'), None)], APPLY(VAR([], ATOM('if')), [INFIX(TEXT([PLAIN(' __i < __last ')], 0, 0)), APPLY(VAR([], ATOM('__i')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], []), APPLY(VAR([], ATOM('__func')), [VAR([], ATOM('__i'))], [])], []))], [])))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('do'), [ATOM('body')], 'do {\n($body)\n} while ( 0 )'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('foo'), [ATOM('body')], '({\n($body)\n})'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('__EOL__'), COND(APPLY(VAR([], ATOM('not')), [APPLY(VAR([], ATOM('isatom')), [VAR([], ATOM('EOL'))], [])], []), VAR([], ATOM('EOL')), TEXT([PLAIN('\n')], 0, 0))), PLAIN('\n'), SET(ATOM('define'), LAMBDA([([], ATOM('sig'), None), ([], ATOM('body'), None)], APPLY(VAR([], ATOM('join')), [APPLY(VAR([], ATOM('split')), [TEXT([APPLY(VAR([], ATOM('unq')), [STR('"#define"')], []), PLAIN(' '), APPLY(VAR([], ATOM('sig')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('body')), [], [])], 0, 0), VAR([], ATOM('__EOL__'))], []), TEXT([PLAIN(' \\'), APPLY(VAR([], ATOM('__EOL__')), [], [])], 0, 0)], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('def'), [ATOM('name')], '($set ($name) 1)\n($unq "#define") ($name)'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('undef'), [ATOM('name')], '($set ($name) 0)\n($unq "#undef")  ($name)'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('def-if'), [ATOM('cond'), ATOM('name')], '($set ($name) 1 ? ($cond) | 0)\n($if ($name) [($unq "#define") ($name)])'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('skip-if'), [ATOM('cond')], '($if ($cond) ($skip))'), PLAIN('\n'), MACRO(ATOM('skip-if-not'), [ATOM('cond')], '($if ($not ($cond)) ($skip))'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('BIN'), LAMBDA([([], ATOM('b'), None)], APPLY(VAR([], ATOM('atoi')), [VAR([], ATOM('b')), INT(2L)], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('BB'), LAMBDA([([], ATOM('...'), None)], APPLY(VAR([], ATOM('sum')), [APPLY(APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('__va_args__'))], [])], []), [LAMBDA([([], ATOM('__i'), None)], INFIX(TEXT([PLAIN(' '), APPLY(VAR([], ATOM('BIN')), [APPLY(VAR([], ATOM('__i')), [APPLY(VAR([], ATOM('reversed')), [VAR([], ATOM('__va_args__'))], [])], [])], []), PLAIN(' << '), APPLY(VAR([], ATOM('__i')), [], []), PLAIN(' * 8 ')], 0, 0)))], [])], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('def-fn-argv'), LAMBDA([([], ATOM('type'), None), ([], ATOM('name'), None), ([ATOM('type'), ATOM('arg-begin'), ATOM('arg-count'), ATOM('arg-value'), ATOM('arg-end')], ATOM('body'), None)], TEXT([APPLY(VAR([], ATOM('type')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('name')), [], []), PLAIN('( int argcnt, ... )\n{\n\t'), APPLY(VAR([], ATOM('body')), [], [(ATOM('type'), VAR([], ATOM('type'))), (ATOM('arg-begin'), TEXT([PLAIN('\t\tva_list argptr;\n\t\tva_start( argptr, argcnt );')], 0, 0)), (ATOM('arg-count'), TEXT([PLAIN('\t\targcnt')], 0, 0)), (ATOM('arg-value'), LAMBDA([([], ATOM('type'), None)], TEXT([PLAIN('\t\tva_arg( argptr, '), APPLY(VAR([], ATOM('type')), [], []), PLAIN(' )')], 0, 0))), (ATOM('arg-end'), TEXT([PLAIN('\t\tva_end( argptr );')], 0, 0))]), PLAIN('\n}')], 0, 0))), PLAIN('\n\n'), SET(ATOM('INT_MAX'), INFIX(TEXT([PLAIN(' sys.maxint ')], 0, 0))), PLAIN('\n\n'), SET(ATOM('INT_MIN'), INFIX(TEXT([PLAIN(' -sys.maxint - 1 ')], 0, 0))), PLAIN('\n'), IMPORT_END(), PLAIN('\n'), APPLY(VAR([], ATOM('def-fn-argv')), [TEXT([PLAIN('    int result = 0;\n    '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-begin')), [], []), PLAIN('\n    while ( '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-count')), [], []), PLAIN('-- ) result += '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-value')), [VAR(LATE_BOUNDED(), ATOM('type'))], []), PLAIN(';\n    '), APPLY(VAR(LATE_BOUNDED(), ATOM('arg-end')), [], []), PLAIN('\n    return ( result );')], 0, 0)], [(ATOM('type'), VAR([], ATOM('int'))), (ATOM('name'), VAR([], ATOM('sumi')))]), PLAIN('\n')], 0, 0),

r"""
#define OLLEH

int sumi( int argcnt, ... )
{
	int result = 0;
	va_list argptr;
	va_start( argptr, argcnt );
	while ( argcnt-- ) result += va_arg( argptr, int );
	va_end( argptr );
	return ( result );
}
"""
),(
#   ---- 09 -- COND, recursion, indent
TRACE_STAGE_NONE,

r"""
($add ? 0 | sub 10 ? 1 | 5 0 ? 0 | 3)
($set if \cond.\then:[].\else:[].($ then ? cond | else))
($if ($eq 1 1) \then 'True' \else 'False')
($if ($eq 0 1) 'True' 'False')
($if 1 'True')
($if 0 \else 'False')
($if { 2 + 2 != 2 * 2 } 'True' 'F')
($set q 10)
($if ($eq q 0) 'Zero' q)
($set fact \n.($if ($eq n 0) 1 ($mul ($fact ($sub n 1)) n)))
($fact 0)
($fact 12)
($set fact \n.($ 1 ?($eq n 0) | ($mul ($fact ($sub n 1)) n)))
($fact 33) //max is ~1200
    ($set f \n.($if ($eq n 0) "0000" "BAD"))
    ($f 0)
        ($f 10)
    ($f 0)
        ($f 20)
    // macro
    ($macro if (cond then else) ($ ($then) ? ($cond) | ($else)))
    ($set f \n.($if ($eq n 0) "0000" "BAD"))
    ($f 0)
        ($f "a")
    ($f 0)
        ($f 20)
($set f \c.\a.\b.($ ($range c) \i.($b ? i | a)))
($ \n.($f n A B) 3)
""",

TEXT([PLAIN('\n'), APPLY(COND(INT(0L), VAR([], ATOM('add')), VAR([], ATOM('sub'))), [COND(INT(1L), INT(10L), INT(5L)), COND(INT(0L), INT(0L), INT(3L))], []), PLAIN('\n'), SET(ATOM('if'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('then')), VAR([], ATOM('else'))), [], []))), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [INT(1L), INT(1L)], [])], [(ATOM('then'), STR("'True'")), (ATOM('else'), STR("'False'"))]), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [INT(0L), INT(1L)], []), STR("'True'"), STR("'False'")], []), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [INT(1L), STR("'True'")], []), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [INT(0L)], [(ATOM('else'), STR("'False'"))]), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [INFIX(TEXT([PLAIN(' 2 + 2 != 2 * 2 ')], 0, 0)), STR("'True'"), STR("'F'")], []), PLAIN('\n'), SET(ATOM('q'), INT(10L)), PLAIN('\n'), APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [VAR([], ATOM('q')), INT(0L)], []), STR("'Zero'"), VAR([], ATOM('q'))], []), PLAIN('\n'), SET(ATOM('fact'), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [VAR([], ATOM('n')), INT(0L)], []), INT(1L), APPLY(VAR([], ATOM('mul')), [APPLY(VAR([], ATOM('fact')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(1L)], [])], []), VAR([], ATOM('n'))], [])], []))), PLAIN('\n'), APPLY(VAR([], ATOM('fact')), [INT(0L)], []), PLAIN('\n'), APPLY(VAR([], ATOM('fact')), [INT(12L)], []), PLAIN('\n'), SET(ATOM('fact'), LAMBDA([([], ATOM('n'), None)], APPLY(COND(APPLY(VAR([], ATOM('eq')), [VAR([], ATOM('n')), INT(0L)], []), INT(1L), APPLY(VAR([], ATOM('mul')), [APPLY(VAR([], ATOM('fact')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(1L)], [])], []), VAR([], ATOM('n'))], [])), [], []))), PLAIN('\n'), APPLY(VAR([], ATOM('fact')), [INT(33L)], []), PLAIN(' //max is ~1200\n    '), SET(ATOM('f'), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [VAR([], ATOM('n')), INT(0L)], []), STR('"0000"'), STR('"BAD"')], []))), PLAIN('\n    '), APPLY(VAR([], ATOM('f')), [INT(0L)], []), PLAIN('\n        '), APPLY(VAR([], ATOM('f')), [INT(10L)], []), PLAIN('\n    '), APPLY(VAR([], ATOM('f')), [INT(0L)], []), PLAIN('\n        '), APPLY(VAR([], ATOM('f')), [INT(20L)], []), PLAIN('\n    // macro\n    '), MACRO(ATOM('if'), [ATOM('cond'), ATOM('then'), ATOM('else')], ' ($ ($then) ? ($cond) | ($else))'), PLAIN('\n    '), SET(ATOM('f'), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('eq')), [VAR([], ATOM('n')), INT(0L)], []), STR('"0000"'), STR('"BAD"')], []))), PLAIN('\n    '), APPLY(VAR([], ATOM('f')), [INT(0L)], []), PLAIN('\n        '), APPLY(VAR([], ATOM('f')), [STR('"a"')], []), PLAIN('\n    '), APPLY(VAR([], ATOM('f')), [INT(0L)], []), PLAIN('\n        '), APPLY(VAR([], ATOM('f')), [INT(20L)], []), PLAIN('\n'), SET(ATOM('f'), LAMBDA([([], ATOM('c'), None), ([], ATOM('a'), None), ([], ATOM('b'), None)], APPLY(APPLY(VAR([], ATOM('range')), [VAR([], ATOM('c'))], []), [LAMBDA([([], ATOM('i'), None)], APPLY(COND(VAR([], ATOM('i')), VAR([], ATOM('b')), VAR([], ATOM('a'))), [], []))], []))), PLAIN('\n'), APPLY(LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('f')), [VAR([], ATOM('n')), VAR([], ATOM('A')), VAR([], ATOM('B'))], [])), [INT(3L)], []), PLAIN('\n')], 0, 0),

r"""
7
'True'
'False'
'True'
'False'
'F'
10
1
479001600
8683317618811886495518194401280000000 //max is ~1200
    "0000"
        "BAD"
    "0000"
        "BAD"
    // macro
    "0000"
        "BAD"
    "0000"
        "BAD"
ABB
"""
),(
#   ---- 10 -- INFIX, recursion
TRACE_STAGE_NONE,

r"""
($set fib1 \n.($n ? ($lt n 2) | ($add ($fib1 ($sub n 1)) ($fib1 ($sub n 2)))))
($set if \cond.\then:[].\else:[].($ then ? cond | else))
($set fib \n.($if ($lt n 2) n ($add ($fib ($sub n 1)) ($fib ($sub n 2)))))
($set fib2 \n.($n ? { n < 2 } | {($fib2 { n - 1 }) + ($fib2 { n - 2 })}))
($fib 10)
($fib1 10)
($ {($fib2 1) + ($fib2 2) + ($fib2 3) - ($fib2 6)})
($set ( a b )( 5 10 ))
($set c { a + b })
(${ int(( b + c - 2 ) * 3.5 / a )})
($set f \a.($  {a + 1}))
($set g \a.($f {a + 2}))
($set h \a.($g {a + 3}))
($h 4)
""",

TEXT([PLAIN('\n'), SET(ATOM('fib1'), LAMBDA([([], ATOM('n'), None)], APPLY(COND(APPLY(VAR([], ATOM('lt')), [VAR([], ATOM('n')), INT(2L)], []), VAR([], ATOM('n')), APPLY(VAR([], ATOM('add')), [APPLY(VAR([], ATOM('fib1')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(1L)], [])], []), APPLY(VAR([], ATOM('fib1')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(2L)], [])], [])], [])), [], []))), PLAIN('\n'), SET(ATOM('if'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('then')), VAR([], ATOM('else'))), [], []))), PLAIN('\n'), SET(ATOM('fib'), LAMBDA([([], ATOM('n'), None)], APPLY(VAR([], ATOM('if')), [APPLY(VAR([], ATOM('lt')), [VAR([], ATOM('n')), INT(2L)], []), VAR([], ATOM('n')), APPLY(VAR([], ATOM('add')), [APPLY(VAR([], ATOM('fib')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(1L)], [])], []), APPLY(VAR([], ATOM('fib')), [APPLY(VAR([], ATOM('sub')), [VAR([], ATOM('n')), INT(2L)], [])], [])], [])], []))), PLAIN('\n'), SET(ATOM('fib2'), LAMBDA([([], ATOM('n'), None)], APPLY(COND(INFIX(TEXT([PLAIN(' n < 2 ')], 0, 0)), VAR([], ATOM('n')), INFIX(TEXT([APPLY(VAR([], ATOM('fib2')), [INFIX(TEXT([PLAIN(' n - 1 ')], 0, 0))], []), PLAIN(' + '), APPLY(VAR([], ATOM('fib2')), [INFIX(TEXT([PLAIN(' n - 2 ')], 0, 0))], [])], 0, 0))), [], []))), PLAIN('\n'), APPLY(VAR([], ATOM('fib')), [INT(10L)], []), PLAIN('\n'), APPLY(VAR([], ATOM('fib1')), [INT(10L)], []), PLAIN('\n'), APPLY(INFIX(TEXT([APPLY(VAR([], ATOM('fib2')), [INT(1L)], []), PLAIN(' + '), APPLY(VAR([], ATOM('fib2')), [INT(2L)], []), PLAIN(' + '), APPLY(VAR([], ATOM('fib2')), [INT(3L)], []), PLAIN(' - '), APPLY(VAR([], ATOM('fib2')), [INT(6L)], [])], 0, 0)), [], []), PLAIN('\n'), SET([ATOM('a'), ATOM('b')], LIST([INT(5L), INT(10L)])), PLAIN('\n'), SET(ATOM('c'), INFIX(TEXT([PLAIN(' a + b ')], 0, 0))), PLAIN('\n'), APPLY(INFIX(TEXT([PLAIN(' int(( b + c - 2 ) * 3.5 / a )')], 0, 0)), [], []), PLAIN('\n'), SET(ATOM('f'), LAMBDA([([], ATOM('a'), None)], APPLY(INFIX(TEXT([PLAIN('a + 1')], 0, 0)), [], []))), PLAIN('\n'), SET(ATOM('g'), LAMBDA([([], ATOM('a'), None)], APPLY(VAR([], ATOM('f')), [INFIX(TEXT([PLAIN('a + 2')], 0, 0))], []))), PLAIN('\n'), SET(ATOM('h'), LAMBDA([([], ATOM('a'), None)], APPLY(VAR([], ATOM('g')), [INFIX(TEXT([PLAIN('a + 3')], 0, 0))], []))), PLAIN('\n'), APPLY(VAR([], ATOM('h')), [INT(4L)], []), PLAIN('\n')], 0, 0),

r"""
55
55
-4
16
10
"""
),(
#   ---- 11 -- "for each" loop
TRACE_STAGE_NONE,

r"""
($ ($range 3) (`Q))
($ ($range 10 21 2) \a.($mul a a) \a.($sqrt a) \b.(${'\t' + str(b)}))
($set R (0 2 4 6))
($set A (zero 0 one 1 two 2 three 3))
($set F \p.($p *A))
($set S \p.($mod "%s " p ))
($set LOOP \r.\b.($ ($range *r) b))
($set R1 (0 7 2))
($set FL (F S))
($ ($LOOP R1 *FL) ? {($R F S) == ($LOOP R1 *FL)} | ]ERROR ($LOOP R1 *FL) != ($R F S)\[)
($LOOP (0 100 10) \o.($o))
($set R ((0 a) (1 bb) (2 ccc) (3 dddd)))
($R \l.($ \n.\id.[ ($id) = (${n * 11});] *l))
($set L (0 90 180))
($set R ($L cos))
(${ '%f %f %f' % tuple(R) })
($set L1 ($LOOP ($len L) \i.($unq ($mod '($%d)' i))))
(${ ' '.join(L1) } *($R))
($(1 2 3))
{
    ($ ($range 3) \i.]
        ($set fn \ii.($ii))($ ($range ($add i 2)) fn),

    \[ )
}
($set fn ( '($\\i.($add i 1))' '($\\i.($i))' '($\\i.($sub i 1))' ))
($set each ($range ($len fn)))
($each \i.[ ($ ($$($i fn)) 10);])
($set a (
    (1 2 3 4 5)
    (6 7 8 9 0)
    (z w r t y)
    (u i o p s)
    (d f g h j)
))
($a \aa.($aa \aaa.[ {($aaa)}]))
($(0 1 2) \i.($(2 3 4) \ii.[ {($i ($ii a))} (($ii ($i a)))]))
($macro _set (name val)($set ($name) ($val)))
($_set five 5)
($mul five five)
($ (add sub mul div) \fn.($fn 8 2 ))
($set q 3)
($macro a (n) ($emit q \d.($add d ($n)) ))
{
    ($emit q inc), ($($range 4) \n.[($a n), ])($q),
}
""",

TEXT([PLAIN('\n'), APPLY(APPLY(VAR([], ATOM('range')), [INT(3L)], []), [STR('Q')], []), PLAIN('\n'), APPLY(APPLY(VAR([], ATOM('range')), [INT(10L), INT(21L), INT(2L)], []), [LAMBDA([([], ATOM('a'), None)], APPLY(VAR([], ATOM('mul')), [VAR([], ATOM('a')), VAR([], ATOM('a'))], [])), LAMBDA([([], ATOM('a'), None)], APPLY(VAR([], ATOM('sqrt')), [VAR([], ATOM('a'))], [])), LAMBDA([([], ATOM('b'), None)], APPLY(INFIX(TEXT([STR("'\\t'"), PLAIN(' + str(b)')], 0, 0)), [], []))], []), PLAIN('\n'), SET(ATOM('R'), LIST([INT(0L), INT(2L), INT(4L), INT(6L)])), PLAIN('\n'), SET(ATOM('A'), LIST([VAR([], ATOM('zero')), INT(0L), VAR([], ATOM('one')), INT(1L), VAR([], ATOM('two')), INT(2L), VAR([], ATOM('three')), INT(3L)])), PLAIN('\n'), SET(ATOM('F'), LAMBDA([([], ATOM('p'), None)], APPLY(VAR([], ATOM('p')), [EMBED(VAR([], ATOM('A')))], []))), PLAIN('\n'), SET(ATOM('S'), LAMBDA([([], ATOM('p'), None)], APPLY(VAR([], ATOM('mod')), [STR('"%s "'), VAR([], ATOM('p'))], []))), PLAIN('\n'), SET(ATOM('LOOP'), LAMBDA([([], ATOM('r'), None), ([], ATOM('b'), None)], APPLY(APPLY(VAR([], ATOM('range')), [EMBED(VAR([], ATOM('r')))], []), [VAR([], ATOM('b'))], []))), PLAIN('\n'), SET(ATOM('R1'), LIST([INT(0L), INT(7L), INT(2L)])), PLAIN('\n'), SET(ATOM('FL'), LIST([VAR([], ATOM('F')), VAR([], ATOM('S'))])), PLAIN('\n'), APPLY(COND(INFIX(TEXT([APPLY(VAR([], ATOM('R')), [VAR([], ATOM('F')), VAR([], ATOM('S'))], []), PLAIN(' == '), APPLY(VAR([], ATOM('LOOP')), [VAR([], ATOM('R1')), EMBED(VAR([], ATOM('FL')))], [])], 0, 0)), APPLY(VAR([], ATOM('LOOP')), [VAR([], ATOM('R1')), EMBED(VAR([], ATOM('FL')))], []), TEXT([PLAIN('ERROR '), APPLY(VAR([], ATOM('LOOP')), [VAR([], ATOM('R1')), EMBED(VAR([], ATOM('FL')))], []), PLAIN(' != '), APPLY(VAR([], ATOM('R')), [VAR([], ATOM('F')), VAR([], ATOM('S'))], [])], 0, 0)), [], []), PLAIN('\n'), APPLY(VAR([], ATOM('LOOP')), [LIST([INT(0L), INT(100L), INT(10L)]), LAMBDA([([], ATOM('o'), None)], APPLY(VAR([], ATOM('o')), [], []))], []), PLAIN('\n'), SET(ATOM('R'), LIST([LIST([INT(0L), VAR([], ATOM('a'))]), LIST([INT(1L), VAR([], ATOM('bb'))]), LIST([INT(2L), VAR([], ATOM('ccc'))]), LIST([INT(3L), VAR([], ATOM('dddd'))])])), PLAIN('\n'), APPLY(VAR([], ATOM('R')), [LAMBDA([([], ATOM('l'), None)], APPLY(LAMBDA([([], ATOM('n'), None), ([], ATOM('id'), None)], TEXT([PLAIN(' '), APPLY(VAR([], ATOM('id')), [], []), PLAIN(' = '), APPLY(INFIX(TEXT([PLAIN('n * 11')], 0, 0)), [], []), PLAIN(';')], 0, 0)), [EMBED(VAR([], ATOM('l')))], []))], []), PLAIN('\n'), SET(ATOM('L'), LIST([INT(0L), INT(90L), INT(180L)])), PLAIN('\n'), SET(ATOM('R'), APPLY(VAR([], ATOM('L')), [VAR([], ATOM('cos'))], [])), PLAIN('\n'), APPLY(INFIX(TEXT([PLAIN(' '), STR("'%f %f %f'"), PLAIN(' % tuple(R) ')], 0, 0)), [], []), PLAIN('\n'), SET(ATOM('L1'), APPLY(VAR([], ATOM('LOOP')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('L'))], []), LAMBDA([([], ATOM('i'), None)], APPLY(VAR([], ATOM('unq')), [APPLY(VAR([], ATOM('mod')), [STR("'($%d)'"), VAR([], ATOM('i'))], [])], []))], [])), PLAIN('\n'), APPLY(INFIX(TEXT([PLAIN(' '), STR("' '"), PLAIN('.join(L1) ')], 0, 0)), [EMBED(APPLY(VAR([], ATOM('R')), [], []))], []), PLAIN('\n'), APPLY(LIST([INT(1L), INT(2L), INT(3L)]), [], []), PLAIN('\n{\n    '), APPLY(APPLY(VAR([], ATOM('range')), [INT(3L)], []), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN('        '), SET(ATOM('fn'), LAMBDA([([], ATOM('ii'), None)], APPLY(VAR([], ATOM('ii')), [], []))), APPLY(APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('add')), [VAR([], ATOM('i')), INT(2L)], [])], []), [VAR([], ATOM('fn'))], []), PLAIN(',\n')], 0, 0))], []), PLAIN('\n}\n'), SET(ATOM('fn'), LIST([STR("'($\\\\i.($add i 1))'"), STR("'($\\\\i.($i))'"), STR("'($\\\\i.($sub i 1))'")])), PLAIN('\n'), SET(ATOM('each'), APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('fn'))], [])], [])), PLAIN('\n'), APPLY(VAR([], ATOM('each')), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN(' '), APPLY(EVAL(APPLY(APPLY(VAR([], ATOM('i')), [VAR([], ATOM('fn'))], []), [], [])), [INT(10L)], []), PLAIN(';')], 0, 0))], []), PLAIN('\n'), SET(ATOM('a'), LIST([LIST([INT(1L), INT(2L), INT(3L), INT(4L), INT(5L)]), LIST([INT(6L), INT(7L), INT(8L), INT(9L), INT(0L)]), LIST([VAR([], ATOM('z')), VAR([], ATOM('w')), VAR([], ATOM('r')), VAR([], ATOM('t')), VAR([], ATOM('y'))]), LIST([VAR([], ATOM('u')), VAR([], ATOM('i')), VAR([], ATOM('o')), VAR([], ATOM('p')), VAR([], ATOM('s'))]), LIST([VAR([], ATOM('d')), VAR([], ATOM('f')), VAR([], ATOM('g')), VAR([], ATOM('h')), VAR([], ATOM('j'))])])), PLAIN('\n'), APPLY(VAR([], ATOM('a')), [LAMBDA([([], ATOM('aa'), None)], APPLY(VAR([], ATOM('aa')), [LAMBDA([([], ATOM('aaa'), None)], TEXT([PLAIN(' {'), APPLY(VAR([], ATOM('aaa')), [], []), PLAIN('}')], 0, 0))], []))], []), PLAIN('\n'), APPLY(LIST([INT(0L), INT(1L), INT(2L)]), [LAMBDA([([], ATOM('i'), None)], APPLY(LIST([INT(2L), INT(3L), INT(4L)]), [LAMBDA([([], ATOM('ii'), None)], TEXT([PLAIN(' {'), APPLY(VAR([], ATOM('i')), [APPLY(VAR([], ATOM('ii')), [VAR([], ATOM('a'))], [])], []), PLAIN('} ('), APPLY(VAR([], ATOM('ii')), [APPLY(VAR([], ATOM('i')), [VAR([], ATOM('a'))], [])], []), PLAIN(')')], 0, 0))], []))], []), PLAIN('\n'), MACRO(ATOM('_set'), [ATOM('name'), ATOM('val')], '($set ($name) ($val))'), PLAIN('\n'), APPLY(VAR([], ATOM('_set')), [VAR([], ATOM('five')), INT(5L)], []), PLAIN('\n'), APPLY(VAR([], ATOM('mul')), [VAR([], ATOM('five')), VAR([], ATOM('five'))], []), PLAIN('\n'), APPLY(LIST([VAR([], ATOM('add')), VAR([], ATOM('sub')), VAR([], ATOM('mul')), VAR([], ATOM('div'))]), [LAMBDA([([], ATOM('fn'), None)], APPLY(VAR([], ATOM('fn')), [INT(8L), INT(2L)], []))], []), PLAIN('\n'), SET(ATOM('q'), INT(3L)), PLAIN('\n'), MACRO(ATOM('a'), [ATOM('n')], ' ($emit q \\d.($add d ($n)) )'), PLAIN('\n{\n    '), EMIT(VAR([], ATOM('q')), VAR([], ATOM('inc'))), PLAIN(', '), APPLY(APPLY(VAR([], ATOM('range')), [INT(4L)], []), [LAMBDA([([], ATOM('n'), None)], TEXT([APPLY(VAR([], ATOM('a')), [VAR([], ATOM('n'))], []), PLAIN(', ')], 0, 0))], []), APPLY(VAR([], ATOM('q')), [], []), PLAIN(',\n}\n')], 0, 0),

r"""
QQQ
10.0	12.0	14.0	16.0	18.0	20.0
"zero ""one ""two ""three "
0102030405060708090
a = 0; bb = 11; ccc = 22; dddd = 33;
1.000000 -0.448074 -0.598460
1.0 -0.448073616129 -0.598460069058
123
{
    01,
    012,
    0123,

}
11; 10; 9;
{1} {2} {3} {4} {5} {6} {7} {8} {9} {0} {z} {w} {r} {t} {y} {u} {i} {o} {p} {s} {d} {f} {g} {h} {j}
{z} (3) {u} (4) {d} (5) {w} (8) {i} (9) {f} (0) {r} (r) {o} (t) {g} (y)
25
106164
{
    3, 4, 4, 5, 7, 10,
}
"""
),(
#   ---- 12 -- dict
TRACE_STAGE_NONE,

r"""
($! dict )
($set name    ( ch      f       i    ))
($set type    ( char    float   int  ))
($set length  ( 1       2       4    ))
($set default ( 1       0.2     -10  ))
($set delta   ( 0       0.1     10   )) /* dict */
($ ($range ($len name)) \i.]
    ($set l ($i length)) ($set val ($i default)) ($set d ($i delta))
    ($i type) ($i name)($ [[($l)]] ? { l > 1 }) = ($ [{ ($ ($range l) \ii.[(${} val + ( d * ii )), ])}] ? { l > 1 } | val);

\[ )
($! macro dict )
($macro dict (id cols body)
    ($set cols-($id) ($range ($len (($cols)) )))
    ($set each-($id) ($range ($len (($body)) )))
    ($set (($cols))
        ($cols-($id) \i.($each-($id) \ii.($i ($ii (($body)) ))))
    )
)
($dict D
    (` name     type             length  default  format   )
    (`
    (  app      char             5       "yupp"   "\n%s "  )
    (  release  float            1       0.5      "%.1f"   )
    (  pre      char             1       'a'      "%c"     )
    (  number   (`unsigned int)  1       1        "%d"     )
    )
)
($each-D \i.]
    ($set dim [[($i length)]] ? { ($i length) > 1 })
    ($i type) ($i name)($dim) = ($i default);

\[ )
($each-D \i.]
    printf(($i format), ($i name));

\[ )
($macro dict (id cols body)
    ($set each-($id) ($range ($len (($body)) )))
    ($set (($cols))
        ($ ($range ($len ($split (`($cols)) ))) \i.($ (($body)) \var.($i var)))
    )
)
($dict D1
    (` name  type  length  default  format )
    (`
    (  s     char  5       "abc"    "%s"   )
    (  c     char  1       'a'      "%c"   )
    (  d     int   4       1        "%d"   )
    )
)
($each-D1 \i.]
    ($set dim [[($i length)]] ? { ($i length) > 1 })
    ($i type) ($i name)($dim) = ($i default);

\[ )
""",

TEXT([PLAIN('\n'), COMMENT(), PLAIN('\n'), SET(ATOM('name'), LIST([VAR([], ATOM('ch')), VAR([], ATOM('f')), VAR([], ATOM('i'))])), PLAIN('\n'), SET(ATOM('type'), LIST([VAR([], ATOM('char')), VAR([], ATOM('float')), VAR([], ATOM('int'))])), PLAIN('\n'), SET(ATOM('length'), LIST([INT(1L), INT(2L), INT(4L)])), PLAIN('\n'), SET(ATOM('default'), LIST([INT(1L), FLOAT(0.2), INT(-10L)])), PLAIN('\n'), SET(ATOM('delta'), LIST([INT(0L), FLOAT(0.1), INT(10L)])), PLAIN(' /* dict */\n'), APPLY(APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('name'))], [])], []), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN('    '), SET(ATOM('l'), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('length'))], [])), PLAIN(' '), SET(ATOM('val'), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('default'))], [])), PLAIN(' '), SET(ATOM('d'), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('delta'))], [])), PLAIN('\n    '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('type'))], []), PLAIN(' '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('name'))], []), APPLY(COND(INFIX(TEXT([PLAIN(' l > 1 ')], 0, 0)), TEXT([PLAIN('['), APPLY(VAR([], ATOM('l')), [], []), PLAIN(']')], 0, 0), None), [], []), PLAIN(' = '), APPLY(COND(INFIX(TEXT([PLAIN(' l > 1 ')], 0, 0)), TEXT([PLAIN('{ '), APPLY(APPLY(VAR([], ATOM('range')), [VAR([], ATOM('l'))], []), [LAMBDA([([], ATOM('ii'), None)], TEXT([INFIX(TEXT([PLAIN(' val + ( d * ii )')], 0, 0)), PLAIN(', ')], 0, 0))], []), PLAIN('}')], 0, 0), VAR([], ATOM('val'))), [], []), PLAIN(';\n')], 0, 0))], []), PLAIN('\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('dict'), [ATOM('id'), ATOM('cols'), ATOM('body')], '\n    ($set cols-($id) ($range ($len (($cols)) )))\n    ($set each-($id) ($range ($len (($body)) )))\n    ($set (($cols))\n        ($cols-($id) \\i.($each-($id) \\ii.($i ($ii (($body)) ))))\n    )\n'), PLAIN('\n'), APPLY(VAR([], ATOM('dict')), [VAR([], ATOM('D')), STR(' name     type             length  default  format   '), STR('\n    (  app      char             5       "yupp"   "\\n%s "  )\n    (  release  float            1       0.5      "%.1f"   )\n    (  pre      char             1       \'a\'      "%c"     )\n    (  number   (`unsigned int)  1       1        "%d"     )\n    ')], []), PLAIN('\n'), APPLY(VAR([], ATOM('each-D')), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN('    '), SET(ATOM('dim'), COND(INFIX(TEXT([PLAIN(' '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('length'))], []), PLAIN(' > 1 ')], 0, 0)), TEXT([PLAIN('['), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('length'))], []), PLAIN(']')], 0, 0), None)), PLAIN('\n    '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('type'))], []), PLAIN(' '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('name'))], []), APPLY(VAR([], ATOM('dim')), [], []), PLAIN(' = '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('default'))], []), PLAIN(';\n')], 0, 0))], []), PLAIN('\n'), APPLY(VAR([], ATOM('each-D')), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN('    printf('), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('format'))], []), PLAIN(', '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('name'))], []), PLAIN(');\n')], 0, 0))], []), PLAIN('\n'), MACRO(ATOM('dict'), [ATOM('id'), ATOM('cols'), ATOM('body')], '\n    ($set each-($id) ($range ($len (($body)) )))\n    ($set (($cols))\n        ($ ($range ($len ($split (`($cols)) ))) \\i.($ (($body)) \\var.($i var)))\n    )\n'), PLAIN('\n'), APPLY(VAR([], ATOM('dict')), [VAR([], ATOM('D1')), STR(' name  type  length  default  format '), STR('\n    (  s     char  5       "abc"    "%s"   )\n    (  c     char  1       \'a\'      "%c"   )\n    (  d     int   4       1        "%d"   )\n    ')], []), PLAIN('\n'), APPLY(VAR([], ATOM('each-D1')), [LAMBDA([([], ATOM('i'), None)], TEXT([PLAIN('    '), SET(ATOM('dim'), COND(INFIX(TEXT([PLAIN(' '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('length'))], []), PLAIN(' > 1 ')], 0, 0)), TEXT([PLAIN('['), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('length'))], []), PLAIN(']')], 0, 0), None)), PLAIN('\n    '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('type'))], []), PLAIN(' '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('name'))], []), APPLY(VAR([], ATOM('dim')), [], []), PLAIN(' = '), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('default'))], []), PLAIN(';\n')], 0, 0))], []), PLAIN('\n')], 0, 0),

r"""
/* dict */
char ch = 1;
float f[2] = { 0.2, 0.3, };
int i[4] = { -10, 0, 10, 20, };

char app[5] = "yupp";
float release = 0.5;
char pre = 'a';
unsigned int number = 1;

printf("\n%s ", app);
printf("%.1f", release);
printf("%c", pre);
printf("%d", number);

char s[5] = "abc";
char c = 'a';
int d[4] = 1;

"""
),(
#   ---- 13 -- let
TRACE_STAGE_NONE,

r"""
($import stdlib)
($let x 10 ($\i.($mul i x) { 15.6 + x }))
($x) ($! 'x' must be unbound here)
($let (pow2 pow4) (\i.($mul i i) \i.($pow2 ($pow2 i))) ($pow2 ($pow4 2)))
($! unfold)
($set planet (Mercury Venus Earth Mars Jupiter Saturn Uranus Neptune))
($set delim ($reversed ($unfold ($len planet) [] [($SPACE)and ] [, ])))
($($range ($len planet)) \i.[($i planet)($i delim)])
""",

TEXT([PLAIN('\n'), IMPORT_BEGIN(), COMMENT(), PLAIN('\n'), MACRO(ATOM('dict'), [ATOM('id'), ATOM('cols'), ATOM('body')], '\n\t($set cols-($id) ($range ($len (($cols)) )))\n\t($set each-($id) ($range ($len (($body)) )))\n\t($set (($cols))\n\t\t($cols-($id) \\__i.($ (($body)) \\__var.($__i __var)))\n\t)\n'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('if'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('then')), VAR([], ATOM('else'))), [], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('unless'), LAMBDA([([], ATOM('cond'), None), ([], ATOM('then'), TEXT([], 0, 0)), ([], ATOM('else'), TEXT([], 0, 0))], APPLY(COND(VAR([], ATOM('cond')), VAR([], ATOM('else')), VAR([], ATOM('then'))), [], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('unfold'), LAMBDA([([], ATOM('count'), None), ([], ATOM('...'), None)], LET([ATOM('__last'), ATOM('__func')], LIST([APPLY(VAR([], ATOM('sub')), [APPLY(VAR([], ATOM('len')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], []), INT(1L)], []), APPLY(VAR([], ATOM('__last')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], [])]), APPLY(APPLY(VAR([], ATOM('range')), [VAR([], ATOM('count'))], []), [LAMBDA([([], ATOM('__i'), None)], APPLY(VAR([], ATOM('if')), [INFIX(TEXT([PLAIN(' __i < __last ')], 0, 0)), APPLY(VAR([], ATOM('__i')), [APPLY(VAR([], ATOM('lazy')), [VAR([], ATOM('__va_args__'))], [])], []), APPLY(VAR([], ATOM('__func')), [VAR([], ATOM('__i'))], [])], []))], [])))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('do'), [ATOM('body')], 'do {\n($body)\n} while ( 0 )'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('foo'), [ATOM('body')], '({\n($body)\n})'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('__EOL__'), COND(APPLY(VAR([], ATOM('not')), [APPLY(VAR([], ATOM('isatom')), [VAR([], ATOM('EOL'))], [])], []), VAR([], ATOM('EOL')), TEXT([PLAIN('\n')], 0, 0))), PLAIN('\n'), SET(ATOM('define'), LAMBDA([([], ATOM('sig'), None), ([], ATOM('body'), None)], APPLY(VAR([], ATOM('join')), [APPLY(VAR([], ATOM('split')), [TEXT([APPLY(VAR([], ATOM('unq')), [STR('"#define"')], []), PLAIN(' '), APPLY(VAR([], ATOM('sig')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('body')), [], [])], 0, 0), VAR([], ATOM('__EOL__'))], []), TEXT([PLAIN(' \\'), APPLY(VAR([], ATOM('__EOL__')), [], [])], 0, 0)], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('def'), [ATOM('name')], '($set ($name) 1)\n($unq "#define") ($name)'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('undef'), [ATOM('name')], '($set ($name) 0)\n($unq "#undef")  ($name)'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('def-if'), [ATOM('cond'), ATOM('name')], '($set ($name) 1 ? ($cond) | 0)\n($if ($name) [($unq "#define") ($name)])'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), MACRO(ATOM('skip-if'), [ATOM('cond')], '($if ($cond) ($skip))'), PLAIN('\n'), MACRO(ATOM('skip-if-not'), [ATOM('cond')], '($if ($not ($cond)) ($skip))'), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('BIN'), LAMBDA([([], ATOM('b'), None)], APPLY(VAR([], ATOM('atoi')), [VAR([], ATOM('b')), INT(2L)], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('BB'), LAMBDA([([], ATOM('...'), None)], APPLY(VAR([], ATOM('sum')), [APPLY(APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('__va_args__'))], [])], []), [LAMBDA([([], ATOM('__i'), None)], INFIX(TEXT([PLAIN(' '), APPLY(VAR([], ATOM('BIN')), [APPLY(VAR([], ATOM('__i')), [APPLY(VAR([], ATOM('reversed')), [VAR([], ATOM('__va_args__'))], [])], [])], []), PLAIN(' << '), APPLY(VAR([], ATOM('__i')), [], []), PLAIN(' * 8 ')], 0, 0)))], [])], []))), PLAIN('\n\n'), COMMENT(), PLAIN('\n'), SET(ATOM('def-fn-argv'), LAMBDA([([], ATOM('type'), None), ([], ATOM('name'), None), ([ATOM('type'), ATOM('arg-begin'), ATOM('arg-count'), ATOM('arg-value'), ATOM('arg-end')], ATOM('body'), None)], TEXT([APPLY(VAR([], ATOM('type')), [], []), PLAIN(' '), APPLY(VAR([], ATOM('name')), [], []), PLAIN('( int argcnt, ... )\n{\n\t'), APPLY(VAR([], ATOM('body')), [], [(ATOM('type'), VAR([], ATOM('type'))), (ATOM('arg-begin'), TEXT([PLAIN('\t\tva_list argptr;\n\t\tva_start( argptr, argcnt );')], 0, 0)), (ATOM('arg-count'), TEXT([PLAIN('\t\targcnt')], 0, 0)), (ATOM('arg-value'), LAMBDA([([], ATOM('type'), None)], TEXT([PLAIN('\t\tva_arg( argptr, '), APPLY(VAR([], ATOM('type')), [], []), PLAIN(' )')], 0, 0))), (ATOM('arg-end'), TEXT([PLAIN('\t\tva_end( argptr );')], 0, 0))]), PLAIN('\n}')], 0, 0))), PLAIN('\n\n'), SET(ATOM('INT_MAX'), INFIX(TEXT([PLAIN(' sys.maxint ')], 0, 0))), PLAIN('\n\n'), SET(ATOM('INT_MIN'), INFIX(TEXT([PLAIN(' -sys.maxint - 1 ')], 0, 0))), PLAIN('\n'), IMPORT_END(), PLAIN('\n'), LET(ATOM('x'), INT(10L), APPLY(LAMBDA([([], ATOM('i'), None)], APPLY(VAR([], ATOM('mul')), [VAR([], ATOM('i')), VAR([], ATOM('x'))], [])), [INFIX(TEXT([PLAIN(' 15.6 + x ')], 0, 0))], [])), PLAIN('\n'), APPLY(VAR([], ATOM('x')), [], []), PLAIN(' '), COMMENT(), PLAIN('\n'), LET([ATOM('pow2'), ATOM('pow4')], LIST([LAMBDA([([], ATOM('i'), None)], APPLY(VAR([], ATOM('mul')), [VAR([], ATOM('i')), VAR([], ATOM('i'))], [])), LAMBDA([([], ATOM('i'), None)], APPLY(VAR([], ATOM('pow2')), [APPLY(VAR([], ATOM('pow2')), [VAR([], ATOM('i'))], [])], []))]), APPLY(VAR([], ATOM('pow2')), [APPLY(VAR([], ATOM('pow4')), [INT(2L)], [])], [])), PLAIN('\n'), COMMENT(), PLAIN('\n'), SET(ATOM('planet'), LIST([VAR([], ATOM('Mercury')), VAR([], ATOM('Venus')), VAR([], ATOM('Earth')), VAR([], ATOM('Mars')), VAR([], ATOM('Jupiter')), VAR([], ATOM('Saturn')), VAR([], ATOM('Uranus')), VAR([], ATOM('Neptune'))])), PLAIN('\n'), SET(ATOM('delim'), APPLY(VAR([], ATOM('reversed')), [APPLY(VAR([], ATOM('unfold')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('planet'))], []), TEXT([], 0, 0), TEXT([APPLY(VAR([], ATOM('SPACE')), [], []), PLAIN('and ')], 0, 0), TEXT([PLAIN(', ')], 0, 0)], [])], [])), PLAIN('\n'), APPLY(APPLY(VAR([], ATOM('range')), [APPLY(VAR([], ATOM('len')), [VAR([], ATOM('planet'))], [])], []), [LAMBDA([([], ATOM('i'), None)], TEXT([APPLY(VAR([], ATOM('i')), [VAR([], ATOM('planet'))], []), APPLY(VAR([], ATOM('i')), [VAR([], ATOM('delim'))], [])], 0, 0))], []), PLAIN('\n')], 0, 0),

r"""
256.0
x
256
Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus and Neptune
"""
),(
#   ---- XX --
TRACE_STAGE_NONE,

r"""
""",

TEXT([PLAIN('\n')], 0, 0),

r"""
"""
)]

#   -----------------------------------
#   Testkit routines
#   -----------------------------------

CH  = '.'
LL  = 79
___ = CH * LL

#   ---------------------------------------------------------------------------
def ___title___( t ):
    l = len( t )
    d = ( LL - 2 - l ) // 2
    return CH * d + ' ' + t + ' ' + CH * ( LL - 2 - l - d )

#   ---------------------------------------------------------------------------
def test( kit, t ):                                                                                                    #pylint: disable=too-many-statements
    """
    For each test case: ( text, parsed, evaluated ),
    check: ( yuparse( yushell.input_file ) == parsed ) and ( yueval( parsed ) == evaluated ).
    """
#   ---------------
    print ___title___( t )

    failed = []
    i = 0
    for ( TR, text, parsed, evaluated ) in kit:
        i += 1
        trace.stages = TR | _TRACE
        trace.set_current( TRACE_STAGE_PARSE )
        TR2F = trace.enabled and trace.file
        LOG = not trace.enabled or trace.file
        e = None
        try:
            print '* %d *' % ( i )
            print text, '\n'
            if TR2F:
                trace.info( text )
            if trace.enabled:
                trace.info( ___title___( 'test %d' % ( i )))
            trace.deepest = 0
#   ---- parse
            yushell( text )
            yuinit()
            ast = yuparse( yushell.input_file )

            print repr( ast ), '\n'
            if TR2F:
                trace.info( repr( ast ))
                trace.info( trace.TEMPL_DEEPEST, trace.deepest )

#   ---- test
            result = ( ast == parsed )

        except:                                                                                                        #pylint: disable=bare-except
            e_type, e, tb = sys.exc_info()
            msg = '\n'
            arg = e.args[ 0 ]
            if _TRACEBACK or isinstance( arg, str ) and arg.startswith( 'python' ):
#               -- enabled traceback or not raised exception
                msg += ''.join( traceback.format_tb( tb ))
            msg += ''.join( traceback.format_exception_only( e_type, e ))
            print msg
            if TR2F:
                trace.info( msg )
                trace.info( trace.TEMPL_DEEPEST, trace.deepest )
            if LOG:
                log.error( msg )

            result = isinstance( parsed, type ) and issubclass( parsed, Exception ) and isinstance( e, parsed )

        if not result:
            failed += [ i ]
            print '*** FAIL *** Expected AST:'
            print repr( parsed ), '\n'

        if evaluated and e is None:
            trace.set_current( TRACE_STAGE_EVAL )
            TR2F = trace.enabled and trace.file
            LOG = not trace.enabled or trace.file
            try:
                trace.deepest = 0
#   ---- eval
                plain = yueval( ast )

                if isinstance( plain, str ):
                    plain = replace_steady( reduce_emptiness( plain ))
                    res = plain
                else:
                    res = repr( plain )
                print res, '\n'
                if TR2F:
                    trace.info( res )
                    trace.info( trace.TEMPL_DEEPEST, trace.deepest )
#   ---- test
                result = ( plain == evaluated )

            except:                                                                                                    #pylint: disable=bare-except
                e_type, e, tb = sys.exc_info()
                msg = '\n'
                arg = e.args[ 0 ]
                if _TRACEBACK or isinstance( arg, str ) and arg.startswith( 'python' ):
#                   -- enabled traceback or not raised exception
                    msg += ''.join( traceback.format_tb( tb ))
                msg += ''.join( traceback.format_exception_only( e_type, e ))
                print msg
                if TR2F:
                    trace.info( msg )
                    trace.info( trace.TEMPL_DEEPEST, trace.deepest )
                if LOG:
                    log.error( msg )

                result = ( isinstance( evaluated, type ) and issubclass( evaluated, Exception )
                and isinstance( e, evaluated ))

            if not result:
                failed += [ i ]
                print '*** FAIL *** Expected result:'
                print evaluated, '\n'

        trace.set_current( TR )
        if trace.enabled:
            trace.info( ___ )

    print ___
    print '%47s\n' % ( 'F A I L E D' if failed else 'P A S S E D' )
    print '  %d fault(s) in %d test(s)' % ( len( failed ), len( kit ))
    if failed:
        print '  %s' % ( str( failed ))
    print ___

    return len( failed )

#   ---------------------------------------------------------------------------
if __name__ == '__main__':
    t_failed = 0
    t_failed -= test( t_parse_kit, t_parse_title )
    t_failed -= test( t_eval_kit, t_eval_title )

    sys.exit( t_failed )
