"""
Like aiopipe.py but with task dependencies. In order to support that, one needs
to sunblass asyncio.Task and specify a custom task factory.

Of course, another way would be to create a DAG and schedule that. In that case
the DAG coroutine would then schedule its own tasks at the right times.
"""
import asyncio
import subprocess
import time


async def monitor(task):
    """Monitor a task and exit once that task is done."""

    while True:
        if not task.done():
            await asyncio.sleep(0)
        else:
            print(f'task {id(task)} is done!')
            return task.result()


async def runner(argv, timeout=0):
    """
    Run the input command-line executable (specified in a Popen-style list) and
    return its exit code. Optionally specify a timeout. If timeout is 0 or
    None, simply wait until the process is done.
    """

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
    """
    Not-so-simple-callback: log what happened to STDOUT and schedule any
    task dependency.
    """
    if task.cancelled():
        print(f'[task {id(task)}] was cancelled :-(')
    elif task.exception() is not None:
        ex = task.exception()
        ex_type = ex.__class__.__name__
        print(f'[task {id(task)}] raised "{ex_type}({ex})"')
    elif task.done():
        print(f'[task {id(task)}] returned {task.result()}')

        if hasattr(task, 'children'):
            loop = asyncio.get_event_loop()

            for coroutine in task.children:
                print(f'[task {id(task)}] scheduling child coroutine')
                task = loop.create_task(coroutine)
                task.add_done_callback(defcallback)
    else:
        print(f'[task {id(task)}]: we do not know what happened :-\\')


class MyTask(asyncio.Task):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = []


def my_task_factory(loop, coro):
    return MyTask(coro)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_task_factory(my_task_factory)

    loop.create_task(runner('sleep 10'.split(), timeout=5)),
    loop.create_task(runner('sleep 10'.split())),
    loop.create_task(runner('sleep 10'.split())),

    task = loop.create_task(runner('sleep 10'.split()))
    monitor_task = loop.create_task(monitor(task))

    task = loop.create_task(runner('sleep 10'.split()))
    task.children.append(runner('sleep 5'.split()))

    # Set my callback to all tasks
    for task in asyncio.Task.all_tasks():
        task.add_done_callback(defcallback)

    while True:
        pending = [t for t in asyncio.Task.all_tasks() if not t.done()]
        if pending:
            loop.run_until_complete(asyncio.wait(pending))
        else:
            loop.close()
            break
