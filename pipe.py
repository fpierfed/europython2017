from collections import defaultdict
import selectors
import subprocess
import time


TICK = 0.001
RESOLUTION = 3


def sleep(n):
    yield TICK * n


def monitor(task):
    while True:
        if task.result is None:
            yield
        else:
            print(f'task {task.id} is done!')
            return task.result


def runner(argv, timeout=0):
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
        yield from sleep(20)


def defcallback(task):
    print(f'[task {task.id}] completed with result={task.result}')


def deferrback(task):
    print(f'[task {task.id}] raised "{task.exception}"')


class Task:
    instances_created = 0

    def __init__(self, coroutine, callback=defcallback, errback=deferrback):
        self.coroutine = coroutine
        self.id = Task.instances_created
        Task.instances_created += 1

        self._result = None
        self._exception = None
        self.isrunning = False
        self.cancelled = False

        self.callback = callback
        self.errback = errback

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value
        self.isrunning = False
        self.cancelled = False

    @property
    def exception(self):
        return self._exception

    @exception.setter
    def exception(self, value):
        self._exception = value
        self.isrunning = False
        self.cancelled = True


class Loop:
    def __init__(self):
        self.now = 0
        self.ready_at = defaultdict(list)
        self.all_tasks = []

    def schedule(self, task, t=0):
        t = round(t, RESOLUTION)
        if t <= self.now:
            t = self.now

        if not isinstance(task, Task):
            task = Task(task)

        self.ready_at[t].append(task)
        if task not in self.all_tasks:
            self.all_tasks.append(task)
        if t == 0:
            print(f'[loop] task {task.id} scheduled at t={t}')

    def create_task(self, coroutine):
        task = Task(coroutine)
        self.schedule(task)
        return task

    def remove(self, task):
        if task in self.all_tasks:
            self.all_tasks.remove(task)

    def run(self):
        sel = selectors.DefaultSelector()

        while self.all_tasks:
            self.now = round(self.now, RESOLUTION)

            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

            while self.ready_at[self.now]:
                task = self.ready_at[self.now].pop(0)
                try:
                    yielded = next(task.coroutine)
                except StopIteration as e:
                    task.result = e.value
                    task.callback(task)
                    self.remove(task)
                except subprocess.TimeoutExpired as e:
                    task.exception = e
                    task.errback(task)
                    self.remove(task)
                else:
                    if yielded is None:
                        yielded = TICK
                    run_next = round(self.now + yielded, RESOLUTION)
                    self.schedule(task, t=run_next)
            self.now += TICK
            time.sleep(TICK)


if __name__ == '__main__':
    loop = Loop()

    loop.create_task(runner('sleep 10'.split(), timeout=5))
    loop.create_task(runner('sleep 10'.split()))
    loop.create_task(runner('sleep 10'.split()))
    loop.create_task(runner('sleep 10'.split()))
    loop.create_task(runner('sleep 10'.split()))

    task = loop.create_task(runner('sleep 10'.split()))
    loop.create_task(monitor(task))

    loop.run()
