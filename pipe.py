from collections import defaultdict
import subprocess
import time
import uuid


TICK = 0.001
RESOLUTION = 3


def runner(argv, timeout=0):
    _id = str(uuid.uuid4())

    t0 = time.time()
    print(f'[{_id}] Starting {" ".join(argv)} at t={t0}')
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)

    while True:
        exit_code = proc.poll()
        if exit_code is None:
            # Process is still running
            if timeout > 0 and time.time() - t0 >= timeout:
                print(f'[{_id}] Time is up!')
                proc.kill()
                return None
        else:
            print(f'[{_id}] {" ".join(argv)} exited; exit code {exit_code}')
            return proc
        # time.sleep(1)     <-- BAD idea
        yield 20 * TICK


def defcallback(result):
    print(f'[callback] result={result}')


def deferrback(error):
    print(f'[errback] exception={error}')


if __name__ == '__main__':
    now = 0
    ready_at = defaultdict(list)
    coro_ids = {}

    ready_at[now] = [(runner('sleep 10'.split()), defcallback, deferrback),
                     (runner('sleep 10'.split()), defcallback, deferrback),
                     (runner('sleep 10'.split()), defcallback, deferrback),
                     (runner('sleep 10'.split()), defcallback, deferrback),
                     (runner('sleep 10'.split()), defcallback, deferrback),
                     (runner('sleep 10'.split()), defcallback, deferrback)]
    number_of_coroutines = len(ready_at[now])

    while number_of_coroutines:
        now = round(now, RESOLUTION)

        while ready_at[now]:
            coro, clbk, erbk = ready_at[now].pop(0)
            try:
                run_next = round(now + coro.send(None), RESOLUTION)
            except StopIteration as e:
                clbk(e.value.returncode)
                number_of_coroutines -= 1
            except Exception as e:
                erbk(e)
                number_of_coroutines -= 1
            else:
                # print(f'[loop] waking up coroutine at t={now + run_next}')
                ready_at[run_next].append((coro, clbk, erbk))
        now += TICK
        time.sleep(TICK)
