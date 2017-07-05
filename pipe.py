from collections import defaultdict
import selectors
import subprocess
import time


CURRENT_EVENT_LOOP = None


def sleep(n):
    """
    Sleep for n iterations. Meaning we ask the event loop to wake us up
    after n iterations, i.e. at iteration current + n + 1
    """
    yield n


def monitor(task):
    """Monitor a task and exit once that task is done."""

    while True:
        if task.result is None:
            yield from sleep(0)
        else:
            print(f'task {task.id} is done!')
            return task.result


def runner(argv, timeout=0):
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
        yield from sleep(20)


def defcallback(task):
    """Schedule all the task children"""

    print(f'[task {task.id}] completed with result={task.result}')

    loop = get_event_loop()
    for child in task.children:
        print(f'[task {task.id}] scheduling child coroutine')
        loop.create_task(child)


def deferrback(task):
    print(f'[task {task.id}] raised "{task.exception}"')


class Task:
    """Wrap a coroutine in a Task object that actis like a Future."""

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

        self.children = []

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
    """This is the scheduler of all our Tasks."""

    def __init__(self):
        self.tasks = []
        self.ready_at = defaultdict(list)
        self.current_iteration = 0

    def schedule(self, task, iteration=0):
        """Schedule task at a given iteration number."""

        if iteration is None or iteration < self.current_iteration:
            iteration = self.current_iteration

        self.ready_at[iteration].append(task)
        if task not in self.tasks:
            self.tasks.append(task)
        if iteration == 0:
            print(f'[loop] task {task.id} scheduled at t={0}')

    def create_task(self, coroutine):
        """
        Wrap a coroutine in a Task object and schedule it at the first possible
        loop iteration.
        """
        task = Task(coroutine)

        if self.current_iteration == 0:
            run_at_iteration = 0
        else:
            run_at_iteration = self.current_iteration + 1

        self.schedule(task, iteration=run_at_iteration)
        return task

    def remove(self, task):
        """
        Remove task from the list of all active Tasks. This is done to control
        how long self.run() shold stick around for.
        """
        if task in self.tasks:
            self.tasks.remove(task)

    def run(self):
        """
        Run all active Tasks, concurrently. Exit once there are no more Tasks
        to run.
        """
        sel = selectors.DefaultSelector()

        while self.tasks:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

            for task in self.ready_at[self.current_iteration]:
                try:
                    run_after = next(task.coroutine)
                except StopIteration as e:
                    task.result = e.value
                    task.callback(task)
                    self.remove(task)
                except subprocess.TimeoutExpired as e:
                    task.exception = e
                    task.errback(task)
                    self.remove(task)
                else:
                    run_next = self.current_iteration + run_after + 1
                    self.schedule(task, run_next)

            self.current_iteration += 1
            time.sleep(.01)


def get_event_loop():
    """Return the Loop instance (it is a singleton-wannabe)."""

    global CURRENT_EVENT_LOOP

    if CURRENT_EVENT_LOOP is None:
        CURRENT_EVENT_LOOP = Loop()
    return CURRENT_EVENT_LOOP


if __name__ == '__main__':
    loop = get_event_loop()

    loop.create_task(runner('sleep 10'.split(), timeout=5))
    loop.create_task(runner('sleep 10'.split()))
    loop.create_task(runner('sleep 10'.split()))

    task = loop.create_task(runner('sleep 10'.split()))
    loop.create_task(monitor(task))

    task = loop.create_task(runner('sleep 10'.split()))
    task.children.append(runner('sleep 5'.split()))
    loop.run()
