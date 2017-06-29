from collections import defaultdict
from functools import wraps
import subprocess
import time
import uuid


TICK = 0.01    # one simulation tick in seconds
PRCS = 2


def coroutine(fn):
    @wraps(fn)
    def wrapper(*args, **kwds):
        coro = fn(*args, **kwds)
        coro.send(None)
        return coro
    return wrapper


def runner(argv, timeout=0):
    _id = str(uuid.uuid4())

    t0 = time.time()

    print(f'[{_id}] Running {" ".join(argv)} at {t0}')
    proc = subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False)

    while True:
        exit_code = proc.poll()
        if exit_code is None:
            if timeout > 0 and time.time() - t0 >= timeout:
                print(f'[{_id}] Time is up!')
                return None
        else:
            print(f'[{_id}] {" ".join(argv)} done.')
            return proc
        # time.sleep(10)    # <-- BAD idea
        yield TICK * 20


def generic_callback(result):
    print(result)


if __name__ == '__main__':
    # Scheduler/event loop
    now = 0
    ready_at = defaultdict(list)
    ready_at[now] = [(runner(argv), generic_callback)
                     for argv in ['sleep 5'.split(),
                                  'sleep 10'.split()]]
    number_of_coroutines = len(ready_at[now])

    while number_of_coroutines:
        now = round(now, PRCS)

        while ready_at[now]:
            coro, clbk = ready_at[now].pop(0)
            try:
                run_next = round(now + coro.send(None), PRCS)
            except StopIteration as e:
                number_of_coroutines -= 1
                clbk(e.value)
            else:
                print(f'[loop] waking up coroutine at t={run_next}')
                ready_at[run_next].append((coro, clbk))
        now += TICK
        time.sleep(TICK)
