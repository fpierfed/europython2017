import asyncio


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
    proc = await asyncio.create_subprocess_exec(*argv,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    if timeout <= 0:
        timeout = None
    await asyncio.wait_for(proc.wait(), timeout=timeout)
    return proc.returncode


def defcallback(task):
    """Schedule all the task children but only if we terminated OK"""
    if task.cancelled():
        print(f'[task {id(task)}] was cancelled :-(')
    elif task.exception() is not None:
        ex = task.exception()
        ex_type = ex.__class__.__name__
        print(f'[task {id(task)}] raised "{ex_type}({ex})"')
    elif task.done():
        print(f'[task {id(task)}] returned {task.result()}')
    else:
        print(f'[task {id(task)}]: we do not know what happened :-\\')


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
