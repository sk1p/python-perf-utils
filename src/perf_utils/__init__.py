import os
import time
import signal
import contextlib
import subprocess

import psutil


def get_children(main_process):
    children = [
        pr for pr in psutil.process_iter() if pr.ppid() == main_process.pid
    ]
    return children


@contextlib.contextmanager
def perf(name, args=None):
    main_pid = os.getpid()
    main_process = psutil.Process(pid=main_pid)
    children = get_children(main_process)
    if args is None:
        args = []
    else:
        args = list(args)
    pids = [str(main_pid)] + [str(c.pid) for c in children]
    pids = ",".join(pids)
    perf_proc = subprocess.Popen(
        ["perf", "record", "-F", "max", "-g", "-p", pids] + args
    )
    # FIXME: how else do we wait until perf has started up? check stdout?
    time.sleep(0.1)
    try:
        yield
    finally:
        perf_proc.send_signal(signal.SIGINT)
        perf_proc.wait()

        # FIXME: name must not contain special chars and is assumed to come
        # from a trusted source
        flame_cmd = f"perf script | stackcollapse-perf.pl | flamegraph.pl > profiles/{name}.svg" # noqa: 501
        subprocess.run(flame_cmd, shell=True, check=True)
