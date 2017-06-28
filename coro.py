def myrange(n):
    assert n >= 0

    i = 0
    while i < n:
        yield i
        i += 1


if __name__ == '__main__':
    # for x in myrange(10):
    #     print(x)
    #
    # print(list(myrange(10)))

    coro = myrange(10)
    print(coro)
    print(coro.send(None))
    print(next(coro))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
    print(coro.send(None))
