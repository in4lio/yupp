
#  coro.yugen.py was generated by yup.py (yupp) 1.0c3
#  out of coro.py 

CO_READY = 0
CO_WAIT  = 1
CO_YIELD = 2
CO_END   = 3
CO_SKIP  = 4

c = False

def coro_A():
    while True:
        print 'A'
        yield CO_YIELD

def coro_B():
    global c

    for i in xrange( 5 ):
        print 'B'
        if i & 1:
            c = True
        yield CO_YIELD

    while True: yield CO_END

def coro_C():
    global c

    while True:
        while not ( c ): yield CO_WAIT
        print 'C'
        c = False

if __name__ == '__main__':
    A = coro_A()
    B = coro_B()
    C = coro_C()

    while True:
        A.next()
        if not ((  B.next() ) < CO_END ):
            break
        C.next()
        print
