# coding: yupp

($__TITLE__ 0)

($import coroutine-py)

c = False

def ($coro A):
    while True:
        print 'A'
        ($coro-yield)

def ($coro B):
    global c

    for i in xrange( 5 ):
        print 'B'
        if i & 1:
            c = True
        ($coro-yield)

    ($coro-quit)

def ($coro C):
    global c

    while True:
        ($coro-wait,,c)
        print 'C'
        c = False

if __name__ == '__main__':
    ($coro-init A)
    ($coro-init B)
    ($coro-init C)

    while True:
        ($coro-call A)
        if not ($coro-alive ($coro-call B)):
            break
        ($coro-call C)
        print
