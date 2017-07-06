"""
Simple example of generator function in pure Python.
"""


def say(msg='Hello, world'):
    i = 0

    while True:
        print(f'[coroutine] Iteration {i}')

        msg = yield msg
        if msg is None:
            break

        print(f'[coroutine] Iteration {i} end')
        i += 1


if __name__ == '__main__':
    coro = say()
    print('[system] Calling send method')
    print(coro.send(None))
    print('[system] Calling send method')
    print(coro.send('Foo!'))
    print('[system] Calling send method')
    print(coro.send('Bar!'))
    print('[system] Calling send method')
    print(coro.send(None))
