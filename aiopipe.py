import asyncio
import subprocess
import time


@asyncio.coroutine
def runner(argv, timeout=0):
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)

    t0 = time.time()

    while True:
        exit_code = proc.poll()
        if exit_code is None:
            # Process is still running
            if timeout > 0 and time.time() - t0 >= timeout:
                proc.kill()
                raise Exception('Timeout exceeded')
        else:
            return proc.returncode
        # time.sleep(1)     <-- BAD idea
        yield from asyncio.sleep(.1)


def defcallback(future):
    if future.cancelled():
        print(f'[{id(future)}] was cancelled.')
        return

    e = future.exception()
    if e is not None:
        print(f'[{id(future)}] exception={e}')
        return

    print(f'[{id(future)}] result={future.result()}')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    # Run one at the time: not what we want!
    # loop.run_until_complete(runner('sleep 10'.split()))
    # loop.run_until_complete(runner('sleep 10'.split()))
    # loop.run_until_complete(runner('sleep 10'.split()))

    # Call the coroutines in parallel, still no callbacks.
    # tasks = [runner('sleep 10'.split(), timeout=5),
    #          runner('sleep 10'.split()),
    #          runner('sleep 10'.split())]
    #
    # loop.run_until_complete(asyncio.wait(tasks))

    tasks = [asyncio.Task(runner('sleep 10'.split(), timeout=5)),
             asyncio.Task(runner('sleep 10'.split())),
             asyncio.Task(runner('sleep 10'.split()))]
    for task in tasks:
        task.add_done_callback(defcallback)

    loop.run_until_complete(asyncio.wait(tasks))
