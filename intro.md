## Talking Points

* Python has great support for async programming
    * Since the end of the 90s
    * But especially since the early 2000s

* There are only few main ideas to remember
    * Asynchronous/non-blocking functions return immediately
    * Synchronous/blocking ("normal") functions do not return until they are done
    * Use async programming especially when the CPU is idle most of the time
    * Write code in a way that does not block
    * Everything happens in a single thread
        * You get concurrency i.e., several pieces of code "alive" at the same time 
        * You do not get parallelism  i.e., only one piece of code runs at any given point in time
        * But, you do not need locks etc. if you are careful
        * You need an event loop/scheduler
    * You need a way to know when your async functions are done
        * Futures and callbacks
