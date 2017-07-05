import asyncio
import subprocess
import time


async def monitor(task):
    while True:
        if not task.done():
            await asyncio.sleep(0)
        else:
            print(f'task {id(task)} is done!')
            return task.result()


async def runner(argv, timeout=0):
    def stringify(xs):
        return map(str, xs)

    argv = list(stringify(argv))
    proc = subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)

    t0 = time.time()

    while True:
        exit_code = proc.poll()
        if exit_code is None:
            # Process is still running
            if timeout > 0 and time.time() - t0 >= timeout:
                proc.kill()
                stdout = proc.stdout.read()
                stderr = proc.stderr.read()
                raise subprocess.TimeoutExpired(cmd=' '.join(argv),
                                                timeout=timeout,
                                                output=stdout,
                                                stderr=stderr)
        else:
            return proc.returncode
        # time.sleep(1)     <-- BAD idea
        await asyncio.sleep(.1)


def defcallback(task):
    """Schedule all the task children but only if we terminated OK"""
    if task.cancelled():
        print(f'[task {id(task)}] was cancelled :-(')
    elif task.exception() is not None:
        print(f'[task {id(task)}] raised "{task.exception()}"')
    elif task.result() is not None:
        print(f'[task {id(task)}] returned {task.result()}')
    else:
        print(f'[task {id(task)}]: we do not know what happened :-\\')

    # loop = asyncio.get_event_loop()
    #
    # for child in task.children:
    #     print(f'[task {id(task)}] scheduling child coroutine')
    #     loop.create_task(child)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    tasks = [
        loop.create_task(runner('sleep 10'.split(), timeout=5)),
        loop.create_task(runner('sleep 10'.split())),
        loop.create_task(runner('sleep 10'.split())),
    ]

    task = loop.create_task(runner('sleep 10'.split()))
    monitor_task = loop.create_task(monitor(task))
    tasks += [task, monitor_task]

    # Set my callback to all tasks
    for task in tasks:
        task.add_done_callback(defcallback)

    loop.run_until_complete(asyncio.wait(tasks))
