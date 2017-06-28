def say(msg='Hello, world'):
    while True:
        msg = yield msg
        if msg is None:
            break


if __name__ == '__main__':
    coro = say()
    print(coro.send(None))
    print(coro.send('Foo!'))
    print(coro.send('Bar!'))
    print(coro.send(None))
