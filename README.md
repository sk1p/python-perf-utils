NOTE: this is a bit hacky, use at your own risk!

Some simple tools to profile Python programs using Linux perf. This is useful, for
example, to profile I/O heavy code, find bottlenecks in lower level system code etc.

Example usage:

```python

from perf_utils import perf

with perf(name="something"):
    do_something_compute_intensive()

```

The `perf` decorator will then write a flamegraph to `./profiles/<name>.svg`.

Needs to have `perf`, `stackcollapse-perf.pl` and `flamegraph.pl` installed and
available in the `$PATH` (the latter two from https://github.com/brendangregg/FlameGraph)
