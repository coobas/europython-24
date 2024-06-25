# Jakub Urban: From built-in concurrency primitives to large scale distributed computing

## Abstract

This talk is specifically designed for Python developers and data practitioners who wish to deepen their skills in asynchronous code execution, from single CPU applications to complex distributed systems with thousands of cores. We'll provide a detailed exploration and explanation of Python's asynchronous execution models and concurrency primitives, focusing on `Future` and `Executor` interfaces within the `concurrent.futures` module, and the event-driven architecture of `asyncio`. Special attention will be given to the processing of large datasets, a common challenge in data science and engineering.

We will start with the fundamental concepts and then explore how they apply to large scale, distributed execution frameworks like Dask or Ray. On step-by-step examples, we aim to demonstrate simple function executions and map-reduce operations. We will illustrate efficient collaboration between different concurrency models. The session will cover the transition to large-scale, distributed execution frameworks, offering practical guidelines for scaling your computations effectively and addressing common hurdles like data serialization in distributed environments.

Attendees will leave with a solid understanding of asynchronous code execution underpinnings. This talk will empower you to make informed practical decisions about applying concurrency in your data processing workflows. You will be able to seamlessly integrate new libraries or frameworks into your projects, ensuring optimal development lifecycle, performance and scalability.

## Concurrency lets you wait efficiently

- Concurrency enables you doing other things while waiting for results or other resources.
  - For example, you can wait for multiple calculations or API responds.
  - It's like a superpower of **waiting** in multiple queues at once.
- You do not need to care how the work to clear a queue is done.
![Communist Czech queues](communist_queues.png)
([Foto: Archiv Ladislava Růžičky](https://magazin.aktualne.cz/nemame-zeptejte-se-po-novem-roce-nakupy-za-socialismu-v-cesk/r~49f5bc5a5eba11eebe29ac1f6b220ee8/))
- Would be great for (Czech) communist queues.
  - Sometimes people even did not know what they were waiting for.
  - Would be great to wait in multiple queues at once.

## Concurrency lets you organise work efficiently

- You can respond to (accept) multiple requests even if there are still tasks to be done.
  - Requests can come, for example, from a queue or an API.
- You can dispatch queue requests to multiple workers.
  - ... or just switch between tasks efficiently.
  - ... although context switching is not free.

## Parallelism lets you *execute* multiple things at once

- Parallelism is about executing multiple things simultaneously.
- Concurrency does not imply parallelism.
  - Although parallelism is typically desired in concurrent systems.
- Examples of parallel calculation:
  - GPU's or vectorized CPU operations (SIMD).
  - Multi-core machines with shared memory (MIMD).
  - Distributed systems: clusters, clouds (MIMD).

## Where do you need concurrency?
- Web servers
- High-performance computing (HPC)
- Data engineering
- Machine learning


## Python defines built-in concurrency primitives

- `concurrent.futures`
  - > ... provides a high-level interface for asynchronously executing callables.
  - Proposed in 2009: [PEP-3148](https://peps.python.org/pep-3148)
  - We will focus on using and building on these primitives.
- Other standard lib [modules for concurrent execution](https://docs.python.org/3/library/concurrency.html) include:
  - `threading` and `multiprocessing`: parallelism, synchronisation primitives.
  - `subprocess`: subprocess management.
  - `asyncio`: cooperative multitasking.
  - `contextvars`: context-local state.

## `from concurrent.futures import Executor`
> Executor is an abstract class that provides methods to execute calls asynchronously.
- This is indeed abstract 😅
- What does one need in particular?
  1. Create an executor: Choose type and parameters.
  2. Submit tasks to the executor.
  3. Collect results.
  4. Shutdown the executor.

## 1. Create an executor

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

MAX_WORKERS = 4

thread_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
process_executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)
```

## 2. Submit tasks to the executor

```python
def do_some_math(x: float) -> float:
    return x * x
```

1. Single calculation via `submit`:
```python
result = thread_executor.submit(do_some_math, 5)
```
2. Multiple calculations via `map`:
```python
results = thread_executor.map(do_some_math, range(10))
```

## 3a. Collect result: single `Future`

- The output of `submit` is a `concurrent.futures.Future` object:

```python
print(result)
<Future at 0x122921490 state=finished returned int>
```

- `Future` is a placeholder for the result of a computation that may not be completed yet.
- `Future` encapsulates the asynchronous execution.
- Most important methods are:
  - `result(timeout=None)`: Waits for the computation to complete and returns the result.
  - `done()`: Returns `True` if the call was successfully cancelled or finished running.
  - `cancel()`: Attempts to cancel the computation.

## 3b. Collect multiple results

- The output of `map` is a generator object:

```python
print(results)
<generator object Executor.map.<locals>.result_iterator at 0x122a1f4d0>
```

- This generator yields results as they become available.

## 3c. Collect multiple results with `as_completed`

- We can submit multiple tasks without using executor's `map` method.
  - This will yield multiple `Future` objects.

```python
futures = [executor.submit(do_some_math, x) for x in range(10)]
```
or using built-in `map`:
```python
from functools import partial
futures = map(partial(executor.submit, do_some_math), range(10))
```

- We can use `as_completed` now iterate over futures as they complete:

```python
from concurrent.futures import as_completed

for future in as_completed(futures):
    print(future.result())
```

## 3d. Collect multiple results with `wait`

- `wait` gives us more flexibility and control over the futures while waiting.
  - We can use waiting timeout.
  - We can, e.g., cancel futures that have not started running.

```python
done, not_done = wait(futures, timeout=1, return_when=FIRST_COMPLETED)
```

- `done` and `not_done` are sets of futures.

## 4. Shutdown the executor

- Executors should be shutdown to release resources.
  - This may be done automatically when the executor is garbage collected.
  - The type and released resources depend on the executor type.

```python
executor.shutdown(wait=True, cancel_futures=False)
```

- `wait=True` blocks until all futures are completed and resources are freed.
- `cancel_futures=False` cancels pending futures tha have not started running.

- Lifetime can also be managed by a `with` block:

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    result = executor.submit(do_some_math, 5)
```

## `ThreadPoolExecutor` limitation: Global Interpreter Lock (GIL)

- Global Interpreter Lock (GIL) is probably the most (in)famous limitation of CPython.
- GIL prevents multiple threads from executing Python code simultaneously (in parallel).
- However, GIL can be released by:
  - I/O operations (file operations, network requests).
  - C extensions (NumPy, Pandas, TensorFlow).
- ... thus enabling threads to run in parallel.

## `ProcessPoolExecutor` limitation: Serialization

- Submitted tasks, i.e callables and data, are sent as pickles to the worker processes.
- Not all objects can be pickled.
  - E.g., lambda or nested functions.

```python
process_executor.submit(lambda x: x * x, 5).result()
```
```
PicklingError: Can't pickle <function <lambda> ...
```

## Resolving serialization issues

- Libraries like `cloudpickle` or `dill` resolve a lot of these limitations.
- Our first non-builtin executor: [`joblib/loky`](https://github.com/joblib/loky)
> The aim of this project is to provide a robust, cross-platform and cross-version implementation of the `ProcessPoolExecutor` class of `concurrent.futures`.
  - Consistent and robust spawn behaviour
  - Reusable executor
  - Transparent cloudpickle integration

```python
# Create an executor with 4 worker processes, that will
# automatically shutdown after idling for 2s
executor = loky.get_reusable_executor(max_workers=4, timeout=2)
```

- `loky` is a straightforward replacement for `ProcessPoolExecutor`.

## `concurrent.futures` within `asyncio`

- `asyncio` enables concurrent code using the `async`/`await` syntax.
- An internal event loop manages the execution of coroutines.
- This is a cooperative multitasking model.
- `asyncio.Future` is similar to `concurrent.futures.Future`.
  - and can be created from `concurrent.futures.Future`:
```python
concurrent_future = executor.submit(do_some_math, 5)
asyncio_future = asyncio.wrap_future(concurrent_future)
```
- This can also be done via `loop.run_in_executor`.
```python
loop = asyncio.get_event_loop()
asyncio_future = loop.run_in_executor(executor, do_some_math, 5)
```
- The `asyncio` `Future` can be awaited as usual:
```python
result = await asyncio_future
```

## Practical data processing usecases with `concurrent.futures`

- Quick parallel batch processing, e.g.
  - Run Pandas pipeline on multiple files.
  - Grid search hyperparameters.
- Non-blocking data processing in a web server or a streaming processor.
  - Even a single-worker executor can enable non-blocking processing.
  - Especially useful for `asyncio` applications.
  - Must be careful with resource utilisation, in particular RAM.

## Scaling out: Distributed computing

At some point, your calculation may not fit into a single machine.
- Need to process huge datasets.
- The calculation is too heavy.
- We need too many repetitions, e.g. in a grid search.

Sometimes, resons for distributed computing are not resource-related.
- Security or compliance can constrain local or ad-hoc processing.
- You simply need to turn off your computer.

## Resource-driven scaling out

- Memory: "My data do not fit into my (computer's) memory."
  - Symptoms: OOM (Out Of Memory) kills, swapping leading to system freeze.
- Processing power: "My calculation takes too long."
  - Symptoms: CPU, GPU, other PU's at 100%, calculation time too long.

Before spinning up a cluster, there are possibilities:
- Profile and possibly optimise your code.
- Data can (sometimes) be memory-mapped.
- Large data can be processed in chunks.
  - This is where executors can help.
  - Even the large scale frameworks like Dask or Ray can help when running on a single machine.
