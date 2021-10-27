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
    perf_proc = subprocess.Popen(
        ["perf", "record", "-F", "max", "-g", "-p", pids] + args
    )
    # FIXME: how else do we wait until perf has started up?
    time.sleep(0.1)
    try:
        yield
    finally:
        perf_proc.send_signal(signal.SIGINT)
        perf_proc.wait()

        fname_out = os.path.join(output_dir, f"{name}.svg")
        flame_cmd = "perf script | stackcollapse-perf.pl | flamegraph.pl"
        with open(fname_out, "wb") as f_out:
            p = subprocess.run(flame_cmd, shell=True, check=True, capture_output=True)
            f_out.write(p.stdout)
