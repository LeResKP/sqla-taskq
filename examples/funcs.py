import time


def test_func1(*args, **kw):
    print 'test_func1 called'
    time.sleep(2)
    print 'test_func1 done'
    return 1


def test_func2(*args, **kw):
    print 'test_func2 called'
    time.sleep(4)
    print 'test_func2 done'
    return 2
