import os
import sys
import time
import signal
import contextlib
import subprocess
import base64
from tempfile import TemporaryDirectory

import psutil


def get_children(main_process):
    children = [
        pr for pr in psutil.process_iter() if pr.ppid() == main_process.pid
    ]
    return children


class PerfResult:
    def __init__(self, flamegraph_path: str):
        self.flamegraph_path = flamegraph_path

    def show(self):
        from IPython.display import SVG
        with open(self.flamegraph_path, "rb") as f:
            raw_svg = f.read()
            encoded = base64.standard_b64encode(raw_svg).decode("ascii")
        url = f"data:image/svg+xml;base64,{encoded}"
        return SVG(url=url)


@contextlib.contextmanager
def perf(name, args=None, output_dir="profiles"):
    main_pid = os.getpid()
    main_process = psutil.Process(pid=main_pid)
    children = get_children(main_process)
    if args is None:
        args = []
    else:
        args = list(args)
    pids = [str(main_pid)] + [str(c.pid) for c in children]
    pids = ",".join(pids)

    with TemporaryDirectory(prefix="perf_data") as perf_data_dir:
        perf_proc = subprocess.Popen(
            ["perf", "record", "-o", "perf.data", "-F", "max", "-g", "-p", pids] + args,
            cwd=perf_data_dir,
        )
        # FIXME: how else do we wait until perf has started up?
        time.sleep(0.1)
        fname_out = os.path.join(output_dir, f"{name}.svg")
        try:
            yield PerfResult(fname_out)
        finally:
            perf_proc.send_signal(signal.SIGINT)
            perf_proc.wait()

            flame_cmd = "perf script | stackcollapse-perf.pl | flamegraph.pl"
            with open(os.path.join(perf_data_dir, "perf.data"), "rb") as perf_data:
                with open(fname_out, "wb") as f_out:
                    p = subprocess.run(
                        flame_cmd,
                        shell=True,
                        check=True,
                        stdin=perf_data,
                        stdout=subprocess.PIPE,
                        stderr=sys.stderr,
                        cwd=perf_data_dir,
                    )
                    f_out.write(p.stdout)


@contextlib.contextmanager
def timer(name=None, nbytes=None):
    t0 = time.perf_counter()
    yield
    t1 = time.perf_counter()
    delta = t1 - t0

    parts = ["timer"]
    if name:
        parts.append(name)
    parts.append(f"{delta:.5f}s")
    if nbytes:
        throughput = nbytes / delta
        parts.append(f"{throughput/1024/1024/1024:.4f}GiB/s")

    print(" ".join(parts))
